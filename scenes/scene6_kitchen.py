"""
Scene 6: Kitchen/grocery scene with food-like objects.

Replicates the image showing a robot arm on a table with various food items:
tomato, broccoli, spice jar, dressing bottle, sauce bottle, etc.
Objects are approximated with colored geometric primitives.
"""
import pybullet as p
import numpy as np
from scenes.scene_utils import (
    init_pybullet, load_ground_plane, load_table, load_fr3v2,
    set_robot_pose, create_cylinder, create_box, create_sphere,
    set_camera, run_simulation,
    COLORS, TABLE_HEIGHT, FR3V2_READY_POSE,
)


def build_scene(gui=True):
    """Build the kitchen/grocery scene with food-like objects."""
    client_id = init_pybullet(gui)
    load_ground_plane()
    load_table(position=[0.0, 0.0, 0.0])

    # Robot on the left side
    robot_id = load_fr3v2(position=[-0.35, -0.25, TABLE_HEIGHT])
    set_robot_pose(robot_id, FR3V2_READY_POSE)

    z = TABLE_HEIGHT
    objects = {}

    # --- Tomato (red sphere) ---
    objects["tomato"] = create_sphere(
        position=[-0.10, 0.05, z + 0.035],
        radius=0.035,
        color=COLORS["red"],
    )

    # --- Broccoli (green sphere, slightly bumpy look via color) ---
    objects["broccoli"] = create_sphere(
        position=[-0.05, -0.05, z + 0.03],
        radius=0.03,
        color=COLORS["dark_green"],
    )

    # --- Spice jar (small cylinder, dark label) ---
    objects["spice_jar"] = create_cylinder(
        position=[0.05, 0.08, z + 0.045],
        radius=0.022,
        height=0.09,
        color=[0.3, 0.15, 0.05, 1],  # Dark brown
    )
    # Green cap
    create_cylinder(
        position=[0.05, 0.08, z + 0.095],
        radius=0.023,
        height=0.01,
        color=COLORS["green"],
    )

    # --- Ranch dressing bottle (tall, white/blue label) ---
    objects["dressing"] = create_cylinder(
        position=[0.15, 0.10, z + 0.08],
        radius=0.028,
        height=0.16,
        color=COLORS["white"],
    )
    # Blue label band
    create_cylinder(
        position=[0.15, 0.10, z + 0.06],
        radius=0.029,
        height=0.06,
        color=COLORS["light_blue"],
    )

    # --- Olive oil / sauce bottle (tall, green-tinted) ---
    objects["oil_bottle"] = create_cylinder(
        position=[0.20, -0.05, z + 0.07],
        radius=0.025,
        height=0.14,
        color=COLORS["dark_green"],
    )

    # --- Small jar / can (short cylinder) ---
    objects["small_can"] = create_cylinder(
        position=[0.08, -0.10, z + 0.03],
        radius=0.025,
        height=0.06,
        color=COLORS["gray"],
    )
    # Gold lid
    create_cylinder(
        position=[0.08, -0.10, z + 0.065],
        radius=0.026,
        height=0.008,
        color=COLORS["yellow"],
    )

    # --- Pepper/spice bottle (medium, red cap) ---
    objects["pepper"] = create_cylinder(
        position=[-0.15, 0.15, z + 0.05],
        radius=0.020,
        height=0.10,
        color=COLORS["orange"],
    )
    create_cylinder(
        position=[-0.15, 0.15, z + 0.105],
        radius=0.021,
        height=0.01,
        color=COLORS["red"],
    )

    set_camera(distance=0.9, yaw=80, pitch=-40, target=[0.05, 0.02, TABLE_HEIGHT + 0.05])

    return client_id, robot_id, objects


def main():
    print("Scene 6: Kitchen/Grocery - Food items on table")
    client_id, robot_id, objects = build_scene()
    print(f"  Robot ID: {robot_id}")
    print(f"  {len(objects)} food objects placed")
    run_simulation()
    p.disconnect()


if __name__ == "__main__":
    main()
