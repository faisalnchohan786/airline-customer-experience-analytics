"""Shared helpers for Airline Customer Experience Analytics statistical scripts."""
import pandas as pd
from data_loader import load_datasets


def load_customer_journey():
    """Load customer journey data using the project's existing shared loader."""
    datasets = load_datasets("data")
    return datasets.as_dict()["customer_journey"]


def require_columns(df, columns):
    missing = [column for column in columns if column not in df.columns]
    if missing:
        raise ValueError(
            f"Required column(s) missing: {missing}. "
            f"Available columns: {list(df.columns)}"
        )


def p_value_text(p_value):
    """Avoid printing a numerically underflowed p-value as literal zero."""
    if pd.isna(p_value):
        return "not available"
    if p_value == 0:
        return "< numerical precision limit"
    if p_value < 0.001:
        return f"{p_value:.3e}"
    return f"{p_value:.6f}"


def print_decision(p_value, alpha=0.05):
    if pd.isna(p_value):
        print("Decision: p-value unavailable.")
    elif p_value < alpha:
        print(f"Decision: Reject the null hypothesis at alpha={alpha:.2f}.")
    else:
        print(f"Decision: Fail to reject the null hypothesis at alpha={alpha:.2f}.")


def clean_binary_and_score(df, required_columns):
    """Coerce relevant numeric columns and keep valid non-missing rows."""
    work = df.copy()
    for column in required_columns:
        work[column] = pd.to_numeric(work[column], errors="coerce")
    return work


def cluster_available(df):
    return "customer_id" in df.columns and df["customer_id"].notna().any()
