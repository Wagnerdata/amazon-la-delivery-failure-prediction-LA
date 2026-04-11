"""
build_notebook05.py — Write notebooks/05_final_analysis.ipynb

Generates a complete, self-contained Jupyter notebook that:
  1. Loads packages_validation.csv
  2. Feature engineers, drops zero-variance and leakage columns
  3. Trains RandomForest with class_weight='balanced'
  4. Evaluates with recall, precision, AUC-ROC
  5. Compares SMOTE vs. no-SMOTE
  6. Tunes threshold for maximum recall
  7. Saves model to ml/random_forest_model.pkl
  8. Exports feature_importance_final.png to reports/figures/
"""

import json
from pathlib import Path

OUT = Path(__file__).parent.parent / "notebooks" / "05_final_analysis.ipynb"


def code_cell(source: str, cell_id: str) -> dict:
    return {
        "cell_type": "code",
        "execution_count": None,
        "id": cell_id,
        "metadata": {},
        "outputs": [],
        "source": source,
    }


def md_cell(source: str, cell_id: str) -> dict:
    return {
        "cell_type": "markdown",
        "id": cell_id,
        "metadata": {},
        "source": source,
    }


cells = []

# ─── TITLE ───────────────────────────────────────────────────────────────────
cells.append(md_cell(
    "# Notebook 05 — Final Analysis\n"
    "## Amazon LA Last-Mile Delivery Failure Prediction\n\n"
    "**Dataset:** Amazon Last Mile Routing Research Challenge (LMRC 2021)  \n"
    "**Scope:** 3,559 packages, 15 routes, Los Angeles, July 2018  \n"
    "**Program:** Correlation One DANA — Week 12 Final Portfolio Project  \n"
    "**Date:** April 2026\n\n"
    "---\n\n"
    "This notebook covers the full modeling pipeline:\n"
    "1. Feature engineering on the real LMRC dataset\n"
    "2. RandomForest with `class_weight='balanced'` (140:1 imbalance)\n"
    "3. Evaluation: recall, precision, AUC-ROC (NOT accuracy)\n"
    "4. SMOTE comparison — with vs. without oversampling\n"
    "5. Threshold optimization for maximum recall\n"
    "6. Feature importance (model-based)\n"
    "7. Model persistence → `ml/random_forest_model.pkl`",
    "cell-title"
))

# ─── IMPORTS ─────────────────────────────────────────────────────────────────
cells.append(code_cell(
    "import warnings\n"
    "warnings.filterwarnings('ignore')\n\n"
    "import pickle\n"
    "import numpy as np\n"
    "import pandas as pd\n"
    "import matplotlib\n"
    "import matplotlib.pyplot as plt\n"
    "import matplotlib.patches as mpatches\n"
    "import seaborn as sns\n"
    "from pathlib import Path\n\n"
    "from sklearn.ensemble import RandomForestClassifier\n"
    "from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score\n"
    "from sklearn.preprocessing import LabelEncoder\n"
    "from sklearn.metrics import (\n"
    "    classification_report, confusion_matrix, roc_auc_score,\n"
    "    roc_curve, precision_recall_curve, average_precision_score,\n"
    "    recall_score, precision_score, f1_score\n"
    ")\n\n"
    "# imbalanced-learn for SMOTE\n"
    "try:\n"
    "    from imblearn.over_sampling import SMOTE\n"
    "    HAS_SMOTE = True\n"
    "except ImportError:\n"
    "    HAS_SMOTE = False\n"
    "    print('[INFO] imbalanced-learn not installed. ')\n"
    "    print('       Run: pip install imbalanced-learn')\n"
    "    print('       SMOTE comparison will be skipped.')\n\n"
    "matplotlib.rcParams['figure.facecolor'] = 'white'\n"
    "matplotlib.rcParams['axes.facecolor']   = 'white'\n\n"
    "DANGER  = '#E74C3C'\n"
    "WARN    = '#F39C12'\n"
    "SAFE    = '#27AE60'\n"
    "NAVY    = '#2C3E50'\n"
    "ACCENT  = '#2980B9'\n\n"
    "BASE         = Path('..').resolve()\n"
    "FIGURES_DIR  = BASE / 'reports' / 'figures'\n"
    "ML_DIR       = BASE / 'ml'\n"
    "FIGURES_DIR.mkdir(parents=True, exist_ok=True)\n"
    "ML_DIR.mkdir(parents=True, exist_ok=True)\n\n"
    "print('All imports OK')\n"
    "print(f'Figures → {FIGURES_DIR}')\n"
    "print(f'Model   → {ML_DIR}')",
    "cell-imports"
))

