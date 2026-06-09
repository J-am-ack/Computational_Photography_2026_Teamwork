# covnert exposure bracket to HDR output
import argparse 
import os 
from functools import partial
from multiprocessing import Pool
from tqdm import tqdm
import numpy as np
import skimage
import ezexr
from relighting.tonemapper import TonemapHDR

def create_argparser():    
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_dir", type=str, required=True, help='directory that contain the image') #dataset name or directory 
    parser.add_argument("--output_dir", type=str, required=True, help='directory that contain the image') #dataset name or directory 
    parser.add_argument("--endwith", type=str, default=".png" ,help='file ending to filter out unwant image')
    parser.add_argument("--ev_string", type=str, default="_ev" ,help='string that use for search ev value')
    parser.add_argument("--EV", type=str, default="auto" ,help='avalible ev value, or auto to use all EVs found per image')
    parser.add_argument("--gamma", default=2.4, help="Gamma value", type=float)
    parser.add_argument("--merge_mode", choices=["original", "weighted"], default="weighted", help="HDR luminance merge mode")
    parser.add_argument("--weight_dark_point", type=float, default=0.02, help="Raw LDR luminance where exposure weight starts")
    parser.add_argument("--weight_mid_point", type=float, default=0.5, help="Raw LDR luminance with maximum exposure weight")
    parser.add_argument("--weight_saturation_point", type=float, default=0.98, help="Raw LDR luminance where exposure weight reaches zero")
    parser.add_argument("--deghost_sigma", type=float, default=0.35, help="Log-luminance sigma for exposure consistency deghosting")
    parser.add_argument("--weight_eps", type=float, default=1e-6, help="Small value to avoid division by zero in HDR merge")
    parser.add_argument('--preview_output', dest='preview_output', action='store_true')
    parser.set_defaults(preview_output=False)
    return parser

def parse_filename(ev_string, endwith,filename):
    a = filename.split(ev_string)
    name = ev_string.join(a[:-1])
    ev = a[-1].replace(endwith, "")
    # Handle optional _seedX suffix (e.g., "-00_seed37" -> ev="-00", seed_suffix="_seed37")
    seed_suffix = ""
    if "_seed" in ev:
        ev, seed_part = ev.split("_seed", 1)
        seed_suffix = "_seed" + seed_part
    ev = int(ev) / 10
    name = name + seed_suffix
    return {
        'name': name,
        'ev': ev,
        'filename': filename
    }

def compute_exposure_weight(raw_luminance, args):
    rising = (raw_luminance - args.weight_dark_point) / max(args.weight_mid_point - args.weight_dark_point, args.weight_eps)
    falling = (args.weight_saturation_point - raw_luminance) / max(args.weight_saturation_point - args.weight_mid_point, args.weight_eps)
    return np.clip(np.minimum(rising, falling), 0.0, 1.0)

def compute_consistency_weight(luminance, reference_luminance, reference_weight, args):
    log_diff = np.log(luminance + args.weight_eps) - np.log(reference_luminance + args.weight_eps)
    consistent = np.exp(-(log_diff ** 2) / (2 * args.deghost_sigma ** 2))
    return (1.0 - reference_weight) + reference_weight * consistent

def merge_luminance_original(luminances, evs):
    out_luminance = luminances[len(evs) - 1]
    for i in range(len(evs) - 1, 0, -1):
        maxval = 1 / (2 ** evs[i-1])
        p1 = np.clip((luminances[i-1] - 0.9 * maxval) / (0.1 * maxval), 0, 1)
        p2 = out_luminance > luminances[i-1]
        mask = (p1 * p2).astype(np.float32)
        out_luminance = luminances[i-1] * (1-mask) + out_luminance * mask
    return out_luminance

def merge_luminance_weighted(luminances, raw_luminances, args):
    reference_luminance = luminances[0]
    reference_weight = compute_exposure_weight(raw_luminances[0], args)

    weighted_sum = np.zeros_like(reference_luminance, dtype=np.float64)
    weight_sum = np.zeros_like(reference_luminance, dtype=np.float64)
    for luminance, raw_luminance in zip(luminances, raw_luminances):
        exposure_weight = compute_exposure_weight(raw_luminance, args)
        consistency_weight = compute_consistency_weight(luminance, reference_luminance, reference_weight, args)
        weight = exposure_weight * consistency_weight + args.weight_eps
        weighted_sum += weight * luminance
        weight_sum += weight

    return (weighted_sum / np.maximum(weight_sum, args.weight_eps)).astype(np.float32)

