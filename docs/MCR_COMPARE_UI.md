# MCR Compare UI

This page is the side-by-side interactive explainer for the MCR formulations you
care about right now:

1. Continuous MCR with PRM reduction
2. Discrete MCR problem statement
3. Exact discrete search
4. Greedy discrete search
5. Semantic-weighted MCR
6. Path-conditioned semantic MCR from your professor's idea

## Build

```bash
python scripts/build_mcr_compare_ui.py
```

## Output

`outputs/mcr_compare_ui/index.html`

Open that file in a browser locally.

## What The UI Emphasizes

- the objective being optimized
- the search state
- whether one label per vertex is enough
- where exact and greedy differ
- why semantic weights change the preferred path
- why the professor's path-conditioned idea needs multi-label state

## Reading The Panels

- The selector at the top of each panel chooses the formulation.
- If a formulation has a trace, the slider steps through the search.
- The graph view highlights the selected method's preferred path.
- For greedy and semantic views, the reference path shows what the stronger
  baseline would prefer.