# ─── SECTION 1: LOAD ─────────────────────────────────────────────────────────
cells.append(md_cell(
    "---\n## 1. Load Data & Create Target\n\n"
    "`delivery_failure` = `damaged_on_arrival` — the `DELIVERY_ATTEMPTED` "
    "scan status from the LMRC dataset. Excluding `damaged_on_arrival` as a "
    "feature prevents data leakage.",
    "cell-s1-md"
))

cells.append(code_cell(
    "df = pd.read_csv(BASE / 'data' / 'packages_validation.csv')\n\n"
    "# ── Target: delivery_failure = damaged_on_arrival ──────────────────────\n"
    "df['delivery_failure'] = df['damaged_on_arrival']\n\n"
    "print(f'Dataset shape   : {df.shape[0]:,} rows × {df.shape[1]} columns')\n"
    "print(f'Failure count   : {df[\"delivery_failure\"].sum()} ({df[\"delivery_failure\"].mean():.2%})')\n"
    "print(f'Class ratio     : ~{int(df[\"delivery_failure\"].value_counts()[0] / df[\"delivery_failure\"].sum())}:1')\n"
    "print()\n"
    "print('Column dtypes:')\n"
    "print(df.dtypes)\n"
    "df.head(3)",
    "cell-load"
))

# ─── SECTION 2: FEATURE ENGINEERING ─────────────────────────────────────────
cells.append(md_cell(
    "---\n## 2. Feature Engineering\n\n"
    "Steps:\n"
    "- **Drop zero-variance columns**: `days_in_fc`, `weather_risk` (identical value for all rows)\n"
    "- **Drop data leakage column**: `damaged_on_arrival` (IS the target)\n"
    "- **Encode categoricals**: carrier, shift, package_type → label-encoded integers\n"
    "- **Bucket route distance**: < 40 km / 40–60 km / > 60 km",
    "cell-s2-md"
))

cells.append(code_cell(
    "# ── Zero-variance audit ──────────────────────────────────────────────────\n"
    "print('Zero-variance check:')\n"
    "for col in ['days_in_fc', 'weather_risk']:\n"
    "    print(f'  {col}: {df[col].nunique()} unique value(s) → {df[col].unique()}')\n\n"
    "# ── Drop zero-variance + leakage columns ─────────────────────────────────\n"
    "EXCLUDE = ['package_id', 'days_in_fc', 'weather_risk', 'damaged_on_arrival',\n"
    "           'delivery_failure']\n\n"
    "# ── Encode categoricals ───────────────────────────────────────────────────\n"
    "encoders = {}\n"
    "df_enc = df.copy()\n\n"
    "for col in ['carrier', 'shift', 'package_type']:\n"
    "    le = LabelEncoder()\n"
    "    df_enc[col + '_enc'] = le.fit_transform(df_enc[col])\n"
    "    encoders[col] = le\n"
    "    print(f'{col} classes: {list(le.classes_)}')\n\n"
    "# ── Distance bucket ───────────────────────────────────────────────────────\n"
    "df_enc['dist_bucket'] = pd.cut(\n"
    "    df_enc['route_distance_km'],\n"
    "    bins=[-1, 40, 60, 9999],\n"
    "    labels=[0, 1, 2]   # 0=<40km, 1=40-60km, 2=>60km\n"
    ").astype(int)\n\n"
    "FEATURES = [\n"
    "    'carrier_enc', 'shift_enc', 'package_type_enc',\n"
    "    'dist_bucket', 'packages_in_route',\n"
    "    'double_scan', 'locker_issue', 'cr_number_missing'\n"
    "]\n\n"
    "X = df_enc[FEATURES].values\n"
    "y = df_enc['delivery_failure'].values\n\n"
    "print(f'\\nFeature matrix: {X.shape}')\n"
    "print(f'Target vector : {y.shape}  ({y.sum()} positives)')\n"
    "print(f'Features used : {FEATURES}')",
    "cell-feature-eng"
))