def process_image(args, info):
    
    #output directory
    hdrdir = args.output_dir
    os.makedirs(hdrdir, exist_ok=True)
    
    scaler = np.array([0.212671, 0.715160, 0.072169])
    name = info['name']
    # ev value for each file
    evs = [e for e in sorted(info['ev'], reverse = True)]

    # filename
    files = [info['ev'][e] for e in evs]
    
    # inital first image
    image0 = skimage.io.imread(os.path.join(args.input_dir, files[0]))[...,:3]
    image0 = skimage.img_as_float(image0)
    image0_linear = np.power(image0, args.gamma)

    # read luminace for every image
    raw_luminances = []
    luminances = []
    for i in range(len(evs)):
        # load image
        path = os.path.join(args.input_dir, files[i])
        image = skimage.io.imread(path)[...,:3]
        image = skimage.img_as_float(image)
        
        # apply gama correction
        linear_img = np.power(image, args.gamma)

        # compute raw LDR luminance before exposure compensation for weighting
        raw_lumi = linear_img @ scaler
        raw_luminances.append(raw_lumi)
        
        # convert the brighness
        linear_img *= 1 / (2 ** evs[i])
        
        # compute luminace
        lumi = linear_img @ scaler
        luminances.append(lumi)
        
    if args.merge_mode == "original":
        out_luminace = merge_luminance_original(luminances, evs)
    else:
        out_luminace = merge_luminance_weighted(luminances, raw_luminances, args)
        
    hdr_rgb = image0_linear * (out_luminace / (luminances[0] + 1e-10))[:, :, np.newaxis]
    
    # tone map for visualization    
    hdr2ldr = TonemapHDR(gamma=args.gamma, percentile=99, max_mapping=0.9)
    
    
    ldr_rgb, _, _ = hdr2ldr(hdr_rgb)
    
    ezexr.imwrite(os.path.join(hdrdir, name+".exr"), hdr_rgb.astype(np.float32))
    if args.preview_output:
        preview_dir = os.path.join(args.output_dir, "preview")
        os.makedirs(preview_dir, exist_ok=True)
        bracket = []
        for s in 2 ** np.linspace(0, evs[-1], 10): #evs[-1] is -5
            lumi = np.clip((s * hdr_rgb) ** (1/args.gamma), 0, 1)
            bracket.append(lumi)
        bracket = np.concatenate(bracket, axis=1)
        skimage.io.imsave(os.path.join(preview_dir, name+".png"), skimage.img_as_ubyte(bracket))
    return None

def main():
    # load arguments
    args = create_argparser().parse_args()
    
    files = sorted(os.listdir(args.input_dir))
    
    #filter file out with file ending
    files = [f for f in files if f.endswith(args.endwith)]
    evs = None if args.EV.strip().lower() == "auto" else [float(e.strip()) for e in args.EV.split(",")]
    
    # parse into useful data
    files = [parse_filename(args.ev_string, args.endwith, f) for f in files]
    
    # filter out unused ev unless automatic per-image EV discovery is enabled
    if evs is not None:
        files = [f for f in files if f['ev'] in evs]
  
    info = {}
    for f in files:
        if not f['name'] in info:
            info[f['name']] = {}
        info[f['name']][f['ev']] = f['filename']

    infolist = []
    for k in info:
        if evs is not None and len(info[k]) != len(evs):
            print("WARNING: missing ev in ", k)
            continue
        if evs is None and len(info[k]) < 2:
            print("WARNING: need at least two ev values in ", k)
            continue
        # convert to list data
        infolist.append({'name': k, 'ev': info[k]})
    
    fn = partial(process_image, args)
    with Pool(8) as p:
        r = list(tqdm(p.imap(fn, infolist), total=len(infolist)))

     
    
if __name__ == "__main__":
    main()
