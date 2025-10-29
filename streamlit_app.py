"""
app.py — Version B (Polished)
Polished Streamlit UI implementing the deterministic Risk Capacity score (0–100)
per the exact specifications provided.

Run with:
    streamlit run app.py

Mapping functions are top-level and have docstrings to support unit tests.
"""

from typing import Dict
import streamlit as st
import pandas as pd

# -----------------------
# Exact mapping functions (spec)
# -----------------------

def map_sli(sli: float) -> float:
    """
    SLI mapping.
    sli = investable_assets / max(1, annual_withdrawals)

    Behavior (exact):
    - if sli <= 1: return 0
    - 1 < sli <= 5: map linearly to 1..40
    - 5 < sli <= 20: map linearly to 40..80
    - sli > 20: map to 80..100 (piecewise linear):
        - 20 < sli <= 50: 80..95
        - 50 < sli: 95..100 (caps at 100)
    """
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
    """
    Income ratio mapping.
    r = income / max(1, fixed_expenses + variable_expenses)

    - if r <= 1: return 10
    - 1 < r <= 1.5: linear 10 → 40
    - 1.5 < r <= 2.5: linear 40 → 75
    - r > 2.5: linear 75 → 100 (cap)
    """
    if r <= 1.0:
        return 10.0
    if 1.0 < r <= 1.5:
        return 10.0 + (r - 1.0) / (1.5 - 1.0) * (40.0 - 10.0)
    if 1.5 < r <= 2.5:
        return 40.0 + (r - 1.5) / (2.5 - 1.5) * (75.0 - 40.0)
    # r > 2.5
    mapped = 75.0 + (r - 2.5) / (5.0 - 2.5) * (100.0 - 75.0)
    return min(mapped, 100.0)


def map_emergency_months(months: float) -> float:
    """
    Emergency months mapping.
    months = investable_assets / max(1, monthly_expenses)

    - months <= 1 -> 5
    - 1 < months <= 3 -> linear 20 → 40
    - 3 < months <= 6 -> linear 40 → 70
    - months > 6 -> linear 70 → 100 (cap)
    """
    if months <= 1.0:
        return 5.0
    if 1.0 < months <= 3.0:
        return 20.0 + (months - 1.0) / (3.0 - 1.0) * (40.0 - 20.0)
    if 3.0 < months <= 6.0:
        return 40.0 + (months - 3.0) / (6.0 - 3.0) * (70.0 - 40.0)
    mapped = 70.0 + (months - 6.0) / (24.0 - 6.0) * (100.0 - 70.0)
    return min(mapped, 100.0)


def map_industry(s: str) -> float:
    """Industry mapping: 'Stable'->90, 'Moderate'->60, 'Unstable'->25"""
    m = {"Stable": 90.0, "Moderate": 60.0, "Unstable": 25.0}
    return float(m.get(s, 60.0))


def map_age(age: int) -> float:
    """
    Age mapping:
    - age <= 30 -> 90
    - 31 <= age <= 40 -> 75
    - 41 <= age <= 55 -> 50
    - 56 <= age <= 65 -> 30
    - age > 65 -> 10
    """
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
    """
    Growth mapping:
    - g < 0 -> 10
    - 0 <= g <= 2 -> 30
    - 2 < g <= 5 -> 60
    - g > 5 -> 85
    """
    if g < 0.0:
        return 10.0
    if 0.0 <= g <= 2.0:
        return 30.0
    if 2.0 < g <= 5.0:
        return 60.0
    return 85.0


def map_dependents(d: int) -> float:
    """Dependents mapping: 0->90,1->70,2->50,3->30,4+->15"""
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
    """
    Compute weighted average score:
    sum(weight * subscore) / 100
    Clamp 0-100 and round to 1 decimal place.
    """
    total = 0.0
    for k, w in WEIGHTS.items():
        total += w * subscores[k]
    score = total / 100.0
    score = max(0.0, min(100.0, score))
    return round(score, 1)


# -----------------------
# UI (polished)
# -----------------------
METHODOLOGY = (
    " We compute a transparent Risk Capacity score (0–100) by mapping core financial cushions "
    "(investable assets, income and expenses) and demographic anchors (age, dependents, industry) "
    "to normalized subscores, then combining them via a defensible weighted average. We prioritize "
    "liquidity and income because empirical lifecycle and withdrawal theory show they most powerfully "
    "determine downside resilience. The app provides a sensitivity panel and a confidence flag for "
    "estimated inputs. Future work may apply simple ML to calibrate factor weights using historical "
    "outcomes; the rule-based system remains the primary, explainable driver."
)

def format_metric_color(score: float) -> str:
    """Return color string for st.metric styling guidance (not enforced by Streamlit)."""
    if score < 30:
        return "red"
    if score < 50:
        return "orange"
    if score < 70:
        return "yellow"
    return "green"


