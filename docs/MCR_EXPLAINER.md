# MCR Explainer

This is the starting point for building explanatory visualizations around the core Minimum Constraint Removal problem from [papers/mcr.pdf](/home/shiraku/Documents/code/mcr/papers/mcr.pdf).

## Core Idea
The original formulation is not optimizing path length. It is optimizing the size of the union of violated constraints along a path.

For the discrete graph version:
1. Each vertex `v` has a cover `C[v]`, the set of violated constraints at that node.
2. A path explanation is the union of covers over every vertex on that path.
3. The MCR solution is the path whose union has minimum cardinality.

That means:
- a longer path can be better than a shorter one
- a path with repeated exposure to the same obstacle can still be cheap
- the search state is not just the current vertex
- the search state is `(vertex, subset-of-constraints-seen-so-far)`

## Why Two Algorithms
The paper uses two discrete subroutines:

1. Exact search
It keeps multiple irreducible subsets per vertex.
This is optimal, but can blow up combinatorially.

2. Greedy search
It keeps only one smallest subset per vertex.
This is fast, but can be suboptimal on adversarial examples.

## New Visualization Scaffold
Run:

```bash
python scripts/mcr_core_visualization.py
```

Outputs are written to:

`outputs/mcr_core_explainer/`

Current figures:
- `mcr_formulation_summary.png`
- `core_exact_iterations.png`
- `core_greedy_iterations.png`
- `greedy_failure_comparison.png`

## Why This Matters For The Next Formulation
Before comparing your professor’s new formulation, we need a baseline visualization language that makes these questions obvious:

1. What is the state?
2. What is the objective?
3. What gets accumulated as the path grows?
4. Why do exact and greedy diverge?
5. What changes when weights, semantics, or uncertainty are introduced?

This scaffold is intended to become that baseline.
