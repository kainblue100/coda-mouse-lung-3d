% CODA Section 4 — isolated /home/bzhang/coda_lungs_auto
% Mirrors train_image_segmentation_lung.m; uses train_deeplab_r2026b for MATLAB R2026b.
addpath('/home/bzhang/coda_lungs_auto/coda');
addpath('/home/bzhang/coda_lungs_auto/coda/segmentation base functions');
warning('off','all');

pth       = '/home/bzhang/coda_lungs_auto/annot/';
pthtest   = [pth 'testing image/'];
pthim     = [pth '10x/'];
pthtestim = [pthtest '10x/'];
pthclassify= '/home/bzhang/coda_lungs_auto/10x/';
umpix     = 1;
nm        = '2026_11_13_auto';
sxy       = 1000;
ntrain    = 15;

annotation_whitespace = [0 0 0 0 0 2 0];
add_whitespace_to     = [6 7];
nesting_order         = [7 2 5 4 3 1 6];
combine_classes       = [1 2 3 4 5 6 7];
WS = {annotation_whitespace, add_whitespace_to, nesting_order, combine_classes};

classNames = ["bronchioles" "alveoli" "vasculature","cancer","nonexpanded","background","stroma"];
cmap = [150 099 023; 023 080 150; 150 031 023; 199 196 147;
        023 080 150; 255 255 255; 242 167 227];

numclass = max(WS{3});
nblack   = numclass+1;
nwhite   = combine_classes(add_whitespace_to); nwhite = nwhite(1);
classNames = [classNames "black"];
pthDL    = [pth, nm, filesep];
nvalidate= max([round(ntrain/5) 1]);

try
    g = gpuDevice(1);
    fprintf('GPU: %s  free=%.1f GB\n', g.Name, g.AvailableMemory/1e9);
catch ME
    fprintf('GPU warn: %s\n', ME.message);
end

fprintf('=== Section 4 train nm=%s ===\n', nm);
[ctlist,numann0] = load_xml_loop(pth, pthim, WS, umpix, nm, numclass, cmap);
build_model_tiles(pthDL, classNames, nblack, sxy, numann0, ctlist, ntrain, nvalidate);
train_deeplab_r2026b(pthDL, 1:numclass+1, sxy, classNames);

% Optional test (non-fatal)
try
    load_xml_loop(pthtest, pthtestim, WS, umpix, nm, numclass, cmap);
    deeplab_classification(pthtestim, pthDL, sxy, nm, cmap, nblack, nwhite);
catch ME
    fprintf('test skipped: %s\n', ME.message);
end

fprintf('net.mat exists=%d\n', exist([pthDL 'net.mat'],'file'));
fprintf('=== SECTION 4 TRAIN DONE ===\n');
