
"""Export validated Excel datasets to Parquet for Amazon Athena."""

from pathlib import Path

import pandas as pd

from data_loader import load_datasets


def main() -> None:
    project_dir = Path(__file__).resolve().parents[1]
    data_dir = project_dir / "data"
    output_dir = data_dir / "athena_parquet"

    # Load the four original datasets.
    datasets = load_datasets(data_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("\n" + "=" * 65)
    print("EXPORTING DATASETS TO PARQUET")
    print("=" * 65)

    for name, original_df in datasets.as_dict().items():
        output_file = output_dir / f"{name}.parquet"

        # Export locally; no AWS resources are used here.
        original_df.to_parquet(
            output_file,
            index=False,
            engine="pyarrow",
            compression="snappy",
        )

        # Read the file back to verify the exported data.
        exported_df = pd.read_parquet(
            output_file,
            engine="pyarrow",
        )

        if list(exported_df.columns) != list(original_df.columns):
            raise ValueError(f"Column mismatch in {output_file.name}")

        if exported_df.shape != original_df.shape:
            raise ValueError(
                f"Dimension mismatch in {output_file.name}: "
                f"original={original_df.shape}, "
                f"exported={exported_df.shape}"
            )

        try:
            pd.testing.assert_frame_equal(
                original_df.reset_index(drop=True),
                exported_df.reset_index(drop=True),
                check_dtype=False,
            )
        except AssertionError as exc:
            raise ValueError(
                f"Data comparison failed for {output_file.name}"
            ) from exc

        size_kb = output_file.stat().st_size / 1024

        print(
            f"[PASS] {output_file.name} | "
            f"Rows: {len(exported_df):,} | "
            f"Columns: {len(exported_df.columns)} | "
            f"Size: {size_kb:,.1f} KB"
        )

    print(f"\nOutput folder: {output_dir}")
    print("All four Parquet files passed verification.")


if __name__ == "__main__":
    main()
