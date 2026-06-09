from pathlib import Path
import random
import shutil

random.seed(42)

src_img_dir = Path("./polyhaven")
src_gt_dir = Path("../DiffusionLight-evaluation/polyhaven/GT")

dst_img_dir = Path("./test1")
dst_gt_dir = Path("../DiffusionLight-evaluation/test1/GT")

dst_img_dir.mkdir(parents=True, exist_ok=True)
dst_gt_dir.mkdir(parents=True, exist_ok=True)

img_exts = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
gt_ext = ".exr"

images = sorted([p for p in src_img_dir.iterdir() if p.suffix.lower() in img_exts])

pairs = []
for img_path in images:
    gt_path = src_gt_dir / f"{img_path.stem}{gt_ext}"
    if gt_path.exists():
        pairs.append((img_path, gt_path))
    else:
        print(f"Missing GT: {gt_path}")

if len(pairs) < 200:
    raise RuntimeError(f"Only found {len(pairs)} valid image-GT pairs, need 200.")

sampled = random.sample(pairs, 200)

for img_path, gt_path in sampled:
    shutil.copy2(img_path, dst_img_dir / img_path.name)
    shutil.copy2(gt_path, dst_gt_dir / gt_path.name)

print(f"Copied {len(sampled)} image-GT pairs.")
print(f"Images -> {dst_img_dir}")
print(f"GT HDR -> {dst_gt_dir}")