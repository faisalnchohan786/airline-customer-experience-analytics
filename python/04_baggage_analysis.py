"""Research question: Are baggage issues associated with satisfaction and complaints?

Run from the project root:
    python python/baggage_analysis.py

All findings are illustrative because the project dataset is synthetic.
"""
import pandas as pd
import statsmodels.formula.api as smf
from scipy.stats import chi2_contingency, ttest_ind

from analysis_utils import (
    load_customer_journey, require_columns, p_value_text, print_decision
)

ALPHA = 0.05


def main():
    df = load_customer_journey()
    required = [
        "baggage_issue_flag", "overall_satisfaction_score",
        "complaint_flag", "customer_id"
    ]
    require_columns(df, required)

    work = df[required].copy()
    for col in required[:-1]:
        work[col] = pd.to_numeric(work[col], errors="coerce")

    valid = work.dropna(subset=required)
    valid = valid[
        valid["baggage_issue_flag"].isin([0, 1])
        & valid["complaint_flag"].isin([0, 1])
        & valid["overall_satisfaction_score"].between(1, 5)
    ].copy()
    if valid.empty or valid["baggage_issue_flag"].nunique() < 2:
        raise ValueError("Valid records from both baggage groups are required.")

    print("=" * 60)
    print("BAGGAGE ISSUE ANALYSIS")
    print("=" * 60)
    print(f"Valid records: {len(valid):,}; excluded: {len(df) - len(valid):,}")

    print("\n--- Satisfaction summary by baggage issue ---")
    summary = valid.groupby("baggage_issue_flag")["overall_satisfaction_score"].agg(
        ["count", "mean", "std", "median"]
    ).rename(index={0: "No baggage issue", 1: "Baggage issue"}).round(3)
    print(summary)

    no_issue = valid.loc[valid["baggage_issue_flag"] == 0, "overall_satisfaction_score"]
    issue = valid.loc[valid["baggage_issue_flag"] == 1, "overall_satisfaction_score"]
    test = ttest_ind(issue, no_issue, equal_var=False, alternative="two-sided")
    print("\n--- Welch's t-test: satisfaction ---")
    print(f"Mean difference (issue - no issue): {issue.mean() - no_issue.mean():.3f}")
    print(f"T-statistic: {test.statistic:.4f}")
    print(f"P-value: {p_value_text(test.pvalue)}")
    print_decision(test.pvalue, ALPHA)

    model = smf.ols(
        "overall_satisfaction_score ~ baggage_issue_flag", data=valid
    ).fit(cov_type="cluster", cov_kwds={"groups": valid["customer_id"]})
    ci = model.conf_int().loc["baggage_issue_flag"]
    print("\n--- Customer-clustered satisfaction regression ---")
    print(f"Estimated difference: {model.params['baggage_issue_flag']:.3f}")
    print(f"Clustered SE: {model.bse['baggage_issue_flag']:.4f}")
    print(f"P-value: {p_value_text(model.pvalues['baggage_issue_flag'])}")
    print(f"95% CI: [{ci.iloc[0]:.3f}, {ci.iloc[1]:.3f}]")

    complaint_table = pd.crosstab(
        valid["baggage_issue_flag"], valid["complaint_flag"]
    ).reindex(index=[0, 1], columns=[0, 1], fill_value=0)
    chi2, complaint_p, dof, _ = chi2_contingency(complaint_table, correction=False)
    complaint_rates = valid.groupby("baggage_issue_flag")["complaint_flag"].mean() * 100

    print("\n--- Complaint rates by baggage issue ---")
    print(f"No baggage issue: {complaint_rates.loc[0]:.2f}%")
    print(f"Baggage issue: {complaint_rates.loc[1]:.2f}%")
    print(f"Difference: {complaint_rates.loc[1] - complaint_rates.loc[0]:.2f} percentage points")
    print("\n--- Chi-square test: baggage issue and complaint ---")
    print(f"Chi-square statistic: {chi2:.4f}; df: {dof}")
    print(f"P-value: {p_value_text(complaint_p)}")
    print_decision(complaint_p, ALPHA)
    print("\nCaution: chi-square is unadjusted for repeated customers; findings are synthetic.")


if __name__ == "__main__":
    main()
