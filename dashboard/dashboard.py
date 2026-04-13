"""
Amazon LA — Delivery Failure Prediction Dashboard
Streamlit application with 3 operational pages.

Run with:  streamlit run dashboard/dashboard.py
"""

import pickle
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
import traceback

# ── Paths ────────────────────────────────────
ROOT        = Path(__file__).parent.parent
DATA_PATH   = ROOT / 'data' / 'packages_train.csv'
MODEL_PATH  = ROOT / 'artifacts' / 'delivery_model.pkl'

# ── Amazon brand colours ─────────────────────
AMAZON_ORANGE = '#FF9900'
AMAZON_NAVY   = '#232F3E'
AMAZON_BLUE   = '#146EB4'
AMAZON_GREEN  = '#067D62'
AMAZON_RED    = '#CC0C39'

# ── Page config ─────────────────────────────
st.set_page_config(
    page_title='Amazon LA — Delivery Failure Prediction',
    page_icon='📦',
    layout='wide',
    initial_sidebar_state='expanded',
)

# ── Main Script with Error Handling ──
try:

# ── Custom CSS — Amazon styling ────
st.markdown(f"""
<style>
    /* Main background */
    .stApp {{
        background-color: #f8f9fa;
    }}
    /* Header bar */
    .main-header {{
        background: linear-gradient(90deg, {AMAZON_NAVY} 0%, #37475a 100%);
        padding: 1.2rem 2rem;
        border-radius: 8px;
        margin-bottom: 1.5rem;
    }}
    .main-header h1 {{
        color: white;
        margin: 0;
        font-size: 1.6rem;
        font-weight: 700;
    }}
    .main-header p {{
        color: {AMAZON_ORANGE};
        margin: 0.2rem 0 0 0;
        font-size: 0.9rem;
    }}
    /* KPI cards */
    .kpi-card {{
        background: white;
        border-left: 4px solid {AMAZON_ORANGE};
        border-radius: 6px;
        padding: 1rem 1.2rem;
        box-shadow: 0 1px 4px rgba(0,0,0,0.08);
        text-align: center;
    }}
    .kpi-value {{
        font-size: 2rem;
        font-weight: 800;
        color: {AMAZON_NAVY};
    }}
    .kpi-label {{
        font-size: 0.78rem;
        color: #666;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }}
    /* Risk badge */
    .risk-high   {{ background:#fde8e8; color:{AMAZON_RED};    padding:0.6rem 1.2rem; border-radius:6px; font-size:1.1rem; font-weight:700; }}
    .risk-medium {{ background:#fff4e5; color:#b45309;          padding:0.6rem 1.2rem; border-radius:6px; font-size:1.1rem; font-weight:700; }}
    .risk-low    {{ background:#e8f5e9; color:{AMAZON_GREEN};   padding:0.6rem 1.2rem; border-radius:6px; font-size:1.1rem; font-weight:700; }}
    /* Section headers */
    .section-title {{
        color: {AMAZON_NAVY};
        font-weight: 700;
        font-size: 1.1rem;
        border-bottom: 2px solid {AMAZON_ORANGE};
        padding-bottom: 0.3rem;
        margin-bottom: 1rem;
    }}
</style>
""", unsafe_allow_html=True)


# ── Data & model loaders ─
@st.cache_data
def load_data():
    try:
        if not DATA_PATH.exists():
            st.sidebar.error(f"Data file not found: {DATA_PATH}")
            return None
        return pd.read_csv(DATA_PATH)
    except Exception as e:
        st.sidebar.error(f"Error loading data: {e}")
        return None

@st.cache_resource
def load_model():
    try:
        if not MODEL_PATH.exists():
            st.sidebar.error(f"Model file not found: {MODEL_PATH}")
            return None
        with open(MODEL_PATH, 'rb') as f:
            return pickle.load(f)
    except Exception as e:
        st.sidebar.error(f"Error loading model: {e}")
        return None


DIST_BINS = [0, 15, 30, 50, 70, 85]


def _dist_bucket(km: float) -> int:
    """Convert route distance (km) to ordinal bucket 0–4, matching train_model.py bins."""
    for i, edge in enumerate([15, 30, 50, 70]):
        if km <= edge:
            return i
    return 4


