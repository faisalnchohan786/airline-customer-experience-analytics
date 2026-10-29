
"""Load the four airline analytics datasets into pandas DataFrames."""

from dataclasses import dataclass
from pathlib import Path

import pandas as pd


@dataclass
class DatasetBundle:
    """Hold all four datasets together for reuse."""

    customer_journey: pd.DataFrame
    airport: pd.DataFrame
    flight_schedule: pd.DataFrame
    service_case: pd.DataFrame

    def as_dict(self) -> dict[str, pd.DataFrame]:
        """Return datasets as a dictionary."""
        return {
            "customer_journey": self.customer_journey,
            "airport": self.airport,
            "flight_schedule": self.flight_schedule,
            "service_case": self.service_case,
        }


def load_datasets(data_dir: Path) -> DatasetBundle:
    """Load each Excel dataset once and return the DataFrames."""

    data_dir = Path(data_dir)

    if not data_dir.is_dir():
        raise FileNotFoundError(
            f"Data folder does not exist: {data_dir}"
        )

    files = {
        "customer_journey": "customer_journey.xlsx",
        "airport": "airport.xlsx",
        "flight_schedule": "flight_schedule.xlsx",
        "service_case": "service_case.xlsx",
    }

    datasets = {}

    for dataset_name, filename in files.items():
        file_path = data_dir / filename

        if not file_path.is_file():
            raise FileNotFoundError(
                f"Required dataset not found: {file_path}"
            )

        try:
            datasets[dataset_name] = pd.read_excel(
                file_path,
                engine="openpyxl",
            )
            print(
                f"Loaded {filename}: "
                f"{len(datasets[dataset_name]):,} rows"
            )

        except Exception as exc:
            raise ValueError(
                f"Could not read {filename}: {exc}"
            ) from exc

    print("\nAll four datasets loaded successfully.")

    return DatasetBundle(
        customer_journey=datasets["customer_journey"],
        airport=datasets["airport"],
        flight_schedule=datasets["flight_schedule"],
        service_case=datasets["service_case"],
    )


if __name__ == "__main__":
    project_dir = Path(__file__).resolve().parents[1]
    data_dir = project_dir / "data"

    loaded_data = load_datasets(data_dir)

    print("\nDataset summary:")
    for name, df in loaded_data.as_dict().items():
        print(f"{name}: {df.shape[0]:,} rows, {df.shape[1]} columns")
