# MCR Process Notes

## Current Workflow
1. Define or edit a scene in `configs/scenes/`.
2. Run it with `python run.py --scene <scene-name>` or `pixi run run --scene <scene-name>`.
3. Keep scene-specific logic in YAML and shared runtime behavior in `src/mcr/env/`.
4. Add new datasets, object sources, and modeling notes to `docs/datasets.md`.

## 2026-03-28
### Objective
Move from one-off scene scripts to a scene catalog with stable environment management and maintainable documentation.

### Completed
1. Added package versioning in `src/mcr/__init__.py`.
2. Added a scene catalog with legacy aliases so numbered and older scene names still resolve.
3. Expanded the YAML scene runtime to support labels, spheres, mesh objects, and richer procedural generation.
4. Added a visual fallback in `RobotManager` so the FR3 arm stays visibly shaded even when COLLADA material parsing is incomplete.
5. Added `environment.yml`, a top-level `README.md`, and `docs/datasets.md`.
6. Added reusable object preset libraries in `configs/objects/` and a dataset-staging kitchen scene for future YCB/GSO imports.
7. Imported three official Google scanned kitchen assets and wired them into a dedicated YAML scene plus reusable mesh presets.
8. Added named camera viewpoints plus a normalization script and imported three official Google scanned pantry package assets.
9. Expanded `.gitignore` and documentation so ad-hoc dataset pulls and local staging do not clutter version control.

### Remaining
1. Decide whether to fully retire `scenes/*.py` after the YAML scenes cover every case you still care about.
2. Add mesh-based assets for kitchen and household scenes once you choose a source dataset.
3. If you want stricter reproducibility, pin exact dependency versions in `pixi.lock` after validating on your machine.
