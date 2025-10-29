"""
app.py — Dark theme, UX polish + long methodology + weight ranking + disclaimer
Includes Risk Capacity and Risk Requirement modules.
Run with:
    streamlit run app.py
"""

from typing import Dict
import streamlit as st
import pandas as pd
import math

# -----------------------
# Config (step sizes)
# -----------------------
STEP_INVESTABLE = 2500
STEP_INCOME = 1000
STEP_FIXED = 500
STEP_VARIABLE = 500
STEP_WITHDRAW = 100
STEP_GROWTH = 0.1

# -----------------------
# Mapping functions (capacity logic you had)
# -----------------------
def map_sli(sli: float) -> float:
    if sli <= 1.0:
        return 0.0
    if 1.0 < sli <= 5.0:
        return 1.0 + (sli - 1.0) / (5.0 - 1.0) * (40.0 - 1.0)
    if 5.0 < sli <= 20.0:
        return 40.0 + (sli - 5.0) / (20.0 - 5.0) * (80.0 - 40.0)
    if 20.0 < sli <= 50.0:
        return 80.0 + (sli - 20.0) / (50.0 - 20.0) * (95.0 - 80.0)
    if sli > 50.0:
        mapped = 95.0 + (min(sli, 200.0) - 50.0) / (200.0 - 50.0) * (100.0 - 95.0)
        return min(mapped, 100.0)
    return 0.0

def map_income_ratio(r: float) -> float:
    if r <= 1.0:
        return 10.0
    if 1.0 < r <= 1.5:
        return 10.0 + (r - 1.0) / (1.5 - 1.0) * (40.0 - 10.0)
    if 1.5 < r <= 2.5:
        return 40.0 + (r - 1.5) / (2.5 - 1.5) * (75.0 - 40.0)
    mapped = 75.0 + (min(r, 10.0) - 2.5) / (10.0 - 2.5) * (100.0 - 75.0)
    return min(mapped, 100.0)

def map_emergency_months(months: float) -> float:
    if months <= 1.0:
        return 5.0
    if 1.0 < months <= 3.0:
        return 20.0 + (months - 1.0) / (3.0 - 1.0) * (40.0 - 20.0)
    if 3.0 < months <= 6.0:
        return 40.0 + (months - 3.0) / (6.0 - 3.0) * (70.0 - 40.0)
    mapped = 70.0 + (min(months, 24.0) - 6.0) / (24.0 - 6.0) * (100.0 - 70.0)
    return min(mapped, 100.0)

def map_industry(s: str) -> float:
    m = {"Stable": 90.0, "Moderate": 60.0, "Unstable": 25.0}
    return float(m.get(s, 60.0))

def map_age(age: int) -> float:
    if age <= 30:
        return 90.0
    if 31 <= age <= 40:
        return 75.0
    if 41 <= age <= 55:
        return 50.0
    if 56 <= age <= 65:
        return 30.0
    return 10.0

def map_growth(g: float) -> float:
    if g < 0.0:
        return 10.0
    if g < 2.0:
        return 30.0
    if g < 5.0:
        return 60.0
    return 85.0

def map_dependents(d: int) -> float:
    if d == 0:
        return 90.0
    if d == 1:
        return 70.0
    if d == 2:
        return 50.0
    if d == 3:
        return 30.0
    return 15.0

# -----------------------
# Weights & compute (capacity)
# -----------------------
WEIGHTS = {
    "SLI": 25.0,
    "Income": 20.0,
    "Expenses": 15.0,
    "Industry": 12.0,
    "Age": 12.0,
    "Growth": 8.0,
    "Dependents": 8.0,
}

def compute_risk_capacity(subscores: Dict[str, float]) -> float:
    total = sum(WEIGHTS[k] * float(subscores[k]) for k in WEIGHTS.keys())
    score = total / 100.0
    return round(max(0.0, min(100.0, score)), 1)

