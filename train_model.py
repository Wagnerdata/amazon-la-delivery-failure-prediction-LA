"""
train_model.py — Amazon LA Delivery Failure Prediction
RandomForest classifier with full evaluation artefacts.

Usage:
    python train_model.py
"""

import warnings
warnings.filterwarnings('ignore')

import pickle
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import (
    accuracy_score, classification_report, confusion_matrix,
    roc_auc_score, roc_curve, precision_recall_curve, average_precision_score,
)

# ── Paths ────────────────────────────────────────────────────────────────────
ROOT       = Path(__file__).parent
DATA_DIR   = ROOT / 'data'
ARTIFACTS  = ROOT / 'artifacts'
FIGURES    = ROOT / 'reports' / 'figures'

ARTIFACTS.mkdir(exist_ok=True)
FIGURES.mkdir(parents=True, exist_ok=True)

# ── Amazon brand colours ─────────────────────────────────────────────────────
AMAZON_ORANGE = '#FF9900'
AMAZON_NAVY   = '#232F3E'
AMAZON_BLUE   = '#146EB4'

plt.rcParams.update({
    'figure.facecolor': 'white',
    'axes.facecolor':   'white',
    'axes.edgecolor':   AMAZON_NAVY,
    'axes.labelcolor':  AMAZON_NAVY,
    'xtick.color':      AMAZON_NAVY,
    'ytick.color':      AMAZON_NAVY,
    'text.color':       AMAZON_NAVY,
    'font.family':      'sans-serif',
})

# ── Feature definitions ───────────────────────────────────────────────────────
CATEGORICAL_FEATURES = ['package_type', 'shift', 'carrier']
NUMERIC_FEATURES     = ['dist_bucket', 'packages_in_route']
BINARY_FEATURES      = ['double_scan', 'locker_issue', 'cr_number_missing']
TARGET               = 'damaged_on_arrival'  # Delivery Failure Proxy — NOT a feature

# route_distance_km is binned into an ordinal dist_bucket before modelling
DIST_BINS   = [0, 15, 30, 50, 70, 85]
DIST_LABELS = [0, 1, 2, 3, 4]          # 0=0–15 km … 4=71–85 km

ENCODED_FEATURES = [
    'carrier_enc',
    'shift_enc',
    'package_type_enc',
    'dist_bucket',
    'packages_in_route',
    'double_scan',
    'locker_issue',
    'cr_number_missing',
]


def load_and_encode(path: Path) -> tuple[pd.DataFrame, dict]:
    """Load CSV, encode categoricals, bin distance, return (df_encoded, encoders)."""
    df = pd.read_csv(path)
    encoders = {}

    for col, enc_col in [
        ('package_type', 'package_type_enc'),
        ('shift',        'shift_enc'),
        ('carrier',      'carrier_enc'),
    ]:
        le = LabelEncoder()
        df[enc_col] = le.fit_transform(df[col])
        encoders[col] = le

    # Bin route distance into ordinal integer buckets (0–4)
    df['dist_bucket'] = pd.cut(
        df['route_distance_km'], bins=DIST_BINS, labels=DIST_LABELS
    ).astype(int)

    return df, encoders


def plot_confusion_matrix(cm: np.ndarray, save_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(6, 5))
    sns.heatmap(
        cm, annot=True, fmt='d', cmap='YlOrBr',
        xticklabels=['Delivered', 'Failed'],
        yticklabels=['Delivered', 'Failed'],
        ax=ax, linewidths=0.5,
    )
    ax.set_title('Confusion Matrix — Validation Set', fontsize=14, fontweight='bold',
                 color=AMAZON_NAVY, pad=12)
    ax.set_ylabel('Actual', fontweight='bold')
    ax.set_xlabel('Predicted', fontweight='bold')
    plt.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"  Saved: {save_path}")


def plot_roc_curve(fpr: np.ndarray, tpr: np.ndarray, auc: float, save_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.plot(fpr, tpr, color=AMAZON_ORANGE, lw=2.5,
            label=f'ROC Curve  (AUC = {auc:.4f})')
    ax.plot([0, 1], [0, 1], 'k--', lw=1.2, label='Random classifier')
    ax.fill_between(fpr, tpr, alpha=0.12, color=AMAZON_ORANGE)
    ax.set_xlim([0.0, 1.0])
    ax.set_ylim([0.0, 1.02])
    ax.set_xlabel('False Positive Rate', fontweight='bold')
    ax.set_ylabel('True Positive Rate', fontweight='bold')
    ax.set_title('ROC Curve — Delivery Failure Classifier', fontsize=14,
                 fontweight='bold', color=AMAZON_NAVY, pad=12)
    ax.legend(loc='lower right', framealpha=0.9)
    plt.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"  Saved: {save_path}")