def predict_failure(artifact: dict, input_dict: dict) -> tuple[float, str]:
    """Score a single package using the 8 LMRC features. Returns (probability, risk_label).

    Features (order must match ENCODED_FEATURES in train_model.py):
        carrier_enc, shift_enc, package_type_enc, dist_bucket,
        packages_in_route, double_scan, short_service_time, cr_number_missing
    """
    model    = artifact['model']
    encoders = artifact['encoders']

    row = [
        encoders['carrier'].transform([input_dict['carrier']])[0],
        encoders['shift'].transform([input_dict['shift']])[0],
        encoders['package_type'].transform([input_dict['package_type']])[0],
        _dist_bucket(input_dict['route_distance_km']),
        input_dict['packages_in_route'],
        input_dict['double_scan'],
        input_dict['short_service_time'],
        input_dict['cr_number_missing'],
    ]

    prob = model.predict_proba([row])[0][1]

    if prob >= 0.50:
        risk = 'HIGH'
    elif prob >= 0.20:
        risk = 'MEDIUM'
    else:
        risk = 'LOW'

    return float(prob), risk


def make_bar_chart(x_labels, y_values, title, ylabel, color=AMAZON_ORANGE,
                   baseline=None, figsize=(8, 4.5)):
    """Reusable bar chart with Amazon styling."""
    fig, ax = plt.subplots(figsize=figsize)
    fig.patch.set_facecolor('white')
    ax.set_facecolor('white')
    bars = ax.bar(x_labels, y_values, color=color, edgecolor='white',
                   linewidth=0.4, width=0.6)
    if baseline is not None:
        ax.axhline(baseline, color=AMAZON_NAVY, linestyle='--', linewidth=1.8,
                    label=f'Overall avg ({baseline:.1f}%)', alpha=0.8)
        ax.legend(fontsize=9)
    for bar, val in zip(bars, y_values):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + max(y_values) * 0.015,
                f'{val:.1f}%', ha='center', fontsize=10, fontweight='bold', color=AMAZON_NAVY)
    ax.set_ylabel(ylabel, fontweight='bold', color=AMAZON_NAVY)
    ax.set_title(title, fontsize=12, fontweight='bold', color=AMAZON_NAVY, pad=10)
    ax.spines[['top', 'right']].set_visible(False)
    ax.tick_params(axis='x', colors=AMAZON_NAVY)
    ax.tick_params(axis='y', colors=AMAZON_NAVY)
    plt.tight_layout()
    return fig


