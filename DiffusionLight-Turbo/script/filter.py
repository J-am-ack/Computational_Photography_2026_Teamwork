from pathlib import Path
import csv

test_dir = Path("./test1")

source_dir = Path(
    "../DiffusionLight-evaluation/output/polyhaven_turbo/stylelight/rendered"
)

output_dir = Path(
    "../DiffusionLight-evaluation/output/test1_turbo/stylelight/rendered"
)
output_dir.mkdir(parents=True, exist_ok=True)

csv_names = [
    "diffuse_scenes.csv",
    "matte_silver_scenes.csv",
    "mirror_scenes.csv",
]

test_names = {
    path.stem
    for path in test_dir.iterdir()
    if path.is_file()
}

print(f"Test scenes: {len(test_names)}")


def filter_csv(source_path):
    output_path = output_dir / f"{source_path.stem}_1.csv"

    with source_path.open(
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as file:
        reader = csv.DictReader(file, skipinitialspace=True)

        if not reader.fieldnames:
            raise ValueError(f"No header found in {source_path}")

        fieldnames = [
            name.strip()
            for name in reader.fieldnames
            if name is not None
        ]

        rows = []

        for raw_row in reader:
            row = {
                key.strip(): value.strip()
                for key, value in raw_row.items()
                if key is not None
            }

            filename = row.get("name", "")

            if Path(filename).stem in test_names:
                rows.append(row)

    metric_names = [
        name for name in fieldnames
        if name != "name"
    ]

    average_row = {"name": "AVERAGE"}

    for metric in metric_names:
        values = []

        for row in rows:
            try:
                values.append(float(row[metric]))
            except (KeyError, TypeError, ValueError):
                pass

        average_row[metric] = (
            sum(values) / len(values)
            if values else ""
        )

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

    matched_names = {
        Path(row["name"]).stem
        for row in rows
    }

    missing_names = sorted(test_names - matched_names)

    print(f"\n{source_path.name}")
    print(f"Matched: {len(rows)}/{len(test_names)}")
    print(f"Saved: {output_path}")

    for metric in metric_names:
        value = average_row[metric]

        if value != "":
            print(f"  Average {metric}: {value:.6f}")

    if missing_names:
        print(f"\nMissing scenes: {len(missing_names)}")

        for index, name in enumerate(missing_names, start=1):
            print(f"  {index}. {name}")
    else:
        print("Missing scenes: 0")


for csv_name in csv_names:
    source_path = source_dir / csv_name

    if source_path.exists():
        filter_csv(source_path)
    else:
        print(f"Not found: {source_path}")