"""
Professional airline-style visualisations for Airline Customer Experience Analytics.

Run from the project root:
    python python/visualise_customer_experience.py

Input:
    data/customer_journey.xlsx

Outputs:
    outputs/visualisations_professional/*.png
    outputs/visualisations_professional/visualisation_summary.csv

All data in this portfolio project are synthetic.
"""

from pathlib import Path
import warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import statsmodels.api as sm
import statsmodels.formula.api as smf

warnings.filterwarnings("ignore", category=FutureWarning)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = PROJECT_ROOT / "data" / "customer_journey.xlsx"
OUTPUT_DIR = PROJECT_ROOT / "python" /"outputs" /"visualisations_professional"
SUMMARY_FILENAME = "visualisation_summary.csv"

REQUIRED_COLUMNS = [
    "customer_id",
    "disruption_flag",
    "delay_minutes",
    "baggage_issue_flag",
    "overall_satisfaction_score",
    "complaint_flag",
]

# Neutral enterprise palette, suitable for airline analytics without copying a brand.
NAVY = "#102A43"
BLUE = "#2878B5"
TEAL = "#159A9C"
SKY = "#69B7D5"
AMBER = "#E3A43B"
GREY = "#627D98"
LIGHT = "#D9E2EC"
BG = "#F7FAFC"
TEXT = "#243B53"


def setup_style():
    plt.rcParams.update({
        "figure.facecolor": BG,
        "axes.facecolor": BG,
        "axes.edgecolor": LIGHT,
        "axes.labelcolor": TEXT,
        "text.color": TEXT,
        "xtick.color": TEXT,
        "ytick.color": TEXT,
        "font.family": "DejaVu Sans",
        "font.size": 10,
        "axes.titlesize": 15,
        "axes.titleweight": "bold",
        "axes.labelsize": 10,
        "axes.titlepad": 14,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.color": LIGHT,
        "grid.linewidth": 0.8,
        "grid.alpha": 0.75,
        "axes.axisbelow": True,
        "savefig.facecolor": BG,
    })


def load_data():
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Could not find {DATA_PATH}. Keep customer_journey.xlsx in the data/ folder."
        )
    df = pd.read_excel(DATA_PATH)
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    for col in REQUIRED_COLUMNS[1:]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=REQUIRED_COLUMNS).copy()
    df = df[
        df["disruption_flag"].isin([0, 1])
        & df["baggage_issue_flag"].isin([0, 1])
        & df["complaint_flag"].isin([0, 1])
        & (df["delay_minutes"] >= 0)
        & df["overall_satisfaction_score"].between(1, 5)
    ].copy()

    if df.empty:
        raise ValueError("No valid records remain after validation.")
    print(f"Loaded {len(df):,} valid journey records.")
    print("Reminder: the dataset is synthetic.")
    return df


def save_fig(fig, filename):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUTPUT_DIR / filename, dpi=220, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved {filename}")


def add_bar_labels(ax, bars, values, counts, percent=False):
    """Use real newline characters in labels, not literal backslash-n sequences."""
    labels = []
    for value, count in zip(values, counts):
        value_text = f"{value:.1f}%" if percent else f"{value:.2f}"
        labels.append(f"{value_text}\n({count:,} journeys)")
    ax.bar_label(bars, labels=labels, padding=5, fontsize=9, color=NAVY)


def bar_chart(df, group_col, outcome, groups, labels, colors, title, ylabel,
              filename, percent=False, summary_rows=None):
    grouped = df.groupby(group_col)[outcome].agg(["count", "mean"])
    present_groups = [group for group in groups if group in grouped.index]
    names = [labels[group] for group in present_groups]
    counts = [int(grouped.loc[group, "count"]) for group in present_groups]
    values = [
        float(grouped.loc[group, "mean"]) * (100 if percent else 1)
        for group in present_groups
    ]

    fig, ax = plt.subplots(figsize=(9, 5.4))
    bars = ax.bar(names, values, color=colors[:len(values)], width=0.58, zorder=3)
    ax.set_title(title, loc="left")
    ax.set_ylabel(ylabel)
    ax.grid(axis="x", visible=False)
    ax.grid(axis="y", visible=True)
    upper = max(values) if values else 1
    ax.set_ylim(0, upper * 1.30 if upper > 0 else 1)
    add_bar_labels(ax, bars, values, counts, percent=percent)
    fig.tight_layout()
    save_fig(fig, filename)

    if summary_rows is not None:
        for name, count, value in zip(names, counts, values):
            summary_rows.append({
                "chart": title,
                "group": name,
                "n": count,
                "metric": ylabel,
                "value": value,
            })


