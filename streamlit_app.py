# app.py
import streamlit as st
import math

st.set_page_config(page_title="Risk Capacity Calculator", layout="centered")

st.title("Risk Capacity Calculator (0-100)")
st.markdown("Enter the investor's info. This tool computes a transparent, weighted Risk Capacity score and suggests an equity range.")

# --- Inputs ---
age = st.number_input("Age (years)", min_value=18, max_value=120, value=38)
dependents = st.number_input("Number of dependents", min_value=0, max_value=10, value=2)
income = st.number_input("Annual income (USD)", min_value=0.0, value=500000.0, step=1000.0, format="%.2f")
fixed_expenses = st.number_input("Annual fixed expenses (USD)", min_value=0.0, value=30000.0, step=100.0, format="%.2f")
variable_expenses = st.number_input("Annual variable expenses (USD)", min_value=0.0, value=30000.0, step=100.0, format="%.2f")
industry = st.selectbox("Industry stability", options=["Stable","Moderate","Unstable"], index=1)
expected_growth = st.number_input("Expected salary growth (annual %)", value=2.0, format="%.2f")
investable_assets = st.number_input("Investable assets (USD)", min_value=0.0, value=500000.0, step=1000.0, format="%.2f")
annual_withdrawals = st.number_input("Annual withdrawals (USD)", min_value=0.0, value=10000.0, step=100.0, format="%.2f")

# --- Normalization helper functions ---
def map_sli(sli):
    if sli <= 1:
        return 0
    if sli <= 5:
        return 1 + (sli - 1) * (39/4)  # linear 1..40
    if sli <= 20:
        return 40 + (sli - 5) * (40/15)  # linear 40..80
    return 90 if sli > 50 else 80 + min((sli - 20) * (10/30),10)  # >20 -> 80..100, with a cap

def map_income_ratio(r):
    if r <= 1:
        return 10
    if r <= 1.5:
        return 10 + (r - 1) * (30/0.5)
    if r <= 2.5:
        return 40 + (r - 1.5) * (35/1.0)
    return 75 + min((r - 2.5) * (25/5.0),25)

def map_emergency_months(months):
    if months <= 1:
        return 5
    if months <= 3:
        return 20 + (months - 1) * (20/2)
    if months <= 6:
        return 40 + (months - 3) * (30/3)
    return 70 + min((months - 6) * (30/24),30)

def map_industry(s):
    return {"Stable":90,"Moderate":60,"Unstable":25}.get(s,60)

def map_age(a):
    if a <= 30: return 90
    if a <= 40: return 75
    if a <= 55: return 50
    if a <= 65: return 30
    return 10

def map_growth(g):
    if g < 0: return 10
    if g <= 2: return 30
    if g <= 5: return 60
    return 85

def map_dependents(d):
    if d == 0: return 90
    if d == 1: return 70
    if d == 2: return 50
    if d == 3: return 30
    return 15

# --- Compute subscores ---
sli = investable_assets / (annual_withdrawals if annual_withdrawals>0 else 1)
s_sli = map_sli(sli)

income_ratio = income / max(1.0, (fixed_expenses + variable_expenses))
s_income = map_income_ratio(income_ratio)

monthly_expenses = (fixed_expenses + variable_expenses) / 12.0
emergency_months = investable_assets / max(1.0, monthly_expenses)
s_expenses = map_emergency_months(emergency_months)

s_industry = map_industry(industry)
s_age = map_age(age)
s_growth = map_growth(expected_growth)
s_dependents = map_dependents(int(dependents))

# --- Weights (sum to 100) ---
w = {"sli":25, "income":20, "expenses":15, "industry":12, "age":12, "growth":8, "dependents":8}

# Weighted sum
raw_score = (w["sli"]*s_sli + w["income"]*s_income + w["expenses"]*s_expenses +
             w["industry"]*s_industry + w["age"]*s_age + w["growth"]*s_growth +
             w["dependents"]*s_dependents) / 100.0

risk_capacity_score = max(0.0, min(100.0, round(raw_score,1)))

# --- Output ---
st.metric("Risk Capacity Score", f"{risk_capacity_score} / 100")

# Equity band guidance:
def equity_band(score):
    if score < 30: return "0–30% equities (Very conservative)"
    if score < 50: return "30–45% equities (Conservative)"
    if score < 70: return "45–65% equities (Moderate)"
    if score < 85: return "65–80% equities (Aggressive)"
    return "80–100% equities (Very aggressive)"

st.write("Recommended equity exposure (guideline):", equity_band(risk_capacity_score))

# Breakdown expander
with st.expander("See score breakdown & subscores"):
    st.write("Subscores (0–100):")
    st.write({
        "SLI (years)": round(sli,2),
        "SLI subscore": round(s_sli,1),
        "Income ratio": round(income_ratio,2),
        "Income subscore": round(s_income,1),
        "Emergency months": round(emergency_months,1),
        "Expenses subscore": round(s_expenses,1),
        "Industry subscore": s_industry,
        "Age subscore": s_age,
        "Growth subscore": s_growth,
        "Dependents subscore": s_dependents
    })
    st.write("Weights used (percent):", w)

# Sensitivity quick panel
with st.expander("Quick sensitivity: change assets/income by ±20%"):
    assets_down = investable_assets * 0.8
    assets_up = investable_assets * 1.2
    # recompute function for quick sim
    def compute_score(a_assets, a_income):
        sli_v = a_assets / max(1.0, annual_withdrawals)
        si = map_sli(sli_v)
        ir = a_income / max(1.0, (fixed_expenses+variable_expenses))
        s_ir = map_income_ratio(ir)
        em = a_assets / max(1.0, monthly_expenses)
        se = map_emergency_months(em)
        val = (w["sli"]*si + w["income"]*s_ir + w["expenses"]*se + w["industry"]*s_industry +
               w["age"]*s_age + w["growth"]*s_growth + w["dependents"]*s_dependents)/100.0
        return round(max(0.0,min(100.0,val)),1)
    st.write("Score w/ assets -20%:", compute_score(assets_down, income))
    st.write("Score w/ assets +20%:", compute_score(assets_up, income))
    st.write("Score w/ income -20%:", compute_score(investable_assets, income*0.8))
    st.write("Score w/ income +20%:", compute_score(investable_assets, income*1.2))

st.markdown("---")
st.caption("Methodology: subscores are mapped from standardized buckets. Weights reflect liquidity (SLI), income, and expenses as primary drivers of loss resilience. See README for full justification and references to lifecycle investing and portfolio theory.")
