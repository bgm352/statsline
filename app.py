"""
Statsline: Dealer Arbitrage & Lamar 6-Gate Inspection Suite
Built with Python, OpenCV, and Streamlit.
"""
import streamlit as st
import pandas as pd
from datetime import date, timedelta
from core.underwriting import ArbitrageCandidate, calculate_batch_summary
from core.lamar_audit import SixGateAudit, analyze_card_centering_opencv
from core.database import load_candidates, save_candidates

st.set_page_config(
    page_title="Statsline | Dealer Arbitrage & 6-Gate Inspection",
    page_icon="💎",
    layout="wide",
)

# Initialize session state from seed JSON
if "inventory" not in st.session_state:
    st.session_state.inventory = load_candidates()

st.title("💎 Statsline: Dealer Arbitrage & Pre-Grading Underwriting Engine")
st.caption("Off-Season Trough Acquisition • Lamar 6-Gate Loupe Audit • Spring Liquidity Execution")

# Sidebar Configuration
with st.sidebar:
    st.header("⚙️ Dealer Parameters")
    platform_fee = st.slider("Platform / eBay Fee (%)", min_value=0.0, max_value=20.0, value=13.0, step=0.5) / 100.0
    default_grading_fee = st.number_input("Standard PSA Grading + Logistics ($/card)", value=40.0, step=5.0)
    hours_per_batch = st.number_input("Hands-On Labor Hours per Batch", value=2.5, step=0.5)
    w2_hourly_rate = st.number_input("Benchmark Active W-2 Hourly Rate ($/hr)", value=70.0, step=5.0)

    st.divider()
    st.subheader("📅 Turnaround Queue Clock")
    sub_date = st.date_input("Target PSA Ship Date", value=date(2026, 11, 28))
    psa_business_days = st.slider("Estimated PSA Turnaround (Business Days)", 45, 110, 75)
    calendar_days = int(psa_business_days * (7 / 5)) + 6  # Add transit buffer
    est_return_date = sub_date + timedelta(days=calendar_days)
    st.metric("Est. Slab Return Window", est_return_date.strftime("%b %d, %Y"))
    if est_return_date.month in (2, 3):
        st.success("✅ Hits Peak Cactus League / Spring Training Liquidity Wave!")
    else:
        st.warning("⚠️ Adjust submission date to land in Feb/March liquidity window.")

tabs = st.tabs([
    "📊 Master Batch Ledger",
    "🧮 Deal Underwriter (2x & Floor Check)",
    "🔬 Lamar 6-Gate & OpenCV Inspector",
    "📈 10-Card Monthly Scaling Blueprint"
])

# -------------------------------------------------------------------------
# TAB 1: MASTER BATCH LEDGER
# -------------------------------------------------------------------------
with tabs[0]:
    st.subheader("📦 Active Master Submission Batch vs. Evaluated Rejections")

    # Sync fee rate
    for c in st.session_state.inventory:
        c.platform_fee_rate = platform_fee

    summary = calculate_batch_summary(
        st.session_state.inventory,
        hours_invested=hours_per_batch,
        w2_hourly_benchmark=w2_hourly_rate,
    )

    if summary:
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Active Batch Size", f"{summary['card_count']} Cards", f"${summary['total_basis']:.2f} All-In Basis")
        c2.metric("Downside Floor (All PSA 9s)", f"${summary['all_9_gross']:.2f} Gross", f"Net: ${summary['all_9_net']:.2f} (Protected)")
        c3.metric("Realistic Hybrid Profit", f"+${summary['realistic_profit']:,.2f}", f"${summary['effective_hourly_realistic']:,.0f}/hr yield")
        c4.metric("All-Gem PSA 10 Profit", f"+${summary['all_gem_profit']:,.2f}", f"{summary['portfolio_multiplier']}x Cash Multiplier")
        c5.metric("Hourly Yield (All-Gem)", f"${summary['effective_hourly_all_gem']:,.2f}/hr", f"={summary['w2_equivalent_hours']} W-2 hrs")

    st.markdown("#### ✅ Approved PSA Submission Roster (Cleared 6-Gate Audit)")
    evaluated_rows = [c.evaluate_deal() for c in st.session_state.inventory]
    df_all = pd.DataFrame(evaluated_rows)

    df_active = df_all[df_all["passed_6_gate"] & (~df_all["is_watermarked_scan"])].copy()
    if not df_active.empty:
        display_cols = [
            "card_id", "card_name", "category", "raw_cost", "grading_fee",
            "all_in_basis", "psa9_comp", "psa10_comp", "net_psa10_proceeds",
            "psa10_net_profit", "cash_multiplier", "verdict"
        ]
        st.dataframe(
            df_active[display_cols].style.format({
                "raw_cost": "${:,.2f}",
                "grading_fee": "${:,.2f}",
                "all_in_basis": "${:,.2f}",
                "psa9_comp": "${:,.2f}",
                "psa10_comp": "${:,.2f}",
                "net_psa10_proceeds": "${:,.2f}",
                "psa10_net_profit": "+${:,.2f}",
                "cash_multiplier": "{:.2f}x",
            }),
            use_container_width=True,
            hide_index=True,
        )

    st.markdown("#### 🛑 Rejected / Watchlist Candidates (Filtered Out by Underwriting Rules)")
    df_rejected = df_all[(~df_all["passed_6_gate"]) | (df_all["is_watermarked_scan"])].copy()
    if not df_rejected.empty:
        rej_cols = [
            "card_id", "card_name", "raw_cost", "all_in_basis", "psa9_comp",
            "psa10_comp", "max_safe_raw_bid", "verdict", "notes"
        ]
        st.dataframe(
            df_rejected[rej_cols].style.format({
                "raw_cost": "${:,.2f}",
                "all_in_basis": "${:,.2f}",
                "psa9_comp": "${:,.2f}",
                "psa10_comp": "${:,.2f}",
                "max_safe_raw_bid": "${:,.2f}",
            }),
            use_container_width=True,
            hide_index=True,
        )

