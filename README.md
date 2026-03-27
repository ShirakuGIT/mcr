# MCR Robotics

PyBullet scenes for minimum constraint removal experiments, FR3 visualization, and scene prototyping with YAML-driven configurations.

## Structure
- `src/mcr/`: package code for scene loading, robot loading, and environment orchestration.
- `configs/scenes/`: scene definitions in YAML.
- `assets/`: URDFs and meshes used by the runtime.
- `docs/datasets.md`: recommended external object datasets for replacing primitive placeholders with scanned meshes.
- `PROCESS.md`: working notes and refactor history.

## Environment
Use either Pixi or Conda.

### Pixi
```bash
pixi run list-scenes
pixi run list-views
pixi run run --scene tabletop_kitchen_grocery_objects
pixi run run --scene tabletop_kitchen_google_scanned_objects --view top_down
```

### Conda
```bash
conda env create -f environment.yml
conda activate mcr-robotics
python run.py --list-scenes
python run.py --list-views
python run.py --scene tabletop_scattered_cylinders_path_planning
python run.py --scene tabletop_kitchen_google_scanned_objects --view front
```

Available camera views:
- `default`
- `top_down`
- `front`
- `back`

## Scene Authoring
Scenes live under `configs/scenes/` and follow a data-first layout:

```yaml
name: "Example Scene"
robot:
  urdf: "assets/urdfs/fr3v2_local.urdf"
  base_position: [-0.35, -0.30, 0.625]
  initial_pose: "ready"
environment:
  ground:
    urdf: "plane.urdf"
  table:
    urdf: "table/table.urdf"
    position: [0.0, 0.0, 0.0]
camera:
  distance: 0.9
  yaw: 80
  pitch: -40
  target: [0.05, 0.02, 0.675]
objects:
  - id: "goal"
    type: "sphere"
    position: [0.2, 0.15, 0.64]
    radius: 0.02
    color: "green"
    label:
      text: "Goal"
      offset: [0.0, 0.0, 0.08]
```

Supported object types:
- `cylinder`
- `box`
- `sphere`
- `mesh`
- `proc_grid`

## Scene Catalog
- `tabletop_scattered_cylinders_path_planning`
- `tabletop_uniform_cylinders_approach_10_objects`
- `tabletop_uniform_cylinders_approach_20_objects`
- `shelf_packed_cylinders_transfer`
- `tabletop_weighted_contact_costs`
- `tabletop_push_rotate_nonprehensile`
- `tabletop_kitchen_grocery_objects`
- `tabletop_kitchen_grocery_dataset_staging`
- `tabletop_kitchen_google_scanned_objects`
- `tabletop_pantry_google_scanned_objects`
- `tabletop_dense_household_clutter_reach`

Older scene names such as `tabletop_cluttered_path` still resolve through aliases in the catalog.

## Object Presets
Reusable object definitions can live in `configs/objects/` and be attached to a scene with `object_libraries`.

```yaml
object_libraries:
  - "configs/objects/household_and_grocery_presets.yaml"

objects:
  - id: "tomato"
    preset: "tomato_proxy"
    position: [-0.10, 0.05, 0.660]
```

This lets you swap a primitive proxy for a mesh or URDF-backed asset by editing one preset instead of every scene.

## Fuel Normalization
For Gazebo Fuel imports, use:

```bash
python scripts/normalize_fuel_asset.py --emit-preset assets/datasets/google_scanned_objects/<asset-dir>
```

That mirrors `texture.png` next to each OBJ, computes mesh extents, and prints a preset stub you can paste into `configs/objects/`.

## Ad-Hoc Data Pulls
The repo is structured so people can pull dataset assets as needed without polluting version control with raw archives and temporary downloads.

Tracked:
- normalized mesh assets you actually use in scenes
- preset YAMLs in `configs/objects/`
- provenance notes such as `SOURCES.md`

Ignored:
- raw archives
- temporary download folders
- local staging directories
- virtual environments, caches, and other machine-local artifacts

When you add a new asset family, update:
1. `docs/datasets.md`
2. `PROCESS.md`
3. `assets/datasets/<family>/SOURCES.md` if you intend to keep the normalized assets in-repo
