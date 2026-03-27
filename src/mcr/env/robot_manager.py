from __future__ import annotations

from pathlib import Path

import numpy as np
import pybullet as p


class RobotManager:
    """Handles loading, control, and visual improvements for the Franka robot."""

    DEFAULT_LINK_COLORS = {
        "link0": [0.90, 0.92, 0.93, 1.0],
        "link1": [0.88, 0.90, 0.91, 1.0],
        "link2": [0.88, 0.90, 0.91, 1.0],
        "link3": [0.86, 0.88, 0.89, 1.0],
        "link4": [0.86, 0.88, 0.89, 1.0],
        "link5": [0.85, 0.87, 0.88, 1.0],
        "link6": [0.84, 0.86, 0.87, 1.0],
        "link7": [0.82, 0.84, 0.85, 1.0],
        "hand": [0.92, 0.93, 0.94, 1.0],
        "leftfinger": [0.22, 0.22, 0.24, 1.0],
        "rightfinger": [0.22, 0.22, 0.24, 1.0],
    }

    def __init__(self, urdf_path, base_pos=None, base_orn=None):
        self.urdf_path = Path(urdf_path).expanduser().resolve()
        self.base_pos = base_pos or [0, 0, 0]
        self.base_orn = base_orn or [0, 0, 0, 1]
        self.robot_id = None
        self.joint_indices = []

    def load(self, use_fixed_base=True):
        """Load the robot with visual improvements."""
        if not self.urdf_path.exists():
            raise FileNotFoundError(f"Robot URDF not found: {self.urdf_path}")

        p.setAdditionalSearchPath(str(self.urdf_path.parent))
        p.setAdditionalSearchPath(str(self.urdf_path.parent.parent))

        flags = p.URDF_USE_SELF_COLLISION | p.URDF_USE_MATERIAL_COLORS_FROM_MTL
        self.robot_id = p.loadURDF(
            str(self.urdf_path),
            basePosition=self.base_pos,
            baseOrientation=self.base_orn,
            useFixedBase=use_fixed_base,
            flags=flags,
        )

        self.joint_indices = self._get_revolute_joint_indices()
        self._apply_dynamics_tuning()
        self._apply_visual_fallback()
        return self.robot_id

    def _get_revolute_joint_indices(self):
        indices = []
        for i in range(p.getNumJoints(self.robot_id)):
            info = p.getJointInfo(self.robot_id, i)
            if info[2] == p.JOINT_REVOLUTE:
                indices.append(i)
        return indices

    def _apply_dynamics_tuning(self):
        """Stabilize simulation by adding damping."""
        for j in range(p.getNumJoints(self.robot_id)):
            p.changeDynamics(
                self.robot_id,
                j,
                linearDamping=0.04,
                angularDamping=0.04,
                jointDamping=0.01,
            )

    def _apply_visual_fallback(self):
        """Ensure the FR3 remains visibly colored even if DAE materials are ignored."""
        for joint_index in range(-1, p.getNumJoints(self.robot_id)):
            if joint_index == -1:
                link_name = "base"
            else:
                info = p.getJointInfo(self.robot_id, joint_index)
                link_name = info[12].decode("utf-8")

            rgba = self._color_for_link(link_name)
            if rgba is None:
                continue
            p.changeVisualShape(self.robot_id, joint_index, rgbaColor=rgba)

    def _color_for_link(self, link_name):
        for suffix, color in self.DEFAULT_LINK_COLORS.items():
            if link_name.endswith(suffix):
                return color
        return None

    def set_pose(self, angles):
        """Instantly set robot joint angles."""
        if len(angles) != len(self.joint_indices):
            print(
                f"Warning: Angle count ({len(angles)}) mismatch with DoF "
                f"({len(self.joint_indices)})"
            )
            return

        for idx, angle in zip(self.joint_indices, angles):
            p.resetJointState(self.robot_id, idx, angle)

    def get_current_pose(self):
        """Get current configuration."""
        return np.array([p.getJointState(self.robot_id, i)[0] for i in self.joint_indices])


if __name__ == "__main__":
    p.connect(p.GUI)
    p.setGravity(0, 0, -9.81)
    mgr = RobotManager("assets/urdfs/fr3v2_local.urdf", base_pos=[0, 0, 0])
    mgr.load()
    while True:
        p.stepSimulation()
