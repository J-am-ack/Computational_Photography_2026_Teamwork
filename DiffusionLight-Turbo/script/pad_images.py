import os
from PIL import Image

def resize_and_pad_to_png(image_path, output_path, target_size=(1024, 1024)):
    """
    将图片等比例缩放，并用黑色填充到目标尺寸（居中），最终保存为标准的 PNG 格式
    """
    img = Image.open(image_path)
    
    # 【核心修改】如果是 RGBA（带透明度）或其它特殊模式，统一转为 RGB
    # 这样可以确保填充的 (0, 0, 0) 是纯黑色，而不是透明背景
    if img.mode in ("RGBA", "P", "LA"):
        img = img.convert("RGB")
    elif img.mode != "RGB":
        img = img.convert("RGB")
        
    img.thumbnail(target_size, Image.Resampling.LANCZOS) # 等比例缩放到长边为1024
    
    # 创建一个 1024x1024 的纯黑底板
    background = Image.new("RGB", target_size, (0, 0, 0))
    
    # 计算居中对齐的坐标
    offset = (
        (target_size[0] - img.width) // 2,
        (target_size[1] - img.height) // 2
    )
    
    # 将缩放后的图片粘贴到黑底板上
    background.paste(img, offset)
    
    # 【核心修改】指定以 PNG 格式保存
    background.save(output_path, "PNG")

def batch_process_to_png(input_dir, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    for filename in os.listdir(input_dir):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.bmp', '.tiff')):
            in_path = os.path.join(input_dir, filename)
            
            # 【核心修改】无论原图是 .jpg 还是 .webp，输出文件名一律强转为 .png 后缀
            base_name = os.path.splitext(filename)[0]
            out_path = os.path.join(output_dir, f"{base_name}.png")
            
            try:
                resize_and_pad_to_png(in_path, out_path)
                print(f"Success: {filename} -> {base_name}.png")
            except Exception as e:
                print(f"Error processing {filename}: {e}")

# 示例用法
input_folder = "./example_lxm"
output_folder = "./example_lxm/output"
batch_process_to_png(input_folder, output_folder)