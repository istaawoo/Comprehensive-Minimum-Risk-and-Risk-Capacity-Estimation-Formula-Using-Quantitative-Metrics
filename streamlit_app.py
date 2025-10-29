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

def compute_risk_requirement(rrr: float, real_pct: float, short_pct: float, draw_ratio: float) -> float:
    sc_rrr = map_rrr(rrr)
    sc_real = map_realreq(real_pct)
    sc_short = map_shortfall(short_pct)
    sc_draw = map_drawimpact(draw_ratio)
    total = REQ_WEIGHTS["RRR"] * sc_rrr + REQ_WEIGHTS["RealReq"] * sc_real + REQ_WEIGHTS["Shortfall"] * sc_short + REQ_WEIGHTS["DrawImpact"] * sc_draw
    score = total / 100.0
    return round(max(0.0, min(100.0, score)), 1)

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
        .stNumberInput, .stSelectbox { max-width: 320px; }
        .stDataFrame table { table-layout: auto !important; }
        .stCaption { color: var(--muted) !important; }
        </style>
        """, unsafe_allow_html=True
    )

    st.title("Risk Capacity Estimator")
    st.write("Objective estimate (0-100) of how much investment risk a client can afford financially.")

    left, right = st.columns([1.0, 1.3])
    with left:
        st.header("Inputs")
        st.caption("Fill the fields below. Use realistic values; missing values reduce confidence.")
        age = st.number_input("Age (years)", min_value=0, value=39, step=1)
        dependents = st.number_input("Number of dependents", min_value=0, value=2, step=1)
        annual_income = st.number_input("Annual income (USD)", min_value=0, value=500000, step=STEP_INCOME, format="%d")
        annual_fixed = st.number_input("Annual fixed expenses (USD)", min_value=0, value=30000, step=STEP_FIXED, format="%d")
        annual_variable = st.number_input("Annual variable expenses (USD)", min_value=0, value=30000, step=STEP_VARIABLE, format="%d")

        # force choice: use radio to prevent typing
        industry = st.radio("Industry stability", ["Stable", "Moderate", "Unstable"], index=1)

        expected_growth = st.number_input("Expected salary growth (annual %)", value=2.0, step=STEP_GROWTH, format="%.2f")
        investable_assets = st.number_input("Investable assets (USD)", min_value=0, value=500000, step=STEP_INVESTABLE, format="%d")
        annual_withdrawals = st.number_input("Annual withdrawals (USD)", min_value=0, value=10000, step=STEP_WITHDRAW, format="%d")

        st.markdown("### Goal inputs (for Risk Requirement)")
        target_wealth = st.number_input("Target portfolio value (USD)", min_value=0, value=1500000, step=10000, format="%d")
        current_portfolio = st.number_input("Current portfolio value (USD)", min_value=0, value=500000, step=1000, format="%d")
        horizon_years = st.number_input("Time horizon (years)", min_value=1, value=10, step=1)
        inflation = st.number_input("Assumed inflation rate (%)", min_value=0.0, value=2.0, step=0.1, format="%.2f")
        expected_return = st.number_input("Expected annual return (%)", min_value=-10.0, value=6.0, step=0.1, format="%.2f")
        avg_drawdown = st.number_input("Average historical drawdown (%)", min_value=0.0, value=30.0, step=1.0, format="%.1f")
        drawdown_tolerance = st.number_input("Drawdown tolerance (%)", min_value=0.0, value=15.0, step=1.0, format="%.1f")

        if annual_withdrawals == 0:
            st.warning("Annual withdrawals = 0. Using 1 as fallback for SLI calculation; consider entering expected withdrawals.")

    with right:
        st.header("Results")

        # capacity calculations (existing)
        monthly_expenses = (annual_fixed + annual_variable) / 12.0
        sli_value = investable_assets / max(1.0, annual_withdrawals)
        income_ratio = annual_income / max(1.0, (annual_fixed + annual_variable))
        months = investable_assets / max(1.0, monthly_expenses)

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

        st.markdown(f"<div class='rc-card'><div class='rc-score'>{fmt_num(capacity_score)} / 100</div></div>", unsafe_allow_html=True)

        # Requirement calculations (new)
        # RRR = (T / C)^(1/n) - 1
        T = max(1.0, float(target_wealth))
        C = max(1.0, float(current_portfolio))
        n = max(1.0, float(horizon_years))
        rrr = math.pow(T / C, 1.0 / n) - 1.0
        real_req = (rrr * 100.0) - float(inflation)  # in percent
        shortfall = max(0.0, real_req - float(expected_return))
        draw_ratio = (float(avg_drawdown)) / max(float(drawdown_tolerance), 0.01)

        requirement_score = compute_risk_requirement(rrr, real_req, shortfall, draw_ratio)

        st.subheader("Risk requirement score (how aggressive must you be)")
        st.write(f"Requirement score: {fmt_num(requirement_score)} / 100")
        # interpret
        if requirement_score < 20:
            st.info("Goal requires little extra risk. Conservative approach feasible.")
        elif requirement_score < 45:
            st.info("Moderate risk needed to meet goal.")
        elif requirement_score < 70:
            st.warning("Significant risk needed; consider extending horizon or increasing savings.")
        else:
            st.error("High risk needed. Consider changing goal, time, or saving much more.")

        # alignment
        diff = capacity_score - requirement_score
        st.markdown("### Alignment check")
        if diff >= 10:
            st.success(f"Capacity exceeds requirement by {fmt_num(diff)} points. Goal is feasible within capacity.")
        elif diff >= -10:
            st.info(f"Capacity roughly matches requirement (diff {fmt_num(diff)}). Proceed with caution; detail execution and monitoring.")
        else:
            st.warning(f"Capacity is {fmt_num(-diff)} points below requirement. Reassess the plan: raise savings, extend horizon, or accept lower target.")

        # Show breakdown table (capacity)
        with st.expander("Score breakdown: Case-specific (readable)"):
            rows = []
            sorted_weights = sorted(WEIGHTS.items(), key=lambda kv: -kv[1])
            rank_map = {k: i+1 for i, (k, _) in enumerate(sorted_weights)}
            ordered_keys = [k for k, _ in sorted_weights]
            for key in ordered_keys:
                raw_val = {"SLI": sli_value, "Income": income_ratio, "Expenses": months, "Industry": industry, "Age": age, "Growth": expected_growth, "Dependents": dependents}[key]
                rows.append({
                    "Rank (by weight)": rank_map[key],
                    "Risk factor": key,
                    "Value (this input)": fmt_num(raw_val) if key not in ["Industry","Age","Dependents"] else str(raw_val),
                    "Subscore": fmt_num(subscores[key]),
                    "Weight": f"{int(WEIGHTS[key])}%",
                    "Why this matters (this input)": zone_sentence(key, raw_val)
                })
            df_break = pd.DataFrame(rows)
            st.dataframe(df_break, width=920, height=240)

        # Show requirement details
        with st.expander("Requirement details (how we computed it)"):
            st.write(f"RRR (annual) = {fmt_num(rrr*100)}%")
            st.write(f"Real return requirement = {fmt_num(real_req)}%")
            st.write(f"Shortfall = {fmt_num(shortfall)}%")
            st.write(f"Average drawdown = {fmt_num(avg_drawdown)}%")
            st.write(f"Drawdown tolerance = {fmt_num(drawdown_tolerance)}%")
            st.write(f"Drawdown ratio = {round(draw_ratio,2)}")
            st.write("Mapping rules: RRR and RealReq map higher values to higher requirement. Shortfall maps linearly 0-10% to 0-100. Draw ratio mapped to 0,25,60,100 buckets.")
            st.write("Weights: RRR 40%, RealReq 25%, Shortfall 20%, DrawImpact 15%.")

        # CSV download
        df_out = pd.DataFrame([{
            "age": age,
            "dependents": dependents,
            "annual_income": annual_income,
            "annual_fixed": annual_fixed,
            "annual_variable": annual_variable,
            "industry": industry,
            "expected_growth": expected_growth,
            "investable_assets": investable_assets,
            "annual_withdrawals": annual_withdrawals,
            "capacity_score": capacity_score,
            "target_wealth": target_wealth,
            "current_portfolio": current_portfolio,
            "horizon_years": horizon_years,
            "inflation": inflation,
            "expected_return": expected_return,
            "avg_drawdown": avg_drawdown,
            "drawdown_tolerance": drawdown_tolerance,
            "requirement_score": requirement_score
        }])
        csv = df_out.to_csv(index=False)
        st.download_button("Download inputs & result (CSV)", csv, file_name="risk_capacity_result.csv", mime="text/csv")

        # Legal disclaimer
        with st.expander("Legal disclaimer (must read)"):
            st.write("This tool provides educational information only and is not financial or investment advice. Nothing on this site constitutes an offer or solicitation to buy or sell securities. Always consult a licensed financial professional before acting on information from this tool. We accept no liability for investment decisions made based on outputs from this calculator.")

    st.markdown("---")
    st.write("Purpose: Produce an objective, explainable estimate of a client's financial risk capacity and the minimum risk required to reach their stated goals. Use together with preference and professional judgment.")

if __name__ == "__main__":
    main()
