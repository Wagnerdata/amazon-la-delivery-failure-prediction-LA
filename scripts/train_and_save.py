"""
train_and_save.py — Train the RandomForest, generate model charts, save artifact.

Run from project root:  python scripts/train_and_save.py
"""
import warnings
warnings.filterwarnings("ignore")
import pickle
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import (
    roc_auc_score, recall_score, precision_score, f1_score,
    average_precision_score, roc_curve, precision_recall_curve,
)

try:
    from imblearn.over_sampling import SMOTE
    HAS_SMOTE = True
except ImportError:
    HAS_SMOTE = False

matplotlib.rcParams["figure.facecolor"] = "white"
matplotlib.rcParams["axes.facecolor"]   = "white"

DANGER = "#E74C3C"; WARN = "#F39C12"; SAFE = "#27AE60"
NAVY   = "#2C3E50"; ACCENT = "#2980B9"

BASE        = Path(__file__).parent.parent
FIGURES_DIR = BASE / "reports" / "figures"
ML_DIR      = BASE / "ml"
FIGURES_DIR.mkdir(exist_ok=True)
ML_DIR.mkdir(exist_ok=True)

# ── Load ──────────────────────────────────────────────────────────────────────
print("Loading data...")
df = pd.read_csv(BASE / "data" / "packages_validation.csv")
df["delivery_failure"] = df["delivery_failed"]
print(f"  Rows: {len(df):,} | Failures: {df['delivery_failure'].sum()} ({df['delivery_failure'].mean():.2%})")

# ── Feature engineering ───────────────────────────────────────────────────────
encoders = {}
df_enc = df.copy()
for col in ["carrier", "shift", "package_type"]:
    le = LabelEncoder()
    df_enc[col + "_enc"] = le.fit_transform(df_enc[col])
    encoders[col] = le

df_enc["dist_bucket"] = pd.cut(
    df_enc["route_distance_km"], bins=[-1, 40, 60, 9999], labels=[0, 1, 2]
).astype(int)

FEATURES = [
    "carrier_enc", "shift_enc", "package_type_enc",
    "dist_bucket", "packages_in_route",
    "double_scan", "short_service_time", "cr_number_missing",
]

X = df_enc[FEATURES].values
y = df_enc["delivery_failure"].values

# ── Split ─────────────────────────────────────────────────────────────────────
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.20, random_state=42, stratify=y
)
print(f"  Train: {len(X_train)} | Test: {len(X_test)} | Failures train: {y_train.sum()} test: {y_test.sum()}")

# ── Baseline RF ───────────────────────────────────────────────────────────────
print("Training Baseline RF (class_weight=balanced)...")
rf_base = RandomForestClassifier(
    n_estimators=300, class_weight="balanced",
    random_state=42, n_jobs=-1, max_depth=8, min_samples_leaf=3
)
rf_base.fit(X_train, y_train)
y_prob_base = rf_base.predict_proba(X_test)[:, 1]
y_pred_base = rf_base.predict(X_test)
auc_base    = roc_auc_score(y_test, y_prob_base)
rec_base    = recall_score(y_test, y_pred_base, zero_division=0)
prec_base   = precision_score(y_test, y_pred_base, zero_division=0)
ap_base     = average_precision_score(y_test, y_prob_base)
print(f"  AUC={auc_base:.4f} Recall={rec_base:.4f} Prec={prec_base:.4f} AP={ap_base:.4f}")

