#!/usr/bin/env python3
"""CODA Section 2 (OpenSlide path): downsample NDPI -> 10x/5x/1x TIFs.

Official guide: ds=[1,2,10] um/px -> folders 10x, 5x, 1x.
NDPI here is ~0.4416 um/px at 20x objective.
"""
from __future__ import annotations

import argparse
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import openslide
from PIL import Image

Image.MAX_IMAGE_PIXELS = None


TARGETS = (
    ("10x", 1.0),  # ~1 um/px
    ("5x", 2.0),   # ~2 um/px
    ("1x", 10.0),  # ~10 um/px
)


def mpp_of(slide: openslide.OpenSlide) -> float:
    mx = slide.properties.get("openslide.mpp-x")
    if mx is None:
        raise RuntimeError("missing openslide.mpp-x")
    return float(mx)


def best_level(slide: openslide.OpenSlide, downsample: float) -> int:
    # Prefer the highest level whose downsample <= target (closest without upsampling).
    levels = list(slide.level_downsamples)
    best = 0
    for i, ds in enumerate(levels):
        if ds <= downsample + 1e-6:
            best = i
        else:
            break
    return best


def downsample_one(ndpi: Path, out_root: Path, overwrite: bool = False) -> str:
    slide = openslide.OpenSlide(str(ndpi))
    try:
        mpp = mpp_of(slide)
        stem = ndpi.stem
        outs = []
        for folder, target_um in TARGETS:
            out_dir = out_root / folder
            out_dir.mkdir(parents=True, exist_ok=True)
            out_path = out_dir / f"{stem}.tif"
            if out_path.exists() and not overwrite:
                outs.append(f"{folder}:skip")
                continue
            factor = target_um / mpp  # relative to level-0 pixels
            lvl = best_level(slide, factor)
            lvl_ds = float(slide.level_downsamples[lvl])
            # Read full level, then residual resize to exact target.
            region = slide.read_region((0, 0), lvl, slide.level_dimensions[lvl])
            rgb = region.convert("RGB")
            residual = lvl_ds / factor
            # residual < 1 means level is finer than target -> shrink; >1 means upsample (avoid)
            if abs(residual - 1.0) > 1e-3:
                tw = max(1, int(round(rgb.width * residual)))
                th = max(1, int(round(rgb.height * residual)))
                rgb = rgb.resize((tw, th), Image.Resampling.NEAREST)
            # Save uncompressed TIFF for MATLAB compatibility
            rgb.save(out_path, format="TIFF", compression="raw")
            outs.append(f"{folder}:{rgb.size[0]}x{rgb.size[1]}")
        return f"{ndpi.name} mpp={mpp:.4f} -> " + ", ".join(outs)
    finally:
        slide.close()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=r"D:\coda_lungs\20x")
    ap.add_argument("--dst", default=r"D:\coda_lungs\auto_run")
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--overwrite", action="store_true")
    ap.add_argument("--limit", type=int, default=0, help="process first N only (0=all)")
    args = ap.parse_args()

    src = Path(args.src)
    dst = Path(args.dst)
    dst.mkdir(parents=True, exist_ok=True)
    files = sorted(src.glob("*.ndpi"))
    if args.limit > 0:
        files = files[: args.limit]
    print(f"NDPI files: {len(files)}")
    print(f"output root: {dst}")

    ok = 0
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(downsample_one, f, dst, args.overwrite): f for f in files}
        for fut in as_completed(futs):
            f = futs[fut]
            try:
                msg = fut.result()
                ok += 1
                print(f"[{ok}/{len(files)}] {msg}", flush=True)
            except Exception as e:
                print(f"FAIL {f.name}: {e}", flush=True)
    print(f"DONE {ok}/{len(files)}")


if __name__ == "__main__":
    main()