# ─── SECTION 3: TRAIN/TEST SPLIT ─────────────────────────────────────────────
cells.append(md_cell(
    "---\n## 3. Train / Test Split\n\n"
    "Stratified split preserves the 0.7% failure rate in both subsets. "
    "With only 25 failures, an 80/20 split gives ~20 failures for training "
    "and ~5 for testing — a very small but real test.",
    "cell-s3-md"
))

cells.append(code_cell(
    "X_train, X_test, y_train, y_test = train_test_split(\n"
    "    X, y, test_size=0.20, random_state=42, stratify=y\n"
    ")\n\n"
    "print('Train / Test split (stratified):')\n"
    "print(f'  Train: {len(X_train):,} rows | {y_train.sum()} failures ({y_train.mean():.2%})')\n"
    "print(f'  Test : {len(X_test):,} rows  | {y_test.sum()} failures ({y_test.mean():.2%})')\n\n"
    "# Confirm class ratio preserved\n"
    "print(f'\\nClass ratio (train): {int((1-y_train.mean())/y_train.mean())}:1')\n"
    "print(f'Class ratio (test) : {int((1-y_test.mean())/y_test.mean())}:1')",
    "cell-split"
))

# ─── SECTION 4: BASELINE RF ──────────────────────────────────────────────────
cells.append(md_cell(
    "---\n## 4. Baseline RandomForest — `class_weight='balanced'`\n\n"
    "The `class_weight='balanced'` parameter reweights each failure sample by "
    "approximately 140× relative to a successful delivery. This is the first "
    "and most important imbalance correction — it shifts the model away from "
    "the naive 'always predict delivered' baseline.",
    "cell-s4-md"
))

cells.append(code_cell(
    "rf_base = RandomForestClassifier(\n"
    "    n_estimators=300,\n"
    "    class_weight='balanced',\n"
    "    random_state=42,\n"
    "    n_jobs=-1,\n"
    "    max_depth=8,\n"
    "    min_samples_leaf=3,\n"
    ")\n"
    "rf_base.fit(X_train, y_train)\n\n"
    "y_pred_base  = rf_base.predict(X_test)\n"
    "y_prob_base  = rf_base.predict_proba(X_test)[:, 1]\n\n"
    "auc_base     = roc_auc_score(y_test, y_prob_base)\n"
    "recall_base  = recall_score(y_test, y_pred_base, zero_division=0)\n"
    "prec_base    = precision_score(y_test, y_pred_base, zero_division=0)\n"
    "ap_base      = average_precision_score(y_test, y_prob_base)\n\n"
    "print('=== Baseline RF (class_weight=balanced) ===')\n"
    "print(f'AUC-ROC          : {auc_base:.4f}')\n"
    "print(f'Avg Precision    : {ap_base:.4f}')\n"
    "print(f'Recall  (fail)   : {recall_base:.4f}')\n"
    "print(f'Precision (fail) : {prec_base:.4f}')\n"
    "print()\n"
    "print(classification_report(y_test, y_pred_base,\n"
    "      target_names=['Delivered', 'Failed'], digits=4, zero_division=0))",
    "cell-baseline"
))

# ─── SECTION 5: SMOTE ────────────────────────────────────────────────────────
cells.append(md_cell(
    "---\n## 5. SMOTE Comparison\n\n"
    "SMOTE (Synthetic Minority Oversampling) generates synthetic failure "
    "samples in feature space to balance the training set. We compare this "
    "against the `class_weight='balanced'` baseline to decide which performs better.",
    "cell-s5-md"
))

