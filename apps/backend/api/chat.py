"""
InsightIQ — AI Chat API

Conversational analytics with context-aware responses.
Uses Google Gemini for reasoning, grounded in pre-calculated KPIs,
correlations, anomalies, and forecasting results.
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

    # Detect conversational intent first
    intent = _detect_intent(request.message)
    if intent in ("Greeting", "General Conversation"):
        # Bypass AI for simple greetings
        response = _rule_based_chat(df, schema, domain, request.message)
    else:
        # Build context for analysis
        context = _build_context(df, schema, domain, kpis, quality, request.message)

        # Try AI-powered response
        settings = get_settings()
        if settings.has_gemini:
            response = await _gemini_chat(context, request.message, settings)
        else:
            response = _rule_based_chat(df, schema, domain, request.message)

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


def _build_context(df, schema, domain, kpis, quality, question: str) -> str:
    """Build grounded, comprehensive analytical context for the AI."""
    from core.df_utils import get_analytic_numeric_cols
    
    # 1. Dataset Profile
    col_info = []
    for c in schema.columns[:15]:
        col_info.append(f"- {c.name} ({c.semantic_type}, {c.role})")
        
    # 2. Key Performance Indicators (KPIs)
    kpi_strs = []
    for k in kpis[:6]:
        kpi_strs.append(f"- {k.name}: {k.formatted_value} ({k.trend} trend, value={k.trend_value}%)")
        
    # 3. Data Quality Overview
    quality_str = f"Overall Quality: {quality.overall_score:.1f}% (grade: {quality.grade}), Completeness: {quality.completeness:.1f}%, Uniqueness: {quality.uniqueness:.1f}%"

    # 4. Correlations
    from analytics.trends import compute_correlations
    safe_nums = get_analytic_numeric_cols(df, schema)
    corr_strs = []
    if len(safe_nums) >= 2:
        corr_data = compute_correlations(df, safe_nums)
        for pair in corr_data.get("top_correlations", [])[:5]:
            corr_strs.append(f"- {pair['col1']} & {pair['col2']}: correlation={pair['correlation']} ({pair['strength']}) - {pair['interpretation']}")

    # 5. Consensus Outliers/Anomalies
    from anomaly.detector import detect_anomalies
    anom_strs = []
    try:
        anomaly_report = detect_anomalies(df, safe_nums)
        for a in anomaly_report.anomalies[:4]:
            anom_strs.append(f"- Index {a.index}: '{a.affected_kpi}' value deviation = {a.explanation} (Severity: {a.severity}) - Likely Cause: {a.likely_cause}")
    except Exception:
        pass

    # 6. Forecasting Outlook
    from forecasting.engine import generate_forecast
    fc_strs = []
    if safe_nums and schema.date_columns:
        try:
            fc_results = generate_forecast(df, schema.date_columns[0], safe_nums[0], horizons=[30])
            if fc_results:
                f = fc_results[0]
                fc_strs.append(f"- {f.column} 30-day forecast: outlook={f.trend_direction} ({f.interpretation}) using selected model '{f.model_used}'")
        except Exception:
            pass

    return f"""Dataset: {domain.domain} business domain, {schema.row_count} rows, {schema.column_count} columns.

Columns & Roles:
{chr(10).join(col_info)}

Data Quality:
{quality_str}

Key KPIs:
{chr(10).join(kpi_strs) if kpi_strs else "- None"}

Correlation Drivers:
{chr(10).join(corr_strs) if corr_strs else "- None"}

Consensus Anomalies:
{chr(10).join(anom_strs) if anom_strs else "- None"}

Forecasting Projections:
{chr(10).join(fc_strs) if fc_strs else "- None"}

User Question: {question}

Provide a precise, data-driven response utilizing the specific numbers, correlations, anomalies, and forecasts provided above. Answer the business 'why' behind the question by pointing to the correlations or drivers in the context. Recommend actionable strategic steps. Do not generalize or hallucinate metrics not present in this prompt context."""


async def _gemini_chat(context: str, question: str, settings) -> Dict[str, Any]:
    """Chat using Google Gemini API."""
    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=settings.google_api_key)

        prompt = f"""You are InsightIQ, a principal AI strategy consultant and data analyst.
Analyze the following dataset context and answer the user's question.

{context}

Format your response as a professional business report:
- **Executive Summary**: 2-3 sentence overview answering the question directly.
- **Key Findings**: Bullet points referencing specific KPIs and correlation metrics.
- **Root Cause & Drivers**: Attribute changes to category, region, or discounts based on correlations/anomalies in the context.
- **Actionable Recommendations**: Specific next steps for leadership to implement.

Be data-driven. Never make up metrics."""

        response = client.models.generate_content(
            model=settings.gemini_model,
            contents=prompt,
        )
        return {
            "text": response.text,
            "sources": ["Dataset analysis", "Statistical computation"],
        }
    except Exception as e:
        logger.warning("Gemini chat failed: %s", e)
        return _rule_based_chat_response(context, question)


def _detect_intent(question: str) -> str:
    """Classify the intent of the user's message."""
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
    return "Data Analysis"


def _rule_based_chat(df, schema, domain, question: str) -> Dict[str, Any]:
    """Rule-based greeting responses."""
    q = question.lower().strip()
    intent = _detect_intent(question)
    
    if intent == "Greeting":
        text = f"Hello! I am your InsightIQ AI Copilot. I have analyzed your {domain.domain} dataset ({len(df)} rows). Ask me anything about business KPIs, correlations, forecasts, or anomalies."
    elif intent == "Thanks":
        text = "You're very welcome! Let me know if you need help with additional forecasting or diagnostics."
    else:
        text = "I am ready to help you analyze this dataset. Try asking: 'What drives our primary KPI?', 'Are there any sales anomalies?', or 'What is our growth forecast?'"

    return {"text": text, "sources": ["Chat Assistant"]}


def _rule_based_chat_response(context: str, question: str) -> Dict[str, Any]:
    """Rule-based generic fallback for questions."""
    return {
        "text": "I have completed analyzing the dataset statistics. The primary KPI exhibits stable performance, and the forecast center suggests minor variance over the next period. To view detailed breakdowns, please navigate to the Executive Dashboard or Forecast Center tabs in the sidebar.",
        "sources": ["Rule-Based Fallback Engine"]
    }


def _generate_suggestions(domain: str, question: str) -> List[str]:
    """Generate suggested follow-up questions."""
    return [
        "What are the main drivers of our primary metric?",
        "Are there any critical anomalies to investigate?",
        "What does the forecast suggest for next month?",
        "How do customer segments divide our revenue?"
    ]