# -------------------------------------------------------------------------
# TAB 2: DEAL UNDERWRITER (2x RULE & MAX BID CALCULATOR)
# -------------------------------------------------------------------------
with tabs[1]:
    st.subheader("🧮 Live Listing Underwriter & Max Auction Bid Calculator")
    st.write("Evaluate eBay/COMC listings in real time before deploying capital.")

    col_left, col_right = st.columns([1, 1])
    with col_left:
        u_name = st.text_input("Card Title / Year / Parallel", value="2018-19 Panini Prizm Stephen Curry Silver #222")
        u_cat = st.selectbox("Portfolio Bucket", ["Core 70% (High-Liquidity)", "Lottery 30% (Asymmetric)"])
        u_raw = st.number_input("Listed Raw Price ($)", min_value=0.0, value=45.0, step=1.0)
        u_ship = st.number_input("Shipping Cost ($)", min_value=0.0, value=0.0, step=0.5)
        u_grade = st.number_input("PSA Grading Tier Cost ($)", min_value=15.0, value=default_grading_fee, step=5.0)
        u_psa9 = st.number_input("Verified PSA 9 Comp ($)", min_value=0.0, value=100.0, step=5.0)
        u_psa10 = st.number_input("Verified PSA 10 Comp ($)", min_value=0.0, value=385.0, step=10.0)
        u_watermark = st.checkbox("Listing uses watermarked stock scan (e.g., COMC)", value=False)
        u_notes = st.text_input("Sourcing / Inspection Notes", value="Target auction snipe ceiling check.")

    candidate = ArbitrageCandidate(
        card_id=f"CAND-{len(st.session_state.inventory)+1:03d}",
        card_name=u_name,
        category=u_cat,
        raw_cost=u_raw,
        shipping_cost=u_ship,
        grading_fee=u_grade,
        psa9_comp=u_psa9,
        psa10_comp=u_psa10,
        platform_fee_rate=platform_fee,
        is_watermarked_scan=u_watermark,
        passed_6_gate=not u_watermark,
        notes=u_notes,
    )
    eval_res = candidate.evaluate_deal()

    with col_right:
        st.markdown("### 📋 Underwriting Decision")
        if eval_res["verdict"] in ("MASTER ARBITRAGE LOCK", "APPROVED"):
            st.success(f"**Verdict: {eval_res['verdict']}**")
        elif "HIGH CONVICTION" in eval_res["verdict"]:
            st.warning(f"**Verdict: {eval_res['verdict']}**")
        else:
            st.error(f"**Verdict: {eval_res['verdict']}**")

        m1, m2, m3 = st.columns(3)
        m1.metric("All-In Basis", f"${eval_res['all_in_basis']:.2f}")
        m2.metric("Max Safe Raw Bid (PSA 9 Floor)", f"${eval_res['max_safe_raw_bid']:.2f}")
        m3.metric("Gross / Net Multiplier", f"{eval_res['gross_multiplier']}x / {eval_res['cash_multiplier']}x")

        m4, m5 = st.columns(2)
        m4.metric("PSA 9 Net Outcome (After Fees)", f"${eval_res['psa9_net_profit']:+.2f}")
        m5.metric("PSA 10 Net Profit (After Fees)", f"${eval_res['psa10_net_profit']:+.2f}")

        st.markdown("#### 🔍 Gate Flags")
        for flag in eval_res["flags"]:
            st.write(f"- {flag}")

        if st.button("➕ Add Candidate to Inventory Ledger"):
            st.session_state.inventory.append(candidate)
            save_candidates(st.session_state.inventory)
            st.success(f"Saved {u_name} to inventory!")
            st.rerun()

