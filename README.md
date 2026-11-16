# CODA Mouse Lung — 3D Digital Pathology

Showcase site for a CODA (Kiemen et al., *Nature Methods* 2022) reconstruction of the public mouse-lung serial histology dataset.

Inspired by [Wirtz Lab — 3D Pathology using AI](https://wirtzlab.johnshopkins.edu/research/digital-pathology/).

## 150-slice interactive preview

**[Open the 150-slice interactive lung preview](https://kainblue100.github.io/coda-mouse-lung-3d/lung-slices.html)**

This experimental, self-contained preview uses Python DeepLab segmentation and Octave-compatible registration. Its seven labels include six tissue classes and background; the sample species is unconfirmed. It is not the original MATLAB CODA full pipeline, contains no real cell coordinates, and has not undergone expert validation. It is not for clinical use.

The full volume is 150 × 4515 × 4220 (Z/Y/X), with original Z/XY spacing of 10/4 µm. The web preview is downsampled to 20 µm in XY and may miss fine structures. Automatic artifact screening is off by default and can remove real tissue when enabled.

## Pipeline (independent run)

1. Downsample NDPI → 10× / 5× / 1× TIFF  
2. Tissue masks + elastic registration  
3. DeepLab semantic segmentation  
4. Warp labels → `volume.mat`  
5. Marching-cubes meshes → Blender Cycles hero + turntable  

Workspace on compute: `/home/bzhang/coda_lungs_auto`  
Local site: `website/`

## Local preview

Open `index.html` or serve:

```bash
python -m http.server 8080 -d website
```

## GitHub Pages

The site is published from the repository root on the `main` branch.
