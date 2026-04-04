"""Scene description via VLM (Ollama local vision model)."""
from __future__ import annotations

import base64
import json
import urllib.request


def capture_scene_frame(camera_distance=None, camera_yaw=None, camera_pitch=None, camera_target=None, save_path=None):
    """Capture a rendered frame from PyBullet and return as base64 JPEG."""
    import math
    import pybullet as p

    distance = camera_distance or 1.3
    yaw = camera_yaw or 130
    pitch = camera_pitch or -30
    target = camera_target or [0.05, 0.30, 0.90]

    # Compute view matrix from spherical coords (matches PyBullet's debug camera convention)
    yaw_rad = math.radians(yaw)
    pitch_rad = math.radians(pitch)
    dx = distance * math.cos(pitch_rad) * math.cos(yaw_rad)
    dy = distance * math.cos(pitch_rad) * math.sin(yaw_rad)
    dz = distance * math.sin(pitch_rad)
    cam_pos = [target[0] - dx, target[1] - dy, target[2] - dz]

    view_matrix = p.computeViewMatrix(cam_pos, target, [0, 0, 1])
    proj_matrix = p.computeProjectionMatrixFOV(60, 1280 / 720, 0.01, 10.0)

    width, height, rgb, depth, seg = p.getCameraImage(
        1280, 720, viewMatrix=view_matrix, projectionMatrix=proj_matrix,
        renderer=p.ER_BULLET_HARDWARE_OPENGL,
    )

    try:
        import numpy as np
        from PIL import Image
        import io
        img = Image.fromarray(np.array(rgb, dtype=np.uint8).reshape((height, width, 4)), "RGBA")
        img = img.convert("RGB")
        if save_path:
            img.save(save_path, "JPEG", quality=95)
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=90)
        return base64.b64encode(buf.getvalue()).decode("utf-8")
    except ImportError:
        raise RuntimeError("PIL (pillow) and numpy are required. Install: pip install pillow numpy")


def describe_image(image_b64: str, model: str = "llava", prompt: str = None) -> str:
    """Send a base64 JPEG image to Ollama and return the description."""
    if prompt is None:
        prompt = (
            "Describe this 3D robotics simulation scene in thorough detail. "
            "Provide a numbered list of every item you can see, including: "
            "the robot arm and its pose, every object on the table (name, color, shape, position), "
            "every object on each shelf level (top, middle, bottom — name, color, approximate position), "
            "the furniture layout (table, shelf/cupboard — material, dimensions, spatial relationships). "
            "Be precise and specific. If an object is small or partially occluded, still mention it."
        )

    payload = json.dumps({
        "model": model,
        "prompt": prompt,
        "images": [image_b64],
        "stream": False,
    }).encode("utf-8")

    req = urllib.request.Request(
        "http://localhost:11434/api/generate",
        data=payload,
        headers={"Content-Type": "application/json"},
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            return result.get("response", "(no response from model)")
    except urllib.error.URLError as e:
        return f"Error: Could not reach Ollama at localhost:11434. Is it running? ({e})"
    except Exception as e:
        return f"Error: {e}"


def describe_scene(model: str = "llava", prompt: str = None,
                   camera_distance=None, camera_yaw=None, camera_pitch=None, camera_target=None,
                   save_frame=None) -> str:
    """Capture the current PyBullet scene and describe it via Ollama."""
    image_b64 = capture_scene_frame(camera_distance, camera_yaw, camera_pitch, camera_target, save_path=save_frame)
    if save_frame:
        print(f"  Frame saved to: {save_frame}")
    return describe_image(image_b64, model=model, prompt=prompt)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Capture and describe a PyBullet scene")
    parser.add_argument("--model", default="llava", help="Ollama model name (default: llava)")
    parser.add_argument("--prompt", default=None, help="Custom prompt for the VLM")
    args = parser.parse_args()

    result = describe_scene(model=args.model, prompt=args.prompt)
    print(result)
