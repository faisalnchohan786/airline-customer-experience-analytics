"""Research question: Which factors are associated with complaint risk?

Run from the project root:
    python python/complaint_risk_analysis.py

Fits a customer-clustered logistic regression. All data are synthetic.
"""
import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf

from analysis_utils import load_customer_journey, require_columns, p_value_text


def main():
    df = load_customer_journey()
    required = [
        "complaint_flag", "disruption_flag", "delay_minutes",
        "baggage_issue_flag", "customer_id"
    ]
    require_columns(df, required)

    work = df[required].copy()
    for col in [
        "complaint_flag", "disruption_flag",
        "delay_minutes", "baggage_issue_flag"
    ]:
        work[col] = pd.to_numeric(work[col], errors="coerce")

    valid = work.dropna(subset=required)
    valid = valid[
        valid["complaint_flag"].isin([0, 1])
        & valid["disruption_flag"].isin([0, 1])
        & valid["baggage_issue_flag"].isin([0, 1])
        & (valid["delay_minutes"] >= 0)
    ].copy()

    if valid["complaint_flag"].nunique() < 2:
        raise ValueError("Both complaint outcomes (0 and 1) are required.")

    print("=" * 60)
    print("COMPLAINT RISK ANALYSIS")
    print("=" * 60)
    print(f"Valid records: {len(valid):,}; excluded: {len(df) - len(valid):,}")
    print(f"Overall complaint rate: {valid['complaint_flag'].mean() * 100:.2f}%")

    formula = (
        "complaint_flag ~ disruption_flag + delay_minutes + baggage_issue_flag"
    )
    model = smf.glm(
        formula=formula,
        data=valid,
        family=sm.families.Binomial(),
    ).fit(
        cov_type="cluster",
        cov_kwds={"groups": valid["customer_id"]},
    )

    ci = model.conf_int()
    print("\n--- Customer-clustered logistic regression ---")
    print(model.summary())
    print("\n--- Adjusted odds ratios ---")
    for term in ["disruption_flag", "delay_minutes", "baggage_issue_flag"]:
        beta = model.params[term]
        lower, upper = ci.loc[term, 0], ci.loc[term, 1]
        print(
            f"{term}: OR={np.exp(beta):.3f}; "
            f"95% CI=[{np.exp(lower):.3f}, {np.exp(upper):.3f}]; "
            f"p={p_value_text(model.pvalues[term])}"
        )

    print("\nOdds ratio guide: OR > 1 indicates higher odds of a complaint;")
    print("OR < 1 indicates lower odds, conditional on the other model variables.")
    print("Odds ratios are not the same as risk ratios or percentage-point changes.")
    print("Interpretation is associational, not causal; data are synthetic.")


if __name__ == "__main__":
    main()
