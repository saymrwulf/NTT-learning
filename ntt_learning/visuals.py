"""Blunt visual helpers for the NTT notebooks."""

from __future__ import annotations

from typing import Sequence

import ipywidgets as widgets
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from IPython.display import clear_output, display

from .toy_ntt import TransformStage, TransformTrace, pairwise_product_grid, wraparound_contributions


def _value_colors(values: Sequence[int]) -> list[str]:
    colors = []
    for value in values:
        if value < 0:
            colors.append("#f08a5d")
        elif value == 0:
            colors.append("#d9d9d9")
        else:
            colors.append("#7ad3a8")
    return colors


def _draw_value_row(ax, values: Sequence[int], y: float, prefix: str) -> None:
    colors = _value_colors(values)
    for index, (value, color) in enumerate(zip(values, colors)):
        ax.text(
            index,
            y,
            f"{prefix}{index}\n{value}",
            ha="center",
            va="center",
            fontsize=10,
            family="monospace",
            bbox={
                "boxstyle": "round,pad=0.35",
                "facecolor": color,
                "edgecolor": "#222222",
                "linewidth": 1.2,
            },
        )


def plot_convolution_grid(
    left: Sequence[int], right: Sequence[int], title: str = "Schoolbook Product Grid"
):
    """Plot the full schoolbook multiplication table and the diagonal sums."""
    grid = pairwise_product_grid(left, right)
    diagonal_sums = []
    for diagonal in range(len(left) + len(right) - 1):
        total = 0
        for row in range(len(left)):
            column = diagonal - row
            if 0 <= column < len(right):
                total += grid[row][column]
        diagonal_sums.append(total)

    fig, axes = plt.subplots(2, 1, figsize=(max(7, len(right) * 1.2), 6), height_ratios=[3, 1])
    heatmap_ax, sum_ax = axes

    heatmap_ax.imshow(grid, cmap="YlGnBu", aspect="auto")
    heatmap_ax.set_title(title, fontsize=14, fontweight="bold")
    heatmap_ax.set_xlabel("right coefficient index")
    heatmap_ax.set_ylabel("left coefficient index")
    heatmap_ax.set_xticks(range(len(right)))
    heatmap_ax.set_yticks(range(len(left)))

    for row, row_values in enumerate(grid):
        for column, value in enumerate(row_values):
            heatmap_ax.text(column, row, str(value), ha="center", va="center", color="#101010", fontsize=10)

    sum_ax.axis("off")
    sum_ax.set_title("Diagonal Sums = Convolution Coefficients", fontsize=12, fontweight="bold", pad=8)
    for index, value in enumerate(diagonal_sums):
        sum_ax.text(
            index,
            0,
            f"y{index}\n{value}",
            ha="center",
            va="center",
            fontsize=10,
            family="monospace",
            bbox={
                "boxstyle": "round,pad=0.35",
                "facecolor": "#f4f1de",
                "edgecolor": "#222222",
                "linewidth": 1.0,
            },
        )
    sum_ax.set_xlim(-0.5, len(diagonal_sums) - 0.5)
    sum_ax.set_ylim(-1, 1)
    fig.tight_layout()
    return fig


def plot_wraparound(
    coefficients: Sequence[int],
    n: int,
    *,
    negacyclic: bool = True,
    title: str | None = None,
):
    """Plot how the tail wraps back into degree < n."""
    rows = wraparound_contributions(coefficients, n=n, negacyclic=negacyclic)
    if title is None:
        title = "Negacyclic Folding" if negacyclic else "Cyclic Folding"

    fig, ax = plt.subplots(figsize=(max(8, len(coefficients) * 1.1), 5.5))
    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.axis("off")

    top_y = 2.4
    bottom_y = 0.4
    _draw_value_row(ax, coefficients, top_y, "x^")
    reduced_values = [row["total"] for row in rows]
    _draw_value_row(ax, reduced_values, bottom_y, "slot ")

    for slot, row in enumerate(rows):
        for contribution in row["contributions"]:
            source_index = contribution["source_index"]
            color = "#d1495b" if contribution["sign"] < 0 else "#2a9d8f"
            label = "-" if contribution["sign"] < 0 else "+"
            ax.annotate(
                "",
                xy=(slot, bottom_y + 0.3),
                xytext=(source_index, top_y - 0.25),
                arrowprops={"arrowstyle": "->", "color": color, "linewidth": 2.0},
            )
            mid_x = (slot + source_index) / 2
            mid_y = (top_y + bottom_y) / 2 + 0.25
            ax.text(
                mid_x,
                mid_y,
                f"{label} wrap {contribution['wraps']}",
                ha="center",
                va="center",
                fontsize=9,
                color=color,
                family="monospace",
            )

    ax.set_xlim(-0.8, max(len(coefficients), n) - 0.2)
    ax.set_ylim(-0.4, 3.2)
    fig.tight_layout()
    return fig


