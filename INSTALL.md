# Installing CHROMAS for the Gilly Lab Humboldt squid project

CHROMAS (Ukrow, Renard, Moghimi & Laurent, eLife 2025; `pip install chromas`, version 0.1.1) tracks individual
chromatophores in video. It does **not** install and run cleanly from `pip install chromas` alone on a Windows laptop
without a GPU. This document lists every change that was needed, and `setup.bat` applies them all.

Tested: Windows 11, Python 3.12, CPU only, no C compiler. `setup.sh` (Linux / macOS) does the same steps; it was run on Ubuntu 22.04 with Python 3.12 (chromas install and all seven patches), without the PyTorch step, and not on macOS.

## Quick install

```
cd <the folder where you cloned gillylab_chromas>
setup.bat
winget install Gyan.FFmpeg          (once per computer; then open a new terminal)
```

Linux / macOS: run `./setup.sh` instead, and install FFmpeg with `sudo apt install ffmpeg` or `brew install ffmpeg`.

Then add the CHROMAS authors' weights and example data (not part of this repository):

1. Download `Chromas2025.zip` from https://doi.org/10.17617/3.MJI3HA (check the licence on that page first).
2. Put the zip in this folder (or in your Downloads folder).
3. Run `build_demo.bat` (or `build_demo.bat "C:\path\Chromas2025.zip"`). It copies the weights to `model_weights\`, the
   example videos and dataset to `data\`, and the training images and masks to `training_data\`. See "Trained weights" below.

Then check the install:

```
.venv\Scripts\python -c "import torch, torchvision, decord, moving_least_squares, chromas; print('imports ok')"
```

## What `setup.bat` does, and why

| Step | What | Why |
|---|---|---|
| 1 | Uses Python **3.12** | chromas pins scikit-image 0.24, which has no wheel for Python 3.13. pip then tries to compile it and fails without a compiler (meson error). |
| 2 | Creates `.venv` here | CHROMAS needs opencv-python 4.x and older dask/zarr/xarray, which conflict with the squid project (Python 3.13, OpenCV 5, DuckDB 2). Separate environments keep both working. |
| 3 | `pip install --only-binary=scikit-image -r requirements.txt` | `chromas==0.1.1` plus `decord`. The flag forbids compiling scikit-image. |
| 4 | Installs CPU builds of `torch==2.15.0 torchvision==0.29.2 torchaudio==2.11.1` (the versions tested) | Not declared by chromas. Missing torchvision gives `No module named 'torchvision'` in the segment step. |
| 5 | `extras\apply_patches.py` | The seven fixes below. |
| 6 | Notes about FFmpeg and weights | These cannot be installed by pip. |

### Dependencies chromas does not declare

| Missing | Symptom | Fix |
|---|---|---|
| **FFmpeg**, system-wide | `CHROMAS finished but wrote no dataset`; log shows an `ffmpeg_command`. On Windows chromas cuts the video with `powershell ffmpeg ...`. | `winget install Gyan.FFmpeg`, new terminal. |
| **decord** | segment step stops: `No module named 'decord'` | In `requirements.txt` (Windows wheel for Python 3.12). |
| **torchvision** | segment step stops: `No module named 'torchvision'` | Step 4. |
| **moving_least_squares** | register step stops: `No module named 'moving_least_squares'` | Modification 1 below. |

### Modification 1: `moving_least_squares` replacement

`chromas run` imports a module `moving_least_squares`. The chromas wheel ships only Cython **source** for it
(`chromas/source/moving_least_squares/`), which pip does not build, and the PyPI package of the same name is broken
(its sdist lacks `mls.pyx`). Building the original needs the Microsoft C++ Build Tools.

`extras\moving_least_squares.py` is a pure NumPy re-implementation of the one function chromas uses,
`similarity(p, q, v, alpha)` (moving least squares, similarity variant; Schaefer et al. 2006). It was compared with the
compiled original on random control points and matched to about 0.001 px (float32 rounding); it is a few times slower.
`apply_patches.py` copies it to `.venv\Lib\site-packages\`.

### Modification 2: CPU patch of the neural-net segmentation

CHROMAS's neural-net step is written for CUDA. On a CPU-only machine it fails with
`Attempting to deserialize object on a CUDA device but torch.cuda.is_available() is False`, and `chromas run` still
prints "Pipeline run completed successfully" afterwards. `apply_patches.py` edits two files in the installed package
(originals are kept as `.bak`):

- `chromas/source/segmentation/neuralnet_utils.py`: `torch.load(weights, map_location='cpu')`; the model is converted
  with `.half()` only when CUDA is available, otherwise `.float()`.
- `chromas/source/segmentation/segmentation_neuralnet.py` (3 places): `.cuda()` becomes
  `.to('cuda' if torch.cuda.is_available() else 'cpu')`, and the input uses `.float()` on the CPU.

The patch is idempotent. Reinstalling or upgrading chromas removes it; run `python extras\apply_patches.py` again.
It refuses to patch (and changes nothing) if a line it expects is not found, e.g. in a different chromas version.

**Status:** the patched code was started on `example_chunk_0.mp4` and its segmentation step ran
(40 of 196 frames in about 15 minutes, 4 Dask workers, about 8 GiB of memory). **A full neural-net run to the end
(register, stitch, area) has not been completed on this laptop.** Expect roughly an hour for 196 frames of 1000x1000
video on a CPU. A GPU makes it practical; with one, pass `--gpu true` and the patch changes nothing.

### Modification 3: registration on sparse skin

When the register step looks for points to track, CHROMAS skips every frame in which chromatophores cover less
than 5 % of the image (`registration.py`, about line 803: `... .mean().compute() < 0.05:`). On skin with small,
widely spaced chromatophores it skips all of them and the run fails. The Gilly lab's squid skin video
(`TS-20220801155100769.mp4`, in the squid project's `examples/gilly_2022/`) is about 3 % chromatophore.
`apply_patches.py` lowers the limit to 1 % (the line is marked `# sparse-skin patch`; the original is kept as
`registration.py.bak`). Dense skin such as the cuttlefish examples is above both limits and is unaffected.

