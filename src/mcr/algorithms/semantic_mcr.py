from __future__ import annotations

from dataclasses import dataclass
import heapq
import itertools


Graph = dict[str, tuple[str, ...]]


@dataclass
class SemanticObject:
    object_id: str
    display_name: str
    safety_score: float
    category: str
    semantic_weight: float
    rationale: str
    removable: bool = True


def subset_label(subset: frozenset[str]) -> str:
    if not subset:
        return "{}"
    return "{" + ",".join(sorted(subset)) + "}"


def subset_weight(subset: frozenset[str], weights: dict[str, float]) -> float:
    return sum(weights[item] for item in subset)


def make_undirected_graph(edges: list[tuple[str, str]]) -> Graph:
    adjacency: dict[str, set[str]] = {}
    for left, right in edges:
        adjacency.setdefault(left, set()).add(right)
        adjacency.setdefault(right, set()).add(left)
    return {
        vertex: tuple(sorted(neighbors))
        for vertex, neighbors in adjacency.items()
    }


def weighted_mcr_greedy(
    graph: Graph,
    cover: dict[str, frozenset[str]],
    weights: dict[str, float],
    start: str,
    goal: str,
):
    counter = itertools.count()
    start_subset = cover[start]
    pq = [(subset_weight(start_subset, weights), next(counter), start, start_subset)]
    best_subset: dict[str, frozenset[str] | None] = {node: None for node in graph}
    best_subset[start] = start_subset
    parent: dict[tuple[str, frozenset[str]], tuple[str, frozenset[str]] | None] = {
        (start, start_subset): None
    }
    trace = []
    visited = set()
    goal_state = None

    while pq:
        current_cost, _, vertex, subset = heapq.heappop(pq)
        if vertex in visited:
            continue
        visited.add(vertex)
        trace.append((vertex, subset, current_cost))
        if vertex == goal:
            goal_state = (vertex, subset)
            break

        for neighbor in graph[vertex]:
            next_subset = subset | cover[neighbor]
            current_best = best_subset[neighbor]
            next_cost = subset_weight(next_subset, weights)
            if current_best is None or next_cost < subset_weight(current_best, weights):
                best_subset[neighbor] = next_subset
                parent[(neighbor, next_subset)] = (vertex, subset)
                heapq.heappush(pq, (next_cost, next(counter), neighbor, next_subset))

    if goal_state is None:
        raise RuntimeError("Weighted greedy MCR failed to reach the goal")

    path = []
    state = goal_state
    while state is not None:
        path.append(state[0])
        state = parent[state]
    path.reverse()

    return {
        "path": path,
        "subset": goal_state[1],
        "cost": subset_weight(goal_state[1], weights),
        "trace": trace,
    }


def cardinality_mcr_greedy(
    graph: Graph,
    cover: dict[str, frozenset[str]],
    start: str,
    goal: str,
):
    unit_weights = {
        object_id: 1.0
        for subset in cover.values()
        for object_id in subset
    }
    return weighted_mcr_greedy(graph, cover, unit_weights, start, goal)


def build_semantic_demo():
    edges = [
        ("start", "fragile_route_1"),
        ("fragile_route_1", "fragile_route_2"),
        ("fragile_route_2", "goal"),
        ("start", "soft_route_1"),
        ("soft_route_1", "soft_route_2"),
        ("soft_route_2", "soft_route_3"),
        ("soft_route_3", "goal"),
    ]
    graph = make_undirected_graph(edges)
    positions = {
        "start": (0.0, 0.0),
        "fragile_route_1": (1.2, 1.0),
        "fragile_route_2": (2.4, 1.0),
        "soft_route_1": (1.0, -0.8),
        "soft_route_2": (2.0, -1.1),
        "soft_route_3": (3.0, -0.8),
        "goal": (4.1, 0.0),
    }
    scene_objects = {
        "fragile_vase": SemanticObject(
            object_id="fragile_vase",
            display_name="Fragile vase",
            safety_score=0.94,
            category="fragile",
            semantic_weight=9.0,
            rationale="High breakage risk; should be treated as near-hard constraint.",
        ),
        "knife_block": SemanticObject(
            object_id="knife_block",
            display_name="Knife block",
            safety_score=0.91,
            category="dangerous",
            semantic_weight=8.0,
            rationale="Sharp / hazardous object; collision should be strongly discouraged.",
        ),
        "cardboard_box": SemanticObject(
            object_id="cardboard_box",
            display_name="Empty box",
            safety_score=0.18,
            category="soft-contact",
            semantic_weight=1.5,
            rationale="Cheap to bump or push aside.",
        ),
        "dish_towel": SemanticObject(
            object_id="dish_towel",
            display_name="Dish towel",
            safety_score=0.08,
            category="soft-contact",
            semantic_weight=0.5,
            rationale="Benign cloth contact.",
        ),
        "sponge": SemanticObject(
            object_id="sponge",
            display_name="Sponge",
            safety_score=0.12,
            category="soft-contact",
            semantic_weight=1.0,
            rationale="Minor clutter item with low consequence.",
        ),
    }
    cover = {
        "start": frozenset(),
        "fragile_route_1": frozenset({"fragile_vase"}),
        "fragile_route_2": frozenset({"fragile_vase", "knife_block"}),
        "soft_route_1": frozenset({"dish_towel"}),
        "soft_route_2": frozenset({"dish_towel", "cardboard_box"}),
        "soft_route_3": frozenset({"dish_towel", "cardboard_box", "sponge"}),
        "goal": frozenset(),
    }
    weights = {
        object_id: obj.semantic_weight for object_id, obj in scene_objects.items()
    }
    return graph, positions, cover, scene_objects, weights, "start", "goal"