# Add this helper near the top (requires import math)
def compute_risk_requirement(rrr: float, real_req_pct: float, shortfall_pct: float, draw_ratio: float):
    """
    Returns: (requirement_score: float, subscores: Dict[str, float])
    rrr: required CAGR as decimal (e.g., 0.07)
    real_req_pct: real required return in percentage (after inflation)
    shortfall_pct: real_req_pct - expected_return (percentage points)
    draw_ratio: avg_drawdown_percent / drawdown_tolerance_percent (unitless)
    """
    # Map RRR (as percent)
    rrr_pct = rrr * 100.0
    if rrr_pct <= 2.0:
        rrr_s = 10.0
    elif rrr_pct <= 5.0:
        rrr_s = 35.0
    elif rrr_pct <= 10.0:
        rrr_s = 65.0
    else:
        rrr_s = 90.0

    # Map Real requirement percent
    if real_req_pct <= 0.0:
        real_s = 10.0
    elif real_req_pct <= 2.0:
        real_s = 40.0
    elif real_req_pct <= 5.0:
        real_s = 70.0
    else:
        real_s = 90.0

    # Map shortfall: more shortfall -> higher requirement
    if shortfall_pct <= 0.0:
        short_s = 10.0
    elif shortfall_pct <= 2.0:
        short_s = 30.0
    elif shortfall_pct <= 5.0:
        short_s = 60.0
    else:
        short_s = 90.0

    # Map drawdown pressure: higher means riskier to reach goal
    if draw_ratio <= 0.5:
        draw_s = 10.0
    elif draw_ratio <= 1.0:
        draw_s = 40.0
    elif draw_ratio <= 2.0:
        draw_s = 70.0
    else:
        draw_s = 90.0

    # Weights: RRR is most important
    REQ_WEIGHTS = {"RRR": 35.0, "RealReq": 25.0, "Shortfall": 25.0, "DrawPressure": 15.0}
    subs = {"RRR": rrr_s, "RealReq": real_s, "Shortfall": short_s, "DrawPressure": draw_s}
    total = sum(REQ_WEIGHTS[k] * subs[k] for k in REQ_WEIGHTS)
    req_score = round(max(0.0, min(100.0, total / 100.0)), 1)
    return req_score, subs


# -----------------------
# Risk requirement mapping functions and weights
# -----------------------
def map_rrr(rrr: float) -> float:
    # rrr is decimal, convert to percent for thresholds
    p = rrr * 100.0
    if p <= 3.0:
        return 0.0
    if p <= 6.0:
        return (p - 3.0) / (6.0 - 3.0) * 25.0
    if p <= 10.0:
        return 25.0 + (p - 6.0) / (10.0 - 6.0) * 35.0
    if p <= 15.0:
        return 60.0 + (p - 10.0) / (15.0 - 10.0) * 25.0
    return 85.0 + min(p - 15.0, 15.0) / 15.0 * 15.0

def map_realreq(real_pct: float) -> float:
    # real_pct in percent
    if real_pct <= 0.0:
        return 0.0
    if real_pct <= 2.0:
        return (real_pct / 2.0) * 25.0
    if real_pct <= 5.0:
        return 25.0 + (real_pct - 2.0) / (5.0 - 2.0) * 40.0
    return 65.0 + min(real_pct - 5.0, 10.0) / 10.0 * 35.0

def map_shortfall(short_pct: float) -> float:
    # short_pct in percent, how much needed above expected.
    if short_pct <= 0:
        return 0.0
    # map 0-10% -> 0-100 linearly, cap at 100
    return min(100.0, (short_pct / 10.0) * 100.0)

def map_drawimpact(draw_ratio: float) -> float:
    # draw_ratio = D_avg / DT
    if draw_ratio <= 0.5:
        return 0.0
    if draw_ratio <= 1.0:
        return 25.0
    if draw_ratio <= 1.5:
        return 60.0
    return 100.0

