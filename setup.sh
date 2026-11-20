#!/usr/bin/env bash
# Creates the virtual environment for CHROMAS in this folder and installs everything needed to run it
# on a computer WITHOUT a GPU and WITHOUT a C compiler (Linux / macOS). See INSTALL.md for the reasons behind each step.
set -e

# Keep the window open at the end (also after an error) so the messages can be read.
finish() {
  code=$?
  echo
  if [ "$code" -ne 0 ]; then echo "Setup failed (exit code $code). See the messages above."; fi
  if [ -t 0 ]; then read -r -p "Press Enter to close this window..." _; fi
}
trap finish EXIT
cd "$(dirname "$0")"

# 1. Python 3.12 (chromas pins scikit-image 0.24, which has no wheel for Python 3.13)
if ! command -v python3.12 >/dev/null 2>&1; then
  echo "Python 3.12 not found."
  echo "  macOS (Homebrew):   brew install python@3.12"
  echo "  Ubuntu / Debian:    install python3.12 (deadsnakes PPA) or use pyenv"
  exit 1
fi

# 2. Virtual environment
if [ ! -d .venv ]; then
  python3.12 -m venv .venv
fi
source .venv/bin/activate
python -m pip install --upgrade pip

# 3. CPU builds of PyTorch first (chromas needs torchvision, which it does not declare). Installing them before chromas
#    keeps pip from pulling the much larger CUDA build of PyTorch that chromas's dependencies would otherwise bring in.
#    Linux: the CPU index. macOS: the default index already has CPU builds.
if [ "$(uname -s)" = "Linux" ]; then
  pip install torch==2.15.0 torchvision==0.29.2 torchaudio==2.11.1 --index-url https://download.pytorch.org/whl/cpu
else
  pip install torch==2.15.0 torchvision==0.29.2 torchaudio==2.11.1
fi

# 4. chromas and decord (requirements.txt), prebuilt scikit-image only
pip install --only-binary=scikit-image -r requirements.txt

# 5. Fixes for chromas itself: moving_least_squares replacement, the CPU patch, and the others
python extras/apply_patches.py

# 6. Things setup cannot install for you
command -v ffmpeg >/dev/null 2>&1 || echo "NOTE: FFmpeg is not installed. macOS: brew install ffmpeg   Ubuntu / Debian: sudo apt install ffmpeg"
[ -f model_weights/sepia_2classes_fcn_resnet50.pth ] || echo 'NOTE: trained weights missing. See "Trained weights" in INSTALL.md.'

echo
echo "Done. Check the install with:  .venv/bin/python -c \"import torch, torchvision, decord, moving_least_squares, chromas; print('imports ok')\""
echo "Activate with:                 source .venv/bin/activate"
