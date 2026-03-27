"""
Scene 5: Non-prehensile manipulation scene (push/rotate).

Replicates the image showing a robot that needs to push and rotate objects
to clear a path. Features:
  - Flat paper/cloth-like objects (thin boxes) that can be pushed/rotated
  - An "unsafe" object (e.g., coffee cup that shouldn't be disturbed)
  - A "safe" object (lightweight, can be moved)
  - A goal region the robot needs to reach
"""
import pybullet as p
import numpy as np
from scenes.scene_utils import (
    init_pybullet, load_ground_plane, load_table, load_fr3v2,
    set_robot_pose, create_cylinder, create_box, create_sphere,
    set_camera, run_simulation, add_debug_text,
    COLORS, TABLE_HEIGHT, FR3V2_READY_POSE,
)


def build_scene(gui=True):
    """Build the push/rotate manipulation scene."""
    client_id = init_pybullet(gui)
    load_ground_plane()
    load_table(position=[0.0, 0.0, 0.0])

    # Robot behind the table
    robot_id = load_fr3v2(position=[0.0, -0.45, TABLE_HEIGHT])
    set_robot_pose(robot_id, FR3V2_READY_POSE)

    z = TABLE_HEIGHT
    objects = {}

    # --- Paper/cloth-like flat objects (thin boxes that can be pushed/rotated) ---
    # Large blue paper/cloth - angled on the table
    orn_paper1 = p.getQuaternionFromEuler([0, 0, 0.3])  # Slightly rotated
    objects["paper_blue"] = {
        "id": create_box(
            position=[-0.05, 0.05, z + 0.003],
            half_extents=[0.12, 0.08, 0.002],
            color=COLORS["light_blue"],
            mass=0.05,  # Light, pushable
            orientation=orn_paper1,
        ),
        "type": "pushable",
    }

    # Yellow paper overlapping
    orn_paper2 = p.getQuaternionFromEuler([0, 0, -0.2])
    objects["paper_yellow"] = {
        "id": create_box(
            position=[-0.02, 0.08, z + 0.006],
            half_extents=[0.10, 0.07, 0.002],
            color=COLORS["yellow"],
            mass=0.05,
            orientation=orn_paper2,
        ),
        "type": "pushable",
    }

    # --- Unsafe object: coffee cup (tall cylinder, should NOT be disturbed) ---
    objects["coffee_cup"] = {
        "id": create_cylinder(
            position=[0.15, 0.25, z + 0.04],
            radius=0.035,
            height=0.08,
            color=COLORS["brown"],
        ),
        "type": "unsafe",
    }
    # Cup handle (small box)
    create_box(
        position=[0.19, 0.25, z + 0.04],
        half_extents=[0.015, 0.005, 0.02],
        color=COLORS["brown"],
    )

    # --- Safe / lightweight object (can be moved) ---
    objects["safe_box"] = {
        "id": create_box(
            position=[-0.20, 0.00, z + 0.02],
            half_extents=[0.03, 0.02, 0.02],
            color=COLORS["green"],
            mass=0.02,
        ),
        "type": "safe",
    }

    # --- Snack packet (small flat box, movable) ---
    objects["packet"] = {
        "id": create_box(
            position=[0.22, -0.05, z + 0.01],
            half_extents=[0.04, 0.03, 0.008],
            color=COLORS["orange"],
            mass=0.03,
        ),
        "type": "movable",
    }

    # --- Goal position marker (green sphere on the table) ---
    objects["goal"] = {
        "id": create_sphere(
            position=[0.20, 0.15, z + 0.015],
            radius=0.015,
            color=COLORS["green"],
        ),
        "type": "goal",
    }

    # Labels
    if gui:
        add_debug_text("Unsafe", [0.15, 0.25, z + 0.15], color=[1, 0, 0], size=1.3)
        add_debug_text("Safe", [-0.20, 0.00, z + 0.10], color=[0, 1, 0], size=1.3)
        add_debug_text("Push", [-0.05, 0.05, z + 0.08], color=[0.3, 0.3, 1], size=1.3)
        add_debug_text("Rotate", [-0.02, 0.15, z + 0.08], color=[0.8, 0.8, 0], size=1.3)

    set_camera(distance=1.0, yaw=90, pitch=-50, target=[0.0, 0.08, TABLE_HEIGHT])

    return client_id, robot_id, objects


def main():
    print("Scene 5: Non-Prehensile Manipulation (Push/Rotate)")
    client_id, robot_id, objects = build_scene()
    print(f"  Robot ID: {robot_id}")
    for name, obj in objects.items():
        print(f"  {name}: type={obj['type']}")
    run_simulation()
    p.disconnect()


if __name__ == "__main__":
    main()
