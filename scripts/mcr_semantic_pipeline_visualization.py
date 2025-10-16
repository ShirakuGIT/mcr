#!/usr/bin/env python3
"""Generate an intuitive semantic-weighted MCR explainer as SVG."""

from __future__ import annotations

from html import escape
import importlib.util
from pathlib import Path
import sys


def load_semantic_module():
    module_path = Path(__file__).resolve().parents[1] / "src" / "mcr" / "algorithms" / "semantic_mcr.py"
    spec = importlib.util.spec_from_file_location("semantic_mcr_local", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load semantic module from {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


semantic_mcr = load_semantic_module()
build_semantic_demo = semantic_mcr.build_semantic_demo
cardinality_mcr_greedy = semantic_mcr.cardinality_mcr_greedy
subset_label = semantic_mcr.subset_label
weighted_mcr_greedy = semantic_mcr.weighted_mcr_greedy


DARK = "#101418"
PANEL = "#171d23"
GRID = "#2e3842"
TEXT = "#e6edf3"
MUTED = "#9fb0c0"
GREEN = "#4ade80"
RED = "#f87171"
BLUE = "#60a5fa"
YELLOW = "#fbbf24"

WIDTH = 1600
HEIGHT = 1000
OUTPUT_DIR = Path("outputs/mcr_semantic_explainer")


def svg_text(x, y, text, size=18, color=TEXT, weight="normal"):
    return (
        f'<text x="{x}" y="{y}" fill="{color}" font-size="{size}" '
        f'font-family="monospace" font-weight="{weight}">{escape(text)}</text>'
    )


def svg_multiline_text(x, y, lines, size=18, color=TEXT, line_gap=24, weight="normal"):
    chunks = [
        f'<text x="{x}" y="{y}" fill="{color}" font-size="{size}" '
        f'font-family="monospace" font-weight="{weight}">'
    ]
    for index, line in enumerate(lines):
        dy = 0 if index == 0 else line_gap
        chunks.append(
            f'<tspan x="{x}" dy="{dy}">{escape(line)}</tspan>'
        )
    chunks.append("</text>")
    return "".join(chunks)


def wrap_lines(text, width):
    words = text.split()
    if not words:
        return [""]
    lines = []
    current = words[0]
    for word in words[1:]:
        candidate = f"{current} {word}"
        if len(candidate) <= width:
            current = candidate
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def path_edges(path):
    return set(zip(path[:-1], path[1:])) | set(zip(path[1:], path[:-1]))


def panel(x, y, w, h, title):
    return [
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="18" fill="{PANEL}" stroke="{GRID}" stroke-width="2"/>',
        svg_text(x + 24, y + 40, title, size=24, weight="bold"),
    ]


def semantic_weight_of_result(result, objects):
    return sum(objects[obj].semantic_weight for obj in result["subset"])


def draw_graph(panel_x, panel_y, panel_w, panel_h, graph, positions, cover, objects, result, title):
    chunks = panel(panel_x, panel_y, panel_w, panel_h, title)
    graph_x = panel_x + 40
    graph_y = panel_y + 80
    graph_w = panel_w - 80
    graph_h = 260
    x_values = [pos[0] for pos in positions.values()]
    y_values = [pos[1] for pos in positions.values()]
    min_x, max_x = min(x_values), max(x_values)
    min_y, max_y = min(y_values), max(y_values)

    def map_point(name):
        raw_x, raw_y = positions[name]
        px = graph_x + ((raw_x - min_x) / (max_x - min_x)) * graph_w
        py = graph_y + graph_h - ((raw_y - min_y) / (max_y - min_y)) * graph_h
        return px, py

    highlighted = path_edges(result["path"])
    seen_edges = set()
    for left, neighbors in graph.items():
        for right in neighbors:
            if (right, left) in seen_edges:
                continue
            seen_edges.add((left, right))
            x1, y1 = map_point(left)
            x2, y2 = map_point(right)
            edge_color = GREEN if (left, right) in highlighted else GRID
            edge_width = 6 if (left, right) in highlighted else 3
            chunks.append(
                f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{edge_color}" stroke-width="{edge_width}" stroke-linecap="round"/>'
            )

    for node in positions:
        px, py = map_point(node)
        node_color = YELLOW if node in {"start", "goal"} else BLUE
        chunks.append(
            f'<circle cx="{px}" cy="{py}" r="24" fill="{node_color}" stroke="{DARK}" stroke-width="3"/>'
        )
        name_lines = node.replace("_", " ").split()
        if len(name_lines) > 2:
            name_lines = [" ".join(name_lines[:2]), " ".join(name_lines[2:])]
        label_y = py - 34
        chunks.append(svg_multiline_text(px - 42, label_y, name_lines, size=14, weight="bold"))
        object_names = [objects[obj].display_name for obj in cover[node]]
        cover_lines = object_names if object_names else ["free"]
        chunks.append(svg_multiline_text(px - 56, py + 44, cover_lines, size=13, color=MUTED, line_gap=18))

    result_lines = [
        f"path: {' -> '.join(result['path'])}",
        f"collision set: {subset_label(result['subset'])}",
        "objects: " + ", ".join(objects[obj].display_name for obj in sorted(result["subset"])),
        f"collision count: {len(result['subset'])}",
        f"semantic weight: {semantic_weight_of_result(result, objects):.1f}",
    ]
    box_x = panel_x + 28
    box_y = panel_y + panel_h - 150
    box_w = panel_w - 56
    box_h = 118
    chunks.append(
        f'<rect x="{box_x}" y="{box_y}" width="{box_w}" height="{box_h}" rx="14" fill="{DARK}" stroke="{GRID}" stroke-width="2"/>'
    )
    chunks.append(svg_multiline_text(box_x + 18, box_y + 32, result_lines, size=17, line_gap=24))
    return chunks


def draw_vlm_table(panel_x, panel_y, panel_w, panel_h, objects):
    chunks = panel(panel_x, panel_y, panel_w, panel_h, "1. VLM scene assessment to semantic weights")
    cursor_y = panel_y + 82
    for obj in objects.values():
        chunks.append(
            f'<rect x="{panel_x + 24}" y="{cursor_y - 24}" width="{panel_w - 48}" height="86" rx="12" fill="{DARK}" stroke="{GRID}" stroke-width="1.5"/>'
        )
        header = (
            f"{obj.display_name} | score={obj.safety_score:.2f} | "
            f"class={obj.category} | w={obj.semantic_weight:.1f}"
        )
        chunks.append(svg_text(panel_x + 42, cursor_y + 4, header, size=17, weight="bold"))
        rationale_lines = wrap_lines(obj.rationale, 66)
        chunks.append(
            svg_multiline_text(
                panel_x + 42,
                cursor_y + 32,
                rationale_lines,
                size=15,
                color=MUTED,
                line_gap=20,
            )
        )
        cursor_y += 100
    return chunks


def draw_history_note(panel_x, panel_y, panel_w, panel_h):
    chunks = panel(panel_x, panel_y, panel_w, panel_h, "4. Why history-dependent collisions change the state")
    lines = [
        "Professor's modification:",
        "The same roadmap vertex can have different collision sets depending",
        "on which path history reached it.",
        "",
        "That means state is no longer just vertex v.",
        "It becomes (v, accumulated_collision_set).",
        "",
        "Greedy danger:",
        "If you keep only one best subset at each vertex, you may discard a",
        "history that looks slightly worse now but avoids a dangerous object later.",
        "",
        "Minimum correct change:",
        "Keep multiple non-dominated subsets per vertex.",
        "",
        "Practical approximation:",
        "Use beam search or bounded-frontier pruning with semantic cost.",
    ]
    chunks.append(svg_multiline_text(panel_x + 28, panel_y + 84, lines, size=18, line_gap=26))

    diagram_x = panel_x + 28
    diagram_y = panel_y + 360
    chunks.append(svg_text(diagram_x, diagram_y, "Example same-vertex ambiguity", size=20, weight="bold"))
    cx = diagram_x + 280
    cy = diagram_y + 90
    left_x = diagram_x + 90
    right_x = diagram_x + 500
    bottom_y = diagram_y + 200
    for x, y, label, color in [
        (left_x, cy, "history A", BLUE),
        (cx, cy, "same vertex v", YELLOW),
        (right_x, cy, "future", BLUE),
        (cx, bottom_y, "history B", RED),
    ]:
        chunks.append(f'<circle cx="{x}" cy="{y}" r="28" fill="{color}" stroke="{DARK}" stroke-width="3"/>')
        chunks.append(svg_text(x - 46, y + 54, label, size=15))
    for x1, y1, x2, y2, label in [
        (left_x + 30, cy, cx - 30, cy, "{towel}"),
        (cx + 30, cy, right_x - 30, cy, "+ knife block"),
        (cx, bottom_y - 30, cx, cy + 30, "{box}"),
    ]:
        chunks.append(
            f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{GRID}" stroke-width="4" stroke-linecap="round"/>'
        )
        chunks.append(svg_text((x1 + x2) / 2 - 34, (y1 + y2) / 2 - 10, label, size=14, color=MUTED))
    return chunks


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    graph, positions, cover, objects, weights, start, goal = build_semantic_demo()
    standard = cardinality_mcr_greedy(graph, cover, start, goal)
    semantic = weighted_mcr_greedy(graph, cover, weights, start, goal)

    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" fill="none">',
        f'<rect width="{WIDTH}" height="{HEIGHT}" fill="{DARK}"/>',
        svg_text(40, 40, "Semantic-Weighted MCR Pipeline", size=30, weight="bold"),
        svg_text(40, 72, "VLM assessment -> semantic weights -> path-level collision cost", size=18, color=MUTED),
    ]
    svg.extend(draw_vlm_table(30, 100, 740, 390, objects))
    svg.extend(draw_graph(800, 100, 770, 390, graph, positions, cover, objects, standard, "2. Standard MCR minimizes number of collided objects"))
    svg.extend(draw_graph(30, 530, 740, 430, graph, positions, cover, objects, semantic, "3. Semantic MCR minimizes total semantic consequence"))
    svg.extend(draw_history_note(800, 530, 770, 430))
    svg.append("</svg>")

    svg_path = OUTPUT_DIR / "semantic_mcr_pipeline.svg"
    svg_path.write_text("\n".join(svg), encoding="utf-8")

    summary_lines = [
        "# Semantic MCR Run",
        "",
        f"- Standard path: {' -> '.join(standard['path'])}",
        f"- Standard subset: {subset_label(standard['subset'])}",
        f"- Standard collision count: {len(standard['subset'])}",
        f"- Standard semantic weight: {semantic_weight_of_result(standard, objects):.1f}",
        f"- Semantic path: {' -> '.join(semantic['path'])}",
        f"- Semantic subset: {subset_label(semantic['subset'])}",
        f"- Semantic collision count: {len(semantic['subset'])}",
        f"- Semantic semantic weight: {semantic_weight_of_result(semantic, objects):.1f}",
        "",
        "Interpretation:",
        "- Standard MCR prefers fewer collisions even if they are semantically severe.",
        "- Semantic MCR prefers more benign collisions if their total consequence is lower.",
        "- With history-dependent collision sets, one subset per vertex is not generally sufficient.",
    ]
    (OUTPUT_DIR / "semantic_mcr_pipeline_summary.md").write_text(
        "\n".join(summary_lines),
        encoding="utf-8",
    )

    print(f"Saved semantic explainer to {svg_path}")
    print(
        f"Standard path: {' -> '.join(standard['path'])}  "
        f"subset={subset_label(standard['subset'])}  "
        f"count={len(standard['subset'])}  semantic_weight={semantic_weight_of_result(standard, objects):.1f}"
    )
    print(
        f"Semantic path: {' -> '.join(semantic['path'])}  "
        f"subset={subset_label(semantic['subset'])}  "
        f"count={len(semantic['subset'])}  semantic_weight={semantic_weight_of_result(semantic, objects):.1f}"
    )


if __name__ == "__main__":
    main()
