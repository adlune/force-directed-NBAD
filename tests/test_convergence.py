"""
convergence tests on hand-built graphs whose correct answer is known.
"""

import numpy as np
import pytest

from example_graphs import two_cliques, two_nodes
from force_simulation import ideal_distance, run_simulation


# c = 0.1 makes k small compared with the frame, so a start at 3k still fits
# inside it and neither node touches the walls
c_small = 0.1


@pytest.mark.parametrize("start_over_k", [0.3, 3.0])
def test_two_connected_nodes_settle_at_distance_k(start_over_k):
    k = ideal_distance(2, 1.0, 1.0, c_small)
    half_gap = start_over_k * k / 2
    start = np.array([[-half_gap, 0.0], [half_gap, 0.0]])

    # gravity is switched off: the exact answer d = k holds only for the two
    # Fruchterman-Reingold forces (gravity would pull the pair slightly closer)
    result = run_simulation(two_nodes(), c=c_small, positions=start, gravity=0.0)

    final_distance = np.linalg.norm(result["positions"][0] - result["positions"][1])
    assert result["converged"]
    assert abs(final_distance - k) < 1e-3 * k


@pytest.mark.parametrize("seed", range(5))
def test_two_cliques_converge_from_any_start(seed):
    # different seeds give different random starting layouts; with a stable
    # damping and slow enough cooling, every one of them must converge
    result = run_simulation(two_cliques(size=5), seed=seed)
    assert result["converged"]


def test_two_cliques_form_two_separate_clusters():
    adjacency = two_cliques(size=5)
    result = run_simulation(adjacency, max_iterations=500)
    positions = result["positions"]

    group_a, group_b = positions[:5], positions[5:]
    center_a, center_b = group_a.mean(axis=0), group_b.mean(axis=0)

    # how spread out each group is: average distance of its nodes to its center
    spread = np.mean([
        np.linalg.norm(group_a - center_a, axis=1).mean(),
        np.linalg.norm(group_b - center_b, axis=1).mean(),
    ])
    separation = np.linalg.norm(center_a - center_b)

    # two clearly separate clusters: the centers are much farther apart
    # than the size of either cluster
    assert separation > 2 * spread