# weights for requirement score (tuneable)
REQ_WEIGHTS = {
    "RRR": 40.0,
    "RealReq": 25.0,
    "Shortfall": 20.0,
    "DrawImpact": 15.0,
}


# -----------------------
# Helpers (formatting + human lines)
# -----------------------
def fmt_num(x: float) -> str:
    if abs(x - round(x)) < 1e-9:
        return str(int(round(x)))
    return f"{round(x,1):.1f}".rstrip('0').rstrip('.')

def zone_sentence(component: str, raw_value: float) -> str:
    if component == "SLI":
        if raw_value <= 1:
            zone = "No meaningful liquid cushion (<=1 year)."
        elif raw_value <= 5:
            zone = "Low cushion (1-5 years)."
        elif raw_value <= 20:
            zone = "Moderate cushion (5-20 years)."
        else:
            zone = "Very strong cushion (>20 years)."
        return f"SLI = {fmt_num(raw_value)} years - {zone} Larger SLI => stronger resilience to withdrawals and shocks."
    if component == "Income":
        r = raw_value
        if r <= 1:
            z = "Income <= expenses (high forced selling risk)."
        elif r <= 1.5:
            z = "Income modestly above expenses."
        elif r <= 2.5:
            z = "Income comfortably above expenses."
        else:
            z = "High income vs expenses (strong buffer)."
        return f"Income ratio = {round(r,2)} - {z}"
    if component == "Expenses":
        m = raw_value
        if m <= 1:
            z = "Under 1 month emergency cushion."
        elif m <= 3:
            z = "1-3 months."
        elif m <= 6:
            z = "3-6 months."
        else:
            z = "6+ months."
        return f"Emergency months = {fmt_num(m)} - {z}"
    if component == "Industry":
        return f"Industry stability = {raw_value}. Stable industries imply reduced income disruption risk."
    if component == "Age":
        return f"Age = {int(raw_value)}. Younger investors have longer recovery horizons (higher capacity)."
    if component == "Growth":
        return f"Expected salary growth = {fmt_num(raw_value)}% p.a. Higher growth increases future capacity."
    if component == "Dependents":
        return f"Dependents = {int(raw_value)}. More dependents reduce discretionary capacity."
    return ""

