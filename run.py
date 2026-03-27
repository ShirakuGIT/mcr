#!/usr/bin/env python3
"""MCR scene runner."""

import argparse
import sys

from src.mcr import __version__
from src.mcr.env.scene_catalog import get_scene_path, iter_scene_entries
from src.mcr.env.scene_manager import SceneManager


def main():
    parser = argparse.ArgumentParser(description="MCR scene runner")
    parser.add_argument(
        "--scene",
        type=str,
        default="tabletop_scattered_cylinders_path_planning",
        help="Name of the scene YAML file (without .yaml extension)",
    )
    parser.add_argument("--headless", action="store_true", help="Run without GUI")
    parser.add_argument("--duration", type=int, default=10000, help="Simulation steps")
    parser.add_argument(
        "--view",
        type=str,
        choices=["default", "top_down", "front", "back"],
        default="default",
        help="Camera viewpoint preset",
    )
    parser.add_argument("--list-views", action="store_true", help="List available camera viewpoints")
    parser.add_argument("--list-scenes", action="store_true", help="List available scene YAMLs")
    parser.add_argument("--version", action="store_true", help="Print package version")
    args = parser.parse_args()

    if args.version:
        print(__version__)
        return

    if args.list_scenes:
        print("Available scenes:")
        for name, _ in iter_scene_entries():
            print(f"  - {name}")
        return

    if args.list_views:
        print("Available camera views:")
        for name in ["default", "top_down", "front", "back"]:
            print(f"  - {name}")
        return

    scene_path = get_scene_path(args.scene)
    if not scene_path.exists():
        print(f"Error: Scene file not found: {scene_path}")
        print("Available scenes:")
        for name, _ in iter_scene_entries():
            print(f"  - {name}")
        sys.exit(1)

    mgr = SceneManager(gui=not args.headless)
    mgr.init_simulation()
    mgr.load_scene(scene_path, view=args.view)
    print(f"\nRunning simulation for {args.duration} steps...")
    mgr.run_loop(duration=args.duration)


if __name__ == "__main__":
    main()
