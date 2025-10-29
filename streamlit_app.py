"""
app.py — Dark theme, UX polish + long methodology + weight ranking + disclaimer
Run with:
    streamlit run app.py
"""

from typing import Dict
import streamlit as st
import pandas as pd

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
# Mapping functions (same deterministic logic as before)
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
# Weights & compute
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
# Helpers (formatting + human lines)
# -----------------------
def fmt_num(x: float) -> str:
    if abs(x - round(x)) < 1e-9:
        return str(int(round(x)))
    return f"{round(x,1):.1f}".rstrip('0').rstrip('.')

def zone_sentence(component: str, raw_value: float) -> str:
    if component == "SLI":
        if raw_value <= 1:
            zone = "No meaningful liquid cushion (≤1 year)."
        elif raw_value <= 5:
            zone = "Low cushion (1–5 years)."
        elif raw_value <= 20:
            zone = "Moderate cushion (5–20 years)."
        else:
            zone = "Very strong cushion (>20 years)."
        return f"SLI = {fmt_num(raw_value)} years — {zone} Larger SLI => stronger resilience to withdrawals/immediate shocks."
    if component == "Income":
        r = raw_value
        if r <= 1:
            z = "Income ≤ expenses (high risk of forced selling)."
        elif r <= 1.5:
            z = "Income modestly above expenses."
        elif r <= 2.5:
            z = "Income comfortably above expenses."
        else:
            z = "High income vs expenses (strong buffer)."
        return f"Income ratio = {round(r,2)} — {z} Higher ratio reduces selling pressure during downturns."
    if component == "Expenses":
        m = raw_value
        if m <= 1:
            z = "Under 1 month emergency cushion."
        elif m <= 3:
            z = "1–3 months."
        elif m <= 6:
            z = "3–6 months."
        else:
            z = "6+ months."
        return f"Emergency months = {fmt_num(m)} — {z} Bigger cushion improves short-term survival without liquidating assets."
    if component == "Industry":
        return f"Industry stability = {raw_value}. Stable industries imply reduced income-disruption risk."
    if component == "Age":
        return f"Age = {int(raw_value)}. Younger investors have longer recovery horizons (higher capacity for growth risk)."
    if component == "Growth":
        return f"Expected salary growth = {fmt_num(raw_value)}% p.a. Higher growth increases future capacity to bear risk."
    if component == "Dependents":
        return f"Dependents = {int(raw_value)}. More dependents reduce discretionary capacity and increase required safety."
    return ""

