#!/usr/bin/env python3
"""Legacy numbered scene runner backed by YAML scene configs."""

import sys

from src.mcr.env.scene_catalog import SCENE_ALIASES, get_scene_path
from src.mcr.env.scene_manager import SceneManager


NUMBERED_SCENES = {
    1: SCENE_ALIASES["scene1"],
    2: SCENE_ALIASES["scene2"],
    3: SCENE_ALIASES["scene3"],
    4: SCENE_ALIASES["scene4"],
    5: SCENE_ALIASES["scene5"],
    6: SCENE_ALIASES["scene6"],
    7: SCENE_ALIASES["scene7"],
    8: SCENE_ALIASES["scene8"],
}


def run_scene(scene_num, gui=True, duration=10000):
    scene_name = NUMBERED_SCENES.get(scene_num)
    if scene_name is None:
        print(f"Unknown scene number: {scene_num}")
        print("Valid scenes: 1-8 or 'all'")
        sys.exit(1)

    mgr = SceneManager(gui=gui)
    mgr.init_simulation()
    mgr.load_scene(get_scene_path(scene_name))
    mgr.run_loop(duration=duration)


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print(__doc__)
        sys.exit(0)

    gui = "--headless" not in sys.argv

    if sys.argv[1] == "all":
        for i in range(1, 9):
            print(f"\n{'=' * 50}")
            print(f"Scene {i}")
            print(f"{'=' * 50}")
            run_scene(i, gui=gui)
    else:
        scene_num = int(sys.argv[1])
        run_scene(scene_num, gui=gui)


if __name__ == "__main__":
    main()
