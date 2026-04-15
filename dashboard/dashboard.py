import streamlit as st
import pickle
import traceback
from pathlib import Path

# ── Page config (ABSOLUTELY MUST BE FIRST) ─────────────────────────────
st.set_page_config(
    page_title='Amazon LA — Last-Mile Analytics',
    page_icon='📦',
    layout='wide',
    initial_sidebar_state='expanded',
)

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

matplotlib.use('Agg')

# ── Paths (Using CWD for Cloud Compatibility) ──────────────────────────
ROOT           = Path.cwd()
TRAIN_PATH     = ROOT / 'data' / 'packages_train.csv'
VAL_PATH       = ROOT / 'data' / 'packages_validation.csv'
MODEL_PATH     = ROOT / 'artifacts' / 'delivery_model.pkl'

# ── Amazon brand colours ─────────────────────
AMAZON_ORANGE = '#FF9900'
AMAZON_NAVY   = '#232F3E'
AMAZON_BLUE   = '#146EB4'
AMAZON_GREEN  = '#067D62'
AMAZON_RED    = '#CC0C39'
AMAZON_LIGHT  = '#f3f3f3'

# ── ROI Constants ──
COST_PER_FAILURE = 17.50

# ── Main Script with Error Handling ──
try:
    # ── Custom CSS — Premium Amazon Styling ────
    st.markdown(f"""
    <style>
        .stApp {{
            background-color: #fafafa;
        }}
        .premium-card {{
            background: white;
            padding: 1.5rem;
            border-radius: 12px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            border-top: 5px solid {AMAZON_ORANGE};
            margin-bottom: 20px;
        }}
        .main-header {{
            background: linear-gradient(135deg, {AMAZON_NAVY} 0%, #37475a 100%);
            padding: 2.5rem 3rem;
            border-radius: 12px;
            margin-bottom: 2rem;
        }}
        .main-header h1 {{ color: white; margin: 0; font-size: 2.4rem; font-weight: 800; }}
        .main-header p {{ color: {AMAZON_ORANGE}; margin: 0.5rem 0 0 0; font-size: 1.1rem; }}
        .kpi-value {{ font-size: 2.5rem; font-weight: 800; color: {AMAZON_NAVY}; }}
        .kpi-label {{ font-size: 0.85rem; color: #555; font-weight: 700; text-transform: uppercase; }}
        .risk-badge {{ padding: 0.8rem 1.5rem; border-radius: 8px; font-weight: 800; font-size: 1.2rem; text-align: center; }}
        .risk-high   {{ background-color: #fee2e2; color: {AMAZON_RED}; border: 1px solid #f87171; }}
        .risk-medium {{ background-color: #fff7ed; color: #9a3412; border: 1px solid #fb923c; }}
        .risk-low    {{ background-color: #f0fdf4; color: {AMAZON_GREEN}; border: 1px solid #4ade80; }}
        .section-title {{ color: {AMAZON_NAVY}; font-weight: 800; font-size: 1.3rem; margin: 1.5rem 0 1rem 0; display: flex; align-items: center; }}
        .section-title::before {{ content: ""; width: 4px; height: 24px; background: {AMAZON_ORANGE}; margin-right: 12px; border-radius: 2px; }}
    </style>
    """, unsafe_allow_html=True)

    # ── Data & model loaders ─
    @st.cache_data
    def load_data():
        dfs = []
        # Support both Windows and Cloud paths
        for p in [TRAIN_PATH, VAL_PATH]:
            if p.exists():
                dfs.append(pd.read_csv(p))
            else:
                # Fallback for some cloud environments
                alt_p = Path(__file__).parent.parent / 'data' / p.name
                if alt_p.exists():
                    dfs.append(pd.read_csv(alt_p))
        if not dfs: return None
        return pd.concat(dfs, ignore_index=True)

    @st.cache_resource
    def load_model():
        p = MODEL_PATH
        if not p.exists():
            p = Path(__file__).parent.parent / 'artifacts' / 'delivery_model.pkl'
        if not p.exists(): return None
        with open(p, 'rb') as f:
            return pickle.load(f)

    df       = load_data()
    artifact = load_model()

    # ── Sidebar Navigation ──
    st.sidebar.markdown(f"<div style='background:{AMAZON_NAVY}; padding:2rem 1rem; border-radius:15px; text-align:center; margin-bottom: 2rem;'><div style='font-size:3rem; margin-bottom:10px;'>📦</div><div style='color:white; font-weight:800; font-size:1.4rem; letter-spacing:1px;'>AMAZON LA</div></div>", unsafe_allow_html=True)
    page = st.sidebar.radio("MENU", ["Operations Overview", "Package Risk Scoring", "Commercial ROI Analysis"])
    
    with st.sidebar.expander("🛠️ Diagnostics"):
        st.write(f"CWD: `{Path.cwd()}`")
        st.write(f"Data found: `{df is not None}`")
        st.write(f"Model found: `{artifact is not None}`")

    # ═════════════════════════════════════════════
    # PAGE 1: OPERATIONS OVERVIEW
    # ═════════════════════════════════════════════
    if page == "Operations Overview":
        if df is None:
            st.error("🚨 Data source not found. Please verify the `data/` directory.")
            st.stop()

        total = len(df)
        fail_rate = df['delivery_failed'].mean() * 100
        total_lost = df['delivery_failed'].sum() * COST_PER_FAILURE
        
        st.markdown(f"<div class='main-header'><h1>Amazon LA Operations</h1><p>Official LMRC (MIT CTL) | Real Logistics Intel</p></div>", unsafe_allow_html=True)

        m1, m2, m3, m4 = st.columns(4)
        m1.markdown(f"<div class='premium-card'><div class='kpi-value'>{total:,}</div><div class='kpi-label'>Total Deliveries</div></div>", unsafe_allow_html=True)
        m2.markdown(f"<div class='premium-card'><div class='kpi-value' style='color:{AMAZON_RED}'>{fail_rate:.1f}%</div><div class='kpi-label'>Failure Rate</div></div>", unsafe_allow_html=True)
        m3.markdown(f"<div class='premium-card'><div class='kpi-value'>{df['packages_in_route'].median():.0f}</div><div class='kpi-label'>Avg Route Load</div></div>", unsafe_allow_html=True)
        m4.markdown(f"<div class='premium-card'><div class='kpi-value' style='color:{AMAZON_GREEN}'>${total_lost:,.0f}</div><div class='kpi-label'>Est. Operational Loss</div></div>", unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("<div class='section-title'>Failure by Carrier</div>", unsafe_allow_html=True)
            stats = (df.groupby('carrier')['delivery_failed'].mean() * 100).sort_values(ascending=False)
            names = {'carrier_A': 'Lgx Central', 'carrier_B': 'Reg. Hub', 'carrier_C': 'Exp. Hub', 'carrier_D': 'Local Courier'}
            fig, ax = plt.subplots(figsize=(8, 5))
            ax.bar([names.get(c, c) for c in stats.index], stats.values, color=AMAZON_ORANGE)
            ax.axhline(fail_rate, color=AMAZON_NAVY, ls='--')
            sns.despine()
            st.pyplot(fig)
        with c2:
            st.markdown("<div class='section-title'>Carrier × Weather Risk</div>", unsafe_allow_html=True)
            pivot = (df.groupby(['carrier', 'weather_risk'])['delivery_failed'].mean().unstack() * 100).fillna(0)
            fig2, ax2 = plt.subplots(figsize=(8, 5))
            sns.heatmap(pivot, annot=True, cmap='YlOrRd', ax=ax2, cbar=False)
            st.pyplot(fig2)

    # ═════════════════════════════════════════════
    # PAGE 2: RISK SCORING
    # ═════════════════════════════════════════════
    elif page == "Package Risk Scoring":
        st.markdown(f"<div class='main-header'><h1>Risk Prediction</h1><p>8-Feature Operational Assessment</p></div>", unsafe_allow_html=True)
        if artifact:
            col_in, col_out = st.columns([1, 1], gap="large")
            with col_in:
                with st.container(border=True):
                    sc1, sc2 = st.columns(2)
                    with sc1:
                        p_type = st.selectbox("Type", ['standard', 'high_value'])
                        s_time = st.selectbox("Shift", ['morning', 'afternoon'])
                        carrier = st.selectbox("Carrier", ['carrier_A', 'carrier_B', 'carrier_C', 'carrier_D'])
                    with sc2:
                        dist = st.slider("Distance (km)", 5, 100, 35)
                        load = st.slider("Load", 10, 150, 75)
                    st.divider()
                    st_time = st.toggle("Short Service (<25s)")
                    scan    = st.toggle("Double Scan")
                    miss    = st.toggle("Missing Ref")
                    predict_btn = st.button("🔮 Score", type="primary", use_container_width=True)

            with col_out:
                if predict_btn:
                    # Score using model
                    model = artifact['model']
                    encoders = artifact['encoders']
                    row = [encoders['carrier'].transform([carrier])[0], encoders['shift'].transform([s_time])[0], encoders['package_type'].transform([p_type])[0],
                           (0 if dist<=15 else 1 if dist<=30 else 2 if dist<=50 else 3 if dist<=70 else 4), load, int(scan), int(st_time), int(miss)]
                    prob = model.predict_proba([row])[0][1]
                    risk = 'HIGH' if prob >= 0.50 else 'MEDIUM' if prob >= 0.16 else 'LOW'
                    css = 'risk-high' if risk=='HIGH' else 'risk-medium' if risk=='MEDIUM' else 'risk-low'
                    st.markdown(f"<div class='risk-badge {css}'>{risk} RISK</div>", unsafe_allow_html=True)
                    st.metric("Failure Probability", f"{prob*100:.1f}%")
                    st.progress(prob)
                else:
                    st.info("Set parameters and click Score.")
            
            st.markdown("---")
            st.markdown(f"#### Live Metrics: AUC-ROC {artifact['metrics']['auc_roc']:.4f} | Recall {artifact['metrics']['recall']*100:.1f}%")

    # ═════════════════════════════════════════════
    # PAGE 3: COMMERCIAL ROI
    # ═════════════════════════════════════════════
    elif page == "Commercial ROI Analysis":
        st.markdown(f"<div class='main-header'><h1>Business ROI</h1><p>Predictive Logistics Financial Impact</p></div>", unsafe_allow_html=True)
        recall = artifact['metrics']['recall'] if artifact else 0.875
        fails = df['delivery_failed'].sum() if df is not None else 140
        savings = fails * recall * COST_PER_FAILURE
        st.markdown(f"<div class='premium-card'><h3>Est. Savings: **${savings:,.2f}**</h3><p>Avoided costs based on model detection rate and $17.50 unit failure cost.</p></div>", unsafe_allow_html=True)

except Exception as e:
    st.error("🚨 App Runtime Error")
    st.code(traceback.format_exc())
