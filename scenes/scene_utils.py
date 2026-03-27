"""
Shared utilities for MCR PyBullet scenes.
"""
import os
import pybullet as p
import pybullet_data
import numpy as np

# Paths
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FR3V2_URDF = os.path.join(PROJECT_ROOT, "urdfs", "fr3v2_local.urdf")

# FR3v2 joint limits from URDF
FR3V2_JOINT_LIMITS = {
    "lower": [-2.9007, -1.8361, -2.9007, -3.0770, -2.8763, 0.4398, -3.0508],
    "upper": [ 2.9007,  1.8361,  2.9007, -0.1169,  2.8763, 4.6216,  3.0508],
}

# Named poses from SRDF
FR3V2_READY_POSE = [0.0, -0.7854, 0.0, -2.3562, 0.0, 1.5708, 0.7854]
FR3V2_EXTENDED_POSE = [0.0, 0.0, 0.0, -0.1, 0.0, 3.14, 0.0]

# Standard colors (RGBA)
COLORS = {
    "red":        [0.85, 0.15, 0.15, 1],
    "green":      [0.15, 0.70, 0.15, 1],
    "blue":       [0.15, 0.15, 0.85, 1],
    "yellow":     [0.90, 0.85, 0.10, 1],
    "orange":     [0.95, 0.55, 0.10, 1],
    "purple":     [0.60, 0.15, 0.70, 1],
    "cyan":       [0.10, 0.80, 0.80, 1],
    "brown":      [0.55, 0.30, 0.10, 1],
    "pink":       [0.95, 0.45, 0.65, 1],
    "dark_green":  [0.10, 0.40, 0.10, 1],
    "dark_blue":   [0.10, 0.10, 0.50, 1],
    "olive":      [0.50, 0.50, 0.10, 1],
    "white":      [0.95, 0.95, 0.95, 1],
    "black":      [0.10, 0.10, 0.10, 1],
    "gray":       [0.50, 0.50, 0.50, 1],
    "light_blue": [0.40, 0.60, 0.90, 1],
}


def init_pybullet(gui=True):
    """Initialize PyBullet with standard settings."""
    mode = p.GUI if gui else p.DIRECT
    client_id = p.connect(mode)
    p.configureDebugVisualizer(p.COV_ENABLE_GUI, 0)
    p.setAdditionalSearchPath(pybullet_data.getDataPath())
    p.setGravity(0, 0, -9.81)
    return client_id


def load_ground_plane():
    """Load a ground plane."""
    return p.loadURDF("plane.urdf")


def load_table(position=None, orientation=None):
    """Load the standard PyBullet table."""
    pos = position or [0, 0, 0]
    orn = orientation or p.getQuaternionFromEuler([0, 0, 0])
    return p.loadURDF("table/table.urdf", basePosition=pos, baseOrientation=orn)


def load_fr3v2(position=None, orientation=None, use_fixed_base=True):
    """Load the FR3v2 robot with local mesh paths."""
    pos = position or [0, -0.4, 0.625]
    orn = orientation or p.getQuaternionFromEuler([0, 0, 0])
    robot_id = p.loadURDF(
        FR3V2_URDF,
        basePosition=pos,
        baseOrientation=orn,
        useFixedBase=use_fixed_base,
        flags=p.URDF_USE_SELF_COLLISION,
    )
    # Apply damping for stability
    for j in range(p.getNumJoints(robot_id)):
        p.changeDynamics(robot_id, j, linearDamping=0.04, angularDamping=0.04)
    return robot_id


def set_robot_pose(robot_id, joint_angles):
    """Set the FR3v2 to a specific joint configuration (instant reset)."""
    rev_indices = get_revolute_joint_indices(robot_id)
    for idx, angle in zip(rev_indices, joint_angles):
        p.resetJointState(robot_id, idx, angle)


def get_revolute_joint_indices(robot_id):
    """Get indices of revolute joints."""
    indices = []
    for i in range(p.getNumJoints(robot_id)):
        info = p.getJointInfo(robot_id, i)
        if info[2] == p.JOINT_REVOLUTE:
            indices.append(i)
    return indices


def create_cylinder(position, radius=0.025, height=0.10, color=None, mass=0.0):
    """Create a cylinder obstacle at the given position."""
    rgba = color or COLORS["blue"]
    col_id = p.createCollisionShape(p.GEOM_CYLINDER, radius=radius, height=height)
    vis_id = p.createVisualShape(p.GEOM_CYLINDER, radius=radius, length=height, rgbaColor=rgba)
    body_id = p.createMultiBody(
        baseMass=mass,
        baseCollisionShapeIndex=col_id,
        baseVisualShapeIndex=vis_id,
        basePosition=position,
    )
    return body_id


def create_box(position, half_extents=None, color=None, mass=0.0, orientation=None):
    """Create a box obstacle at the given position."""
    he = half_extents or [0.03, 0.03, 0.05]
    rgba = color or COLORS["brown"]
    orn = orientation or [0, 0, 0, 1]
    col_id = p.createCollisionShape(p.GEOM_BOX, halfExtents=he)
    vis_id = p.createVisualShape(p.GEOM_BOX, halfExtents=he, rgbaColor=rgba)
    body_id = p.createMultiBody(
        baseMass=mass,
        baseCollisionShapeIndex=col_id,
        baseVisualShapeIndex=vis_id,
        basePosition=position,
        baseOrientation=orn,
    )
    return body_id


def create_sphere(position, radius=0.03, color=None, mass=0.0):
    """Create a sphere obstacle."""
    rgba = color or COLORS["red"]
    col_id = p.createCollisionShape(p.GEOM_SPHERE, radius=radius)
    vis_id = p.createVisualShape(p.GEOM_SPHERE, radius=radius, rgbaColor=rgba)
    body_id = p.createMultiBody(
        baseMass=mass,
        baseCollisionShapeIndex=col_id,
        baseVisualShapeIndex=vis_id,
        basePosition=position,
    )
    return body_id


def set_camera(distance=1.5, yaw=45, pitch=-30, target=None):
    """Set the debug visualizer camera."""
    tgt = target or [0, 0, 0.5]
    p.resetDebugVisualizerCamera(
        cameraDistance=distance,
        cameraYaw=yaw,
        cameraPitch=pitch,
        cameraTargetPosition=tgt,
    )


def add_debug_text(text, position, color=None, size=1.5):
    """Add a debug text label in the scene."""
    rgb = color or [1, 1, 1]
    return p.addUserDebugText(text, position, textColorRGB=rgb, textSize=size)


def run_simulation(steps=10000, dt=1.0/240.0):
    """Run the simulation for N steps."""
    import time
    try:
        for _ in range(steps):
            p.stepSimulation()
            time.sleep(dt)
    except KeyboardInterrupt:
        print("Simulation stopped.")


TABLE_HEIGHT = 0.625  # Height of the table surface
