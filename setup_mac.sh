#!/usr/bin/env bash
# setup_mac.sh — one-shot setup for mcr-robotics on Apple Silicon Mac
# Usage: bash setup_mac.sh
# Works on: macOS + M1 / M2 / M3 / M4 (osx-arm64)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_NAME="mcr-robotics"

# ── colors ────────────────────────────────────────────────────────────────────
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
ok()   { echo -e "${GREEN}✓${NC} $*"; }
warn() { echo -e "${YELLOW}!${NC} $*"; }
die()  { echo -e "${RED}✗${NC} $*"; exit 1; }

echo ""
echo "  mcr-robotics — Mac setup"
echo "  ─────────────────────────────────────────"
echo ""

# ── 1. verify we're on Apple Silicon ─────────────────────────────────────────
ARCH=$(uname -m)
if [[ "$ARCH" != "arm64" ]]; then
    warn "This script targets Apple Silicon (arm64). Detected: $ARCH"
    warn "If you're on Intel Mac, the conda-forge pybullet binary may differ."
    read -p "Continue anyway? [y/N] " -n1 -r; echo
    [[ $REPLY =~ ^[Yy]$ ]] || exit 1
fi
ok "Apple Silicon detected ($ARCH)"

# ── 2. check for conda (miniconda / anaconda / miniforge) ────────────────────
if ! command -v conda &>/dev/null; then
    echo ""
    warn "conda not found. Installing Miniconda for Apple Silicon..."
    MINICONDA_URL="https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-arm64.sh"
    MINICONDA_SH="/tmp/miniconda_install.sh"
    curl -fsSL "$MINICONDA_URL" -o "$MINICONDA_SH"
    bash "$MINICONDA_SH" -b -p "$HOME/miniconda3"
    eval "$("$HOME/miniconda3/bin/conda" shell.bash hook)"
    ok "Miniconda installed at ~/miniconda3"
else
    # make sure conda shell functions are loaded in this script's subshell
    CONDA_BASE=$(conda info --base 2>/dev/null)
    # shellcheck source=/dev/null
    source "$CONDA_BASE/etc/profile.d/conda.sh"
    ok "conda found ($(conda --version))"
fi

# ── 3. remove stale env if it exists ─────────────────────────────────────────
if conda env list | grep -q "^${ENV_NAME} "; then
    warn "Existing '${ENV_NAME}' environment found — removing it first..."
    conda env remove -n "$ENV_NAME" -y -q
    ok "Old environment removed"
fi

# ── 4. create environment from environment.yml ───────────────────────────────
echo ""
echo "  Creating conda environment '${ENV_NAME}'..."
echo "  (this downloads ~150 MB the first time — grab a coffee)"
echo ""
cd "$SCRIPT_DIR"
conda env create -f environment.yml

ok "Environment '${ENV_NAME}' created"

# ── 5. smoke test ─────────────────────────────────────────────────────────────
echo ""
echo "  Running smoke test..."
conda run -n "$ENV_NAME" python - <<'PYEOF'
import pybullet
import numpy
import yaml
import scipy
import matplotlib
import networkx
from src.mcr import __version__
print(f"  pybullet : {pybullet.getAPIVersion()}")
print(f"  numpy    : {numpy.__version__}")
print(f"  networkx : {networkx.__version__}")
print(f"  mcr pkg  : v{__version__}")
PYEOF

ok "All imports OK"

# ── 6. list available scenes ──────────────────────────────────────────────────
echo ""
echo "  Available scenes:"
conda run -n "$ENV_NAME" python run.py --list-scenes 2>/dev/null | grep "  -"

# ── 7. done ───────────────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}  Setup complete!${NC}"
echo ""
echo "  To activate the environment:"
echo "    conda activate ${ENV_NAME}"
echo ""
echo "  To run a scene (GUI, runs until Ctrl+C):"
echo "    python run.py --scene tabletop_scattered_cylinders_path_planning"
echo ""
echo "  To run headless:"
echo "    python run.py --scene tabletop_scattered_cylinders_path_planning --headless"
echo ""
echo "  NOTE: pybullet is installed from conda-forge as a prebuilt binary."
echo "  Do NOT 'pip install pybullet' — it will fail to compile on macOS 15+."
echo ""