def plot_bit_reversal_mapping(length: int, title: str = "Normal Order To Bit-Reversed Order"):
    """Plot the bit-reversal permutation as explicit wires."""
    if length <= 0 or length & (length - 1):
        raise ValueError("plot_bit_reversal_mapping requires a power-of-two length")

    from .toy_ntt import bit_reversed_indices

    permutation = bit_reversed_indices(length)
    width = length.bit_length() - 1

    fig, ax = plt.subplots(figsize=(8, max(4, length * 0.65)))
    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.axis("off")

    for index, target in enumerate(permutation):
        ax.text(
            0,
            -index,
            f"{index:>2} | {index:0{width}b}",
            ha="center",
            va="center",
            family="monospace",
            bbox={"boxstyle": "round,pad=0.25", "facecolor": "#edf6f9", "edgecolor": "#264653"},
        )
        ax.text(
            4,
            -target,
            f"{target:>2} | {target:0{width}b}",
            ha="center",
            va="center",
            family="monospace",
            bbox={"boxstyle": "round,pad=0.25", "facecolor": "#fff3b0", "edgecolor": "#9c6644"},
        )
        ax.plot([0.6, 3.4], [-index, -target], color="#7f5539", linewidth=2.2, alpha=0.9)

    ax.text(0, 1, "NO", ha="center", va="center", fontsize=12, fontweight="bold")
    ax.text(4, 1, "BO", ha="center", va="center", fontsize=12, fontweight="bold")
    ax.set_xlim(-1.2, 5.2)
    ax.set_ylim(-length + 0.2, 1.8)
    fig.tight_layout()
    return fig


def plot_stage(stage: TransformStage, title: str | None = None):
    """Plot one explicit butterfly stage with input and output rows."""
    if title is None:
        title = f"{stage.algorithm.upper()} Stage {stage.stage_index}"

    fig, ax = plt.subplots(figsize=(max(8, len(stage.input_values) * 1.35), 5.8))
    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.axis("off")

    input_y = 2.6
    output_y = 0.5
    _draw_value_row(ax, stage.input_values, input_y, "i")
    _draw_value_row(ax, stage.output_values, output_y, "o")

    colors = ["#264653", "#2a9d8f", "#e76f51", "#8d99ae", "#c1121f", "#3a86ff"]
    for pair_index, ((left, right), zeta) in enumerate(zip(stage.pairings, stage.zetas)):
        color = colors[pair_index % len(colors)]
        center_x = (left + right) / 2
        ax.plot([left, right], [input_y - 0.45, input_y - 0.45], color=color, linewidth=2.5)
        ax.plot([left, left], [input_y - 0.45, output_y + 0.55], color=color, linewidth=1.5, alpha=0.85)
        ax.plot([right, right], [input_y - 0.45, output_y + 0.55], color=color, linewidth=1.5, alpha=0.85)
        ax.text(
            center_x,
            1.55,
            f"pair {left}-{right}\nzeta={zeta}",
            ha="center",
            va="center",
            fontsize=10,
            family="monospace",
            bbox={
                "boxstyle": "round,pad=0.35",
                "facecolor": "#ffffff",
                "edgecolor": color,
                "linewidth": 1.4,
            },
        )

    ax.text(
        len(stage.input_values) / 2 - 0.5,
        -0.05,
        stage.note,
        ha="center",
        va="center",
        fontsize=10,
        color="#333333",
    )
    ax.set_xlim(-0.8, len(stage.input_values) - 0.2)
    ax.set_ylim(-0.5, 3.3)
    fig.tight_layout()
    return fig


def plot_trace_overview(trace: TransformTrace, title: str | None = None):
    """Plot every stage output as a column of values."""
    if title is None:
        title = f"{trace.algorithm.upper()} Trace Overview"

    columns = [trace.input_values] + [stage.output_values for stage in trace.stages]
    fig, ax = plt.subplots(figsize=(max(9, len(columns) * 2.0), max(4.5, len(trace.input_values) * 0.7)))
    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.axis("off")

    for column_index, values in enumerate(columns):
        x = column_index * 2.0
        for row_index, value in enumerate(values):
            ax.text(
                x,
                -row_index,
                str(value),
                ha="center",
                va="center",
                fontsize=10,
                family="monospace",
                bbox={
                    "boxstyle": "round,pad=0.25",
                    "facecolor": _value_colors([value])[0],
                    "edgecolor": "#222222",
                    "linewidth": 1.0,
                },
            )
        if column_index == 0:
            label = "input"
        else:
            label = f"stage {column_index}"
        ax.text(x, 1, label, ha="center", va="center", fontsize=11, fontweight="bold")

    ax.set_xlim(-1.0, (len(columns) - 1) * 2.0 + 1.0)
    ax.set_ylim(-len(trace.input_values) + 0.2, 1.8)
    fig.tight_layout()
    return fig


def interactive_trace(trace: TransformTrace, title: str | None = None):
    """Return a slider-based stage explorer for a transform trace."""
    if title is None:
        title = f"{trace.algorithm.upper()} Stage Explorer"

    slider = widgets.IntSlider(
        value=1,
        min=1,
        max=max(1, len(trace.stages)),
        step=1,
        description="Stage",
        continuous_update=False,
    )
    output = widgets.Output()

    def render(stage_index: int) -> None:
        with output:
            clear_output(wait=True)
            stage = trace.stages[stage_index - 1]
            fig = plot_stage(stage, title=f"{title} | Stage {stage_index}")
            display(fig)
            plt.close(fig)
            rows = []
            for pair, zeta in zip(stage.pairings, stage.zetas):
                left, right = pair
                rows.append(
                    f"pair {pair}: inputs=({stage.input_values[left]}, {stage.input_values[right]}) "
                    f"-> outputs=({stage.output_values[left]}, {stage.output_values[right]}) | zeta={zeta}"
                )
            print("\n".join(rows))

    slider.observe(lambda change: render(change["new"]), names="value")
    render(slider.value)
    widget = widgets.VBox([widgets.HTML(f"<h4>{title}</h4>"), slider, output])
    return widget


def show_trace(trace: TransformTrace, title: str | None = None):
    """Display the interactive trace widget immediately."""
    widget = interactive_trace(trace, title=title)
    display(widget)
    return widget
