from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
SCENE_DIR = PROJECT_ROOT / "configs" / "scenes"

SCENE_ALIASES = {
    "tabletop_cluttered_path": "tabletop_scattered_cylinders_path_planning",
    "tabletop_approach_high_clutter": "tabletop_uniform_cylinders_approach_20_objects",
    "shelf_packed_cylinders_transfer": "shelf_packed_cylinders_transfer",
    "scene1": "tabletop_scattered_cylinders_path_planning",
    "scene2": "tabletop_uniform_cylinders_approach_10_objects",
    "scene3": "tabletop_uniform_cylinders_approach_20_objects",
    "scene4": "shelf_packed_cylinders_transfer",
    "scene5": "tabletop_weighted_contact_costs",
    "scene6": "tabletop_push_rotate_nonprehensile",
    "scene7": "tabletop_kitchen_grocery_objects",
    "scene8": "tabletop_dense_household_clutter_reach",
    "scene9": "tabletop_kitchen_grocery_dataset_staging",
    "scene10": "tabletop_kitchen_google_scanned_objects",
}


def normalize_scene_name(name: str) -> str:
    scene_name = Path(name).stem
    return SCENE_ALIASES.get(scene_name, scene_name)


def get_scene_path(name: str) -> Path:
    scene_name = normalize_scene_name(name)
    return SCENE_DIR / f"{scene_name}.yaml"


def iter_scene_entries() -> list[tuple[str, Path]]:
    return sorted((path.stem, path) for path in SCENE_DIR.glob("*.yaml"))