**Status:** with this change CHROMAS 0.1.1 (lookup method) ran through chunking, segmentation, registration,
stitching and area on the Gilly video (600 frames, 136 chromatophores in the analysed region).
That run was made in a Linux environment; the patch was applied to this `.venv` on 13 Nov 2026 and has not yet been
run here on Windows.

### Modification 4: training on this PyTorch

`chromas train` creates its learning-rate scheduler with `verbose=True`, which the installed PyTorch (2.15) no longer
accepts, so training stops at once; and it loads starting weights without `map_location`, which fails without a GPU.
`apply_patches.py` removes `verbose=True` and adds `map_location='cpu'` in
`chromas\source\training\neural_net_training.py` (marked `# training patch`). How to prepare training data and
fine-tune the network: `docs/TRAINING_THE_NETWORK.md` in the squid project. No full training run has been made on
this laptop.

### Modification 5: the slice step on NumPy 2

`chromas slice` (the wedges behind the dashboard's flower plots) computes 2-D cross products with `np.cross`, which NumPy 2 accepts only for 3-D vectors, so it stops with "Both input arrays must be (arrays of) 3-dimensional vectors" and prints "Slicing failed!". `apply_patches.py` writes the 2-D cross product out in `chromas\source\slicing\slicing.py` (marked `# numpy 2 patch`). Tested on both Gilly lab videos.

### Modification 6: videos with a sound track

`chromas run` cuts the video into chunks with ffmpeg and filters the sound with `setpts`, which is a video filter, so ffmpeg stops ("Error linking filters", "Error opening output files: Invalid argument") for any video that has sound. The error then appeared as "'str' object has no attribute 'decode'", because CHROMAS decodes text that is already text. `apply_patches.py` writes the chunks without sound (`-an`; CHROMAS never uses it) and shows ffmpeg's own message, in `chromas\source\chunking\chunking.py` (marked `# audio patch`). Found with `jeb114157_video1.mp4`, which has an AAC sound track.

### Modification 7: the lookup method with several chunks

As shipped, the lookup method segments every chunk of a dataset from the first chunk's video, so all chunks come out as
copies of chunk 0 (found with a test video that loses focus in the middle of the clip). `apply_patches.py` segments each
chunk from its own video in `chromas\source\segmentation\segmentation_lookup.py`. The neural network and random forest
methods do not have this fault.

## Trained weights (not in the pip package)

The neural-net method needs a `.pth` file; the default path inside the package does not exist.
From the CHROMAS data repository (Edmond, doi 10.17617/3.MJI3HA) download `Chromas2025.zip`, then run
`build_demo.bat` (zip in this folder or in Downloads, or `build_demo.bat "C:\path\Chromas2025.zip"`). It copies

- `model_weights\sepia_2classes_fcn_resnet50.pth` (141 MB) into `model_weights\`
- `tutorial_data\` (`example.mp4`, `example_chunk_0/1/2.mp4`, `example.dataset`) into `data\`
- `training_data\sepia_binary` and `sepia_3class` (painted `images\` and `masks\`, 79 MB) into `training_data\`

All three folders are ignored by git. To do it by hand, copy those folders from the unzipped `Chromas2025` folder.

The provided models were trained on manually annotated images of both bobtail squid (*Euprymna berryi*) and cuttlefish
(*Sepia officinalis*), not on Humboldt squid, and their performance on Humboldt squid has not been tested. The licence
of the weights is stated on the Edmond page of the data release; check it before you share the file. The CHROMAS paper
says the neural-network method needs an NVIDIA GPU; this install runs it on the CPU only because of modification 2.

## Running CHROMAS by hand

```
.venv\Scripts\activate
chromas run data\example_short_120f.mp4 --output-name output\demo.zarr --force-overwrite true ^
    --method neuralnet --focus-threshold 0.01 --weights model_weights\sepia_2classes_fcn_resnet50.pth
```

- Flags of the single steps become options that take a value in `chromas run`: write `--force-overwrite true`,
  `--gpu true`. A bare flag swallows the next argument and the command fails with exit code 2.
- The many "parameter ... is used more than once" warnings are harmless.
- The video needs at least 100 consecutive in-focus frames (`min_chunk_duration`), so clips shorter than that fail.
  `data\example_short_120f.mp4` is the first 120 frames of `example_chunk_0.mp4` for quicker tests.
- `chromas run` can print an error for a step and still report success. A good run has data files in
  `<name>.zarr\chunk_0\segmentation\` and an `areas` array in `chunk_0`, not only `.zarray` and `.zattrs`.
- The Dask dashboard at http://127.0.0.1:8787 opens by itself; it is harmless.
- `--method lookup` opens interactive matplotlib windows (click colour cluster centres, press Q, more windows follow);
  the run waits for them. It saves `output\lookup_table.npz`, which can be passed with `--weights` to skip the clicking,
  but the result depends on where you clicked: a poor table labels most of the frame as chromatophore (81% in our test)
  and registration then fails with `Not enough chromatophores detected (0 < 40)`.
- `--method randomforest` needs a trained random-forest model, which is not provided; it was not tried.

## The bridge: how the squid project uses CHROMAS

The two projects stay in **separate environments** and talk only through files and subprocesses. The squid project never
imports chromas.

```
 squid project (Python 3.13)                       this project (Python 3.12)
 ----------------------------                      ---------------------------
 chromatophore_holoviews.py
   CHROMAS tab = chromas_view.py
        |  Run CHROMAS button (thread)
        v
 chromas_bridge.py  -- run_pipeline() ---------->  .venv\Scripts\chromas.exe run VIDEO ...
        |                                              writes output\<name>.zarr
        |          -- export_dataset() ---------->  .venv\Scripts\python.exe chromas_export.py
        |                                              reads the Zarr with zarr only, writes
        |                                              processed\chromas_export\<name>\
        |                                              areas.csv, focus.csv, info.json, overlay.png
        v
 load_into_duckdb()  ->  processed\gl_chromas.duckdb
        |                  chromas_runs, chromas_areas, chromas_focus
        v
 chromas_view.py reads the tables (read-only) -> area curves, heat map, stats table, overlay
```

**Definition of the bridge** (all in the squid project):

- **Location.** `config.defaults.toml`, section `[chromas]`: `home = "../gillylab_chromas"` (relative to the squid
  project; the environment variable `GL_CHROMAS_HOME` overrides it), `method = "neuralnet"`, `focus_threshold = 0.01`.
  From `home` the bridge derives `.venv\Scripts\chromas.exe`, `.venv\Scripts\python.exe`, `data\`, `output\` and
  `model_weights\sepia_2classes_fcn_resnet50.pth`.
- **Step 1, run.** `chromas_bridge.run_pipeline(video, name, method, focus_threshold, gpu, weights)` starts
  `chromas.exe run <video> --output-name output\<name>.zarr --force-overwrite true --method <m> --focus-threshold <t>`
  with `--weights <file>` and `--gpu true` when given. A bare video name is looked up in `data\`. For `neuralnet` it
  checks the weights file exists. Output is streamed to the dashboard (click warnings filtered out) and the complete
  unfiltered output is appended to `processed\chromas_last_run.log`. It raises an error if the Zarr was not written.
- **Step 2, export.** `chromas_export.py` runs **in the CHROMAS Python** (it is the one with zarr). It reads the
  `chunking` group and each `chunk_N/areas` array (column 0 is the background and is dropped) and writes
  `areas.csv` (chunk, frame, orig_frame, t_s, chromatophore, area), `focus.csv`, `info.json` (fps, chunk and
  chromatophore counts, synthetic flag) and `overlay.png` (if OpenCV and scikit-image are present).
  It fails with "No chunk has 'areas'" when CHROMAS stopped before its area step.
- **Step 3, load.** `load_into_duckdb()` replaces the dataset's rows in one transaction in
  `processed\gl_chromas.duckdb`. This is a separate file from `gl_chromatophore.duckdb`, which the dashboard keeps open
  read-only.

| Table | Content |
|---|---|
| `chromas_runs` | one row per dataset: video, zarr path, method, fps and its source, counts, synthetic flag, overlay path, import time |
| `chromas_areas` | `dataset_id, chunk, frame, orig_frame, t_s, chromatophore, area` |
| `chromas_focus` | `dataset_id, frame, t_s, in_focus, statistic` |

- **Command line** (squid environment, squid folder): `python chromas_bridge.py check | list | run VIDEO [--name --method
  --focus-threshold --weights --gpu] | import PATH.zarr [--name]`. `import` loads a Zarr that was produced by hand.
- **Demo without CHROMAS results:** `make_fake_chromas.py` (run with the CHROMAS python) writes a synthetic
  CHROMAS-style Zarr, `output\fake_demo.zarr`. The dashboard marks it "Synthetic data".
- **Time axis.** `t_s` uses the frame number from the original video divided by fps (from the dataset attribute, else
  the original video, else 20). CHROMAS's `--onset` option is not applied; this has not been checked against a real run.

Not yet verified end to end: a complete real run through the dashboard (neural net finishing and being exported). The
export and the dashboard were tested with the synthetic dataset and with a stub of chromas.
