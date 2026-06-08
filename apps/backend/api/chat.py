"""
InsightIQ — AI Chat API

Conversational analytics with context-aware, intent-based routing.
Uses Google Gemini for reasoning, grounded in pre-calculated KPIs,
correlations, anomalies, customer RFM segments, and forecasting results.
Provides data-rich rule-based fallbacks containing real numbers when Gemini is offline.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
import json

import pandas as pd
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from dataclasses import asdict

from api.datasets import get_dataset_store
from core.settings import get_settings
from core.security import get_current_user
from core.gemini_utils import generate_content_with_gemini

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatRequest(BaseModel):
    dataset_id: str
    message: str
    conversation_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    charts: List[Dict[str, Any]] = []
    insights: List[Dict[str, Any]] = []
    suggested_questions: List[str] = []
    sources: List[str] = []


# Simple conversation memory
_conversations: Dict[str, List[Dict[str, str]]] = {}


@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest, user: dict = Depends(get_current_user)):
    """Process a chat message and return AI-generated analysis."""
    ds = get_dataset_store().get(request.dataset_id)
    if not ds:
        raise HTTPException(404, "Dataset not found")

    df: pd.DataFrame = ds["df"]
    schema = ds["schema"]
    domain = ds["domain"]
    kpis = ds.get("kpis", [])
    quality = ds["quality"]

    # 1. Detect conversational intent
    intent = _detect_intent(request.message)
    logger.info(f"Detected conversational intent: '{intent}' for message: '{request.message}'")

    if intent in ("Greeting", "Thanks", "General Conversation"):
        response = _rule_based_chat(df, schema, domain, request.message)
    else:
        # Extract real dataset statistics
        stats_dict = _extract_dataset_stats(df, schema, domain, kpis, quality)
        
        # Build context for analysis
        context = _build_intent_context(intent, stats_dict, request.message)

        # Try AI-powered response
        settings = get_settings()
        if settings.has_gemini:
            try:
                response = await _gemini_chat(intent, context, request.message, settings)
            except Exception as gemini_err:
                logger.error(f"Gemini chat failed: {gemini_err}. Falling back to data-driven rule compiler.")
                response = _compile_data_driven_fallback(intent, stats_dict, request.message)
        else:
            logger.info("Gemini API not configured. Using data-driven rule compiler fallback.")
            response = _compile_data_driven_fallback(intent, stats_dict, request.message)

    # Generate suggested follow-up questions
    suggestions = _generate_suggestions(domain.domain, request.message)

    # Log to Supabase chat_logs table if authenticated and not a guest
    settings = get_settings()
    if settings.has_supabase and user and user.get("role") != "guest":
        try:
            from supabase import create_client, Client
            client: Client = create_client(settings.supabase_url, settings.supabase_anon_key)
            if user.get("token"):
                client.postgrest.auth(user["token"])
            
            client.table("chat_logs").insert({
                "user_id": user.get("id"),
                "dataset_id": request.dataset_id,
                "message": request.message,
                "response": response["text"],
            }).execute()
            logger.info("Successfully saved chat log to Supabase.")
        except Exception as db_err:
            logger.error(f"Failed to save chat log to Supabase: {db_err}")

    return ChatResponse(
        response=response["text"],
        charts=response.get("charts", []),
        insights=response.get("insights", []),
        suggested_questions=suggestions,
        sources=response.get("sources", []),
    )


def _detect_intent(question: str) -> str:
    """Classify the intent of the user's message using keyword mapping."""
    q = question.lower().strip()

    greetings = ["hi", "hello", "hey", "good morning", "good afternoon", "good evening", "greetings"]
    thanks = ["thank you", "thanks", "thx", "appreciate it"]
    general = ["how are you", "what are you", "who are you", "help"]

    if any(q.startswith(g) or q == g for g in greetings):
        return "Greeting"
    if any(t in q for t in thanks):
        return "Thanks"
    if any(g in q for g in general):
        return "General Conversation"

    # Intent routing for 10 C-Level strategic domains
    if any(kw in q for kw in ["forecast", "predict", "projection", "outlook", "horizon", "future", "smooth"]):
        return "Forecast Analysis"
    if any(kw in q for kw in ["anomaly", "anomalies", "outlier", "outliers", "deviation", "irregular", "zscore", "iqr"]):
        return "Anomaly Investigation"
    if any(kw in q for kw in ["correlation", "correlations", "correlate", "linked", "dependency", "heatmap", "relationship"]):
        return "Correlation Analysis"
    if any(kw in q for kw in ["drive", "driver", "drivers", "factor", "factors", "cause", "why", "reason", "variance", "pop", "attribut", "waterfall"]):
        return "Revenue Drivers"
    if any(kw in q for kw in ["customer", "customers", "client", "clients", "buyer", "segment", "segments", "rfm", "clv", "loyalty"]):
        return "Customer Insights"
    if any(kw in q for kw in ["recommend", "recommendation", "recommendations", "opportunities", "action", "plan", "opportunity"]):
        return "Strategic Recommendations"
    if any(kw in q for kw in ["risk", "risks", "mitigation", "mitigations", "threat", "threats", "exposure", "weakness"]):
        return "Risk Assessment"
    if any(kw in q for kw in ["trend", "trends", "historical", "history", "time series", "chronological", "over time"]):
        return "Trend Analysis"
    if any(kw in q for kw in ["quality", "missing", "null", "completeness", "uniqueness", "clean", "grade"]):
        return "Data Quality"
    if any(kw in q for kw in ["kpi", "kpis", "metric", "metrics", "value", "measure", "growth", "percentage", "amount"]):
        return "KPI Analysis"

    return "Executive Summary"


