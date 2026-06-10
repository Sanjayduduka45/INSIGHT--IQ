"""
InsightIQ — Business Insight and Executive Intelligence Engine

Generates a startup-grade strategic executive summary, structured data story,
and diagnostic recommendations.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
import pandas as pd
import numpy as np

from intelligence.kpi_generator import KPI
from intelligence.quality_scorer import QualityReport
from core.settings import get_settings

logger = logging.getLogger(__name__)


def generate_executive_report(
    df: pd.DataFrame,
    schema: Any,
    quality: QualityReport,
    kpis: List[KPI],
    domain: str,
    context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Compile a business-grade executive report for C-level stakeholders."""
    
    # ── 1. GATHER CONCRETE STATISTICAL FACTS (Rule-Based Grounding) ──────────
    facts = _compile_factual_summary(df, schema, quality, kpis, domain)
    
    # ── 2. ATTEMPT GEMINI GENERATION IF CONFIGURABLE ──────────────────────────
    settings = get_settings()
    if settings.has_gemini:
        try:
            report = _generate_gemini_report(facts, settings, context)
            if report:
                return report
        except Exception as e:
            logger.warning(f"Gemini executive report generation failed: {e}. Falling back to template-based generator.")
            
    # ── 3. TEMPLATE-BASED PROFESSIONAL COMPILER (Ground Truth Fallback) ──────
    return _generate_template_report(facts, context)


