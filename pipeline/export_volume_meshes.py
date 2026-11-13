#!/usr/bin/env python3
"""Export CODA volume.mat classes to OBJ meshes for Blender."""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

CLASS_NAMES = {
    1: "bronchioles",
    2: "alveoli",
    3: "vasculature",
    4: "cancer",
    5: "nonexpanded",
    6: "background",
    7: "stroma",
}

# Official CODA lung cmap (0-1)
CMAP = {
    1: (150 / 255, 99 / 255, 23 / 255),
    2: (23 / 255, 80 / 255, 150 / 255),
    3: (150 / 255, 31 / 255, 23 / 255),
    4: (199 / 255, 196 / 255, 147 / 255),
    5: (23 / 255, 80 / 255, 150 / 255),
    7: (242 / 255, 167 / 255, 227 / 255),
}


def load_vol(path: Path):
    try:
        from scipy.io import loadmat

        d = loadmat(str(path))
        if "vol" in d:
            return np.asarray(d["vol"])
    except Exception:
        pass
    import h5py

    with h5py.File(path, "r") as f:
        vol = np.array(f["vol"])
        # MATLAB v7.3 often stores as Fortran order / transposed
        if vol.ndim == 3:
            vol = np.transpose(vol, (2, 1, 0))
        return vol


def write_obj(path: Path, verts: np.ndarray, faces: np.ndarray) -> None:
    with path.open("w", encoding="utf-8") as f:
        f.write("# CODA lung mesh\n")
        for v in verts:
            f.write(f"v {v[0]:.5f} {v[1]:.5f} {v[2]:.5f}\n")
        for face in faces:
            # skimage faces are 0-based; OBJ is 1-based
            f.write(f"f {face[0]+1} {face[1]+1} {face[2]+1}\n")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--volume", required=True)
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--classes", default="1,2,3,7", help="comma classes to mesh")
    ap.add_argument("--step", type=int, default=2, help="downsample for meshing speed")
    ap.add_argument("--smooth", type=int, default=1)
    args = ap.parse_args()

    from skimage import measure, morphology

    out = Path(args.outdir)
    out.mkdir(parents=True, exist_ok=True)
    vol = load_vol(Path(args.volume))
    print("vol", vol.shape, vol.dtype, "unique", np.unique(vol)[:20])

    if args.step > 1:
        vol = vol[:: args.step, :: args.step, :: args.step]

    classes = [int(x) for x in args.classes.split(",") if x.strip()]
    for c in classes:
        if c == 6:
            continue
        mask = vol == c
        if args.smooth:
            mask = morphology.binary_closing(mask, morphology.ball(1))
            mask = morphology.remove_small_objects(mask, min_size=200)
        if mask.sum() < 500:
            print(f"skip class {c}: too few voxels ({mask.sum()})")
            continue
        verts, faces, normals, _ = measure.marching_cubes(mask.astype(np.float32), level=0.5, step_size=1)
        # scale: step voxels -> mm if sk=4 um => 0.004 mm * step
        verts = verts * (0.004 * args.step)
        name = CLASS_NAMES.get(c, f"class_{c}")
        obj = out / f"{c:02d}_{name}.obj"
        write_obj(obj, verts, faces)
        print(f"wrote {obj.name}: verts={len(verts)} faces={len(faces)} color={CMAP.get(c)}")

    meta = out / "materials.json"
    import json

    meta.write_text(
        json.dumps(
            {
                "classes": {
                    str(c): {"name": CLASS_NAMES.get(c, str(c)), "rgb": list(CMAP.get(c, (0.5, 0.5, 0.5)))}
                    for c in classes
                    if c != 6
                },
                "unit": "mm",
                "voxel_um": 4 * args.step,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print("DONE", out)


if __name__ == "__main__":
    main()
