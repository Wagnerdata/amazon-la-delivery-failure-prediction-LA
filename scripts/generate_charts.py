"""
generate_charts.py — Export all 6 EDA charts for the datafolio.

Charts written to: reports/figures/
  1. failure_rate_by_carrier.png
  2. failure_rate_by_shift.png
  3. failure_rate_by_distance.png
  4. class_imbalance.png
  5. correlation_heatmap.png
  6. feature_importance_preview.png
"""

import os
import sqlite3
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.preprocessing import LabelEncoder

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE        = Path(__file__).parent.parent
DATA_PATH   = BASE / "data" / "packages_validation.csv"
FIGURES_DIR = BASE / "reports" / "figures"
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

# ── Color palette ──────────────────────────────────────────────────────────────
DANGER_COLOR  = "#E74C3C"   # red   — high risk
WARN_COLOR    = "#F39C12"   # orange — medium risk
SAFE_COLOR    = "#27AE60"   # green  — low risk
NEUTRAL_COLOR = "#3498DB"   # blue   — mid risk
NAVY          = "#2C3E50"   # dark navy — text / titles
PALETTE       = [DANGER_COLOR, WARN_COLOR, NEUTRAL_COLOR, SAFE_COLOR]

# ── Global matplotlib settings ─────────────────────────────────────────────────
matplotlib.rcParams.update({
    "figure.facecolor": "white",
    "axes.facecolor":   "white",
    "font.family":      "sans-serif",
    "axes.spines.top":  False,
    "axes.spines.right": False,
})

# ── Load data ──────────────────────────────────────────────────────────────────
print("Loading packages_validation.csv …")
df = pd.read_csv(DATA_PATH)
df["delivery_failure"] = df["damaged_on_arrival"]   # canonical target
overall_avg = df["delivery_failure"].mean() * 100

# SQLite for SQL-based queries
conn = sqlite3.connect(":memory:")
df.to_sql("packages", conn, index=False, if_exists="replace")


# ──────────────────────────────────────────────────────────────────────────────
# 1. failure_rate_by_carrier.png
# ──────────────────────────────────────────────────────────────────────────────
def chart_carrier():
    query = """
        SELECT carrier,
               COUNT(*)                                              AS total_packages,
               SUM(delivery_failure)                                 AS failures,
               ROUND(100.0 * SUM(delivery_failure) / COUNT(*), 2)   AS failure_rate_pct
        FROM packages
        GROUP BY carrier
        ORDER BY failure_rate_pct DESC
    """
    carrier_df = pd.read_sql(query, conn)

    max_rate = carrier_df["failure_rate_pct"].max()
    min_rate = carrier_df["failure_rate_pct"].min()
    bar_colors = [
        DANGER_COLOR if r == max_rate else
        SAFE_COLOR   if r == min_rate else
        NEUTRAL_COLOR
        for r in carrier_df["failure_rate_pct"]
    ]

    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(carrier_df["carrier"], carrier_df["failure_rate_pct"],
                  color=bar_colors, edgecolor="white", linewidth=1.2, width=0.6)
    ax.axhline(overall_avg, color="#7F8C8D", linestyle="--", linewidth=1.8,
               label=f"Overall average ({overall_avg:.2f}%)")

    for bar, row in zip(bars, carrier_df.itertuples()):
        ax.text(bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.04,
                f"{row.failure_rate_pct:.2f}%\n(n={row.total_packages:,})",
                ha="center", fontsize=10, fontweight="bold", color=NAVY)

    ax.set_xlabel("Carrier", fontweight="bold", color=NAVY)
    ax.set_ylabel("Failure Rate (%)", fontweight="bold", color=NAVY)
    ax.set_title("Delivery Failure Rate by Carrier\n(Amazon Last-Mile Research Challenge — LA Routes, July 2018)",
                 fontsize=13, fontweight="bold", color=NAVY, pad=12)
    ax.set_ylim(0, max_rate * 1.60)
    ax.legend(fontsize=10)
    ax.tick_params(colors=NAVY)
    sns.despine(ax=ax)
    plt.tight_layout()

    out = FIGURES_DIR / "failure_rate_by_carrier.png"
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  ✓ {out.name}")