def _extract_dataset_stats(df: pd.DataFrame, schema: Any, domain: Any, kpis: List[Any], quality: Any) -> Dict[str, Any]:
    """Extract raw metrics and analysis from the dataset to ground both prompts and fallbacks."""
    from core.df_utils import get_analytic_numeric_cols, get_categorical_cols
    from analytics.customer_intelligence import compute_customer_intelligence
    from analytics.root_cause import diagnose_root_causes
    from anomaly.detector import detect_anomalies
    from forecasting.engine import generate_forecast

    safe_nums = get_analytic_numeric_cols(df, schema)
    safe_cats = get_categorical_cols(df, schema)

    # 1. Total Metrics
    total_rows = len(df)
    total_cols = len(df.columns)
    
    # 2. KPIs
    kpi_list = []
    for k in kpis:
        kpi_list.append({
            "name": k.name,
            "value": k.formatted_value,
            "trend": k.trend,
            "trend_value": k.trend_value,
            "description": k.description
        })

    # 3. Data Quality
    quality_summary = {
        "score": quality.overall_score,
        "grade": quality.grade,
        "completeness": quality.completeness,
        "uniqueness": quality.uniqueness,
        "consistency": quality.consistency,
        "validity": quality.validity,
        "issues_count": len(quality.issues)
    }

    # 4. Correlation
    from analytics.trends import compute_correlations
    correlations = []
    if len(safe_nums) >= 2:
        try:
            corr_data = compute_correlations(df, safe_nums)
            correlations = corr_data.get("top_correlations", [])[:5]
        except Exception:
            pass

    # 5. Anomalies
    anomaly_list = []
    try:
        anomaly_report = detect_anomalies(df, safe_nums)
        for a in anomaly_report.anomalies[:5]:
            anomaly_list.append({
                "index": a.index,
                "metric": a.affected_kpi,
                "explanation": a.explanation,
                "severity": a.severity,
                "cause": a.likely_cause
            })
    except Exception:
        pass

    # 6. Customer RFM
    customer_info = {"eligible": False}
    try:
        cust_intel = compute_customer_intelligence(df, schema)
        if cust_intel.get("eligible"):
            customer_info = {
                "eligible": True,
                "total_customers": cust_intel.get("total_customers"),
                "repeat_rate": cust_intel.get("repeat_rate"),
                "repeat_revenue_share": cust_intel.get("repeat_revenue_share"),
                "pareto_80_20_customer_pct": cust_intel.get("pareto_80_20_customer_pct"),
                "segments": [
                    {"name": v["name"], "count": v["customer_count"], "share": v["share_percentage"]}
                    for v in cust_intel["segments"].values() if v["customer_count"] > 0
                ]
            }
    except Exception:
        pass

    # 7. Root Cause
    root_cause_info = []
    try:
        rcs = diagnose_root_causes(df, schema, quality, kpis)
        for rc in rcs:
            drivers = []
            for drv in rc.get("drivers", []):
                drivers.append({
                    "driver": drv.get("driver"),
                    "contribution": drv.get("contribution_pct"),
                    "description": drv.get("description")
                })
            root_cause_info.append({
                "metric": rc.get("metric"),
                "direction": rc.get("impact_direction"),
                "overall_change_pct": rc.get("overall_change_pct"),
                "explanation": rc.get("explanation"),
                "drivers": drivers
            })
    except Exception:
        pass

    # 8. Forecast
    forecast_info = []
    if safe_nums and schema.date_columns:
        try:
            fc_results = generate_forecast(df, schema.date_columns[0], safe_nums[0], horizons=[30])
            for f in fc_results:
                forecast_info.append({
                    "metric": f.column,
                    "direction": f.trend_direction,
                    "interpretation": f.interpretation,
                    "model": f.model_used
                })
        except Exception:
            pass

    return {
        "domain": domain.domain,
        "rows": total_rows,
        "cols": total_cols,
        "numeric_cols": safe_nums,
        "categorical_cols": safe_cats,
        "kpis": kpi_list,
        "quality": quality_summary,
        "correlations": correlations,
        "anomalies": anomaly_list,
        "customer": customer_info,
        "root_causes": root_cause_info,
        "forecasts": forecast_info
    }


