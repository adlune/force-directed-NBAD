"""
energy_valley.py

draws the energy landscape of a small example, to show that the simulation
walks downhill on the energy until it reaches the bottom of a valley (the
same idea as gradient descent). one free node is linked to two fixed nodes,
so the energy depends only on the free node's (x, y) and can be drawn as a
surface. the paths use the same forces, step sizes and moves as the real
simulation.

usage:
  python src/energy_valley.py     # writes docs/figures/energy_valley.png
"""

import matplotlib
matplotlib.use("Agg")   # draw to files only; no window is needed
import matplotlib.pyplot as plt
import numpy as np

import theme
from force_simulation import energy, move, net_forces, pairwise, stiffness

theme.apply()

k = 1.0                                     # lengths are measured in units of k
fixed = np.array([[-0.6, 0.0], [0.6, 0.0]])
# the free node is the last one, linked to both fixed nodes
adjacency = np.array([[0, 0, 1], [0, 0, 1], [1, 1, 0]])
min_distance = 1e-9
temperature = 0.3                           # step cap, as in the simulation
frame = 10.0                                # large enough never to clamp


def energy_at(point):
    """energy of the three nodes when the free node is at point."""
    positions = np.vstack([fixed, point])
    _, dist = pairwise(positions, min_distance)
    return energy(positions, dist, adjacency, k)


def descend(start, tolerance=1e-3, max_steps=500):
    """
    move the free node with the simulation's update rule until its force is
    below tolerance * k, and return the path. the fixed nodes are put back
    after every move.
    """
    positions = np.vstack([fixed, start])
    path = [positions[2].copy()]
    for _ in range(max_steps):
        diff, dist = pairwise(positions, min_distance)
        forces = net_forces(positions, diff, dist, adjacency, k)
        if np.linalg.norm(forces[2]) < tolerance * k:
            break
        step_size = 0.9 / stiffness(dist, adjacency, k)
        positions = move(positions, forces, temperature, frame, frame, step_size)
        positions[:2] = fixed
        path.append(positions[2].copy())
    return np.array(path)


def draw():
    # the energy on a grid, measured from the bottom of the valleys. the
    # energy rises without limit near the fixed nodes (repulsion) and far
    # away (springs), so it is cut at a ceiling to keep the valleys visible
    bottom = energy_at(np.array([0.0, 0.8 * k]))
    ceiling = 3.0
    x, y = np.meshgrid(np.linspace(-1.6, 1.6, 129), np.linspace(-1.6, 1.6, 129))
    height = np.array([[energy_at(np.array([a, b])) for a, b in zip(row_x, row_y)]
                       for row_x, row_y in zip(x, y)]) - bottom
    height = np.minimum(height, ceiling)

    # two ordinary starts, and one that begins next to the saddle
    paths = [descend(np.array(start)) for start in [(-1.2, 1.2), (1.2, -1.15),
                                                    (0.35, 0.001)]]

    fig = plt.figure(figsize=(12, 5))
    surface_ax = fig.add_subplot(1, 2, 1, projection="3d")
    map_ax = fig.add_subplot(1, 2, 2)

    # left: the landscape as a surface, shaded light gray, with the paths
    # drawn slightly above it so the surface does not hide them
    surface_ax.plot_surface(x, y, height, color=theme.gray_100,
                            edgecolor=theme.gray_300, linewidth=0.25,
                            rstride=4, cstride=4, shade=True, alpha=0.95)
    for p in paths:
        z = np.array([energy_at(q) for q in p]) - bottom + 0.04
        surface_ax.plot(p[:, 0], p[:, 1], z, color=theme.ink, linewidth=1.2,
                        marker="o", markersize=2.5, zorder=5)
    surface_ax.view_init(elev=32, azim=-58)
    surface_ax.set_xlabel("x / k")
    surface_ax.set_ylabel("y / k")
    surface_ax.set_zlabel("E − E_min")
    surface_ax.set_xticks([-1, 0, 1])
    surface_ax.set_yticks([-1, 0, 1])
    surface_ax.set_zticks([0, 1, 2, 3])
    for axis in (surface_ax.xaxis, surface_ax.yaxis, surface_ax.zaxis):
        axis.pane.set_visible(False)
        axis._axinfo["grid"]["color"] = theme.hairline
    surface_ax.set_title("The energy landscape")

    # right: the same landscape seen from above, as contour lines
    levels = [0.02, 0.1, 0.25, 0.5, 0.8, 1.2, 1.7, 2.3]
    map_ax.contour(x, y, height, levels=levels, colors=theme.gray_500,
                   linewidths=0.7)
    for p in paths:
        map_ax.plot(p[:, 0], p[:, 1], color=theme.ink, linewidth=1.2,
                    marker="o", markersize=3)
    map_ax.scatter(fixed[:, 0], fixed[:, 1], s=60, color=theme.node_color,
                   zorder=4)
    # a white box behind each label keeps it readable over the contour lines
    note = dict(color=theme.ink_secondary, fontsize=9, ha="center", zorder=6,
                bbox=dict(facecolor=theme.surface, edgecolor="none", pad=1))
    map_ax.text(0, 0.8 * k + 0.12, "valley", va="bottom", **note)
    map_ax.text(0, -0.8 * k - 0.12, "valley", va="top", **note)
    map_ax.text(0, -0.12, "saddle", va="top", **note)
    for point in fixed:
        map_ax.text(point[0], -0.18, "fixed node", va="top", **note)
    map_ax.set_aspect("equal")
    map_ax.set_xlabel("x / k")
    map_ax.set_ylabel("y / k")
    map_ax.grid(False)
    theme.style_axis(map_ax, "Seen from above, with the steps of the simulation")

    fig.text(0.015, 0.97, "Equilibrium is the bottom of an energy valley",
             fontsize=14, fontweight="semibold", color=theme.ink, va="top")
    fig.text(0.015, 0.905, "one node linked to two fixed nodes; each dot is "
             "one iteration, moving downhill until the force is zero",
             fontsize=10, color=theme.ink_secondary, va="top")
    fig.subplots_adjust(left=0.02, right=0.98, top=0.8, bottom=0.1, wspace=0.12)
    fig.savefig("docs/figures/energy_valley.png", dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    draw()
