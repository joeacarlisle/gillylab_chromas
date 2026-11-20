"""Fixes needed to run CHROMAS 0.1.1 on a Windows laptop without a GPU or a C compiler.

Run it with the CHROMAS virtual environment's python (setup.bat does this):

    .venv\\Scripts\\python extras\\apply_patches.py [site-packages folder]

It is safe to run more than once. It does seven things:

1. Installs moving_least_squares.py (a pure NumPy replacement for CHROMAS's bundled Cython module,
   which pip does not build) into site-packages.
2. Patches the CHROMAS neural-net code so it runs on the CPU. As shipped it calls .cuda() and
   .half() unconditionally, and torch.load() fails on weights saved on a GPU machine.
   Originals are kept as <file>.bak. Reinstalling chromas undoes the patch: run this again.
3. Lets registration work on sparse skin. CHROMAS skips every frame in which chromatophores cover less than 5 %
   of the image when it looks for points to track; on skin with small, widely spaced chromatophores (the Gilly lab's
   squid skin is about 3 %) it skips them all and fails. The limit is lowered to 1 %. Dense skin is unaffected.
4. Lets `chromas train` run with the installed PyTorch on a CPU: the learning-rate scheduler is created without the
   `verbose` argument (removed from PyTorch), and starting weights saved on a GPU machine are loaded onto the CPU.
5. Lets `chromas slice` run with NumPy 2: it computes 2-D cross products with np.cross, which NumPy 2 accepts only for
   3-D vectors ("Both input arrays must be (arrays of) 3-dimensional vectors"). They are written out instead.
6. Lets `chromas run` cut videos that have a sound track. Its ffmpeg command filters the audio with `setpts`, which
   is a video filter, so ffmpeg stops ("Error linking filters ... audio") for any video with sound; the chunks are now
   written without sound (`-an`), which CHROMAS never uses. The real ffmpeg message was also hidden behind
   "'str' object has no attribute 'decode'"; it is now shown.

7. Lets the lookup method segment videos that split into several chunks. As shipped it segments every chunk from
   the FIRST chunk's video, so all chunks of a dataset come out as copies of chunk 0 (found on 16 November 2026 with a
   test video that loses focus mid-clip). Each chunk is now segmented from its own video. The neural network and
   random forest methods do not have this fault.

Each change is checked on its own, so a file that already has some changes gets the missing ones.
"""
import shutil
import sys
import sysconfig
from pathlib import Path

HERE = Path(__file__).resolve().parent
MARK = '# CPU patch'
DEV = "'cuda' if torch.cuda.is_available() else 'cpu'"
SPARSE = '# sparse-skin patch: was 0.05; the Gilly lab squid skin is about 3 % chromatophore'
TRAIN = '# training patch'
NUMPY2 = '# numpy 2 patch: np.cross needs 3-D vectors'

PATCHES = {
    'chromas/source/segmentation/neuralnet_utils.py': [
        ("torch.load(weights)", "torch.load(weights, map_location='cpu')"),
        ("model = model.half()",
         f"model = model.half() if torch.cuda.is_available() else model.float()  {MARK}"),
    ],
    'chromas/source/segmentation/segmentation_neuralnet.py': [
        ("normalize(img.half().permute(0, 3, 1, 2) / 255).cuda()",
         f"normalize((img.half() if torch.cuda.is_available() else img.float()).permute(0, 3, 1, 2) / 255)"
         f".to({DEV})  {MARK}"),
        ("\t\t\t\tmodel.cuda()", f"\t\t\t\tmodel.to({DEV})  {MARK}"),
        ("model = model.cuda()", f"model = model.to({DEV})  {MARK}"),
    ],
    'chromas/source/registration/registration.py': [
        ("while (chunk.segmentation.sel(frame=point_detection_frame) > 0).mean().compute() < 0.05:",
         f"while (chunk.segmentation.sel(frame=point_detection_frame) > 0).mean().compute() < 0.01:  {SPARSE}"),
    ],
    'chromas/source/training/neural_net_training.py': [
        ("ReduceLROnPlateau(optimizer, mode='min', factor=0.1, patience=5, verbose=True)",
         f"ReduceLROnPlateau(optimizer, mode='min', factor=0.1, patience=5)  {TRAIN}: verbose= was removed from PyTorch"),
        ("model.load_state_dict(torch.load(weights), strict=False)",
         f"model.load_state_dict(torch.load(weights, map_location='cpu'), strict=False)  {TRAIN}"),
    ],
    'chromas/source/chunking/chunking.py': [
        ("-af 'aselect=between(n\\,{onset}\\,{offset}),setpts=PTS-STARTPTS'", "-an -dn"),
        ("raise RuntimeError(result.stderr.decode('utf-8'))", "raise RuntimeError(result.stderr)  # audio patch"),
    ],
    'chromas/source/segmentation/segmentation_lookup.py': [
        ("\t\tsegment_video(video_path, weights, dataset, chunk_idx=chunk_idx,",
         "\t\tsegment_video(str(xr.open_zarr(dataset, 'chunking').chunk_paths.data.compute()[chunk_idx]), weights, dataset, "
         "chunk_idx=chunk_idx,"),
    ],
    'chromas/source/slicing/slicing.py': [
        ("\tr1, r2, r3 = tri\n",
         f"\tr1, r2, r3 = tri\n\tcross = lambda a, b: a[..., 0] * b[..., 1] - a[..., 1] * b[..., 0]  {NUMPY2}\n"),
        ("denominator = np.cross(r1 - r3, r2 - r3)", "denominator = cross(r1 - r3, r2 - r3)"),
        ("l1 = np.cross(r - r3, r2 - r3)", "l1 = cross(r - r3, r2 - r3)"),
        ("l2 = np.cross(r - r3, r3 - r1)", "l2 = cross(r - r3, r3 - r1)"),
    ],
}


def main():
    site = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(sysconfig.get_paths()['purelib'])
    if not (site / 'chromas').is_dir():
        sys.exit(f'chromas is not installed in {site}. Run this with the CHROMAS venv python.')

    shutil.copy2(HERE / 'moving_least_squares.py', site / 'moving_least_squares.py')
    print(f'installed  moving_least_squares.py -> {site}')

    for rel, pairs in PATCHES.items():
        path = site / rel
        with open(path, encoding='utf-8', newline='') as fh:     # keeps the file's line endings (Path.read_text
            text = fh.read()                                          # takes newline= only from Python 3.13)
        todo = [(old, new) for old, new in pairs if new not in text]
        if not todo:
            print(f'already patched  {rel}')
            continue
        for old, new in todo:
            if text.count(old) != 1:
                sys.exit(f'{rel}: expected one occurrence of {old!r}, found {text.count(old)}. '
                         'A different chromas version? Nothing changed in this file.')
        backup = path.with_name(path.name + '.bak')
        if not backup.exists():
            shutil.copy2(path, backup)
        for old, new in todo:
            text = text.replace(old, new)
        path.write_text(text, encoding='utf-8', newline='')
        print(f'patched    {rel} ({len(todo)} change(s))')


if __name__ == '__main__':
    main()
