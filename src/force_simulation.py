"""
force_simulation.py

the Fruchterman-Reingold force model. nodes live in a frame of size
width x height centered at the origin. every pair of nodes repels with
magnitude k**2 / d, every edge attracts with magnitude d**2 / k, and every
node is pulled toward the center with magnitude g * distance. each
iteration moves the nodes along their net force, with a step scaled to each
node's stiffness, capped by the temperature, and clamped to the frame.

array shapes used throughout (n = number of nodes):
  positions  (n, 2)     row v is the (x, y) position of node v
  adjacency  (n, n)     1 where an edge exists, 0 elsewhere
  forces     (n, 2)     row v is the net force on node v
"""

import numpy as np


def ideal_distance(n_nodes, width, height, c=1.0):
    """k = c * sqrt(width * height / n_nodes), the ideal distance between nodes."""
    return c * np.sqrt(width * height / n_nodes)


def pairwise(positions, min_distance):
    """
    return the difference vectors and distances between every pair of nodes.

      diff[v, u] = x_v - x_u        shape (n, n, 2)
      dist[v, u] = |x_v - x_u|      shape (n, n)

    distances are floored at min_distance so that later divisions and
    logarithms never see a zero (this also covers the diagonal, v = u).
    """
    diff = positions[:, np.newaxis, :] - positions[np.newaxis, :, :]
    dist = np.linalg.norm(diff, axis=2)
    dist = np.maximum(dist, min_distance)
    return diff, dist


def net_forces(positions, adjacency, k, min_distance, gravity=0.0):
    """
    net force on every node.

    for each pair (v, u) we compute a signed magnitude along the unit vector
    from u to v: positive pushes v away from u, negative pulls v toward u.
      repulsion, all pairs:   + k**2 / d
      attraction, edges only: - d**2 / k
    the force on v is the sum over u of magnitude * unit vector, plus the
    central gravity - gravity * x_v, a pull toward the origin that grows
    with distance (it keeps separate components from drifting apart).
    """
    diff, dist = pairwise(positions, min_distance)

    # unit vectors from u toward v; on the diagonal diff is 0, so unit is 0
    unit = diff / dist[:, :, np.newaxis]

    repulsion = k**2 / dist
    np.fill_diagonal(repulsion, 0.0)          # a node does not push itself
    attraction = adjacency * dist**2 / k      # zero wherever there is no edge

    magnitude = repulsion - attraction        # shape (n, n)
    forces = (magnitude[:, :, np.newaxis] * unit).sum(axis=1)
    return forces - gravity * positions


def energy(positions, adjacency, k, min_distance, gravity=0.0):
    """
    total energy:
      E = sum over edges of d**3 / (3k)  -  sum over pairs u < v of k**2 ln d
          + (gravity / 2) * sum over nodes of |x_v|**2
    each pair is counted once by keeping only the upper triangle of the
    distance table (row < column).
    """
    _, dist = pairwise(positions, min_distance)
    rows, cols = np.triu_indices(len(positions), 1)
    d = dist[rows, cols]
    a = adjacency[rows, cols]
    pair_energy = np.sum(a * d**3 / (3 * k)) - np.sum(k**2 * np.log(d))
    gravity_energy = gravity / 2 * np.sum(positions**2)
    return pair_energy + gravity_energy


def residual_force(positions, forces, width, height):
    """
    largest net force on any node, ignoring force components that push a node
    out through the frame edge it is resting on. the frame
    cancels those components, so they do not count as imbalance.
    """
    half = np.array([width / 2, height / 2])
    projected = forces.copy()
    # each test works coordinate by coordinate: x against the left and right
    # edges, y against the bottom and top edges
    projected[(positions >= half) & (projected > 0)] = 0.0
    projected[(positions <= -half) & (projected < 0)] = 0.0
    return np.max(np.linalg.norm(projected, axis=1))


