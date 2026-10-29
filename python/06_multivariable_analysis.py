"""Research question: Are disruption, delay and baggage issues associated with satisfaction together?

Run from the project root:
    python python/multivariable_analysis.py

This is an adjusted association model, not a causal model. All data are synthetic.
"""
import pandas as pd
import statsmodels.formula.api as smf

from analysis_utils import load_customer_journey, require_columns, p_value_text


def main():
    df = load_customer_journey()
    required = [
        "overall_satisfaction_score", "disruption_flag",
        "delay_minutes", "baggage_issue_flag", "customer_id"
    ]
    require_columns(df, required)

    work = df[required].copy()
    for col in [
        "overall_satisfaction_score", "disruption_flag",
        "delay_minutes", "baggage_issue_flag"
    ]:
        work[col] = pd.to_numeric(work[col], errors="coerce")

    valid = work.dropna(subset=required)
    valid = valid[
        valid["overall_satisfaction_score"].between(1, 5)
        & valid["disruption_flag"].isin([0, 1])
        & valid["baggage_issue_flag"].isin([0, 1])
        & (valid["delay_minutes"] >= 0)
    ].copy()

    if len(valid) < 10:
        raise ValueError("Not enough valid records for multivariable analysis.")

    print("=" * 60)
    print("MULTIVARIABLE SATISFACTION ANALYSIS")
    print("=" * 60)
    print(f"Valid records: {len(valid):,}; excluded: {len(df) - len(valid):,}")

    formula = (
        "overall_satisfaction_score ~ disruption_flag "
        "+ delay_minutes + baggage_issue_flag"
    )
    model = smf.ols(formula, data=valid).fit(
        cov_type="cluster", cov_kwds={"groups": valid["customer_id"]}
    )

    print("\n--- Customer-clustered multivariable regression ---")
    print(model.summary())
    ci = model.conf_int()
    print("\n--- Adjusted associations ---")
    for term in ["disruption_flag", "delay_minutes", "baggage_issue_flag"]:
        print(
            f"{term}: coefficient={model.params[term]:.5f}; "
            f"clustered SE={model.bse[term]:.5f}; "
            f"p={p_value_text(model.pvalues[term])}; "
            f"95% CI=[{ci.loc[term, 0]:.5f}, {ci.loc[term, 1]:.5f}]"
        )

    print(f"\nR-squared: {model.rsquared:.3f}")
    print("Interpretation: each coefficient is adjusted for the other included")
    print("variables, but omitted confounders may remain. Do not claim causation.")
    print("Check overlap between disruption and delay before interpreting coefficients.")
    print("All findings are illustrative because the dataset is synthetic.")


if __name__ == "__main__":
    main()
