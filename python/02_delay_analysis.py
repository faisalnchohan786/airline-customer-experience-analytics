"""Research question: Are longer delays associated with lower satisfaction?

Run from the project root:
    python python/delay_analysis.py

All findings are illustrative because the project dataset is synthetic.
"""
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scipy.stats import spearmanr

from analysis_utils import (
    load_customer_journey, require_columns, p_value_text, print_decision
)

ALPHA = 0.05


def main():
    df = load_customer_journey()
    required = ["delay_minutes", "overall_satisfaction_score", "customer_id"]
    require_columns(df, required)

    work = df[required].copy()
    for col in ["delay_minutes", "overall_satisfaction_score"]:
        work[col] = pd.to_numeric(work[col], errors="coerce")

    valid = work.dropna(subset=["delay_minutes", "overall_satisfaction_score", "customer_id"])
    valid = valid[
        (valid["delay_minutes"] >= 0)
        & valid["overall_satisfaction_score"].between(1, 5)
    ].copy()

    if len(valid) < 3:
        raise ValueError("Not enough valid records for delay analysis.")

    print("=" * 60)
    print("DELAY AND SATISFACTION ANALYSIS")
    print("=" * 60)
    print(f"Valid records: {len(valid):,}; excluded: {len(df) - len(valid):,}")
    print("\n--- Delay summary ---")
    print(valid["delay_minutes"].describe().round(2))
    print("\n--- Satisfaction by delay band ---")

    # Bands are descriptive categories; keep the exact delay definitions visible.
    bins = [-np.inf, 0, 15, 60, np.inf]
    labels = ["0 minutes", "1–15 minutes", "16–60 minutes", "Over 60 minutes"]
    # Since delays are non-negative, 0 belongs to its own band.
    valid["delay_band"] = pd.cut(
        valid["delay_minutes"],
        bins=bins,
        labels=labels,
        right=True,
        include_lowest=True,
    )
    band_summary = valid.groupby("delay_band", observed=False).agg(
        journeys=("overall_satisfaction_score", "size"),
        mean_satisfaction=("overall_satisfaction_score", "mean"),
        median_satisfaction=("overall_satisfaction_score", "median"),
        complaint_rate=("overall_satisfaction_score", lambda s: np.nan),
    )
    # Replace the placeholder complaint_rate column; this script focuses on satisfaction.
    band_summary = band_summary.drop(columns=["complaint_rate"]).round(3)
    print(band_summary)

    rho, p_value = spearmanr(
        valid["delay_minutes"], valid["overall_satisfaction_score"]
    )
    print("\n--- Spearman rank correlation ---")
    print(f"Spearman rho: {rho:.4f}")
    print(f"P-value: {p_value_text(p_value)}")
    print_decision(p_value, ALPHA)
    print("Interpretation: negative rho indicates that longer delays tend to")
    print("be associated with lower satisfaction; correlation is not causation.")

    # Customer-clustered OLS: coefficient is expected score change per delay minute.
    model = smf.ols(
        "overall_satisfaction_score ~ delay_minutes", data=valid
    ).fit(cov_type="cluster", cov_kwds={"groups": valid["customer_id"]})
    ci = model.conf_int().loc["delay_minutes"]
    print("\n--- Customer-clustered linear regression ---")
    print(f"Estimated change per delay minute: {model.params['delay_minutes']:.5f}")
    print(f"Clustered standard error: {model.bse['delay_minutes']:.5f}")
    print(f"P-value: {p_value_text(model.pvalues['delay_minutes'])}")
    print(f"95% CI: [{ci.iloc[0]:.5f}, {ci.iloc[1]:.5f}]")
    print(f"R-squared: {model.rsquared:.3f}")
    print("\nCompleted. Results are illustrative because the dataset is synthetic.")


if __name__ == "__main__":
    main()
