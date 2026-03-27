#!/usr/bin/env python3
"""Generate explanatory visualizations for the core discrete MCR problem."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx

from src.mcr.algorithms.discrete_mcr import (
    build_core_mcr_example,
    build_greedy_failure_example,
    exact_mcr_trace,
    greedy_mcr_trace,
    subset_label,
)


DARK = "#101418"
PANEL = "#171d23"
GRID = "#2e3842"
TEXT = "#e6edf3"
MUTED = "#9fb0c0"
GREEN = "#4ade80"
RED = "#f87171"
BLUE = "#60a5fa"
YELLOW = "#fbbf24"
PURPLE = "#c084fc"

plt.rcParams.update(
    {
        "figure.facecolor": DARK,
        "axes.facecolor": PANEL,
        "axes.edgecolor": GRID,
        "savefig.facecolor": DARK,
        "text.color": TEXT,
        "axes.labelcolor": TEXT,
        "xtick.color": MUTED,
        "ytick.color": MUTED,
        "font.family": "monospace",
    }
)


OUTPUT_DIR = Path("outputs/mcr_core_explainer")


def draw_graph(ax, graph, positions, cover, path=None, active_vertex=None, title=""):
    ax.set_title(title, fontsize=11, pad=8)
    ax.set_xticks([])
    ax.set_yticks([])
    for u, v in graph.edges():
        ax.plot(
            [positions[u][0], positions[v][0]],
            [positions[u][1], positions[v][1]],
            color=GRID,
            lw=2,
            zorder=1,
        )

    if path:
        for u, v in zip(path[:-1], path[1:]):
            ax.plot(
                [positions[u][0], positions[v][0]],
                [positions[u][1], positions[v][1]],
                color=GREEN,
                lw=4,
                zorder=2,
            )

    for node, (x, y) in positions.items():
        color = BLUE
        if node in {"s", "t"}:
            color = YELLOW
        if node == active_vertex:
            color = RED
        ax.scatter(x, y, s=460, c=color, edgecolors=DARK, linewidths=1.5, zorder=3)
        ax.text(x, y + 0.22, node, ha="center", fontsize=10, fontweight="bold")
        ax.text(x, y - 0.02, subset_label(cover[node]), ha="center", va="center", fontsize=8)


def draw_trace_table(ax, trace, step_index, title):
    ax.set_title(title, fontsize=11, pad=8)
    ax.axis("off")
    shown = trace[: step_index + 1]
    lines = []
    for step in shown[-8:]:
        lines.append(
            f"{step.step_index:02d}  expand {step.vertex:<2}  S={subset_label(step.subset)}"
        )
    ax.text(
        0.02,
        0.98,
        "\n".join(lines),
        va="top",
        fontsize=9,
        bbox=dict(fc=DARK, ec=GRID, pad=6),
    )


def draw_best_subsets(ax, best_subsets, title):
    ax.set_title(title, fontsize=11, pad=8)
    ax.axis("off")
    lines = []
    for node in sorted(best_subsets):
        subsets = best_subsets[node]
        rendered = ", ".join(subset_label(s) for s in subsets) if subsets else "-"
        lines.append(f"{node:<2}: {rendered}")
    ax.text(
        0.02,
        0.98,
        "\n".join(lines),
        va="top",
        fontsize=9,
        bbox=dict(fc=DARK, ec=GRID, pad=6),
    )


def save_iteration_figure(name, graph, positions, cover, result, algorithm_title):
    trace = result["trace"]
    chosen_steps = sorted(set([0, min(1, len(trace) - 1), min(3, len(trace) - 1), len(trace) - 1]))
    fig, axes = plt.subplots(2, len(chosen_steps), figsize=(4.5 * len(chosen_steps), 8))
    for col, step_index in enumerate(chosen_steps):
        step = trace[step_index]
        draw_graph(
            axes[0, col],
            graph,
            positions,
            cover,
            path=result["path"] if step_index == len(trace) - 1 else None,
            active_vertex=step.vertex,
            title=f"{algorithm_title} step {step_index}",
        )
        draw_trace_table(axes[1, col], trace, step_index, "Search expansions")
    fig.suptitle(
        f"{algorithm_title} on Discrete MCR\nFinal cover = {subset_label(result['goal_subset'])}   path = {' -> '.join(result['path'])}",
        fontsize=13,
        y=0.98,
    )
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    fig.savefig(OUTPUT_DIR / name, dpi=160, bbox_inches="tight")
    plt.close(fig)


def save_failure_comparison(name, graph, positions, cover, exact_result, greedy_result):
    fig, axes = plt.subplots(1, 2, figsize=(12, 5.5))
    draw_graph(
        axes[0],
        graph,
        positions,
        cover,
        path=exact_result["path"],
        title=f"Exact MCR   S={subset_label(exact_result['goal_subset'])}",
    )
    draw_graph(
        axes[1],
        graph,
        positions,
        cover,
        path=greedy_result["path"],
        title=f"Greedy MCR   S={subset_label(greedy_result['goal_subset'])}",
    )
    fig.suptitle(
        "Greedy Can Be Suboptimal\nThis is the paper’s key warning: locally smaller subsets can miss the globally best explanation.",
        fontsize=13,
        y=0.98,
    )
    fig.tight_layout(rect=[0, 0, 1, 0.94])
    fig.savefig(OUTPUT_DIR / name, dpi=160, bbox_inches="tight")
    plt.close(fig)


def save_summary_figure(name, exact_result, greedy_result):
    fig, ax = plt.subplots(figsize=(10, 4.5))
    ax.axis("off")
    lines = [
        "Core formulation from Hauser (2012)",
        "",
        "Continuous MCR:",
        "Find a path from qs to qg whose cover C(path) contains the fewest unique constraints.",
        "",
        "Discrete MCR:",
        "Each graph node v has a cover C[v].",
        "A path explanation is the union of all covers along that path.",
        "The objective is not shortest path length.",
        "The objective is to minimize | union_v in path C[v] |.",
        "",
        f"Core example exact result:  {subset_label(exact_result['goal_subset'])} via {' -> '.join(exact_result['path'])}",
        f"Core example greedy result: {subset_label(greedy_result['goal_subset'])} via {' -> '.join(greedy_result['path'])}",
        "",
        "Exact search keeps multiple irreducible subsets per vertex.",
        "Greedy search keeps only one best-so-far subset per vertex.",
        "That is why greedy is fast, but can fail on adversarial graphs.",
    ]
    ax.text(
        0.02,
        0.98,
        "\n".join(lines),
        va="top",
        fontsize=10,
        bbox=dict(fc=PANEL, ec=GRID, pad=8),
    )
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / name, dpi=160, bbox_inches="tight")
    plt.close(fig)


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    core_graph, core_positions, core_cover, start, goal = build_core_mcr_example()
    core_exact = exact_mcr_trace(core_graph, core_cover, start, goal)
    core_greedy = greedy_mcr_trace(core_graph, core_cover, start, goal)

    failure_graph, failure_positions, failure_cover, start, goal = build_greedy_failure_example()
    failure_exact = exact_mcr_trace(failure_graph, failure_cover, start, goal)
    failure_greedy = greedy_mcr_trace(failure_graph, failure_cover, start, goal)

    save_iteration_figure(
        "core_exact_iterations.png",
        core_graph,
        core_positions,
        core_cover,
        core_exact,
        "Exact search",
    )
    save_iteration_figure(
        "core_greedy_iterations.png",
        core_graph,
        core_positions,
        core_cover,
        core_greedy,
        "Greedy search",
    )
    save_failure_comparison(
        "greedy_failure_comparison.png",
        failure_graph,
        failure_positions,
        failure_cover,
        failure_exact,
        failure_greedy,
    )
    save_summary_figure("mcr_formulation_summary.png", core_exact, core_greedy)

    print(f"Saved visualizations to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
