"""
Financial Risk Assessment Calculator

This application helps determine how much investment risk a person can handle (Risk Capacity)
and how much risk they need to take to reach their financial goals (Risk Requirement).

What this calculator does:
1. Takes in personal financial information (income, expenses, savings, etc.)
2. Analyzes multiple factors that affect someone's ability to handle financial risk
3. Provides a score from 0 to 100 for both risk capacity and risk requirement
4. Gives detailed explanations of what these scores mean

Think of this like a financial health check that helps answer two key questions:
- How much investment risk can you afford to take? (Risk Capacity)
- How much risk do you need to take to reach your goals? (Risk Requirement)

To run this application:
    streamlit run app.py

Author: istaawoo
License: See LICENSE file
"""

# Import necessary Python libraries
# streamlit: Creates web interfaces for Python applications
# pandas: Handles data analysis and calculations
# math: Provides mathematical functions
# typing: Helps with type hints for better code understanding

from typing import Dict
import streamlit as st
import pandas as pd
import math

# -----------------------
# Configuration: Step Sizes for Input Fields
# -----------------------
# These constants define how much the input values change when users click up/down arrows

# Amount by which investable assets (savings, investments) changes per step (in USD)
STEP_INVESTABLE = 2500

# Amount by which annual income changes per step (in USD)
STEP_INCOME = 1000

# Amount by which fixed expenses (rent, utilities, etc.) change per step (in USD)
STEP_FIXED = 500

# Amount by which variable expenses (dining, entertainment, etc.) change per step (in USD)
STEP_VARIABLE = 500

# Amount by which annual withdrawals from investments change per step (in USD)
STEP_WITHDRAW = 100

# Percentage points by which expected salary growth changes per step
STEP_GROWTH = 0.1

# -----------------------
# Risk Capacity Assessment Functions
# -----------------------

def map_sli(sli: float) -> float:
    """
    Calculates a risk score (0-100) based on the Savings Longevity Index (SLI).
    
    SLI measures how many years your savings could last if you had to live off them:
    SLI = Total Investable Assets / Annual Withdrawals
    
    Parameters:
    sli (float): Number of years savings would last at current withdrawal rate
    
    Returns:
    float: Risk capacity score (0-100) where:
    - 0 means very low capacity (savings last less than 1 year)
    - 40 means moderate capacity (savings last 5 years)
    - 80 means high capacity (savings last 20 years)
    - 100 means maximum capacity (savings last 50+ years)
    
    Example:
    If someone has $100,000 in savings and withdraws $20,000/year:
    SLI = 100,000 / 20,000 = 5 years
    This would return a moderate risk capacity score around 40
    """
    if sli <= 1.0:  # Savings last less than 1 year
        return 0.0
    if 1.0 < sli <= 5.0:  # Savings last 1-5 years
        return 1.0 + (sli - 1.0) / (5.0 - 1.0) * (40.0 - 1.0)
    if 5.0 < sli <= 20.0:  # Savings last 5-20 years
        return 40.0 + (sli - 5.0) / (20.0 - 5.0) * (80.0 - 40.0)
    if 20.0 < sli <= 50.0:  # Savings last 20-50 years
        return 80.0 + (sli - 20.0) / (50.0 - 20.0) * (95.0 - 80.0)
    if sli > 50.0:  # Savings last more than 50 years
        mapped = 95.0 + (min(sli, 200.0) - 50.0) / (200.0 - 50.0) * (100.0 - 95.0)
        return min(mapped, 100.0)
    return 0.0

def map_income_ratio(r: float) -> float:
    """
    Calculates a risk score (0-100) based on the Income-to-Expenses Ratio.
    
    This ratio shows how well your income covers your expenses:
    Ratio = Annual Income / (Annual Fixed Expenses + Annual Variable Expenses)
    
    Parameters:
    r (float): Income-to-Expenses ratio
    
    Returns:
    float: Risk capacity score (0-100) where:
    - 10 means very low capacity (income barely covers or doesn't cover expenses)
    - 40 means moderate capacity (income is 1.5x expenses)
    - 75 means high capacity (income is 2.5x expenses)
    - 100 means maximum capacity (income is 10x or more than expenses)
    
    Example:
    If someone earns $60,000/year and has $30,000 in total expenses:
    Ratio = 60,000 / 30,000 = 2.0
    This would return a moderate-to-high risk capacity score around 60
    """
    if r <= 1.0:  # Income is less than or equal to expenses
        return 10.0
    if 1.0 < r <= 1.5:  # Income is 1-1.5x expenses
        return 10.0 + (r - 1.0) / (1.5 - 1.0) * (40.0 - 10.0)
    if 1.5 < r <= 2.5:  # Income is 1.5-2.5x expenses
        return 40.0 + (r - 1.5) / (2.5 - 1.5) * (75.0 - 40.0)
    # Income is more than 2.5x expenses (capped at 10x)
    mapped = 75.0 + (min(r, 10.0) - 2.5) / (10.0 - 2.5) * (100.0 - 75.0)
    return min(mapped, 100.0)

