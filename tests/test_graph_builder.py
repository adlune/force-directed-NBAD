"""
tests for graph_builder.py, using a tiny hand-made table of flows whose
correct graph we can work out on paper.
"""

import numpy as np
import pandas as pd

from graph_builder import build_graph, flows_in_window


def make_flows():
    # four flows between hosts a, b, c, d:
    #   a -> b and b -> a must become one single edge a - b
    #   a -> c gives the edge a - c
    #   d -> d is a host talking to itself and must be ignored
    return pd.DataFrame({
        "src_ip": ["a", "b", "a", "d"],
        "dst_ip": ["b", "a", "c", "d"],
        "timestamp": pd.to_datetime([
            "2017-07-03 09:00:10",
            "2017-07-03 09:00:20",
            "2017-07-03 09:00:59",
            "2017-07-03 09:01:00",
        ]),
    })


def test_nodes_are_sorted_and_skip_self_loops():
    nodes, _ = build_graph(make_flows())
    # d only appears in a self-loop, so it is not a node
    assert list(nodes) == ["a", "b", "c"]


def test_adjacency_matches_hand_calculation():
    _, adjacency = build_graph(make_flows())
    # rows and columns follow the node order a, b, c
    expected = np.array([
        [0, 1, 1],
        [1, 0, 0],
        [1, 0, 0],
    ])
    assert np.array_equal(adjacency, expected)


def test_adjacency_is_symmetric_with_empty_diagonal():
    _, adjacency = build_graph(make_flows())
    assert np.array_equal(adjacency, adjacency.T)
    assert np.all(np.diag(adjacency) == 0)


def test_window_excludes_its_end():
    flows = make_flows()
    start = pd.Timestamp("2017-07-03 09:00:00")
    window = flows_in_window(flows, start, length="60s")
    # 09:01:00 is the start of the next window, so only 3 flows belong here
    assert len(window) == 3
