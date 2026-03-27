#!/usr/bin/env python3
"""Normalize a Gazebo Fuel asset layout for local PyBullet use.

This script mirrors textures next to OBJ meshes, computes raw mesh extents,
and optionally prints a preset snippet you can paste into a YAML object library.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import shutil


def find_obj_files(asset_dir: Path) -> list[Path]:
    return sorted(asset_dir.glob("**/meshes/*.obj"))


def compute_extents(obj_path: Path):
    mins = [float("inf")] * 3
    maxs = [float("-inf")] * 3
    count = 0
    with obj_path.open("r", encoding="utf-8", errors="ignore") as handle:
        for line in handle:
            if not line.startswith("v "):
                continue
            _, x, y, z, *_ = line.split()
            vals = [float(x), float(y), float(z)]
            for i, value in enumerate(vals):
                mins[i] = min(mins[i], value)
                maxs[i] = max(maxs[i], value)
            count += 1
    if count == 0:
        raise ValueError(f"No vertex data found in {obj_path}")
    extents = [maxs[i] - mins[i] for i in range(3)]
    return mins, maxs, extents, count


def mirror_texture(asset_root: Path, obj_path: Path):
    texture_source = asset_root / "materials" / "textures" / "texture.png"
    texture_target = obj_path.parent / "texture.png"
    if texture_source.exists():
        shutil.copy2(texture_source, texture_target)
        return texture_target
    return None


def emit_preset(asset_name: str, obj_path: Path):
    preset_name = f"gso_{asset_name}"
    rel_path = obj_path.as_posix()
    return "\n".join(
        [
            f"  {preset_name}:",
            "    type: mesh",
            f"    mesh: {rel_path}",
            "    mesh_scale: [1.0, 1.0, 1.0]",
            "    mass: 0.2",
        ]
    )


def main():
    parser = argparse.ArgumentParser(description="Normalize Gazebo Fuel mesh assets")
    parser.add_argument("asset_dirs", nargs="+", help="Asset directories to normalize")
    parser.add_argument(
        "--emit-preset",
        action="store_true",
        help="Print YAML preset stubs for each normalized asset",
    )
    args = parser.parse_args()

    for asset_dir_arg in args.asset_dirs:
        asset_dir = Path(asset_dir_arg).resolve()
        if not asset_dir.exists():
            raise FileNotFoundError(f"Asset directory not found: {asset_dir}")

        obj_files = find_obj_files(asset_dir)
        if not obj_files:
            raise FileNotFoundError(f"No OBJ meshes found under: {asset_dir}")

        print(f"\n[{asset_dir.name}]")
        for obj_path in obj_files:
            texture_target = mirror_texture(asset_dir, obj_path)
            mins, maxs, extents, count = compute_extents(obj_path)
            print(f"mesh: {obj_path}")
            print(f"  vertices: {count}")
            print(f"  mins: {mins}")
            print(f"  maxs: {maxs}")
            print(f"  extents: {extents}")
            if texture_target:
                print(f"  mirrored_texture: {texture_target}")
            if args.emit_preset:
                print("  preset:")
                print(emit_preset(asset_dir.name, obj_path))


if __name__ == "__main__":
    main()
