% CODA Section 3 on isolated server workspace
addpath('/home/bzhang/coda_lungs_auto/coda');
addpath('/home/bzhang/coda_lungs_auto/coda/image registration base functions');
warning('off','all');

pth1x = '/home/bzhang/coda_lungs_auto/1x/';
fprintf('=== Section 3 ===\n1x tifs=%d\n', numel(dir([pth1x '*.tif'])));
tic; calculate_tissue_ws(pth1x, 1); fprintf('TA %.1f min\n', toc/60);
tic; calculate_image_registration(pth1x); fprintf('reg %.1f min\n', toc/60);
fprintf('D warps=%d\n', numel(dir([pth1x 'registered/elastic registration/save_warps/D/*.mat'])));
fprintf('=== SECTION 3 DONE ===\n');
