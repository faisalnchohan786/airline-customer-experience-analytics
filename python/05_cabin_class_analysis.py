"""Research question: Does satisfaction differ by cabin class?

Run from the project root:
    python python/cabin_class_analysis.py

Uses an omnibus customer-clustered regression test and group summaries.
All findings are illustrative because the dataset is synthetic.
"""
import pandas as pd
import statsmodels.formula.api as smf

from analysis_utils import load_customer_journey, require_columns, p_value_text


def main():
    df = load_customer_journey()
    required = ["cabin_class", "overall_satisfaction_score", "customer_id"]
    require_columns(df, required)

    work = df[required].copy()
    work["overall_satisfaction_score"] = pd.to_numeric(
        work["overall_satisfaction_score"], errors="coerce"
    )
    work["cabin_class"] = work["cabin_class"].astype("string").str.strip()
    valid = work.dropna(subset=required)
    valid = valid[
        valid["cabin_class"].ne("")
        & valid["overall_satisfaction_score"].between(1, 5)
    ].copy()

    if valid["cabin_class"].nunique() < 2:
        raise ValueError("At least two cabin classes are required.")

    print("=" * 60)
    print("CABIN CLASS AND SATISFACTION ANALYSIS")
    print("=" * 60)
    print(f"Valid records: {len(valid):,}; excluded: {len(df) - len(valid):,}")
    print("\n--- Satisfaction by cabin class ---")
    summary = valid.groupby("cabin_class")["overall_satisfaction_score"].agg(
        ["count", "mean", "std", "median"]
    ).sort_values("mean", ascending=False).round(3)
    print(summary)

    # Treatment-coded OLS with customer-clustered covariance.
    model = smf.ols(
        "overall_satisfaction_score ~ C(cabin_class)", data=valid
    ).fit(cov_type="cluster", cov_kwds={"groups": valid["customer_id"]})

    # Robust joint Wald test of all cabin-class terms, excluding intercept.
    term_names = [name for name in model.params.index if name.startswith("C(cabin_class)")]
    if not term_names:
        raise ValueError("Could not construct cabin-class comparison terms.")
    restriction = " = 0, ".join(term_names) + " = 0"
    test = model.wald_test(restriction, scalar=True)

    print("\n--- Customer-clustered omnibus regression test ---")
    print(f"Wald statistic: {float(test.statistic):.4f}")
    print(f"Degrees of freedom: {len(term_names)}")
    print(f"P-value: {p_value_text(float(test.pvalue))}")
    if test.pvalue < 0.05:
        print("Decision: Evidence that at least one cabin-class mean differs.")
    else:
        print("Decision: Insufficient evidence of a difference across cabin classes.")
    print("This is an overall test; it does not identify which pairs differ.")
    print("If needed later, use multiplicity-adjusted pairwise comparisons.")
    print("\nCaution: observational association only; dataset is synthetic.")


if __name__ == "__main__":
    main()