def plot_delay_bands(df, summary_rows):
    df = df.copy()
    bins = [-0.001, 0, 15, 60, np.inf]
    labels = ["0 min", "1–15 min", "16–60 min", ">60 min"]
    df["delay_band"] = pd.cut(
        df["delay_minutes"], bins=bins, labels=labels, right=True, include_lowest=True
    )
    grouped = (
        df.groupby("delay_band", observed=False)["overall_satisfaction_score"]
        .agg(["count", "mean"])
        .reindex(labels)
        .dropna(subset=["mean"])
    )

    fig, ax = plt.subplots(figsize=(9, 5.4))
    colors = [TEAL, BLUE, SKY, AMBER][:len(grouped)]
    bars = ax.bar(grouped.index.astype(str), grouped["mean"], color=colors, width=0.62, zorder=3)
    ax.set_title("Satisfaction declines as delay severity increases", loc="left")
    ax.set_ylabel("Mean satisfaction score (1–5)")
    ax.set_xlabel("Delay duration")
    ax.set_ylim(0, 5)
    ax.grid(axis="x", visible=False)
    add_bar_labels(
        ax, bars, grouped["mean"].tolist(), grouped["count"].astype(int).tolist()
    )
    fig.tight_layout()
    save_fig(fig, "02_satisfaction_by_delay_band.png")

    for band, row in grouped.iterrows():
        summary_rows.append({
            "chart": "Satisfaction by delay band",
            "group": str(band),
            "n": int(row["count"]),
            "metric": "Mean satisfaction score (1–5)",
            "value": float(row["mean"]),
        })


def plot_adjusted_satisfaction(df):
    model_df = df[
        ["customer_id", "overall_satisfaction_score", "disruption_flag",
         "delay_minutes", "baggage_issue_flag"]
    ].dropna().copy()
    model = smf.ols(
        "overall_satisfaction_score ~ disruption_flag + delay_minutes + baggage_issue_flag",
        data=model_df
    ).fit(cov_type="cluster", cov_kwds={"groups": model_df["customer_id"]})

    terms = ["disruption_flag", "delay_minutes", "baggage_issue_flag"]
    names = ["Disruption (yes vs no)", "Each additional delay minute", "Baggage issue (yes vs no)"]
    estimates = model.params[terms]
    ci = model.conf_int().loc[terms]
    lower = estimates - ci[0]
    upper = ci[1] - estimates

    fig, ax = plt.subplots(figsize=(9, 5.4))
    y = np.arange(len(terms))
    ax.errorbar(
        estimates.values, y, xerr=np.vstack([lower.values, upper.values]),
        fmt="o", markersize=8, color=TEAL, ecolor=BLUE, elinewidth=2.2,
        capsize=5, markeredgecolor=BG, markeredgewidth=1.2
    )
    ax.axvline(0, color=AMBER, linestyle="--", linewidth=1.8, label="No association reference")
    ax.set_yticks(y, names)
    ax.invert_yaxis()
    ax.set_xlabel("Adjusted change in satisfaction points (95% CI)")
    ax.set_title("Operational factors associated with satisfaction", loc="left")
    ax.grid(axis="y", visible=False)
    ax.legend(frameon=False, loc="lower right")
    fig.tight_layout()
    save_fig(fig, "05_adjusted_satisfaction_coefficients.png")
    print("\nAdjusted satisfaction estimates:")
    print(pd.DataFrame({
        "coefficient": estimates, "ci_lower": ci[0], "ci_upper": ci[1],
        "p_value": model.pvalues[terms]
    }).to_string())