def map_emergency_months(months: float) -> float:
    """
    Calculates a risk score (0-100) based on Emergency Fund coverage.
    
    Emergency Fund coverage shows how many months you could cover expenses with savings:
    Months = Total Investable Assets / Monthly Expenses
    
    Parameters:
    months (float): Number of months expenses could be covered by savings
    
    Returns:
    float: Risk capacity score (0-100) where:
    - 5 means very low capacity (less than 1 month of expenses covered)
    - 40 means moderate capacity (3 months of expenses covered)
    - 70 means high capacity (6 months of expenses covered)
    - 100 means maximum capacity (24+ months of expenses covered)
    
    Example:
    If someone has $30,000 in savings and $5,000 in monthly expenses:
    Months = 30,000 / 5,000 = 6 months
    This would return a high risk capacity score of 70
    """
    if months <= 1.0:  # Less than 1 month of emergency funds
        return 5.0
    if 1.0 < months <= 3.0:  # 1-3 months of emergency funds
        return 20.0 + (months - 1.0) / (3.0 - 1.0) * (40.0 - 20.0)
    if 3.0 < months <= 6.0:  # 3-6 months of emergency funds
        return 40.0 + (months - 3.0) / (6.0 - 3.0) * (70.0 - 40.0)
    # More than 6 months of emergency funds (capped at 24 months)
    mapped = 70.0 + (min(months, 24.0) - 6.0) / (24.0 - 6.0) * (100.0 - 70.0)
    return min(mapped, 100.0)

def map_industry(s: str) -> float:
    """
    Calculates a risk score (0-100) based on industry stability.
    
    Different industries have different levels of job security and income stability.
    For example:
    - Stable: Government, Healthcare, Utilities
    - Moderate: Technology, Manufacturing, Education
    - Unstable: Startups, Real Estate, Entertainment
    
    Parameters:
    s (str): Industry stability category ("Stable", "Moderate", or "Unstable")
    
    Returns:
    float: Risk capacity score where:
    - 90 for Stable industries (high job security)
    - 60 for Moderate industries (average job security)
    - 25 for Unstable industries (low job security)
    Default is 60 if category is not recognized
    """
    m = {"Stable": 90.0, "Moderate": 60.0, "Unstable": 25.0}
    return float(m.get(s, 60.0))

def map_age(age: int) -> float:
    """
    Calculates a risk score (0-100) based on age.
    
    Younger people generally can take more investment risk because they:
    1. Have more time to recover from market downturns
    2. Usually have more earning years ahead
    3. Can adjust their financial strategy over time
    
    Parameters:
    age (int): Person's age in years
    
    Returns:
    float: Risk capacity score where:
    - 90 for age <= 30 (highest risk capacity)
    - 75 for ages 31-40
    - 50 for ages 41-55
    - 30 for ages 56-65
    - 10 for ages > 65 (lowest risk capacity)
    """
    if age <= 30:  # Young adults with longest recovery horizon
        return 90.0
    if 31 <= age <= 40:  # Early career with good recovery time
        return 75.0
    if 41 <= age <= 55:  # Mid-career with moderate recovery time
        return 50.0
    if 56 <= age <= 65:  # Late career with limited recovery time
        return 30.0
    return 10.0  # Retirement age with shortest recovery time

def map_growth(g: float) -> float:
    """
    Calculates a risk score (0-100) based on expected salary growth.
    
    Higher expected salary growth allows for more risk-taking because:
    1. Future higher income can offset investment losses
    2. Increases future saving capacity
    3. Provides more financial flexibility
    
    Parameters:
    g (float): Expected annual salary growth percentage
    
    Returns:
    float: Risk capacity score where:
    - 10 for negative growth (declining income)
    - 30 for 0-2% growth (below inflation)
    - 60 for 2-5% growth (moderate growth)
    - 85 for > 5% growth (high growth)
    """
    if g < 0.0:  # Declining income
        return 10.0
    if g < 2.0:  # Growth below typical inflation
        return 30.0
    if g < 5.0:  # Moderate growth
        return 60.0
    return 85.0  # High growth

