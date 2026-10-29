
"""Reusable inspection functions for airline analytics datasets."""

from data_loader import DatasetBundle


def inspect_datasets(datasets: DatasetBundle) -> None:
    """Inspect datasets already loaded into memory."""

    print("\n" + "=" * 70)
    print("DATASET INSPECTION REPORT")
    print("=" * 70)

    for name, df in datasets.as_dict().items():
        print(f"\nDATASET: {name}")
        print("-" * 70)
        print(f"Rows: {len(df):,}")
        print(f"Columns: {len(df.columns):,}")
        print(f"Completely duplicated rows: {df.duplicated().sum():,}")

        print("\nCOLUMN NAMES AND DATA TYPES")
        for column, dtype in df.dtypes.items():
            print(f"  {column}: {dtype}")

        print("\nMISSING VALUES")
        missing = df.isna().sum()
        missing = missing[missing > 0]

        if missing.empty:
            print("  No missing values detected.")
        else:
            for column, count in missing.items():
                percentage = count / len(df) * 100 if len(df) else 0
                print(
                    f"  {column}: {count:,} "
                    f"({percentage:.2f}%)"
                )

    print("\nDATASET INSPECTION COMPLETE")