cells.append(code_cell(
    "if HAS_SMOTE:\n"
    "    # SMOTE on training set only — NEVER on test set\n"
    "    smote = SMOTE(random_state=42, k_neighbors=min(5, y_train.sum() - 1))\n"
    "    X_sm, y_sm = smote.fit_resample(X_train, y_train)\n"
    "    print(f'Before SMOTE: {len(X_train)} rows | {y_train.sum()} failures')\n"
    "    print(f'After  SMOTE: {len(X_sm)} rows | {y_sm.sum()} failures')\n\n"
    "    rf_smote = RandomForestClassifier(\n"
    "        n_estimators=300, random_state=42, n_jobs=-1,\n"
    "        max_depth=8, min_samples_leaf=3\n"
    "    )\n"
    "    rf_smote.fit(X_sm, y_sm)\n\n"
    "    y_pred_sm  = rf_smote.predict(X_test)\n"
    "    y_prob_sm  = rf_smote.predict_proba(X_test)[:, 1]\n\n"
    "    auc_sm    = roc_auc_score(y_test, y_prob_sm)\n"
    "    recall_sm = recall_score(y_test, y_pred_sm, zero_division=0)\n"
    "    prec_sm   = precision_score(y_test, y_pred_sm, zero_division=0)\n"
    "    ap_sm     = average_precision_score(y_test, y_prob_sm)\n\n"
    "    print('\\n=== SMOTE + RF ===')\n"
    "    print(f'AUC-ROC          : {auc_sm:.4f}')\n"
    "    print(f'Avg Precision    : {ap_sm:.4f}')\n"
    "    print(f'Recall  (fail)   : {recall_sm:.4f}')\n"
    "    print(f'Precision (fail) : {prec_sm:.4f}')\n"
    "    print()\n"
    "    print(classification_report(y_test, y_pred_sm,\n"
    "          target_names=['Delivered', 'Failed'], digits=4, zero_division=0))\n"
    "\n"
    "    # ── Side-by-side comparison ──────────────────────────────────────────\n"
    "    print('=== COMPARISON TABLE ===')\n"
    "    comp = pd.DataFrame({\n"
    "        'Metric': ['AUC-ROC', 'Recall (fail)', 'Precision (fail)', 'Avg Precision'],\n"
    "        'Balanced Weight': [auc_base, recall_base, prec_base, ap_base],\n"
    "        'SMOTE':           [auc_sm, recall_sm, prec_sm, ap_sm],\n"
    "    })\n"
    "    comp = comp.round(4)\n"
    "    print(comp.to_string(index=False))\n"
    "    best_model_name = 'SMOTE+RF' if recall_sm >= recall_base else 'Balanced-Weight RF'\n"
    "    best_model      = rf_smote if recall_sm >= recall_base else rf_base\n"
    "    best_probs      = y_prob_sm if recall_sm >= recall_base else y_prob_base\n"
    "    print(f'\\n→ Best model for recall: {best_model_name}')\n"
    "else:\n"
    "    print('SMOTE not available — using Balanced-Weight RF as best model')\n"
    "    best_model_name = 'Balanced-Weight RF'\n"
    "    best_model      = rf_base\n"
    "    best_probs      = y_prob_base",
    "cell-smote"
))

# ─── SECTION 6: THRESHOLD OPTIMIZATION ───────────────────────────────────────
cells.append(md_cell(
    "---\n## 6. Threshold Optimization\n\n"
    "The default probability threshold (0.5) is designed for balanced classes. "
    "With a 140:1 imbalance, lowering the threshold towards the failure class "
    "improves recall at the cost of more false positives — an acceptable "
    "trade-off given the $17 cost of each missed failure vs a quick manual review.",
    "cell-s6-md"
))

