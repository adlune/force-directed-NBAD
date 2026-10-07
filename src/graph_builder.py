"""
graph_builder.py

turns CICIDS2017 flow records into graphs, in two steps:
  1. load_flows: read one CSV from the GeneratedLabelledFlows release, keep
     the columns the model needs, and return a clean table of flows.
  2. build_graph: take the flows of one time window and return the nodes
     (IP addresses) and the adjacency matrix of the undirected graph.
"""

import sys

import numpy as np
import pandas as pd


# the CSVs have 85 columns; these are the only ones the model uses.
# names are written without the leading space that most headers carry.
columns_to_keep = [
    "Source IP",
    "Destination IP",
    "Destination Port",
    "Protocol",
    "Timestamp",
    "Total Length of Fwd Packets",
    "Total Length of Bwd Packets",
    "Label",
]


def parse_timestamps(raw):
    """
    convert the Timestamp column (text) into real datetimes.

    the files use one of two formats:
      "03/07/2017 08:55:58"  day first, with seconds
      "7/7/2017 3:30"        month first, no seconds
    both are written on a 12 hour clock without AM/PM, so 1:00 means 13:00.
    """
    raw = raw.str.strip()

    # two colons means the time includes seconds, which is the day first format
    if raw.iloc[0].count(":") == 2:
        times = pd.to_datetime(raw, format="%d/%m/%Y %H:%M:%S")
    else:
        times = pd.to_datetime(raw, format="%m/%d/%Y %H:%M")

    # the capture ran from about 8:55 to 17:00, so any hour below 8 is afternoon
    is_afternoon = times.dt.hour < 8
    times = times + pd.to_timedelta(is_afternoon.astype(int) * 12, unit="h")
    return times


def load_flows(path):
    """
    load one CSV and return a table with one row per flow and the columns
    src_ip, dst_ip, dst_port, protocol, timestamp, bytes, label,
    sorted by time.
    """
    flows = pd.read_csv(
        path,
        # read only the columns we need; strip() handles the leading spaces
        usecols=lambda name: name.strip() in columns_to_keep,
        # latin-1 can decode any byte, so it never fails even on files that
        # are not valid UTF-8; for plain ASCII text the result is identical
        encoding="latin-1",
    )
    flows.columns = flows.columns.str.strip()

    flows["timestamp"] = parse_timestamps(flows["Timestamp"])

    # total traffic of the flow in both directions, a candidate edge weight
    flows["bytes"] = (
        flows["Total Length of Fwd Packets"] + flows["Total Length of Bwd Packets"]
    )

    flows = flows.rename(columns={
        "Source IP": "src_ip",
        "Destination IP": "dst_ip",
        "Destination Port": "dst_port",
        "Protocol": "protocol",
        "Label": "label",
    })
    flows = flows[["src_ip", "dst_ip", "dst_port", "protocol",
                   "timestamp", "bytes", "label"]]

    # the rows of the raw files are not guaranteed to be in time order
    flows = flows.sort_values("timestamp").reset_index(drop=True)
    return flows


def window_starts(flows, length="60s"):
    """
    return the start time of every window that covers the flows.
    the first start is rounded down to a whole minute, so windows line up
    with the clock (09:00:00, 09:01:00, ...).
    """
    first = flows["timestamp"].min().floor(length)
    last = flows["timestamp"].max()
    return pd.date_range(first, last, freq=length)


def flows_in_window(flows, start, length="60s"):
    """
    return the flows with start <= timestamp < start + length.
    the end is excluded so that a flow never falls into two windows.
    """
    end = start + pd.Timedelta(length)
    inside = (flows["timestamp"] >= start) & (flows["timestamp"] < end)
    return flows[inside]


def build_graph(window_flows):
    """
    build the undirected, unweighted graph of one window.

    returns:
      nodes      array of the N IP addresses, sorted; node i is nodes[i]
      adjacency  N x N array of 0 and 1; adjacency[i, j] = 1 when hosts i and
                 j exchanged at least one flow, in either direction
    """
    # a flow from a host to itself cannot be an edge (its length would be 0),
    # so it is dropped; this also keeps the matrix diagonal at 0
    pairs = window_flows[window_flows["src_ip"] != window_flows["dst_ip"]]

    # every IP that appears as source or destination becomes one node.
    # np.unique also sorts them, so the same window always gives the same order
    nodes = np.unique(np.concatenate([
        pairs["src_ip"].to_numpy(),
        pairs["dst_ip"].to_numpy(),
    ]))

    # translate each IP into its row number in the matrix
    index_of = {ip: i for i, ip in enumerate(nodes)}
    src = pairs["src_ip"].map(index_of).to_numpy()
    dst = pairs["dst_ip"].map(index_of).to_numpy()

    # mark both directions, so A -> B and B -> A give the same single edge.
    # repeated flows between the same pair just write 1 again (unweighted)
    n = len(nodes)
    adjacency = np.zeros((n, n), dtype=int)
    adjacency[src, dst] = 1
    adjacency[dst, src] = 1
    return nodes, adjacency


if __name__ == "__main__":
    # quick summary when run directly:
    # python src/graph_builder.py data/raw/Monday-WorkingHours.pcap_ISCX.csv
    flows = load_flows(sys.argv[1])
    print(flows.head())
    print()
    print("flows:", len(flows))
    print("time range:", flows["timestamp"].min(), "to", flows["timestamp"].max())
    print("unique IPs:", pd.concat([flows["src_ip"], flows["dst_ip"]]).nunique())
    print("labels:", flows["label"].value_counts().to_dict())

    # build the graph of the first window as an example
    start = window_starts(flows)[0]
    nodes, adjacency = build_graph(flows_in_window(flows, start))
    # each edge appears twice in the matrix (i, j and j, i), so divide by 2
    print()
    print("first window starts at", start)
    print("nodes:", len(nodes), "| edges:", adjacency.sum() // 2)
