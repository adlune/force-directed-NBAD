"""
theme.py

one shared look for every figure and animation in the project, in the style
of ForceAtlas2 drawings: black and white only. small solid black nodes, thin
light gray edges, black curves and text on a white surface, and quiet axes
so the data stands out.

usage:
    import theme
    theme.apply()                   # once, before creating figures
    theme.style_axis(ax, "title")   # for each plot panel
"""

import matplotlib as mpl
import numpy as np


# the gray scale, from white to black
white = "#ffffff"
gray_100 = "#f0f0f0"
gray_200 = "#e2e2e2"
gray_300 = "#cfcfcf"
gray_500 = "#8c8c8c"
gray_700 = "#4d4d4d"
black = "#111111"

# roles: which shade each kind of element uses
surface = white
ink = black                 # titles and main text
ink_secondary = gray_700    # labels and subtitles
ink_muted = gray_500        # tick marks and notes
hairline = gray_200         # grid lines

line_color = black          # curves
node_color = black          # every node
edge_color = gray_300       # graph edges, light so the nodes dominate
frame_color = gray_200      # the simulation frame
marker_color = black        # the current-iteration marker


def apply():
    """set matplotlib defaults so every figure starts with the theme."""
    mpl.rcParams.update({
        "figure.facecolor": surface,
        "axes.facecolor": surface,
        "savefig.facecolor": surface,
        "font.family": "sans-serif",
        "font.sans-serif": ["Segoe UI", "Helvetica Neue", "Arial", "DejaVu Sans"],
        "font.size": 10,
        "axes.titlesize": 11,
        "axes.titleweight": "semibold",
        "axes.titlecolor": ink,
        "axes.titlelocation": "left",
        "axes.titlepad": 10,
        "axes.labelcolor": ink_secondary,
        "axes.labelsize": 9,
        "axes.edgecolor": gray_300,
        "axes.linewidth": 0.8,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "axes.axisbelow": True,
        "grid.color": hairline,
        "grid.linewidth": 0.7,
        "xtick.color": ink_muted,
        "ytick.color": ink_muted,
        "xtick.labelcolor": ink_secondary,
        "ytick.labelcolor": ink_secondary,
        "xtick.labelsize": 8.5,
        "ytick.labelsize": 8.5,
        "xtick.major.size": 0,
        "ytick.major.size": 0,
        "lines.linewidth": 1.6,
        "lines.solid_capstyle": "round",
    })


def style_axis(ax, title):
    """title the panel and keep only the hairline grid on the y axis."""
    ax.set_title(title)
    ax.grid(axis="x", visible=False)


def node_sizes(adjacency, smallest=6.0, largest=45.0):
    """
    marker area of each node from its degree (number of connections).
    the scale uses the square root of the degree, because marker area grows
    with the square of its width; nodes stay small, and hubs are only
    moderately larger. returns the sizes and the drawing order (hubs last,
    on top of their leaves).
    """
    degree = adjacency.sum(axis=1)
    scaled = np.sqrt(degree) / np.sqrt(max(degree.max(), 1))
    sizes = smallest + (largest - smallest) * scaled
    order = np.argsort(degree)
    return sizes, order
