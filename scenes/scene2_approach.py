"""
Scene 2: Approach scenes with uniform cylinder obstacles.

Replicates images (a) and (b) showing the robot approaching a goal through
a field of 10 or 20 uniformly-colored cylinders on a tabletop.
"""
import pybullet as p
import numpy as np
from scenes.scene_utils import (
    init_pybullet, load_ground_plane, load_table, load_fr3v2,
    set_robot_pose, create_cylinder, set_camera, run_simulation,
    COLORS, TABLE_HEIGHT, FR3V2_READY_POSE,
)


def build_scene(num_objects=10, gui=True, seed=42):
    """
    Build an approach scene with uniformly-colored cylinders.

    Args:
        num_objects: 10 or 20 cylinders.
        gui: Whether to use GUI mode.
        seed: Random seed for reproducible placement.
    """
    client_id = init_pybullet(gui)
    load_ground_plane()
    load_table(position=[0.0, 0.0, 0.0])

    # Robot on the left side
    robot_id = load_fr3v2(position=[-0.35, -0.30, TABLE_HEIGHT])
    set_robot_pose(robot_id, FR3V2_READY_POSE)

    rng = np.random.RandomState(seed)
    z = TABLE_HEIGHT + 0.05

    # Place cylinders in a grid-like region in front of the robot
    # The images show cylinders roughly arranged in rows
    obstacle_ids = []
    color = COLORS["blue"]
    radius = 0.022
    height = 0.12

    if num_objects == 10:
        # 2 rows x 5 columns arrangement
        for row in range(2):
            for col in range(5):
                x = -0.05 + col * 0.08 + rng.uniform(-0.01, 0.01)
                y = -0.10 + row * 0.12 + rng.uniform(-0.01, 0.01)
                oid = create_cylinder(
                    position=[x, y, z + height / 2],
                    radius=radius,
                    height=height,
                    color=color,
                )
                obstacle_ids.append(oid)
    elif num_objects == 20:
        # 4 rows x 5 columns arrangement
        for row in range(4):
            for col in range(5):
                x = -0.05 + col * 0.07 + rng.uniform(-0.01, 0.01)
                y = -0.15 + row * 0.09 + rng.uniform(-0.01, 0.01)
                oid = create_cylinder(
                    position=[x, y, z + height / 2],
                    radius=radius,
                    height=height,
                    color=color,
                )
                obstacle_ids.append(oid)

    # Brown/tan cylinder as the goal object (different color)
    goal_id = create_cylinder(
        position=[0.25, 0.10, z + 0.06],
        radius=0.025,
        height=0.12,
        color=COLORS["brown"],
    )

    set_camera(distance=0.9, yaw=70, pitch=-40, target=[0.1, 0.0, TABLE_HEIGHT])

    return client_id, robot_id, obstacle_ids, goal_id


def main():
    import sys
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    print(f"Scene 2: Approach with {n} objects")
    client_id, robot_id, obstacles, goal = build_scene(num_objects=n)
    print(f"  Robot ID: {robot_id}")
    print(f"  {len(obstacles)} obstacles, 1 goal")
    run_simulation()
    p.disconnect()


if __name__ == "__main__":
    main()