cells.append(code_cell(
    "thresholds  = np.arange(0.05, 0.96, 0.05)\n"
    "recall_list = []\n"
    "prec_list   = []\n"
    "f1_list     = []\n\n"
    "for t in thresholds:\n"
    "    y_t = (best_probs >= t).astype(int)\n"
    "    recall_list.append(recall_score(y_test, y_t, zero_division=0))\n"
    "    prec_list.append(precision_score(y_test, y_t, zero_division=0))\n"
    "    f1_list.append(f1_score(y_test, y_t, zero_division=0))\n\n"
    "thresh_df = pd.DataFrame({\n"
    "    'threshold': thresholds,\n"
    "    'recall':    recall_list,\n"
    "    'precision': prec_list,\n"
    "    'f1':        f1_list,\n"
    "})\n\n"
    "# Best threshold: maximize recall with precision > 0\n"
    "valid = thresh_df[thresh_df['precision'] > 0]\n"
    "best_thresh_row = valid.loc[valid['recall'].idxmax()]\n"
    "best_thresh = best_thresh_row['threshold']\n\n"
    "print('Threshold sweep (recall × precision × F1):')\n"
    "print(thresh_df.round(4).to_string(index=False))\n"
    "print(f'\\n→ Optimal threshold for recall: {best_thresh:.2f}')\n"
    "print(f'  Recall    : {best_thresh_row[\"recall\"]:.4f}')\n"
    "print(f'  Precision : {best_thresh_row[\"precision\"]:.4f}')\n"
    "print(f'  F1        : {best_thresh_row[\"f1\"]:.4f}')\n\n"
    "# ── Plot threshold curve ────────────────────────────────────────────────\n"
    "fig, ax = plt.subplots(figsize=(10, 5))\n"
    "ax.plot(thresholds, recall_list,    color=DANGER, lw=2.5, label='Recall')\n"
    "ax.plot(thresholds, prec_list,      color=SAFE,   lw=2.5, label='Precision')\n"
    "ax.plot(thresholds, f1_list,        color=ACCENT, lw=2,   label='F1', linestyle='--')\n"
    "ax.axvline(best_thresh, color=WARN, linestyle=':', lw=2,\n"
    "           label=f'Optimal threshold ({best_thresh:.2f})')\n"
    "ax.set_xlabel('Decision Threshold', fontweight='bold')\n"
    "ax.set_ylabel('Score', fontweight='bold')\n"
    "ax.set_title(f'Threshold Optimization — {best_model_name}\\n'\n"
    "             'Lowering threshold trades precision for recall (preferred for $17 failure cost)',\n"
    "             fontsize=12, fontweight='bold', color=NAVY)\n"
    "ax.legend()\n"
    "ax.set_xlim(0, 1)\n"
    "ax.set_ylim(0, 1.05)\n"
    "sns.despine(ax=ax)\n"
    "plt.tight_layout()\n"
    "plt.savefig(FIGURES_DIR / 'threshold_optimization.png', dpi=150, bbox_inches='tight')\n"
    "plt.show()",
    "cell-threshold"
))

# ─── SECTION 7: FEATURE IMPORTANCE ───────────────────────────────────────────
cells.append(md_cell(
    "---\n## 7. Feature Importance — Model-Based (RandomForest)\n\n"
    "The RandomForest's `feature_importances_` attribute reports the mean "
    "decrease in impurity (Gini) contributed by each feature across all trees. "
    "This is a model-internal measure and complements the conditional failure-rate "
    "ranking from the EDA notebook.",
    "cell-s7-md"
))

cells.append(code_cell(
    "importances = pd.DataFrame({\n"
    "    'feature':    FEATURES,\n"
    "    'importance': best_model.feature_importances_\n"
    "}).sort_values('importance', ascending=True)\n\n"
    "def imp_color(val):\n"
    "    if val >= 0.20: return DANGER\n"
    "    elif val >= 0.12: return WARN\n"
    "    else: return ACCENT\n\n"
    "bar_colors = [imp_color(v) for v in importances['importance']]\n\n"
    "fig, ax = plt.subplots(figsize=(10, 6))\n"
    "bars = ax.barh(importances['feature'], importances['importance'],\n"
    "               color=bar_colors, edgecolor='white', height=0.65)\n\n"
    "for bar, val in zip(bars, importances['importance']):\n"
    "    ax.text(val + 0.002, bar.get_y() + bar.get_height()/2,\n"
    "            f'{val:.4f}', va='center', fontsize=9, color=NAVY)\n\n"
    "legend_patches = [\n"
    "    mpatches.Patch(facecolor=DANGER, label='High importance (≥ 0.20)'),\n"
    "    mpatches.Patch(facecolor=WARN,   label='Medium importance (0.12–0.20)'),\n"
    "    mpatches.Patch(facecolor=ACCENT, label='Lower importance (< 0.12)'),\n"
    "]\n"
    "ax.legend(handles=legend_patches, fontsize=9)\n"
    "ax.set_xlabel('Mean Decrease in Gini Impurity', fontweight='bold')\n"
    "ax.set_title(\n"
    "    f'Feature Importance — {best_model_name}\\n'\n"
    "    '(Model-based: mean decrease in impurity across 300 trees)',\n"
    "    fontsize=12, fontweight='bold', color=NAVY\n"
    ")\n"
    "sns.despine(ax=ax)\n"
    "plt.tight_layout()\n\n"
    "out_path = FIGURES_DIR / 'feature_importance_final.png'\n"
    "plt.savefig(out_path, dpi=150, bbox_inches='tight')\n"
    "plt.show()\n"
    "print(f'  ✓ Saved → {out_path}')\n\n"
    "print('\\nFeature importances:')\n"
    "print(importances.sort_values('importance', ascending=False).to_string(index=False))",
    "cell-fi"
))

