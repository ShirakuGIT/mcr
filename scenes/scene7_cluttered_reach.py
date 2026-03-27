"""
Scene 7: Cluttered reach scene (IMPACT/LAPP style).

Replicates the bottom comparison image showing a robot reaching through
dense clutter to grasp a target object. Features various containers,
bottles, and household objects packed closely together.
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
    """Build the cluttered reach scene with dense household objects."""
    client_id = init_pybullet(gui)
    load_ground_plane()
    load_table(position=[0.0, 0.0, 0.0])

    # Robot behind the table, slightly to the right
    robot_id = load_fr3v2(position=[0.15, -0.50, TABLE_HEIGHT])
    set_robot_pose(robot_id, FR3V2_READY_POSE)

    z = TABLE_HEIGHT
    objects = {}

    # --- Coke bottle (tall, dark red/brown) ---
    objects["coke_bottle"] = create_cylinder(
        position=[-0.05, 0.10, z + 0.10],
        radius=0.028,
        height=0.20,
        color=[0.35, 0.05, 0.05, 1],
    )

    # --- Blue bucket/container (wide, short) ---
    objects["blue_bucket"] = create_cylinder(
        position=[-0.15, 0.05, z + 0.05],
        radius=0.045,
        height=0.10,
        color=COLORS["blue"],
    )

    # --- Red bowl (wide, very short) ---
    objects["red_bowl"] = create_cylinder(
        position=[0.05, 0.18, z + 0.025],
        radius=0.06,
        height=0.05,
        color=COLORS["red"],
    )

    # --- White/cream container (yogurt cup) ---
    objects["yogurt"] = create_cylinder(
        position=[-0.18, 0.20, z + 0.04],
        radius=0.035,
        height=0.08,
        color=COLORS["white"],
    )
    # Label
    create_cylinder(
        position=[-0.18, 0.20, z + 0.03],
        radius=0.036,
        height=0.04,
        color=COLORS["purple"],
    )

    # --- Yellow box (cereal/food box) ---
    objects["cereal_box"] = create_box(
        position=[0.10, 0.08, z + 0.06],
        half_extents=[0.035, 0.02, 0.06],
        color=COLORS["yellow"],
    )

    # --- Small pink container ---
    objects["pink_container"] = create_cylinder(
        position=[0.08, 0.25, z + 0.03],
        radius=0.03,
        height=0.06,
        color=COLORS["pink"],
    )

    # --- Target object to reach (green sphere, partially hidden) ---
    objects["target"] = create_sphere(
        position=[-0.08, 0.22, z + 0.025],
        radius=0.025,
        color=COLORS["green"],
    )

    # --- Additional clutter ---
    # Small brown jar
    objects["brown_jar"] = create_cylinder(
        position=[0.00, 0.00, z + 0.035],
        radius=0.025,
        height=0.07,
        color=COLORS["brown"],
    )

    # Tall skinny bottle
    objects["tall_bottle"] = create_cylinder(
        position=[-0.12, -0.05, z + 0.09],
        radius=0.018,
        height=0.18,
        color=COLORS["dark_green"],
    )

    # Another container in the back
    objects["back_container"] = create_cylinder(
        position=[0.15, 0.22, z + 0.05],
        radius=0.04,
        height=0.10,
        color=COLORS["orange"],
    )

    if gui:
        add_debug_text("Target", [-0.08, 0.22, z + 0.10], color=[0, 1, 0], size=1.3)

    set_camera(distance=1.0, yaw=90, pitch=-40, target=[0.0, 0.10, TABLE_HEIGHT + 0.05])

    return client_id, robot_id, objects


def main():
    print("Scene 7: Cluttered Reach (IMPACT/LAPP style)")
    client_id, robot_id, objects = build_scene()
    print(f"  Robot ID: {robot_id}")
    print(f"  {len(objects)} objects in cluttered scene")
    run_simulation()
    p.disconnect()


if __name__ == "__main__":
    main()
