# Dataset Staging

Place downloaded third-party household object assets here.

Suggested layout:

- `assets/datasets/ycb/<object-name>/`
- `assets/datasets/gso/<object-name>/`
- `assets/datasets/hope/<object-name>/`

Keep raw downloads separate from cleaned simulation assets when possible. A practical pattern is:

- `raw/` for untouched downloads
- `processed/` for mesh files rescaled and aligned for PyBullet

Then reference the processed mesh or URDF from `configs/objects/*.yaml` presets.
