#!/usr/bin/env python3
"""Build a standalone side-by-side UI for comparing MCR formulations."""

from __future__ import annotations

import heapq
import itertools
import json
from pathlib import Path


OUTPUT_DIR = Path("outputs/mcr_compare_ui")
OUTPUT_HTML = OUTPUT_DIR / "index.html"


def subset_label(subset):
    if not subset:
        return "{}"
    return "{" + ",".join(sorted(subset)) + "}"


def make_graph(edges):
    adjacency = {}
    for left, right in edges:
        adjacency.setdefault(left, set()).add(right)
        adjacency.setdefault(right, set()).add(left)
    return {node: tuple(sorted(neighbors)) for node, neighbors in adjacency.items()}


def reconstruct_path(parents, end_state):
    path = []
    state = end_state
    while state is not None:
        path.append(state[0])
        state = parents[state]
    return list(reversed(path))


def exact_mcr_trace(graph, cover, start, goal):
    counter = itertools.count()
    start_subset = cover[start]
    pq = [(len(start_subset), next(counter), start, start_subset)]
    best_subsets = {node: [] for node in graph}
    best_subsets[start] = [start_subset]
    parents = {(start, start_subset): None}
    trace = []
    goal_state = None

    while pq:
        _, _, vertex, subset = heapq.heappop(pq)
        if any(existing < subset for existing in best_subsets[vertex]):
            continue
        trace.append(
            {
                "step_index": len(trace),
                "vertex": vertex,
                "subset": subset_label(subset),
                "frontier": [
                    {"vertex": queued_vertex, "subset": subset_label(queued_subset)}
                    for _, _, queued_vertex, queued_subset in pq
                ],
                "best_subsets": {
                    node: [subset_label(item) for item in subsets]
                    for node, subsets in best_subsets.items()
                },
            }
        )
        if vertex == goal:
            goal_state = (vertex, subset)
            break

        for neighbor in graph[vertex]:
            next_subset = subset | cover[neighbor]
            dominated = False
            to_remove = []
            for existing in best_subsets[neighbor]:
                if existing <= next_subset:
                    dominated = True
                    break
                if next_subset < existing:
                    to_remove.append(existing)
            if dominated:
                continue
            for item in to_remove:
                best_subsets[neighbor].remove(item)
            best_subsets[neighbor].append(next_subset)
            parents[(neighbor, next_subset)] = (vertex, subset)
            heapq.heappush(pq, (len(next_subset), next(counter), neighbor, next_subset))

    if goal_state is None:
        raise RuntimeError("Exact MCR failed")

    return {
        "path": reconstruct_path(parents, goal_state),
        "subset": subset_label(goal_state[1]),
        "count": len(goal_state[1]),
        "trace": trace,
    }


def greedy_mcr_trace(graph, cover, start, goal):
    counter = itertools.count()
    start_subset = cover[start]
    pq = [(len(start_subset), next(counter), start, start_subset)]
    best_subset = {node: None for node in graph}
    best_subset[start] = start_subset
    parents = {(start, start_subset): None}
    visited = set()
    trace = []
    goal_state = None

    while pq:
        _, _, vertex, subset = heapq.heappop(pq)
        if vertex in visited:
            continue
        visited.add(vertex)
        trace.append(
            {
                "step_index": len(trace),
                "vertex": vertex,
                "subset": subset_label(subset),
                "frontier": [
                    {"vertex": queued_vertex, "subset": subset_label(queued_subset)}
                    for _, _, queued_vertex, queued_subset in pq
                ],
                "best_subsets": {
                    node: ([] if item is None else [subset_label(item)])
                    for node, item in best_subset.items()
                },
            }
        )
        if vertex == goal:
            goal_state = (vertex, subset)
            break

        for neighbor in graph[vertex]:
            next_subset = subset | cover[neighbor]
            current_best = best_subset[neighbor]
            if current_best is None or len(next_subset) < len(current_best):
                best_subset[neighbor] = next_subset
                parents[(neighbor, next_subset)] = (vertex, subset)
                heapq.heappush(pq, (len(next_subset), next(counter), neighbor, next_subset))

    if goal_state is None:
        raise RuntimeError("Greedy MCR failed")

    return {
        "path": reconstruct_path(parents, goal_state),
        "subset": subset_label(goal_state[1]),
        "count": len(goal_state[1]),
        "trace": trace,
    }


