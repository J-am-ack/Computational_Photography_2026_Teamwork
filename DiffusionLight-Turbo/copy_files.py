from pathlib import Path
import shutil

src_dir = Path("./output_test1/hdr")
dst_dir = Path("../DiffusionLight-evaluation/test1/turbo")

dst_dir.mkdir(parents=True, exist_ok=True)

for src_path in src_dir.glob("*.exr"):
    new_name = src_path.name.replace("_seed37", "")
    dst_path = dst_dir / new_name

    shutil.copy2(src_path, dst_path)
    print(f"{src_path.name} -> {dst_path}")

print("Done.")