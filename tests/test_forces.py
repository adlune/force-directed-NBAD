"""
unit tests for the force formulas, checked against results worked out on
paper.
"""

import numpy as np
import pytest

from example_graphs import two_cliques, two_nodes
from force_simulation import energy, net_forces, stiffness


def test_two_nodes_at_distance_k_feel_no_force():
    # at d = k the attraction d**2 / k and the repulsion k**2 / d are equal
    k = 0.2
    positions = np.array([[0.0, 0.0], [k, 0.0]])
    forces = net_forces(positions, two_nodes(), k, 1e-12)
    assert np.allclose(forces, 0.0, atol=1e-12)


def test_two_nodes_at_distance_k_have_stiffness_3():
    # spring 2d/k = 2 plus repulsion k**2/d**2 = 1
    k = 0.2
    positions = np.array([[0.0, 0.0], [k, 0.0]])
    assert np.allclose(stiffness(positions, two_nodes(), k, 1e-12), [3.0, 3.0])


@pytest.mark.parametrize("gravity", [0.0, 1.0])
def test_forces_are_minus_the_gradient_of_the_energy(gravity):
    # move one coordinate a tiny amount h in both directions; the change in
    # energy divided by 2h approximates the derivative, which must equal
    # minus the force (the check of the energy derivation, with and without
    # the central gravity)
    adjacency = two_cliques(size=3)
    k = 0.3
    positions = np.random.default_rng(1).uniform(-0.5, 0.5, size=(6, 2))
    forces = net_forces(positions, adjacency, k, 1e-12, gravity)

    h = 1e-6
    for v in range(6):
        for axis in range(2):
            shifted_up = positions.copy()
            shifted_down = positions.copy()
            shifted_up[v, axis] += h
            shifted_down[v, axis] -= h
            slope = (energy(shifted_up, adjacency, k, 1e-12, gravity)
                     - energy(shifted_down, adjacency, k, 1e-12, gravity)) / (2 * h)
            assert np.isclose(-slope, forces[v, axis], rtol=1e-5, atol=1e-8)