def weighted_mcr_greedy(graph, cover, weights, start, goal):
    counter = itertools.count()
    start_subset = cover[start]
    pq = [(sum(weights[item] for item in start_subset), next(counter), start, start_subset)]
    best_subset = {node: None for node in graph}
    best_subset[start] = start_subset
    parents = {(start, start_subset): None}
    visited = set()
    trace = []
    goal_state = None

    while pq:
        current_cost, _, vertex, subset = heapq.heappop(pq)
        if vertex in visited:
            continue
        visited.add(vertex)
        trace.append(
            {
                "step_index": len(trace),
                "vertex": vertex,
                "subset": subset_label(subset),
                "score": round(current_cost, 2),
            }
        )
        if vertex == goal:
            goal_state = (vertex, subset)
            break
        for neighbor in graph[vertex]:
            next_subset = subset | cover[neighbor]
            current_best = best_subset[neighbor]
            next_cost = sum(weights[item] for item in next_subset)
            best_cost = float("inf") if current_best is None else sum(weights[item] for item in current_best)
            if current_best is None or next_cost < best_cost:
                best_subset[neighbor] = next_subset
                parents[(neighbor, next_subset)] = (vertex, subset)
                heapq.heappush(pq, (next_cost, next(counter), neighbor, next_subset))

    if goal_state is None:
        raise RuntimeError("Weighted greedy MCR failed")

    subset = goal_state[1]
    return {
        "path": reconstruct_path(parents, goal_state),
        "subset": subset_label(subset),
        "count": len(subset),
        "semantic_weight": round(sum(weights[item] for item in subset), 2),
        "trace": trace,
    }


