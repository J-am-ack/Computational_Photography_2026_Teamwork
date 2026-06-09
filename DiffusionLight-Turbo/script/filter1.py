from pathlib import Path
import csv

# test1 中抽取出的输入图片
test_dir = Path("./test1")

# 500 张图片对应的完整 editableindoor 评测结果
source_path = Path(
    "../DiffusionLight-evaluation/output/"
    "polyhaven_turbo/editableindoor/scenes.csv"
)

# test1 对应的输出位置
output_dir = Path(
    "../DiffusionLight-evaluation/output/"
    "test1_turbo/editableindoor"
)
output_dir.mkdir(parents=True, exist_ok=True)

output_path = output_dir / "scenes_1.csv"


# 获取 test1 中所有场景名称，不包含扩展名
test_names = {
    path.stem
    for path in test_dir.iterdir()
    if path.is_file()
}

print(f"Test1 scenes: {len(test_names)}")


if not source_path.exists():
    raise FileNotFoundError(f"Not found: {source_path}")


with source_path.open(
    "r",
    encoding="utf-8-sig",
    newline=""
) as file:
    reader = csv.DictReader(file, skipinitialspace=True)

    if not reader.fieldnames:
        raise ValueError("metric.csv does not contain a valid header.")

    # 清理列名两侧可能存在的空格
    fieldnames = [
        name.strip()
        for name in reader.fieldnames
        if name is not None
    ]

    # 自动查找文件名列，兼容 name、Name 等写法
    name_field = next(
        (
            name for name in fieldnames
            if name.lower().strip('", ') == "name"
        ),
        None
    )

    if name_field is None:
        raise ValueError(
            f"Cannot find the name column. Columns: {fieldnames}"
        )

    rows = []

    for raw_row in reader:
        row = {
            key.strip(): value.strip()
            for key, value in raw_row.items()
            if key is not None
        }

        filename = row.get(name_field, "")
        scene_name = Path(filename).stem

        if scene_name in test_names:
            rows.append(row)


# 计算除名称列外的各项平均值
metric_names = [
    name for name in fieldnames
    if name != name_field
]

average_row = {
    field: ""
    for field in fieldnames
}
average_row[name_field] = "AVERAGE"

for metric in metric_names:
    values = []

    for row in rows:
        try:
            values.append(float(row[metric]))
        except (KeyError, TypeError, ValueError):
            pass

    if values:
        average_row[metric] = sum(values) / len(values)


# 写入筛选后的结果
with output_path.open(
    "w",
    encoding="utf-8",
    newline=""
) as file:
    writer = csv.DictWriter(
        file,
        fieldnames=fieldnames
    )

    writer.writeheader()

    for row in rows:
        writer.writerow({
            field: row.get(field, "")
            for field in fieldnames
        })

    writer.writerow(average_row)


# 检查是否存在未匹配场景
matched_names = {
    Path(row[name_field]).stem
    for row in rows
}

missing_names = sorted(test_names - matched_names)

print(f"Matched: {len(rows)}/{len(test_names)}")
print(f"Saved: {output_path}")

print("\nAverage metrics:")
for metric in metric_names:
    value = average_row[metric]

    if isinstance(value, (int, float)):
        print(f"  {metric}: {value:.6f}")

if missing_names:
    print(f"\nMissing scenes: {len(missing_names)}")

    for name in missing_names:
        print(f"  {name}")