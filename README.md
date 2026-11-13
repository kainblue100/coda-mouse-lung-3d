# CODA Mouse Lung — 3D Digital Pathology

Showcase site for a CODA (Kiemen et al., *Nature Methods* 2022) reconstruction of the public mouse-lung serial histology dataset.

Inspired by [Wirtz Lab — 3D Pathology using AI](https://wirtzlab.johnshopkins.edu/research/digital-pathology/).

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

This repo is intended for `kainblue100.github.io` project Pages from `/docs` or `website/` root after assets are filled.
