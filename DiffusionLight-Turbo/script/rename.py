import os
import shutil
from pathlib import Path

def rename_images(folder_path, start_number=1, digits=4):
    """
    将文件夹中的图片按 0001.png/jpg 形式重命名
    
    参数:
        folder_path: 图片文件夹路径
        start_number: 起始编号，默认 1
        digits: 编号位数，默认 4（即 0001）
    """
    folder = Path(folder_path)
    if not folder.exists():
        print(f"错误：文件夹不存在 {folder_path}")
        return
    
    # 支持的图片扩展名
    image_exts = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff', '.tif', '.svg'}
    
    # 获取所有图片文件（按文件名排序）
    images = sorted([f for f in folder.iterdir() 
                     if f.is_file() and f.suffix.lower() in image_exts])
    
    if not images:
        print("未找到图片文件")
        return
    
    print(f"找到 {len(images)} 个图片文件，开始重命名...")
    
    for i, img_path in enumerate(images, start=start_number):
        new_name = f"{i:0{digits}d}{img_path.suffix.lower()}"
        new_path = folder / new_name
        
        # 如果目标文件已存在，跳过或处理冲突
        if new_path.exists() and new_path != img_path:
            print(f"  跳过（目标已存在）: {img_path.name}")
            continue
        
        if img_path.name != new_name:
            shutil.move(str(img_path), str(new_path))
            print(f"  {img_path.name} -> {new_name}")
        else:
            print(f"  已符合命名: {img_path.name}")
    
    print("重命名完成！")

# ========== 使用示例 ==========

# 方式1：直接修改下面的路径后运行
if __name__ == "__main__":
    # 把这里改成你的文件夹路径
    target_folder = r"/root/DiffusionLight-Turbo/example_yjm"  # Windows
    # target_folder = "/home/username/Pictures/MyPhotos"   # Linux/Mac
    
    rename_images(target_folder)
    
    # 高级用法：
    # rename_images(target_folder, start_number=1, digits=4)  # 从0001开始，4位数字
    # rename_images(target_folder, start_number=5, digits=3)   # 从005开始，3位数字