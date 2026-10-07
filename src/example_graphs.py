"""
example_graphs.py

small hand-built graphs whose correct layout we know in advance. they are
used to check the simulation before running it on real traffic.
"""

import numpy as np


def two_nodes():
    """two nodes joined by one edge; the equilibrium distance is exactly k."""
    return np.array([
        [0, 1],
        [1, 0],
    ])


def two_cliques(size=5):
    """
    two groups of `size` nodes, every node connected to every other node in
    its group, plus one bridge edge between the last node of the first group
    and the first node of the second group. the layout should show two
    separate clusters joined by the bridge.
    """
    n = 2 * size
    adjacency = np.zeros((n, n), dtype=int)

    # fill each group's block with 1, then remove the diagonal (no self-loops)
    adjacency[:size, :size] = 1
    adjacency[size:, size:] = 1
    np.fill_diagonal(adjacency, 0)

    bridge_a, bridge_b = size - 1, size
    adjacency[bridge_a, bridge_b] = 1
    adjacency[bridge_b, bridge_a] = 1
    return adjacency