# ──────────────────────────────────────────────────────────────────────────────
# 2. failure_rate_by_shift.png
# ──────────────────────────────────────────────────────────────────────────────
def chart_shift():
    query = """
        SELECT shift,
               COUNT(*)                                              AS total_packages,
               SUM(delivery_failure)                                 AS failures,
               ROUND(100.0 * SUM(delivery_failure) / COUNT(*), 2)   AS failure_rate_pct
        FROM packages
        GROUP BY shift
        ORDER BY failure_rate_pct DESC
    """
    shift_df = pd.read_sql(query, conn)

    present = shift_df["shift"].tolist()
    order   = [s for s in ["morning", "afternoon", "night"] if s in present]
    plot_df = shift_df.set_index("shift").reindex(order).reset_index()

    shift_colors = [DANGER_COLOR, WARN_COLOR, SAFE_COLOR][: len(order)]

    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(plot_df["shift"].str.capitalize(),
                  plot_df["failure_rate_pct"],
                  color=shift_colors, edgecolor="white", linewidth=1.2, width=0.5)
    ax.axhline(overall_avg, color="#7F8C8D", linestyle="--", linewidth=1.8,
               label=f"Overall average ({overall_avg:.2f}%)")

    for bar, row in zip(bars, plot_df.itertuples()):
        ax.text(bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.04,
                f"{row.failure_rate_pct:.2f}%\n(n={row.total_packages:,})",
                ha="center", fontsize=11, fontweight="bold", color=NAVY)

    # Annotation for "only 2 shifts"
    ax.annotate("Only 2 shifts observed\n(no night routes in LA dataset)",
                xy=(0.97, 0.97), xycoords="axes fraction",
                ha="right", va="top", fontsize=9, color="#7F8C8D",
                style="italic")

    ax.set_xlabel("Delivery Shift", fontweight="bold", color=NAVY)
    ax.set_ylabel("Failure Rate (%)", fontweight="bold", color=NAVY)
    ax.set_title("Delivery Failure Rate by Shift\n(Morning routes face more access barriers — locked lobbies, low occupancy)",
                 fontsize=12, fontweight="bold", color=NAVY, pad=12)
    ax.set_ylim(0, plot_df["failure_rate_pct"].max() * 1.60)
    ax.legend(fontsize=10)
    sns.despine(ax=ax)
    plt.tight_layout()

    out = FIGURES_DIR / "failure_rate_by_shift.png"
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  ✓ {out.name}")


# ──────────────────────────────────────────────────────────────────────────────
# 3. failure_rate_by_distance.png
# ──────────────────────────────────────────────────────────────────────────────
def chart_distance():
    query = """
        SELECT distance_bucket,
               COUNT(*)                                              AS total_packages,
               SUM(delivery_failure)                                 AS failures,
               ROUND(100.0 * SUM(delivery_failure) / COUNT(*), 2)   AS failure_rate_pct
        FROM (
            SELECT delivery_failure,
                   CASE
                       WHEN route_distance_km < 40  THEN '< 40 km'
                       WHEN route_distance_km <= 60 THEN '40-60 km'
                       ELSE                              '> 60 km'
                   END AS distance_bucket
            FROM packages
        ) sub
        GROUP BY distance_bucket
        ORDER BY failure_rate_pct DESC
    """
    dist_df = pd.read_sql(query, conn)

    dist_order = ["< 40 km", "40-60 km", "> 60 km"]
    plot_df = dist_df.set_index("distance_bucket").reindex(dist_order).reset_index()
    plot_df["failure_rate_pct"] = plot_df["failure_rate_pct"].fillna(0)

    dist_colors = [DANGER_COLOR, WARN_COLOR, SAFE_COLOR]

    fig, ax = plt.subplots(figsize=(9, 5.5))
    bars = ax.bar(plot_df["distance_bucket"], plot_df["failure_rate_pct"],
                  color=dist_colors, edgecolor="white", linewidth=1.2, width=0.55)
    ax.axhline(overall_avg, color="#7F8C8D", linestyle="--", linewidth=1.8,
               label=f"Overall average ({overall_avg:.2f}%)")

    for bar, row in zip(bars, plot_df.itertuples()):
        ax.text(bar.get_x() + bar.get_width() / 2,
                max(bar.get_height(), 0) + 0.05,
                f"{row.failure_rate_pct:.2f}%\n(n={row.total_packages:,})",
                ha="center", fontsize=11, fontweight="bold", color=NAVY)

    # Urban Density Paradox annotation
    ax.annotate(
        "URBAN DENSITY PARADOX\nDense LA neighborhoods: locked lobbies,\nkey-fob access, congested Amazon Lockers",
        xy=(0, plot_df.loc[plot_df["distance_bucket"] == "< 40 km", "failure_rate_pct"].values[0]),
        xytext=(1.05, 1.60),
        arrowprops=dict(arrowstyle="->", color=DANGER_COLOR, lw=2.0),
        fontsize=9, color=DANGER_COLOR, fontweight="bold",
        bbox=dict(boxstyle="round,pad=0.4", facecolor="#FFF0EE",
                  edgecolor=DANGER_COLOR, alpha=0.95),
    )

    ax.set_xlabel("Route Distance Bucket", fontweight="bold", color=NAVY)
    ax.set_ylabel("Failure Rate (%)", fontweight="bold", color=NAVY)
    ax.set_title("Delivery Failure Rate by Route Distance\n"
                 "(Counterintuitive: shortest routes have the HIGHEST failure rate)",
                 fontsize=12, fontweight="bold", color=NAVY, pad=12)
    ax.set_ylim(0, 3.0)
    ax.legend(fontsize=10)
    sns.despine(ax=ax)
    plt.tight_layout()

    out = FIGURES_DIR / "failure_rate_by_distance.png"
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  ✓ {out.name}")