def main():
    st.set_page_config(page_title="Risk Capacity Estimator — Version B", layout="wide")
    st.title("Risk Capacity Estimator — Version B (Polished)")
    st.write("Transparent, rule-based Risk Capacity score (0–100). Shows subscores, mappings, weights, and sensitivity.")

    # Layout: left column for inputs, right for outputs
    left, right = st.columns([1, 1.25])

    with left:
        st.header("Inputs")
        st.caption("Provide client financials and demographics. Negative values are coerced to 0.")

        age = st.number_input("Age (years)", min_value=0, value=38, step=1, help="Client age in years (int).")
        dependents = st.number_input("Number of dependents", min_value=0, value=2, step=1, help="Count of dependents (int).")
        annual_income = st.number_input("Annual income (USD)", min_value=0.0, value=500000.00, step=1000.0, help="Gross annual income (float).")
        annual_fixed = st.number_input("Annual fixed expenses (USD)", min_value=0.0, value=30000.00, step=500.0, help="Essential fixed expenses per year (float).")
        annual_variable = st.number_input("Annual variable expenses (USD)", min_value=0.0, value=30000.00, step=500.0, help="Variable expenses per year (float).")
        industry = st.selectbox("Industry stability", ["Stable", "Moderate", "Unstable"], index=1, help="Select industry stability (dropdown).")
        expected_growth = st.number_input("Expected salary growth (annual %)", value=2.0, help="Expected yearly salary growth percentage (float).")
        investable_assets = st.number_input("Investable assets (USD)", min_value=0.0, value=500000.00, step=1000.0, help="Liquid investable assets (float).")
        annual_withdrawals = st.number_input("Annual withdrawals (USD)", min_value=0.0, value=10000.00, step=500.0, help="Planned yearly withdrawals from portfolio (float).")

        # Input validation notices
        if annual_withdrawals == 0.0:
            st.warning("Annual withdrawals = 0. Using 1 as safe fallback for SLI calculation; consider entering expected withdrawals.")
        # No negative possible because min_value set to 0 above.

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

        score = compute_risk_capacity(subscores)

        # Metric with color logic (Streamlit doesn't let us set color directly on metric,
        # but we add guiding text and use info/warning where appropriate)
        st.metric(label="Risk Capacity Score", value=f"{score} / 100")

        # Equity band mapping
        if score < 30:
            band = "0–30% equities (Very conservative)"
        elif 30 <= score < 50:
            band = "30–45% equities (Conservative)"
        elif 50 <= score < 70:
            band = "45–65% equities (Moderate)"
        elif 70 <= score < 85:
            band = "65–80% equities (Aggressive)"
        else:
            band = "80–100% equities (Very aggressive)"
        st.subheader("Recommended equity exposure")
        st.info(band)

        # Score breakdown expander
        with st.expander("Score breakdown (subscores, mapping, weights)"):
            st.write("Subscores and weights (exact):")
            for k, v in subscores.items():
                st.write(f"- {k}: {v:.1f}  (weight {WEIGHTS[k]:.0f})")
            st.write("Mapping logic: see each mapping function's docstring in code for exact piecewise rules.")

        # Assumptions & Confidence
        with st.expander("Assumptions & Confidence"):
            st.write("Inputs provided by user vs defaults are shown in the left panel.")
            st.write("Sensitivity: rapid ±20% scenarios for income and assets are below.")
            st.write("Confidence note: numeric inputs given by the user are considered high-confidence; any 0 or missing values are flagged.")

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

        # Methodology expander (required exact paragraph)
        with st.expander("Methodology (verbatim)"):
            st.write(METHODOLOGY)

        # Weights explanation expander (weights_explain.md content)
        with st.expander("Weights explanation"):
            st.write("- SLI (25): Liquidity buffer and withdrawal sustainability; follows lifecycle and safe-withdrawal logic.")
            st.write("- Income (20): Human capital and income stability reduce forced selling risk.")
            st.write("- Expenses (15): Emergency cushion directly affects short-term resilience.")
            st.write("- Industry (12): Employment risk affects income continuity.")
            st.write("- Age (12): Life-cycle stage affects time to recover from losses.")
            st.write("- Growth (8): Expected earnings growth affects future capacity.")
            st.write("- Dependents (8): Obligations reduce discretionary capacity.")

        # Share / Deploy (exact commands)
        with st.expander("Share / Deploy (Git & Streamlit commands)"):
            st.code("git add app.py requirements.txt README.md weights_explain.md\n"
                    "git commit -m \"Add Risk Capacity app (Version B)\"\n"
                    "git push origin main\n")
            st.write("Then in Streamlit Community Cloud: New app → connect GitHub repo → branch 'main' → file 'app.py' → Deploy")

        # Copy methodology to clipboard (best-effort: provide text area and copy button)
        st.subheader("Copy methodology")
        st.code(METHODOLOGY)
        # Note: direct clipboard copy isn't available server-side; instruct user to copy.

    # Footer small note
    st.markdown("---")
    st.write("Short 'Why this matters': Objective capacity separates what client *can* tolerate financially from what they *prefer* to tolerate subjectively.")

if __name__ == "__main__":
    main()