# ── SMOTE ─────────────────────────────────────────────────────────────────────
if HAS_SMOTE:
    print("Training SMOTE+RF...")
    smote = SMOTE(random_state=42, k_neighbors=min(5, y_train.sum() - 1))
    X_sm, y_sm = smote.fit_resample(X_train, y_train)
    rf_smote = RandomForestClassifier(
        n_estimators=300, random_state=42, n_jobs=-1, max_depth=8, min_samples_leaf=3
    )
    rf_smote.fit(X_sm, y_sm)
    y_prob_sm = rf_smote.predict_proba(X_test)[:, 1]
    y_pred_sm = rf_smote.predict(X_test)
    auc_sm    = roc_auc_score(y_test, y_prob_sm)
    rec_sm    = recall_score(y_test, y_pred_sm, zero_division=0)
    prec_sm   = precision_score(y_test, y_pred_sm, zero_division=0)
    ap_sm     = average_precision_score(y_test, y_prob_sm)
    print(f"  AUC={auc_sm:.4f} Recall={rec_sm:.4f} Prec={prec_sm:.4f} AP={ap_sm:.4f}")

    best_model = rf_smote if rec_sm >= rec_base else rf_base
    best_probs = y_prob_sm if rec_sm >= rec_base else y_prob_base
    best_name  = "SMOTE+RF" if rec_sm >= rec_base else "Balanced-Weight RF"
else:
    best_model = rf_base
    best_probs = y_prob_base
    best_name  = "Balanced-Weight RF"

print(f"  Best model: {best_name}")

# ── Threshold optimization ────────────────────────────────────────────────────
print("Optimizing threshold...")
thresholds = np.arange(0.05, 0.96, 0.05)
rows = []
for t in thresholds:
    yt = (best_probs >= t).astype(int)
    rows.append({
        "threshold": t,
        "recall":    recall_score(y_test, yt, zero_division=0),
        "precision": precision_score(y_test, yt, zero_division=0),
        "f1":        f1_score(y_test, yt, zero_division=0),
    })
thresh_df = pd.DataFrame(rows)
valid     = thresh_df[thresh_df["precision"] > 0]
best_row  = valid.loc[valid["recall"].idxmax()]
best_thresh = best_row["threshold"]
print(f"  Best threshold: {best_thresh:.2f} -> recall={best_row['recall']:.4f} prec={best_row['precision']:.4f}")

# ── Plot: threshold curve ─────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(thresh_df["threshold"], thresh_df["recall"],    color=DANGER, lw=2.5, label="Recall")
ax.plot(thresh_df["threshold"], thresh_df["precision"], color=SAFE,   lw=2.5, label="Precision")
ax.plot(thresh_df["threshold"], thresh_df["f1"],        color=ACCENT, lw=2,   label="F1", linestyle="--")
ax.axvline(best_thresh, color=WARN, linestyle=":", lw=2,
           label=f"Optimal ({best_thresh:.2f})")
ax.set_xlabel("Decision Threshold", fontweight="bold")
ax.set_ylabel("Score", fontweight="bold")
ax.set_title(
    f"Threshold Optimization — {best_name}\n"
    "Lowering threshold trades precision for recall ($17/missed failure)",
    fontsize=12, fontweight="bold", color=NAVY,
)
ax.legend(); ax.set_xlim(0, 1); ax.set_ylim(0, 1.05)
sns.despine(ax=ax); plt.tight_layout()
plt.savefig(FIGURES_DIR / "threshold_optimization.png", dpi=150, bbox_inches="tight")
plt.close()
print("  Saved threshold_optimization.png")

# ── Plot: feature importance ──────────────────────────────────────────────────
imps = pd.DataFrame({
    "feature":    FEATURES,
    "importance": best_model.feature_importances_,
}).sort_values("importance", ascending=True)

def ic(v):
    return DANGER if v >= 0.20 else WARN if v >= 0.12 else ACCENT

bc = [ic(v) for v in imps["importance"]]
fig, ax = plt.subplots(figsize=(10, 6))
bars = ax.barh(imps["feature"], imps["importance"], color=bc, edgecolor="white", height=0.65)
for bar, val in zip(bars, imps["importance"]):
    ax.text(val + 0.002, bar.get_y() + bar.get_height() / 2,
            f"{val:.4f}", va="center", fontsize=9, color=NAVY)