def plot_feature_importance(model: RandomForestClassifier,
                            feature_names: list, save_path: Path) -> None:
    importances = model.feature_importances_
    indices = np.argsort(importances)[::-1]
    sorted_names = [feature_names[i] for i in indices]
    sorted_vals  = importances[indices]

    colors = [AMAZON_ORANGE if v > np.median(importances) else AMAZON_BLUE
              for v in sorted_vals]

    fig, ax = plt.subplots(figsize=(9, 6))
    bars = ax.barh(sorted_names[::-1], sorted_vals[::-1], color=colors[::-1],
                   edgecolor='white', height=0.7)
    ax.set_xlabel('Feature Importance (Gini)', fontweight='bold')
    ax.set_title('Feature Importance — Random Forest\nDelivery Failure Prediction Model',
                 fontsize=13, fontweight='bold', color=AMAZON_NAVY, pad=12)

    for bar, val in zip(bars, sorted_vals[::-1]):
        ax.text(bar.get_width() + 0.002, bar.get_y() + bar.get_height() / 2,
                f'{val:.4f}', va='center', fontsize=9, color=AMAZON_NAVY)

    ax.set_xlim(0, sorted_vals.max() + 0.06)
    plt.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"  Saved: {save_path}")


def plot_precision_recall(precision, recall, avg_prec, save_path):
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.plot(recall, precision, color=AMAZON_BLUE, lw=2.5,
            label=f'PR Curve  (AP = {avg_prec:.4f})')
    ax.fill_between(recall, precision, alpha=0.12, color=AMAZON_BLUE)
    ax.set_xlabel('Recall', fontweight='bold')
    ax.set_ylabel('Precision', fontweight='bold')
    ax.set_title('Precision-Recall Curve — Delivery Failure Classifier',
                 fontsize=13, fontweight='bold', color=AMAZON_NAVY, pad=12)
    ax.legend(loc='upper right', framealpha=0.9)
    plt.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"  Saved: {save_path}")


def main():
    print("=" * 60)
    print("  Amazon LA — Delivery Failure Prediction Model")
    print("=" * 60)

    # ── Load data ────────────────────────────────────────────────────────────
    print("\n[1/4] Loading data...")
    train_df, encoders = load_and_encode(DATA_DIR / 'packages_train.csv')
    val_df,   _        = load_and_encode(DATA_DIR / 'packages_validation.csv')

    # Re-apply same encoders to validation set
    for col, enc_col in [
        ('package_type', 'package_type_enc'),
        ('shift',        'shift_enc'),
        ('carrier',      'carrier_enc'),
    ]:
        val_df[enc_col] = encoders[col].transform(val_df[col])

    X_train = train_df[ENCODED_FEATURES].values
    y_train = train_df[TARGET].values
    X_val   = val_df[ENCODED_FEATURES].values
    y_val   = val_df[TARGET].values

    print(f"  Train shape : {X_train.shape} | failure rate: {y_train.mean():.1%}")
    print(f"  Val shape   : {X_val.shape}   | failure rate: {y_val.mean():.1%}")

    # ── Train model ──────────────────────────────────────────────────────────
    print("\n[2/4] Training RandomForest (n_estimators=200, max_depth=8)...")
    model = RandomForestClassifier(
        n_estimators=200,
        max_depth=8,
        min_samples_split=10,
        min_samples_leaf=5,
        class_weight='balanced',
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_train, y_train)

    # ── Evaluate ─────────────────────────────────────────────────────────────
    print("\n[3/4] Evaluating model...")
    y_pred      = model.predict(X_val)
    y_prob      = model.predict_proba(X_val)[:, 1]
    auc         = roc_auc_score(y_val, y_prob)
    acc         = accuracy_score(y_val, y_pred)
    avg_prec    = average_precision_score(y_val, y_prob)

    print(f"\n  Accuracy      : {acc:.4f}")
    print(f"  AUC-ROC       : {auc:.4f}")
    print(f"  Avg Precision : {avg_prec:.4f}")
    print("\n  Classification Report:")
    print(classification_report(y_val, y_pred,
                                target_names=['Delivered', 'Failed'],
                                digits=4))

    # ── Save plots ───────────────────────────────────────────────────────────
    print("[4/4] Saving evaluation plots...")

    cm = confusion_matrix(y_val, y_pred)
    plot_confusion_matrix(cm, FIGURES / 'confusion_matrix.png')

    fpr, tpr, _ = roc_curve(y_val, y_prob)
    plot_roc_curve(fpr, tpr, auc, FIGURES / 'roc_curve.png')

    precision_vals, recall_vals, _ = precision_recall_curve(y_val, y_prob)
    plot_precision_recall(precision_vals, recall_vals, avg_prec,
                          FIGURES / 'precision_recall_curve.png')

    plot_feature_importance(model, ENCODED_FEATURES,
                            FIGURES / 'feature_importance.png')

    # ── Save artefact ────────────────────────────────────────────────────────
    artifact_path = ARTIFACTS / 'delivery_model.pkl'
    with open(artifact_path, 'wb') as f:
        pickle.dump({'model': model, 'encoders': encoders,
                     'features': ENCODED_FEATURES,
                     'metrics': {'auc': auc, 'accuracy': acc,
                                 'avg_precision': avg_prec}}, f)
    print(f"\n  Model artifact saved → {artifact_path}")
    print("\n" + "=" * 60)
    print(f"  Training complete. AUC-ROC: {auc:.4f}")
    print("=" * 60)


if __name__ == '__main__':
    main()