def plot_complaint_odds_ratios(df):
    model_df = df[
        ["customer_id", "complaint_flag", "disruption_flag",
         "delay_minutes", "baggage_issue_flag"]
    ].dropna().copy()
    model = smf.glm(
        "complaint_flag ~ disruption_flag + delay_minutes + baggage_issue_flag",
        data=model_df, family=sm.families.Binomial()
    ).fit(cov_type="cluster", cov_kwds={"groups": model_df["customer_id"]})

    terms = ["disruption_flag", "delay_minutes", "baggage_issue_flag"]
    names = ["Disruption (yes vs no)", "Each additional delay minute", "Baggage issue (yes vs no)"]
    odds = np.exp(model.params[terms])
    log_ci = model.conf_int().loc[terms]
    lower, upper = np.exp(log_ci[0]), np.exp(log_ci[1])

    fig, ax = plt.subplots(figsize=(9, 5.4))
    y = np.arange(len(terms))
    ax.errorbar(
        odds.values, y,
        xerr=np.vstack([odds.values - lower.values, upper.values - odds.values]),
        fmt="o", markersize=8, color=TEAL, ecolor=BLUE, elinewidth=2.2,
        capsize=5, markeredgecolor=BG, markeredgewidth=1.2
    )
    ax.axvline(1, color=AMBER, linestyle="--", linewidth=1.8, label="OR = 1 (no association)")
    ax.set_xscale("log")
    ax.set_yticks(y, names)
    ax.invert_yaxis()
    ax.set_xlabel("Adjusted odds ratio (log scale; 95% CI)")
    ax.set_title("Factors associated with complaint odds", loc="left")
    ax.grid(axis="y", visible=False)
    ax.legend(frameon=False, loc="lower right")
    fig.tight_layout()
    save_fig(fig, "06_adjusted_complaint_odds_ratios.png")
    print("\nAdjusted complaint odds ratios:")
    print(pd.DataFrame({
        "odds_ratio": odds, "ci_lower": lower, "ci_upper": upper,
        "p_value": model.pvalues[terms]
    }).to_string())


def main():
    setup_style()
    df = load_data()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    summary_rows = []

    bar_chart(
        df, "disruption_flag", "overall_satisfaction_score", [0, 1],
        {0: "No disruption", 1: "Disruption"}, [TEAL, AMBER],
        "Disruption is associated with lower satisfaction",
        "Mean satisfaction score (1–5)", "01_satisfaction_by_disruption.png",
        summary_rows=summary_rows
    )
    plot_delay_bands(df, summary_rows)
    bar_chart(
        df, "disruption_flag", "complaint_flag", [0, 1],
        {0: "No disruption", 1: "Disruption"}, [TEAL, AMBER],
        "Complaint rates are higher for disrupted journeys",
        "Journeys with a complaint (%)", "03_complaint_rate_by_disruption.png",
        percent=True, summary_rows=summary_rows
    )
    bar_chart(
        df, "baggage_issue_flag", "complaint_flag", [0, 1],
        {0: "No baggage issue", 1: "Baggage issue"}, [TEAL, AMBER],
        "Baggage issues are associated with more complaints",
        "Journeys with a complaint (%)", "04_complaint_rate_by_baggage_issue.png",
        percent=True, summary_rows=summary_rows
    )
    plot_adjusted_satisfaction(df)
    plot_complaint_odds_ratios(df)

    summary_path = OUTPUT_DIR / SUMMARY_FILENAME
    pd.DataFrame(summary_rows).to_csv(summary_path, index=False)
    print(f"\nSaved summary: {summary_path}")
    print("\n" + "=" * 60)
    print("PROFESSIONAL VISUALISATIONS COMPLETE")
    print("=" * 60)
    print(f"Output folder: {OUTPUT_DIR}")
    print(f"Valid records used: {len(df):,}")
    print("All data are synthetic; associations are not causal.")


if __name__ == "__main__":
    main()