# -------------------------------------------------------------------------
# TAB 3: LAMAR 6-GATE & OPENCV INSPECTOR
# -------------------------------------------------------------------------
with tabs[2]:
    st.subheader("🔬 Lamar 6-Gate Inspection Desk & OpenCV Centering Calibrator")
    col_gate, col_cv = st.columns([1, 1])

    with col_gate:
        st.markdown("#### 10x Loupe & Raking Light 6-Gate Checklist")
        g1 = st.checkbox("Gate 1: Front Centering within 55/45 tolerance", value=True)
        g2 = st.checkbox("Gate 2: Reverse Centering within 70/30 tolerance", value=True)
        g3 = st.checkbox("Gate 3: Raking Light Surface Check (Zero print lines, dimples, or chrome scratches)", value=True)
        g4 = st.checkbox("Gate 4: 10x Loupe Corners (Four razor-sharp tips, zero flaring)", value=True)
        g5 = st.checkbox("Gate 5: Dark-Stock Reverse Edges (Zero white specks on Kurtz/151 dark borders)", value=True)
        g6 = st.checkbox("Gate 6: Fresh Penny Sleeve + Card Saver I (Zero fingerprint hazing)", value=True)
        lr_slider = st.slider("Measured Front Left/Right Centering (%)", 35.0, 65.0, 50.0, 0.5)
        tb_slider = st.slider("Measured Front Top/Bottom Centering (%)", 35.0, 65.0, 50.0, 0.5)

        audit = SixGateAudit(
            gate1_front_centering=g1,
            gate2_back_centering=g2,
            gate3_surface_chromium=g3,
            gate4_corners_10x=g4,
            gate5_edges_dark_stock=g5,
            gate6_eye_appeal_sleever=g6,
            front_lr_ratio=lr_slider,
            front_tb_ratio=tb_slider,
        ).evaluate()

        if audit["passed_all"]:
            st.success(f"**{audit['recommendation']}** ({audit['gates_passed']} Gates Cleared | L/R: {audit['lr_split']} | T/B: {audit['tb_split']})")
        else:
            st.error(f"**{audit['recommendation']}** ({audit['gates_passed']} Gates Cleared)")

    with col_cv:
        st.markdown("#### 📷 OpenCV Digital Centering & Surface Analyzer")
        uploaded_file = st.file_uploader("Upload Raw Card Image (PNG/JPG)", type=["png", "jpg", "jpeg"])
        if uploaded_file is not None:
            img_bytes = uploaded_file.read()
            c_l, c_r, c_t, c_b = st.columns(4)
            left_px = c_l.number_input("Left Border (px)", min_value=1, value=45)
            right_px = c_r.number_input("Right Border (px)", min_value=1, value=45)
            top_px = c_t.number_input("Top Border (px)", min_value=1, value=45)
            bot_px = c_b.number_input("Bottom Border (px)", min_value=1, value=45)

            annotated_img, cv_metrics = analyze_card_centering_opencv(
                img_bytes, left_px, right_px, top_px, bot_px
            )
            st.image(annotated_img, caption="OpenCV Annotated Centering Guides", use_container_width=True)
            st.json(cv_metrics)
        else:
            st.info("Upload a high-resolution unwatermarked card scan to run OpenCV border ratio and Laplacian surface analysis.")

# -------------------------------------------------------------------------
# TAB 4: 10-CARD MONTHLY SCALING BLUEPRINT
# -------------------------------------------------------------------------
with tabs[3]:
    st.subheader("📈 Systematic 10-Card Monthly Scaling Simulator")
    st.markdown("""
    **Operational Cadence:**
    - **Days 1–15 (The Trough Sweep):** Hunt raw inventory during mid-month auction lulls. Enforce max bid ceilings.
    - **Days 16–25 (Lamar 6-Gate Audit):** Inspect all arrivals under 10x magnification. Flip rejects raw immediately.
    - **Day 28 (Batch Manifest):** Ship 10-card survivor box to PSA to create a rolling 30-day slab return pipeline.
    """)

    s1, s2, s3 = st.columns(3)
    monthly_budget = s1.slider("Target Monthly Deployed Capital ($)", 500, 3000, 1350, 50)
    expected_gem_rate = s2.slider("Expected PSA 10 Gem Rate (%)", 40, 100, 70, 5) / 100.0
    avg_gem_mult = s3.slider("Target Average Gem 10 Net Multiplier (x)", 2.0, 4.5, 3.4, 0.1)

    core_allocation = monthly_budget * 0.70
    lottery_allocation = monthly_budget * 0.30

    # Simulate monthly outcome where PSA 9s break even (1.0x) and PSA 10s hit avg_gem_mult
    expected_monthly_net = (monthly_budget * expected_gem_rate * avg_gem_mult) + (monthly_budget * (1 - expected_gem_rate) * 1.0)
    expected_monthly_profit = expected_monthly_net - monthly_budget
    annualized_profit = expected_monthly_profit * 12

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("70% Core Allocation (7 Cards)", f"${core_allocation:,.0f}", "PSA 9 Floor Protected")
    k2.metric("30% Asymmetric Lottery (3 Cards)", f"${lottery_allocation:,.0f}", "Low-Numbered /50 & Grails")
    k3.metric("Projected Monthly Net Profit", f"+${expected_monthly_profit:,.0f}/mo", f"At {int(expected_gem_rate*100)}% Gem Rate")
    k4.metric("Annualized Rolling Pipeline Profit", f"+${annualized_profit:,.0f}/yr", "~6 hrs/mo total labor")
