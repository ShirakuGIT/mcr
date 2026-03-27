from __future__ import annotations

from pathlib import Path
import time

import pybullet as p
import pybullet_data
import yaml

from src.mcr.env.robot_manager import RobotManager
from src.mcr.env.scene_catalog import PROJECT_ROOT


class SceneManager:
    """Loads and builds PyBullet environments from YAML configurations."""

    VIEWPOINTS = {
        "default": {},
        "top_down": {"distance": 1.05, "yaw": 90, "pitch": -89},
        "front": {"distance": 0.95, "yaw": 0, "pitch": -20},
        "back": {"distance": 0.95, "yaw": 180, "pitch": -20},
    }

    COLORS = {
        "red": [0.85, 0.15, 0.15, 1],
        "green": [0.15, 0.70, 0.15, 1],
        "blue": [0.15, 0.15, 0.85, 1],
        "yellow": [0.90, 0.85, 0.10, 1],
        "orange": [0.95, 0.55, 0.10, 1],
        "purple": [0.60, 0.15, 0.70, 1],
        "cyan": [0.10, 0.80, 0.80, 1],
        "brown": [0.55, 0.30, 0.10, 1],
        "black": [0.10, 0.10, 0.10, 1],
        "gray": [0.50, 0.50, 0.50, 1],
        "olive": [0.50, 0.50, 0.10, 1],
        "dark_blue": [0.10, 0.10, 0.50, 1],
        "dark_green": [0.10, 0.40, 0.10, 1],
        "white": [0.95, 0.95, 0.95, 1],
        "light_blue": [0.40, 0.60, 0.90, 1],
        "pink": [0.95, 0.45, 0.65, 1],
    }

    POSES = {
        "ready": [0.0, -0.7854, 0.0, -2.3562, 0.0, 1.5708, 0.7854],
        "extended": [0.0, 0.0, 0.0, -0.1, 0.0, 3.14, 0.0],
    }

    def __init__(self, gui=True):
        self.gui = gui
        self.client_id = None
        self.robot = None
        self.obstacle_ids = []
        self.object_index = {}
        self.object_presets = {}

    def init_simulation(self):
        """Initialize PyBullet."""
        mode = p.GUI if self.gui else p.DIRECT
        self.client_id = p.connect(mode)
        p.configureDebugVisualizer(p.COV_ENABLE_GUI, 0)
        p.setGravity(0, 0, -9.81)
        return self.client_id

    def load_scene(self, yaml_path, view=None):
        """Build the scene from YAML."""
        yaml_path = Path(yaml_path).resolve()
        with yaml_path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle)

        print(f"Loading Scene: {data.get('name', 'Unnamed')}")
        self.object_presets = self._load_object_presets(data.get("object_libraries", []))

        env_data = data.get("environment", {})
        if "ground" in env_data:
            ground_info = env_data["ground"]
            ground_urdf = ground_info.get("urdf", "plane.urdf") if isinstance(ground_info, dict) else "plane.urdf"
            p.loadURDF(str(self._resolve_urdf_path(ground_urdf)))
        if "table" in env_data:
            table_info = env_data["table"]
            table_orn = p.getQuaternionFromEuler(table_info.get("orientation", [0, 0, 0]))
            p.loadURDF(
                str(self._resolve_urdf_path(table_info["urdf"])),
                basePosition=table_info["position"],
                baseOrientation=table_orn,
            )

        robot_data = data.get("robot", {})
        if robot_data:
            self.robot = RobotManager(
                self._resolve_path(robot_data.get("urdf", "assets/urdfs/fr3v2_local.urdf")),
                base_pos=robot_data.get("base_position", [0, 0, 0]),
                base_orn=p.getQuaternionFromEuler(robot_data.get("base_orientation", [0, 0, 0])),
            )
            self.robot.load()
            init_pose = robot_data.get("initial_pose", "ready")
            pose_angles = self.POSES.get(init_pose, self.POSES["ready"]) if isinstance(init_pose, str) else init_pose
            self.robot.set_pose(pose_angles)

        for obj in data.get("objects", []) + data.get("obstacles", []):
            self._create_obstacle(self._expand_object_spec(obj))

        cam = self._resolve_camera(data.get("camera", {}), view=view)
        if cam:
            p.resetDebugVisualizerCamera(
                cameraDistance=cam.get("distance", 1.5),
                cameraYaw=cam.get("yaw", 45),
                cameraPitch=cam.get("pitch", -30),
                cameraTargetPosition=cam.get("target", [0, 0, 0.5]),
            )

        return data

    def _create_obstacle(self, obs):
        """Create an object based on type."""
        color = self._resolve_color(obs["color"]) if "color" in obs else None

        if obs["type"] == "proc_grid":
            return self._create_proc_grid(obs)

        pos = obs.get("pos", obs.get("position"))
        orn = p.getQuaternionFromEuler(obs.get("orientation_euler", [0, 0, 0]))
        mass = obs.get("mass", 0.0)
        body_id = None

        if obs["type"] == "cylinder":
            radius = obs.get("radius", 0.025)
            height = obs.get("height", 0.10)
            col_id = p.createCollisionShape(p.GEOM_CYLINDER, radius=radius, height=height)
            vis_id = p.createVisualShape(p.GEOM_CYLINDER, radius=radius, length=height, rgbaColor=color)
            body_id = p.createMultiBody(
                baseMass=mass,
                baseCollisionShapeIndex=col_id,
                baseVisualShapeIndex=vis_id,
                basePosition=pos,
                baseOrientation=orn,
            )
        elif obs["type"] == "box":
            half_extents = obs.get("half_extents", [0.03, 0.03, 0.05])
            col_id = p.createCollisionShape(p.GEOM_BOX, halfExtents=half_extents)
            vis_id = p.createVisualShape(p.GEOM_BOX, halfExtents=half_extents, rgbaColor=color)
            body_id = p.createMultiBody(
                baseMass=mass,
                baseCollisionShapeIndex=col_id,
                baseVisualShapeIndex=vis_id,
                basePosition=pos,
                baseOrientation=orn,
            )
        elif obs["type"] == "sphere":
            radius = obs.get("radius", 0.03)
            col_id = p.createCollisionShape(p.GEOM_SPHERE, radius=radius)
            vis_id = p.createVisualShape(p.GEOM_SPHERE, radius=radius, rgbaColor=color)
            body_id = p.createMultiBody(
                baseMass=mass,
                baseCollisionShapeIndex=col_id,
                baseVisualShapeIndex=vis_id,
                basePosition=pos,
                baseOrientation=orn,
            )
        elif obs["type"] == "mesh":
            mesh_path = str(self._resolve_path(obs["mesh"]))
            scale = obs.get("mesh_scale", [1.0, 1.0, 1.0])
            mesh_color = color or [1.0, 1.0, 1.0, 1.0]
            col_id = p.createCollisionShape(p.GEOM_MESH, fileName=mesh_path, meshScale=scale)
            vis_id = p.createVisualShape(
                p.GEOM_MESH,
                fileName=mesh_path,
                meshScale=scale,
                rgbaColor=mesh_color,
            )
            body_id = p.createMultiBody(
                baseMass=mass,
                baseCollisionShapeIndex=col_id,
                baseVisualShapeIndex=vis_id,
                basePosition=pos,
                baseOrientation=orn,
            )
        elif obs["type"] == "urdf":
            body_id = p.loadURDF(
                str(self._resolve_urdf_path(obs["urdf"])),
                basePosition=pos,
                baseOrientation=orn,
                useFixedBase=obs.get("use_fixed_base", False),
                globalScaling=obs.get("scale", 1.0),
            )
            if color is not None:
                p.changeVisualShape(body_id, -1, rgbaColor=color)
        else:
            print(f"Warning: Unknown obstacle type {obs['type']}")
            return None

        self._register_body(obs, body_id)
        return body_id

    def _create_proc_grid(self, obs):
        """Procedurally generate a grid of objects."""
        import numpy as np

        rng = np.random.RandomState(obs.get("seed", 42))
        rows = obs.get("rows", 2)
        cols = obs.get("cols", 5)
        start_pos = obs.get("start_pos", [-0.05, -0.10, 0.675])
        spacing = obs.get("spacing", [0.08, 0.12])
        jitter = obs.get("jitter", 0.01)

        item_type = obs.get("item_type", "cylinder")
        color = self._resolve_color(obs.get("color", "blue"))
        mass = obs.get("mass", 0.0)
        orientation = p.getQuaternionFromEuler(obs.get("orientation_euler", [0, 0, 0]))

        ids = []
        for row in range(rows):
            for col in range(cols):
                x = start_pos[0] + col * spacing[0] + rng.uniform(-jitter, jitter)
                y = start_pos[1] + row * spacing[1] + rng.uniform(-jitter, jitter)
                z = start_pos[2]

                if item_type == "cylinder":
                    radius = obs.get("radius", 0.022)
                    height = obs.get("height", 0.12)
                    col_id = p.createCollisionShape(p.GEOM_CYLINDER, radius=radius, height=height)
                    vis_id = p.createVisualShape(p.GEOM_CYLINDER, radius=radius, length=height, rgbaColor=color)
                elif item_type == "box":
                    half_extents = obs.get("half_extents", [0.03, 0.03, 0.05])
                    col_id = p.createCollisionShape(p.GEOM_BOX, halfExtents=half_extents)
                    vis_id = p.createVisualShape(p.GEOM_BOX, halfExtents=half_extents, rgbaColor=color)
                elif item_type == "sphere":
                    radius = obs.get("radius", 0.03)
                    col_id = p.createCollisionShape(p.GEOM_SPHERE, radius=radius)
                    vis_id = p.createVisualShape(p.GEOM_SPHERE, radius=radius, rgbaColor=color)
                else:
                    raise ValueError(f"Unsupported proc_grid item_type: {item_type}")

                body_id = p.createMultiBody(
                    baseMass=mass,
                    baseCollisionShapeIndex=col_id,
                    baseVisualShapeIndex=vis_id,
                    basePosition=[x, y, z],
                    baseOrientation=orientation,
                )
                ids.append(body_id)
                self._register_body(obs, body_id, generated=True)
        return ids

    def _register_body(self, obs, body_id, generated=False):
        self.obstacle_ids.append(body_id)
        object_id = obs.get("id")
        if object_id and not generated:
            self.object_index[object_id] = body_id

        label = obs.get("label")
        if label and self.gui:
            base_position = list(p.getBasePositionAndOrientation(body_id)[0])
            offset = label.get("offset", [0.0, 0.0, 0.12])
            text_position = [base_position[i] + offset[i] for i in range(3)]
            p.addUserDebugText(
                label["text"],
                text_position,
                textColorRGB=label.get("color", [1.0, 1.0, 1.0]),
                textSize=label.get("size", 1.2),
            )

    def _resolve_color(self, value):
        if isinstance(value, list):
            return value
        return self.COLORS.get(value, self.COLORS["blue"])

    def _load_object_presets(self, library_entries):
        presets = {}
        for library_entry in library_entries:
            library_path = self._resolve_path(library_entry)
            with library_path.open("r", encoding="utf-8") as handle:
                library_data = yaml.safe_load(handle) or {}
            presets.update(library_data.get("presets", {}))
        return presets

    def _expand_object_spec(self, obj):
        preset_name = obj.get("preset")
        if not preset_name:
            return obj
        preset = self.object_presets.get(preset_name)
        if preset is None:
            raise KeyError(f"Unknown object preset: {preset_name}")
        merged = dict(preset)
        merged.update(obj)
        merged.pop("preset", None)
        return merged

    def _resolve_camera(self, camera_data, view=None):
        cam = dict(camera_data or {})
        if not cam:
            cam = {"target": [0, 0, 0.5]}

        scene_views = cam.pop("views", {})
        selected_view = view or "default"
        if selected_view not in self.VIEWPOINTS and selected_view not in scene_views:
            raise KeyError(f"Unknown camera view: {selected_view}")

        merged = dict(cam)
        merged.update(self.VIEWPOINTS.get(selected_view, {}))
        merged.update(scene_views.get(selected_view, {}))
        return merged

    def _resolve_path(self, path_value):
        path = Path(path_value)
        if path.is_absolute():
            return path
        return (PROJECT_ROOT / path).resolve()

    def _resolve_urdf_path(self, path_value):
        path = Path(path_value)
        if path.is_absolute() and path.exists():
            return path

        candidates = [
            PROJECT_ROOT / path,
            PROJECT_ROOT / "assets" / path,
            Path(pybullet_data.getDataPath()) / path,
        ]
        for candidate in candidates:
            if candidate.exists():
                return candidate.resolve()
        raise FileNotFoundError(f"Unable to resolve URDF asset: {path_value}")

    def run_loop(self, duration=10000):
        """Simple simulation loop."""
        try:
            for _ in range(duration):
                p.stepSimulation()
                time.sleep(1.0 / 240.0)
        except KeyboardInterrupt:
            print("Stopped.")


if __name__ == "__main__":
    import sys

    gui = "--headless" not in sys.argv
    path = PROJECT_ROOT / "configs" / "scenes" / "tabletop_scattered_cylinders_path_planning.yaml"
    mgr = SceneManager(gui=gui)
    mgr.init_simulation()
    mgr.load_scene(path)
    mgr.run_loop()
