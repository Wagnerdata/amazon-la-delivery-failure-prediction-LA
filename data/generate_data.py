"""
Synthetic Data Generator — Amazon Spain Logistics
Generates realistic delivery failure prediction datasets
enriched with real 2023 Barcelona open data:
  - Accident risk per neighbourhood (Guardia Urbana 2023)
  - Traffic congestion per shift (Barcelona traffic sensors 2023)
"""

import numpy as np
import pandas as pd
from pathlib import Path

OUTPUT_DIR    = Path(__file__).parent
PROCESSED_DIR = OUTPUT_DIR / 'processed'

# ── Load real Barcelona processed tables (built from raw open data) ──────────
_accident_risk_df  = pd.read_csv(PROCESSED_DIR / 'accident_risk_by_barrio.csv')
_traffic_cong_df   = pd.read_csv(PROCESSED_DIR / 'traffic_congestion_by_shift.csv')

# Barrio → accident_risk lookup
_BARRIOS     = _accident_risk_df['Nom_barri'].tolist()
_BARRIO_RISK = dict(zip(_accident_risk_df['Nom_barri'], _accident_risk_df['accident_risk']))

# Shift → congestion_level lookup  (morning/afternoon/night)
_SHIFT_CONGESTION = dict(zip(_traffic_cong_df['shift'], _traffic_cong_df['congestion_level']))


def generate_dataset(n_samples: int, seed: int = 42) -> pd.DataFrame:
    """Generate a synthetic logistics dataset with realistic failure correlations."""
    rng = np.random.default_rng(seed)

    # ── Categorical features ────────────────────────────────────────────────
    package_type = rng.choice(
        ['standard', 'high_value', 'fragile', 'locker', 'large'],
        size=n_samples,
        p=[0.45, 0.14, 0.14, 0.15, 0.12],
    )
    shift = rng.choice(
        ['morning', 'afternoon', 'night'],
        size=n_samples,
        p=[0.40, 0.40, 0.20],
    )
    carrier = rng.choice(
        ['carrier_A', 'carrier_B', 'carrier_C', 'carrier_D'],
        size=n_samples,
        p=[0.35, 0.25, 0.25, 0.15],
    )
    weather_risk = rng.choice(
        ['low', 'medium', 'high'],
        size=n_samples,
        p=[0.55, 0.30, 0.15],
    )

    # ── Numerical features ──────────────────────────────────────────────────
    route_distance_km = np.round(rng.uniform(2.0, 85.0, n_samples), 2)
    packages_in_route = rng.integers(15, 121, n_samples)
    days_in_fc = rng.integers(0, 13, n_samples)

    # ── Binary operational flags ────────────────────────────────────────────
    double_scan        = rng.binomial(1, 0.08, n_samples)
    locker_issue       = rng.binomial(1, 0.06, n_samples)
    damaged_on_arrival = rng.binomial(1, 0.04, n_samples)
    cr_number_missing  = rng.binomial(1, 0.10, n_samples)

    # ── Real Barcelona neighbourhood (uniform across 74 barrios) ────────────
    neighbourhood    = rng.choice(_BARRIOS, size=n_samples)
    accident_risk    = np.array([_BARRIO_RISK[b]      for b in neighbourhood])
    traffic_cong     = np.array([_SHIFT_CONGESTION[s] for s in shift])

    # ── Failure probability — business-logic correlations ───────────────────
    p = np.full(n_samples, 0.06, dtype=float)   # base rate ~6%

    # High-value + night shift → courier fatigue, less secure handoffs
    p += 0.06 * ((package_type == 'high_value') & (shift == 'night'))

    # carrier_D (Correos) + long distance → slower SLA, higher miss rate
    p += 0.084 * ((carrier == 'carrier_D') & (route_distance_km > 50))

    # Carrier D baseline underperformance
    p += 0.042 * (carrier == 'carrier_D')

    # Damaged packages almost always fail
    p += 0.33 * (damaged_on_arrival == 1)

    # Scan / locker operational errors
    p += 0.072 * (double_scan == 1)
    p += 0.06 * (locker_issue == 1)

    # Night shift baseline increase
    p += 0.03 * (shift == 'night')

    # Weather impact on delivery success
    p += 0.048 * (weather_risk == 'high')
    p += 0.018 * (weather_risk == 'medium')

    # Missing customer reference → address ambiguity
    p += 0.048 * (cr_number_missing == 1)

    # Fragile packages need extra care
    p += 0.024 * (package_type == 'fragile')

    # Long dwell time in FC suggests processing issues
    p += 0.0024 * days_in_fc

    # Dense routes → driver overload
    p += 0.00048 * (packages_in_route - 60).clip(min=0)

    # ── Real Barcelona risk factors (Guardia Urbana + traffic sensors 2023) ─
    p += 0.12 * (accident_risk == 'high')
    p += 0.06 * (accident_risk == 'medium')

    p += 0.10 * (traffic_cong == 'high')
    p += 0.05 * (traffic_cong == 'medium')

    p = np.clip(p, 0.0, 0.97)
    delivery_failed = rng.binomial(1, p, n_samples)

    df = pd.DataFrame({
        'package_id':           [f'PKG-ES-{i+1:07d}' for i in range(n_samples)],
        'package_type':         package_type,
        'shift':                shift,
        'carrier':              carrier,
        'route_distance_km':    route_distance_km,
        'packages_in_route':    packages_in_route,
        'double_scan':          double_scan,
        'locker_issue':         locker_issue,
        'damaged_on_arrival':   damaged_on_arrival,
        'weather_risk':         weather_risk,
        'cr_number_missing':    cr_number_missing,
        'days_in_fc':           days_in_fc,
        'neighbourhood':        neighbourhood,
        'accident_risk':        accident_risk,
        'traffic_congestion':   traffic_cong,
        'delivery_failed':      delivery_failed,
    })
    return df


if __name__ == '__main__':
    print("Generating Amazon Spain logistics datasets (enriched with real Barcelona data)...")

    train_df = generate_dataset(5000, seed=42)
    val_df   = generate_dataset(1500, seed=123)
    test_df  = generate_dataset(1000, seed=999)

    train_df.to_csv(OUTPUT_DIR / 'packages_train.csv',      index=False)
    val_df.to_csv(  OUTPUT_DIR / 'packages_validation.csv', index=False)
    test_df.to_csv( OUTPUT_DIR / 'packages_test.csv',       index=False)

    for name, df in [('Train', train_df), ('Validation', val_df), ('Test', test_df)]:
        rate = df['delivery_failed'].mean()
        print(f"  {name:12s} — {len(df):5,d} rows | failure rate: {rate:.1%}")

    print("\nNew real-data columns:")
    print("  accident_risk      :", train_df['accident_risk'].value_counts().to_dict())
    print("  traffic_congestion :", train_df['traffic_congestion'].value_counts().to_dict())
    print("\nData saved to data/")
