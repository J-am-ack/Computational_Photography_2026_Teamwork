from pathlib import Path
from PIL import Image

input_dir = Path("./ppt")
output_dir = Path("./ppt1")
output_dir.mkdir(parents=True, exist_ok=True)

valid_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

for input_path in input_dir.iterdir():
    if not input_path.is_file():
        continue
    if input_path.suffix.lower() not in valid_extensions:
        continue

    with Image.open(input_path) as image:
        image = image.convert("RGB")
        width, height = image.size
        side = max(width, height)

        # 创建黑色正方形画布，并将原图居中放置。
        square = Image.new("RGB", (side, side), color=(0, 0, 0))
        left = (side - width) // 2
        top = (side - height) // 2
        square.paste(image, (left, top))

        result = square.resize(
            (1024, 1024),
            Image.Resampling.LANCZOS,
        )

        output_path = output_dir / f"{input_path.stem}.png"
        result.save(output_path, format="PNG")

        print(f"{input_path.name} -> {output_path.name}")

print("Done.")