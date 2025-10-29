"""
app.py — Version B (Polished) — fixed
 - Always auto-recomputes on input change (no hashing/recalc guard)
 - Fixed step sizes (investable_assets = 2,500 step)
 - Improved CSS for readable text and tasteful green accent
 - Small defensive checks, clearer mapping caps
Run with:
    streamlit run app.py
"""

from typing import Dict
import streamlit as st
import pandas as pd

# -----------------------
# Constants & limits
# -----------------------
SLI_HIGH_CAP = 200.0
INCOME_R_MAX = 10.0
EMERGENCY_MONTHS_MAX = 24.0

# Step config (change these to taste)
STEP_INVESTABLE = 2500
STEP_INCOME = 1000
STEP_FIXED = 500
STEP_VARIABLE = 500
STEP_WITHDRAW = 100
STEP_GROWTH = 0.1

# -----------------------
# Exact mapping functions (spec)
# -----------------------

def map_sli(sli: float) -> float:
    """See docstring in original; uses SLI_HIGH_CAP to cap extreme values."""
    if sli <= 1.0:
        return 0.0
    if 1.0 < sli <= 5.0:
        return 1.0 + (sli - 1.0) / (5.0 - 1.0) * (40.0 - 1.0)
    if 5.0 < sli <= 20.0:
        return 40.0 + (sli - 5.0) / (20.0 - 5.0) * (80.0 - 40.0)
    if 20.0 < sli <= 50.0:
        return 80.0 + (sli - 20.0) / (50.0 - 20.0) * (95.0 - 80.0)
    if sli > 50.0:
        mapped = 95.0 + (min(sli, SLI_HIGH_CAP) - 50.0) / (SLI_HIGH_CAP - 50.0) * (100.0 - 95.0)
        return min(mapped, 100.0)
    return 0.0


def map_income_ratio(r: float) -> float:
    """Income mapping with INCOME_R_MAX cap to avoid runaway extrapolation."""
    if r <= 1.0:
        return 10.0
    if 1.0 < r <= 1.5:
        return 10.0 + (r - 1.0) / (1.5 - 1.0) * (40.0 - 10.0)
    if 1.5 < r <= 2.5:
        return 40.0 + (r - 1.5) / (2.5 - 1.5) * (75.0 - 40.0)
    # r > 2.5
    mapped = 75.0 + (min(r, INCOME_R_MAX) - 2.5) / (INCOME_R_MAX - 2.5) * (100.0 - 75.0)
    return min(mapped, 100.0)


def map_emergency_months(months: float) -> float:
    """Emergency months mapping with EMERGENCY_MONTHS_MAX cap."""
    if months <= 1.0:
        return 5.0
    if 1.0 < months <= 3.0:
        return 20.0 + (months - 1.0) / (3.0 - 1.0) * (40.0 - 20.0)
    if 3.0 < months <= 6.0:
        return 40.0 + (months - 3.0) / (6.0 - 3.0) * (70.0 - 40.0)
    mapped = 70.0 + (min(months, EMERGENCY_MONTHS_MAX) - 6.0) / (EMERGENCY_MONTHS_MAX - 6.0) * (100.0 - 70.0)
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
    # boundaries chosen to be non-overlapping
    if g < 0.0:
        return 10.0
    if g < 2.0:   # 0.0 <= g < 2.0
        return 30.0
    if g < 5.0:   # 2.0 <= g < 5.0
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
# Weights (exact)
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
    # defensive check
    missing = [k for k in WEIGHTS.keys() if k not in subscores]
    if missing:
        raise ValueError(f"Missing subscores: {missing}")
    total = sum(WEIGHTS[k] * float(subscores[k]) for k in WEIGHTS.keys())
    score = total / 100.0
    return round(max(0.0, min(100.0, score)), 1)


# -----------------------
# UI (polished)
# -----------------------
METHODOLOGY = (
    "We compute a transparent Risk Capacity score (0–100) by mapping core financial cushions "
    "(investable assets, income and expenses) and demographic anchors (age, dependents, industry) "
    "to normalized subscores, then combining them via a defensible weighted average. We prioritize "
    "liquidity and income because empirical lifecycle and withdrawal theory show they most powerfully "
    "determine downside resilience. The app provides a sensitivity panel and a confidence flag for "
    "estimated inputs. Future work may apply simple ML to calibrate factor weights using historical "
    "outcomes; the rule-based system remains the primary, explainable driver."
)