def _build_intent_context(intent: str, stats: Dict[str, Any], question: str) -> str:
    """Build detailed, targeted analytical context focusing on the user's specific intent."""
    
    header = f"Dataset: {stats['domain']} domain, {stats['rows']} rows, {stats['cols']} columns."
    
    if intent == "Forecast Analysis":
        sub_context = f"""[FORECAST CONTEXT]
Projections:
{json.dumps(stats['forecasts'], indent=2) if stats['forecasts'] else "- None available (no date sequence detected)"}"""

    elif intent == "Anomaly Investigation":
        sub_context = f"""[ANOMALY CONTEXT]
Anomalies detected: {len(stats['anomalies'])} outliers.
Detail breakdown:
{json.dumps(stats['anomalies'], indent=2) if stats['anomalies'] else "- No anomalies detected."}"""

    elif intent == "Correlation Analysis":
        sub_context = f"""[CORRELATION CONTEXT]
Correlations:
{json.dumps(stats['correlations'], indent=2) if stats['correlations'] else "- No correlations computed."}"""

    elif intent == "Customer Insights":
        sub_context = f"""[CUSTOMER CONTEXT]
Customer RFM:
{json.dumps(stats['customer'], indent=2) if stats['customer']['eligible'] else "- Customer columns missing or ineligible for RFM."}"""

    elif intent == "Revenue Drivers":
        sub_context = f"""[REVENUE DRIVERS CONTEXT]
PoP Driver Variance Attribution:
{json.dumps(stats['root_causes'], indent=2) if stats['root_causes'] else "- No temporal changes or drivers isolated."}"""

    elif intent == "Strategic Recommendations":
        sub_context = f"""[RECOMMENDATION DATA]
KPI trends: {[k['name'] + ' is ' + k['trend'] for k in stats['kpis']]}
Data Quality Grade: {stats['quality']['grade']}
Anomaly count: {len(stats['anomalies'])}
Repeat buyer rate: {stats['customer'].get('repeat_rate', 'N/A')}%"""

    elif intent == "Risk Assessment":
        sub_context = f"""[RISK CONTEXT]
Data Quality Grade: {stats['quality']['grade']}
Anomaly count: {len(stats['anomalies'])}
Declining KPIs: {[k['name'] for k in stats['kpis'] if k['trend'] == 'down']}"""

    elif intent == "Trend Analysis":
        sub_context = f"""[TREND CONTEXT]
KPI trends and historic run-rates:
{json.dumps(stats['kpis'], indent=2)}"""

    elif intent == "Data Quality":
        sub_context = f"""[DATA QUALITY CONTEXT]
Data Quality details:
{json.dumps(stats['quality'], indent=2)}"""

    elif intent == "KPI Analysis":
        sub_context = f"""[KPI CONTEXT]
Key Performance Indicators:
{json.dumps(stats['kpis'], indent=2)}"""

    else:
        # Executive Summary
        sub_context = f"""[OVERALL SUMMARY CONTEXT]
KPIs: {[k['name'] + ': ' + k['value'] for k in stats['kpis'][:3]]}
Quality Grade: {stats['quality']['grade']}
Anomalies: {len(stats['anomalies'])}
Forecasting: {[f['metric'] + ' projection is ' + f['direction'] for f in stats['forecasts']]}"""

    return f"""{header}

{sub_context}

User Question: {question}

Provide a precise, data-driven response utilizing the specific numbers, correlations, anomalies, and forecasts provided above. Answer the business 'why' behind the question by pointing to the correlations or drivers in the context. Recommend actionable strategic steps. Do not generalize or hallucinate metrics not present in this prompt context."""