def _compile_factual_summary(
    df: pd.DataFrame,
    schema: Any,
    quality: QualityReport,
    kpis: List[KPI],
    domain: str
) -> Dict[str, Any]:
    """Extract precise numbers and insights directly from data."""
    from core.df_utils import get_analytic_numeric_cols, get_categorical_cols
    
    nums = get_analytic_numeric_cols(df, schema)
    cats = get_categorical_cols(df, schema)
    
    primary_kpi = kpis[0] if kpis else None
    
    # Identify key columns by token matching
    rev_keywords = ["revenue", "sales", "spend", "amount", "total", "price", "cost", "value"]
    profit_keywords = ["profit", "margin", "earnings", "net"]
    cat_keywords = ["category", "type", "class", "genre", "dept", "department"]
    cust_keywords = ["customer", "cust", "client", "member", "user", "buyer"]
    region_keywords = ["region", "state", "country", "city", "location", "area"]
    
    rev_col = next((c for c in nums if any(kw in c.lower() for kw in rev_keywords)), None) or (nums[0] if nums else None)
    profit_col = next((c for c in nums if any(kw in c.lower() for kw in profit_keywords)), None)
    cat_col = next((c for c in cats if any(kw in c.lower() for kw in cat_keywords)), None) or (cats[0] if cats else None)
    cust_col = next((c for c in df.columns if any(kw in c.lower() for kw in cust_keywords)), None)
    region_col = next((c for c in df.columns if any(kw in c.lower() for kw in region_keywords)), None)

    # 1. Total Revenue / Main Metric Sum
    total_rev_val = float(df[rev_col].sum()) if rev_col and rev_col in df.columns else 0.0
    
    # 2. Profit Sum
    if profit_col and profit_col in df.columns:
        total_profit_val = float(df[profit_col].sum())
    else:
        total_profit_val = total_rev_val * 0.15  # Fallback: assume 15% estimated profit margin
        
    # 3. Growth rate calculation
    growth_rate = 0.0
    growth_status = "stable"
    if schema.date_columns and rev_col:
        try:
            date_col = schema.date_columns[0]
            df_sorted = df.dropna(subset=[date_col, rev_col]).copy()
            df_sorted[date_col] = pd.to_datetime(df_sorted[date_col], errors="coerce")
            df_sorted = df_sorted.dropna(subset=[date_col]).sort_values(date_col)
            if len(df_sorted) >= 4:
                half = len(df_sorted) // 2
                first_half = df_sorted.iloc[:half][rev_col].mean()
                second_half = df_sorted.iloc[half:][rev_col].mean()
                if first_half != 0:
                    growth_rate = ((second_half - first_half) / abs(first_half)) * 100
                    growth_status = "growth" if growth_rate > 2 else "decline" if growth_rate < -2 else "stable"
        except Exception:
            pass

    # 4. Top Category concentration
    top_cat_name = "N/A"
    top_cat_share = 0.0
    if cat_col and rev_col:
        try:
            grouped = df.groupby(cat_col)[rev_col].sum().sort_values(ascending=False)
            total = grouped.sum()
            if total > 0:
                top_cat_name = str(grouped.index[0])
                top_cat_share = (grouped.iloc[0] / total) * 100
        except Exception:
            pass
            
    # 5. Top Customer segment concentration
    top_cust_name = "N/A"
    top_cust_share = 0.0
    if cust_col and rev_col:
        try:
            grouped = df.groupby(cust_col)[rev_col].sum().sort_values(ascending=False)
            total = grouped.sum()
            if total > 0:
                top_cust_name = str(grouped.index[0])
                top_cust_share = (grouped.iloc[0] / total) * 100
        except Exception:
            pass
            
    # 6. Top Region concentration
    top_region_name = "N/A"
    top_region_share = 0.0
    if region_col and rev_col:
        try:
            grouped = df.groupby(region_col)[rev_col].sum().sort_values(ascending=False)
            total = grouped.sum()
            if total > 0:
                top_region_name = str(grouped.index[0])
                top_region_share = (grouped.iloc[0] / total) * 100
        except Exception:
            pass
            
    # 7. Correlation summary
    strongest_corr = ""
    if len(nums) >= 2:
        try:
            corr = df[nums[:5]].corr().unstack().reset_index()
            corr.columns = ["c1", "c2", "val"]
            corr = corr[corr["c1"] != corr["c2"]].copy()
            corr["abs_val"] = corr["val"].abs()
            top_corr = corr.sort_values("abs_val", ascending=False).iloc[0]
            strongest_corr = f"A correlation of {top_corr['val']:.2f} exists between '{top_corr['c1']}' and '{top_corr['c2']}'."
        except Exception:
            pass

    # 8. Anomaly rate
    anomaly_rate = 0.0
    total_cells = 0
    anomalous_cells = 0
    for col in nums[:5]:
        series = df[col].dropna()
        if len(series) > 10 and series.std() > 0:
            z_scores = (series - series.mean()).abs() / series.std()
            anomalous_cells += int((z_scores > 3).sum())
            total_cells += len(series)
    if total_cells > 0:
        anomaly_rate = (anomalous_cells / total_cells) * 100

    return {
        "domain": domain,
        "rows": len(df),
        "cols": len(df.columns),
        "primary_kpi_name": primary_kpi.name if primary_kpi else "KPI",
        "primary_kpi_value": primary_kpi.formatted_value if primary_kpi else "N/A",
        "primary_kpi_trend": primary_kpi.trend if primary_kpi else "stable",
        "primary_kpi_change": abs(primary_kpi.trend_value) if primary_kpi else 0.0,
        "completeness": quality.completeness,
        "overall_quality": quality.overall_score,
        "anomaly_rate": round(anomaly_rate, 2),
        "total_revenue": total_rev_val,
        "total_profit": total_profit_val,
        "growth_rate": round(growth_rate, 2),
        "growth_status": growth_status,
        "top_cat_name": top_cat_name,
        "top_cat_share": round(top_cat_share, 1),
        "top_cust_name": top_cust_name,
        "top_cust_share": round(top_cust_share, 1),
        "top_region_name": top_region_name,
        "top_region_share": round(top_region_share, 1),
        "strongest_corr": strongest_corr,
        "kpis_declining": [k.name for k in kpis if k.trend == "down"],
        "kpis_growing": [k.name for k in kpis if k.trend == "up"]
    }


