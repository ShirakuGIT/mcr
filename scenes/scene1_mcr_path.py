"""
Scene 1: MCR Path Planning - Tabletop with scattered colored cylinders.

Replicates the top image showing "Shortest Path" vs "MCR Path" through
a field of ~12 colored cylinder obstacles on a tabletop with the Franka FR3
robot mounted on the left side.
"""
import pybullet as p
import numpy as np
from scenes.scene_utils import (
    init_pybullet, load_ground_plane, load_table, load_fr3v2,
    set_robot_pose, create_cylinder, set_camera, run_simulation,
    add_debug_text, COLORS, TABLE_HEIGHT, FR3V2_READY_POSE,
)


def build_scene(gui=True):
    """Build the MCR path planning scene with scattered colored cylinders."""
    client_id = init_pybullet(gui)
    load_ground_plane()
    load_table(position=[0.0, 0.0, 0.0])

    # Robot on the left side of the table, facing right
    robot_id = load_fr3v2(position=[-0.35, -0.35, TABLE_HEIGHT])
    set_robot_pose(robot_id, FR3V2_READY_POSE)

    z = TABLE_HEIGHT + 0.05  # Cylinder base on table

    # Scattered colored cylinders matching the image layout
    # The image shows ~12 cylinders of various colors in a semi-random spread
    obstacles = [
        # (x, y, radius, height, color_name)
        (-0.05, -0.05, 0.020, 0.10, "red"),
        (-0.10,  0.05, 0.018, 0.08, "dark_blue"),
        (-0.02,  0.10, 0.022, 0.12, "brown"),
        ( 0.08,  0.02, 0.015, 0.10, "black"),
        ( 0.10,  0.12, 0.020, 0.14, "purple"),
        ( 0.15,  0.05, 0.018, 0.09, "gray"),
        ( 0.05, -0.10, 0.020, 0.08, "red"),
        (-0.08, -0.15, 0.022, 0.07, "purple"),
        ( 0.00,  0.20, 0.020, 0.10, "olive"),
        ( 0.12, -0.08, 0.018, 0.11, "green"),
        ( 0.20,  0.15, 0.020, 0.10, "blue"),
        ( 0.25, -0.05, 0.015, 0.08, "orange"),
        ( 0.18,  0.25, 0.020, 0.09, "red"),
    ]

    obstacle_ids = []
    for x, y, r, h, color_name in obstacles:
        oid = create_cylinder(
            position=[x, y, z + h / 2],
            radius=r,
            height=h,
            color=COLORS[color_name],
        )
        obstacle_ids.append(oid)

    # Camera: top-down angled view like the image
    set_camera(distance=1.0, yaw=90, pitch=-55, target=[0.05, 0.0, TABLE_HEIGHT])

    return client_id, robot_id, obstacle_ids


def main():
    print("Scene 1: MCR Path Planning - Colored cylinders on tabletop")
    client_id, robot_id, obstacles = build_scene()
    print(f"  Robot ID: {robot_id}")
    print(f"  {len(obstacles)} obstacle cylinders placed")
    run_simulation()
    p.disconnect()


if __name__ == "__main__":
    main()