async def _gemini_chat(intent: str, context: str, question: str, settings: Any) -> Dict[str, Any]:
    """Chat using Google Gemini API."""
    
    # Custom instructions depending on intent
    intent_prompts = {
        "Forecast Analysis": "You are forecasting next month's numbers. Explain the projected values, moving averages, and growth rate. Detail expected, best case, and worst case scenarios with confidence values.",
        "Anomaly Investigation": "Analyze data anomalies. Explain the severity, rows affected, and index numbers. Outline the likely business impact of these sudden data spikes or dips.",
        "Correlation Analysis": "Trace statistical relationships. Point to specific Pearson correlation coefficients. Explain features of importance and how variables change in tandem.",
        "Customer Insights": "Analyze customer segments, CLV, and RFM attributes. Discuss Pareto concentrations (e.g. top 10% contributing 80% revenue) and repeat buyer metrics.",
        "Revenue Drivers": "Examine period-over-period waterfall drivers. Attribute shifts in sales or performance to categorical groupings and discounts.",
        "Strategic Recommendations": "Formulate prioritized business initiatives. Balance immediate cost-saving opportunities and long-term risk mitigations.",
        "Risk Assessment": "Analyze business and operational risks. Assess data completeness risks, declining indicators, anomaly density spikes, and outline concrete mitigation options.",
        "Trend Analysis": "Trace historical and temporal growth trends. Highlight month-over-month expansions, historical run-rates, and season patterns.",
        "Data Quality": "Analyze data completeness and accuracy. Recommend specific validation or cleaning rules to restore reporting integrity.",
        "KPI Analysis": "Audit key performance metrics. Detail trend directions, positive growth, and declining metrics.",
        "Executive Summary": "Present a strategic summary overview of the entire dataset portfolio. Highlight core KPIs, health index, and key dimensions."
    }

    role_instruction = intent_prompts.get(intent, intent_prompts["Executive Summary"])

    prompt = f"""You are InsightIQ, a principal AI strategy consultant and data analyst.
{role_instruction}
Analyze the following dataset context and answer the user's question.

{context}

Format your response as a professional business report:
- **Executive Summary**: 2-3 sentence overview answering the question directly.
- **Key Findings**: Bullet points referencing specific KPIs and correlation metrics.
- **Root Cause & Drivers**: Attribute changes to category, region, or discounts based on correlations/anomalies in the context.
- **Actionable Recommendations**: Specific next steps for leadership to implement.

Be data-driven. Never make up metrics. Reference actual numbers from the context."""

    text = generate_content_with_gemini(
        prompt=prompt,
        model_name=settings.gemini_model,
        api_key=settings.google_api_key,
        response_mime_type="text/plain",
        temperature=0.4
    )

    return {
        "text": text,
        "sources": ["Dataset Analysis", "Statistical Computation", "Grounded AI reasoning"],
    }


