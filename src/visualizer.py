"""
visualizer.py

pictures of a simulation run (the dictionary returned by run_simulation),
drawn with the shared look from theme.py:
  plot_convergence  static figure: energy and residual force vs iteration
  animate           GIF: the layout moving, next to the two curves with a
                    marker showing the current iteration

energy and residual force have different units and scales, so each gets its
own panel instead of sharing one plot with two y-axes. the residual is shown
divided by k on a logarithmic axis, next to the convergence threshold.
in the layout, node size and shade both grow with the number of connections.
"""

import sys

import matplotlib
matplotlib.use("Agg")   # draw to files only; no window is needed
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation, PillowWriter
from matplotlib.collections import LineCollection
from matplotlib.patches import Rectangle

import theme

theme.apply()


def edge_segments(positions, adjacency):
    """
    one line segment per edge, shape (m, 2, 2): segment e goes from
    positions[rows[e]] to positions[cols[e]]. np.triu keeps each edge once.
    """
    rows, cols = np.nonzero(np.triu(adjacency))
    return np.stack([positions[rows], positions[cols]], axis=1)


def status_text(result):
    if result["converged"]:
        return f"converged after {result['iterations']:,} iterations"
    return f"not converged after {result['iterations']:,} iterations"


def add_titles(fig, title, result):
    """main title in dark ink, the convergence status below it in gray."""
    fig.text(0.015, 0.965, title, fontsize=14, fontweight="semibold",
             color=theme.ink, va="top")
    fig.text(0.015, 0.905, status_text(result), fontsize=10,
             color=theme.ink_secondary, va="top")


def energy_gap(energy):
    """
    E - E_final for every iteration, for plotting on a log scale. early
    changes are thousands of times larger than late ones, so on a linear
    axis everything after the first few iterations looks flat; the log
    scale shows each factor of 10 with the same height. values that are not
    positive (the last point, which is exactly 0, and any brief dip below
    the final value) cannot be shown on a log axis and become nan (not a
    number), which matplotlib leaves as a gap.
    """
    gap = energy - energy[-1]
    return np.where(gap > 0, gap, np.nan)


def draw_curves(ax_energy, ax_residual, result, tolerance=1e-3):
    """draw the energy and residual curves; used by both figure types."""
    history = result["history"]
    iterations = np.arange(len(history["energy"]))
    residual_over_k = history["residual"] / result["k"]

    ax_energy.semilogy(iterations, energy_gap(history["energy"]),
                       color=theme.line_color)
    theme.style_axis(ax_energy, "Energy above final value  E − E_final")
    ax_energy.set_xlabel("iteration")
    ax_energy.margins(x=0)

    ax_residual.semilogy(iterations, residual_over_k, color=theme.line_color)
    # the threshold is a real reference value: dashed line plus a label
    ax_residual.axhline(tolerance, color=theme.ink_muted, linewidth=1,
                        linestyle=(0, (4, 3)))
    # the label sits at the left end, where the curve is still far above it
    # (the curve meets the threshold at the right end when the run converges)
    ax_residual.annotate("convergence threshold", xy=(0, tolerance),
                         xycoords=("axes fraction", "data"),
                         xytext=(4, 5), textcoords="offset points",
                         ha="left", color=theme.ink_secondary, fontsize=8.5)
    theme.style_axis(ax_residual, "Residual force  R / k")
    ax_residual.set_xlabel("iteration")
    ax_residual.margins(x=0)


def plot_convergence(result, path, title):
    """save the static convergence figure (the course deliverable)."""
    fig, (ax_energy, ax_residual) = plt.subplots(1, 2, figsize=(11, 4.4))
    draw_curves(ax_energy, ax_residual, result)
    add_titles(fig, title, result)
    fig.tight_layout(rect=(0, 0, 1, 0.86), w_pad=3)
    fig.savefig(path, dpi=150)
    plt.close(fig)


