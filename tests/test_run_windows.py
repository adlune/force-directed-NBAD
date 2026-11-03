"""
tests for the starting layout used by the warm start.
"""

import numpy as np

from run_windows import starting_layout


def test_warm_start_places_nodes_by_the_rules():
    # a and b were in the previous window; c is new and connected to a;
    # d is new and connected only to c, which is also new
    nodes = np.array(["a", "b", "c", "d"])
    adjacency = np.array([
        [0, 1, 1, 0],
        [1, 0, 0, 0],
        [1, 0, 0, 1],
        [0, 0, 1, 0],
    ])
    previous = {"a": np.array([0.1, 0.2]), "b": np.array([-0.3, 0.0]), "gone": np.array([0.4, 0.4])}
    k = 0.05
    positions = starting_layout(nodes, adjacency, previous, k, 1.0, 1.0,
                                np.random.default_rng(0))

    # nodes that were present keep their positions
    assert np.allclose(positions[0], previous["a"])
    assert np.allclose(positions[1], previous["b"])
    # the new neighbour of a starts at distance k from it
    assert np.isclose(np.linalg.norm(positions[2] - previous["a"]), k)
    # d has no neighbour that was present, so it only has to lie in the frame
    assert np.all(np.abs(positions[3]) <= 0.5)


def test_cold_start_is_random_inside_the_frame():
    nodes = np.array(["a", "b", "c"])
    adjacency = np.array([[0, 1, 0], [1, 0, 1], [0, 1, 0]])
    positions = starting_layout(nodes, adjacency, {}, 0.1, 1.0, 1.0,
                                np.random.default_rng(0))
    assert np.all(np.abs(positions) <= 0.5)
    # three random points are all different
    assert len(np.unique(positions, axis=0)) == 3
