@echo off
REM Creates the virtual environment for CHROMAS in this folder and installs everything needed to run it
REM on a Windows laptop WITHOUT a GPU and WITHOUT a C compiler. See INSTALL.md for the reasons behind each step.
cd /d "%~dp0"

REM 1. Python 3.12 (chromas pins scikit-image 0.24, which has no wheel for Python 3.13)
where py >nul 2>nul
if errorlevel 1 (
  echo Python launcher "py" not found. Install Python 3.12 with: winget install Python.Python.3.12
  goto fail
)
py -3.12 --version >nul 2>nul
if errorlevel 1 (
  echo Python 3.12 not found. Install it with: winget install Python.Python.3.12
  goto fail
)

REM 2. Virtual environment
if not exist .venv (
  py -3.12 -m venv .venv
  if errorlevel 1 goto fail
)
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip

REM 3. chromas and decord (requirements.txt), prebuilt scikit-image only
pip install --only-binary=scikit-image -r requirements.txt
if errorlevel 1 goto fail

REM 4. CPU builds of PyTorch (smaller download; chromas needs torchvision, which it does not declare)
pip install torch==2.15.0 torchvision==0.29.2 torchaudio==2.11.1 --index-url https://download.pytorch.org/whl/cpu
if errorlevel 1 goto fail

REM 5. Fixes for chromas itself: moving_least_squares replacement, the CPU patch, and registration on sparse skin
python extras\apply_patches.py
if errorlevel 1 goto fail

REM 6. Things setup cannot install for you
where ffmpeg >nul 2>nul
if errorlevel 1 echo NOTE: FFmpeg is not on the PATH. Install it with: winget install Gyan.FFmpeg   (then open a new terminal)
if not exist model_weights\sepia_2classes_fcn_resnet50.pth echo NOTE: trained weights missing. See "Trained weights" in INSTALL.md.

echo.
echo Done. Check the install with:  .venv\Scripts\python -c "import torch, torchvision, decord, moving_least_squares, chromas; print('imports ok')"
echo Activate with:                 .venv\Scripts\activate
pause
exit /b 0
:fail
echo.
echo Setup failed. See the messages above.
pause
exit /b 1
