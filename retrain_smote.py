"""
retrain_smote.py — SMOTE retraining + threshold optimisation
Trains on packages_train.csv, evaluates on packages_validation.csv.

Usage:
    python retrain_smote.py
"""

import pickle
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    roc_auc_score, recall_score,
    precision_score, average_precision_score,
)
from sklearn.preprocessing import LabelEncoder
from imblearn.over_sampling import SMOTE

PROJECT   = Path('C:/Users/User/Correlation one Logistc Predict agent/delivery-failure-prediction')
TRAIN_CSV = PROJECT / 'data' / 'packages_train.csv'
VAL_CSV   = PROJECT / 'data' / 'packages_validation.csv'
MODEL     = PROJECT / 'artifacts' / 'delivery_model.pkl'

TARGET = 'delivery_failed'

# ── Bins MUST match train_model.py and dashboard/_dist_bucket() ──────────────
DIST_BINS   = [0, 15, 30, 50, 70, 85]
DIST_LABELS = [0, 1, 2, 3, 4]

FEATURES = [
    'carrier_enc', 'shift_enc', 'package_type_enc', 'dist_bucket',
    'packages_in_route', 'double_scan', 'short_service_time', 'cr_number_missing',
]

# ── Load data ─────────────────────────────────────────────────────────────────
print('=' * 60)
print('  SMOTE + RF Retrain — Amazon LA Delivery Failure')
print('=' * 60)

train_df = pd.read_csv(TRAIN_CSV)
val_df   = pd.read_csv(VAL_CSV)

print(f'\nTrain : {len(train_df):,} rows | failures: {train_df[TARGET].sum()} ({train_df[TARGET].mean():.2%})')
print(f'Val   : {len(val_df):,} rows | failures: {val_df[TARGET].sum()} ({val_df[TARGET].mean():.2%})')

# ── Encode categoricals — one LabelEncoder per column ────────────────────────
encoders = {}
for col, enc_col in [
    ('carrier',      'carrier_enc'),
    ('shift',        'shift_enc'),
    ('package_type', 'package_type_enc'),
]:
    le = LabelEncoder()
    train_df[enc_col] = le.fit_transform(train_df[col])
    val_df[enc_col]   = le.transform(val_df[col])
    encoders[col] = le

# ── Bin route distance (consistent with train_model.py & dashboard.py) ────────
for df in [train_df, val_df]:
    df['dist_bucket'] = pd.cut(
        df['route_distance_km'], bins=DIST_BINS, labels=DIST_LABELS
    ).astype(int)

X_train = train_df[FEATURES]
y_train = train_df[TARGET]
X_test  = val_df[FEATURES]
y_test  = val_df[TARGET]

# ── SMOTE ─────────────────────────────────────────────────────────────────────
n_pos   = int(y_train.sum())
k_neigh = min(4, n_pos - 1)
print(f'\nSMOTE k_neighbors={k_neigh} (train positives={n_pos})')
smote         = SMOTE(random_state=42, k_neighbors=k_neigh)
X_res, y_res  = smote.fit_resample(X_train, y_train)
print(f'After SMOTE — train size: {len(X_res):,} | failures: {int(y_res.sum())}')

# ── Train RandomForest ────────────────────────────────────────────────────────
print('\nTraining RandomForest (n_estimators=200, max_depth=8)...')
rf = RandomForestClassifier(
    n_estimators=200,
    max_depth=8,
    class_weight='balanced',
    random_state=42,
    n_jobs=-1,
)
rf.fit(X_res, y_res)

# ── Evaluate raw scores ───────────────────────────────────────────────────────
probs = rf.predict_proba(X_test)[:, 1]
auc   = roc_auc_score(y_test, probs)
ap    = average_precision_score(y_test, probs)

print(f'\nAUC-ROC       : {auc:.4f}')
print(f'Avg Precision : {ap:.4f}')

# ── Threshold optimisation ────────────────────────────────────────────────────
print(f'\nThreshold optimisation (showing recall >= 70%):')
print(f'{"Threshold":>12} {"Recall":>8} {"Precision":>10} {"Flagged":>8}')
print('-' * 44)

# Strategy: among all thresholds that achieve recall >= 75%, pick the HIGHEST
# (most selective). Avoids flagging half the dataset at ultra-low thresholds.
MIN_RECALL     = 0.80   # target from instructor feedback
best_threshold = 0.50   # fallback
best_recall    = 0.0

for thresh in np.arange(0.02, 0.51, 0.01):
    preds   = (probs >= thresh).astype(int)
    recall  = recall_score(y_test, preds, zero_division=0)
    prec    = precision_score(y_test, preds, zero_division=0)
    flagged = int(preds.sum())

    if recall >= 0.70:
        marker = ' <-- target' if recall >= MIN_RECALL else ''
        print(f'{thresh:>12.2f} {recall:>8.2%} {prec:>10.4f} {flagged:>8}{marker}')

    # Keep updating as long as recall >= MIN_RECALL — last update = highest threshold
    if recall >= MIN_RECALL:
        best_recall    = recall
        best_threshold = thresh

print(f'\nBest threshold: {best_threshold:.2f}  ->  Recall: {best_recall:.2%}')

# ── Final evaluation at chosen threshold ──────────────────────────────────────
final_preds    = (probs >= best_threshold).astype(int)
final_recall   = recall_score(y_test, final_preds, zero_division=0)
final_prec     = precision_score(y_test, final_preds, zero_division=0)

print(f'\n=== FINAL MODEL METRICS ===')
print(f'AUC-ROC              : {auc:.4f}')
print(f'Avg Precision        : {ap:.4f}')
print(f'Recall @ {best_threshold:.2f}       : {final_recall:.2%}')
print(f'Precision @ {best_threshold:.2f}    : {final_prec:.4f}')
print(f'Threshold            : {best_threshold:.2f}')
print(f'Features             : {FEATURES}')

# ── Save bundle (encoders keyed by column name — dashboard compatible) ────────
bundle = {
    'model'          : rf,
    'encoders'       : encoders,          # keys: 'carrier', 'shift', 'package_type'
    'features'       : FEATURES,
    'best_threshold' : best_threshold,
    'metrics'        : {
        'auc_roc'       : round(auc, 4),
        'avg_precision' : round(ap, 4),
        'recall'        : round(final_recall, 4),
        'precision'     : round(final_prec, 4),
        'threshold'     : best_threshold,
    },
    'model_name' : 'SMOTE+RF',
    'dataset'    : {
        'source'    : 'Amazon LMRC 2021 — packages_train.csv / packages_validation.csv',
        'train_rows': len(train_df),
        'val_rows'  : len(val_df),
        'failures'  : int(train_df[TARGET].sum()),
        'city'      : 'Los Angeles',
        'period'    : 'July 2018',
    },
}

with open(MODEL, 'wb') as f:
    pickle.dump(bundle, f)

print(f'\n  Model saved -> {MODEL}')
print(f'  Bundle keys : {list(bundle.keys())}')
print(f'  Encoder keys: {list(encoders.keys())}')
print('=' * 60)