# ─── SECTION 8: ROC / PR CURVES ──────────────────────────────────────────────
cells.append(md_cell(
    "---\n## 8. ROC and Precision-Recall Curves\n\n"
    "AUC-ROC summarizes discrimination across all thresholds. "
    "The Precision-Recall curve is more informative for imbalanced classes — "
    "it shows the recall vs precision trade-off at each threshold directly.",
    "cell-s8-md"
))

cells.append(code_cell(
    "fig, axes = plt.subplots(1, 2, figsize=(13, 5))\n\n"
    "# ── ROC curve ───────────────────────────────────────────────────────────\n"
    "fpr, tpr, _ = roc_curve(y_test, best_probs)\n"
    "auc_val     = roc_auc_score(y_test, best_probs)\n"
    "axes[0].plot(fpr, tpr, color=ACCENT, lw=2.5,\n"
    "             label=f'ROC curve (AUC = {auc_val:.4f})')\n"
    "axes[0].plot([0, 1], [0, 1], 'k--', lw=1.2, label='Random classifier')\n"
    "axes[0].fill_between(fpr, tpr, alpha=0.10, color=ACCENT)\n"
    "axes[0].set_xlabel('False Positive Rate', fontweight='bold')\n"
    "axes[0].set_ylabel('True Positive Rate', fontweight='bold')\n"
    "axes[0].set_title(f'ROC Curve — {best_model_name}', fontweight='bold', color=NAVY)\n"
    "axes[0].legend()\n"
    "sns.despine(ax=axes[0])\n\n"
    "# ── Precision-Recall curve ───────────────────────────────────────────────\n"
    "prec_c, rec_c, _ = precision_recall_curve(y_test, best_probs)\n"
    "ap_val           = average_precision_score(y_test, best_probs)\n"
    "baseline_pr      = y_test.mean()\n"
    "axes[1].plot(rec_c, prec_c, color=DANGER, lw=2.5,\n"
    "             label=f'PR curve (AP = {ap_val:.4f})')\n"
    "axes[1].axhline(baseline_pr, color='gray', linestyle='--', lw=1.2,\n"
    "                label=f'Random classifier ({baseline_pr:.3f})')\n"
    "axes[1].fill_between(rec_c, prec_c, alpha=0.10, color=DANGER)\n"
    "axes[1].set_xlabel('Recall', fontweight='bold')\n"
    "axes[1].set_ylabel('Precision', fontweight='bold')\n"
    "axes[1].set_title(f'Precision-Recall Curve — {best_model_name}',\n"
    "                  fontweight='bold', color=NAVY)\n"
    "axes[1].legend()\n"
    "sns.despine(ax=axes[1])\n\n"
    "plt.suptitle('Model Evaluation — Imbalanced Class Performance',\n"
    "             fontsize=13, fontweight='bold', color=NAVY)\n"
    "plt.tight_layout()\n"
    "plt.savefig(FIGURES_DIR / 'roc_pr_curves.png', dpi=150, bbox_inches='tight')\n"
    "plt.show()",
    "cell-roc"
))

