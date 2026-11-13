% Classify all 10x slices with trained model (isolated auto workspace).
addpath('/home/bzhang/coda_lungs_auto/coda');
addpath('/home/bzhang/coda_lungs_auto/coda/segmentation base functions');
warning('off','all');

pthclassify = '/home/bzhang/coda_lungs_auto/10x/';
pthDL       = '/home/bzhang/coda_lungs_auto/annot/2026_11_13_auto/';
nm          = '2026_11_13_auto';
sxy         = 1000;
nblack      = 8;
nwhite      = 6;
cmap = [150 099 023; 023 080 150; 150 031 023; 199 196 147;
        023 080 150; 255 255 255; 242 167 227];

try
    g = gpuDevice(1); fprintf('GPU: %s\n', g.Name);
catch
end

fprintf('=== classify %d images ===\n', numel(dir([pthclassify '*.tif'])));
tic;
deeplab_classification(pthclassify, pthDL, sxy, nm, cmap, nblack, nwhite);
fprintf('done %.1f min\n', toc/60);
outpth = [pthclassify 'classification_' nm filesep];
fprintf('classified: %d\n', numel(dir([outpth '*.tif'])));
fprintf('=== SECTION 4.5 DONE ===\n');