# ═════════════════════════════════════════════
# SIDEBAR NAVIGATION
# ══════════════════════════════════════════════
st.sidebar.markdown(f"""
<div style='background:{AMAZON_NAVY}; padding:1rem; border-radius:8px; text-align:center;'>
    <span style='color:{AMAZON_ORANGE}; font-size:2rem;'>📦</span><br>
    <span style='color:white; font-weight:700; font-size:1.1rem;'>Amazon LA</span><br>
    <span style='color:#aaa; font-size:0.8rem;'>Logistics Analytics</span>
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown("---")
page = st.sidebar.radio(
    "Navigation",
    ["Operations Overview", "Package Risk Scoring", "Route Analysis"],
    label_visibility='collapsed',
)

st.sidebar.markdown("---")
st.sidebar.markdown(f"""
<div style='font-size:0.78rem; color:#666; padding:0.5rem;'>
    <b style='color:{AMAZON_NAVY};'>Data:</b> Amazon LA Last-Mile (Synthetic)<br>
    <b style='color:{AMAZON_NAVY};'>Model:</b> SMOTE+RF (AUC = 0.87, Recall = 87.5%)<br>
    <b style='color:{AMAZON_NAVY};'>Program:</b> Correlation One DANA W12
</div>
""", unsafe_allow_html=True)

# ── Load resources ──
df       = load_data()
artifact = load_model()

# ── System Status ──
st.sidebar.markdown("---")
with st.sidebar.expander("🛠️ System Status", expanded=True):
    if df is not None:
        st.success(f"Data Loaded: {len(df):,} rows")
        if 'delivery_failed' in df.columns:
            st.info(f"Target logic: Found")
        else:
            st.warning("Target logic: MISSING")
            st.code(df.columns.tolist())
    else:
        st.error("Data Loaded: FAILED")

    if artifact is not None:
        st.success("Model Loaded: READY")
    else:
        st.error("Model Loaded: FAILED")

# ══════════════════════════════════════
# PAGE 1 — OPERATIONS OVERVIEW
# ═══════════════════════════════════
if page == "Operations Overview":
    if df is None or artifact is None:
        st.error("Unable to load data or model. Check System Status in sidebar.")
        st.stop()

    # ── KPI Calculations ──
    total          = len(df)
    fail_rate      = df['delivery_failed'].mean() * 100
    n_failed       = df['delivery_failed'].sum()
    top_carrier    = (df.groupby('carrier')['delivery_failed'].mean()
                       .idxmax().replace('carrier_D', 'carrier_D (Local Courier)'))
    top_fail       = df.groupby('carrier')['delivery_failed'].mean().max() * 100
    cr_miss_rate   = df['cr_number_missing'].mean() * 100

    st.markdown(f"""
    <div class='main-header'>
        <h1>📦 Amazon LA — Last-Mile Operations Overview</h1>
        <p>Delivery Failure Analytics Dashboard | Training Dataset (n={total:,})</p>
    </div>
    """, unsafe_allow_html=True)

    # ── KPI Cards ──
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""
        <div class='kpi-card'>
            <div class='kpi-value'>{total:,}</div>
            <div class='kpi-label'>Total Packages</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class='kpi-card'>
            <div class='kpi-value' style='color:{AMAZON_RED};'>{fail_rate:.1f}%</div>
            <div class='kpi-label'>Delivery Failed Rate</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class='kpi-card'>
            <div class='kpi-value' style='color:{AMAZON_ORANGE};'>{top_fail:.1f}%</div>
            <div class='kpi-label'>Top Failing Carrier Rate</div>
        </div>""", unsafe_allow_html=True)
    with c4:
        st.markdown(f"""
        <div class='kpi-card'>
            <div class='kpi-value' style='color:{AMAZON_NAVY};'>{cr_miss_rate:.1f}%</div>
            <div class='kpi-label'>CR# Missing Rate</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Row 1: Carrier + Shift charts 
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("<div class='section-title'>Failure Rate by Carrier</div>",
                    unsafe_allow_html=True)
        carrier_stats = (df.groupby('carrier')['delivery_failed'].mean() * 100).sort_values()
        carrier_names = {'carrier_A': 'Amazon Lgx', 'carrier_B': 'Regional Hub',
                          'carrier_C': 'Express Hub', 'carrier_D': 'Local Courier'}
        labels  = [carrier_names[c] for c in carrier_stats.index]
        colors  = [AMAZON_RED if v > 25 else AMAZON_ORANGE if v > 18 else AMAZON_GREEN
                   for v in carrier_stats.values]
        fig = make_bar_chart(labels, carrier_stats.values.tolist(),
                              'Delivery Failure Rate by Carrier', 'Failure Rate (%)',
                              color=colors, baseline=fail_rate)
        st.pyplot(fig, use_container_width=True)
        plt.close()

    with col2:
        st.markdown("<div class='section-title'>Failure Rate by Delivery Shift</div>",
                    unsafe_allow_html=True)
        shift_order = ['morning', 'afternoon']
        shift_stats = (df.groupby('shift')['delivery_failed'].mean() * 100
                        ).reindex(shift_order)
        s_colors = [AMAZON_GREEN, AMAZON_ORANGE]
        fig2 = make_bar_chart(
            [s.capitalize() for s in shift_order],
            shift_stats.values.tolist(),
            'Failure Rate by Shift', 'Failure Rate (%)',
            color=s_colors, baseline=fail_rate,
        )
        st.pyplot(fig2, use_container_width=True)
        plt.close()

    # ── Row 2: Heatmap + Package Type ──
    col3, col4 = st.columns(2)

    with col3:
        st.markdown("<div class='section-title'>Carrier × Weather Risk Heatmap</div>",
                    unsafe_allow_html=True)
        pivot = (df.groupby(['carrier', 'weather_risk'])['delivery_failed']
                  .mean().unstack() * 100).reindex(columns=['low', 'medium', 'high'], fill_value=0)
        pivot.index = ['Amazon Lgx', 'Regional Hub', 'Express Hub', 'Local Courier']
        pivot.columns = ['Low', 'Medium', 'High']

        fig3, ax3 = plt.subplots(figsize=(7, 4.5))
        fig3.patch.set_facecolor('white')
        sns.heatmap(pivot, annot=True, fmt='.1f', cmap='YlOrRd', ax=ax3,
                     linewidths=0.5, linecolor='white',
                     cbar_kws={'label': 'Failure Rate (%)'},
                     annot_kws={'size': 12, 'weight': 'bold'})
        ax3.set_title('Failure Rate (%) — Carrier × Weather Risk',
                       fontsize=12, fontweight='bold', color=AMAZON_NAVY, pad=10)
        ax3.set_xlabel('Weather Risk', fontweight='bold')
        ax3.set_ylabel('Carrier', fontweight='bold')
        plt.tight_layout()
        st.pyplot(fig3, use_container_width=True)
        plt.close()

    with col4:
        st.markdown("<div class='section-title'>Failure Rate by Package Type</div>",
                    unsafe_allow_html=True)
        pkg_stats = (df.groupby('package_type')['delivery_failed'].mean() * 100
                      ).sort_values(ascending=False)
        pkg_labels = [p.replace('_', ' ').title() for p in pkg_stats.index]
        cmap = plt.cm.YlOrRd(np.linspace(0.3, 0.85, len(pkg_stats)))
        fig4 = make_bar_chart(pkg_labels, pkg_stats.values.tolist(),
                               'Failure Rate by Package Type', 'Failure Rate (%)',
                               color=cmap[::-1].tolist(), baseline=fail_rate)
        st.pyplot(fig4, use_container_width=True)
        plt.close()

    # ── Summary table ──
    st.markdown("---")
    st.markdown("<div class='section-title'>Operations Summary Table</div>",
                unsafe_allow_html=True)
    summary = df.groupby('carrier').agg(
        Packages=('delivery_failed', 'count'),
        Failures=('delivery_failed', 'sum'),
        Failure_Rate=('delivery_failed', 'mean'),
        Avg_Distance=('route_distance_km', 'mean'),
    ).round(3)
    summary['Failure_Rate'] = (summary['Failure_Rate'] * 100).map('{:.1f}%'.format)
    summary['Avg_Distance'] = summary['Avg_Distance'].map('{:.1f} km'.format)
    summary.index = summary.index.map({'carrier_A':'Amazon Lgx (A)', 'carrier_B':'Regional Hub (B)',
                                        'carrier_C':'Express Hub (C)', 'carrier_D':'Local Courier (D)'})
    st.dataframe(summary, use_container_width=True)


# ════════════════════════════════════════════════════════════════════════
# PAGE 2 — PACKAGE RISK SCORING
# ═════════════════════════════════════════════════════════════════════════════
elif page == "Package Risk Scoring":

    st.markdown(f"""
    <div class='main-header'>
        <h1>🎯 Package Risk Scoring Tool</h1>
        <p>Pre-dispatch failure probability scoring powered by RandomForest (AUC = 0.71)</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("Enter package attributes to predict delivery failure probability.")
    st.markdown("---")

    col_form, col_result = st.columns([1.2, 1])

    with col_form:
        st.markdown("#### Package Attributes")

        c1, c2 = st.columns(2)
        with c1:
            package_type = st.selectbox(
                "Package Type",
                ['standard', 'high_value'],
                help="Package category — Standard or High Value (LMRC data)",
            )
            shift = st.selectbox(
                "Delivery Shift",
                ['morning', 'afternoon'],
                help="Delivery shift (morning = lowest risk)",
            )
            carrier = st.selectbox(
                "Carrier",
                ['carrier_A', 'carrier_B', 'carrier_C', 'carrier_D'],
                format_func=lambda x: {
                    'carrier_A': 'carrier_A — Amazon Logistics',
                    'carrier_B': 'carrier_B — Regional Hub',
                    'carrier_C': 'carrier_C — Express Hub',
                    'carrier_D': 'carrier_D — Local Courier',
                }[x],
                help="carrier_D has highest failure rates on long routes",
            )

        with c2:
            route_distance_km = st.slider(
                "Route Distance (km)", 2, 85, 30,
                help="Longer routes correlate with higher failure rates",
            )
            packages_in_route = st.slider(
                "Packages in Route", 15, 120, 60,
                help="Total packages the driver must deliver",
            )

        st.markdown("#### Operational Flags")
        f1, f2 = st.columns(2)
        with f1:
            double_scan         = st.checkbox("Double Scan Detected", help="Scan error flag — package scanned twice")
            short_service_time  = st.checkbox("Short Service Time (<25s)", help="Planned service time under 25s — typical of locker/dense-urban stops")
        with f2:
            cr_number_missing = st.checkbox("CR Number Missing", help="Missing customer reference — address ambiguity")

        predict_btn = st.button("🔮 Predict Delivery Risk", type="primary", use_container_width=True)

    with col_result:
        st.markdown("#### Prediction Result")

        if predict_btn:
            input_dict = {
                'package_type':      package_type,
                'shift':             shift,
                'carrier':           carrier,
                'route_distance_km': route_distance_km,
                'packages_in_route': packages_in_route,
                'double_scan':          int(double_scan),
                'short_service_time':   int(short_service_time),
                'cr_number_missing': int(cr_number_missing),
            }

            prob, risk = predict_failure(artifact, input_dict)

            # Risk display
            risk_styles = {
                'HIGH':   ('risk-high',   '🔴 HIGH RISK',   'Manual review REQUIRED before dispatch'),
                'MEDIUM': ('risk-medium', '🟡 MEDIUM RISK', 'Supervisor review recommended'),
                'LOW':    ('risk-low',    '🟢 LOW RISK',    'Standard dispatch approved'),
            }
            css_class, label, action = risk_styles[risk]

            st.markdown(f"""
            <div class='{css_class}' style='text-align:center; margin:1rem 0;'>
                {label}
            </div>
            """, unsafe_allow_html=True)

            # Probability gauge
            st.metric("Failure Probability", f"{prob:.1%}")
            st.progress(float(prob))
            st.info(f"**Recommended Action**: {action}")

            # Probability gauge chart
            fig, ax = plt.subplots(figsize=(5, 3))
            fig.patch.set_facecolor('white')
            bar_color = AMAZON_RED if prob >= 0.50 else AMAZON_ORANGE if prob >= 0.20 else AMAZON_GREEN
            ax.barh(['Failure Probability'], [prob], color=bar_color, height=0.4,
                     edgecolor='white')
            ax.barh(['Failure Probability'], [1 - prob], left=[prob],
                     color='#e0e0e0', height=0.4, edgecolor='white')
            ax.axvline(0.20, color=AMAZON_NAVY, linestyle='--', linewidth=1.5, alpha=0.6, label='Low/Med (20%)')
            ax.axvline(0.50, color=AMAZON_RED,  linestyle='--', linewidth=1.5, alpha=0.6, label='Med/High (50%)')
            ax.set_xlim(0, 1)
            ax.set_xlabel('Probability', fontweight='bold', color=AMAZON_NAVY)
            ax.set_title(f'Risk Probability: {prob:.1%}', fontweight='bold', color=AMAZON_NAVY)
            ax.legend(fontsize=8, loc='lower right')
            ax.spines[['top', 'right']].set_visible(False)
            plt.tight_layout()
            st.pyplot(fig, use_container_width=True)
            plt.close()

            # Risk factor summary
            risk_factors = []
            if carrier == 'carrier_D' and route_distance_km > 50:
                risk_factors.append("🔴 Local Courier + long route (>50km) — high-risk combination")
            if shift == 'night':
                risk_factors.append("🟠 Night shift — elevated failure baseline")
            if double_scan:
                risk_factors.append("🟠 Double scan detected — operational error flag")
            if short_service_time:
                risk_factors.append("🟠 Short service time (<25s) — locker/dense-urban stop")
            if cr_number_missing:
                risk_factors.append("🟡 CR number missing — address ambiguity")
            if route_distance_km > 70:
                risk_factors.append("🟡 Long route (>70km) — elevated distance bucket")

            if risk_factors:
                st.markdown("**Risk Factors Detected:**")
                for rf in risk_factors:
                    st.markdown(f"- {rf}")
            else:
                st.success("No specific risk factors detected. Low-risk package.")
        else:
            st.markdown("""
            <div style='background:#f0f4ff; padding:2rem; border-radius:8px; text-align:center; color:#666;'>
                <h3 style='color:#232F3E;'>Ready to score</h3>
                <p>Configure the package attributes on the left and click <b>Predict Delivery Risk</b></p>
            </div>
            """, unsafe_allow_html=True)

    # Model performance callout
    st.markdown("---")
    st.markdown("#### Model Performance Reference")
    mc1, mc2, mc3, mc4 = st.columns(4)
    mc1.metric("AUC-ROC", "0.8728", "vs 0.50 random baseline")
    mc2.metric("Recall (@ 0.16)", "87.5%", "of failures detected")
    mc3.metric("Threshold", "0.16", "tuned for recall >= 80%")
    mc4.metric("Avg Precision", "0.2823", "PR-AUC score")


# ═════════════════════════════════════════════════════════════════════════════
# PAGE 3 — ROUTE ANALYSIS
# ════════════════════════════════════════════════════════════════════════════
elif page == "Route Analysis":

    st.markdown(f"""
    <div class='main-header'>
        <h1>🗺️ Route Performance Analysis</h1>
        <p>Route distance vs failure rate exploration | Filter by carrier and risk indicators</p>
    </div>
    """, unsafe_allow_html=True)

    # ── Filters ────────────────────────────────────────────────────────────
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        carrier_filter = st.multiselect(
            "Filter by Carrier",
            options=['carrier_A', 'carrier_B', 'carrier_C', 'carrier_D'],
            default=['carrier_A', 'carrier_B', 'carrier_C', 'carrier_D'],
            format_func=lambda x: {'carrier_A':'Amazon Lgx','carrier_B':'Reg. Hub',
                                    'carrier_C':'Exp. Hub','carrier_D':'Local Courier'}[x],
        )
    with col_f2:
        shift_filter = st.multiselect(
            "Filter by Shift",
            options=['morning', 'afternoon'],
            default=['morning', 'afternoon'],
        )
    with col_f3:
        show_failed_only = st.checkbox("Show delivery failures only", value=False)

    # Apply filters
    filtered = df[df['carrier'].isin(carrier_filter) & df['shift'].isin(shift_filter)]
    if show_failed_only:
        filtered = filtered[filtered['delivery_failed'] == 1]

    st.markdown(f"**Showing {len(filtered):,} packages** after filters applied.")
    st.markdown("---")

    # ── Scatter: Distance vs packages_in_route, coloured by outcome ──────────
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("<div class='section-title'>Distance vs Route Load — by Outcome</div>",
                    unsafe_allow_html=True)
        fig, ax = plt.subplots(figsize=(7, 5))
        fig.patch.set_facecolor('white')
        ax.set_facecolor('white')
        for outcome, color, label, alpha in [(0, AMAZON_BLUE, 'Delivered', 0.35),
                                               (1, AMAZON_ORANGE, 'Delivery Failed', 0.7)]:
            subset = filtered[filtered['delivery_failed'] == outcome]
            ax.scatter(subset['route_distance_km'], subset['packages_in_route'],
                        c=color, label=label, alpha=alpha, s=15, edgecolors='none')
        ax.set_xlabel('Route Distance (km)', fontweight='bold')
        ax.set_ylabel('Packages in Route', fontweight='bold')
        ax.set_title('Route Distance vs Load by Delivery Outcome',
                      fontsize=11, fontweight='bold', color=AMAZON_NAVY)
        ax.legend(markerscale=2)
        ax.spines[['top', 'right']].set_visible(False)
        plt.tight_layout()
        st.pyplot(fig, use_container_width=True)
        plt.close()

    with col2:
        st.markdown("<div class='section-title'>Failure Rate by Distance Bucket</div>",
                    unsafe_allow_html=True)
        filtered_copy = filtered.copy()
        bins = [0, 15, 30, 50, 70, 85]
        labels_bins = ['0–15km', '16–30km', '31–50km', '51–70km', '71–85km']
        filtered_copy['dist_bucket'] = pd.cut(filtered_copy['route_distance_km'],
                                               bins=bins, labels=labels_bins)
        bucket_fail = (filtered_copy.groupby('dist_bucket', observed=True)['delivery_failed']
                        .agg(['mean', 'count']).reset_index())

        fig2, ax2 = plt.subplots(figsize=(7, 5))
        fig2.patch.set_facecolor('white')
        ax2.set_facecolor('white')
        colors = [AMAZON_GREEN if v < 0.18 else AMAZON_ORANGE if v < 0.25 else AMAZON_RED
                   for v in bucket_fail['mean']]
        bars = ax2.bar(bucket_fail['dist_bucket'].astype(str),
                        bucket_fail['mean'] * 100, color=colors, edgecolor='white', width=0.6)
        ax2.set_xlabel('Distance Bucket', fontweight='bold')
        ax2.set_ylabel('Failure Rate (%)', fontweight='bold')
        ax2.set_title('Failure Rate by Route Distance Bucket',
                       fontsize=11, fontweight='bold', color=AMAZON_NAVY)
        ax2.spines[['top', 'right']].set_visible(False)
        for bar, (_, row) in zip(bars, bucket_fail.iterrows()):
            ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.2,
                      f'{row["mean"]*100:.1f}%\n(n={row["count"]:,})',
                      ha='center', fontsize=9, fontweight='bold', color=AMAZON_NAVY)
        plt.tight_layout()
        st.pyplot(fig2, use_container_width=True)
        plt.close()

    # ── Carrier performance comparison ─────────────────────────────────────────
    st.markdown("---")
    st.markdown("<div class='section-title'>Carrier Performance — Selected Filters</div>",
                unsafe_allow_html=True)

    carrier_perf = filtered.groupby('carrier').agg(
        Packages=('delivery_failed', 'count'),
        Failures=('delivery_failed', 'sum'),
        Failure_Rate=('delivery_failed', 'mean'),
        Avg_Distance_km=('route_distance_km', 'mean'),
        Avg_Route_Load=('packages_in_route', 'mean'),
    ).reset_index()

    carrier_perf['Failure_Rate_Pct'] = (carrier_perf['Failure_Rate'] * 100).round(1)
    carrier_perf['carrier'] = carrier_perf['carrier'].map({
        'carrier_A': 'Amazon Logistics (A)', 'carrier_B': 'Regional Hub (B)',
        'carrier_C': 'Express Hub (C)', 'carrier_D': 'Local Courier (D)',
    })
    carrier_perf = carrier_perf.drop('Failure_Rate', axis=1).rename(
        columns={'carrier': 'Carrier', 'Failure_Rate_Pct': 'Failure Rate (%)',
                 'Avg_Distance_km': 'Avg Distance (km)', 'Avg_Route_Load': 'Avg Route Load'}
    )

    carrier_perf['Avg Distance (km)'] = carrier_perf['Avg Distance (km)'].round(1)
    carrier_perf['Avg Route Load']    = carrier_perf['Avg Route Load'].round(1)

    st.dataframe(carrier_perf.set_index('Carrier'), use_container_width=True)

    # ── Raw data viewer ────────────────────────────────────────────────────────
    st.markdown("---")
    with st.expander("View Raw Data (filtered)", expanded=False):
        st.dataframe(filtered.reset_index(drop=True), use_container_width=True,
                      height=400)
        st.caption(f"Showing {len(filtered):,} rows. Download from the dataframe toolbar.")

except Exception as main_err:
    st.error("🚨 Critical Error during app startup!")
    st.code(traceback.format_exc())
    st.info("Check System Status or contact the developer.")