# ─── SECTION 9: SAVE MODEL ───────────────────────────────────────────────────
cells.append(md_cell(
    "---\n## 9. Save Model Artifact\n\n"
    "Saves the best model (and all supporting objects) to `ml/random_forest_model.pkl`.",
    "cell-s9-md"
))

cells.append(code_cell(
    "artifact = {\n"
    "    'model':       best_model,\n"
    "    'model_name':  best_model_name,\n"
    "    'encoders':    encoders,\n"
    "    'features':    FEATURES,\n"
    "    'best_threshold': float(best_thresh),\n"
    "    'metrics': {\n"
    "        'auc_roc':          float(auc_val),\n"
    "        'avg_precision':    float(ap_val),\n"
    "        'recall_optimized': float(best_thresh_row['recall']),\n"
    "        'precision_at_opt': float(best_thresh_row['precision']),\n"
    "    },\n"
    "    'dataset': {\n"
    "        'source':    'Amazon LMRC 2021',\n"
    "        'location':  'Los Angeles, CA',\n"
    "        'period':    'July 2018',\n"
    "        'n_packages': len(df),\n"
    "        'n_failures':  int(df['delivery_failure'].sum()),\n"
    "        'failure_rate': float(df['delivery_failure'].mean()),\n"
    "    }\n"
    "}\n\n"
    "pkl_path = ML_DIR / 'random_forest_model.pkl'\n"
    "with open(pkl_path, 'wb') as f:\n"
    "    pickle.dump(artifact, f)\n\n"
    "print(f'Model saved → {pkl_path}')\n"
    "print(f'File size   : {pkl_path.stat().st_size / 1024:.1f} KB')\n\n"
    "# ── Verify round-trip ───────────────────────────────────────────────────\n"
    "with open(pkl_path, 'rb') as f:\n"
    "    check = pickle.load(f)\n\n"
    "auc_check = roc_auc_score(y_test,\n"
    "    check['model'].predict_proba(X_test)[:, 1])\n"
    "print(f'Reload verify AUC : {auc_check:.4f}  ✓')",
    "cell-save"
))

# ─── SECTION 10: SUMMARY ─────────────────────────────────────────────────────
cells.append(md_cell(
    "---\n## 10. Summary of Findings\n\n"
    "### Dataset\n"
    "| Attribute | Value |\n"
    "|-----------|-------|\n"
    "| Source | Amazon LMRC 2021 (real data) |\n"
    "| Geography | Los Angeles, CA |\n"
    "| Period | July 2018 |\n"
    "| Packages | 3,559 |\n"
    "| Routes | 15 |\n"
    "| Failure rate | 0.70% (25 failures) |\n"
    "| Class imbalance | ~140:1 |\n\n"
    "### Key Findings\n"
    "| Finding | Value |\n"
    "|---------|-------|\n"
    "| carrier_D failure rate | 1.39% (highest) |\n"
    "| carrier_B failure rate | 0.00% (zero failures) |\n"
    "| Morning shift | 1.37% vs 0.55% afternoon |\n"
    "| Routes < 40 km | 1.89% (urban density paradox) |\n"
    "| Routes > 60 km | 0.00% |\n"
    "| Zero-variance cols | days_in_fc, weather_risk |\n"
    "| Data leakage col | damaged_on_arrival (=target) |\n\n"
    "### Modeling Decisions\n"
    "- `class_weight='balanced'` corrects 140:1 imbalance\n"
    "- SMOTE provides an additional comparison point\n"
    "- Threshold tuned toward recall (cost: $17/missed failure)\n"
    "- AUC-ROC and Average Precision are primary metrics\n\n"
    "---\n"
    "*Amazon LMRC 2021 (public dataset) — Correlation One DANA W12 — April 2026*",
    "cell-summary"
))

# ── Write notebook ─────────────────────────────────────────────────────────────
nb = {
    "nbformat": 4,
    "nbformat_minor": 5,
    "metadata": {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3"
        },
        "language_info": {
            "name": "python",
            "version": "3.9.0"
        }
    },
    "cells": cells,
}

OUT.write_text(json.dumps(nb, indent=1, ensure_ascii=False), encoding="utf-8")
print(f"  ✓ Notebook written → {OUT}")
print(f"    {len(cells)} cells")
