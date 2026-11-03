"""
compare_starts.py

compares the cold start and the warm start on the same consecutive windows,
with several seeds each. every (start, seed) pair is one job, and the jobs
run in parallel.

usage:
  python src/compare_starts.py data/raw/Monday-WorkingHours.pcap_ISCX.csv
      --start 10:00 --end 10:20 --seeds 3
"""

import argparse
import time

import pandas as pd

from graph_builder import load_flows, window_starts
from run_windows import run_in_parallel


def main():
    parser = argparse.ArgumentParser(description="cold start against warm start")
    parser.add_argument("file")
    parser.add_argument("--start", default="10:00")
    parser.add_argument("--end", default="10:20")
    parser.add_argument("--seeds", type=int, default=3)
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--output", default="results/compare_starts.csv")
    args = parser.parse_args()

    flows = load_flows(args.file)
    day = flows["timestamp"].min().normalize()
    first = day + pd.Timedelta(args.start + ":00")
    end = day + pd.Timedelta(args.end + ":00")
    starts = window_starts(flows)
    starts = starts[(starts >= first) & (starts < end)]
    chunk = flows[(flows["timestamp"] >= first) & (flows["timestamp"] < end)]

    jobs = [
        {"name": "warm" if warm else "cold", "flows": chunk, "starts": starts,
         "warm_start": warm, "seed": seed}
        for warm in (False, True)
        for seed in range(args.seeds)
    ]

    clock = time.perf_counter()
    table = run_in_parallel(jobs, args.workers)
    wall = time.perf_counter() - clock
    table.to_csv(args.output, index=False)

    # one line per window: the mean over seeds of each start
    per_window = table.pivot_table(index="window", columns="file",
                                   values=["iterations", "seconds"], aggfunc="mean")
    print(per_window.round(1).to_string())
    print()
    totals = table.groupby(["file", "seed"])[["iterations", "seconds"]].sum()
    print(totals.round(1).to_string())
    print()
    print("not converged:", (~table["converged"]).sum(), "of", len(table))
    print(f"wall time {wall:.0f} s for {table['seconds'].sum():.0f} s of simulation")


if __name__ == "__main__":
    main()