def stiffness(positions, adjacency, k, min_distance, gravity=0.0):
    """
    how stiff each node is: an upper estimate of the curvature of the energy
    around that node,

      stiffness_v = sum over neighbours of 2 d / k  +  sum over all u of k**2 / d**2
                    + gravity

    each term is the curvature along the line joining the pair: 2 d / k for a
    spring (second derivative of d**3 / 3k) and k**2 / d**2 for the repulsion
    (second derivative of -k**2 ln d). the gravity energy (gravity / 2)|x|**2
    has curvature gravity in every direction. a hub with many springs is
    stiff; a leaf is soft. for two nodes at distance k without gravity the
    stiffness is 2 + 1 = 3.
    """
    _, dist = pairwise(positions, min_distance)
    repulsion = k**2 / dist**2
    np.fill_diagonal(repulsion, 0.0)
    springs = adjacency * 2 * dist / k
    return springs.sum(axis=1) + repulsion.sum(axis=1) + gravity


def move(positions, forces, temperature, width, height, step_size):
    """
    one position update: node v moves in the direction of its force by
    min(step_size[v] * |force_v|, temperature), then is clamped to the frame.

    step_size has one value per node (see run_simulation). using the force
    itself as the step (step_size = 1, the original method) overshoots: for
    two nodes the error near equilibrium is multiplied by -5 each step.
    """
    length = np.linalg.norm(forces, axis=1)
    step = np.minimum(step_size * length, temperature)

    # direction = force / length; a node with zero force does not move,
    # so replace its length by 1 to avoid dividing by zero
    safe_length = np.where(length > 0, length, 1.0)
    direction = forces / safe_length[:, np.newaxis]

    new_positions = positions + direction * step[:, np.newaxis]

    half = np.array([width / 2, height / 2])
    return np.clip(new_positions, -half, half)


def run_simulation(adjacency, width=1.0, height=1.0, c=0.3, positions=None,
                   initial_temperature=None, cooling=1.0, damping=0.9,
                   gravity=1.0, tolerance=1e-3, max_iterations=10000, seed=0):
    """
    run the simulation until the residual force drops below tolerance * k,
    or until max_iterations is reached.

    c                    scale of k; values below 1 make the layout smaller
                         than the frame, so weakly connected nodes are not
                         pushed against the walls
    positions            starting layout; random inside the frame if None
    initial_temperature  largest first step; width / 10 if None, as in the
                         original Fruchterman and Reingold paper
    cooling              factor that multiplies the temperature each iteration.
                         1.0 keeps it constant: with per-node steps the
                         iteration is already stable, so the temperature only
                         limits the large jumps of the first iterations, and
                         letting it shrink to zero freezes the layout
    damping              each node's step is damping / stiffness_v. the step
                         is stable when the largest curvature of the rescaled
                         problem times damping is below 2; that curvature is
                         at most 2 (gershgorin circle theorem), so any
                         damping below 1 is safe
    gravity              strength g of the central pull - g * x_v. separate
                         components settle at a distance of about c / sqrt(g)
                         from the center, whatever the number of nodes
    tolerance            convergence threshold as a fraction of k

    returns a dictionary with the final positions, k, whether it converged,
    and the history of every iteration (for plots and the animation).
    """
    n = len(adjacency)
    k = ideal_distance(n, width, height, c)
    min_distance = 1e-9 * k
    half = np.array([width / 2, height / 2])

    if positions is None:
        # a fixed seed gives the same starting layout every run
        rng = np.random.default_rng(seed)
        positions = rng.uniform(-half, half, size=(n, 2))
    positions = np.array(positions, dtype=float)

    temperature = width / 10 if initial_temperature is None else initial_temperature

    history = {"positions": [], "energy": [], "residual": [], "temperature": []}
    converged = False

    # the loop counter itself is not needed, so it is named _
    for _ in range(max_iterations):
        forces = net_forces(positions, adjacency, k, min_distance, gravity)
        residual = residual_force(positions, forces, width, height)

        # record the state before moving, so entry i describes layout i
        history["positions"].append(positions.copy())
        history["energy"].append(
            energy(positions, adjacency, k, min_distance, gravity))
        history["residual"].append(residual)
        history["temperature"].append(temperature)

        if residual < tolerance * k:
            converged = True
            break

        # stiff nodes (hubs) take small steps, soft nodes (leaves) large ones
        step_size = damping / stiffness(positions, adjacency, k, min_distance,
                                        gravity)
        positions = move(positions, forces, temperature, width, height, step_size)
        temperature *= cooling

    return {
        "positions": positions,
        "k": k,
        "converged": converged,
        "iterations": len(history["energy"]),
        "history": {name: np.array(values) for name, values in history.items()},
    }
