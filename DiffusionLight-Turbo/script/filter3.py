from pathlib import Path
import argparse
import csv
import math


def parse_args():
    parser = argparse.ArgumentParser(
        description="Filter directional evaluation CSV by test subset."
    )
    parser.add_argument(
        "--test_dir",
        type=Path,
        default=Path("./test1"),
        help="Directory containing test1 input images.",
    )
    parser.add_argument(
        "--source_csv",
        type=Path,
        default=Path(
            "../DiffusionLight-evaluation/output/"
            "polyhaven_turbo/envmapnet/directional_score.csv"
        ),
        help="CSV containing evaluation results for the full dataset.",
    )
    parser.add_argument(
        "--output_csv",
        type=Path,
        default=Path(
            "../DiffusionLight-evaluation/output/"
            "test1_turbo/envmapnet/directional_score_1.csv"
        ),
        help="Output CSV for the filtered test subset.",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    if not args.test_dir.exists():
        raise FileNotFoundError(f"Test directory not found: {args.test_dir}")

    if not args.source_csv.exists():
        raise FileNotFoundError(f"Source CSV not found: {args.source_csv}")

    args.output_csv.parent.mkdir(parents=True, exist_ok=True)

    test_names = {
        path.stem
        for path in args.test_dir.iterdir()
        if path.is_file()
    }

    print(f"Test scenes: {len(test_names)}")

    with args.source_csv.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        reader = csv.DictReader(file, skipinitialspace=True)

        if not reader.fieldnames:
            raise ValueError("The source CSV has no valid header.")

        fieldnames = [
            field.strip()
            for field in reader.fieldnames
            if field is not None
        ]

        if "filename" not in fieldnames or "score" not in fieldnames:
            raise ValueError(
                "CSV must contain 'filename' and 'score' columns. "
                f"Found: {fieldnames}"
            )

        selected_rows = []

        for raw_row in reader:
            row = {
                key.strip(): value.strip()
                for key, value in raw_row.items()
                if key is not None
            }

            scene_name = Path(row.get("filename", "")).stem

            if scene_name in test_names:
                selected_rows.append(row)

    valid_scores = []

    for row in selected_rows:
        try:
            score = float(row["score"])

            if math.isfinite(score):
                valid_scores.append(score)
        except (KeyError, TypeError, ValueError):
            pass

    average_score = (
        sum(valid_scores) / len(valid_scores)
        if valid_scores else ""
    )

    with args.output_csv.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=["filename", "score"],
        )

        writer.writeheader()

        for row in selected_rows:
            writer.writerow({
                "filename": row.get("filename", ""),
                "score": row.get("score", ""),
            })

        writer.writerow({
            "filename": "AVERAGE",
            "score": average_score,
        })

    matched_names = {
        Path(row["filename"]).stem
        for row in selected_rows
    }
    missing_names = sorted(test_names - matched_names)

    print(f"Matched: {len(selected_rows)}/{len(test_names)}")
    print(f"Valid scores: {len(valid_scores)}")
    print(f"Saved: {args.output_csv}")

    if average_score != "":
        print(f"Average score: {average_score:.6f}")

    if missing_names:
        print(f"\nMissing scenes: {len(missing_names)}")

        for index, name in enumerate(missing_names, start=1):
            print(f"  {index}. {name}")
    else:
        print("Missing scenes: 0")


if __name__ == "__main__":
    main()