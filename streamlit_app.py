"""
app.py — Dark theme, UX polish
Run with:
    streamlit run app.py
"""

from typing import Dict
import streamlit as st
import pandas as pd

# -----------------------
# Simple config
# -----------------------
STEP_INVESTABLE = 2500
STEP_INCOME = 1000
STEP_FIXED = 500
STEP_VARIABLE = 500
STEP_WITHDRAW = 100
STEP_GROWTH = 0.1

# -----------------------
# Mapping functions (unchanged logic, cleaned)
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
    missing = [k for k in WEIGHTS.keys() if k not in subscores]
    if missing:
        raise ValueError(f"Missing subscores: {missing}")
    total = sum(WEIGHTS[k] * float(subscores[k]) for k in WEIGHTS.keys())
    score = total / 100.0
    return round(max(0.0, min(100.0, score)), 1)

# -----------------------
# Helpers: formatting + human explanations
# -----------------------
def fmt_num(x: float) -> str:
    # show integer when whole, else one decimal
    if abs(x - round(x)) < 1e-9:
        return str(int(round(x)))
    return f"{round(x,1):.1f}".rstrip('0').rstrip('.')

def zone_sentence(component: str, raw_value: float, subscore: float) -> str:
    # human-friendly one-line explanation for the specific input instance
    if component == "SLI":
        if raw_value <= 1:
            zone = "No liquid cushion"
        elif raw_value <= 5:
            zone = "Low cushion"
        elif raw_value <= 20:
            zone = "Moderate cushion"
        else:
            zone = "Very strong cushion"
        return f"SLI = {fmt_num(raw_value)} years → {zone}. More years means more downside resilience."
    if component == "Income":
        r = raw_value
        if r <= 1:
            zone = "Income covers ≤ expenses"
        elif r <= 1.5:
            zone = "Income modestly above expenses"
        elif r <= 2.5:
            zone = "Income comfortably above expenses"
        else:
            zone = "High income relative to expenses"
        return f"Income ratio = {round(r,2)} → {zone}. Larger ratio reduces forced-selling risk."
    if component == "Expenses":
        m = raw_value
        if m <= 1:
            zone = "Under 1 month emergency cushion"
        elif m <= 3:
            zone = "1–3 months emergency cushion"
        elif m <= 6:
            zone = "3–6 months emergency cushion"
        else:
            zone = "6+ months emergency cushion"
        return f"Emergency months = {fmt_num(m)} → {zone}. Larger cushion improves short-term stability."
    if component == "Industry":
        return f"Industry stability labeled '{raw_value}'. Stable industries imply lower job/income disruption risk."
    if component == "Age":
        return f"Age = {int(raw_value)}. Younger investors usually have longer recovery horizon after losses."
    if component == "Growth":
        return f"Expected salary growth = {fmt_num(raw_value)}% per year → implies future capacity to save/invest."
    if component == "Dependents":
        return f"{int(raw_value)} dependents → higher obligations reduce disposable capacity."
    return ""

# -----------------------
# UI
# -----------------------
PAGE_TITLE = "Risk Capacity Estimator"
PAGE_SUB = "Objective estimate (0–100) of how much investment risk a client can afford financially."

