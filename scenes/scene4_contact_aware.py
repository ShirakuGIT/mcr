"""
Scene 4: Contact-aware planning with weighted object costs.

Replicates the image showing "Collision-Free" vs "Acceptable Contact" scenarios.
Objects have different semantic costs:
  - High-cost objects (fragile/important): e.g., stuffed bear proxy, glass
  - Low/negative-cost objects (movable): e.g., cloth, lightweight items

Objects are placed on a white surface with the robot reaching from behind.
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
    """Build the contact-aware scene with weighted objects."""
    client_id = init_pybullet(gui)
    load_ground_plane()
    load_table(position=[0.0, 0.0, 0.0])

    # Robot behind the table
    robot_id = load_fr3v2(position=[0.0, -0.45, TABLE_HEIGHT])
    set_robot_pose(robot_id, FR3V2_READY_POSE)

    z = TABLE_HEIGHT

    objects = {}

    # --- High-cost "fragile" object: tall box representing stuffed bear (cost=8) ---
    objects["bear"] = {
        "id": create_box(
            position=[-0.12, 0.15, z + 0.08],
            half_extents=[0.04, 0.03, 0.08],
            color=COLORS["brown"],
        ),
        "cost": 8,
        "label": "Fragile (8)",
    }
    # Bear's hat (small red box on top)
    create_box(
        position=[-0.12, 0.15, z + 0.18],
        half_extents=[0.035, 0.035, 0.02],
        color=COLORS["red"],
    )

    # --- Medium-cost object: glass/cup (cost=3) ---
    objects["glass"] = {
        "id": create_cylinder(
            position=[0.10, 0.05, z + 0.04],
            radius=0.03,
            height=0.08,
            color=[0.85, 0.85, 0.90, 0.6],  # Translucent glass-like
        ),
        "cost": 3,
        "label": "Glass (3)",
    }

    # --- Low-cost movable object: small bottle (cost=-1, beneficial to move) ---
    objects["bottle"] = {
        "id": create_cylinder(
            position=[-0.05, 0.00, z + 0.05],
            radius=0.022,
            height=0.10,
            color=COLORS["green"],
        ),
        "cost": -1,
        "label": "Movable (-1)",
    }

    # --- Small plate / saucer (cost=3) ---
    objects["plate"] = {
        "id": create_cylinder(
            position=[0.15, 0.18, z + 0.01],
            radius=0.05,
            height=0.015,
            color=COLORS["orange"],
        ),
        "cost": 3,
        "label": "Plate (3)",
    }

    # --- Another small container (cost=5) ---
    objects["container"] = {
        "id": create_cylinder(
            position=[-0.18, -0.05, z + 0.035],
            radius=0.025,
            height=0.07,
            color=[0.3, 0.6, 0.3, 1],
        ),
        "cost": 5,
        "label": "Container (5)",
    }

    # --- Goal object to reach (yellow sphere) ---
    objects["goal"] = {
        "id": create_sphere(
            position=[0.20, 0.20, z + 0.025],
            radius=0.025,
            color=COLORS["yellow"],
        ),
        "cost": 0,
        "label": "Goal",
    }

    # Add cost labels
    if gui:
        for name, obj in objects.items():
            pos = list(p.getBasePositionAndOrientation(obj["id"])[0])
            pos[2] += 0.12
            color = [0.1, 0.9, 0.1] if obj["cost"] <= 0 else [0.9, 0.2, 0.2]
            add_debug_text(obj["label"], pos, color=color, size=1.2)

    set_camera(distance=1.0, yaw=90, pitch=-45, target=[0.0, 0.08, TABLE_HEIGHT])

    return client_id, robot_id, objects


def main():
    print("Scene 4: Contact-Aware Planning with Weighted Costs")
    client_id, robot_id, objects = build_scene()
    print(f"  Robot ID: {robot_id}")
    for name, obj in objects.items():
        print(f"  {name}: cost={obj['cost']}")
    run_simulation()
    p.disconnect()


if __name__ == "__main__":
    main()
