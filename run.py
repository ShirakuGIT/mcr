#!/usr/bin/env python3
"""MCR scene runner."""

import argparse
import sys

from src.mcr import __version__
from src.mcr.env.scene_catalog import get_scene_path, iter_scene_entries
from src.mcr.env.scene_manager import SceneManager
from src.mcr.scene_describe import describe_scene

import pybullet as p


def main():
    parser = argparse.ArgumentParser(description="MCR scene runner")
    parser.add_argument(
        "--scene",
        type=str,
        default="tabletop_scattered_cylinders_path_planning",
        help="Name of the scene YAML file (without .yaml extension)",
    )
    parser.add_argument("--headless", action="store_true", help="Run without GUI")
    parser.add_argument("--duration", type=int, default=None, help="Simulation steps (default: run until Ctrl+C)")
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
    parser.add_argument("--describe", action="store_true", help="Capture a frame and describe it via Ollama VLM")
    parser.add_argument("--describe-model", type=str, default="llava", help="Ollama model for scene description (default: llava)")
    parser.add_argument("--describe-prompt", type=str, default=None, help="Custom prompt for VLM description")
    parser.add_argument("--save-frame", type=str, default=None, help="Save captured frame to this path before describing")
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

    if args.describe:
        print("\nCapturing scene frame for VLM description...")
        desc = describe_scene(
            model=args.describe_model,
            prompt=args.describe_prompt,
            save_frame=args.save_frame,
        )
        print("\n" + "=" * 60)
        print("SCENE DESCRIPTION")
        print("=" * 60)
        print(desc)
        print("=" * 60)
        if args.headless:
            p.disconnect(mgr.client_id)
            return
    if args.duration is not None:
        print(f"\nRunning simulation for {args.duration} steps...")
    else:
        print("\nRunning simulation (Ctrl+C to quit)...")
    mgr.run_loop(duration=args.duration)


if __name__ == "__main__":
    main()