def build_data():
    core_positions = {
        "s": (0.0, 0.0),
        "a": (1.0, 1.0),
        "b": (2.0, 1.0),
        "c": (1.0, -1.0),
        "d": (2.0, -1.0),
        "t": (3.0, 0.0),
    }
    core_graph = make_graph(
        [
            ("s", "a"),
            ("a", "b"),
            ("b", "t"),
            ("s", "c"),
            ("c", "d"),
            ("d", "t"),
            ("a", "d"),
        ]
    )
    core_cover = {
        "s": frozenset(),
        "a": frozenset({"O1"}),
        "b": frozenset({"O1", "O2"}),
        "c": frozenset({"O3"}),
        "d": frozenset({"O2"}),
        "t": frozenset(),
    }
    exact_core = exact_mcr_trace(core_graph, core_cover, "s", "t")

    failure_positions = {
        "s": (0.0, 0.0),
        "u1": (1.0, 1.0),
        "u2": (2.0, 1.0),
        "u3": (3.0, 1.0),
        "v1": (1.0, -1.0),
        "v2": (2.0, -1.0),
        "v3": (3.0, -1.0),
        "t": (4.0, 0.0),
    }
    failure_graph = make_graph(
        [
            ("s", "u1"),
            ("u1", "u2"),
            ("u2", "u3"),
            ("u3", "t"),
            ("s", "v1"),
            ("v1", "v2"),
            ("v2", "v3"),
            ("v3", "t"),
            ("u2", "v2"),
        ]
    )
    failure_cover = {
        "s": frozenset(),
        "u1": frozenset({"O1"}),
        "u2": frozenset({"O1", "O2"}),
        "u3": frozenset({"O2"}),
        "v1": frozenset({"O3"}),
        "v2": frozenset({"O4"}),
        "v3": frozenset({"O5"}),
        "t": frozenset(),
    }
    exact_failure = exact_mcr_trace(failure_graph, failure_cover, "s", "t")
    greedy_failure = greedy_mcr_trace(failure_graph, failure_cover, "s", "t")

    semantic_positions = {
        "start": (0.0, 0.0),
        "fragile_route_1": (1.2, 1.0),
        "fragile_route_2": (2.4, 1.0),
        "soft_route_1": (1.0, -0.8),
        "soft_route_2": (2.0, -1.1),
        "soft_route_3": (3.0, -0.8),
        "goal": (4.1, 0.0),
    }
    semantic_graph = make_graph(
        [
            ("start", "fragile_route_1"),
            ("fragile_route_1", "fragile_route_2"),
            ("fragile_route_2", "goal"),
            ("start", "soft_route_1"),
            ("soft_route_1", "soft_route_2"),
            ("soft_route_2", "soft_route_3"),
            ("soft_route_3", "goal"),
        ]
    )
    semantic_cover = {
        "start": frozenset(),
        "fragile_route_1": frozenset({"fragile_vase"}),
        "fragile_route_2": frozenset({"fragile_vase", "knife_block"}),
        "soft_route_1": frozenset({"dish_towel"}),
        "soft_route_2": frozenset({"dish_towel", "cardboard_box"}),
        "soft_route_3": frozenset({"dish_towel", "cardboard_box", "sponge"}),
        "goal": frozenset(),
    }
    semantic_weights = {
        "fragile_vase": 9.0,
        "knife_block": 8.0,
        "cardboard_box": 1.5,
        "dish_towel": 0.5,
        "sponge": 1.0,
    }
    semantic_standard = greedy_mcr_trace(semantic_graph, semantic_cover, "start", "goal")
    semantic_weighted = weighted_mcr_greedy(semantic_graph, semantic_cover, semantic_weights, "start", "goal")

    professor_positions = {
        "s": (0.0, 0.0),
        "h1": (1.0, 1.0),
        "v": (2.2, 0.0),
        "future": (3.5, 0.8),
        "goal": (4.7, 0.0),
        "h2": (1.1, -1.1),
    }
    professor_graph = make_graph(
        [
            ("s", "h1"),
            ("h1", "v"),
            ("s", "h2"),
            ("h2", "v"),
            ("v", "future"),
            ("future", "goal"),
        ]
    )
    professor_labels = [
        {
            "path": ["s", "h1", "v", "future", "goal"],
            "label_at_v": "{dish_towel}",
            "future_addition": "{knife_block}",
            "final_label": "{dish_towel,knife_block}",
            "semantic_weight": 8.5,
            "narrative": "History A arrives at v after a benign towel contact, but the future edge adds a hazardous knife block.",
        },
        {
            "path": ["s", "h2", "v", "future", "goal"],
            "label_at_v": "{cardboard_box}",
            "future_addition": "{}",
            "final_label": "{cardboard_box}",
            "semantic_weight": 1.5,
            "narrative": "History B reaches the same roadmap vertex with a different collision set and avoids the dangerous object later.",
        },
    ]

    formulations = [
        {
            "id": "continuous_prm",
            "title": "Continuous MCR + PRM",
            "paper_label": "Hauser 2012 continuous formulation",
            "objective": "Find a continuous path from qs to qg whose cover contains the fewest unique violated constraints.",
            "state": "Continuous configuration q in C; planner approximates state space with a roadmap.",
            "search": "Grow a PRM, solve discrete MCR on the roadmap, refine over time.",
            "pros": "Asymptotically approaches the optimal MCR in continuous spaces.",
            "risks": "Needs many samples; explanation quality depends on roadmap refinement.",
            "when_to_use": "Actual robot scenes where configuration space is continuous and exact cell decomposition is intractable.",
            "example_kind": "concept",
            "metrics": [
                {"label": "Domain", "value": "continuous"},
                {"label": "Planner", "value": "PRM reduction"},
                {"label": "Guarantee", "value": "asymptotically optimal"},
            ],
            "bullets": [
                "Obstacle boundaries induce an implicit partition of configuration space.",
                "PRM approximates the connectivity of that partition.",
                "Each roadmap node inherits the set of violated constraints at that sample.",
                "Discrete MCR becomes the inner optimization problem.",
            ],
        },
        {
            "id": "discrete_problem",
            "title": "Discrete MCR Problem",
            "paper_label": "Hauser 2012 discrete formulation",
            "objective": "Minimize the cardinality of the union of covers along an s-t path in a graph.",
            "state": "(vertex, accumulated set of violated constraints)",
            "search": "Problem statement, not a single algorithm.",
            "pros": "Makes the combinatorial object explicit and explainable.",
            "risks": "NP-hard; objective is not shortest path length.",
            "when_to_use": "As the canonical finite abstraction and baseline for all later variants.",
            "example_kind": "graph",
            "graph": {
                "nodes": [{"id": node, "x": pos[0], "y": pos[1], "cover": subset_label(core_cover[node])} for node, pos in core_positions.items()],
                "edges": [{"source": left, "target": right} for left, neighbors in core_graph.items() for right in neighbors if left < right],
                "highlight_path": exact_core["path"],
            },
            "metrics": [
                {"label": "Objective", "value": "|Union C[v]|"},
                {"label": "Path", "value": "s -> t"},
                {"label": "Example optimum", "value": exact_core["subset"]},
            ],
            "bullets": [
                "Each vertex stores a cover C[v].",
                "Path cost is the union of covers, not edge length.",
                "Longer paths can be better if they reuse the same violated constraints.",
                "This is the clean baseline for exact, greedy, and weighted variants.",
            ],
        },
        {
            "id": "exact_search",
            "title": "Exact Discrete Search",
            "paper_label": "Hauser exact discrete subroutine",
            "objective": "Return the globally optimal discrete MCR solution.",
            "state": "(vertex, accumulated subset), with multiple irreducible subsets retained per vertex.",
            "search": "Best-first search over labels; prune only dominated subsets.",
            "pros": "Optimal and faithful to the real combinatorial state.",
            "risks": "Can blow up quickly as the number of non-dominated subsets grows.",
            "when_to_use": "Small or medium graphs, or as a benchmark for approximate methods.",
            "example_kind": "trace_graph",
            "graph": {
                "nodes": [{"id": node, "x": pos[0], "y": pos[1], "cover": subset_label(core_cover[node])} for node, pos in core_positions.items()],
                "edges": [{"source": left, "target": right} for left, neighbors in core_graph.items() for right in neighbors if left < right],
                "highlight_path": exact_core["path"],
            },
            "trace": exact_core["trace"],
            "metrics": [
                {"label": "Final subset", "value": exact_core["subset"]},
                {"label": "Collision count", "value": str(exact_core["count"])},
                {"label": "Trace steps", "value": str(len(exact_core["trace"]))},
            ],
            "bullets": [
                "Keeps several labels per vertex when none dominates the others.",
                "Dominance here is set inclusion, not just cardinality.",
                "This is the formulation most compatible with your professor's path-dependent idea.",
            ],
        },
        {
            "id": "greedy_search",
            "title": "Greedy Discrete Search",
            "paper_label": "Hauser greedy discrete subroutine",
            "objective": "Approximate MCR quickly by keeping only one best-so-far subset per vertex.",
            "state": "(vertex, one retained subset)",
            "search": "Best-first expansion with aggressive per-vertex pruning.",
            "pros": "Simple and fast.",
            "risks": "Can prune away the globally best explanation.",
            "when_to_use": "As a fast baseline or warm start, not as the final truth on hard instances.",
            "example_kind": "trace_graph",
            "graph": {
                "nodes": [{"id": node, "x": pos[0], "y": pos[1], "cover": subset_label(failure_cover[node])} for node, pos in failure_positions.items()],
                "edges": [{"source": left, "target": right} for left, neighbors in failure_graph.items() for right in neighbors if left < right],
                "highlight_path": greedy_failure["path"],
                "reference_path": exact_failure["path"],
            },
            "trace": greedy_failure["trace"],
            "metrics": [
                {"label": "Greedy subset", "value": greedy_failure["subset"]},
                {"label": "Exact subset", "value": exact_failure["subset"]},
                {"label": "Failure gap", "value": f"{greedy_failure['count']} vs {exact_failure['count']}"},
            ],
            "bullets": [
                "The page shows the adversarial-style graph where greedy is suboptimal.",
                "Greedy stores one subset per vertex, so future consequences are hidden.",
                "This is the main warning that carries over to weighted and semantic variants.",
            ],
        },
        {
            "id": "semantic_weighted",
            "title": "Semantic-Weighted MCR",
            "paper_label": "Your current VLM-weighted idea",
            "objective": "Minimize total semantic consequence of the collided object set rather than raw count.",
            "state": "(vertex, accumulated object set), with object-specific semantic weights.",
            "search": "Weighted label search or weighted greedy approximation.",
            "pros": "Distinguishes dangerous/fragile objects from benign clutter.",
            "risks": "If you still keep one label per vertex, you inherit greedy pruning failure in a weighted form.",
            "when_to_use": "Scenes where touching a towel and touching a knife block should not count equally.",
            "example_kind": "trace_graph",
            "graph": {
                "nodes": [{"id": node, "x": pos[0], "y": pos[1], "cover": subset_label(semantic_cover[node])} for node, pos in semantic_positions.items()],
                "edges": [{"source": left, "target": right} for left, neighbors in semantic_graph.items() for right in neighbors if left < right],
                "highlight_path": semantic_weighted["path"],
                "reference_path": semantic_standard["path"],
            },
            "trace": semantic_weighted["trace"],
            "metrics": [
                {"label": "Standard count-optimal", "value": semantic_standard["subset"]},
                {"label": "Semantic route", "value": semantic_weighted["subset"]},
                {"label": "Semantic weight", "value": str(semantic_weighted["semantic_weight"])},
            ],
            "bullets": [
                "VLM outputs become object tags or scalar weights.",
                "The graph shows why 3 benign collisions can beat 2 severe ones.",
                "This is already a meaningful upgrade over plain cardinality MCR.",
            ],
            "object_weights": [
                {"name": "Fragile vase", "weight": 9.0, "class": "fragile"},
                {"name": "Knife block", "weight": 8.0, "class": "dangerous"},
                {"name": "Dish towel", "weight": 0.5, "class": "soft-contact"},
                {"name": "Cardboard box", "weight": 1.5, "class": "soft-contact"},
                {"name": "Sponge", "weight": 1.0, "class": "soft-contact"},
            ],
        },
        {
            "id": "professor_path_conditioned",
            "title": "Path-Conditioned Semantic MCR",
            "paper_label": "Professor's proposed modification",
            "objective": "Minimize semantic consequence when collision labels at a vertex depend on how the path reached that vertex.",
            "state": "(vertex, path-conditioned collision label) rather than one fixed C[v].",
            "search": "Multi-label search over history-dependent states; greedy single-label pruning is generally unsafe.",
            "pros": "Matches the actual semantics of contact history and future consequences.",
            "risks": "State explosion is even more pronounced than in standard exact MCR.",
            "when_to_use": "When the same roadmap vertex can imply different object consequences depending on prior path choices.",
            "example_kind": "history_graph",
            "graph": {
                "nodes": [{"id": node, "x": pos[0], "y": pos[1], "cover": ""} for node, pos in professor_positions.items()],
                "edges": [{"source": left, "target": right} for left, neighbors in professor_graph.items() for right in neighbors if left < right],
            },
            "metrics": [
                {"label": "Label at v (A)", "value": professor_labels[0]["label_at_v"]},
                {"label": "Label at v (B)", "value": professor_labels[1]["label_at_v"]},
                {"label": "Correct pruning", "value": "multi-label only"},
            ],
            "bullets": [
                "The same roadmap vertex v is not a sufficient state summary anymore.",
                "Two histories can meet at v with different future semantic costs.",
                "This pushes the formulation toward exact-style or bounded multi-label search.",
            ],
            "history_labels": professor_labels,
        },
    ]
    return formulations


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>MCR Compare UI</title>
  <style>
    :root {
      --bg: #0d1117;
      --panel: #161b22;
      --panel-2: #11161d;
      --border: #2d3742;
      --text: #e6edf3;
      --muted: #9fb0c0;
      --accent: #60a5fa;
      --accent-2: #4ade80;
      --warn: #fbbf24;
      --danger: #f87171;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
      background:
        radial-gradient(circle at top left, rgba(96,165,250,.10), transparent 28%),
        radial-gradient(circle at bottom right, rgba(74,222,128,.08), transparent 24%),
        var(--bg);
      color: var(--text);
    }
    .page {
      max-width: 1600px;
      margin: 0 auto;
      padding: 24px;
    }
    .hero {
      display: grid;
      gap: 12px;
      margin-bottom: 20px;
    }
    h1 {
      margin: 0;
      font-size: 30px;
      letter-spacing: -.02em;
    }
    .subtitle {
      color: var(--muted);
      max-width: 980px;
      line-height: 1.5;
    }
    .topbar {
      display: grid;
      grid-template-columns: 1fr auto;
      gap: 12px;
      align-items: center;
      margin-bottom: 18px;
    }
    .compare-note {
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 14px 16px;
      color: var(--muted);
    }
    .controls {
      display: flex;
      gap: 10px;
      align-items: center;
      flex-wrap: wrap;
    }
    button {
      background: var(--panel);
      color: var(--text);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 10px 14px;
      cursor: pointer;
    }
    button:hover { border-color: var(--accent); }
    .panes {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 18px;
    }
    .pane {
      background: linear-gradient(180deg, rgba(255,255,255,.02), rgba(255,255,255,0)), var(--panel);
      border: 1px solid var(--border);
      border-radius: 20px;
      padding: 18px;
      min-height: 900px;
      display: grid;
      gap: 16px;
      align-content: start;
    }
    .pane-header {
      display: grid;
      gap: 10px;
    }
    label {
      color: var(--muted);
      font-size: 13px;
      text-transform: uppercase;
      letter-spacing: .08em;
    }
    select, input[type="range"] {
      width: 100%;
    }
    select {
      background: var(--panel-2);
      color: var(--text);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 12px;
      font: inherit;
    }
    .title-row {
      display: flex;
      gap: 12px;
      align-items: baseline;
      flex-wrap: wrap;
    }
    .title-row h2 {
      margin: 0;
      font-size: 24px;
    }
    .tag {
      padding: 4px 10px;
      border-radius: 999px;
      border: 1px solid var(--border);
      color: var(--muted);
      font-size: 12px;
    }
    .summary {
      line-height: 1.55;
      color: var(--muted);
    }
    .metrics {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 10px;
    }
    .metric {
      background: var(--panel-2);
      border: 1px solid var(--border);
      border-radius: 14px;
      padding: 12px;
      min-height: 84px;
    }
    .metric .k {
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: .08em;
      color: var(--muted);
      margin-bottom: 8px;
    }
    .metric .v {
      font-size: 16px;
      line-height: 1.35;
    }
    .card {
      background: var(--panel-2);
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 16px;
    }
    .card h3 {
      margin: 0 0 10px;
      font-size: 16px;
    }
    .grid-2 {
      display: grid;
      grid-template-columns: 1.1fr .9fr;
      gap: 14px;
    }
    .field {
      margin-bottom: 10px;
    }
    .field .k {
      color: var(--muted);
      text-transform: uppercase;
      letter-spacing: .08em;
      font-size: 12px;
      margin-bottom: 6px;
    }
    .field .v {
      line-height: 1.5;
    }
    ul {
      margin: 0;
      padding-left: 18px;
      color: var(--muted);
      line-height: 1.5;
    }
    .trace-head {
      display: flex;
      justify-content: space-between;
      gap: 10px;
      align-items: center;
      margin-bottom: 10px;
    }
    .trace-status {
      color: var(--muted);
      font-size: 13px;
    }
    .trace-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 10px;
      margin-top: 10px;
    }
    pre {
      margin: 0;
      white-space: pre-wrap;
      word-break: break-word;
      color: var(--muted);
      font-size: 13px;
      line-height: 1.45;
    }
    .weights {
      display: grid;
      gap: 8px;
      margin-top: 10px;
    }
    .weight-row {
      display: grid;
      grid-template-columns: 1fr auto auto;
      gap: 10px;
      align-items: center;
      padding: 10px 12px;
      border-radius: 12px;
      border: 1px solid var(--border);
      background: rgba(255,255,255,.02);
    }
    .weight-row .cls { color: var(--muted); font-size: 12px; }
    .weight-row .num { color: var(--accent-2); }
    .history-grid {
      display: grid;
      gap: 10px;
    }
    .history-box {
      padding: 12px;
      border-radius: 14px;
      border: 1px solid var(--border);
      background: rgba(255,255,255,.02);
    }
    .history-box h4 {
      margin: 0 0 8px;
      font-size: 15px;
    }
    .history-box p {
      margin: 0;
      color: var(--muted);
      line-height: 1.45;
    }
    .compare-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 10px;
    }
    .compare-cell {
      background: var(--panel-2);
      border: 1px solid var(--border);
      border-radius: 14px;
      padding: 12px;
    }
    .compare-cell .k {
      color: var(--muted);
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: .08em;
      margin-bottom: 6px;
    }
    svg {
      width: 100%;
      height: auto;
      display: block;
      border-radius: 14px;
      background: #0f141b;
      border: 1px solid var(--border);
    }
    @media (max-width: 1100px) {
      .panes, .grid-2, .compare-grid, .metrics { grid-template-columns: 1fr; }
      .pane { min-height: auto; }
    }
  </style>