def map_dependents(d: int) -> float:
    """
    Calculates a risk score (0-100) based on number of dependents.
    
    More dependents typically mean:
    1. Higher fixed expenses (food, healthcare, education)
    2. Less financial flexibility
    3. Greater need for stable income
    
    Parameters:
    d (int): Number of financial dependents
    
    Returns:
    float: Risk capacity score where:
    - 90 for 0 dependents (maximum flexibility)
    - 70 for 1 dependent
    - 50 for 2 dependents
    - 30 for 3 dependents
    - 15 for 4+ dependents (minimum flexibility)
    """
    if d == 0:  # No dependents
        return 90.0
    if d == 1:  # One dependent
        return 70.0
    if d == 2:  # Two dependents
        return 50.0
    if d == 3:  # Three dependents
        return 30.0
    return 15.0  # Four or more dependents

# -----------------------
# Risk Capacity Scoring Weights
# -----------------------
# These weights determine how important each factor is in calculating the final risk capacity score.
# The weights add up to 100% (100.0) and represent the relative importance of each factor.

WEIGHTS = {
    # Savings Longevity Index: Most important (25%)
    # Shows how long savings would last. Higher weight because it directly measures financial cushion.
    "SLI": 25.0,

    # Income-to-Expenses Ratio: Second most important (20%)
    # Shows ability to cover expenses. Critical for ongoing financial stability.
    "Income": 20.0,

    # Emergency Fund Coverage: Third most important (15%)
    # Shows short-term financial safety net. Important for unexpected expenses.
    "Expenses": 15.0,

    # Industry Stability: Fourth most important (12%)
    # Shows job security and income reliability.
    "Industry": 12.0,

    # Age: Equal to Industry (12%)
    # Shows investment time horizon and ability to recover from losses.
    "Age": 12.0,

    # Expected Salary Growth: Less important (8%)
    # Shows future earning potential. Less weight as it's less certain.
    "Growth": 8.0,

    # Number of Dependents: Less important (8%)
    # Shows financial obligations. Less weight but still impacts flexibility.
    "Dependents": 8.0,
}

def compute_risk_capacity(subscores: Dict[str, float]) -> float:
    """
    Calculates the final risk capacity score by combining all individual factor scores.
    
    This function:
    1. Takes the individual scores for each factor (SLI, Income, etc.)
    2. Multiplies each score by its importance weight
    3. Adds all weighted scores together
    4. Ensures the final score is between 0 and 100
    
    Parameters:
    subscores (Dict[str, float]): Dictionary containing scores for each factor
        Example: {
            'SLI': 75.0,       # Good savings longevity
            'Income': 60.0,     # Moderate income ratio
            'Expenses': 40.0,   # Fair emergency coverage
            'Industry': 90.0,   # Very stable industry
            'Age': 75.0,       # Good age for risk
            'Growth': 30.0,     # Low expected growth
            'Dependents': 50.0  # Moderate dependent burden
        }
    
    Returns:
    float: Final risk capacity score (0-100) rounded to 1 decimal place
        0 = Minimum risk capacity (very conservative)
        50 = Moderate risk capacity
        100 = Maximum risk capacity (very aggressive)
    """
    # Calculate weighted sum of all factor scores
    total = sum(WEIGHTS[k] * float(subscores[k]) for k in WEIGHTS.keys())
    
    # Convert to 0-100 scale and ensure it stays within bounds
    score = total / 100.0
    return round(max(0.0, min(100.0, score)), 1)