def main():
    st.set_page_config(page_title="Risk Capacity Estimator — Version B", layout="wide")
    st.title("Risk Capacity Estimator — Version B (Polished)")
    st.write("Transparent, rule-based Risk Capacity score (0–100). Shows subscores, mappings, weights, and sensitivity.")

    # Layout: left column for inputs, right for outputs
    left, right = st.columns([1, 1.25])

    with left:
        st.header("Inputs")
        st.caption("Provide client financials and demographics. Negative values are coerced to 0.")

        # Defaults & steps tuned per request
        age = st.number_input("Age (years)", min_value=0, value=39, step=1, help="Client age in years (int).")
        dependents = st.number_input("Number of dependents", min_value=0, value=2, step=1, help="Count of dependents (int).")
        annual_income = st.number_input("Annual income (USD)", min_value=0, value=500000, step=STEP_INCOME, format="%d", help="Gross annual income.")
        annual_fixed = st.number_input("Annual fixed expenses (USD)", min_value=0, value=30000, step=STEP_FIXED, format="%d", help="Essential fixed expenses per year.")
        annual_variable = st.number_input("Annual variable expenses (USD)", min_value=0, value=30000, step=STEP_VARIABLE, format="%d", help="Variable expenses per year.")
        industry = st.selectbox("Industry stability", ["Stable", "Moderate", "Unstable"], index=1, help="Select industry stability (dropdown).")
        expected_growth = st.number_input("Expected salary growth (annual %)", value=2.0, step=STEP_GROWTH, format="%.2f", help="Expected yearly salary growth percentage (float).")
        investable_assets = st.number_input("Investable assets (USD)", min_value=0, value=500000, step=STEP_INVESTABLE, format="%d", help=f"Liquid investable assets. Step {STEP_INVESTABLE}.")
        annual_withdrawals = st.number_input("Annual withdrawals (USD)", min_value=0, value=10000, step=STEP_WITHDRAW, format="%d", help="Planned yearly withdrawals from portfolio.")

        if annual_withdrawals == 0:
            st.warning("Annual withdrawals = 0. Using 1 as safe fallback for SLI calculation; consider entering expected withdrawals.")

    with right:
        st.header("Results")
        # Derived values
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

        # Always compute (no hash/recalc guard) — Streamlit reruns on input change & file save
        score = compute_risk_capacity(subscores)

        # Improved CSS + readable text + tasteful green accent
        st.markdown(
            f"""
            <style>
            :root {{
                --accent: #129742;
                --bg: #f7faf9;
                --card: #ffffff;
                --text: #111827;
            }}
            html, body, .stApp {{
                background: var(--bg) !important;
                color: var(--text) !important;
            }}
            .rc-card {{
                background: var(--card);
                padding: 16px;
                border-radius: 12px;
                box-shadow: 0 6px 18px rgba(15,23,42,0.06);
                color: var(--text) !important;
            }}
            .rc-score {{ font-size:38px; font-weight:700; color: var(--accent); }}
            .stButton>button {{
                background: var(--accent) !important;
                color: white !important;
                border-radius: 8px !important;
                padding: 8px 12px !important;
            }}
            .stTable td, .stTable th {{ color: var(--text) !important; }}
            </style>
            """,
            unsafe_allow_html=True,
        )

        # Large colored score display using the requested green
        st.markdown(f"<div class='rc-card'><div class='rc-score'>{score} / 100</div></div>", unsafe_allow_html=True)

        # Equity band mapping + banner
        if score < 30:
            band = "0–30% equities (Very conservative)"
            st.warning(band)
        elif 30 <= score < 50:
            band = "30–45% equities (Conservative)"
            st.info(band)
        elif 50 <= score < 70:
            band = "45–65% equities (Moderate)"
            st.info(band)
        elif 70 <= score < 85:
            band = "65–80% equities (Aggressive)"
            st.success(band)
        else:
            band = "80–100% equities (Very aggressive)"
            st.success(band)

        # Score breakdown: clean table presentation
        with st.expander("Score breakdown (subscores, mapping, weights)"):
            mapping_text = {
                "SLI": "piecewise: <=1->0; 1-5->1-40; 5-20->40-80; >20->80-100",
                "Income": "ratio income/(fixed+variable): <=1->10; 1-1.5->10-40; 1.5-2.5->40-75; >2.5->75-100",
                "Expenses": "emergency months: <=1->5; 1-3->20-40; 3-6->40-70; >6->70-100",
                "Industry": "Stable->90; Moderate->60; Unstable->25",
                "Age": "<=30->90;31-40->75;41-55->50;56-65->30;>65->10",
                "Growth": "g<0->10;0-2->30;2-5->60;>5->85",
                "Dependents": "0->90;1->70;2->50;3->30;4+->15",
            }
            rows = []
            for k, v in subscores.items():
                rows.append({"Component": k, "Subscore": round(v, 1), "Weight": int(WEIGHTS[k]), "Mapping": mapping_text.get(k, "")})
            df_break = pd.DataFrame(rows)
            st.table(df_break)
            st.markdown("Mapping logic shown above; exact piecewise rules are implemented in the mapping functions.")

        # Small live captions for clarity
        st.caption(f"SLI (years) = {round(sli_value,2)} → subscore {round(subscores['SLI'],1)}")
        st.caption(f"Income ratio = {round(income_ratio,2)} → subscore {round(subscores['Income'],1)}")
        st.caption(f"Emergency months = {round(months,1)} → subscore {round(subscores['Expenses'],1)}")

        # Sensitivity panel: sliders/buttons for ±20% scenarios
        with st.container():
            st.subheader("Sensitivity scenarios")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Income -20%"):
                    new_income = annual_income * 0.8
                    income_ratio2 = new_income / max(1.0, (annual_fixed + annual_variable))
                    subs2 = subscores.copy()
                    subs2["Income"] = map_income_ratio(income_ratio2)
                    st.write("Score with Income -20%:", compute_risk_capacity(subs2))
                if st.button("Income +20%"):
                    new_income = annual_income * 1.2
                    income_ratio2 = new_income / max(1.0, (annual_fixed + annual_variable))
                    subs2 = subscores.copy()
                    subs2["Income"] = map_income_ratio(income_ratio2)
                    st.write("Score with Income +20%:", compute_risk_capacity(subs2))
            with col2:
                if st.button("Assets -20%"):
                    new_assets = investable_assets * 0.8
                    sli2 = new_assets / max(1.0, annual_withdrawals)
                    subs2 = subscores.copy()
                    subs2["SLI"] = map_sli(sli2)
                    st.write("Score with Assets -20%:", compute_risk_capacity(subs2))
                if st.button("Assets +20%"):
                    new_assets = investable_assets * 1.2
                    sli2 = new_assets / max(1.0, annual_withdrawals)
                    subs2 = subscores.copy()
                    subs2["SLI"] = map_sli(sli2)
                    st.write("Score with Assets +20%:", compute_risk_capacity(subs2))

        # Download CSV
        df = pd.DataFrame([{
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
        csv = df.to_csv(index=False)
        st.download_button("Download inputs & result (CSV)", csv, file_name="risk_capacity_result.csv", mime="text/csv")

        # Methodology expander
        with st.expander("Methodology (verbatim)"):
            st.write(METHODOLOGY)

        # Weights explanation expander
        with st.expander("Weights explanation"):
            st.write("- SLI (25): Liquidity buffer and withdrawal sustainability; follows lifecycle and safe-withdrawal logic.")
            st.write("- Income (20): Human capital and income stability reduce forced selling risk.")
            st.write("- Expenses (15): Emergency cushion directly affects short-term resilience.")
            st.write("- Industry (12): Employment risk affects income continuity.")
            st.write("- Age (12): Life-cycle stage affects time to recover from losses.")
            st.write("- Growth (8): Expected earnings growth affects future capacity.")
            st.write("- Dependents (8): Obligations reduce discretionary capacity.")

        # Share / Deploy guidance
        with st.expander("Share / Deploy (Git & Streamlit commands)"):
            st.code("git add app.py requirements.txt README.md\n"
                    "git commit -m \"Update app: UX, steps, styling\"\n"
                    "git push origin main\n")
            st.write("Then go to Streamlit Community Cloud → connect repo → select branch 'main' and file 'app.py' → Deploy. Pushing commits will auto-redeploy.")

    # Footer
    st.markdown("---")
    st.write("Short 'Why this matters': Objective capacity separates what client *can* tolerate financially from what they *prefer* to tolerate subjectively.")

if __name__ == "__main__":
    main()