# -----------------------
# UI + CSS
# -----------------------
def main():
    st.set_page_config(page_title="Risk Capacity Estimator", layout="wide")
    # CSS: dark theme, readable selects/inputs, compact widths
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
        .rc-card { background: var(--card); padding: 14px; border-radius: 10px; color: var(--text);}
        .rc-score { font-size:36px; font-weight:700; color: var(--accent); }
        input, select, textarea { background: #0f2a3f !important; color: var(--text) !important; border-radius:6px !important; border:1px solid rgba(255,255,255,0.06) !important; padding:6px !important; }
        .stButton>button, .stDownloadButton>button { background: var(--accent) !important; color: #031014 !important; font-weight:600; border-radius:8px !important; padding:8px 12px !important; }
        /* limit input widths so there's not a huge empty trailing space */
        .stNumberInput, .stSelectbox { max-width: 320px; }
        /* make dataframe columns readable and avoid vertical letter-wrapping */
        .stDataFrame table { table-layout: auto !important; }
        /* small caption color */
        .stCaption { color: var(--muted) !important; }
        </style>
        """, unsafe_allow_html=True
    )

    st.title("Risk Capacity Estimator")
    st.write("Objective estimate (0–100) of how much investment risk a client can afford financially.")

    left, right = st.columns([0.95, 1.25])
    with left:
        st.header("Inputs")
        st.caption("Fill the fields below. Use realistic values; missing values reduce confidence.")
        age = st.number_input("Age (years)", min_value=0, value=39, step=1)
        dependents = st.number_input("Number of dependents", min_value=0, value=2, step=1)
        annual_income = st.number_input("Annual income (USD)", min_value=0, value=500000, step=STEP_INCOME, format="%d")
        annual_fixed = st.number_input("Annual fixed expenses (USD)", min_value=0, value=30000, step=STEP_FIXED, format="%d")
        annual_variable = st.number_input("Annual variable expenses (USD)", min_value=0, value=30000, step=STEP_VARIABLE, format="%d")
        # industry is a select; CSS forces readable colors
        industry = st.selectbox("Industry stability", ["Stable", "Moderate", "Unstable"], index=1)
        expected_growth = st.number_input("Expected salary growth (annual %)", value=2.0, step=STEP_GROWTH, format="%.2f")
        investable_assets = st.number_input("Investable assets (USD)", min_value=0, value=500000, step=STEP_INVESTABLE, format="%d")
        annual_withdrawals = st.number_input("Annual withdrawals (USD)", min_value=0, value=10000, step=STEP_WITHDRAW, format="%d")

        if annual_withdrawals == 0:
            st.warning("Annual withdrawals = 0. Using 1 as fallback for SLI calculation; consider entering expected withdrawals.")

    with right:
        st.header("Result")
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

        score = compute_risk_capacity(subscores)
        st.markdown(f"<div class='rc-card'><div class='rc-score'>{fmt_num(score)} / 100</div></div>", unsafe_allow_html=True)

        # equity guidance
        if score < 30:
            st.warning("Recommended equity exposure: 0–30% (Very conservative)")
        elif 30 <= score < 50:
            st.info("Recommended equity exposure: 30–45% (Conservative)")
        elif 50 <= score < 70:
            st.info("Recommended equity exposure: 45–65% (Moderate)")
        elif 70 <= score < 85:
            st.success("Recommended equity exposure: 65–80% (Aggressive)")
        else:
            st.success("Recommended equity exposure: 80–100% (Very aggressive)")

        # Build ranking map (weight rank: 1 = heaviest)
        sorted_weights = sorted(WEIGHTS.items(), key=lambda kv: -kv[1])
        rank_map = {k: i+1 for i, (k, _) in enumerate(sorted_weights)}

        # Score breakdown table (human friendly)
        with st.expander("Score breakdown — this case (readable)"):
            rows = []
            # Order rows by weight rank (heaviest first) so team sees what matters most
            ordered_keys = [k for k, _ in sorted_weights]
            for i, key in enumerate(ordered_keys, start=1):
                raw_val = {
                    "SLI": sli_value,
                    "Income": income_ratio,
                    "Expenses": months,
                    "Industry": industry,
                    "Age": age,
                    "Growth": expected_growth,
                    "Dependents": dependents
                }[key]
                rows.append({
                    "Rank (by weight)": rank_map[key],
                    "Risk factor": key,
                    "Value (this input)": fmt_num(raw_val) if key not in ["Industry","Age","Dependents"] else str(raw_val),
                    "Subscore": fmt_num(subscores[key]),
                    "Weight": f"{int(WEIGHTS[key])}%",
                    "Why this matters (this input)": zone_sentence(key, raw_val)
                })
            df_break = pd.DataFrame(rows)
            # show as dataframe so it doesn't wrap letters vertically
            st.dataframe(df_break, width=880, height=240)

        # Sensitivity panel explanation + buttons
        with st.expander("Sensitivity scenarios (what they do & why)"):
            st.write("These scenarios demonstrate how the final risk score moves if key cushions shift by realistic shocks.")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Income -20%"):
                    new_income_ratio = (annual_income * 0.8) / max(1.0, (annual_fixed + annual_variable))
                    subs2 = subscores.copy(); subs2["Income"] = map_income_ratio(new_income_ratio)
                    st.write("Score with Income -20%:", fmt_num(compute_risk_capacity(subs2)))
                if st.button("Income +20%"):
                    new_income_ratio = (annual_income * 1.2) / max(1.0, (annual_fixed + annual_variable))
                    subs2 = subscores.copy(); subs2["Income"] = map_income_ratio(new_income_ratio)
                    st.write("Score with Income +20%:", fmt_num(compute_risk_capacity(subs2)))
            with col2:
                if st.button("Assets -20%"):
                    sli2 = (investable_assets * 0.8) / max(1.0, annual_withdrawals)
                    subs2 = subscores.copy(); subs2["SLI"] = map_sli(sli2)
                    st.write("Score with Assets -20%:", fmt_num(compute_risk_capacity(subs2)))
                if st.button("Assets +20%"):
                    sli2 = (investable_assets * 1.2) / max(1.0, annual_withdrawals)
                    subs2 = subscores.copy(); subs2["SLI"] = map_sli(sli2)
                    st.write("Score with Assets +20%:", fmt_num(compute_risk_capacity(subs2)))

        # Methodology short + long
        with st.expander("Methodology — short (what this does)"):
            st.write("We map core cushions (liquidity, income vs expenses, emergency months), plus demographic anchors (age, dependents, industry) and expected salary growth into normalized subscores. Those subscores are combined with transparent weights into a 0–100 objective Risk Capacity score. The result is meant to separate what the client *can* afford financially from what they *prefer* psychologically.")
        with st.expander("Methodology — long (detailed ranges & why)"):
            st.markdown("**SLI — Savings Longevity Index (investable assets / annual withdrawals)**")
            st.write("- ≤1 year → subscore ≈ 0 : no cushion; extremely fragile to withdrawals.")
            st.write("- 1–5 years → subscore maps 1 → 40 : low cushion; needs conservative posture.")
            st.write("- 5–20 years → subscore maps 40 → 80 : moderate cushion; supports some growth risk.")
            st.write("- >20 years → subscore maps 80 → 100 : strong cushion; can tolerate higher allocation.")
            st.markdown("**Income ratio — Income ÷ (fixed + variable expenses)**")
            st.write("- ≤1 : income does not cover expenses — forced selling risk (low subscore).")
            st.write("- 1–1.5 : modest cover (low–moderate).")
            st.write("- 1.5–2.5 : comfortable cover (moderate–high).")
            st.write("- >2.5 : high cover (high subscore).")
            st.markdown("**Emergency months — investable assets / monthly expenses**")
            st.write("- <1 month: very weak short-term buffer.")
            st.write("- 1–3 months: minimal coverage.")
            st.write("- 3–6 months: healthy buffer.")
            st.write("- >6 months: strong buffer.")
            st.markdown("**Industry stability**")
            st.write("- Stable → high subscore (less job/income risk).")
            st.write("- Moderate → middle subscore.")
            st.write("- Unstable → lower subscore (higher income disruption risk).")
            st.markdown("**Age**")
            st.write("- Younger investors → higher subscore for capacity (longer recovery horizon).")
            st.write("- Older investors → lower subscore (shorter time to recover from drawdowns).")
            st.markdown("**Expected salary growth**")
            st.write("- Negative/low growth → lower subscore (less future capacity).")
            st.write("- Higher growth → higher subscore (more ability to save later).")
            st.markdown("**Dependents**")
            st.write("- More dependents → lower subscore (more obligations reduce capacity).")
            st.markdown("**Weighting rationale (summary)**")
            st.write("- We give highest weight to liquidity and income because empirical withdrawal & lifecycle theory show these drive forced selling risk. Age & industry are next because they determine recovery time and income stability. Growth and dependents are smaller but still meaningful.")
            st.write("If you need a citation-style justification for each weight to include in the midterm report, I can generate 1–2 short evidence pointers for each weight (e.g., lifecycle investing theory, safe withdrawal research).")

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
            "score": score
        }])
        csv = df_out.to_csv(index=False)
        st.download_button("Download inputs & result (CSV)", csv, file_name="risk_capacity_result.csv", mime="text/csv")

        # Legal disclaimer (clear, short)
        with st.expander("Legal disclaimer (must read)"):
            st.write("This tool provides educational information only and is not financial or investment advice. Nothing on this site constitutes an offer or solicitation to buy or sell securities. Always consult a licensed financial professional before acting on information from this tool. We accept no liability for investment decisions made based on outputs from this calculator.")

    # footer: concise purpose
    st.markdown("---")
    st.write("Purpose: Produce an objective, explainable estimate of a client's financial risk capacity. Use it alongside behavioral preference and professional judgment.")

if __name__ == "__main__":
    main()
