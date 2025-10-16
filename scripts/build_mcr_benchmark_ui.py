#!/usr/bin/env python3
"""Build an animated benchmark UI for comparing MCR algorithms on the same graph."""

from __future__ import annotations

import json
from pathlib import Path


OUTPUT_DIR = Path("outputs/mcr_benchmark_ui")
OUTPUT_HTML = OUTPUT_DIR / "index.html"


def grid_positions(lanes: int, layers: int):
    positions = {"start": (0.0, (lanes - 1) / 2), "goal": (layers + 1, (lanes - 1) / 2)}
    for layer in range(1, layers + 1):
        for lane in range(lanes):
            positions[f"n{layer}_{lane}"] = (layer, lanes - 1 - lane)
    return positions


def layered_graph(graph_id, title, description, lanes, layers, lane_objects, weights, semantic_focus, conditional_rules=None):
    conditional_rules = conditional_rules or {}
    positions = grid_positions(lanes, layers)
    nodes = [
        {"id": node_id, "x": x, "y": y}
        for node_id, (x, y) in positions.items()
    ]
    edges = []
    edge_id = 0

    def add_edge(source, target, adds):
        nonlocal edge_id
        key = f"{source}->{target}"
        conditionals = conditional_rules.get(key, [])
        edges.append(
            {
                "id": f"e{edge_id}",
                "source": source,
                "target": target,
                "adds": list(adds),
                "conditional": conditionals,
            }
        )
        edge_id += 1

    for lane in range(lanes):
        add_edge("start", f"n1_{lane}", lane_objects[(1, lane)])

    for layer in range(1, layers):
        for lane in range(lanes):
            src = f"n{layer}_{lane}"
            for delta in (-1, 0, 1):
                next_lane = lane + delta
                if 0 <= next_lane < lanes:
                    dst = f"n{layer + 1}_{next_lane}"
                    adds = lane_objects[(layer + 1, next_lane)]
                    if delta != 0 and layer % 2 == 0:
                        adds = list(dict.fromkeys(adds + [f"cross_{layer}_{lane}_{next_lane}"]))
                        if f"cross_{layer}_{lane}_{next_lane}" not in weights:
                            weights[f"cross_{layer}_{lane}_{next_lane}"] = 1.0
                    add_edge(src, dst, adds)

    for lane in range(lanes):
        add_edge(f"n{layers}_{lane}", "goal", [])

    conditional_rule_list = []
    for edge in edges:
        if edge["conditional"]:
            for rule in edge["conditional"]:
                conditional_rule_list.append(
                    {
                        "edge": f"{edge['source']} -> {edge['target']}",
                        "if_contains": rule["if_contains"],
                        "adds": rule["adds"],
                    }
                )

    return {
        "id": graph_id,
        "title": title,
        "description": description,
        "nodes": nodes,
        "edges": edges,
        "preview_edges": edges,
        "weights": weights,
        "semantic_focus": semantic_focus,
        "conditional_rules": conditional_rule_list,
        "scale": "small",
    }