# ──────────────────────────────────────────────────────────────────────────────
# 4. class_imbalance.png
# ──────────────────────────────────────────────────────────────────────────────
def chart_class_imbalance():
    counts       = df["delivery_failure"].value_counts().sort_index()
    failure_rate = df["delivery_failure"].mean()

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    # Left: absolute counts
    bar_colors = [SAFE_COLOR, DANGER_COLOR]
    bars = axes[0].bar(["Delivered (0)", "Failed (1)"], counts.values,
                       color=bar_colors, edgecolor="white", linewidth=1.5, width=0.5)
    for bar, val in zip(bars, counts.values):
        pct = val / len(df) * 100
        axes[0].text(bar.get_x() + bar.get_width() / 2,
                     bar.get_height() + 25,
                     f"n = {val:,}\n({pct:.2f}%)",
                     ha="center", va="bottom", fontweight="bold", fontsize=12, color=NAVY)
    axes[0].set_ylabel("Package Count", fontweight="bold", color=NAVY)
    axes[0].set_title("Absolute Class Counts", fontweight="bold", color=NAVY, pad=10)
    axes[0].set_ylim(0, counts.max() * 1.20)
    sns.despine(ax=axes[0])

    # Right: stacked proportion bar
    axes[1].barh([""], [1 - failure_rate], color=SAFE_COLOR,
                 label=f"Delivered  ({1 - failure_rate:.2%})", height=0.5)
    axes[1].barh([""], [failure_rate], left=[1 - failure_rate], color=DANGER_COLOR,
                 label=f"Failed     ({failure_rate:.2%})", height=0.5)
    axes[1].set_xlim(0, 1)
    axes[1].set_xlabel("Proportion of Total Packages", fontweight="bold", color=NAVY)
    axes[1].set_title("Class Proportion — ~140:1 Imbalance", fontweight="bold", color=NAVY, pad=10)
    axes[1].legend(loc="lower right", fontsize=11)
    # Arrow callout
    axes[1].annotate(
        f"Only {counts[1]} failures\nin {len(df):,} packages",
        xy=(1 - failure_rate + failure_rate / 2, 0),
        xytext=(0.7, 0.32),
        arrowprops=dict(arrowstyle="->", color=DANGER_COLOR, lw=1.8),
        fontsize=9, color=DANGER_COLOR, fontweight="bold",
        bbox=dict(boxstyle="round,pad=0.3", facecolor="#FFF0EE",
                  edgecolor=DANGER_COLOR, alpha=0.9),
    )
    sns.despine(ax=axes[1])

    plt.suptitle("Class Imbalance — Why Accuracy Is a Misleading Metric\n"
                 "A model that always predicts 'Delivered' would score 99.3% accuracy",
                 fontsize=12, fontweight="bold", color=NAVY)
    plt.tight_layout()

    out = FIGURES_DIR / "class_imbalance.png"
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  ✓ {out.name}")


