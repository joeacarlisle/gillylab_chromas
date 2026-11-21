# Gilly Lab CHROMAS

A separate environment for [CHROMAS](https://elifesciences.org/articles/106509) (Ukrow, Renard, Moghimi & Laurent, eLife 2025), which segments and tracks individual cephalopod chromatophores in video.

It is kept apart from `gillylab_squid_chromatophore` because CHROMAS needs `opencv-python` 4.x while that project pins `opencv-python-headless` 5.0. Both write to the same `cv2` folder and would overwrite each other.

## Installation

### Root Directory Notes

The project root can be named anything (e.g., `gillylab_chromas`).

To avoid Windows permission issues, place the root folder inside your Windows user directory, next to the squid project:
`C:\Users\<your_username>\gillylab_chromas`

The squid dashboard looks for this folder at `../gillylab_chromas` by default.

### Python Installation Requirements

This project requires **Python 3.12**. Python 3.13, which the squid project uses, does not work here: chromas pins scikit-image 0.24, which has no Windows wheel for 3.13, and pip then fails trying to compile it.

#### Windows

Install Python 3.12 from python.org (not from the Microsoft Store, which puts it in a different folder than the instructions below assume).

1. If you installed Python 3.12 from the Microsoft Store, remove it first: Windows Settings, Apps, "Python 3.12", Uninstall.
2. Download the "Windows installer (64-bit)" for Python 3.12 from https://www.python.org/downloads/windows/.
3. Run it and choose **Install Now**. Leave **"Install for all users"** unticked, so it installs for your user only. Leave the **py launcher** ticked.
4. When the installer asks to **"Add python.exe to PATH"**, select **No** (leave it unticked).
5. Python installs to `C:\Users\<your_username>\AppData\Local\Programs\Python\Python312\`.
6. Check it in Command Prompt: `py -0p` should list `Python312` under `AppData\Local\Programs\Python`.

#### macOS (Homebrew)

    brew install python@3.12

#### Linux (Ubuntu / Debian) using apt install

    sudo add-apt-repository ppa:deadsnakes/ppa
    sudo apt update
    sudo apt install python3.12 python3.12-venv

#### Linux (Ubuntu / Debian) using pyenv

This has the advantage of not requiring root privileges, and it does not install Python 3.12 system wide.

    # Install pyenv:
    curl -fsSL https://pyenv.run | bash
    # Install Python 3.12:
    pyenv install 3.12

### Prerequisites

**Git** must be installed to download the software from GitHub (`git clone`). Download it from [git-scm.com](https://git-scm.com/downloads) and confirm with `git --version`.

**FFmpeg** must be on the PATH, because CHROMAS cuts the video into chunks with it. Confirm with `ffmpeg -version`.

* Windows: `winget install Gyan.FFmpeg`, then open a new terminal.
* macOS: `brew install ffmpeg`
* Linux: `sudo apt install ffmpeg`

Python 3.12 is required (see above). The dependencies, including PyTorch, are installed by `setup.bat` / `setup.sh`; no manual download is required. The install is large because of PyTorch.

### Getting Started

On Windows, clone into your user directory (`C:\Users\<your_username>`), next to `gillylab_squid_chromatophore`:

    cd C:\Users\<your_username>
    git clone https://github.com/joeacarlisle/gillylab_chromas.git
    cd gillylab_chromas

Then follow the **Prerequisites** and **Setup** sections to install Python 3.12 and the project dependencies.

### Setup: Virtual Environment and Installation

*Run from the project root directory.*

#### Windows (Command Prompt)

The quick way (needs Python 3.12; `winget install Python.Python.3.12`):

    cd C:\Users\<your_username>\gillylab_chromas
    setup.bat
    .venv\Scripts\activate
    chromas --help

`setup.bat` creates `.venv` with Python 3.12, installs `requirements.txt` and CPU PyTorch, and applies the patches that make CHROMAS run on a laptop without a GPU or a C compiler. The steps are listed in **INSTALL.md**.

#### macOS / Linux

The quick way (needs `python3.12` on the PATH):

    cd gillylab_chromas
    ./setup.sh
    source .venv/bin/activate
    chromas --help

`setup.sh` does the same as `setup.bat`. It was tested on Ubuntu 22.04 (Linux x86-64) with Python 3.12 up to the patches; PyTorch's CPU index could not be reached from the test machine, so the PyTorch step is untested. macOS has not been tested; `decord` may have no wheel for Apple Silicon.

## Using CHROMAS: command line or dashboard

CHROMAS is a command-line program. With the environment activated (see **Setup**), `chromas` lists its commands and each command lists its own options:

    chromas --help
    chromas run --help
    chromas area --help
    chromas analyse --help

`chromas run` does the whole pipeline on a video (chunking, segmentation, registration, stitching and area). The other commands run single steps or analyses on a finished `<name>.zarr`, such as `area` (measure the areas again), `slice`, `ica`, `analyse cluster` and `train`. In a command, a flag that takes a value is written with the value: `--force-overwrite true`, `--gpu true`.

The dashboard of `gillylab_squid_chromatophore` replaces these calls: its buttons start the same commands for you and load the results into DuckDB, so you do not have to type them. Each command it runs is written at the top of its log, starting with `>`, and every run is appended to `processed/chromas_last_run.log` in the squid project. To repeat a run by hand, copy that line into a terminal in this folder, with the environment activated.

## About CHROMAS

The paper that describes the project is Ukrow, Renard, Moghimi & Laurent, *CHROMAS: A computational pipeline to track chromatophores and analyse their dynamics*, eLife 2025: https://elifesciences.org/articles/106509. It covers what CHROMAS segments and tracks, the three segmentation methods, registration and stitching, and the measures it produces. Copyright stays with the authors; see the article page for the licence.

## Folders

- `data/` input videos, and the authors' example videos after `build_demo.bat` (not tracked by git)
- `output/` CHROMAS results: `<name>.zarr`, the chunk videos, and the lookup colour tables `<name>.lookup_table.npz` that the squid dashboard's colour picker saves (not tracked by git)
- `model_weights/` the trained network `sepia_2classes_fcn_resnet50.pth`, copied here by `build_demo.bat` (not tracked by git)
- `training_data/` the authors' training images and masks, copied here by `build_demo.bat` (not tracked by git)
- `extras/` the patches applied by the setup (tracked)

## Notes

- Overlapping chromatophores cannot be resolved, and CHROMAS recommends at least about 10 pixels per chromatophore, so it suits close-up skin video rather than distant clips such as the Humboldt squid movies used in the other project.
- `decord` is listed in the CHROMAS README but is not installed by `pip install chromas`; it is in `requirements.txt`. Without it the segmentation step fails with `No module named 'decord'`.
- FFmpeg must be installed on the system: on Windows CHROMAS cuts the video into chunks by running `powershell ffmpeg`.

## Used from the squid project

Install both projects in your user directory, side by side (`C:\Users\<your_username>\gillylab_chromas` and `C:\Users\<your_username>\gillylab_squid_chromatophore`). `gillylab_squid_chromatophore` starts `chromas.exe` from this folder's `.venv` (`chromas_bridge.py`, or the CHROMAS tab of its dashboard) and loads the results into its own DuckDB. Videos go in `data/`; results are written to `output/<name>.zarr`. Nothing needs to be changed here for that.

## Trained weights (neuralnet segmentation)

The chromas package ships without trained weights, and this repository does not contain them either. `model_weights/sepia_2classes_fcn_resnet50.pth` comes from `Chromas2025.zip` (Edmond, doi 10.17617/3.MJI3HA) and is put there by `build_demo.bat` (below). The squid project's bridge passes it to `chromas run --weights` for the `neuralnet` method; if the file is missing, a `neuralnet` run stops with a message. The `lookup` and `randomforest` methods need no downloaded weights (a random forest needs a model you train yourself).

**Example data.** The zip also holds the authors' example videos and training images. None of it is in this repository. Download `Chromas2025.zip` from https://doi.org/10.17617/3.MJI3HA (check the licence there first), then run `build_demo.bat` (put the zip in this folder or in your Downloads folder, or pass its path: `build_demo.bat "C:\path\Chromas2025.zip"`). It unpacks the zip and copies the weights to `model_weights\`, the example videos and dataset to `data\`, and the training images and masks to `training_data\`. All three folders are ignored by git.

## Patches applied by the setup

CHROMAS 0.1.1 does not run unchanged on a laptop without a GPU or a C compiler, or on current PyTorch and NumPy. `setup.bat` / `setup.sh` run `extras/apply_patches.py`, which makes seven changes. It edits the installed copy of CHROMAS in `.venv`; the CHROMAS source is not part of this repository. Each edited file is first copied to `<file>.bak`, each change is marked in the code (for example `# sparse-skin patch`), and the script stops without changing anything if a line it expects is not found, as in a different CHROMAS version. The patches are idempotent. Reinstalling or upgrading `chromas` removes them; run `python extras/apply_patches.py` again.

| # | Problem in CHROMAS 0.1.1 | What the patch does |
|---|---|---|
| 1 | `chromas run` imports `moving_least_squares`, a Cython module that `pip install chromas` ships only as source and that needs a C compiler. | Installs `extras/moving_least_squares.py`, a pure NumPy replacement of the one function CHROMAS uses (matches the compiled version to about 0.001 px, slower), into `.venv`'s `site-packages`. |
| 2 | The neural-network segmentation is written for CUDA and stops on a computer without a GPU. | Chooses the device by itself: the GPU if there is one, otherwise the CPU, in single precision. A GPU run is unchanged. |
| 3 | The registration step skips every frame with less than 5 % chromatophore pixels, so a run on sparse skin (for example the Gilly lab squid video, about 3 %) fails. | Lowers the limit to 1 %. Dense skin is unaffected. |
| 4 | `chromas train` stops at once on current PyTorch (`verbose=True` is no longer accepted) and cannot load its starting weights without a GPU. | Removes `verbose=True` and loads the weights onto the CPU. |
| 5 | `chromas slice` stops on NumPy 2 ("Both input arrays must be (arrays of) 3-dimensional vectors"). | Writes out the 2-D cross product by hand. |
| 6 | Videos with a sound track fail in the chunking step, because the video filter is applied to the sound as well. | Cuts the chunks without sound (`-an`; CHROMAS does not use it) and shows ffmpeg's own error message. |
| 7 | The lookup method segments every chunk of a dataset from the first chunk's video, so all chunks are copies of chunk 0. | Segments each chunk from its own video. The neural network and random forest methods are not affected. |

Patch 2 matters only for the neural network, 4 only for training, 5 only for the slice step and 6 only for videos with sound. **INSTALL.md** gives the symptom, the edited file and the test status of each one, and says how the squid project calls CHROMAS.

## Licence and credits

CHROMAS is copyright (c) 2025 Johann Ukrow and is released under the BSD 3-Clause licence; its text is in
`LICENSE-CHROMAS`. This repository holds only an install wrapper and patches for CHROMAS 0.1.1 (`setup.bat`,
`requirements.txt`, `extras/`); they are not by the CHROMAS authors and the authors do not endorse them. Cite: Ukrow,
J., Renard, M. D. M., Moghimi, M. & Laurent, G. CHROMAS: A computational pipeline to track chromatophores and analyze
their dynamics. eLife 14:RP106509 (2025). Source: https://gitlab.mpcdf.mpg.de/mpibr/laur/cuttlefish/chromas

The trained weights (`Chromas2025.zip`, Edmond, doi 10.17617/3.MJI3HA) are not included here. Check the licence on the
Edmond page before you redistribute them.
