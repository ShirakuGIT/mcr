"""
Scene 3: Transfer scene with tall, tightly packed colored cylinders.

Replicates the transfer images showing an initial state with tall colored
cylinders packed on a shelf/table surface, and a final rearranged state.
The scene has cylinders of varying colors and heights arranged in rows.
"""
import pybullet as p
import numpy as np
from scenes.scene_utils import (
    init_pybullet, load_ground_plane, load_table, load_fr3v2,
    set_robot_pose, create_cylinder, create_box, set_camera, run_simulation,
    COLORS, TABLE_HEIGHT, FR3V2_READY_POSE,
)


def build_scene(gui=True):
    """Build the transfer scene with tall packed cylinders."""
    client_id = init_pybullet(gui)
    load_ground_plane()
    load_table(position=[0.0, 0.0, 0.0])

    # Robot behind the table
    robot_id = load_fr3v2(position=[0.0, -0.45, TABLE_HEIGHT])
    set_robot_pose(robot_id, FR3V2_READY_POSE)

    z = TABLE_HEIGHT

    # Back wall / shelf (white panel behind the cylinders)
    create_box(
        position=[0.0, 0.30, z + 0.15],
        half_extents=[0.35, 0.005, 0.15],
        color=COLORS["white"],
    )

    # Tall colored cylinders arranged in rows (like image 3a/3b)
    # The images show ~15 tall cylinders in varying colors: red, green, blue, brown, purple, etc.
    cylinder_specs = [
        # Row 1 (back row, y ~ 0.25)
        (-0.20, 0.25, 0.020, 0.20, "red"),
        (-0.14, 0.25, 0.020, 0.24, "green"),
        (-0.08, 0.25, 0.020, 0.18, "blue"),
        (-0.02, 0.25, 0.020, 0.22, "red"),
        ( 0.04, 0.25, 0.020, 0.16, "purple"),
        ( 0.10, 0.25, 0.020, 0.26, "green"),
        ( 0.16, 0.25, 0.020, 0.20, "blue"),

        # Row 2 (middle row, y ~ 0.18)
        (-0.17, 0.18, 0.020, 0.22, "brown"),
        (-0.11, 0.18, 0.020, 0.18, "red"),
        (-0.05, 0.18, 0.020, 0.24, "green"),
        ( 0.01, 0.18, 0.020, 0.16, "purple"),
        ( 0.07, 0.18, 0.020, 0.20, "blue"),
        ( 0.13, 0.18, 0.020, 0.22, "red"),

        # Row 3 (front row, y ~ 0.11)
        (-0.14, 0.11, 0.020, 0.20, "green"),
        (-0.08, 0.11, 0.020, 0.16, "brown"),
        (-0.02, 0.11, 0.020, 0.22, "blue"),
        ( 0.04, 0.11, 0.020, 0.18, "red"),
        ( 0.10, 0.11, 0.020, 0.24, "green"),
    ]

    obstacle_ids = []
    for x, y, r, h, color_name in cylinder_specs:
        oid = create_cylinder(
            position=[x, y, z + h / 2],
            radius=r,
            height=h,
            color=COLORS[color_name],
        )
        obstacle_ids.append(oid)

    set_camera(distance=1.0, yaw=90, pitch=-35, target=[0.0, 0.15, TABLE_HEIGHT + 0.1])

    return client_id, robot_id, obstacle_ids


def main():
    print("Scene 3: Transfer - Tall packed cylinders")
    client_id, robot_id, obstacles = build_scene()
    print(f"  Robot ID: {robot_id}")
    print(f"  {len(obstacles)} tall cylinders placed")
    run_simulation()
    p.disconnect()


if __name__ == "__main__":
    main()