</head>
<body>
  <div class="page">
    <div class="hero">
      <h1>Minimum Constraint Removal Compare UI</h1>
      <div class="subtitle">
        Side-by-side explorer for the paper formulations and your two semantic variants. Use the left and right selectors to compare objectives, state definitions, retained labels, and search behavior. The key distinction to watch is when a vertex alone is enough, and when the accumulated collision history must stay in the state.
      </div>
    </div>
    <div class="topbar">
      <div class="compare-note" id="compare-note"></div>
      <div class="controls">
        <button id="swap-btn">Swap Panels</button>
      </div>
    </div>
    <div class="panes">
      <section class="pane" id="pane-left"></section>
      <section class="pane" id="pane-right"></section>
    </div>
  </div>
  <script>
    const FORMULATIONS = __FORMULATION_DATA__;

    const defaults = {
      left: "exact_search",
      right: "professor_path_conditioned",
    };

    function getById(id) {
      return FORMULATIONS.find(item => item.id === id);
    }

    function optionMarkup(selectedId) {
      return FORMULATIONS.map(item => {
        const selected = item.id === selectedId ? "selected" : "";
        return `<option value="${item.id}" ${selected}>${item.title}</option>`;
      }).join("");
    }

    function escapeHtml(value) {
      return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;");
    }

    function renderMetrics(metrics) {
      return `<div class="metrics">${metrics.map(metric => `
        <div class="metric">
          <div class="k">${escapeHtml(metric.label)}</div>
          <div class="v">${escapeHtml(metric.value)}</div>
        </div>`).join("")}
      </div>`;
    }

    function normalizePoint(nodes, x, y) {
      const xs = nodes.map(node => node.x);
      const ys = nodes.map(node => node.y);
      const minX = Math.min(...xs);
      const maxX = Math.max(...xs);
      const minY = Math.min(...ys);
      const maxY = Math.max(...ys);
      const px = 40 + ((x - minX) / Math.max(1, maxX - minX)) * 520;
      const py = 220 - ((y - minY) / Math.max(1, maxY - minY)) * 160;
      return { x: px, y: py };
    }

    function pathEdgeSet(path) {
      const items = new Set();
      for (let i = 0; i < path.length - 1; i += 1) {
        items.add(`${path[i]}|${path[i + 1]}`);
        items.add(`${path[i + 1]}|${path[i]}`);
      }
      return items;
    }

    function renderGraph(graph, activeVertex = null) {
      const nodes = graph.nodes;
      const highlight = pathEdgeSet(graph.highlight_path || []);
      const reference = pathEdgeSet(graph.reference_path || []);
      const circles = [];
      const labels = [];
      const lines = [];

      graph.edges.forEach(edge => {
        const p1 = normalizePoint(nodes, nodes.find(n => n.id === edge.source).x, nodes.find(n => n.id === edge.source).y);
        const p2 = normalizePoint(nodes, nodes.find(n => n.id === edge.target).x, nodes.find(n => n.id === edge.target).y);
        let stroke = "#2d3742";
        let width = 3;
        if (reference.has(`${edge.source}|${edge.target}`)) {
          stroke = "#fbbf24";
          width = 4;
        }
        if (highlight.has(`${edge.source}|${edge.target}`)) {
          stroke = "#4ade80";
          width = 6;
        }
        lines.push(`<line x1="${p1.x}" y1="${p1.y}" x2="${p2.x}" y2="${p2.y}" stroke="${stroke}" stroke-width="${width}" stroke-linecap="round"/>`);
      });

      nodes.forEach(node => {
        const p = normalizePoint(nodes, node.x, node.y);
        let fill = "#60a5fa";
        if (node.id === "s" || node.id === "t" || node.id === "start" || node.id === "goal") fill = "#fbbf24";
        if (node.id === activeVertex) fill = "#f87171";
        circles.push(`<circle cx="${p.x}" cy="${p.y}" r="18" fill="${fill}" stroke="#0d1117" stroke-width="3"/>`);
        labels.push(`<text x="${p.x - 18}" y="${p.y - 24}" fill="#e6edf3" font-size="13" font-family="monospace">${escapeHtml(node.id)}</text>`);
        if (node.cover) {
          labels.push(`<text x="${p.x - 34}" y="${p.y + 34}" fill="#9fb0c0" font-size="11" font-family="monospace">${escapeHtml(node.cover)}</text>`);
        }
      });

      return `<svg viewBox="0 0 600 260" aria-label="formulation graph">
        ${lines.join("")}
        ${circles.join("")}
        ${labels.join("")}
      </svg>`;
    }

    function renderTraceCard(formulation, paneKey) {
      if (!formulation.trace) return "";
      const max = formulation.trace.length - 1;
      return `
        <div class="card">
          <div class="trace-head">
            <h3>Search Trace</h3>
            <div class="trace-status" id="${paneKey}-trace-status"></div>
          </div>
          <input type="range" min="0" max="${max}" value="0" id="${paneKey}-trace-slider">
          <div class="trace-grid">
            <div class="compare-cell">
              <div class="k">Expansion</div>
              <pre id="${paneKey}-trace-main"></pre>
            </div>
            <div class="compare-cell">
              <div class="k">Stored Labels</div>
              <pre id="${paneKey}-trace-labels"></pre>
            </div>
          </div>
        </div>
      `;
    }

    function renderObjectWeights(formulation) {
      if (!formulation.object_weights) return "";
      return `
        <div class="card">
          <h3>Semantic Objects</h3>
          <div class="weights">
            ${formulation.object_weights.map(item => `
              <div class="weight-row">
                <div>${escapeHtml(item.name)}<div class="cls">${escapeHtml(item.class)}</div></div>
                <div class="num">${escapeHtml(item.weight)}</div>
                <div class="cls">weight</div>
              </div>`).join("")}
          </div>
        </div>
      `;
    }

    function renderHistoryBoxes(formulation) {
      if (!formulation.history_labels) return "";
      return `
        <div class="card">
          <h3>Path-Conditioned Labels</h3>
          <div class="history-grid">
            ${formulation.history_labels.map((item, index) => `
              <div class="history-box">
                <h4>History ${index + 1}</h4>
                <p>Path: ${escapeHtml(item.path.join(" -> "))}</p>
                <p>Label at shared vertex v: ${escapeHtml(item.label_at_v)}</p>
                <p>Future addition: ${escapeHtml(item.future_addition)}</p>
                <p>Final label: ${escapeHtml(item.final_label)}</p>
                <p>Semantic weight: ${escapeHtml(item.semantic_weight)}</p>
                <p>${escapeHtml(item.narrative)}</p>
              </div>
            `).join("")}
          </div>
        </div>
      `;
    }

    function renderPane(formulation, paneKey) {
      const pane = document.getElementById(`pane-${paneKey}`);
      pane.innerHTML = `
        <div class="pane-header">
          <label for="${paneKey}-select">Formulation</label>
          <select id="${paneKey}-select">${optionMarkup(formulation.id)}</select>
          <div class="title-row">
            <h2>${escapeHtml(formulation.title)}</h2>
            <span class="tag">${escapeHtml(formulation.paper_label)}</span>
          </div>
          <div class="summary">${escapeHtml(formulation.when_to_use)}</div>
        </div>
        ${renderMetrics(formulation.metrics)}
        <div class="grid-2">
          <div class="card">
            <h3>Core Definition</h3>
            <div class="field"><div class="k">Objective</div><div class="v">${escapeHtml(formulation.objective)}</div></div>
            <div class="field"><div class="k">State</div><div class="v">${escapeHtml(formulation.state)}</div></div>
            <div class="field"><div class="k">Search Idea</div><div class="v">${escapeHtml(formulation.search)}</div></div>
          </div>
          <div class="card">
            <h3>Tradeoffs</h3>
            <div class="field"><div class="k">Strength</div><div class="v">${escapeHtml(formulation.pros)}</div></div>
            <div class="field"><div class="k">Risk</div><div class="v">${escapeHtml(formulation.risks)}</div></div>
          </div>
        </div>
        <div class="card">
          <h3>Key Takeaways</h3>
          <ul>${formulation.bullets.map(item => `<li>${escapeHtml(item)}</li>`).join("")}</ul>
        </div>
        ${formulation.graph ? `<div class="card"><h3>Example Structure</h3><div id="${paneKey}-graph">${renderGraph(formulation.graph)}</div></div>` : ""}
        ${renderTraceCard(formulation, paneKey)}
        ${renderObjectWeights(formulation)}
        ${renderHistoryBoxes(formulation)}
      `;
      document.getElementById(`${paneKey}-select`).addEventListener("change", event => {
        state[paneKey] = event.target.value;
        renderAll();
      });
      attachTraceHandlers(formulation, paneKey);
    }

    function attachTraceHandlers(formulation, paneKey) {
      if (!formulation.trace) return;
      const slider = document.getElementById(`${paneKey}-trace-slider`);
      const graphBox = document.getElementById(`${paneKey}-graph`);
      const status = document.getElementById(`${paneKey}-trace-status`);
      const main = document.getElementById(`${paneKey}-trace-main`);
      const labels = document.getElementById(`${paneKey}-trace-labels`);
      const update = () => {
        const step = formulation.trace[Number(slider.value)];
        status.textContent = `step ${step.step_index + 1} / ${formulation.trace.length}`;
        main.textContent = [
          `expand: ${step.vertex}`,
          `subset: ${step.subset}`,
          step.score !== undefined ? `score: ${step.score}` : null,
          step.frontier ? `frontier: ${step.frontier.map(item => `${item.vertex}:${item.subset}`).join(" | ") || "-"}` : null,
        ].filter(Boolean).join("\\n");
        labels.textContent = step.best_subsets
          ? Object.entries(step.best_subsets).map(([node, values]) => `${node}: ${values.length ? values.join(", ") : "-"}`).join("\\n")
          : "No per-vertex label snapshot recorded for this formulation.";
        graphBox.innerHTML = renderGraph(formulation.graph, step.vertex);
      };
      slider.addEventListener("input", update);
      update();
    }

    function renderCompareNote() {
      const left = getById(state.left);
      const right = getById(state.right);
      document.getElementById("compare-note").innerHTML = `
        <strong>Compare focus:</strong> ${escapeHtml(left.title)} vs ${escapeHtml(right.title)}.
        Left state is <code>${escapeHtml(left.state)}</code>.
        Right state is <code>${escapeHtml(right.state)}</code>.
        The main question is whether a roadmap vertex alone is enough, or whether the accumulated label history must remain explicit.
      `;
    }

    function renderAll() {
      renderPane(getById(state.left), "left");
      renderPane(getById(state.right), "right");
      renderCompareNote();
    }

    const state = { ...defaults };
    document.getElementById("swap-btn").addEventListener("click", () => {
      const temp = state.left;
      state.left = state.right;
      state.right = temp;
      renderAll();
    });
    renderAll();
  </script>
</body>
</html>
"""


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    formulations = build_data()
    html = HTML_TEMPLATE.replace("__FORMULATION_DATA__", json.dumps(formulations))
    OUTPUT_HTML.write_text(html, encoding="utf-8")
    print(f"Built compare UI at {OUTPUT_HTML}")


if __name__ == "__main__":
    main()
