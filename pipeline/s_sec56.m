% CODA Section 5+6 — register classified masks + build 3D tissue volume
addpath('/home/bzhang/coda_lungs_auto/coda');
addpath('/home/bzhang/coda_lungs_auto/coda/segmentation base functions');
addpath('/home/bzhang/coda_lungs_auto/coda/image registration base functions');
warning('off','all');

pth    = '/home/bzhang/coda_lungs_auto/';
pth1x  = [pth '1x/'];
nm     = '2026_11_13_auto';
pthclassified  = [pth '10x/classification_' nm '/'];
pthclassifiedE = [pthclassified 'registeredE/'];
pthvolume      = [pth 'lung_data/'];
pthdata        = [pth1x 'registered/elastic registration/save_warps'];

scale  = 10;
nwhite = 6;
sk     = 4;
cmap = [150 099 023; 023 080 150; 150 031 023; 199 196 147;
        023 080 150; 255 255 255; 242 167 227];

fprintf('=== Section 5+6 ===\n');
fprintf('classified=%d warps=%d\n', numel(dir([pthclassified '*.tif'])), numel(dir([pthdata '/D/*.mat'])));

if numel(dir([pthclassifiedE '*.tif'])) < numel(dir([pthclassified '*.tif']))
    fprintf('--- apply_image_registration ---\n'); tic;
    apply_image_registration(pthclassified, pthdata, scale, nwhite);
    fprintf('reg done %.1f min\n', toc/60);
end

imlist = dir([pthclassifiedE '*.tif']);
a = imfinfo([pthclassifiedE, imlist(1).name]); a = [a.Height a.Width];
im1 = imread([pthclassifiedE,imlist(1).name],'PixelRegion',{[1 sk a(1)],[1 sk a(2)]});
im2 = imread([pthclassifiedE,imlist(ceil(length(imlist)/2)).name],'PixelRegion',{[1 sk a(1)],[1 sk a(2)]});
im3 = imread([pthclassifiedE,imlist(end).name],'PixelRegion',{[1 sk a(1)],[1 sk a(2)]});
im1(im1==nwhite)=0; im2(im2==nwhite)=0; im3(im3==nwhite)=0;
im = cat(3,im1,im2,im3);
mask = any(im>0,3); [r,c] = find(mask);
if isempty(r)
    rr = [1 1 size(im,2) size(im,1)];
else
    x0 = max(1,min(c)-2); y0 = max(1,min(r)-2);
    x1 = min(size(im,2),max(c)+2); y1 = min(size(im,1),max(r)+2);
    rr = [x0 y0 x1-x0+1 y1-y0+1];
end
fprintf('crop rr=[%d %d %d %d] -> %dx%dx%d\n', rr, rr(4), rr(3), numel(imlist));

tic;
if exist('build_tissue_volume_headless','file')
    build_tissue_volume_headless(pthclassifiedE, pthvolume, sk, nwhite, cmap, rr);
else
    error('build_tissue_volume_headless missing — need headless crop for batch mode');
end
fprintf('volume done %.1f min\n', toc/60);

V = load([pthvolume 'volume.mat']);
fprintf('vol size %s classes %s\n', mat2str(size(V.vol)), mat2str(unique(V.vol(:))'));
names = ["bronchioles","alveoli","vasculature","cancer","nonexpanded","background","stroma"];
fid = fopen([pthvolume 'class_stats.csv'],'w');
fprintf(fid,'class,name,voxels,volume_mm3\n');
vox_mm3 = (sk*1.0)^3 / 1e9;
for c = 1:7
    v = sum(V.vol(:)==c);
    fprintf(fid,'%d,%s,%d,%.4f\n', c, names(c), v, v*vox_mm3);
    fprintf('  %d %-12s %10d  %.4f mm3\n', c, names(c), v, v*vox_mm3);
end
fclose(fid);
fprintf('=== SECTION 5+6 DONE ===\n');