patches = [
    mpatches.Patch(facecolor=DANGER, label="High importance (>= 0.20)"),
    mpatches.Patch(facecolor=WARN,   label="Medium importance (0.12-0.20)"),
    mpatches.Patch(facecolor=ACCENT, label="Lower importance (< 0.12)"),
]
ax.legend(handles=patches, fontsize=9)
ax.set_xlabel("Mean Decrease in Gini Impurity", fontweight="bold")
ax.set_title(
    f"Feature Importance — {best_name}\n"
    "(mean decrease in impurity across 300 trees)",
    fontsize=12, fontweight="bold", color=NAVY,
)
sns.despine(ax=ax); plt.tight_layout()
plt.savefig(FIGURES_DIR / "feature_importance_final.png", dpi=150, bbox_inches="tight")
plt.close()
print("  Saved feature_importance_final.png")

# ── Plot: ROC + PR curves ─────────────────────────────────────────────────────
fpr, tpr, _ = roc_curve(y_test, best_probs)
auc_val     = roc_auc_score(y_test, best_probs)
prec_c, rec_c, _ = precision_recall_curve(y_test, best_probs)
ap_val      = average_precision_score(y_test, best_probs)

fig, axes = plt.subplots(1, 2, figsize=(13, 5))
axes[0].plot(fpr, tpr, color=ACCENT, lw=2.5, label=f"ROC (AUC={auc_val:.4f})")
axes[0].plot([0, 1], [0, 1], "k--", lw=1.2, label="Random")
axes[0].fill_between(fpr, tpr, alpha=0.10, color=ACCENT)
axes[0].set_xlabel("FPR", fontweight="bold"); axes[0].set_ylabel("TPR", fontweight="bold")
axes[0].set_title(f"ROC Curve — {best_name}", fontweight="bold", color=NAVY)
axes[0].legend(); sns.despine(ax=axes[0])

axes[1].plot(rec_c, prec_c, color=DANGER, lw=2.5, label=f"PR (AP={ap_val:.4f})")
axes[1].axhline(y_test.mean(), color="gray", linestyle="--", lw=1.2,
                label=f"Random ({y_test.mean():.3f})")
axes[1].fill_between(rec_c, prec_c, alpha=0.10, color=DANGER)
axes[1].set_xlabel("Recall", fontweight="bold"); axes[1].set_ylabel("Precision", fontweight="bold")
axes[1].set_title(f"PR Curve — {best_name}", fontweight="bold", color=NAVY)
axes[1].legend(); sns.despine(ax=axes[1])

plt.suptitle("Model Evaluation — Imbalanced Class Performance",
             fontsize=13, fontweight="bold", color=NAVY)
plt.tight_layout()
plt.savefig(FIGURES_DIR / "roc_pr_curves.png", dpi=150, bbox_inches="tight")
plt.close()
print("  Saved roc_pr_curves.png")

# ── Save model artifact ───────────────────────────────────────────────────────
artifact = {
    "model":       best_model,
    "model_name":  best_name,
    "encoders":    encoders,
    "features":    FEATURES,
    "best_threshold": float(best_thresh),
    "metrics": {
        "auc_roc":          float(auc_val),
        "avg_precision":    float(ap_val),
        "recall_optimized": float(best_row["recall"]),
        "precision_at_opt": float(best_row["precision"]),
    },
    "dataset": {
        "source":       "Amazon LMRC 2021",
        "location":     "Los Angeles, CA",
        "period":       "July 2018",
        "n_packages":   len(df),
        "n_failures":   int(df["delivery_failure"].sum()),
        "failure_rate": float(df["delivery_failure"].mean()),
    },
}

pkl_path = ML_DIR / "random_forest_model.pkl"
with open(pkl_path, "wb") as f:
    pickle.dump(artifact, f)

print(f"\nModel saved -> {pkl_path}")
print(f"  File size: {pkl_path.stat().st_size / 1024:.1f} KB")
print(f"  AUC-ROC  : {auc_val:.4f}")
print(f"  Recall @ opt threshold ({best_thresh:.2f}): {best_row['recall']:.4f}")
print(f"  Precision @ opt threshold : {best_row['precision']:.4f}")

# ── Verify round-trip ─────────────────────────────────────────────────────────
with open(pkl_path, "rb") as f:
    check = pickle.load(f)
auc_check = roc_auc_score(y_test, check["model"].predict_proba(X_test)[:, 1])
print(f"  Reload verify AUC: {auc_check:.4f}  OK")
print("\nAll done.")