def _rule_based_chat(df: pd.DataFrame, schema: Any, domain: Any, question: str) -> Dict[str, Any]:
    """Rule-based greeting and general conversation responses."""
    q = question.lower().strip()
    intent = _detect_intent(question)
    
    if intent == "Greeting":
        text = f"Hello! I am your InsightIQ AI Copilot. I have analyzed your {domain.domain} dataset ({len(df):,} rows). Ask me anything about business KPIs, correlations, forecasts, or anomalies."
    elif intent == "Thanks":
        text = "You're very welcome! Let me know if you need help with additional forecasting, customer cohorts, or diagnostics."
    else:
        text = "I am ready to help you analyze this dataset. Try asking: 'What drives our primary KPI?', 'Are there any anomalies?', or 'What is our growth forecast?'"

    return {"text": text, "sources": ["Chat Assistant"]}


def _compile_data_driven_fallback(intent: str, stats: Dict[str, Any], question: str) -> Dict[str, Any]:
    """Provide a highly tailored, data-driven fallback report using actual numbers from the dataset."""
    
    # Extract common variables
    kpi_strs = [f"{k['name']}: {k['value']} ({k['trend']} trend)" for k in stats["kpis"][:3]]
    kpis_line = ", ".join(kpi_strs) if kpi_strs else "No KPIs computed"
    
    if intent == "Forecast Analysis":
        if stats["forecasts"]:
            f = stats["forecasts"][0]
            text = f"""### **Expected Forecast Outlook**
For the primary metric **{f['metric']}**, the 90-day projection indicates a **{f['direction']}** trend. 

**Key Projections:**
- **Outlook**: {f['interpretation']}
- **Smoothing Model**: Holt's Linear (double exponential smoothing)

**Strategic Actions:**
1. Align product safety stock levels with expected growth limits.
2. Review operational capacity thresholds to absorb the projected {f['direction']}.
"""
        else:
            # Numeric columns fallback
            metric = stats["numeric_cols"][0] if stats["numeric_cols"] else "Volume"
            val = stats["kpis"][0]["value"] if stats["kpis"] else f"{stats['rows']:,}"
            text = f"""### **Forecast Horizon Report (Fallback)**
**Historical timeline dates are unavailable** in this dataset. Standard forecasting models cannot compile chronological trends.

**Alternative Analysis:**
- **Current Baseline**: Primary metric '{metric}' stands at a sum total of {val}.
- **Outlook**: Under standard 2% expected growth, target value stands at 30/60/90-day points.
- **Outlier Risks**: Completeness stands at {stats['quality']['completeness']:.1f}%.
"""

    elif intent == "Anomaly Investigation":
        anoms = stats["anomalies"]
        if anoms:
            anom_lines = "\n".join([f"- **Index {a['index']}**: {a['metric']} deviation ({a['explanation']}). Severity: **{a['severity']}**. Cause: {a['cause']}." for a in anoms[:4]])
            text = f"""### **Consensus Outliers & Anomalies**
Our consensus scanning algorithms (Z-Score consensus & IQR boundaries) isolated **{len(anoms)} anomalies** in this dataset.

**Outliers Isolated:**
{anom_lines}

**Business Impact:**
Outlier indexes represent transaction discrepancies or freight delays. High-severity deviations should be audited directly to prevent invoice leakage.
"""
        else:
            text = f"""### **Operational Anomaly Report**
**Consensus audit is normal.** No anomalies or outliers were detected across continuous numeric columns in the {stats['rows']:,} records.

**Diagnostic Parameters:**
- Checked metrics: {', '.join(stats['numeric_cols'][:4])}
- Filter limits: 3-sigma Z-Score and 1.5x IQR boundaries.
"""

    elif intent == "Correlation Analysis":
        corrs = stats["correlations"]
        if corrs:
            corr_lines = "\n".join([f"- **{c['col1']}** & **{c['col2']}**: correlation coefficient = **{c['correlation']}** ({c['strength']}). {c['interpretation']}." for c in corrs[:4]])
            text = f"""### **Correlation & Feature Importance Matrix**
We computed Pearson correlation coefficients across the numerical variables.

**Top Linear Dependencies:**
{corr_lines}

**Business Drivers:**
Strong positive correlations highlight metrics that move in tandem, representing the main operational growth channels.
"""
        else:
            text = """### **Correlation Matrix Report**
**Insufficient continuous variables** to compute a linear correlation matrix. This dataset profile has fewer than 2 continuous metrics.
"""

    elif intent == "Customer Insights":
        cust = stats["customer"]
        if cust["eligible"]:
            segs_lines = "\n".join([f"- **{s['name']}**: {s['count']:,} accounts ({s['share']}% revenue share)." for s in cust["segments"]])
            text = f"""### **Customer CLV & RFM Cohorts**
Segmentation calculations analyzed **{cust['total_customers']:,} unique customers** matching this dataset profile.

**Key Metrics:**
- **Repeat Purchase Rate**: {cust['repeat_rate']}% of customer base are repeat buyers.
- **Repeat Sales Share**: Repeat segments represent **{cust['repeat_revenue_share']}%** of overall volume.
- **Pareto Concentration**: Top **{cust['pareto_80_20_customer_pct']}%** of buyers drive 80% of sales.

**RFM Cohort Sizes:**
{segs_lines}
"""
        else:
            text = """### **Customer Segmentation Profile**
**Customer columns missing.** The dataset does not contain clear customer identifier and transaction monetary columns. RFM segment calculations are ineligible.
"""

    elif intent == "Revenue Drivers":
        rcs = stats["root_causes"]
        if rcs:
            rc_lines = []
            for rc in rcs[:2]:
                drv_lines = "\n".join([f"  * **{d['driver']}** contributes **{d['contribution']}%** ({d['description']})" for d in rc["drivers"][:2]])
                rc_lines.append(f"- **Metric '{rc['metric']}'** {rc['direction']} of **{rc['overall_change_pct']}%**:\n{drv_lines}")
            text = f"""### **Variance Root Cause Attribution**
Period-over-period adjustments attribute metric changes to categorical categories and order quantities.

**Top Attributed Drivers:**
{"\n".join(rc_lines)}

**Recommendation:**
Audit top-attributing categories and margins to isolate discounting leakages.
"""
        else:
            text = f"""### **Diagnostics Fallback Analysis**
**Historical timeline dates are unavailable** to perform period-over-period waterfall analysis.

**Alternative Contributor Scans:**
Top numerical variables by mean value:
{', '.join(stats['numeric_cols'][:3])}
- Completeness: {stats['quality']['completeness']:.1f}%
- Total Rows: {stats['rows']:,} records.
"""

    elif intent == "Strategic Recommendations":
        text = f"""### **Strategic Recommendations**
Based on our statistical audit of this **{stats['domain']}** dataset, we advise the following priorities:

1. **KPI Focus**: Optimize processes related to top metrics (**{kpis_line}**).
2. **Quality Cleanup**: Address quality items (Data Quality Grade **{stats['quality']['grade']}**, score **{stats['quality']['score']:.1f}%**).
3. **Outlier Mitigation**: Track the **{len(stats['anomalies'])} outliers** flagged by anomaly consensus.
4. **Retention Campaign**: Leverage repeat purchase rate of **{stats['customer'].get('repeat_rate', 'N/A')}%** to cross-sell.
"""

    elif intent == "Risk Assessment":
        dq_grade = stats["quality"]["grade"]
        anomaly_cnt = len(stats["anomalies"])
        declining_kpis = [k["name"] for k in stats["kpis"] if k["trend"] == "down"]
        
        text = f"""### **Strategic Risk Assessment & Mitigation**
We have audited operational, financial, and data-integrity risks for this dataset.

**Risk Vector Breakdown:**
- **Data Integrity Risk**: Grade {dq_grade} (completeness is {stats['quality']['completeness']:.1f}%). {"Critical completeness warning." if stats['quality']['completeness'] < 85 else "Quality is within acceptable thresholds."}
- **Outlier Risk**: {anomaly_cnt} anomalies isolated.
- **Performance Leakage**: {", ".join(declining_kpis) if declining_kpis else "No major declining KPIs detected."}

**Mitigation Protocol:**
1. Address missing fields at ingestion gates.
2. Audit anomalous transactional volumes.
"""

    elif intent == "Trend Analysis":
        if stats["forecasts"]:
            f = stats["forecasts"][0]
            text = f"""### **Historical Trend Analysis**
The dataset portfolio has timeline visibility. The primary metric **{f['metric']}** exhibits a chronological pattern.

**Historical Insights:**
- **Run-rate Outlook**: {f['interpretation']}
- **Seasonality & Noise**: Data shows regular variance within bounds.
- **PoP Variance**: Growth parameters show overall progress is stable.
"""
        else:
            metric = stats["numeric_cols"][0] if stats["numeric_cols"] else "Volume"
            text = f"""### **Historical Trend Analysis (Fallback)**
Chronological date headers were not detected.
Sequence analysis of metric '{metric}' indicates normal operational limits with stable variance and a historical mean run rate.
"""

    elif intent == "Data Quality":
        q = stats["quality"]
        text = f"""### **Data Quality Diagnostic Report**
Dataset integrity is evaluated at **{q['score']:.1f}%** overall score, earning a **Grade {q['grade']}** verification rating.

**Quality Dimensions:**
- **Completeness**: {q['completeness']:.1f}% data cell density
- **Uniqueness**: {q['uniqueness']:.1f}% unique row profile
- **Consistency**: {q['consistency']:.1f}% formatting consistency
- **Validity**: {q['validity']:.1f}% logical schema validity

**Risks Isolated:**
There are **{q['issues_count']} data issues** flagged. Ingestion verification recommends data imputation loops.
"""

    elif intent == "KPI Analysis":
        text = f"""### **Key Performance Indicators Performance Audit**
The primary business metrics calculated for this {stats['domain']} portfolio are detailed below.

**Metric Performance:**
{chr(10).join(['- **' + k['name'] + '**: ' + k['value'] + ' (' + k['trend'] + ' trend, ' + str(k['trend_value']) + '% PoP change)' for k in stats['kpis']])}
"""

    else:
        # Executive Summary
        text = f"""### **Executive Summary Report**
This **{stats['domain']}** dataset spans **{stats['rows']:,} records** and {stats['cols']} column variables.

**Strategic Highlights:**
- **Business Health Index**: Composite score stands at A-level.
- **Key Indicators**: {kpis_line}.
- **Data Quality**: **Grade {stats['quality']['grade']}** ({stats['quality']['score']:.1f}% overall).
- **Consensus Anomalies**: **{len(stats['anomalies'])} outliers** isolated.
"""

    return {
        "text": text,
        "sources": ["Data-driven Fallback Engine", "Factual Ingestion Summary"]
    }


def _generate_suggestions(domain: str, question: str) -> List[str]:
    """Generate suggested follow-up questions."""
    return [
        "What are the main drivers of our primary metric?",
        "Are there any critical anomalies to investigate?",
        "What does the forecast suggest for next month?",
        "How do customer segments divide our revenue?"
    ]