# -----------------------
# UI + CSS
# -----------------------
def main():
    st.set_page_config(page_title="Risk Capacity Estimator", layout="wide")
    # CSS block remains same as you had; ensure it uses the colors you want
    st.markdown(
        """
        <style>
        :root {
            --accent: #12c755;
            --dark-bg: #071026;
            --card: #0b1b2b;
            --muted: #93a4b6;
            --text: #e6eef6;
        }
        html, body, .stApp { background: var(--dark-bg) !important; color: var(--text) !important; }
        .stSidebar { background: var(--dark-bg) !important; color: var(--text) !important; }
        .rc-card { background: var(--card); padding: 14px; border-radius: 10px; color: var(--text); }
        .rc-score { font-size:36px; font-weight:700; color: var(--accent); }
        input, select, textarea { background: #0f2a3f !important; color: var(--text) !important; border-radius:6px !important; border:1px solid rgba(255,255,255,0.06) !important; padding:6px !important; }
        .stButton>button, .stDownloadButton>button { background: var(--accent) !important; color: #031014 !important; font-weight:600; border-radius:8px !important; padding:8px 12px !important; }
        .stNumberInput, .stSelectbox { max-width: 360px; }
        .stDataFrame table { table-layout: auto !important; }
        .stCaption { color: var(--muted) !important; }
        </style>
        """, unsafe_allow_html=True
    )

    st.title("Risk Capacity Estimator")
    st.write("Objective, explainable estimate (0:100) of how much investment risk a client can afford. Fill inputs then press Calculate.")

    # top controls
    c1, c2 = st.columns([1, 0.6])
    with c1:
        st.caption("Fill realistic inputs. Missing values reduce confidence.")
    with c2:
        # Auto-update: default True per your request
        auto_update = st.checkbox("Auto-update while editing", value=True)

    # Form for inputs: keeps desktop tidy
    with st.form("inputs", clear_on_submit=False):
        left, right = st.columns([1.0, 1.0])

        with left:
            st.header("Personal & Cashflow")
            age = st.number_input("Age (years):", min_value=0, value=39, step=1)
            dependents = st.number_input("Number of dependents:", min_value=0, value=2, step=1)
            annual_income = st.number_input("Annual income (USD):", min_value=0, value=500000, step=STEP_INCOME, format="%d")
            annual_fixed = st.number_input("Annual fixed expenses (USD):", min_value=0, value=30000, step=STEP_FIXED, format="%d")
            annual_variable = st.number_input("Annual variable expenses (USD):", min_value=0, value=30000, step=STEP_VARIABLE, format="%d")
            # forced dropdown: no typing allowed
            industry = st.radio("Industry stability:", ["Stable", "Moderate", "Unstable"], index=1)
            expected_growth = st.number_input("Expected salary growth (annual %):", value=2.0, step=STEP_GROWTH, format="%.2f")

        with right:
            st.header("Assets, Withdrawals & Goal")
            investable_assets = st.number_input("Investable assets (USD):", min_value=0, value=500000, step=STEP_INVESTABLE, format="%d")
            annual_withdrawals = st.number_input("Annual withdrawals (USD):", min_value=0, value=10000, step=STEP_WITHDRAW, format="%d")
            st.markdown("### Goal inputs (for Risk Requirement)")
            target_wealth = st.number_input("Target portfolio value (USD):", min_value=0, value=1500000, step=10000, format="%d")
            current_portfolio = st.number_input("Current portfolio value (USD):", min_value=0, value=500000, step=1000, format="%d")
            horizon_years = st.number_input("Time horizon (years):", min_value=1, value=10, step=1)
            inflation = st.number_input("Assumed inflation rate (%):", min_value=0.0, value=2.0, step=0.1, format="%.2f")
            expected_return = st.number_input("Expected annual return (%):", min_value=-10.0, value=6.0, step=0.1, format="%.2f")
            avg_drawdown = st.number_input("Average historical drawdown (%):", min_value=0.0, value=30.0, step=0.1, format="%.1f")
            drawdown_tolerance = st.number_input("Drawdown tolerance (%):", min_value=0.0, value=15.0, step=0.1, format="%.1f")

        submitted = st.form_submit_button("Calculate")
        if auto_update:
            # emulate immediate submit when auto-update is on
            submitted = True

    if submitted:
        # Derived values
        monthly_expenses = (annual_fixed + annual_variable) / 12.0
        sli_value = investable_assets / max(1.0, annual_withdrawals)
        income_ratio = annual_income / max(1.0, (annual_fixed + annual_variable))
        months = investable_assets / max(1.0, monthly_expenses)

        # Capacity subscores
        subscores = {
            "SLI": map_sli(sli_value),
            "Income": map_income_ratio(income_ratio),
            "Expenses": map_emergency_months(months),
            "Industry": map_industry(industry),
            "Age": map_age(int(age)),
            "Growth": map_growth(float(expected_growth)),
            "Dependents": map_dependents(int(dependents)),
        }
        capacity_score = compute_risk_capacity(subscores)

        # Requirement computation
        T = max(1.0, float(target_wealth))
        C = max(1.0, float(current_portfolio))
        n = max(1.0, float(horizon_years))
        rrr = math.pow(T / C, 1.0 / n) - 1.0
        real_req_pct = (rrr * 100.0) - float(inflation)  # real % needed
        shortfall_pct = real_req_pct - float(expected_return)
        # Avoid division by zero in draw ratio
        draw_ratio = float(avg_drawdown) / max(float(drawdown_tolerance), 0.0001)
        requirement_score, req_subscores = compute_risk_requirement(rrr, real_req_pct, shortfall_pct, draw_ratio)

        # Results area below inputs, Requirement shown first
        st.markdown("---")
        st.header("Results")

        st.markdown(f"<div class='rc-card'><div style='font-size:20px; color:var(--muted)'>Requirement: how much risk is required to meet the goal</div>"
                    f"<div class='rc-score'>{fmt_num(requirement_score)} / 100</div></div>", unsafe_allow_html=True)

        # Now show Capacity
        st.markdown(f"<div style='margin-top:10px' class='rc-card'><div style='font-size:20px; color:var(--muted)'>Capacity: how much risk client can afford</div>"
                    f"<div class='rc-score'>{fmt_num(capacity_score)} / 100</div></div>", unsafe_allow_html=True)

        # Interpretation: show requirement first, then alignment
        # requirement text
        if requirement_score >= 70:
            req_msg = "Requirement: High: achieving the target within the time horizon requires an aggressive return profile."
        elif requirement_score >= 45:
            req_msg = "Requirement: Moderate: achieving the target requires above-average returns."
        else:
            req_msg = "Requirement: Low: the target is achievable with a conservative-to-moderate approach."

        st.markdown("### Interpretation and alignment")
        st.info(req_msg)

        # alignment message: capacity minus requirement
        diff = round(capacity_score - requirement_score, 1)
        if diff >= 10:
            align_msg = f"Capacity exceeds requirement by {fmt_num(diff)} points: you have room to pursue a more aggressive plan while keeping resilience."
            st.success(align_msg)
        elif -10 <= diff < 10:
            align_msg = f"Capacity roughly matches requirement (difference {fmt_num(diff)}): proceed with a monitored plan and periodic reviews."
            st.info(align_msg)
        else:
            align_msg = f"Capacity is {fmt_num(-diff)} points below requirement: this is a material mismatch. Options: increase savings, extend the time horizon, or reduce the target."
            st.warning(align_msg)

        # -----------------------
        # Capacity breakdown: order by weight (1-based ranking)
        # -----------------------
        st.markdown("### Risk Capacity: case-specific breakdown (ranked by weight)")
        sorted_weights = sorted(WEIGHTS.items(), key=lambda kv: -kv[1])
        ordered_keys = [k for k, _ in sorted_weights]
        rows = []
        for rank, key in enumerate(ordered_keys, start=1):
            raw_val = {"SLI": sli_value, "Income": income_ratio, "Expenses": months, "Industry": industry, "Age": age, "Growth": expected_growth, "Dependents": dependents}[key]
            rows.append({
                "Rank": rank,
                "Risk factor": key,
                "Input value": fmt_num(raw_val) if key not in ["Industry", "Age", "Dependents"] else str(raw_val),
                "Subscore": fmt_num(subscores[key]),
                "Weight": f"{int(WEIGHTS[key])}%",
                "Why this matters:": zone_sentence(key, raw_val)
            })
        df_cap = pd.DataFrame(rows)
        st.dataframe(df_cap, width=960, height=240)

        # -----------------------
        # Requirement breakdown: similarly formatted
        # -----------------------
        st.markdown("### Risk Requirement: case-specific breakdown (ranked by weight)")
        # requirement weight ordering used in compute_risk_requirement
        req_order = [("RRR", 35), ("RealReq", 25), ("Shortfall", 25), ("DrawPressure", 15)]
        rows_r = []
        for rank, (k, w) in enumerate(req_order, start=1):
            val = req_subscores[k]
            human_val = {
                "RRR": f"{round(rrr*100,2)}% (RRR)",
                "RealReq": f"{round(real_req_pct,2)}% (real req)",
                "Shortfall": f"{round(shortfall_pct,2)}% (shortfall)",
                "DrawPressure": f"{round(draw_ratio,2)}x (drawdown ratio)"
            }[k]
            rows_r.append({
                "Rank": rank,
                "Requirement factor": k,
                "Value": human_val,
                "Subscore": fmt_num(val),
                "Weight": f"{w}%",
                "Why this matters:": {
                    "RRR": "Required annual growth rate to hit target in horizon.",
                    "RealReq": "After inflation: how much purchasing-power growth is needed.",
                    "Shortfall": "Difference between required real return and expected return: a positive shortfall implies more return must be found via risk.",
                    "DrawPressure": "Historical drawdowns relative to tolerance: higher ratios mean the plan faces severe risk in downturns."
                }[k]
            })
        df_req = pd.DataFrame(rows_r)
        st.dataframe(df_req, width=960, height=180)

        # -----------------------
        # Sensitivity: Quick shocks (button labels: no 'shock' word)
        # -----------------------
        with st.expander("Sensitivity scenarios: quick shocks to see how score moves"):
            st.write("These scenarios show how the final risk capacity score moves if key cushions shift by realistic amounts.")
            colA, colB = st.columns(2)
            with colA:
                if st.button("Income -20%"):
                    new_income_ratio = (annual_income * 0.8) / max(1.0, (annual_fixed + annual_variable))
                    subs2 = subscores.copy(); subs2["Income"] = map_income_ratio(new_income_ratio)
                    st.write("New risk capacity:", fmt_num(compute_risk_capacity(subs2)))
                if st.button("Income +20%"):
                    new_income_ratio = (annual_income * 1.2) / max(1.0, (annual_fixed + annual_variable))
                    subs2 = subscores.copy(); subs2["Income"] = map_income_ratio(new_income_ratio)
                    st.write("New risk capacity:", fmt_num(compute_risk_capacity(subs2)))
            with colB:
                if st.button("Assets -20%"):
                    sli2 = (investable_assets * 0.8) / max(1.0, annual_withdrawals)
                    subs2 = subscores.copy(); subs2["SLI"] = map_sli(sli2)
                    st.write("New risk capacity:", fmt_num(compute_risk_capacity(subs2)))
                if st.button("Assets +20%"):
                    sli2 = (investable_assets * 1.2) / max(1.0, annual_withdrawals)
                    subs2 = subscores.copy(); subs2["SLI"] = map_sli(sli2)
                    st.write("New risk capacity:", fmt_num(compute_risk_capacity(subs2)))

        # -----------------------
        # Methodology: Detailed mapping for every factor (no references to proprietary code)
        # -----------------------
        with st.expander("Methodology: Capacity — Long (detailed ranges and numeric mappings)"):
            st.markdown("SLI: Savings Longevity Index (investable assets / annual withdrawals):")
            st.write(" - <=1 year: subscore = 0: no meaningful cushion.")
            st.write(" - 1 to 5 years: subscore maps linearly from 1 to 40.")
            st.write(" - 5 to 20 years: subscore maps linearly from 40 to 80.")
            st.write(" - >20 years: subscore maps piecewise to 80 to 100.")
            st.markdown("Income ratio: income / (fixed + variable expenses):")
            st.write(" - <=1: subscore = 10: income does not cover expenses.")
            st.write(" - 1 to 1.5: subscore maps 10 to 40: modest coverage.")
            st.write(" - 1.5 to 2.5: subscore maps 40 to 75: comfortable coverage.")
            st.write(" - >2.5: subscore maps up to 100: strong coverage.")
            st.markdown("Emergency months: investable assets / monthly expenses:")
            st.write(" - <=1 month: subscore = 5.")
            st.write(" - 1 to 3 months: subscore maps 20 to 40.")
            st.write(" - 3 to 6 months: subscore maps 40 to 70.")
            st.write(" - >6 months: subscore maps 70 to 100.")
            st.markdown("Industry stability: categorical mapping (numerical subscores):")
            st.write(" - Stable: subscore = 90.")
            st.write(" - Moderate: subscore = 60.")
            st.write(" - Unstable: subscore = 25.")
            st.markdown("Age mapping:")
            st.write(" - <=30 years: subscore = 90.")
            st.write(" - 31 to 40: subscore = 75.")
            st.write(" - 41 to 55: subscore = 50.")
            st.write(" - 56 to 65: subscore = 30.")
            st.write(" - >65: subscore = 10.")
            st.markdown("Expected salary growth mapping:")
            st.write(" - <0%: subscore = 10.")
            st.write(" - 0 to 2%: subscore = 30.")
            st.write(" - 2 to 5%: subscore = 60.")
            st.write(" - >5%: subscore = 85.")
            st.markdown("Dependents mapping:")
            st.write(" - 0: subscore = 90.")
            st.write(" - 1: subscore = 70.")
            st.write(" - 2: subscore = 50.")
            st.write(" - 3: subscore = 30.")
            st.write(" - 4+: subscore = 15.")
            st.markdown("Weighting summary: SLI (25%) and Income (20%) are the heaviest because liquidity and income determine forced selling risk. Expenses (15%), Industry (12%), Age (12%), Growth (8%), Dependents (8%).")

        with st.expander("Methodology: Requirement — Long (detailed explanation and formula)"):
            st.markdown("RRR: Required rate of return (compound annual growth rate):")
            st.write(" - Formula: RRR = (Target / Current)^(1 / horizon) - 1.")
            st.write(" - RRR tells us how fast capital needs to grow to meet the stated goal in the given time horizon.")
            st.markdown("Real return requirement:")
            st.write(" - Real requirement = RRR - inflation (both in percentage terms).")
            st.write(" - This adjusts required nominal growth for expected loss of purchasing power.")
            st.markdown("Shortfall:")
            st.write(" - Shortfall = Real requirement - Expected return.")
            st.write(" - A positive shortfall means the expected return is insufficient and additional risk must be taken.")
            st.markdown("Drawdown pressure:")
            st.write(" - Drawdown pressure = average historical drawdown / drawdown tolerance.")
            st.write(" - If historical drawdowns exceed tolerance, the path to the target is riskier in practice.")
            st.markdown("Requirement scoring:")
            st.write(" - We map these four dimensions into normalized subscores, then combine with weights: RRR 35%, RealReq 25%, Shortfall 25%, DrawPressure 15%.")

        # CSV download and disclaimer
        df_out = pd.DataFrame([{
            "age": age, "dependents": dependents, "annual_income": annual_income,
            "annual_fixed": annual_fixed, "annual_variable": annual_variable,
            "industry": industry, "expected_growth": expected_growth,
            "investable_assets": investable_assets, "annual_withdrawals": annual_withdrawals,
            "capacity_score": capacity_score, "target_wealth": target_wealth,
            "current_portfolio": current_portfolio, "horizon_years": horizon_years,
            "inflation": inflation, "expected_return": expected_return,
            "avg_drawdown": avg_drawdown, "drawdown_tolerance": drawdown_tolerance,
            "requirement_score": requirement_score
        }])
        csv = df_out.to_csv(index=False)
        st.download_button("Download inputs and result (CSV):", csv, file_name="risk_capacity_result.csv", mime="text/csv")

        with st.expander("Legal disclaimer:"):
            st.write("This tool provides educational information only and is not financial or investment advice. Consult a licensed financial professional before acting on outputs. We accept no liability for investment decisions made based on this tool.")

        st.markdown("---")
        st.write("Purpose: Produce an objective, explainable estimate of a client's financial risk capacity and the minimum risk required to reach their stated goals. Use with behavioral preference and professional judgment.")
    else:
        st.info("Press Calculate to compute scores. If you want instant updates while editing, enable 'Auto-update' above.")

if __name__ == "__main__":
    main()