def animate(result, adjacency, path, title, width=1.0, height=1.0,
            max_frames=150, fps=24, largest_node=45.0):
    """
    save a GIF of the run. long runs are subsampled to at most max_frames
    frames; the frames are spaced evenly on a logarithmic scale of the
    iteration number, because most of the motion happens early.
    """
    history = result["history"]
    n_iterations = len(history["energy"])
    frames = np.unique(np.geomspace(1, n_iterations, max_frames).astype(int) - 1)

    fig = plt.figure(figsize=(12, 6))
    # layout on the left, the two curves stacked on the right
    grid = fig.add_gridspec(2, 2, width_ratios=[1.15, 1], hspace=0.55,
                            left=0.02, right=0.98, top=0.84, bottom=0.09)
    ax_layout = fig.add_subplot(grid[:, 0])
    ax_energy = fig.add_subplot(grid[0, 1])
    ax_residual = fig.add_subplot(grid[1, 1])

    # the layout panel: frame, edges, nodes; no axes or grid
    ax_layout.add_patch(Rectangle((-width / 2, -height / 2), width, height,
                                  fill=False, edgecolor=theme.frame_color,
                                  linewidth=1))
    margin = 0.02 * width
    ax_layout.set_xlim(-width / 2 - margin, width / 2 + margin)
    ax_layout.set_ylim(-height / 2 - margin, height / 2 + margin)
    ax_layout.set_aspect("equal")
    ax_layout.axis("off")

    sizes, order = theme.node_sizes(adjacency, largest=largest_node)
    first = history["positions"][0]
    edges = LineCollection(edge_segments(first, adjacency),
                           colors=theme.edge_color, linewidths=0.6)
    ax_layout.add_collection(edges)
    # hubs are drawn last so they sit on top of their leaves; the thin white
    # outline keeps overlapping nodes distinguishable
    nodes = ax_layout.scatter(first[order, 0], first[order, 1],
                              s=sizes[order], color=theme.node_color,
                              edgecolors=theme.surface, linewidths=0.4, zorder=3)
    iteration_label = ax_layout.text(width / 2, height / 2 + margin, "",
                                     ha="right", va="bottom",
                                     color=theme.ink_secondary, fontsize=10)
    ax_layout.text(width / 2, -height / 2 - 2 * margin,
                   "node size: number of connections",
                   ha="right", va="top", color=theme.ink_muted, fontsize=8.5)

    # the curve panels, with a marker that follows the current iteration
    draw_curves(ax_energy, ax_residual, result)
    residual_over_k = history["residual"] / result["k"]
    gap = energy_gap(history["energy"])
    marker_style = dict(marker="o", markersize=7, color=theme.marker_color,
                        markeredgecolor=theme.surface, markeredgewidth=1.5,
                        zorder=4)
    energy_marker, = ax_energy.plot([], [], **marker_style)
    residual_marker, = ax_residual.plot([], [], **marker_style)

    add_titles(fig, title, result)

    def update(i):
        # called once per frame with the iteration number to show
        positions = history["positions"][i]
        edges.set_segments(edge_segments(positions, adjacency))
        nodes.set_offsets(positions[order])
        energy_marker.set_data([i], [gap[i]])
        residual_marker.set_data([i], [residual_over_k[i]])
        iteration_label.set_text(f"iteration {i:,}")
        return edges, nodes, energy_marker, residual_marker, iteration_label

    animation = FuncAnimation(fig, update, frames=frames, blit=False)
    animation.save(path, writer=PillowWriter(fps=fps), dpi=90)
    plt.close(fig)


if __name__ == "__main__":
    # demo: the two-clique graph and one real Monday window, saved in results/
    #   python src/visualizer.py
    from pathlib import Path

    import pandas as pd

    from example_graphs import two_cliques
    from force_simulation import run_simulation
    from graph_builder import build_graph, flows_in_window, load_flows

    out = Path("results")
    out.mkdir(exist_ok=True)

    cliques = two_cliques()
    result = run_simulation(cliques)
    plot_convergence(result, out / "two_cliques_convergence.png", "Two cliques")
    animate(result, cliques, out / "two_cliques.gif", "Two cliques",
            largest_node=90.0)
    print("two cliques:", status_text(result))

    flows = load_flows("data/raw/Monday-WorkingHours.pcap_ISCX.csv")
    _, window = build_graph(flows_in_window(flows, pd.Timestamp("2017-07-03 10:00")))
    result = run_simulation(window)
    plot_convergence(result, out / "monday_1000_convergence.png", "Monday, 10:00 window")
    animate(result, window, out / "monday_1000.gif", "Monday, 10:00 window")
    print("monday 10:00:", status_text(result))
    sys.exit(0)