def large_dense_graph(
    graph_id,
    title,
    description,
    lanes,
    layers,
    base_objects,
    semantic_weights,
    semantic_focus,
    conditional_stride=None,
):
    positions = grid_positions(lanes, layers)
    nodes = [
        {"id": node_id, "x": x, "y": y}
        for node_id, (x, y) in positions.items()
    ]
    edges = []
    preview_edges = []
    conditional_rule_list = []
    edge_id = 0

    def layer_object(layer, lane):
        return [base_objects[(layer + lane) % len(base_objects)]]

    for lane in range(lanes):
        edges.append(
            {
                "id": f"e{edge_id}",
                "source": "start",
                "target": f"n1_{lane}",
                "adds": layer_object(1, lane),
                "conditional": [],
            }
        )
        if lane % max(1, lanes // 18) == 0:
            preview_edges.append(edges[-1])
        edge_id += 1

    for layer in range(1, layers):
        window_end = min(layers, layer + 3)
        for lane in range(lanes):
            src = f"n{layer}_{lane}"
            for next_layer in range(layer + 1, window_end + 1):
                for next_lane in range(lanes):
                    dst = f"n{next_layer}_{next_lane}"
                    adds = layer_object(next_layer, next_lane)
                    conditionals = []
                    if conditional_stride and (layer + lane + next_lane) % conditional_stride == 0:
                        trigger = base_objects[(layer + next_lane) % len(base_objects)]
                        added = base_objects[(layer + lane + 1) % len(base_objects)]
                        if trigger != added:
                            conditionals = [{"if_contains": [trigger], "adds": [added]}]
                            conditional_rule_list.append(
                                {
                                    "edge": f"{src} -> {dst}",
                                    "if_contains": [trigger],
                                    "adds": [added],
                                }
                            )
                    edge = {
                        "id": f"e{edge_id}",
                        "source": src,
                        "target": dst,
                        "adds": adds,
                        "conditional": conditionals,
                    }
                    edges.append(edge)
                    if (
                        lane % max(1, lanes // 12) == 0
                        and next_lane % max(1, lanes // 12) == 0
                        and (next_layer - layer) == 1
                    ):
                        preview_edges.append(edge)
                    edge_id += 1

    for lane in range(lanes):
        edges.append(
            {
                "id": f"e{edge_id}",
                "source": f"n{layers}_{lane}",
                "target": "goal",
                "adds": [],
                "conditional": [],
            }
        )
        if lane % max(1, lanes // 18) == 0:
            preview_edges.append(edges[-1])
        edge_id += 1

    return {
        "id": graph_id,
        "title": title,
        "description": description,
        "nodes": nodes,
        "edges": edges,
        "preview_edges": preview_edges,
        "weights": semantic_weights,
        "semantic_focus": semantic_focus,
        "conditional_rules": conditional_rule_list[:60],
        "scale": "large",
    }


def build_graphs():
    graphs = []

    weights_1 = {
        "rack": 1.0,
        "bin": 1.0,
        "tray": 1.0,
        "pipe": 1.0,
        "cross_2_0_1": 1.0,
        "cross_2_1_0": 1.0,
        "cross_2_1_2": 1.0,
        "cross_2_2_1": 1.0,
        "cross_4_0_1": 1.0,
        "cross_4_1_0": 1.0,
        "cross_4_1_2": 1.0,
        "cross_4_2_1": 1.0,
    }
    lane_objects_1 = {}
    for layer in range(1, 7):
        lane_objects_1[(layer, 0)] = ["rack"]
        lane_objects_1[(layer, 1)] = ["bin"] if layer < 4 else ["tray"]
        lane_objects_1[(layer, 2)] = ["pipe"]
    graphs.append(
        layered_graph(
            "warehouse_tradeoff",
            "Warehouse Cardinality Tradeoff",
            "A large static graph where different corridors reuse different obstacle labels. Good for seeing why path cost is union size rather than shortest route length.",
            lanes=3,
            layers=6,
            lane_objects=lane_objects_1,
            weights=weights_1,
            semantic_focus="cardinality",
        )
    )

    weights_2 = {
        "o1": 1.0,
        "o2": 1.0,
        "o3": 1.0,
        "o4": 1.0,
        "o5": 1.0,
        "o6": 1.0,
    }
    lane_objects_2 = {}
    for layer in range(1, 7):
        lane_objects_2[(layer, 0)] = ["o1"] if layer < 3 else [f"o{min(6, layer)}"]
        lane_objects_2[(layer, 1)] = ["o2"]
        lane_objects_2[(layer, 2)] = ["o3"] if layer < 5 else ["o4"]
        lane_objects_2[(layer, 3)] = ["o5"]
    graphs.append(
        layered_graph(
            "greedy_failure_large",
            "Expanded Greedy Failure",
            "A larger benchmark where locally cheap labels lure greedy search into a globally worse explanation.",
            lanes=4,
            layers=6,
            lane_objects=lane_objects_2,
            weights=weights_2,
            semantic_focus="greedy-warning",
        )
    )

    weights_3 = {
        "fragile_glass": 9.0,
        "knife_block": 8.0,
        "dish_towel": 0.5,
        "sponge": 1.0,
        "cardboard_box": 1.5,
        "plastic_bag": 1.0,
    }
    lane_objects_3 = {}
    for layer in range(1, 7):
        lane_objects_3[(layer, 0)] = ["fragile_glass"] if layer <= 3 else ["knife_block"]
        lane_objects_3[(layer, 1)] = ["dish_towel"] if layer % 2 else ["sponge"]
        lane_objects_3[(layer, 2)] = ["cardboard_box"] if layer < 4 else ["plastic_bag"]
    graphs.append(
        layered_graph(
            "kitchen_semantic",
            "Kitchen Semantic Benchmark",
            "The shortest explanation by count is not the safest explanation by meaning. This graph separates severe objects from benign clutter.",
            lanes=3,
            layers=6,
            lane_objects=lane_objects_3,
            weights=weights_3,
            semantic_focus="semantic",
        )
    )

    weights_4 = {
        "ceramic_bowl": 7.0,
        "metal_can": 2.0,
        "towel": 0.5,
        "detergent": 6.0,
        "box": 1.5,
        "fruit_bag": 1.0,
        "cross_2_0_1": 1.0,
        "cross_2_1_0": 1.0,
        "cross_2_1_2": 1.0,
        "cross_2_2_1": 1.0,
        "cross_2_2_3": 1.0,
        "cross_2_3_2": 1.0,
        "cross_4_0_1": 1.0,
        "cross_4_1_0": 1.0,
        "cross_4_1_2": 1.0,
        "cross_4_2_1": 1.0,
        "cross_4_2_3": 1.0,
        "cross_4_3_2": 1.0,
    }
    lane_objects_4 = {}
    for layer in range(1, 7):
        lane_objects_4[(layer, 0)] = ["ceramic_bowl"] if layer < 4 else ["detergent"]
        lane_objects_4[(layer, 1)] = ["towel"]
        lane_objects_4[(layer, 2)] = ["metal_can"] if layer % 2 else ["box"]
        lane_objects_4[(layer, 3)] = ["fruit_bag"]
    graphs.append(
        layered_graph(
            "dense_household_mix",
            "Dense Household Semantic Mix",
            "A denser graph with more crossovers and more realistic semantic tradeoffs between dangerous, fragile, and soft-contact objects.",
            lanes=4,
            layers=6,
            lane_objects=lane_objects_4,
            weights=weights_4,
            semantic_focus="semantic-dense",
        )
    )

    weights_5 = {
        "dish_towel": 0.5,
        "cardboard_box": 1.5,
        "knife_block": 8.0,
        "glass_jar": 7.5,
        "soft_pack": 1.0,
        "cross_2_0_1": 1.0,
        "cross_2_1_0": 1.0,
        "cross_2_1_2": 1.0,
        "cross_2_2_1": 1.0,
        "cross_4_0_1": 1.0,
        "cross_4_1_0": 1.0,
        "cross_4_1_2": 1.0,
        "cross_4_2_1": 1.0,
    }
    lane_objects_5 = {}
    for layer in range(1, 7):
        lane_objects_5[(layer, 0)] = ["dish_towel"] if layer < 3 else ["soft_pack"]
        lane_objects_5[(layer, 1)] = ["cardboard_box"]
        lane_objects_5[(layer, 2)] = ["glass_jar"] if layer < 3 else ["soft_pack"]
    conditional_5 = {
        "n4_0->n5_1": [{"if_contains": ["dish_towel"], "adds": ["knife_block"]}],
        "n4_2->n5_1": [{"if_contains": ["glass_jar"], "adds": ["knife_block"]}],
        "n4_1->n5_1": [{"if_contains": ["cardboard_box"], "adds": []}],
    }
    graphs.append(
        layered_graph(
            "history_merge_hazard",
            "History-Conditioned Merge Hazard",
            "The same merge corridor behaves differently depending on what has already been touched. This is the first benchmark where path history genuinely changes future collision additions.",
            lanes=3,
            layers=6,
            lane_objects=lane_objects_5,
            weights=weights_5,
            semantic_focus="history",
            conditional_rules=conditional_5,
        )
    )

    weights_6 = {
        "towel": 0.5,
        "box": 1.5,
        "bag": 1.0,
        "knife": 8.0,
        "acid_bottle": 10.0,
        "glass_plate": 7.0,
        "plastic_wrap": 1.0,
    }
    lane_objects_6 = {}
    for layer in range(1, 7):
        lane_objects_6[(layer, 0)] = ["towel"] if layer < 4 else ["plastic_wrap"]
        lane_objects_6[(layer, 1)] = ["box"]
        lane_objects_6[(layer, 2)] = ["bag"] if layer < 3 else ["glass_plate"]
        lane_objects_6[(layer, 3)] = ["plastic_wrap"] if layer % 2 else ["box"]
    conditional_6 = {
        "n3_1->n4_1": [{"if_contains": ["box"], "adds": ["knife"]}],
        "n4_2->n5_2": [{"if_contains": ["glass_plate"], "adds": ["acid_bottle"]}],
        "n4_0->n5_1": [{"if_contains": ["towel"], "adds": ["knife"]}],
        "n5_1->n6_2": [{"if_contains": ["knife"], "adds": ["acid_bottle"]}],
    }
    graphs.append(
        layered_graph(
            "double_history_benchmark",
            "Double History-Conditioned Benchmark",
            "A larger graph with two different history-triggered hazard mechanisms. This is the strongest benchmark for comparing exact vs greedy under the professor's formulation.",
            lanes=4,
            layers=6,
            lane_objects=lane_objects_6,
            weights=weights_6,
            semantic_focus="history-dense",
            conditional_rules=conditional_6,
        )
    )
    graphs.append(
        large_dense_graph(
            "mega_cardinality_grid",
            "Mega Cardinality Grid",
            "A large static benchmark with over a thousand nodes and over one hundred thousand edges. Intended for large-scale greedy cardinality comparisons and stress-testing frontier growth.",
            lanes=34,
            layers=36,
            base_objects=["rack", "aisle_bin", "crate", "pipe", "barrier", "cart"],
            semantic_weights={
                "rack": 1.0,
                "aisle_bin": 1.0,
                "crate": 1.0,
                "pipe": 1.0,
                "barrier": 1.0,
                "cart": 1.0,
            },
            semantic_focus="large-cardinality",
        )
    )
    graphs.append(
        large_dense_graph(
            "mega_semantic_kitchen",
            "Mega Semantic Kitchen",
            "A large-scale semantic benchmark where thousands of route choices trade severe objects against low-consequence clutter at scale.",
            lanes=36,
            layers=34,
            base_objects=["dish_towel", "sponge", "cardboard_box", "knife_block", "glass_jar", "plastic_wrap"],
            semantic_weights={
                "dish_towel": 0.5,
                "sponge": 1.0,
                "cardboard_box": 1.5,
                "knife_block": 8.0,
                "glass_jar": 7.5,
                "plastic_wrap": 1.0,
            },
            semantic_focus="large-semantic",
        )
    )
    graphs.append(
        large_dense_graph(
            "mega_household_mix",
            "Mega Household Mix",
            "A denser semantic graph with household objects spanning benign, fragile, and hazardous categories. Good for large exact-vs-greedy semantic comparisons when exact is bounded to smaller runs only.",
            lanes=32,
            layers=40,
            base_objects=["towel", "box", "bag", "detergent", "ceramic_bowl", "metal_can", "fruit_pack"],
            semantic_weights={
                "towel": 0.5,
                "box": 1.5,
                "bag": 1.0,
                "detergent": 6.0,
                "ceramic_bowl": 7.0,
                "metal_can": 2.0,
                "fruit_pack": 1.0,
            },
            semantic_focus="large-household",
        )
    )
    graphs.append(
        large_dense_graph(
            "mega_history_merge",
            "Mega History Merge",
            "A large path-conditioned benchmark where conditional hazard additions appear throughout the roadmap. This is the scalable version of the professor-style formulation.",
            lanes=34,
            layers=36,
            base_objects=["dish_towel", "box", "soft_pack", "knife_block", "glass_jar", "plastic_wrap"],
            semantic_weights={
                "dish_towel": 0.5,
                "box": 1.5,
                "soft_pack": 1.0,
                "knife_block": 8.0,
                "glass_jar": 7.5,
                "plastic_wrap": 1.0,
            },
            semantic_focus="large-history",
            conditional_stride=17,
        )
    )
    graphs.append(
        large_dense_graph(
            "mega_double_history",
            "Mega Double History",
            "A larger and harsher history-conditioned benchmark with multiple distributed trigger patterns. Intended to expose single-label pruning failures at scale.",
            lanes=38,
            layers=36,
            base_objects=["towel", "box", "bag", "knife", "acid_bottle", "glass_plate", "plastic_wrap"],
            semantic_weights={
                "towel": 0.5,
                "box": 1.5,
                "bag": 1.0,
                "knife": 8.0,
                "acid_bottle": 10.0,
                "glass_plate": 7.0,
                "plastic_wrap": 1.0,
            },
            semantic_focus="large-history-dense",
            conditional_stride=13,
        )
    )
    return graphs


HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>MCR Benchmark UI</title>
  <style>
    :root {
      --bg: #0b1117;
      --panel: #131b24;
      --panel-2: #0f161d;
      --border: #2a3542;
      --text: #e6edf3;
      --muted: #92a6ba;
      --accent: #60a5fa;
      --accent-2: #4ade80;
      --danger: #f87171;
      --warn: #fbbf24;
      --history: #fb923c;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      color: var(--text);
      font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
      background:
        radial-gradient(circle at 12% 10%, rgba(96,165,250,.10), transparent 22%),
        radial-gradient(circle at 88% 85%, rgba(74,222,128,.08), transparent 18%),
        linear-gradient(180deg, #0b1117, #0d1319 40%, #0b1117);
    }
    .page {
      max-width: 1700px;
      margin: 0 auto;
      padding: 22px;
      display: grid;
      gap: 18px;
    }
    .hero {
      display: grid;
      gap: 10px;
    }
    h1 {
      margin: 0;
      font-size: clamp(28px, 3vw, 40px);
      letter-spacing: -.03em;
    }
    .sub {
      color: var(--muted);
      max-width: 1100px;
      line-height: 1.55;
    }
    .bar, .panel, .card, .stats, .legend {
      background: linear-gradient(180deg, rgba(255,255,255,.02), rgba(255,255,255,0)), var(--panel);
      border: 1px solid var(--border);
      border-radius: 18px;
      box-shadow: inset 0 1px 0 rgba(255,255,255,.02);
    }
    .bar {
      padding: 14px;
      display: grid;
      gap: 14px;
    }
    .control-grid {
      display: grid;
      grid-template-columns: 1.2fr repeat(4, minmax(0, 1fr));
      gap: 12px;
      align-items: end;
    }
    .field {
      display: grid;
      gap: 8px;
    }
    .field label {
      color: var(--muted);
      font-size: 12px;
      letter-spacing: .08em;
      text-transform: uppercase;
    }
    select, input[type="range"] {
      width: 100%;
    }
    select {
      font: inherit;
      color: var(--text);
      background: var(--panel-2);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 12px;
    }
    .button-row {
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
    }
    button {
      font: inherit;
      color: var(--text);
      background: var(--panel-2);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 10px 14px;
      cursor: pointer;
      transition: transform .15s ease, border-color .15s ease;
    }
    button:hover {
      transform: translateY(-1px);
      border-color: var(--accent);
    }
    .graph-bar {
      display: grid;
      grid-template-columns: 1.4fr .9fr;
      gap: 14px;
    }
    .graph-summary, .graph-rules {
      padding: 16px;
    }
    .graph-summary h2, .graph-rules h2 {
      margin: 0 0 10px;
      font-size: 18px;
    }
    .graph-summary p {
      margin: 0 0 12px;
      color: var(--muted);
      line-height: 1.5;
    }
    .chips {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
    }
    .chip {
      background: rgba(255,255,255,.02);
      border: 1px solid var(--border);
      border-radius: 999px;
      padding: 6px 10px;
      color: var(--muted);
      font-size: 12px;
    }
    .rule-list {
      display: grid;
      gap: 8px;
      max-height: 180px;
      overflow: auto;
    }
    .rule {
      background: rgba(251,146,60,.08);
      border: 1px solid rgba(251,146,60,.22);
      border-radius: 12px;
      padding: 10px;
      color: #ffd8b0;
      font-size: 13px;
      line-height: 1.45;
    }
    .bench {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 18px;
    }
    .panel {
      padding: 16px;
      display: grid;
      gap: 14px;
      align-content: start;
    }
    .panel-top {
      display: grid;
      gap: 10px;
    }
    .panel h3 {
      margin: 0;
      font-size: 20px;
    }
    .algo-desc {
      color: var(--muted);
      line-height: 1.45;
      min-height: 44px;
    }
    .stats {
      padding: 14px;
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 10px;
    }
    .stat {
      background: var(--panel-2);
      border: 1px solid var(--border);
      border-radius: 14px;
      padding: 12px;
      min-height: 84px;
    }
    .stat .k {
      color: var(--muted);
      font-size: 12px;
      letter-spacing: .08em;
      text-transform: uppercase;
      margin-bottom: 8px;
    }
    .stat .v {
      font-size: 16px;
      line-height: 1.35;
    }
    .viz {
      padding: 0;
      overflow: hidden;
    }
    svg {
      width: 100%;
      height: auto;
      display: block;
      aspect-ratio: 16 / 9;
      background:
        linear-gradient(180deg, rgba(255,255,255,.02), rgba(255,255,255,0)),
        #0d141b;
    }
    .detail-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 12px;
    }
    .card {
      padding: 14px;
    }
    .card h4 {
      margin: 0 0 10px;
      font-size: 15px;
    }
    .mono {
      white-space: pre-wrap;
      word-break: break-word;
      color: var(--muted);
      font-size: 13px;
      line-height: 1.5;
      margin: 0;
    }
    .legend {
      padding: 12px 14px;
      display: flex;
      gap: 14px;
      flex-wrap: wrap;
      color: var(--muted);
      font-size: 13px;
    }
    .dot {
      width: 12px;
      height: 12px;
      border-radius: 999px;
      display: inline-block;
      margin-right: 6px;
      vertical-align: middle;
    }
    .footer-note {
      color: var(--muted);
      line-height: 1.55;
      padding: 2px 2px 18px;
    }
    @media (max-width: 1250px) {
      .control-grid, .graph-bar, .bench, .detail-grid, .stats {
        grid-template-columns: 1fr;
      }
    }
  </style>
</head>
<body>
  <div class="page">
    <section class="hero">
      <h1>MCR Benchmark UI</h1>
      <div class="sub">
        Choose one benchmark graph, then run two algorithms on that same graph. The app animates search expansions, records runtime and label statistics, and makes the history-conditioned formulation concrete by using edges whose collision additions depend on the path history already accumulated.
      </div>
    </section>

    <section class="bar">
      <div class="control-grid">
        <div class="field">
          <label for="graph-select">Benchmark Graph</label>
          <select id="graph-select"></select>
        </div>
        <div class="field">
          <label for="left-select">Left Algorithm</label>
          <select id="left-select"></select>
        </div>
        <div class="field">
          <label for="right-select">Right Algorithm</label>
          <select id="right-select"></select>
        </div>
        <div class="field">
          <label for="speed-slider">Animation Speed</label>
          <input id="speed-slider" type="range" min="120" max="1400" step="20" value="520">
        </div>
        <div class="field">
          <label>Playback</label>
          <div class="button-row">
            <button id="run-btn">Run</button>
            <button id="pause-btn">Pause</button>
            <button id="step-btn">Step</button>
            <button id="reset-btn">Reset</button>
          </div>
        </div>
      </div>
      <div class="legend">
        <span><span class="dot" style="background:#60a5fa"></span> unexplored node</span>
        <span><span class="dot" style="background:#4ade80"></span> final path</span>
        <span><span class="dot" style="background:#f87171"></span> active expansion</span>
        <span><span class="dot" style="background:#fbbf24"></span> exact/reference path</span>
        <span><span class="dot" style="background:#fb923c"></span> history-conditioned edge</span>
      </div>
    </section>

    <section class="graph-bar">
      <div class="panel graph-summary" id="graph-summary"></div>
      <div class="panel graph-rules" id="graph-rules"></div>
    </section>

    <section class="bench">
      <div class="panel" id="left-panel"></div>
      <div class="panel" id="right-panel"></div>
    </section>

    <div class="footer-note">
      Exact methods keep multiple non-dominated labels per vertex. Greedy methods keep one best-so-far label per vertex. On history-conditioned graphs, that difference is the core benchmark: the same roadmap vertex may need multiple retained labels because future edge effects depend on what happened earlier.
    </div>
  </div>

  <script>
    const GRAPHS = __GRAPH_DATA__;

    const ALGORITHMS = [
      {
        id: "exact_cardinality",
        title: "Exact Discrete MCR",
        objective: "Minimize cardinality of the accumulated collision set.",
        retention: "Keep multiple non-dominated subsets per vertex.",
        pathConditioned: true,
        scoreType: "cardinality",
        exact: true,
      },
      {
        id: "greedy_cardinality",
        title: "Greedy Discrete MCR",
        objective: "Minimize cardinality with one retained label per vertex.",
        retention: "One subset per vertex only.",
        pathConditioned: true,
        scoreType: "cardinality",
        exact: false,
      },
      {
        id: "exact_semantic",
        title: "Exact Semantic MCR",
        objective: "Minimize summed semantic weight of the accumulated collision set.",
        retention: "Keep multiple non-dominated subsets per vertex.",
        pathConditioned: true,
        scoreType: "semantic",
        exact: true,
      },
      {
        id: "greedy_semantic",
        title: "Greedy Semantic MCR",
        objective: "Minimize semantic weight with one retained label per vertex.",
        retention: "One subset per vertex only.",
        pathConditioned: true,
        scoreType: "semantic",
        exact: false,
      },
      {
        id: "exact_path_conditioned",
        title: "Exact Path-Conditioned Semantic MCR",
        objective: "Minimize semantic consequence when edge additions depend on current history.",
        retention: "Keep multiple path-conditioned labels per vertex.",
        pathConditioned: true,
        scoreType: "semantic",
        exact: true,
      },
      {
        id: "greedy_path_conditioned",
        title: "Greedy Path-Conditioned Semantic MCR",
        objective: "Approximate the history-conditioned problem with one retained label per vertex.",
        retention: "One path-conditioned label per vertex.",
        pathConditioned: true,
        scoreType: "semantic",
        exact: false,
      },
    ];

    const state = {
      graphId: GRAPHS[0].id,
      leftAlgo: "exact_cardinality",
      rightAlgo: "greedy_cardinality",
      speed: 520,
      playing: false,
      frame: 0,
      timer: null,
      cache: {},
    };

    function getGraph() {
      return GRAPHS.find(graph => graph.id === state.graphId);
    }

    function getAlgorithm(id) {
      return ALGORITHMS.find(item => item.id === id);
    }

    function setOptions() {
      const graphSelect = document.getElementById("graph-select");
      graphSelect.innerHTML = GRAPHS.map(graph => `<option value="${graph.id}">${graph.title}</option>`).join("");
      graphSelect.value = state.graphId;
      graphSelect.addEventListener("change", event => {
        state.graphId = event.target.value;
        invalidateCache();
        resetPlayback();
        renderAll();
      });

      for (const [elementId, key] of [["left-select", "leftAlgo"], ["right-select", "rightAlgo"]]) {
        const select = document.getElementById(elementId);
        select.innerHTML = ALGORITHMS.map(algo => `<option value="${algo.id}">${algo.title}</option>`).join("");
        select.value = state[key];
        select.addEventListener("change", event => {
          state[key] = event.target.value;
          resetPlayback();
          renderAll();
        });
      }

      const speed = document.getElementById("speed-slider");
      speed.value = String(state.speed);
      speed.addEventListener("input", event => {
        state.speed = Number(event.target.value);
        if (state.playing) startPlayback();
      });
    }

    function invalidateCache() {
      state.cache = {};
    }

    function canonicalSubset(items) {
      return Array.from(new Set(items)).sort();
    }

    function subsetKey(items) {
      return canonicalSubset(items).join("|");
    }

    function subsetLabel(items) {
      const canonical = canonicalSubset(items);
      return canonical.length ? `{${canonical.join(",")}}` : "{}";
    }

    function subsetWeight(items, weights) {
      return canonicalSubset(items).reduce((sum, item) => sum + (weights[item] || 1), 0);
    }

    function applyEdge(subset, edge) {
      const next = new Set(subset);
      for (const item of edge.adds || []) next.add(item);
      for (const rule of edge.conditional || []) {
        const ok = (rule.if_contains || []).every(item => next.has(item) || subset.has(item));
        if (ok) {
          for (const item of rule.adds || []) next.add(item);
        }
      }
      return canonicalSubset(Array.from(next));
    }

    function scoreSubset(subset, graph, algo) {
      if (algo.scoreType === "semantic") return subsetWeight(subset, graph.weights);
      return canonicalSubset(subset).length;
    }

    function isSubset(left, right) {
      const rightSet = new Set(right);
      return left.every(item => rightSet.has(item));
    }

    function buildAdjacency(graph) {
      const adjacency = new Map();
      for (const node of graph.nodes) adjacency.set(node.id, []);
      for (const edge of graph.edges) {
        adjacency.get(edge.source).push(edge);
      }
      return adjacency;
    }

    function reconstructPath(parentMap, stateKey) {
      const path = [];
      let current = stateKey;
      while (current) {
        const [vertex] = current.split("::");
        path.push(vertex);
        current = parentMap.get(current) || null;
      }
      return path.reverse();
    }

    function runAlgorithm(graph, algo) {
      const t0 = performance.now();
      const adjacency = buildAdjacency(graph);
      const startKey = "start::";
      const queue = [{ priority: 0, order: 0, vertex: "start", subset: [] }];
      let order = 1;
      const parentMap = new Map([[startKey, null]]);
      const traces = [];
      let popped = 0;

      if (algo.exact) {
        if (graph.scale === "large") {
          return {
            path: [],
            subset: [],
            score: Number.POSITIVE_INFINITY,
            expanded: 0,
            runtimeMs: +(performance.now() - t0).toFixed(3),
            trace: [],
            labelPolicy: `${algo.retention} (disabled on large-scale benchmark)`,
            status: "disabled_large_exact",
            message: "Exact search is disabled on large-scale benchmarks to keep the UI responsive. Use greedy variants here, and use exact variants on the smaller benchmark set.",
          };
        }
        const labels = new Map(graph.nodes.map(node => [node.id, []]));
        labels.set("start", [[]]);
        while (queue.length) {
          queue.sort((a, b) => a.priority - b.priority || a.order - b.order);
          const current = queue.shift();
          popped += 1;
          const stateKey = `${current.vertex}::${subsetKey(current.subset)}`;
          const retained = labels.get(current.vertex) || [];
          if (retained.some(existing => existing.length < current.subset.length && isSubset(existing, current.subset))) {
            continue;
          }
          traces.push({
            step: traces.length,
            vertex: current.vertex,
            subset: current.subset,
            score: scoreSubset(current.subset, graph, algo),
            queueSize: queue.length,
            labelCounts: Object.fromEntries(Array.from(labels.entries()).map(([vertex, subsets]) => [vertex, subsets.length])),
          });
          if (current.vertex === "goal") {
            const path = reconstructPath(parentMap, stateKey);
            const t1 = performance.now();
            return {
              path,
              subset: current.subset,
              score: scoreSubset(current.subset, graph, algo),
              expanded: popped,
              runtimeMs: +(t1 - t0).toFixed(3),
              trace: traces,
              labelPolicy: algo.retention,
            };
          }
          for (const edge of adjacency.get(current.vertex) || []) {
            const nextSubset = applyEdge(new Set(current.subset), edge);
            const nextLabels = labels.get(edge.target) || [];
            let dominated = false;
            const filtered = [];
            for (const existing of nextLabels) {
              if (isSubset(existing, nextSubset)) {
                dominated = true;
              } else if (!isSubset(nextSubset, existing)) {
                filtered.push(existing);
              }
            }
            if (dominated) continue;
            filtered.push(nextSubset);
            labels.set(edge.target, filtered);
            const nextKey = `${edge.target}::${subsetKey(nextSubset)}`;
            parentMap.set(nextKey, stateKey);
            queue.push({
              priority: scoreSubset(nextSubset, graph, algo),
              order: order++,
              vertex: edge.target,
              subset: nextSubset,
            });
          }
        }
      } else {
        const best = new Map(graph.nodes.map(node => [node.id, null]));
        best.set("start", []);
        const visited = new Set();
        while (queue.length) {
          queue.sort((a, b) => a.priority - b.priority || a.order - b.order);
          const current = queue.shift();
          popped += 1;
          if (visited.has(current.vertex)) continue;
          visited.add(current.vertex);
          const stateKey = `${current.vertex}::${subsetKey(current.subset)}`;
          traces.push({
            step: traces.length,
            vertex: current.vertex,
            subset: current.subset,
            score: scoreSubset(current.subset, graph, algo),
            queueSize: queue.length,
            labelCounts: Object.fromEntries(Array.from(best.entries()).map(([vertex, subset]) => [vertex, subset ? 1 : 0])),
          });
          if (current.vertex === "goal") {
            const path = reconstructPath(parentMap, stateKey);
            const t1 = performance.now();
            return {
              path,
              subset: current.subset,
              score: scoreSubset(current.subset, graph, algo),
              expanded: popped,
              runtimeMs: +(t1 - t0).toFixed(3),
              trace: traces,
              labelPolicy: algo.retention,
            };
          }
          for (const edge of adjacency.get(current.vertex) || []) {
            const nextSubset = applyEdge(new Set(current.subset), edge);
            const currentBest = best.get(edge.target);
            const nextScore = scoreSubset(nextSubset, graph, algo);
            const bestScore = currentBest ? scoreSubset(currentBest, graph, algo) : Number.POSITIVE_INFINITY;
            if (!currentBest || nextScore < bestScore) {
              best.set(edge.target, nextSubset);
              const nextKey = `${edge.target}::${subsetKey(nextSubset)}`;
              parentMap.set(nextKey, stateKey);
              queue.push({
                priority: nextScore,
                order: order++,
                vertex: edge.target,
                subset: nextSubset,
              });
            }
          }
        }
      }
      return {
        path: [],
        subset: [],
        score: Infinity,
        expanded: popped,
        runtimeMs: +(performance.now() - t0).toFixed(3),
        trace: traces,
        labelPolicy: algo.retention,
        status: "no_path",
      };
    }

    function getResult(graph, algoId) {
      const key = `${graph.id}::${algoId}`;
      if (!state.cache[key]) {
        state.cache[key] = runAlgorithm(graph, getAlgorithm(algoId));
      }
      return state.cache[key];
    }

    function graphStats(graph) {
      const historyEdges = graph.edges.filter(edge => (edge.conditional || []).length > 0).length;
      const objectCount = Object.keys(graph.weights).length;
      return [
        { label: "nodes", value: String(graph.nodes.length) },
        { label: "edges", value: String(graph.edges.length) },
        { label: "scale", value: graph.scale },
        { label: "objects", value: String(objectCount) },
        { label: "history edges", value: String(historyEdges) },
        { label: "focus", value: graph.semantic_focus },
      ];
    }

    function renderGraphSummary() {
      const graph = getGraph();
      const stats = graphStats(graph);
      document.getElementById("graph-summary").innerHTML = `
        <h2>${graph.title}</h2>
        <p>${graph.description}</p>
        <div class="chips">${stats.map(item => `<span class="chip">${item.label}: ${item.value}</span>`).join("")}</div>
      `;
      const rules = graph.conditional_rules;
      document.getElementById("graph-rules").innerHTML = `
        <h2>Conditional Transitions</h2>
        ${rules.length ? `<div class="rule-list">${rules.map(rule => `
          <div class="rule">
            <strong>${rule.edge}</strong><br>
            if subset contains ${rule.if_contains.join(", ") || "{}"} then also add ${rule.adds.join(", ") || "{}"}
          </div>`).join("")}</div>` : `<div class="rule">This graph has only static collision additions. It behaves like standard discrete / semantic MCR.</div>`}
      `;
    }

    function optionMarkup(current) {
      return ALGORITHMS.map(algo => `<option value="${algo.id}" ${algo.id === current ? "selected" : ""}>${algo.title}</option>`).join("");
    }

    function nodeMap(graph) {
      return Object.fromEntries(graph.nodes.map(node => [node.id, node]));
    }

    function normalize(graph, nodeId) {
      const nodes = graph.nodes;
      const node = nodeMap(graph)[nodeId];
      const xs = nodes.map(item => item.x);
      const ys = nodes.map(item => item.y);
      const minX = Math.min(...xs);
      const maxX = Math.max(...xs);
      const minY = Math.min(...ys);
      const maxY = Math.max(...ys);
      const x = 60 + ((node.x - minX) / Math.max(1, maxX - minX)) * 840;
      const y = 350 - ((node.y - minY) / Math.max(1, maxY - minY)) * 260;
      return { x, y };
    }

    function edgeSetFromPath(path) {
      const set = new Set();
      for (let i = 0; i < path.length - 1; i += 1) {
        set.add(`${path[i]}|${path[i + 1]}`);
      }
      return set;
    }

    function edgeLabel(edge) {
      const base = edge.adds.length ? `+${edge.adds.join(",")}` : "+{}";
      if (!(edge.conditional || []).length) return base;
      const parts = edge.conditional.map(rule => `if ${rule.if_contains.join("&")}=>+${rule.adds.join(",")}`);
      return `${base}; ${parts.join("; ")}`;
    }

    function renderSvg(graph, result, frame) {
      const trace = result.trace;
      const active = trace[Math.min(frame, Math.max(0, trace.length - 1))];
      const visited = new Set(trace.slice(0, Math.min(frame + 1, trace.length)).map(step => step.vertex));
      const pathEdges = edgeSetFromPath(result.path);
      const nodesById = nodeMap(graph);
      const lines = [];
      const labels = [];
      const circles = [];

      const visibleEdges = graph.scale === "large" ? (graph.preview_edges || []) : graph.edges;
      for (const edge of visibleEdges) {
        const p1 = normalize(graph, edge.source);
        const p2 = normalize(graph, edge.target);
        let stroke = "#32404f";
        let width = 2.5;
        if ((edge.conditional || []).length) {
          stroke = "#fb923c";
          width = 3.5;
        }
        if (pathEdges.has(`${edge.source}|${edge.target}`)) {
          stroke = "#4ade80";
          width = 6;
        }
        lines.push(`<line x1="${p1.x}" y1="${p1.y}" x2="${p2.x}" y2="${p2.y}" stroke="${stroke}" stroke-width="${width}" stroke-linecap="round" opacity="0.95"/>`);

        if ((edge.conditional || []).length) {
          const mx = (p1.x + p2.x) / 2;
          const my = (p1.y + p2.y) / 2;
          labels.push(`<text x="${mx - 42}" y="${my - 8}" fill="#ffd8b0" font-size="11" font-family="monospace">history</text>`);
        }
      }

      for (const node of graph.nodes) {
        const p = normalize(graph, node.id);
        let fill = visited.has(node.id) ? "#60a5fa" : "#314152";
        let radius = 15;
        if (node.id === "start" || node.id === "goal") fill = "#fbbf24";
        if (active && active.vertex === node.id) {
          fill = "#f87171";
          radius = 19;
        }
        circles.push(`<circle cx="${p.x}" cy="${p.y}" r="${radius}" fill="${fill}" stroke="#0b1117" stroke-width="3">
          <animate attributeName="r" values="${radius};${radius + 2};${radius}" dur="1.1s" repeatCount="indefinite" />
        </circle>`);
        labels.push(`<text x="${p.x - 18}" y="${p.y - 24}" fill="#e6edf3" font-size="12" font-family="monospace">${node.id}</text>`);
      }

      if (graph.scale === "large") {
        labels.push(`<text x="26" y="24" fill="#92a6ba" font-size="12" font-family="monospace">previewing sampled edges only; algorithms run on full ${graph.edges.length} edges</text>`);
      }
      return `<svg viewBox="0 0 960 420" preserveAspectRatio="xMidYMid meet">${lines.join("")}${circles.join("")}${labels.join("")}</svg>`;
    }

    function formatStats(result, graph) {
      const scoreValue = Number.isFinite(result.score)
        ? (result.score.toFixed ? result.score.toFixed(2) : String(result.score))
        : "n/a";
      return [
        { label: "Runtime", value: `${result.runtimeMs.toFixed(3)} ms` },
        { label: "Expanded", value: String(result.expanded) },
        { label: "Final set", value: subsetLabel(result.subset) },
        { label: "Score", value: scoreValue },
        { label: "Cardinality", value: String(canonicalSubset(result.subset).length) },
        { label: "Semantic weight", value: subsetWeight(result.subset, graph.weights).toFixed(2) },
        { label: "Path length", value: String(result.path.length ? result.path.length - 1 : 0) },
        { label: "Label policy", value: result.labelPolicy },
      ];
    }

    function statsMarkup(stats) {
      return `<div class="stats">${stats.map(item => `
        <div class="stat">
          <div class="k">${item.label}</div>
          <div class="v">${item.value}</div>
        </div>`).join("")}
      </div>`;
    }

    function traceText(result, frame) {
      if (result.status === "disabled_large_exact") {
        return {
          step: result.message,
          labels: "No labels recorded because this run was intentionally skipped.",
        };
      }
      const step = result.trace[Math.min(frame, Math.max(0, result.trace.length - 1))];
      if (!step) {
        return {
          step: "No trace.",
          labels: "No labels recorded.",
        };
      }
      const counts = Object.entries(step.labelCounts || {}).slice(0, 10).map(([node, count]) => `${node}: ${count}`).join("\\n");
      return {
        step: [
          `step: ${step.step + 1} / ${result.trace.length}`,
          `expand: ${step.vertex}`,
          `subset: ${subsetLabel(step.subset)}`,
          `score: ${step.score.toFixed ? step.score.toFixed(2) : step.score}`,
          `queue size: ${step.queueSize}`,
        ].join("\\n"),
        labels: counts || "No label counts.",
      };
    }

    function renderPanel(side, algoId) {
      const graph = getGraph();
      const algo = getAlgorithm(algoId);
      const result = getResult(graph, algoId);
      const trace = traceText(result, state.frame);
      const root = document.getElementById(`${side}-panel`);
      root.innerHTML = `
        <div class="panel-top">
          <div class="field">
            <label for="${side}-algo">Algorithm</label>
            <select id="${side}-algo">${optionMarkup(algoId)}</select>
          </div>
          <h3>${algo.title}</h3>
        <div class="algo-desc">${algo.objective} ${algo.retention}</div>
        </div>
        ${statsMarkup(formatStats(result, graph))}
        ${result.status === "disabled_large_exact" ? `<div class="card"><h4>Large-Scale Guard</h4><pre class="mono">${result.message}</pre></div>` : ""}
        <div class="card viz" id="${side}-viz">${renderSvg(graph, result, state.frame)}</div>
        <div class="detail-grid">
          <div class="card">
            <h4>Current Expansion</h4>
            <pre class="mono">${trace.step}</pre>
          </div>
          <div class="card">
            <h4>Stored Label Counts</h4>
            <pre class="mono">${trace.labels}</pre>
          </div>
          <div class="card">
            <h4>Search Criteria</h4>
            <pre class="mono">objective: ${algo.objective}
label retention: ${algo.retention}
history-aware transitions: ${algo.pathConditioned ? "yes" : "no"}</pre>
          </div>
          <div class="card">
            <h4>Result Path</h4>
            <pre class="mono">${result.path.join(" -> ") || "no path"}</pre>
          </div>
        </div>
      `;
      document.getElementById(`${side}-algo`).addEventListener("change", event => {
        if (side === "left") state.leftAlgo = event.target.value;
        else state.rightAlgo = event.target.value;
        resetPlayback();
        renderAll();
      });
    }

    function maxTraceLength() {
      const graph = getGraph();
      return Math.max(
        getResult(graph, state.leftAlgo).trace.length,
        getResult(graph, state.rightAlgo).trace.length,
      );
    }

    function resetPlayback() {
      stopPlayback();
      state.frame = 0;
    }

    function stopPlayback() {
      state.playing = false;
      if (state.timer) clearInterval(state.timer);
      state.timer = null;
    }

    function startPlayback() {
      stopPlayback();
      state.playing = true;
      state.timer = setInterval(() => {
        const max = Math.max(0, maxTraceLength() - 1);
        if (state.frame >= max) {
          stopPlayback();
          renderAll();
          return;
        }
        state.frame += 1;
        renderPanelsOnly();
      }, state.speed);
    }

    function renderPanelsOnly() {
      renderPanel("left", state.leftAlgo);
      renderPanel("right", state.rightAlgo);
    }

    function renderAll() {
      renderGraphSummary();
      renderPanelsOnly();
    }

    document.getElementById("run-btn").addEventListener("click", () => {
      if (state.frame >= Math.max(0, maxTraceLength() - 1)) state.frame = 0;
      startPlayback();
    });
    document.getElementById("pause-btn").addEventListener("click", () => {
      stopPlayback();
      renderAll();
    });
    document.getElementById("step-btn").addEventListener("click", () => {
      stopPlayback();
      const max = Math.max(0, maxTraceLength() - 1);
      state.frame = Math.min(max, state.frame + 1);
      renderAll();
    });
    document.getElementById("reset-btn").addEventListener("click", () => {
      resetPlayback();
      renderAll();
    });

    setOptions();
    renderAll();
  </script>
</body>
</html>
"""


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    graphs = build_graphs()
    html = HTML.replace("__GRAPH_DATA__", json.dumps(graphs))
    OUTPUT_HTML.write_text(html, encoding="utf-8")
    print(f"Built benchmark UI at {OUTPUT_HTML}")


if __name__ == "__main__":
    main()
