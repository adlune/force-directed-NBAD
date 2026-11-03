"""
run_windows.py

runs the simulation on a sequence of consecutive windows and collects one row
of measurements per window (size of the graph, iterations to convergence,
final energy, wall time).

two ways to choose the starting layout of each window:
  cold start  every node starts at a random position
  warm start  nodes that were present in the previous window start where
              they ended there, so only the part of the graph that changed
              has to move

long runs are split into chunks (for example one hour each). the windows of a
chunk run in order, because the warm start needs the previous window, while
different chunks and different files are independent and run in parallel,
one process per chunk.

usage:
  python src/run_windows.py data/raw/Monday-WorkingHours.pcap_ISCX.csv
      --start 10:00 --end 11:00 --chunk 60 --workers 4 --output results/monday.csv
"""

import argparse
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

from force_simulation import ideal_distance, run_simulation
from graph_builder import build_graph, flows_in_window, load_flows, window_starts


def starting_layout(nodes, adjacency, previous, k, width, height, rng):
    """
    starting positions for one window.

    previous maps each IP of the previous window to its final position; it is
    empty for a cold start, which then gives every node a random position.
      - a node that was present keeps its previous position
      - a new node with neighbours that were present starts at distance k
        from the average position of those neighbours, in a random direction
        (random, so that two new leaves of one hub do not land on one point)
      - any other node gets a random position in the frame
    """
    half = np.array([width / 2, height / 2])
    positions = rng.uniform(-half, half, size=(len(nodes), 2))

    was_present = np.array([ip in previous for ip in nodes], dtype=bool)
    for i in np.flatnonzero(was_present):
        positions[i] = previous[nodes[i]]

    for i in np.flatnonzero(~was_present):
        old_neighbours = np.flatnonzero((adjacency[i] == 1) & was_present)
        if len(old_neighbours) > 0:
            center = positions[old_neighbours].mean(axis=0)
            angle = rng.uniform(0, 2 * np.pi)
            positions[i] = center + k * np.array([np.cos(angle), np.sin(angle)])

    return np.clip(positions, -half, half)


def run_windows(flows, starts, warm_start=True, seed=0, width=1.0, height=1.0,
                c=0.3):
    """
    run the simulation on each window in starts, in order, and return a table
    with one row per window. windows with fewer than two nodes are skipped,
    since a single node has no layout to compute.
    """
    rng = np.random.default_rng(seed)
    previous = {}
    rows = []

    for start in starts:
        nodes, adjacency = build_graph(flows_in_window(flows, start))
        if len(nodes) < 2:
            continue

        k = ideal_distance(len(nodes), width, height, c)
        positions = starting_layout(
            nodes, adjacency, previous if warm_start else {}, k, width, height, rng)

        clock = time.perf_counter()
        result = run_simulation(adjacency, width, height, c, positions=positions,
                                record_history=False)
        seconds = time.perf_counter() - clock

        rows.append({
            "window": start,
            "nodes": len(nodes),
            "edges": adjacency.sum() // 2,
            # nodes that were also in the previous window (counted even for
            # a cold start, so both kinds of run report the same column)
            "kept_nodes": sum(ip in previous for ip in nodes),
            "warm_start": warm_start,
            "seed": seed,
            "iterations": result["iterations"],
            "converged": result["converged"],
            "energy": result["energy"],
            "seconds": seconds,
        })
        # always remember the final layout; a cold start just ignores it
        previous = dict(zip(nodes, result["positions"]))

    return pd.DataFrame(rows)


def run_job(job):
    """
    run one chunk; job is a dictionary with the chunk's flows and options.
    it is a separate function so that a pool of processes can call it.
    """
    table = run_windows(job["flows"], job["starts"], job["warm_start"], job["seed"])
    table.insert(0, "file", job["name"])
    return table


def split_into_jobs(name, flows, starts, chunk, warm_start, seed):
    """
    group the window starts into chunks of the given length (in minutes) and
    return one job per chunk, each carrying only the flows of its own chunk.
    """
    jobs = []
    chunk_of = starts.floor(f"{chunk}min")
    for chunk_start in chunk_of.unique():
        chunk_starts = starts[chunk_of == chunk_start]
        end = chunk_starts[-1] + pd.Timedelta("60s")
        inside = (flows["timestamp"] >= chunk_starts[0]) & (flows["timestamp"] < end)
        jobs.append({
            "name": name,
            "flows": flows[inside],
            "starts": chunk_starts,
            "warm_start": warm_start,
            "seed": seed,
        })
    return jobs


def run_in_parallel(jobs, workers):
    """
    run the jobs in a pool of worker processes and join their tables.
    each process runs one job at a time; map returns the tables in the order
    of the jobs, whatever order they finish in.
    """
    with ProcessPoolExecutor(max_workers=workers) as pool:
        tables = list(pool.map(run_job, jobs))
    return pd.concat(tables, ignore_index=True)


def main():
    parser = argparse.ArgumentParser(description="run the simulation on consecutive windows")
    parser.add_argument("files", nargs="+", help="CSV files from TrafficLabelling")
    parser.add_argument("--start", help="first window, time of day, for example 10:00")
    parser.add_argument("--end", help="end of the last window (excluded), for example 11:00")
    parser.add_argument("--chunk", type=int, default=60, help="chunk length in minutes")
    parser.add_argument("--workers", type=int, default=4, help="number of processes")
    parser.add_argument("--cold", action="store_true", help="random start for every window")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--output", default="results/windows.csv")
    args = parser.parse_args()

    jobs = []
    for path in args.files:
        flows = load_flows(path)
        starts = window_starts(flows)
        # the times of day are attached to the date of the file
        day = flows["timestamp"].min().normalize()
        if args.start:
            starts = starts[starts >= day + pd.Timedelta(args.start + ":00")]
        if args.end:
            starts = starts[starts < day + pd.Timedelta(args.end + ":00")]
        jobs += split_into_jobs(Path(path).name, flows, starts, args.chunk,
                                not args.cold, args.seed)

    print(f"{len(jobs)} chunks on {args.workers} processes", flush=True)
    clock = time.perf_counter()
    table = run_in_parallel(jobs, args.workers)
    print(f"done in {time.perf_counter() - clock:.0f} s", flush=True)

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(args.output, index=False)
    print(table.groupby("file")[["iterations", "seconds"]].sum())


# the guard is required for the process pool: each worker process imports
# this file, and without it every worker would start its own pool
if __name__ == "__main__":
    main()
