"""Research question: Are complaints more common on disrupted journeys?

Run from the project root:
    python python/complaint_analysis.py

All findings are illustrative because the project dataset is synthetic.
"""
import pandas as pd
from scipy.stats import chi2_contingency
import statsmodels.formula.api as smf

from analysis_utils import (
    load_customer_journey, require_columns, p_value_text, print_decision
)

ALPHA = 0.05


def main():
    df = load_customer_journey()
    required = ["disruption_flag", "complaint_flag", "customer_id"]
    require_columns(df, required)

    work = df[required].copy()
    for col in ["disruption_flag", "complaint_flag"]:
        work[col] = pd.to_numeric(work[col], errors="coerce")

    valid = work.dropna(subset=required)
    valid = valid[
        valid["disruption_flag"].isin([0, 1])
        & valid["complaint_flag"].isin([0, 1])
    ].copy()

    if valid.empty or valid["disruption_flag"].nunique() < 2:
        raise ValueError("Valid records from both disruption groups are required.")

    print("=" * 60)
    print("COMPLAINT AND DISRUPTION ANALYSIS")
    print("=" * 60)
    print(f"Valid records: {len(valid):,}; excluded: {len(df) - len(valid):,}")

    table = pd.crosstab(
        valid["disruption_flag"].map({0: "Not disrupted", 1: "Disrupted"}),
        valid["complaint_flag"].map({0: "No complaint", 1: "Complaint"}),
    ).reindex(index=["Not disrupted", "Disrupted"],
              columns=["No complaint", "Complaint"], fill_value=0)
    print("\n--- Complaint counts ---")
    print(table)

    summary = valid.groupby("disruption_flag")["complaint_flag"].agg(
        journeys="size", complaints="sum", complaint_rate="mean"
    )
    summary["complaint_rate_pct"] = summary["complaint_rate"] * 100
    print("\n--- Complaint rate by disruption status ---")
    print(summary.drop(columns="complaint_rate").rename(
        index={0: "Not disrupted", 1: "Disrupted"}
    ).round(3))

    chi2, p_value, dof, expected = chi2_contingency(table, correction=False)
    print("\n--- Chi-square test of independence ---")
    print(f"Chi-square statistic: {chi2:.4f}")
    print(f"Degrees of freedom: {dof}")
    print(f"P-value: {p_value_text(p_value)}")
    print_decision(p_value, ALPHA)
    print("This standard chi-square test does not account for repeated journeys")
    print("within customers; use it as an initial unadjusted comparison.")

    # Cluster-robust linear probability model gives a percentage-point difference
    # in complaint probability; robust SEs account for repeated customers.
    model = smf.ols("complaint_flag ~ disruption_flag", data=valid).fit(
        cov_type="cluster", cov_kwds={"groups": valid["customer_id"]}
    )
    ci = model.conf_int().loc["disruption_flag"]
    diff_pp = 100 * model.params["disruption_flag"]
    print("\n--- Customer-clustered complaint-rate comparison ---")
    print(f"Estimated difference: {diff_pp:.2f} percentage points")
    print(f"Clustered standard error: {100 * model.bse['disruption_flag']:.2f} percentage points")
    print(f"P-value: {p_value_text(model.pvalues['disruption_flag'])}")
    print(f"95% CI: [{100 * ci.iloc[0]:.2f}, {100 * ci.iloc[1]:.2f}] percentage points")
    print("\nNote: association does not establish causation; data are synthetic.")


if __name__ == "__main__":
    main()
