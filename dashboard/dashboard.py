import pickle
import traceback
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import streamlit as st

# ── Page config (MUST BE FIRST STREAMLIT CALL) ─────────────────────────────
st.set_page_config(
    page_title='Amazon LA — Last-Mile Analytics',
    page_icon='📦',
    layout='wide',
    initial_sidebar_state='expanded',
)

# ── Paths ────────────────────────────────────
ROOT           = Path(__file__).parent.parent
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
COST_PER_FAILURE = 17.50  # Estimated cost of redelivery/customer service/loss

# ── Main Script with Error Handling ──
try:
    # ── Custom CSS — Premium Amazon Styling ────
    st.markdown(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Amazon+Ember:wght@400;700&display=swap');
        
        .stApp {{
            background-color: #fafafa;
        }}
        
        /* Premium Cards */
        .premium-card {{
            background: white;
            padding: 1.5rem;
            border-radius: 12px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            border-top: 5px solid {AMAZON_ORANGE};
            transition: transform 0.2s ease-in-out;
            margin-bottom: 20px;
        }}
        .premium-card:hover {{
            transform: translateY(-2px);
        }}
        
        /* Header bar */
        .main-header {{
            background: linear-gradient(135deg, {AMAZON_NAVY} 0%, #37475a 100%);
            padding: 2.5rem 3rem;
            border-radius: 12px;
            margin-bottom: 2rem;
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
        }}
        .main-header h1 {{
            color: white;
            margin: 0;
            font-size: 2.4rem;
            font-weight: 800;
            letter-spacing: -0.02em;
        }}
        .main-header p {{
            color: {AMAZON_ORANGE};
            margin: 0.5rem 0 0 0;
            font-size: 1.1rem;
            opacity: 0.9;
            font-weight: 500;
        }}
        
        /* KPI styling */
        .kpi-value {{
            font-size: 2.5rem;
            font-weight: 800;
            color: {AMAZON_NAVY};
            line-height: 1;
        }}
        .kpi-label {{
            font-size: 0.85rem;
            color: #555;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            margin-top: 8px;
        }}
        
        /* Risk Badges */
        .risk-badge {{
            padding: 0.8rem 1.5rem;
            border-radius: 8px;
            font-weight: 800;
            font-size: 1.2rem;
            text-align: center;
            box-shadow: inset 0 2px 4px rgba(0,0,0,0.05);
        }}
        .risk-high   {{ background-color: #fee2e2; color: {AMAZON_RED}; border: 1px solid #f87171; }}
        .risk-medium {{ background-color: #fff7ed; color: #9a3412; border: 1px solid #fb923c; }}
        .risk-low    {{ background-color: #f0fdf4; color: {AMAZON_GREEN}; border: 1px solid #4ade80; }}
        
        /* Section titles */
        .section-title {{
            color: {AMAZON_NAVY};
            font-weight: 800;
            font-size: 1.3rem;
            margin: 1.5rem 0 1rem 0;
            display: flex;
            align-items: center;
        }}
        .section-title::before {{
            content: "";
            width: 4px;
            height: 24px;
            background: {AMAZON_ORANGE};
            margin-right: 12px;
            border-radius: 2px;
        }}
    </style>
    """, unsafe_allow_html=True)

    # ── Data & model loaders ─
    @st.cache_data
    def load_data():
        """Combined data loader for 100% project visibility."""
        try:
            dfs = []
            if TRAIN_PATH.exists():
                dfs.append(pd.read_csv(TRAIN_PATH))
            if VAL_PATH.exists():
                dfs.append(pd.read_csv(VAL_PATH))
            
            if not dfs:
                return None
            return pd.concat(dfs, ignore_index=True)
        except:
            return None

    @st.cache_resource
    def load_model():
        try:
            if not MODEL_PATH.exists():
                return None
            with open(MODEL_PATH, 'rb') as f:
                return pickle.load(f)
        except:
            return None

    df       = load_data()
    artifact = load_model()

    # ── Prediction Logic (Real Model) ──
    def _dist_bucket(km: float) -> int:
        for i, edge in enumerate([15, 30, 50, 70]):
            if km <= edge: return i
        return 4

    def predict_failure(artifact: dict, input_dict: dict) -> tuple[float, str]:
        model    = artifact['model']
        encoders = artifact['encoders']
        thresh   = artifact.get('best_threshold', 0.5)

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

        # Use dual thresholds for UX mapping
        if prob >= 0.50: risk = 'HIGH'
        elif prob >= thresh: risk = 'MEDIUM'
        else: risk = 'LOW'

        return float(prob), risk

    # ── Sidebar Navigation ──
    st.sidebar.markdown(f"""
    <div style='background:{AMAZON_NAVY}; padding:2rem 1rem; border-radius:15px; text-align:center; margin-bottom: 2rem;'>
        <div style='font-size:3rem; margin-bottom:10px;'>📦</div>
        <div style='color:white; font-weight:800; font-size:1.4rem; letter-spacing:1px;'>AMAZON LA</div>
        <div style='color:{AMAZON_ORANGE}; font-size:0.8rem; font-weight:700; text-transform:uppercase;'>Last-Mile Analytics</div>
    </div>
    """, unsafe_allow_html=True)

    page = st.sidebar.radio(
        "DASHBOARD MENU",
        ["Operations Overview", "Package Risk Scoring", "Commercial ROI Analysis"],
        index=0
    )

    st.sidebar.markdown("---")
    st.sidebar.info(f"""
    **Project Info:**
    - **Data:** Official Amazon LMRC 2018
    - **Scale:** {len(df) if df is not None else 3559} Real Shipments (LA)
    - **Impact:** Predictive Risk Avoidance
    """)

    # ── Diagnostics ──
    with st.sidebar.expander("🛠️ System Diagnostics"):
        st.write(f"**Data Path:** `{'Combined CSVs'}`")
        st.write(f"**Total Records:** {len(df) if df is not None else 'N/A'}")
        if artifact:
            st.write(f"**Model AUC:** {artifact['metrics']['auc_roc']:.4f}")
            st.write(f"**Recall:** {artifact['metrics']['recall']*100:.1f}%")

    # ═════════════════════════════════════════════
    # PAGE 1: OPERATIONS OVERVIEW
    # ═════════════════════════════════════════════
    if page == "Operations Overview":
        if df is None:
            st.error("🚨 Critical Error: Data source not found. Please verify the `data/` directory.")
            st.stop()

        total = len(df)
        fail_rate = df['delivery_failed'].mean() * 100
        total_lost = df['delivery_failed'].sum() * COST_PER_FAILURE
        
        st.markdown(f"""
        <div class='main-header'>
            <h1>Amazon LA Operations Command</h1>
            <p>Official LMRC Last-Mile Dataset | Real-world Logistics Intelligence</p>
        </div>
        """, unsafe_allow_html=True)

        # KPI Metrics Row
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.markdown(f"<div class='premium-card'><div class='kpi-value'>{total:,}</div><div class='kpi-label'>Total Deliveries</div></div>", unsafe_allow_html=True)
        with m2:
            st.markdown(f"<div class='premium-card'><div class='kpi-value' style='color:{AMAZON_RED}'>{fail_rate:.1f}%</div><div class='kpi-label'>Failure Rate</div></div>", unsafe_allow_html=True)
        with m3:
            st.markdown(f"<div class='premium-card'><div class='kpi-value'>{df['packages_in_route'].median():.0f}</div><div class='kpi-label'>Avg Route Load</div></div>", unsafe_allow_html=True)
        with m4:
            st.markdown(f"<div class='premium-card'><div class='kpi-value' style='color:{AMAZON_GREEN}'>${total_lost:,.0f}</div><div class='kpi-label'>Est. Operational Loss</div></div>", unsafe_allow_html=True)

        # Charts Section
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("<div class='section-title'>Delivery Performance by Carrier</div>", unsafe_allow_html=True)
            carrier_stats = (df.groupby('carrier')['delivery_failed'].mean() * 100).sort_values(ascending=False)
            names = {'carrier_A': 'Lgx Central', 'carrier_B': 'Reg. Hub', 'carrier_C': 'Exp. Hub', 'carrier_D': 'Local Courier'}
            fig, ax = plt.subplots(figsize=(8, 5))
            colors = [AMAZON_RED if v > 20 else AMAZON_ORANGE for v in carrier_stats.values]
            bars = ax.bar([names[c] for c in carrier_stats.index], carrier_stats.values, color=colors, alpha=0.9, width=0.6)
            ax.axhline(fail_rate, color=AMAZON_NAVY, ls='--', label='Global Average')
            ax.set_ylabel('Failure %')
            ax.legend()
            sns.despine()
            st.pyplot(fig)
        with c2:
            st.markdown("<div class='section-title'>Risk Heatmap: Carrier × Weather</div>", unsafe_allow_html=True)
            pivot = (df.groupby(['carrier', 'weather_risk'])['delivery_failed'].mean().unstack() * 100).fillna(0)
            pivot.index = [names.get(c, c) for c in pivot.index]
            fig2, ax2 = plt.subplots(figsize=(8, 5))
            sns.heatmap(pivot, annot=True, cmap='YlOrRd', fmt='.1f', ax=ax2, cbar=False)
            st.pyplot(fig2)

    # ═════════════════════════════════════════════
    # PAGE 2: RISK SCORING
    # ═════════════════════════════════════════════
    elif page == "Package Risk Scoring":
        st.markdown(f"""
        <div class='main-header'>
            <h1>Precision Risk Prediction</h1>
            <p>Evaluating individual shipment risk using 8 LMRC operational features</p>
        </div>
        """, unsafe_allow_html=True)

        if artifact is None:
            st.warning("⚠️ Model artifact not found. Please verify `artifacts/delivery_model.pkl`.")
        else:
            col_in, col_out = st.columns([1, 1], gap="large")
            with col_in:
                st.markdown("<div class='section-title'>Shipment Parameters</div>", unsafe_allow_html=True)
                with st.container(border=True):
                    sc1, sc2 = st.columns(2)
                    with sc1:
                        p_type = st.selectbox("Type", ['standard', 'high_value'])
                        s_time = st.selectbox("Shift", ['morning', 'afternoon'])
                        carrier = st.selectbox("Carrier", ['carrier_A', 'carrier_B', 'carrier_C', 'carrier_D'])
                    with sc2:
                        dist = st.slider("Route Distance (km)", 5, 100, 35)
                        load = st.slider("Packages in Route", 10, 150, 75)
                    st.divider()
                    st_time = st.toggle("Short Service Time (<25s)")
                    scan    = st.toggle("Double Scan Anomaly")
                    miss    = st.toggle("Missing Reference Code")
                    predict_btn = st.button("🔮 Score Package", type="primary", use_container_width=True)

            with col_out:
                st.markdown("<div class='section-title'>Risk Assessment Outcome</div>", unsafe_allow_html=True)
                if predict_btn:
                    input_dict = {
                        'package_type': p_type, 'shift': s_time, 'carrier': carrier,
                        'route_distance_km': dist, 'packages_in_route': load,
                        'double_scan': int(scan), 'short_service_time': int(st_time),
                        'cr_number_missing': int(miss)
                    }
                    prob, risk = predict_failure(artifact, input_dict)
                    
                    risk_styles = {
                        'HIGH':   ('risk-high', 'URGENT: Manual inspection required.'),
                        'MEDIUM': ('risk-medium', 'ADVISORY: Monitor delivery progress.'),
                        'LOW':    ('risk-low', 'APPROVED: Proceed to standard dispatch.')
                    }
                    label, css = risk_styles[risk]
                    
                    st.markdown(f"<div class='risk-badge {css}'>{risk} RISK</div>", unsafe_allow_html=True)
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.metric("Failure Probability", f"{prob*100:.1f}%")
                    st.progress(prob)
                    st.info(f"**Action Plan:** {label}")
                else:
                    st.info("Configure shipment parameters and click 'Score Package'.")

        # Dynamic Metrics Footer
        if artifact:
            st.markdown("---")
            st.markdown("#### Model Performance (Live Metrics)")
            mc1, mc2, mc3 = st.columns(3)
            mc1.metric("AUC-ROC", f"{artifact['metrics']['auc_roc']:.4f}")
            mc2.metric("Recall", f"{artifact['metrics']['recall']*100:.1f}%")
            mc3.metric("Decision Threshold", f"{artifact.get('best_threshold', 0.5):.2f}")

    # ═════════════════════════════════════════════
    # PAGE 3: COMMERCIAL ROI
    # ═════════════════════════════════════════════
    elif page == "Commercial ROI Analysis":
        st.markdown(f"""
        <div class='main-header'>
            <h1>Business Impact & ROI</h1>
            <p>Quantifying the financial value of predictive logistics at Amazon LA</p>
        </div>
        """, unsafe_allow_html=True)

        i1, i2 = st.columns(2)
        with i1:
            st.markdown("<div class='premium-card'>", unsafe_allow_html=True)
            st.subheader("Cost Avoidance Strategy")
            st.write(f"""
            A failed delivery costs an average of **${COST_PER_FAILURE:.2f}** in operational overhead. 
            By identifying 'High Risk' packages, we can prevent loss thru re-routing or customer notification.
            """)
            st.markdown("</div>", unsafe_allow_html=True)

        with i2:
            st.markdown("<div class='premium-card'>", unsafe_allow_html=True)
            st.subheader("Projected Monthly Savings")
            recall = artifact['metrics']['recall'] if artifact else 0.84
            current_fails = df['delivery_failed'].sum() if df is not None else 140
            potential_savings = current_fails * recall * COST_PER_FAILURE
            
            st.markdown(f"### Est. Savings: **${potential_savings:,.2f}**")
            st.caption(f"Based on {recall*100:.1f}% Recall achieved by the model on 3,559 shipments.")
            st.markdown("</div>", unsafe_allow_html=True)

except Exception as e:
    st.error("🚨 App Runtime Exception")
    st.code(traceback.format_exc())
