# MCR Benchmark UI

This is the benchmark-style interactive UI for comparing two MCR algorithms on
the same graph.

## Build

```bash
python scripts/build_mcr_benchmark_ui.py
```

## Output

`outputs/mcr_benchmark_ui/index.html`

## What It Adds

- one selected graph shared by both panels
- animated search traces
- runtime and expansion statistics
- exact vs greedy comparisons on the same benchmark
- semantic-weighted and path-conditioned variants
- explicit conditional transition rules for the professor's formulation
- large-scale graphs with 1000+ nodes and 100000+ edges
- sampled large-graph rendering so the UI stays responsive

## Benchmark Set

The page currently includes 11 graphs:

1. Warehouse Cardinality Tradeoff
2. Expanded Greedy Failure
3. Kitchen Semantic Benchmark
4. Dense Household Semantic Mix
5. History-Conditioned Merge Hazard
6. Double History-Conditioned Benchmark
7. Mega Cardinality Grid
8. Mega Semantic Kitchen
9. Mega Household Mix
10. Mega History Merge
11. Mega Double History

## Large-Scale Behavior

For the 5 mega-scale benchmarks, the app runs algorithms on the full graph but
renders a sampled edge preview so the browser does not need to draw 100k+ SVG
segments at once.

Exact methods are intentionally disabled on the mega-scale graphs. That is a UI
guardrail rather than a modeling claim. The exact variants still run and animate on
the smaller benchmark set, including the path-conditioned graphs.

## Recommended Comparisons

- `Exact Discrete MCR` vs `Greedy Discrete MCR` on `Expanded Greedy Failure`
- `Exact Semantic MCR` vs `Greedy Semantic MCR` on `Kitchen Semantic Benchmark`
- `Exact Path-Conditioned Semantic MCR` vs `Greedy Path-Conditioned Semantic MCR`
  on `History-Conditioned Merge Hazard` or `Double History-Conditioned Benchmark`
- `Greedy Discrete MCR` vs `Greedy Semantic MCR` on `Mega Semantic Kitchen`
- `Greedy Semantic MCR` vs `Greedy Path-Conditioned Semantic MCR` on `Mega History Merge`
