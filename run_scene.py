#!/usr/bin/env python3
"""
MCR PyBullet Scene Runner

Usage:
    python run_scene.py <scene_number> [options]

Scenes:
    1  MCR Path Planning    - Colored cylinders scattered on tabletop
    2  Approach (10 obj)    - 10 uniform blue cylinders
    3  Approach (20 obj)    - 20 uniform blue cylinders
    4  Transfer             - Tall packed colored cylinders on shelf
    5  Contact-Aware        - Weighted objects with semantic costs
    6  Push/Rotate          - Non-prehensile manipulation scene
    7  Kitchen/Grocery      - Food-like objects on table
    8  Cluttered Reach      - Dense clutter (IMPACT/LAPP style)
    all                     - Launch all scenes sequentially

Options:
    --headless     Run without GUI (for testing)
"""
import sys


def run_scene(scene_num, gui=True):
    if scene_num == 1:
        from scenes.scene1_mcr_path import build_scene, main
        main() if gui else build_scene(gui=False)
    elif scene_num == 2:
        from scenes.scene2_approach import build_scene
        build_scene(num_objects=10, gui=gui)
        if gui:
            from scenes.scene_utils import run_simulation
            import pybullet as p
            run_simulation()
            p.disconnect()
    elif scene_num == 3:
        from scenes.scene2_approach import build_scene
        build_scene(num_objects=20, gui=gui)
        if gui:
            from scenes.scene_utils import run_simulation
            import pybullet as p
            run_simulation()
            p.disconnect()
    elif scene_num == 4:
        from scenes.scene3_transfer import main
        main()
    elif scene_num == 5:
        from scenes.scene4_contact_aware import main
        main()
    elif scene_num == 6:
        from scenes.scene5_push_rotate import main
        main()
    elif scene_num == 7:
        from scenes.scene6_kitchen import main
        main()
    elif scene_num == 8:
        from scenes.scene7_cluttered_reach import main
        main()
    else:
        print(f"Unknown scene number: {scene_num}")
        print("Valid scenes: 1-8 or 'all'")
        sys.exit(1)


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print(__doc__)
        sys.exit(0)

    gui = "--headless" not in sys.argv

    if sys.argv[1] == "all":
        for i in range(1, 9):
            print(f"\n{'='*50}")
            print(f"Scene {i}")
            print(f"{'='*50}")
            run_scene(i, gui=gui)
    else:
        scene_num = int(sys.argv[1])
        run_scene(scene_num, gui=gui)


if __name__ == "__main__":
    main()