def main():
    st.set_page_config(page_title=PAGE_TITLE, layout="wide")
    # ---- dark theme CSS ----
    st.markdown(
        """
        <style>
        :root {
            --accent: #12c755;       /* vibrant green */
            --dark-bg: #071026;     /* very dark blue/near-black */
            --card: #0b1b2b;        /* slightly lighter dark card */
            --muted: #93a4b6;       /* muted text */
            --text: #e6eef6;        /* main text */
        }
        html, body, .stApp {
            background: var(--dark-bg) !important;
            color: var(--text) !important;
        }
        .stSidebar, .css-1d391kg { background: var(--dark-bg) !important; }
        .rc-card {
            background: var(--card);
            padding: 16px;
            border-radius: 12px;
            box-shadow: 0 6px 20px rgba(0,0,0,0.6);
            color: var(--text) !important;
        }
        .rc-score { font-size: 38px; font-weight:700; color: var(--accent); }
        h1, h2, h3, label, .stCaption, .stText, .stMarkdown {
            color: var(--text) !important;
        }
        /* Inputs styling (force readable inputs on dark) */
        input, select, textarea {
            background: #0f2a3f !important;
            color: var(--text) !important;
            border-radius: 6px !important;
            border: 1px solid rgba(255,255,255,0.06) !important;
        }
        /* Buttons */
        .stButton>button, .stDownloadButton>button {
            background: var(--accent) !important;
            color: #031014 !important;
            font-weight: 600;
            border-radius: 8px !important;
            padding: 8px 12px !important;
        }
        /* Table text */
        .stTable td, .stTable th { color: var(--text) !important; }
        /* make the small captions easier to see */
        .stCaption { color: var(--muted) !important; }
        </style>
        """, unsafe_allow_html=True
    )

    # Title & subtitle (consumer-facing)
    st.title(PAGE_TITLE)
    st.write(PAGE_SUB)

    left, right = st.columns([1, 1.25])
    with left:
        st.header("Inputs")
        st.caption("Fill the fields below with client data. The score updates live as you change values.")
        age = st.number_input("Age (years)", min_value=0, value=39, step=1, help="Client age in years.")
        dependents = st.number_input("Number of dependents", min_value=0, value=2, step=1, help="How many dependents rely on the client.")
        annual_income = st.number_input("Annual income (USD)", min_value=0, value=500000, step=STEP_INCOME, format="%d")
        annual_fixed = st.number_input("Annual fixed expenses (USD)", min_value=0, value=30000, step=STEP_FIXED, format="%d")
        annual_variable = st.number_input("Annual variable expenses (USD)", min_value=0, value=30000, step=STEP_VARIABLE, format="%d")
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

        # Score card
        st.markdown(f"<div class='rc-card'><div class='rc-score'>{fmt_num(score)} / 100</div></div>", unsafe_allow_html=True)

        # Equity band
        if score < 30:
            st.warning("0–30% equities (Very conservative)")
        elif 30 <= score < 50:
            st.info("30–45% equities (Conservative)")
        elif 50 <= score < 70:
            st.info("45–65% equities (Moderate)")
        elif 70 <= score < 85:
            st.success("65–80% equities (Aggressive)")
        else:
            st.success("80–100% equities (Very aggressive)")

        # Score breakdown (human-friendly)
        with st.expander("Score breakdown — details for this input"):
            rows = []
            ordered_keys = ["SLI", "Income", "Expenses", "Industry", "Age", "Growth", "Dependents"]
            for i, key in enumerate(ordered_keys, start=1):
                sub = subscores[key]
                # raw inputs for a couple items:
                raw_val = {
                    "SLI": sli_value,
                    "Income": income_ratio,
                    "Expenses": months,
                    "Industry": industry,
                    "Age": age,
                    "Growth": expected_growth,
                    "Dependents": dependents
                }[key]
                explanation = zone_sentence(key, raw_val, sub)
                rows.append({
                    "No": i,
                    "Component": key,
                    "Subscore": fmt_num(sub),
                    "Weight": f"{int(WEIGHTS[key])}%",
                    "Explanation": explanation
                })
            df_break = pd.DataFrame(rows)
            st.table(df_break)

        # Sensitivity panel + user-friendly explanation
        with st.expander("Sensitivity scenarios (what & why)"):
            st.write("Sensitivity scenarios show how the overall score moves if income or investable assets change by ±20%. This tests whether the recommendation is robust to realistic shocks.")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Income -20%"):
                    new_income = annual_income * 0.8
                    new_income_ratio = new_income / max(1.0, (annual_fixed + annual_variable))
                    subs2 = subscores.copy()
                    subs2["Income"] = map_income_ratio(new_income_ratio)
                    st.write("Score with Income -20%:", fmt_num(compute_risk_capacity(subs2)))
                if st.button("Income +20%"):
                    new_income = annual_income * 1.2
                    new_income_ratio = new_income / max(1.0, (annual_fixed + annual_variable))
                    subs2 = subscores.copy()
                    subs2["Income"] = map_income_ratio(new_income_ratio)
                    st.write("Score with Income +20%:", fmt_num(compute_risk_capacity(subs2)))
            with col2:
                if st.button("Assets -20%"):
                    new_assets = investable_assets * 0.8
                    sli2 = new_assets / max(1.0, annual_withdrawals)
                    subs2 = subscores.copy()
                    subs2["SLI"] = map_sli(sli2)
                    st.write("Score with Assets -20%:", fmt_num(compute_risk_capacity(subs2)))
                if st.button("Assets +20%"):
                    new_assets = investable_assets * 1.2
                    sli2 = new_assets / max(1.0, annual_withdrawals)
                    subs2 = subscores.copy()
                    subs2["SLI"] = map_sli(sli2)
                    st.write("Score with Assets +20%:", fmt_num(compute_risk_capacity(subs2)))

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

        # Methodology (concise)
        with st.expander("Methodology — short"):
            st.write("This tool maps liquidity (SLI), income vs expenses, emergency cushion, industry stability, age, expected salary growth, and dependents into normalized subscores, then combines them with a transparent weighted average to produce an objective risk capacity (0–100). We prioritize liquidity and income because those most directly determine whether the client can survive short-term drawdowns without forced selling.")

    # footer (clearer)
    st.markdown("---")
    st.write("Purpose: provide an objective, explainable estimate of how much financial risk a client can afford. Use this alongside behavioral preference and your advisor judgment when choosing asset allocation.")

if __name__ == "__main__":
    main()