def compute_risk_requirement(rrr: float, real_req_pct: float, shortfall_pct: float, draw_ratio: float):
    """
    Calculates how much investment risk is needed to achieve financial goals.
    
    This function determines if your financial goals require you to:
    1. Take minimal risk (conservative investing may be enough)
    2. Take moderate risk (balanced investing needed)
    3. Take high risk (aggressive investing required)
    
    Parameters:
    rrr (float): Required Rate of Return as decimal (e.g., 0.07 means 7% per year)
        - This is the annual growth rate needed to reach your target
        - Example: To grow $100,000 to $200,000 in 10 years needs about 7% per year
        
    real_req_pct (float): Real required return percentage after inflation
        - Shows how much growth you need above inflation
        - Example: If you need 7% growth and inflation is 2%, real return needed is 5%
        
    shortfall_pct (float): Gap between what you need and what you expect to get
        - Positive means you need more return than you expect
        - Example: If you need 5% but expect 3%, shortfall is 2%
        
    draw_ratio (float): How well you can handle market drops
        - Ratio of typical market drops to what you can tolerate
        - Example: If markets typically drop 30% but you can only handle 15%,
                  ratio is 2.0 (suggests high risk)
    
    Returns:
    tuple: (requirement_score, subscores)
        - requirement_score (float): Final risk requirement (0-100)
        - subscores (Dict[str, float]): Individual scores for each factor
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
# Risk Requirement Assessment Functions
# -----------------------

def map_rrr(rrr: float) -> float:
    """
    Calculates a risk score (0-100) based on Required Rate of Return (RRR).
    
    The Required Rate of Return is how much your investments need to grow 
    each year to reach your financial goal. Higher required returns usually
    mean you need to take more investment risk.
    
    Parameters:
    rrr (float): Required annual return as decimal (0.07 means 7% per year)
    
    Returns:
    float: Risk requirement score (0-100) where:
    - 0 for required returns <= 3% (very low risk needed)
    - 25 for required returns around 6% (moderate risk needed)
    - 60 for required returns around 10% (high risk needed)
    - 85+ for required returns > 15% (very high risk needed)
    
    Example:
    If you need your money to grow 8% per year:
    rrr = 0.08 (8%)
    This would return a moderate-high risk requirement around 45
    """
    # Convert decimal to percentage for easier thresholds
    p = rrr * 100.0
    
    if p <= 3.0:  # Very conservative return needed
        return 0.0
    if p <= 6.0:  # Conservative to moderate return needed
        return (p - 3.0) / (6.0 - 3.0) * 25.0
    if p <= 10.0:  # Moderate to aggressive return needed
        return 25.0 + (p - 6.0) / (10.0 - 6.0) * 35.0
    if p <= 15.0:  # Aggressive return needed
        return 60.0 + (p - 10.0) / (15.0 - 10.0) * 25.0
    # Very aggressive return needed (capped at 100)
    return 85.0 + min(p - 15.0, 15.0) / 15.0 * 15.0

def map_realreq(real_pct: float) -> float:
    """
    Calculates a risk score (0-100) based on real (inflation-adjusted) required return.
    
    Real required return shows how much your investments need to grow above inflation.
    For example, if you need 7% growth and inflation is 2%, your real required return
    is 5%. This matters because inflation reduces your purchasing power over time.
    
    Parameters:
    real_pct (float): Required return above inflation, in percentage points
    
    Returns:
    float: Risk requirement score (0-100) where:
    - 0 for real return <= 0% (no growth needed above inflation)
    - 25 for real return around 2% (modest growth needed)
    - 65 for real return around 5% (significant growth needed)
    - 100 for real return > 15% (very high growth needed)
    
    Example:
    If you need 3% growth above inflation:
    real_pct = 3.0
    This would return a moderate risk requirement around 45
    """
    if real_pct <= 0.0:  # No real growth needed
        return 0.0
    if real_pct <= 2.0:  # Modest real growth needed
        return (real_pct / 2.0) * 25.0
    if real_pct <= 5.0:  # Moderate real growth needed
        return 25.0 + (real_pct - 2.0) / (5.0 - 2.0) * 40.0
    # Significant real growth needed
    return 65.0 + min(real_pct - 5.0, 10.0) / 10.0 * 35.0

def map_shortfall(short_pct: float) -> float:
    """
    Calculates a risk score (0-100) based on return shortfall.
    
    Shortfall is the gap between what return you need and what you expect to get.
    A positive shortfall means you need to find additional return through taking
    more risk. The larger the shortfall, the more risk you might need to take.
    
    Parameters:
    short_pct (float): Return shortfall in percentage points
        = Required return - Expected return
    
    Returns:
    float: Risk requirement score (0-100) where:
    - 0 for no shortfall (expected return meets or exceeds required)
    - 50 for 5% shortfall (moderate additional return needed)
    - 100 for 10% or greater shortfall (significant additional return needed)
    
    Example:
    If you need 8% return but expect 6%:
    short_pct = 8 - 6 = 2
    This would return a risk requirement of 20
    """
    if short_pct <= 0:  # No shortfall
        return 0.0
    # Linear mapping: 0-10% shortfall maps to 0-100 score
    return min(100.0, (short_pct / 10.0) * 100.0)

def map_drawimpact(draw_ratio: float) -> float:
    """
    Calculates a risk score (0-100) based on drawdown impact ratio.
    
    The drawdown ratio compares typical market drops to what you can tolerate:
    Ratio = Average market drawdown / Your drawdown tolerance
    
    A high ratio means the investment approach you need might have bigger
    drops than you're comfortable with, indicating higher risk.
    
    Parameters:
    draw_ratio (float): Ratio of average drawdown to drawdown tolerance
    
    Returns:
    float: Risk requirement score (0-100) where:
    - 0 for ratio <= 0.5 (market drops well within tolerance)
    - 25 for ratio around 1.0 (drops match tolerance)
    - 60 for ratio around 1.5 (drops exceed tolerance)
    - 100 for ratio > 1.5 (drops significantly exceed tolerance)
    
    Example:
    If markets typically drop 30% but you can only tolerate 20%:
    draw_ratio = 30 / 20 = 1.5
    This would return a high risk requirement of 60
    """
    if draw_ratio <= 0.5:  # Drops well within tolerance
        return 0.0
    if draw_ratio <= 1.0:  # Drops approaching tolerance
        return 25.0
    if draw_ratio <= 1.5:  # Drops exceeding tolerance
        return 60.0
    return 100.0  # Drops far exceeding tolerance

# -----------------------
# Risk Requirement Scoring Weights
# -----------------------
# These weights determine how important each factor is in calculating how much
# risk you need to take to reach your financial goals.
# The weights add up to 100% (100.0).

REQ_WEIGHTS = {
    # Required Rate of Return: Most important (40%)
    # Raw growth rate needed to reach your target. Heavily weighted because
    # it directly shows how ambitious your goal is.
    "RRR": 40.0,
    
    # Real Required Return: Second most important (25%)
    # Growth needed after inflation. Important because it shows true
    # purchasing power growth needed.
    "RealReq": 25.0,
    
    # Return Shortfall: Third most important (20%)
    # Gap between needed and expected returns. Shows how much additional
    # return you need to find through taking risk.
    "Shortfall": 20.0,
    
    # Drawdown Impact: Fourth most important (15%)
    # How market drops compare to your tolerance. Less weight but important
    # for understanding if the required strategy matches your comfort level.
    "DrawImpact": 15.0,
}


# -----------------------
# Helper Functions for Formatting and User-Friendly Output
# -----------------------

def fmt_num(x: float) -> str:
    """
    Formats numbers to be more readable by removing unnecessary decimals.
    
    This function makes numbers look cleaner by:
    1. Converting whole numbers to integers (e.g., 5.0 becomes 5)
    2. Keeping one decimal place for non-whole numbers
    3. Removing trailing zeros after decimal points
    
    Parameters:
    x (float): The number to format
    
    Returns:
    str: A cleanly formatted string representation of the number
    
    Examples:
    fmt_num(5.0) -> "5"
    fmt_num(5.5) -> "5.5"
    fmt_num(5.50) -> "5.5"
    """
    if abs(x - round(x)) < 1e-9:  # If x is effectively a whole number
        return str(int(round(x)))
    # For non-whole numbers, round to 1 decimal and remove unnecessary zeros
    return f"{round(x,1):.1f}".rstrip('0').rstrip('.')

def zone_sentence(component: str, raw_value: float) -> str:
    """
    Creates a human-readable explanation of what different financial metrics mean.
    
    This function takes a financial metric (like savings longevity or income ratio)
    and translates its numerical value into plain English that explains:
    1. What the number means
    2. Which category or zone the number falls into
    3. Why this number matters for financial planning
    
    Parameters:
    component (str): The type of financial metric (SLI, Income, etc.)
    raw_value (float): The actual numerical value of the metric
    
    Returns:
    str: A complete sentence explaining the metric's value and significance
    """
    # Savings Longevity Index (SLI) interpretation
    if component == "SLI":
        # Determine which zone the SLI falls into and explain its meaning
        if raw_value <= 1:
            zone = "No meaningful liquid cushion (<=1 year)."
        elif raw_value <= 5:
            zone = "Low cushion (1-5 years)."
        elif raw_value <= 20:
            zone = "Moderate cushion (5-20 years)."
        else:
            zone = "Very strong cushion (>20 years)."
        # Return complete explanation with the actual value and its implications
        return f"SLI = {fmt_num(raw_value)} years - {zone} Larger SLI => stronger resilience to withdrawals and shocks."
    # Income to Expenses Ratio interpretation
    if component == "Income":
        r = raw_value  # r represents the ratio of income to expenses
        if r <= 1:
            z = "Income <= expenses (high forced selling risk)."  # Income doesn't cover expenses
        elif r <= 1.5:
            z = "Income modestly above expenses."  # Small positive cash flow
        elif r <= 2.5:
            z = "Income comfortably above expenses."  # Good positive cash flow
        else:
            z = "High income vs expenses (strong buffer)."  # Very strong positive cash flow
        return f"Income ratio = {round(r,2)} - {z}"
    
    # Emergency Fund Coverage interpretation
    if component == "Expenses":
        m = raw_value  # m represents months of expenses covered by savings
        if m <= 1:
            z = "Under 1 month emergency cushion."  # Very limited safety net
        elif m <= 3:
            z = "1-3 months."  # Basic safety net
        elif m <= 6:
            z = "3-6 months."  # Standard safety net
        else:
            z = "6+ months."  # Strong safety net
        return f"Emergency months = {fmt_num(m)} - {z}"
    
    # Industry Stability interpretation
    if component == "Industry":
        # Explains how stable employment in their industry typically is
        return f"Industry stability = {raw_value}. Stable industries imply reduced income disruption risk."
    
    # Age Factor interpretation
    if component == "Age":
        # Explains how age affects ability to recover from financial setbacks
        return f"Age = {int(raw_value)}. Younger investors have longer recovery horizons (higher capacity)."
    
    # Expected Salary Growth interpretation
    if component == "Growth":
        # Explains how future salary increases affect financial flexibility
        return f"Expected salary growth = {fmt_num(raw_value)}% p.a. Higher growth increases future capacity."
    
    # Number of Dependents interpretation
    if component == "Dependents":
        # Explains how financial obligations affect risk capacity
        return f"Dependents = {int(raw_value)}. More dependents reduce discretionary capacity."
    
    # Default return if component type is not recognized
    return ""

# -----------------------
# User Interface and Visual Design
# -----------------------

def main():
    """
    Main application function that creates the web interface.
    
    This function:
    1. Sets up the page layout and styling
    2. Creates input forms for financial information
    3. Calculates risk capacity and requirement scores
    4. Displays results with detailed explanations
    5. Provides interactive features for scenario analysis
    
    The interface is designed to be:
    - Clear and easy to understand
    - Visually appealing with a professional dark theme
    - Responsive to different screen sizes
    - Interactive with immediate feedback
    """
    # Configure the page with a wide layout for better use of screen space
    st.set_page_config(page_title="Risk Capacity Estimator", layout="wide")
    # Apply custom styling to make the application look professional and easy to read
    st.markdown(
        """
        <style>
        /* Define color variables for consistent theme */
        :root {
            --accent: #12c755;     /* Bright green for important numbers and buttons */
            --dark-bg: #071026;    /* Dark blue background for better contrast */
            --card: #0b1b2b;       /* Slightly lighter blue for cards and sections */
            --muted: #93a4b6;      /* Muted blue-gray for less important text */
            --text: #e6eef6;       /* Light blue-white for main text */
        }
        
        /* Set the main background and text colors */
        html, body, .stApp { 
            background: var(--dark-bg) !important; 
            color: var(--text) !important; 
        }
        
        /* Style the sidebar to match the main theme */
        .stSidebar { 
            background: var(--dark-bg) !important; 
            color: var(--text) !important; 
        }
        
        /* Style cards that display results */
        .rc-card { 
            background: var(--card); 
            padding: 14px; 
            border-radius: 10px; 
            color: var(--text); 
        }
        
        /* Style the main risk scores to stand out */
        .rc-score { 
            font-size: 36px; 
            font-weight: 700; 
            color: var(--accent); 
        }
        
        /* Style input fields for better visibility */
        input, select, textarea { 
            background: #0f2a3f !important; 
            color: var(--text) !important; 
            border-radius: 6px !important; 
            border: 1px solid rgba(255,255,255,0.06) !important; 
            padding: 6px !important; 
        }
        
        /* Style buttons to stand out */
        .stButton>button, .stDownloadButton>button { 
            background: var(--accent) !important; 
            color: #031014 !important; 
            font-weight: 600; 
            border-radius: 8px !important; 
            padding: 8px 12px !important; 
        }
        
        /* Limit width of number inputs and dropdowns */
        .stNumberInput, .stSelectbox { 
            max-width: 360px; 
        }
        
        /* Make data tables more readable */
        .stDataFrame table { 
            table-layout: auto !important; 
        }
        
        /* Style captions for additional information */
        .stCaption { 
            color: var(--muted) !important; 
        }
        </style>
        """, unsafe_allow_html=True
    )

    # Display the main title and introduction
    st.title("Risk Capacity Estimator")
    st.write("""
    This tool helps determine:
    1. How much investment risk you can afford to take (Risk Capacity)
    2. How much risk you need to take to reach your goals (Risk Requirement)
    
    The tool will give you scores from 0 to 100, where:
    - 0-25: Conservative (low risk)
    - 26-50: Moderate-Conservative
    - 51-75: Moderate-Aggressive
    - 76-100: Aggressive (high risk)
    
    Fill in your financial information below and click Calculate to see your results.
    """)

    # Create a two-column layout for the top controls
    c1, c2 = st.columns([1, 0.6])
    with c1:
        # Remind users to provide accurate information
        st.caption("""
        Please provide accurate numbers for the best results.
        If you're unsure about exact values, use your best estimate.
        Missing or inaccurate values will make the results less reliable.
        """)
    with c2:
        # Option to automatically update results while changing inputs
        auto_update = st.checkbox(
            "Auto-update while editing",
            value=True,
            help="When checked, results will update immediately as you change values"
        )

    # Create a form to collect all financial information
    # Using a form keeps the interface organized and prevents screen flicker
    with st.form("inputs", clear_on_submit=False):
        # Split the form into two columns for better space usage
        left, right = st.columns([1.0, 1.0])

        with left:
            # Section for personal information and regular cash flow
            st.header("Personal & Cashflow")
            
            # Basic personal information
            age = st.number_input(
                "Age (years):",
                min_value=0,
                value=39,
                step=1,
                help="Your current age. This affects how much time you have to recover from investment losses."
            )
            
            dependents = st.number_input(
                "Number of dependents:",
                min_value=0,
                value=2,
                step=1,
                help="People who rely on you financially (children, elderly parents, etc.)"
            )
            
            # Income and regular expenses
            annual_income = st.number_input(
                "Annual income (USD):",
                min_value=0,
                value=500000,
                step=STEP_INCOME,
                format="%d",
                help="Your total yearly income before taxes (salary, bonuses, etc.)"
            )
            
            annual_fixed = st.number_input(
                "Annual fixed expenses (USD):",
                min_value=0,
                value=30000,
                step=STEP_FIXED,
                format="%d",
                help="Yearly expenses that don't change much (rent/mortgage, utilities, insurance)"
            )
            
            annual_variable = st.number_input(
                "Annual variable expenses (USD):",
                min_value=0,
                value=30000,
                step=STEP_VARIABLE,
                format="%d",
                help="Yearly expenses that can vary (dining, entertainment, shopping)"
            )
            
            # Career and income growth potential
            industry = st.radio(
                "Industry stability:",
                ["Stable", "Moderate", "Unstable"],
                index=1,
                help="""
                How stable is employment in your industry?
                Stable: Government, Healthcare, Utilities
                Moderate: Technology, Manufacturing, Education
                Unstable: Startups, Entertainment, Real Estate
                """
            )
            
            expected_growth = st.number_input(
                "Expected salary growth (annual %):",
                value=2.0,
                step=STEP_GROWTH,
                format="%.2f",
                help="How much you expect your salary to increase each year, on average"
            )

        with right:
            # Section for assets, investment withdrawals, and financial goals
            st.header("Assets, Withdrawals & Goal")
            
            # Current financial position
            investable_assets = st.number_input(
                "Investable assets (USD):",
                min_value=0,
                value=500000,
                step=STEP_INVESTABLE,
                format="%d",
                help="Total money available for investing (savings, stocks, bonds, etc.)"
            )
            
            annual_withdrawals = st.number_input(
                "Annual withdrawals (USD):",
                min_value=0,
                value=10000,
                step=STEP_WITHDRAW,
                format="%d",
                help="How much money you take out of your investments each year"
            )
            
            # Financial goals and planning section
            st.markdown("### Goal inputs (for Risk Requirement)")
            st.caption("""
            This section helps determine how much investment risk you need to take
            to reach your financial goals. Be realistic with your targets and timeframe.
            """)
            
            target_wealth = st.number_input(
                "Target portfolio value (USD):",
                min_value=0,
                value=1500000,
                step=10000,
                format="%d",
                help="How much money you want to have in investments by your target date"
            )
            
            current_portfolio = st.number_input(
                "Current portfolio value (USD):",
                min_value=0,
                value=500000,
                step=1000,
                format="%d",
                help="Current total value of your investment portfolio"
            )
            
            horizon_years = st.number_input(
                "Time horizon (years):",
                min_value=1,
                value=10,
                step=1,
                help="How many years until you need to reach your target amount"
            )
            
            # Economic and market assumptions
            inflation = st.number_input(
                "Assumed inflation rate (%):",
                min_value=0.0,
                value=2.0,
                step=0.1,
                format="%.2f",
                help="Expected average yearly increase in prices/cost of living"
            )
            
            expected_return = st.number_input(
                "Expected annual return (%):",
                min_value=-10.0,
                value=6.0,
                step=0.1,
                format="%.2f",
                help="How much you expect your investments to grow each year, on average"
            )
            
            # Risk tolerance metrics
            avg_drawdown = st.number_input(
                "Average historical drawdown (%):",
                min_value=0.0,
                value=30.0,
                step=0.1,
                format="%.1f",
                help="""
                How much investments like yours typically drop in bad markets.
                For example, stock markets often drop 20-30% in bear markets.
                """
            )
            
            drawdown_tolerance = st.number_input(
                "Drawdown tolerance (%):",
                min_value=0.0,
                value=15.0,
                step=0.1,
                format="%.1f",
                help="""
                Maximum investment drop you can tolerate without changing your plan.
                Be honest - many people overestimate their tolerance for losses.
                """
            )

        submitted = st.form_submit_button("Calculate")
        if auto_update:
            # emulate immediate submit when auto-update is on
            submitted = True

    if submitted:
        # Calculate intermediate financial metrics from user inputs
        
        # Convert annual expenses to monthly for emergency fund calculation
        monthly_expenses = (annual_fixed + annual_variable) / 12.0
        
        # Calculate Savings Longevity Index (SLI)
        # This shows how many years your savings would last at current withdrawal rate
        # Using max(1.0, annual_withdrawals) prevents division by zero
        sli_value = investable_assets / max(1.0, annual_withdrawals)
        
        # Calculate Income to Expenses Ratio
        # This shows how well your income covers your expenses
        # A ratio > 1 means you have more income than expenses
        income_ratio = annual_income / max(1.0, (annual_fixed + annual_variable))
        
        # Calculate Emergency Fund Coverage in months
        # This shows how many months your savings could cover expenses
        months = investable_assets / max(1.0, monthly_expenses)

        # Calculate Risk Capacity Scores for each factor
        subscores = {
            # Savings Longevity: How long savings would last
            "SLI": map_sli(sli_value),
            
            # Income Coverage: How well income covers expenses
            "Income": map_income_ratio(income_ratio),
            
            # Emergency Fund: Short-term financial safety net
            "Expenses": map_emergency_months(months),
            
            # Industry: Job and income stability
            "Industry": map_industry(industry),
            
            # Age: Investment time horizon
            "Age": map_age(int(age)),
            
            # Salary Growth: Future earning potential
            "Growth": map_growth(float(expected_growth)),
            
            # Dependents: Financial obligations
            "Dependents": map_dependents(int(dependents)),
        }
        
        # Calculate final Risk Capacity Score (0-100)
        capacity_score = compute_risk_capacity(subscores)

        # Calculate Risk Requirement Score
        # This shows how much investment risk you need to take to reach your goals
        
        # Get target and current values, ensuring we don't divide by zero
        T = max(1.0, float(target_wealth))    # Target portfolio value
        C = max(1.0, float(current_portfolio))  # Current portfolio value
        n = max(1.0, float(horizon_years))    # Number of years to reach target
        
        # Calculate Required Rate of Return (RRR)
        # This is the annual growth rate needed to reach your target
        # Formula: RRR = (Target/Current)^(1/years) - 1
        # Example: To grow $100k to $200k in 10 years needs about 7.2% per year
        rrr = math.pow(T / C, 1.0 / n) - 1.0
        
        # Calculate Real (inflation-adjusted) Required Return
        # This shows how much growth you need above inflation
        # Example: If you need 7% growth and inflation is 2%, you need 5% real growth
        real_req_pct = (rrr * 100.0) - float(inflation)
        
        # Calculate Return Shortfall
        # This shows if you need more return than you expect to get
        # Positive shortfall means you need to take more risk
        shortfall_pct = real_req_pct - float(expected_return)
        
        # Calculate Drawdown Impact Ratio
        # This shows if typical market drops exceed your comfort level
        # Example: If markets drop 30% but you can only handle 15%, ratio is 2.0
        draw_ratio = float(avg_drawdown) / max(float(drawdown_tolerance), 0.0001)
        
        # Calculate final Risk Requirement Score (0-100)
        # Higher scores mean you need to take more investment risk
        requirement_score, req_subscores = compute_risk_requirement(
            rrr,              # Required growth rate
            real_req_pct,     # Growth needed above inflation
            shortfall_pct,    # Extra return needed
            draw_ratio        # Market drops vs tolerance
        )

        # Display Results Section
        st.markdown("---")
        st.header("Results")
        
        # Display Risk Requirement Score
        # This shows how much investment risk you need to take to reach your goals
        st.markdown(
            f"""
            <div class='rc-card'>
                <div style='font-size:20px; color:var(--muted)'>
                    Risk Requirement Score: How much risk you need to take
                    <p style='font-size:14px; margin-top:5px'>
                    This score shows how aggressive your investments need to be to reach your goals:
                    - 0-25: Conservative strategy may be enough
                    - 26-50: Moderate strategy needed
                    - 51-75: Moderately aggressive strategy needed
                    - 76-100: Very aggressive strategy needed
                    </p>
                </div>
                <div class='rc-score'>{fmt_num(requirement_score)} / 100</div>
            </div>
            """, 
            unsafe_allow_html=True
        )

        # Display Risk Capacity Score
        # This shows how much investment risk you can afford to take
        st.markdown(
            f"""
            <div style='margin-top:10px' class='rc-card'>
                <div style='font-size:20px; color:var(--muted)'>
                    Risk Capacity Score: How much risk you can afford
                    <p style='font-size:14px; margin-top:5px'>
                    This score shows your financial ability to handle investment risk:
                    - 0-25: Limited capacity (be conservative)
                    - 26-50: Moderate capacity (some risk ok)
                    - 51-75: Good capacity (can take more risk)
                    - 76-100: Strong capacity (can be aggressive)
                    </p>
                </div>
                <div class='rc-score'>{fmt_num(capacity_score)} / 100</div>
            </div>
            """, 
            unsafe_allow_html=True
        )

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

# This is the standard Python idiom for running the main application
# It ensures the main() function only runs if this file is run directly
# (not when it's imported as a module into another program)
if __name__ == "__main__":
    main()
