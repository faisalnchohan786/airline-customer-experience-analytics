"""
Airline Customer Experience Analytics
Research question: Is disruption associated with overall satisfaction?

IMPORTANT:
- The dataset is synthetic; results are illustrative.
- Welch's t-test and the standard Mann–Whitney U test treat journey rows as
  independent and do not adjust for repeated journeys from the same customer.
- Customer-clustered regression is the primary inferential result for the
  mean difference because it adjusts standard errors for customer-level
  clustering. This simple regression does not adjust for confounders.
"""

import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu, t, ttest_ind
import statsmodels.formula.api as smf

from analysis_utils import (
    load_customer_journey,
    require_columns,
    p_value_text,
    print_decision,
)

ALPHA = 0.05
SATISFACTION_MIN = 1
SATISFACTION_MAX = 5


def main():
    # --------------------------------------------------
    # 1. Load data
    # --------------------------------------------------
    df = load_customer_journey()

    print("=" * 60)
    print("AIRLINE CUSTOMER EXPERIENCE: DISRUPTION ANALYSIS")
    print("=" * 60)
    print(f"\nDataset shape: {df.shape[0]:,} rows, {df.shape[1]} columns")

    # --------------------------------------------------
    # 2. Validate required columns
    # --------------------------------------------------
    required_columns = ["disruption_flag", "overall_satisfaction_score"]
    require_columns(df, required_columns)

    has_customer_id = (
        "customer_id" in df.columns
        and df["customer_id"].notna().any()
    )

    # Keep the original row index so customer IDs stay aligned after filtering.
    analysis_columns = required_columns.copy()
    if "customer_id" in df.columns:
        analysis_columns.append("customer_id")

    analysis_df = df[analysis_columns].copy()

    for column in required_columns:
        analysis_df[column] = pd.to_numeric(
            analysis_df[column], errors="coerce"
        )

    # --------------------------------------------------
    # 3. Data quality checks and valid analysis sample
    # --------------------------------------------------
    print("\n--- Data quality checks ---")
    print("\nMissing values:")
    print(analysis_df[required_columns].isna().sum())

    invalid_flags = (
        analysis_df["disruption_flag"].notna()
        & ~analysis_df["disruption_flag"].isin([0, 1])
    )
    print(f"\nInvalid disruption flags: {int(invalid_flags.sum()):,}")

    invalid_scores = (
        analysis_df["overall_satisfaction_score"].notna()
        & ~analysis_df["overall_satisfaction_score"].between(
            SATISFACTION_MIN, SATISFACTION_MAX
        )
    )
    print(
        "Satisfaction scores outside the expected 1–5 range:",
        f"{int(invalid_scores.sum()):,}",
    )

    valid_mask = (
        analysis_df["disruption_flag"].isin([0, 1])
        & analysis_df["overall_satisfaction_score"].between(
            SATISFACTION_MIN, SATISFACTION_MAX
        )
    )
    if "customer_id" in analysis_df.columns:
        # The main comparison can be performed without customer IDs, but
        # clustered regression requires non-missing customer IDs.
        valid_for_comparison = analysis_df.loc[valid_mask].copy()
        valid_for_clustered = valid_for_comparison.dropna(subset=["customer_id"])
    else:
        valid_for_comparison = analysis_df.loc[valid_mask].copy()
        valid_for_clustered = None

    valid_df = valid_for_comparison
    print(f"\nValid records for comparison: {len(valid_df):,}")
    print(f"Records excluded from comparison: {len(analysis_df) - len(valid_df):,}")

    if valid_df.empty:
        raise ValueError("No valid records remain for analysis.")

    group_counts = valid_df["disruption_flag"].value_counts()
    if 0 not in group_counts.index or 1 not in group_counts.index:
        raise ValueError(
            "Both disruption groups (0 and 1) must contain valid records."
        )

    # --------------------------------------------------
    # 4. Inspect customer-level repetition
    # --------------------------------------------------
    print("\n--- Customer independence check ---")
    if "customer_id" in df.columns:
        journeys_per_customer = df["customer_id"].value_counts(dropna=True)
        print(f"Unique customers: {df['customer_id'].nunique(dropna=True):,}")
        print(f"Journey records: {len(df):,}")
        print(
            "Customers with multiple journeys:",
            f"{int((journeys_per_customer > 1).sum()):,}",
        )

        if not journeys_per_customer.empty:
            print("\n--- Journeys per customer ---")
            print(f"Maximum journeys for one customer: {journeys_per_customer.max()}")
            print(f"Median journeys per customer: {journeys_per_customer.median():.1f}")
            print("\nDistribution of journeys per customer:")
            print(
                journeys_per_customer.value_counts()
                .sort_index()
                .rename_axis("journeys_per_customer")
                .to_frame("customer_count")
            )

        status_df = valid_df.dropna(subset=["customer_id"]) if "customer_id" in valid_df.columns else None
        if status_df is not None and not status_df.empty:
            customer_status_counts = (
                status_df.groupby("customer_id")["disruption_flag"].nunique()
            )
            print("\n--- Disruption status within valid customer records ---")
            print(
                "Customers with both disrupted and non-disrupted journeys:",
                f"{int((customer_status_counts > 1).sum()):,}",
            )
            print(
                "Customers with only one disruption status:",
                f"{int((customer_status_counts == 1).sum()):,}",
            )
    else:
        print("customer_id column unavailable; customer-clustered regression cannot run.")

    # --------------------------------------------------
    # 5. Group sizes and descriptive statistics
    # --------------------------------------------------
    group_labels = {0: "Not disrupted", 1: "Disrupted"}

    print("\n--- Group sizes ---")
    print(
        valid_df["disruption_flag"]
        .map(group_labels)
        .value_counts()
        .reindex(["Not disrupted", "Disrupted"], fill_value=0)
    )

    print("\n--- Satisfaction summary by disruption status ---")
    summary = (
        valid_df.groupby("disruption_flag")["overall_satisfaction_score"]
        .agg(["count", "mean", "std", "median", "min", "max"])
        .rename(index=group_labels)
        .round(3)
    )
    print(summary)

    not_disrupted = valid_df.loc[
        valid_df["disruption_flag"] == 0, "overall_satisfaction_score"
    ]
    disrupted = valid_df.loc[
        valid_df["disruption_flag"] == 1, "overall_satisfaction_score"
    ]

    # --------------------------------------------------
    # 6. Mean difference and score distribution
    # --------------------------------------------------
    mean_difference = disrupted.mean() - not_disrupted.mean()

    print("\n--- Observed difference ---")
    print(f"Mean satisfaction, not disrupted: {not_disrupted.mean():.3f}")
    print(f"Mean satisfaction, disrupted:     {disrupted.mean():.3f}")
    print(f"Mean difference (disrupted - not disrupted): {mean_difference:.3f}")

    print("\n--- Satisfaction score distribution by group ---")
    distribution = pd.crosstab(
        valid_df["overall_satisfaction_score"],
        valid_df["disruption_flag"].map(group_labels),
    ).reindex(columns=["Disrupted", "Not disrupted"], fill_value=0)
    print(distribution)

    # --------------------------------------------------
    # 7. Welch's independent two-sample t-test
    # --------------------------------------------------
    welch_result = ttest_ind(
        disrupted,
        not_disrupted,
        equal_var=False,
        alternative="two-sided",
    )

    print("\n--- Welch's two-sample t-test (unadjusted) ---")
    print(f"T-statistic: {welch_result.statistic:.4f}")
    print(f"P-value: {p_value_text(welch_result.pvalue)}")
    print_decision(welch_result.pvalue, ALPHA)
    print("Note: this standard test does not adjust for repeated customers.")

    # --------------------------------------------------
    # 8. Welch 95% confidence interval and Cohen's d
    # --------------------------------------------------
    var_disrupted = disrupted.var(ddof=1)
    var_not_disrupted = not_disrupted.var(ddof=1)
    n_disrupted = len(disrupted)
    n_not_disrupted = len(not_disrupted)

    se_welch = np.sqrt(
        var_disrupted / n_disrupted + var_not_disrupted / n_not_disrupted
    )
    a = var_disrupted / n_disrupted
    b = var_not_disrupted / n_not_disrupted
    degrees_freedom = (a + b) ** 2 / (
        a**2 / (n_disrupted - 1) + b**2 / (n_not_disrupted - 1)
    )
    critical_value = t.ppf(0.975, degrees_freedom)
    ci_lower = mean_difference - critical_value * se_welch
    ci_upper = mean_difference + critical_value * se_welch

    print("\n--- 95% confidence interval for mean difference (Welch; unadjusted) ---")
    print(f"Mean difference: {mean_difference:.3f}")
    print(f"Lower bound: {ci_lower:.3f}")
    print(f"Upper bound: {ci_upper:.3f}")

    pooled_sd = np.sqrt(
        (
            (n_disrupted - 1) * var_disrupted
            + (n_not_disrupted - 1) * var_not_disrupted
        )
        / (n_disrupted + n_not_disrupted - 2)
    )
    cohens_d = mean_difference / pooled_sd if pooled_sd > 0 else np.nan

    print("\n--- Effect size ---")
    print(f"Cohen's d: {cohens_d:.3f}")

    # --------------------------------------------------
    # 9. Customer-clustered regression (primary inference for mean difference)
    # --------------------------------------------------
    if (
        "customer_id" in valid_df.columns
        and valid_df["customer_id"].notna().sum() >= 2
        and valid_df.loc[valid_df["customer_id"].notna(), "customer_id"].nunique() >= 2
    ):
        model_df = valid_df.dropna(subset=["customer_id"]).copy()
        model = smf.ols(
            "overall_satisfaction_score ~ disruption_flag",
            data=model_df,
        ).fit(
            cov_type="cluster",
            cov_kwds={"groups": model_df["customer_id"]},
        )

        coefficient = model.params["disruption_flag"]
        clustered_se = model.bse["disruption_flag"]
        clustered_p = model.pvalues["disruption_flag"]
        clustered_ci = model.conf_int().loc["disruption_flag"]

        print("\n--- Customer-clustered regression ---")
        print(model.summary())
        print(f"\nEstimated satisfaction difference: {coefficient:.3f}")
        print(f"Clustered standard error: {clustered_se:.4f}")
        print(f"Clustered p-value: {p_value_text(clustered_p)}")
        print(
            "Clustered 95% confidence interval: "
            f"[{clustered_ci.iloc[0]:.3f}, {clustered_ci.iloc[1]:.3f}]"
        )
    else:
        print(
            "\n--- Customer-clustered regression skipped ---\n"
            "At least two non-missing customer IDs are required."
        )

    # --------------------------------------------------
    # 10. Mann–Whitney U test (supplementary, unadjusted)
    # --------------------------------------------------
    mw_result = mannwhitneyu(
        disrupted,
        not_disrupted,
        alternative="two-sided",
        method="asymptotic",
    )

    print("\n--- Mann–Whitney U test (supplementary, unadjusted) ---")
    print(f"U-statistic: {mw_result.statistic:.2f}")
    print(f"P-value: {p_value_text(mw_result.pvalue)}")
    print_decision(mw_result.pvalue, ALPHA)
    print(f"Disrupted journeys: {len(disrupted):,}")
    print(f"Non-disrupted journeys: {len(not_disrupted):,}")
    print(f"Disrupted median satisfaction: {disrupted.median():.2f}")
    print(f"Non-disrupted median satisfaction: {not_disrupted.median():.2f}")
    print("Note: this standard test does not adjust for repeated customers.")

    # --------------------------------------------------
    # 11. Final summary
    # --------------------------------------------------
    print("\n" + "=" * 60)
    print("DISRUPTION ANALYSIS COMPLETED")
    print("=" * 60)
    print("Completed: data-quality checks and descriptive statistics.")
    print("Completed: Welch's t-test, confidence interval and Cohen's d.")
    print("Completed: customer-clustered regression when customer IDs are available.")
    print("Completed: supplementary Mann–Whitney U test.")
    print(
        "\nInterpretation note: findings are illustrative because the dataset "
        "is synthetic. Association does not establish causation."
    )


if __name__ == "__main__":
    main()
