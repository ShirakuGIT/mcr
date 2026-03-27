from __future__ import annotations

from dataclasses import dataclass
import heapq
import itertools
from typing import Any

import networkx as nx


@dataclass
class TraceStep:
    algorithm: str
    step_index: int
    vertex: str
    subset: frozenset[str]
    frontier: list[tuple[str, frozenset[str]]]
    best_subsets: dict[str, list[frozenset[str]]]


def subset_label(subset: frozenset[str]) -> str:
    if not subset:
        return "{}"
    return "{" + ",".join(sorted(subset)) + "}"


def reconstruct_path(parents: dict[tuple[str, frozenset[str]], tuple[str, frozenset[str]] | None], end_state):
    path = []
    current = end_state
    while current is not None:
        path.append(current[0])
        current = parents[current]
    return list(reversed(path))


def exact_mcr_trace(
    graph: nx.Graph,
    cover: dict[str, frozenset[str]],
    start: str,
    goal: str,
):
    counter = itertools.count()
    start_subset = cover[start]
    pq = [(len(start_subset), next(counter), start, start_subset)]
    best_subsets: dict[str, list[frozenset[str]]] = {node: [] for node in graph.nodes()}
    best_subsets[start] = [start_subset]
    parents: dict[tuple[str, frozenset[str]], tuple[str, frozenset[str]] | None] = {
        (start, start_subset): None
    }
    trace: list[TraceStep] = []
    goal_state = None

    while pq:
        _, _, vertex, subset = heapq.heappop(pq)
        if any(existing < subset for existing in best_subsets[vertex]):
            continue

        frontier_snapshot = [(v, s) for _, _, v, s in pq]
        trace.append(
            TraceStep(
                algorithm="exact",
                step_index=len(trace),
                vertex=vertex,
                subset=subset,
                frontier=frontier_snapshot,
                best_subsets={k: list(v) for k, v in best_subsets.items()},
            )
        )

        if vertex == goal:
            goal_state = (vertex, subset)
            break

        for neighbor in graph.neighbors(vertex):
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
            heapq.heappush(
                pq,
                (len(next_subset), next(counter), neighbor, next_subset),
            )

    if goal_state is None:
        raise RuntimeError("Exact MCR failed to reach the goal")

    return {
        "goal_subset": goal_state[1],
        "goal_state": goal_state,
        "path": reconstruct_path(parents, goal_state),
        "trace": trace,
    }


def greedy_mcr_trace(
    graph: nx.Graph,
    cover: dict[str, frozenset[str]],
    start: str,
    goal: str,
):
    counter = itertools.count()
    start_subset = cover[start]
    pq = [(len(start_subset), next(counter), start, start_subset)]
    best_subset: dict[str, frozenset[str] | None] = {node: None for node in graph.nodes()}
    best_subset[start] = start_subset
    parents: dict[tuple[str, frozenset[str]], tuple[str, frozenset[str]] | None] = {
        (start, start_subset): None
    }
    trace: list[TraceStep] = []
    visited: set[str] = set()
    goal_state = None

    while pq:
        _, _, vertex, subset = heapq.heappop(pq)
        if vertex in visited:
            continue
        visited.add(vertex)

        frontier_snapshot = [(v, s) for _, _, v, s in pq]
        trace.append(
            TraceStep(
                algorithm="greedy",
                step_index=len(trace),
                vertex=vertex,
                subset=subset,
                frontier=frontier_snapshot,
                best_subsets={
                    k: ([] if v is None else [v]) for k, v in best_subset.items()
                },
            )
        )

        if vertex == goal:
            goal_state = (vertex, subset)
            break

        for neighbor in graph.neighbors(vertex):
            next_subset = subset | cover[neighbor]
            current_best = best_subset[neighbor]
            if current_best is None or len(next_subset) < len(current_best):
                best_subset[neighbor] = next_subset
                parents[(neighbor, next_subset)] = (vertex, subset)
                heapq.heappush(
                    pq,
                    (len(next_subset), next(counter), neighbor, next_subset),
                )

    if goal_state is None:
        raise RuntimeError("Greedy MCR failed to reach the goal")

    return {
        "goal_subset": goal_state[1],
        "goal_state": goal_state,
        "path": reconstruct_path(parents, goal_state),
        "trace": trace,
    }


def build_core_mcr_example():
    graph = nx.Graph()
    edges = [
        ("s", "a"),
        ("a", "b"),
        ("b", "t"),
        ("s", "c"),
        ("c", "d"),
        ("d", "t"),
        ("a", "d"),
    ]
    graph.add_edges_from(edges)
    positions = {
        "s": (0.0, 0.0),
        "a": (1.0, 1.0),
        "b": (2.0, 1.0),
        "c": (1.0, -1.0),
        "d": (2.0, -1.0),
        "t": (3.0, 0.0),
    }
    cover = {
        "s": frozenset(),
        "a": frozenset({"O1"}),
        "b": frozenset({"O1", "O2"}),
        "c": frozenset({"O3"}),
        "d": frozenset({"O2"}),
        "t": frozenset(),
    }
    return graph, positions, cover, "s", "t"


def build_greedy_failure_example():
    graph = nx.Graph()
    positions = {
        "s": (0.0, 0.0),
        "u1": (1.0, 1.0),
        "u2": (2.0, 1.0),
        "u3": (3.0, 1.0),
        "v1": (1.0, -1.0),
        "v2": (2.0, -1.0),
        "v3": (3.0, -1.0),
        "t": (4.0, 0.0),
    }
    graph.add_edges_from(
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
    cover = {
        "s": frozenset(),
        "u1": frozenset({"O1"}),
        "u2": frozenset({"O1", "O2"}),
        "u3": frozenset({"O2"}),
        "v1": frozenset({"O3"}),
        "v2": frozenset({"O4"}),
        "v3": frozenset({"O5"}),
        "t": frozenset(),
    }
    return graph, positions, cover, "s", "t"