# ──────────────────────────────────────────────────────────────────────────────
# 5. correlation_heatmap.png
# ──────────────────────────────────────────────────────────────────────────────
def chart_heatmap():
    # Drop: identifier, zero-variance cols, and the target proxy (data leakage)
    drop_cols = ["package_id", "weather_risk", "days_in_fc", "damaged_on_arrival"]
    df_corr   = df.drop(columns=drop_cols).copy()

    le = LabelEncoder()
    for col in ["package_type", "shift", "carrier"]:
        df_corr[col] = le.fit_transform(df_corr[col])

    corr_matrix = df_corr.corr()
    mask        = np.triu(np.ones_like(corr_matrix, dtype=bool))

    fig, ax = plt.subplots(figsize=(10, 8))
    sns.heatmap(
        corr_matrix, mask=mask, annot=True, fmt=".2f",
        cmap="RdBu_r", vmin=-0.3, vmax=0.3,
        linewidths=0.5, linecolor="white", ax=ax,
        annot_kws={"size": 9},
        cbar_kws={"label": "Pearson Correlation"},
    )
    ax.set_title(
        "Pearson Correlation Heatmap — Encoded Features vs Target\n"
        "Note: damaged_on_arrival excluded (data leakage); "
        "weather_risk & days_in_fc excluded (zero variance)",
        fontsize=11, fontweight="bold", color=NAVY, pad=12,
    )
    plt.tight_layout()

    out = FIGURES_DIR / "correlation_heatmap.png"
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  ✓ {out.name}")


# ──────────────────────────────────────────────────────────────────────────────
# 6. feature_importance_preview.png
# ──────────────────────────────────────────────────────────────────────────────
def chart_feature_importance():
    feature_rates = {}

    for col in ["carrier", "shift", "package_type"]:
        for val, grp in df.groupby(col):
            rate  = grp["delivery_failure"].mean() * 100
            label = f"{col} = {val}"
            feature_rates[label] = rate

    for flag in ["double_scan", "locker_issue", "cr_number_missing"]:
        active = df[df[flag] == 1]
        if len(active) > 0:
            rate  = active["delivery_failure"].mean() * 100
            label = f"{flag} = 1"
            feature_rates[label] = rate

    importance_df = (
        pd.DataFrame(list(feature_rates.items()),
                     columns=["Feature Value", "Failure Rate (%)"])
        .sort_values("Failure Rate (%)", ascending=True)
        .reset_index(drop=True)
    )

    def risk_color(rate):
        if rate >= 2.0:   return DANGER_COLOR
        elif rate >= 1.0: return WARN_COLOR
        elif rate >= 0.5: return NEUTRAL_COLOR
        else:             return SAFE_COLOR

    bar_colors = [risk_color(r) for r in importance_df["Failure Rate (%)"]]

    fig, ax = plt.subplots(figsize=(11, 7))
    bars = ax.barh(
        importance_df["Feature Value"],
        importance_df["Failure Rate (%)"],
        color=bar_colors, edgecolor="white", linewidth=0.8, height=0.70,
    )
    ax.axvline(overall_avg, color="#7F8C8D", linestyle="--", linewidth=1.8,
               label=f"Overall avg ({overall_avg:.2f}%)")

    for bar, val in zip(bars, importance_df["Failure Rate (%)"]):
        ax.text(val + 0.04, bar.get_y() + bar.get_height() / 2,
                f"{val:.2f}%", va="center", fontsize=9, color=NAVY)

    legend_patches = [
        mpatches.Patch(facecolor=DANGER_COLOR,  label="High risk   (≥ 2.0%)"),
        mpatches.Patch(facecolor=WARN_COLOR,    label="Medium risk (1.0–2.0%)"),
        mpatches.Patch(facecolor=NEUTRAL_COLOR, label="Mild risk   (0.5–1.0%)"),
        mpatches.Patch(facecolor=SAFE_COLOR,    label="Low risk    (< 0.5%)"),
    ]
    ax.legend(handles=legend_patches, loc="lower right", fontsize=9, framealpha=0.9)
    ax.set_xlabel("Conditional Failure Rate (%)", fontweight="bold", color=NAVY)
    ax.set_title(
        "Feature Importance Preview — Conditional Failure Rates\n"
        "Model-free ranking: longer bar = stronger predictive signal",
        fontsize=13, fontweight="bold", color=NAVY, pad=12,
    )
    ax.tick_params(axis="y", labelsize=9)
    sns.despine(ax=ax)
    plt.tight_layout()

    out = FIGURES_DIR / "feature_importance_preview.png"
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  ✓ {out.name}")


# ──────────────────────────────────────────────────────────────────────────────
# Run all charts
# ──────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\nGenerating EDA charts …")
    chart_carrier()
    chart_shift()
    chart_distance()
    chart_class_imbalance()
    chart_heatmap()
    chart_feature_importance()
    print(f"\nAll 6 charts saved to: {FIGURES_DIR}\n")
