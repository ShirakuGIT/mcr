# Semantic MCR

This note captures the semantic-weighted variant you described:

1. A visual language model looks at a scene.
2. It assigns safety-relevant judgments to objects.
3. Those judgments are converted into semantic weights.
4. MCR then prefers paths that collide with lower-consequence objects.

## Intuition
Classical MCR minimizes the number of violated constraints.

Semantic MCR changes the objective to something like:

`minimize sum of semantic weights of objects in the path-level collision set`

That means:
- colliding with one dangerous object can be worse than colliding with three benign objects
- the VLM is not choosing the path directly
- the VLM is providing semantic structure for the optimization objective

## Object Roles
A useful first taxonomy is:

1. Soft-contact
Low semantic weight.
Examples: towel, sponge, empty cardboard box.

2. Removable / manipulable
Medium semantic weight.
Examples: light pantry items that can be moved if necessary.

3. Hard or near-hard constraints
Very high semantic weight.
Examples: fragile vase, knife block, hazardous chemical bottle.

4. Forbidden
Effectively infinite weight.
Examples: objects that must never be contacted or moved.

## Important Modeling Point
If collision sets depend on which roadmap edges were taken, then the same roadmap vertex can correspond to multiple accumulated collision sets.

So the state is no longer just:

`vertex`

It becomes:

`(vertex, accumulated collision set)`

That is why naive greedy per-vertex pruning becomes risky.

## Visualization
Run:

```bash
python scripts/mcr_semantic_pipeline_visualization.py
```

Outputs:

- `outputs/mcr_semantic_explainer/semantic_mcr_pipeline.svg`
- `outputs/mcr_semantic_explainer/semantic_mcr_pipeline_summary.md`

This figure is intended to explain:
1. what the VLM produces
2. how those outputs map to weights
3. how weighted MCR changes the chosen path
4. why history-dependent collision sets require richer search state

## Current Search Assumption
The current explainer still assumes collision cost is assessed on the accumulated
object set for a path.

For your professor's modification, the important change is:

- a roadmap vertex can no longer store one fixed collision set
- the same vertex may need multiple path-conditioned labels
- exact or near-exact search should therefore keep multiple non-dominated
  states per vertex rather than one greedy winner
