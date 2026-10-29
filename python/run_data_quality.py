
"""Run the complete airline data-quality pipeline."""

from pathlib import Path
import sys

from data_loader import load_datasets
from data_inspection import inspect_datasets
from data_validation import validate_datasets


def main() -> int:
    """Load datasets once, then inspect and validate them."""

    project_dir = Path(__file__).resolve().parents[1]
    data_dir = project_dir / "data"

    print("=" * 70)
    print("AIRLINE CUSTOMER EXPERIENCE ANALYTICS")
    print("DATA QUALITY PIPELINE")
    print("=" * 70)

    # Load all four Excel files once.
    try:
        datasets = load_datasets(data_dir)
    except (FileNotFoundError, ValueError) as exc:
        print(f"\nERROR loading datasets: {exc}")
        return 2

    # Reuse the same DataFrames in both stages.
    inspect_datasets(datasets)
    passed, total = validate_datasets(datasets)

    print("\n" + "=" * 70)
    print("FINAL PIPELINE SUMMARY")
    print(f"Validation checks passed: {passed}/{total}")

    if passed == total:
        print("All defined validation checks passed.")
    else:
        print(f"{total - passed} check(s) require investigation.")

    print("=" * 70)

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