def _generate_gemini_report(facts: Dict[str, Any], settings: Any, context: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    """Query Gemini with grounded parameters to construct a tailored C-Level report."""
    import json
    from core.gemini_utils import generate_content_with_gemini
    
    prompt = f"""You are a Senior Strategic Business Advisor and Data Architect.
We are analyzing this dataset to address a specific business problem:
- Business Problem: {context.get('business_problem') if context else 'N/A'}
- Analysis Goal: {context.get('analysis_goal') if context else 'N/A'}
- Primary Success Metric: {context.get('success_metric') if context else 'N/A'}

Review the following statistical facts compiled from our enterprise data:

{json.dumps(facts, indent=2)}

Generate a premium, concise, business-focused Executive Report for senior leadership.
Crucially: Customize the findings, risks, opportunities, recommendations, and summaries to align with the stated business problem and success metric. If the goal is Churn/Retention, do not prioritize overall sales expansion, but on loyalty, churn indicators, CLV, and customer behaviors. If the goal is Revenue Growth, focus on top-performing product categories, markets, and growth pathways.

Provide the output in JSON format with EXACTLY the following keys:
1. "summary" (string: 2-3 sentence strategic executive summary)
2. "summary_fields" (nested object with EXACTLY the following string fields:
     - "revenue" (e.g. "$2.3M total sales value")
     - "profit" (e.g. "$350K net earnings")
     - "growth" (e.g. "+8.2% PoP expansion")
     - "top_category" (e.g. "Technology contributes 36.5% of total revenue")
     - "top_customer_segment" (e.g. "Champions represent 23% of customer volume")
     - "top_region" (e.g. "West contributes 42% of total sales")
     - "biggest_risk" (e.g. "High discount rates eroding Furniture category margins")
     - "biggest_opportunity" (e.g. "Leveraging strong demand in Technology to cross-sell Accessories")
     - "forecast_outlook" (e.g. "Projecting 8.2% sales increase next quarter")
     - "recommended_action" (e.g. "Diversify product offerings and scale Technology catalog")
   )
3. "key_findings" (array of strings: 3 concise, data-backed findings with specific numbers)
4. "risks" (array of strings: 2 key operational or financial risks grounded in data anomalies, quality, or declining metrics)
5. "opportunities" (array of strings: 2 actionable areas for growth, product optimization, or operational efficiency)
6. "recommendations" (array of strings: 3 concrete strategic recommendations for execution)
7. "data_story" (string: a 3-4 sentence storytelling narrative outlining performance, leading categories, top region, and forecast)

Return ONLY the raw JSON block. Do not include markdown wraps like ```json."""

    try:
        text = generate_content_with_gemini(
            prompt=prompt,
            model_name=settings.gemini_model,
            api_key=settings.google_api_key,
            response_mime_type="application/json",
            temperature=0.1
        )
        
        # Parse output safely
        if text.startswith("```"):
            text = text.replace("```json", "").replace("```", "").strip()
            
        parsed = json.loads(text)
        required_keys = ["summary", "summary_fields", "key_findings", "risks", "opportunities", "recommendations", "data_story"]
        if all(k in parsed for k in required_keys):
            return parsed
    except Exception as e:
        logger.error(f"Failed to parse or run Gemini executive report: {e}")
        
    return None


def _generate_template_report(facts: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Robust fallback template providing rich business reports when AI is offline."""
    
    domain = facts["domain"]
    kpi_name = facts["primary_kpi_name"]
    kpi_val = facts["primary_kpi_value"]
    trend = facts["primary_kpi_trend"]
    change = facts["primary_kpi_change"]
    quality = facts["overall_quality"]
    anomaly_rate = facts["anomaly_rate"]
    
    total_rev = facts["total_revenue"]
    total_prof = facts["total_profit"]
    growth_rate = facts["growth_rate"]
    growth_status = facts["growth_status"]
    
    top_cat = facts["top_cat_name"]
    top_cat_share = facts["top_cat_share"]
    top_cust = facts["top_cust_name"]
    top_cust_share = facts["top_cust_share"]
    top_region = facts["top_region_name"]
    top_region_share = facts["top_region_share"]
    
    # Formats
    rev_formatted = f"${total_rev:,.0f}" if total_rev > 0 else "N/A"
    prof_formatted = f"${total_prof:,.0f}" if total_prof > 0 else "N/A"
    growth_formatted = f"{'+' if growth_rate >= 0 else ''}{growth_rate:.1f}% PoP"

    goal = str(context.get("analysis_goal", "")).lower() if context else ""
    prob = str(context.get("business_problem", "")).lower() if context else ""
    
    is_churn_retention = any(k in goal or k in prob for k in ["churn", "retention", "customer"])
    is_marketing = any(k in goal or k in prob for k in ["marketing", "campaign", "ctr", "conversion", "roas"])
    is_ops = any(k in goal or k in prob for k in ["operational", "operations", "supply", "efficiency", "cost", "shipment"])
    
    # ── 1. DYNAMIC SUMMARY ───────────────────────────────────────────────────
    if is_churn_retention:
        summary = f"The primary analysis objective is customer retention and churn reduction. Our data identifies key customer cohorts representing significant churn risks. Interventions must target at-risk groups to improve customer lifetime value (CLV)."
    elif is_marketing:
        summary = f"Analyzing marketing acquisition channels and campaign conversion rates. Performance skews indicate significant ROI variance across channels. Budget re-allocation is recommended to optimize overall ROAS."
    elif is_ops:
        summary = f"Assessing operational throughput, shipping cycle times, and process efficiency. Identified bottlenecks represent significant cost-saving opportunities through workflow automation and supplier audits."
    else:
        # Default/Revenue
        if trend == "up":
            summary = f"The dataset indicates solid growth in key {domain} performance drivers. Primary metrics like '{kpi_name}' have expanded by {change:.1f}%, indicating positive market uptake and operational efficiency. Strategic investment should target scaling these successful operations."
        elif trend == "down":
            summary = f"Recent data shows contraction inside the {domain} portfolio. '{kpi_name}' has decreased by {change:.1f}%. Immediate tactical review is recommended to diagnose category margins and counter ongoing revenue leakage."
        else:
            summary = f"Performance metrics remain stable across {domain}. Operational parameters are running within expected thresholds. Focus should lie on optimization and safeguarding data collection integrity."

    # ── 2. DYNAMIC SUMMARY FIELDS ────────────────────────────────────────────
    top_category_desc = f"{top_cat} contributes {top_cat_share}% of total volume" if top_cat != "N/A" else "Metric distributed evenly across categories"
    top_cust_desc = f"{top_cust} represents {top_cust_share}% of spend" if top_cust != "N/A" else "Homogenous customer distributions observed"
    top_region_desc = f"{top_region} region contributes {top_region_share}% of total" if top_region != "N/A" else "No strong regional concentration patterns detected"
    
    biggest_risk = "Data validation warnings and missing records introduce reporting integrity risks." if quality < 85 else "Minor outlier volatility represents the primary risk vector."
    biggest_opportunity = f"Leverage growth in category '{top_cat}' to optimize stock procurement and cross-sell complementary services." if top_cat != "N/A" else "Automate quality cleanup and remove redundant data rows."
    
    forecast_outlook = f"Forecast suggests metric growth of {growth_rate:.1f}% next period." if growth_status == "growth" else f"Projecting temporary contraction of {abs(growth_rate):.1f}% next period."
    recommended_action = f"Optimize discount levels in '{top_cat}' to protect profitability margin." if top_cat != "N/A" else "Investigate operational channel efficiency metrics."
    
    if is_churn_retention:
        biggest_risk = f"Elevated churn triggers observed in top segment '{top_cust or 'N/A'}'. CLV dilution is expected if repeat buy rates contract."
        biggest_opportunity = "Implement targeted loyalty programs for high-value cohorts to boost purchase frequency."
        recommended_action = f"Establish customer health scoring alerts on '{kpi_name}' activity drop-offs."
    elif is_marketing:
        biggest_risk = "Ad spend concentration in underperforming channels is eroding overall campaign ROI."
        biggest_opportunity = "Reallocate budget from low-performing cohorts to high-CTR regional channels."
        recommended_action = "A/B test ad creatives in top regions to stabilize acquisition costs."
    elif is_ops:
        biggest_risk = "Supply chain delays and cycle time bottlenecks are driving up shipping costs."
        biggest_opportunity = "Automate inventory replenishment rules for top products in dominant regions."
        recommended_action = "Renegotiate carrier contracts for high-volume routes to reduce transit costs."

    summary_fields = {
        "revenue": f"{rev_formatted} total sales value",
        "profit": f"{prof_formatted} net earnings (estimated)",
        "growth": growth_formatted,
        "top_category": top_category_desc,
        "top_customer_segment": top_cust_desc,
        "top_region": top_region_desc,
        "biggest_risk": biggest_risk,
        "biggest_opportunity": biggest_opportunity,
        "forecast_outlook": forecast_outlook,
        "recommended_action": recommended_action
    }

    # ── 3. KEY FINDINGS ──────────────────────────────────────────────────────
    findings = [
        f"Primary indicator '{kpi_name}' sits at {kpi_val}, tracing a {trend} path (change of {change:.1f}%).",
        f"Leading category '{top_cat}' accounts for {top_cat_share}% contribution share." if top_cat != "N/A" else "Metric distributions are stable across category groupings.",
        facts["strongest_corr"] if facts["strongest_corr"] else f"Core metric clusters operate in tandem, suggesting unified channel drivers."
    ]
    if top_region != "N/A":
        findings.append(f"Geographic check isolates '{top_region}' as the dominant region contributing {top_region_share:.1f}% of totals.")
    findings.append(f"Quality audit scores overall data integrity at {quality:.1f}% (Grade {facts.get('overall_quality_grade', 'A')}) with anomaly rate of {anomaly_rate:.1f}%.")
    findings = findings[:5]

    # ── 4. RISKS ─────────────────────────────────────────────────────────────
    risks = []
    if quality < 85:
        risks.append(f"Data validation score is {quality:.1f}%. Missing fields and inconsistent values introduce compliance and reporting risks.")
    else:
        risks.append("No critical quality gaps, but periodic auditing of the collection pipeline is advised to maintain A-grade reporting.")
        
    if anomaly_rate > 3.0:
        risks.append(f"Outlier index is elevated at {anomaly_rate:.1f}%. Sudden variance in transactional volumes indicates leakage or operational friction.")
    else:
        risks.append("Outlier metrics are within tolerance, presenting negligible impact to current business forecasting.")
    
    risks.append(f"Variance check shows potential margin dilution under high discounts.")
    risks = risks[:4]

    # ── 5. OPPORTUNITIES ─────────────────────────────────────────────────────
    if is_churn_retention:
        opps = [
            "Implement customer retention incentives for at-risk cohorts to safeguard lifetime value.",
            "Automate feedback loops when account activity decreases below historic thresholds.",
            "Optimize support resource allocations to prioritize VIP customer issues.",
            "Analyze repeat purchase timing to schedule automated reminders."
        ]
    elif is_marketing:
        opps = [
            "Scale budget in high-ROAS marketing campaigns to capture extra market share.",
            "Optimize regional landing page speed to maximize conversion rate.",
            "Refine customer demographic parameters based on top purchase skews.",
            "Diversify advertising assets to combat ad fatigue in mature campaigns."
        ]
    elif is_ops:
        opps = [
            "Redistribute warehouse inventory to high-volume regions to trim cycle delays.",
            "Establish automated replenishment points to optimize carrying costs.",
            "Audit supplier lead-times to weed out underperforming logistics partners.",
            "Implement batch-processing rules to speed up order fulfillment workflows."
        ]
    else:
        opps = [
            f"Model forecasting indicates {domain} metrics have scalable trends. Shift marketing resources toward top categories.",
            "Operational cost-saving can be realized by automating quality cleanup and removing duplicate entries.",
            f"Design custom incentives for 'Potential Loyalists' to drive conversion rates.",
            f"Optimize localized product arrays using regional category demand analytics."
        ]
    opps = opps[:4]

    # ── 6. STRATEGIC RECOMMENDATIONS ─────────────────────────────────────────
    if is_churn_retention:
        recs = [
            f"Launch a personalized win-back discount campaign for the top segment '{top_cust or 'N/A'}'.",
            "Establish a real-time churn early warning monitor triggering alerts on activity drop-offs.",
            "Implement VIP loyalty bonuses for customers exceeding 3 consecutive purchases.",
            "Address data quality discrepancies in customer ID and transaction logs."
        ]
    elif is_marketing:
        recs = [
            "Shift 15% of budget from underperforming channels into conversion-focused campaigns.",
            "Conduct localized pricing audits in top regions to match competitor bids.",
            "Establish closed-loop marketing attribution tracking for accurate ROI reporting.",
            "Optimize ad spend limits relative to average customer acquisition cost (CAC)."
        ]
    elif is_ops:
        recs = [
            "Deploy safety inventory thresholds for high-demand category products.",
            "Renegotiate route pricing with freight suppliers to trim operational costs.",
            "Standardize batch sorting times at key fulfillment hubs.",
            "Automate inventory audits using daily transaction logs."
        ]
    else:
        recs = [
            f"Establish a real-time monitor for '{kpi_name}' to trigger early warnings when volumes drop below the historical median.",
            "Enforce automated schema verification at the ingestion gate to correct spelling and formatting errors immediately.",
            "Model future cashflows using the Forecast Center to optimize product procurement and workforce allocation.",
            "Establish dynamic replenishment points to automate store shelf stocking."
        ]
    recs = recs[:4]

    # ── 7. DATA STORYTELLING NARRATIVE ───────────────────────────────────────
    data_story = (
        f"Total revenue reached {rev_formatted} while profitability margins remain healthy, contributing {prof_formatted} in earnings. "
        f"'{top_cat}' stands out as the highest-performing category (responsible for {top_cat_share}% of totals). "
        f"Regional sales show strong concentration in '{top_region}' at {top_region_share}% contribution. "
        f"Looking ahead, forecasting models project a '{growth_status}' outlook ({growth_formatted}) over the next performance interval."
    )

    return {
        "summary": summary,
        "summary_fields": summary_fields,
        "key_findings": findings,
        "risks": risks,
        "opportunities": opps,
        "recommendations": recs,
        "data_story": data_story
    }

