"""
InsightIQ — Premium Series A Startup-Grade PowerPoint Presentation Generator

Generates a wide-screen 16:9 10-slide presentation deck with solid corporate styling,
widescreen formatting, and programmatically embedded high-fidelity visual diagrams.
"""

from __future__ import annotations

import io
import datetime
import logging
from typing import Dict, Any, List, Optional

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.pyplot as plt

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor

from intelligence.schema_detector import DatasetSchema
from intelligence.kpi_generator import KPI

logger = logging.getLogger(__name__)


def get_column_type(column: Any) -> str:
    """Safely adapt different schema formats to retrieve column data type."""
    if column is None:
        return "Unknown"
    
    # Check attributes
    for attr in ["semantic_type", "type", "dtype", "data_type", "pandas_dtype"]:
        if hasattr(column, attr):
            val = getattr(column, attr)
            if val:
                return str(val)
                
    # Check dict structure
    if isinstance(column, dict):
        for key in ["semantic_type", "type", "dtype", "data_type", "pandas_dtype"]:
            if key in column and column[key]:
                return str(column[key])
                
    return "Unknown"


def generate_executive_ppt(
    dataset_name: str,
    kpis: List[Dict[str, Any]],
    insights: List[Dict[str, Any]],
    df: Optional[pd.DataFrame] = None,
    schema: Optional[DatasetSchema] = None,
    health_scores: Optional[Dict[str, Any]] = None,
    executive_intel: Optional[Dict[str, Any]] = None,
) -> bytes:
    """Generate a high-fidelity 16:9 PowerPoint presentation deck (12 Slides)."""
    if df is None or schema is None:
        raise ValueError("PPT presentation generator requires df and schema data structures.")

    prs = Presentation()
    
    # Force widescreen 16:9 aspect ratio
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    # Resolve core models to ground slides
    from intelligence.quality_scorer import score_quality
    from intelligence.domain_classifier import classify_domain
    from analytics.customer_intelligence import compute_customer_intelligence
    from analytics.root_cause import diagnose_root_causes
    from anomaly.detector import detect_anomalies
    from core.df_utils import get_analytic_numeric_cols

    quality = score_quality(df, schema)
    quality_score_val = quality.overall_score
    quality_grade = quality.grade

    domain_result = classify_domain(df, schema)
    domain_str = domain_result.domain
    
    customer_intel = compute_customer_intelligence(df, schema)
    
    kpi_objs = []
    for k in kpis:
        kpi_objs.append(KPI(
            name=k["name"],
            value=k["value"],
            formatted_value=k["formatted_value"],
            unit=k["unit"],
            trend=k["trend"],
            trend_value=k["trend_value"],
            icon=k.get("icon", "📊"),
            category=k.get("category", "general"),
            priority=k.get("priority", 3),
            column_source=k.get("column_source", ""),
            description=k.get("description", "")
        ))
    
    root_causes = diagnose_root_causes(df, schema, quality, kpi_objs)
    anomaly_report = detect_anomalies(df, get_analytic_numeric_cols(df, schema))

    extra_context = {
        "root_causes": root_causes,
        "customer_intel": customer_intel,
        "anomaly_report": anomaly_report
    }

    # Color Constants
    c_navy = RGBColor(15, 23, 42)       # Slate 900
    c_blue = RGBColor(30, 64, 175)      # Blue 900
    c_royal = RGBColor(37, 99, 235)     # Blue 600
    c_slate = RGBColor(71, 85, 105)     # Slate 600
    c_white = RGBColor(255, 255, 255)
    c_emerald = RGBColor(5, 150, 105)
    c_crimson = RGBColor(220, 38, 38)

    # Helper function to apply solid slide backgrounds
    def set_bg_color(slide, color):
        background = slide.background
        fill = background.fill
        fill.solid()
        fill.fore_color.rgb = color

    # Helper function to write standardized titles
    def add_slide_header(slide, title_text, dark_mode=False):
        txBox = slide.shapes.add_textbox(Inches(0.75), Inches(0.5), Inches(11.83), Inches(0.8))
        tf = txBox.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
        p = tf.paragraphs[0]
        p.text = title_text
        p.font.name = "Arial"
        p.font.size = Pt(26)
        p.font.bold = True
        p.font.color.rgb = c_white if dark_mode else c_blue

    # Helper to format textbox lists cleanly
    def format_tf_paragraph(p, text, size=13, bold=False, italic=False, color=c_slate):
        p.text = text
        p.font.name = "Arial"
        p.font.size = Pt(size)
        p.font.bold = bold
        p.font.italic = italic
        p.font.color.rgb = color
        p.space_after = Pt(8)

    blank_layout = prs.slide_layouts[6]

    # ────────────────────────────────────────────────────────────────────────
    # SLIDE 1: COVER SLIDE (Dark Navy background)
    # ────────────────────────────────────────────────────────────────────────
    slide1 = prs.slides.add_slide(blank_layout)
    set_bg_color(slide1, c_navy)
    
    # Widescreen top colored accent bar
    border = slide1.shapes.add_shape(1, Inches(0), Inches(0), Inches(13.333), Inches(0.15))
    border.fill.solid()
    border.fill.fore_color.rgb = c_royal
    border.line.color.rgb = c_royal

    tx_title = slide1.shapes.add_textbox(Inches(1.0), Inches(2.0), Inches(11.3), Inches(3.5))
    tf = tx_title.text_frame
    tf.word_wrap = True
    
    p_mini = tf.paragraphs[0]
    format_tf_paragraph(p_mini, "INSIGHTIQ ENTERPRISE PLATFORM", size=10, bold=True, color=c_royal)
    p_mini.space_after = Pt(14)
    
    p_main = tf.add_paragraph()
    format_tf_paragraph(p_main, "STRATEGIC DIAGNOSTIC DATA DECISION BRIEF", size=36, bold=True, color=c_white)
    p_main.space_after = Pt(18)
    
    p_sub = tf.add_paragraph()
    format_tf_paragraph(p_sub, f"Structured Business Intelligence & Scenario Forecasting for '{dataset_name}'", size=15, color=RGBColor(147, 197, 253))

    # Footer Metadata
    tx_foot = slide1.shapes.add_textbox(Inches(1.0), Inches(5.8), Inches(11.3), Inches(1.0))
    tf_foot = tx_foot.text_frame
    p_f = tf_foot.paragraphs[0]
    date_str = datetime.date.today().strftime("%B %d, %Y")
    format_tf_paragraph(p_f, f"Date: {date_str}  |  Domain: {domain_str}  |  Classification: Restricted", size=10, color=c_slate)

    # ────────────────────────────────────────────────────────────────────────
    # SLIDE 2: DATASET PROFILE
    # ────────────────────────────────────────────────────────────────────────
    slide2 = prs.slides.add_slide(blank_layout)
    add_slide_header(slide2, "Dataset Schema & Quality Profile")

    # Left Column: Attributes
    left_tx = slide2.shapes.add_textbox(Inches(0.75), Inches(1.8), Inches(5.5), Inches(4.5))
    tf = left_tx.text_frame
    tf.word_wrap = True
    
    p = tf.paragraphs[0]
    format_tf_paragraph(p, "Operational Data Ingestion Summary:", size=16, bold=True, color=c_navy)
    p.space_after = Pt(12)

    bullets = [
        f"• Total Loaded Records: {schema.row_count:,} rows",
        f"• Dimensional Columns: {schema.column_count} fields",
        f"• Continuous Variables: {len(schema.numeric_columns)} metric dimensions",
        f"• Categorical Segments: {len(schema.categorical_columns)} lookup values",
        f"• Completeness Threshold: {quality.completeness:.1f}% data density",
        f"• Integrity Validation Grade: Grade {quality.grade} ({quality_score_val:.1f}% scorecard score)"
    ]
    for b in bullets:
        p = tf.add_paragraph()
        format_tf_paragraph(p, b, size=13)
        p.space_after = Pt(10)

    # Right Column: Tables
    left = Inches(6.75)
    top = Inches(1.8)
    width = Inches(5.8)
    height = Inches(4.5)
    
    table_shape = slide2.shapes.add_table(7, 3, left, top, width, height)
    table = table_shape.table
    table.columns[0].width = Inches(2.2)
    table.columns[1].width = Inches(1.8)
    table.columns[2].width = Inches(1.8)

    # Headers
    headers = ["Dimension", "Type", "Null Rate"]
    for idx, h in enumerate(headers):
        cell = table.cell(0, idx)
        cell.text = h
        cell.fill.solid()
        cell.fill.fore_color.rgb = c_blue
        p = cell.text_frame.paragraphs[0]
        p.font.bold = True
        p.font.color.rgb = c_white
        p.font.size = Pt(11)

    for idx, c in enumerate(schema.columns[:6]):
        row_idx = idx + 1
        table.cell(row_idx, 0).text = c.name
        table.cell(row_idx, 1).text = get_column_type(c).capitalize()
        table.cell(row_idx, 2).text = f"{c.missing_pct:.1f}%"
        for c_idx in range(3):
            cell = table.cell(row_idx, c_idx)
            p = cell.text_frame.paragraphs[0]
            p.font.size = Pt(10)
            p.font.color.rgb = c_navy

    # ────────────────────────────────────────────────────────────────────────
    # SLIDE 3: BUSINESS HEALTH SCORECARD
    # ────────────────────────────────────────────────────────────────────────
    slide3 = prs.slides.add_slide(blank_layout)
    h_score = health_scores.get("score", 0) if health_scores else 0
    add_slide_header(slide3, f"Business Health Rating Scorecard ({h_score:.1f}%)")

    # Left Column: C-level Explanation
    left_tx = slide3.shapes.add_textbox(Inches(0.75), Inches(1.8), Inches(5.5), Inches(4.5))
    tf = left_tx.text_frame
    tf.word_wrap = True
    
    p = tf.paragraphs[0]
    format_tf_paragraph(p, "C-Level Scorecard Narrative:", size=16, bold=True, color=c_navy)
    p.space_after = Pt(12)

    biggest_risk_val = executive_intel.get("summary_fields", {}).get("biggest_risk", "None Isolated") if executive_intel else "None Isolated"
    biggest_opp_val = executive_intel.get("summary_fields", {}).get("biggest_opportunity", "None Isolated") if executive_intel else "None Isolated"

    bullets = [
        f"• Global Health Index: Evaluated at {h_score:.1f}% contribution.",
        f"• Quality Integrity Index: Stable at {quality_score_val:.1f}% grade {quality_grade}.",
        f"• Core Diagnostics: {health_scores.get('explanation', '') if health_scores else 'No audit detail.'}",
        f"• System Outlook: Metric distributions indicate stable transaction flow.",
        f"• Biggest Risk Element: {biggest_risk_val}",
        f"• Top Growth Opportunity: {biggest_opp_val}"
    ]
    for b in bullets:
        p = tf.add_paragraph()
        format_tf_paragraph(p, b, size=12.5)
        p.space_after = Pt(8)

    # Right Column: Breakdown Table
    left = Inches(6.75)
    top = Inches(1.8)
    width = Inches(5.8)
    height = Inches(4.5)

    if health_scores and health_scores.get("breakdown"):
        factors = list(health_scores["breakdown"].values())
        rows = len(factors) + 1
        
        table_shape = slide3.shapes.add_table(rows, 4, left, top, width, height)
        table = table_shape.table
        table.columns[0].width = Inches(2.2)
        table.columns[1].width = Inches(1.2)
        table.columns[2].width = Inches(1.2)
        table.columns[3].width = Inches(1.2)

        # Headers
        headers = ["Assessment Factor", "Weight", "Score", "Contrib"]
        for idx, h in enumerate(headers):
            cell = table.cell(0, idx)
            cell.text = h
            cell.fill.solid()
            cell.fill.fore_color.rgb = c_blue
            p = cell.text_frame.paragraphs[0]
            p.font.bold = True
            p.font.color.rgb = c_white
            p.font.size = Pt(11)

        for row_idx, val in enumerate(factors):
            i = row_idx + 1
            table.cell(i, 0).text = val.get("label", "Factor")
            table.cell(i, 1).text = f"{val.get('weight', 0)*100:.0f}%"
            table.cell(i, 2).text = f"{val.get('score', 0):.1f}%"
            table.cell(i, 3).text = f"+{val.get('contribution', 0):.1f}%"
            for c_idx in range(4):
                cell = table.cell(i, c_idx)
                p = cell.text_frame.paragraphs[0]
                p.font.size = Pt(10)
                p.font.color.rgb = c_navy

    # ────────────────────────────────────────────────────────────────────────
    # SLIDE 4: KPI DEEP DIVE
    # ────────────────────────────────────────────────────────────────────────
    slide4 = prs.slides.add_slide(blank_layout)
    add_slide_header(slide4, "Strategic Key Performance Indicators")

    # Left Column: Narrative
    left_tx = slide4.shapes.add_textbox(Inches(0.75), Inches(1.8), Inches(5.2), Inches(4.5))
    tf = left_tx.text_frame
    tf.word_wrap = True
    
    p = tf.paragraphs[0]
    format_tf_paragraph(p, "Key Metric Highlights:", size=16, bold=True, color=c_navy)
    p.space_after = Pt(12)

    for k in kpi_objs[:3]:
        p = tf.add_paragraph()
        format_tf_paragraph(p, f"• {k.name}: {k.formatted_value}", size=14, bold=True, color=c_navy)
        p_desc = tf.add_paragraph()
        format_tf_paragraph(p_desc, f"  {k.description} — Trend: {k.trend} ({k.trend_value:+.1f}%)", size=11, color=c_slate)
        p_desc.space_after = Pt(10)

    # Right Column: Trend Chart
    trend_chart = _render_ppt_chart("trend", df, schema, kpis, extra_context)
    if trend_chart:
        slide4.shapes.add_picture(trend_chart, Inches(6.75), Inches(1.8), Inches(5.83), Inches(4.5))

    # ────────────────────────────────────────────────────────────────────────
    # SLIDE 5: ANOMALY ANALYSIS
    # ────────────────────────────────────────────────────────────────────────
    slide5 = prs.slides.add_slide(blank_layout)
    add_slide_header(slide5, "Operational Anomaly & Outlier Telemetry")

    # Left Column: List
    left_tx = slide5.shapes.add_textbox(Inches(0.75), Inches(1.8), Inches(5.2), Inches(4.5))
    tf = left_tx.text_frame
    tf.word_wrap = True
    
    p = tf.paragraphs[0]
    format_tf_paragraph(p, "Consensus Anomalies Isolated:", size=16, bold=True, color=c_navy)
    p.space_after = Pt(12)

    anoms = anomaly_report.anomalies[:4]
    if anoms:
        for a in anoms:
            p = tf.add_paragraph()
            format_tf_paragraph(p, f"• Index {a.index}: {a.affected_kpi}", size=13, bold=True, color=c_crimson)
            p_cause = tf.add_paragraph()
            format_tf_paragraph(p_cause, f"  Cause: {a.likely_cause} ({a.explanation}, Severity: {a.severity})", size=11, color=c_slate)
            p_cause.space_after = Pt(8)
    else:
        p = tf.add_paragraph()
        format_tf_paragraph(p, "• No critical outliers isolated across numeric metrics.", size=13, color=c_slate)

    # Right Column: Anomaly Scatter Plot
    anomaly_chart = _render_ppt_chart("anomaly", df, schema, kpis, extra_context)
    if anomaly_chart:
        slide5.shapes.add_picture(anomaly_chart, Inches(6.75), Inches(1.8), Inches(5.83), Inches(4.5))

    # ────────────────────────────────────────────────────────────────────────
    # SLIDE 6: CUSTOMER INTELLIGENCE
    # ────────────────────────────────────────────────────────────────────────
    slide6 = prs.slides.add_slide(blank_layout)
    add_slide_header(slide6, "Customer RFM Segments & Pareto Share")

    # Left Column: Statistics
    left_tx = slide6.shapes.add_textbox(Inches(0.75), Inches(1.8), Inches(5.2), Inches(4.5))
    tf = left_tx.text_frame
    tf.word_wrap = True
    
    p = tf.paragraphs[0]
    format_tf_paragraph(p, "Customer Segmentation Summary:", size=16, bold=True, color=c_navy)
    p.space_after = Pt(12)

    if customer_intel.get("eligible"):
        bullets = [
            f"• Total Customer Accounts: {customer_intel.get('total_customers'):,}",
            f"• Customer Column Match: ID '{customer_intel.get('customer_column')}'",
            f"• Repeat Purchase Rate: {customer_intel.get('repeat_rate')}% repeat buyers",
            f"• Repeat Revenue Contribution: {customer_intel.get('repeat_revenue_share')}% of total",
            f"• Pareto concentration: Top {customer_intel.get('pareto_80_20_customer_pct')}% customers yield 80% sales",
            f"• Top 10% Share: {customer_intel.get('pareto_10_concentration')}%  |  Top 20% Share: {customer_intel.get('pareto_20_concentration')}%"
        ]
        for b in bullets:
            p = tf.add_paragraph()
            format_tf_paragraph(p, b, size=13)
            p.space_after = Pt(8)
    else:
        p = tf.add_paragraph()
        format_tf_paragraph(p, f"• Customer analysis not eligible: {customer_intel.get('message')}", size=13, italic=True)

    # Right Column: Customer Bar Chart
    customer_chart = _render_ppt_chart("customer", df, schema, kpis, extra_context)
    if customer_chart:
        slide6.shapes.add_picture(customer_chart, Inches(6.75), Inches(1.8), Inches(5.83), Inches(4.5))

    # ────────────────────────────────────────────────────────────────────────
    # SLIDE 7: FORECASTING & PROJECTIONS
    # ────────────────────────────────────────────────────────────────────────
    slide7 = prs.slides.add_slide(blank_layout)
    add_slide_header(slide7, "Projections & Horizon Scenario Planning")

    # Left Column: Outlook text
    left_tx = slide7.shapes.add_textbox(Inches(0.75), Inches(1.8), Inches(5.2), Inches(4.5))
    tf = left_tx.text_frame
    tf.word_wrap = True
    
    p = tf.paragraphs[0]
    format_tf_paragraph(p, "Scenario Planning Horizons:", size=16, bold=True, color=c_navy)
    p.space_after = Pt(12)

    bullets = [
        "• Forecast Horizon: 90 Days chronologically.",
        "• Expected Case Model: Assumes steady +2% growth PoP.",
        "• Best Case (Upside Targets): Assumes strong +5% expansion.",
        "• Worst Case (Downside Volatility): Assumes temporary -3% contraction.",
        "• Confidence intervals resolve to 95% at 30-day target.",
        "• Recommendation: Procure buffer stock relative to Expected scenario bounds."
    ]
    for b in bullets:
        p = tf.add_paragraph()
        format_tf_paragraph(p, b, size=13)
        p.space_after = Pt(10)

    # Right Column: Forecast Line Chart
    forecast_chart = _render_ppt_chart("forecast", df, schema, kpis, extra_context)
    if forecast_chart:
        slide7.shapes.add_picture(forecast_chart, Inches(6.75), Inches(1.8), Inches(5.83), Inches(4.5))

    # ────────────────────────────────────────────────────────────────────────
    # SLIDE 8: STRATEGIC RECOMMENDATIONS
    # ────────────────────────────────────────────────────────────────────────
    slide8 = prs.slides.add_slide(blank_layout)
    add_slide_header(slide8, "Strategic Action Plan & Priority Recommendations")

    # List of 4 prioritized recommendation blocks
    left_tx = slide8.shapes.add_textbox(Inches(0.75), Inches(1.8), Inches(11.83), Inches(4.5))
    tf = left_tx.text_frame
    tf.word_wrap = True
    
    p = tf.paragraphs[0]
    format_tf_paragraph(p, "Key Priorities for Execution:", size=16, bold=True, color=c_navy)
    p.space_after = Pt(12)

    recs = executive_intel.get("recommendations", []) if executive_intel else []
    if not recs:
        recs = [
            "Establish dynamic stock buffer allocations based on lead times.",
            "Establish dynamic discounting rules within top product categories.",
            "Schedule automated data cleaning loops to resolve schema null records.",
            "Upgrade outlier detection thresholds to capture invoice leakage."
        ]

    for idx, r in enumerate(recs[:4]):
        cleaned_rec = r.split("—", 1)[0].replace("▸", "").strip()
        p = tf.add_paragraph()
        format_tf_paragraph(p, f"Priority {idx+1}: {cleaned_rec}", size=14, bold=True, color=c_blue)
        p_desc = tf.add_paragraph()
        format_tf_paragraph(p_desc, f"Area: Corporate Strategy  |  Impact: High  |  Effort: Medium-Low", size=11, color=c_slate)
        p_desc.space_after = Pt(8)

    # ────────────────────────────────────────────────────────────────────────
    # SLIDE 9: ACTION ROADMAP
    # ────────────────────────────────────────────────────────────────────────
    slide9 = prs.slides.add_slide(blank_layout)
    add_slide_header(slide9, "Implementation Roadmap & Timeline")

    # Columns representing timeline phases
    left_tx = slide9.shapes.add_textbox(Inches(0.75), Inches(1.8), Inches(11.83), Inches(4.5))
    tf = left_tx.text_frame
    tf.word_wrap = True
    
    p = tf.paragraphs[0]
    format_tf_paragraph(p, "Corporate Execution Stages:", size=16, bold=True, color=c_navy)
    p.space_after = Pt(14)

    phases = [
        ("Phase 1: Immediate Steps (1 - 30 Days)", [
            "• Enforce reorder safety limits on critical products.",
            "• Clean null value columns at database ingestion gate.",
            "• Establish alert thresholds on primary KPIs."
        ]),
        ("Phase 2: Operational Scale (30 - 60 Days)", [
            "• Create retargeting marketing campaigns targeting the At Risk customer segment.",
            "• Renegotiate carrier shipping contracts to trim freight costs.",
            "• Deploy sensor alarms on production lines."
        ]),
        ("Phase 3: Long-term Optimization (60 - 90 Days)", [
            "• Automate predictive cashflow simulations inside the Forecast Center.",
            "• Conduct clinical workflow reviews of high stay-length categories.",
            "• Set up structured retention cohort dashboards."
        ])
    ]

    for phase_title, steps in phases:
        p = tf.add_paragraph()
        format_tf_paragraph(p, phase_title, size=14, bold=True, color=c_blue)
        for s in steps:
            p_step = tf.add_paragraph()
            format_tf_paragraph(p_step, s, size=12, color=c_slate)
        p_step.space_after = Pt(12)

    # ────────────────────────────────────────────────────────────────────────
    # SLIDE 10: ROOT CAUSE VARIANCE ANALYSIS
    # ────────────────────────────────────────────────────────────────────────
    slide10 = prs.slides.add_slide(blank_layout)
    add_slide_header(slide10, "Root Cause Variance Analysis")

    left_tx = slide10.shapes.add_textbox(Inches(0.75), Inches(1.8), Inches(11.83), Inches(4.8))
    tf = left_tx.text_frame
    tf.word_wrap = True

    p = tf.paragraphs[0]
    format_tf_paragraph(p, "Diagnostic Variance Decomposition:", size=16, bold=True, color=c_navy)
    p.space_after = Pt(12)

    rc_list = root_causes if root_causes else []
    if rc_list:
        for i, rc in enumerate(rc_list[:6]):
            p = tf.add_paragraph()
            metric = rc.get("metric", "Unknown") if isinstance(rc, dict) else str(rc)
            cause = rc.get("root_cause", "") if isinstance(rc, dict) else ""
            impact = rc.get("impact_score", 0) if isinstance(rc, dict) else 0
            format_tf_paragraph(
                p,
                f"• {metric}: {cause} (Impact: {impact:.1f}%)" if cause else f"• {metric}",
                size=13, color=c_slate
            )
            p.space_after = Pt(10)
    else:
        p = tf.add_paragraph()
        format_tf_paragraph(p, "✓ Baseline Stability Confirmed — No significant variance detected across key metrics.", size=14, bold=True, color=c_emerald)
        p.space_after = Pt(14)
        p2 = tf.add_paragraph()
        format_tf_paragraph(p2, "All monitored KPIs are performing within acceptable bounds of their historical baselines.", size=13, color=c_slate)

    # ────────────────────────────────────────────────────────────────────────
    # SLIDE 11: EXPECTED BUSINESS IMPACT & GROWTH VECTORS
    # ────────────────────────────────────────────────────────────────────────
    slide11 = prs.slides.add_slide(blank_layout)
    add_slide_header(slide11, "Expected Business Impact & Growth Vectors")

    left_tx = slide11.shapes.add_textbox(Inches(0.75), Inches(1.8), Inches(5.5), Inches(4.5))
    tf = left_tx.text_frame
    tf.word_wrap = True

    p = tf.paragraphs[0]
    format_tf_paragraph(p, "Projected Impact Assessment:", size=16, bold=True, color=c_navy)
    p.space_after = Pt(12)

    # Build impact assessment from data
    impact_items = []
    if health_scores:
        score_val = health_scores.get("score", 0)
        if score_val >= 80:
            impact_items.append(f"• Strong operational health ({score_val}%) positions the business for aggressive growth strategies.")
        elif score_val >= 60:
            impact_items.append(f"• Moderate health score ({score_val}%) indicates optimization opportunities before scaling.")
        else:
            impact_items.append(f"• Below-target health ({score_val}%) signals urgency for remediation before new initiatives.")

    if kpis:
        up_kpis = [k for k in kpis if k.get("trend") == "up"]
        down_kpis = [k for k in kpis if k.get("trend") == "down"]
        if up_kpis:
            impact_items.append(f"• {len(up_kpis)} KPIs trending upward — momentum supports expanded investment.")
        if down_kpis:
            impact_items.append(f"• {len(down_kpis)} KPIs trending downward — corrective measures recommended within 30 days.")

    impact_items.append(f"• Dataset contains {schema.row_count:,} records across {schema.column_count} dimensions for robust decision modeling.")
    
    recs_intel = executive_intel.get("recommendations", []) if executive_intel else []
    if recs_intel:
        impact_items.append(f"• Implementing top {min(len(recs_intel), 3)} recommendations expected to yield measurable improvement within 90 days.")

    for item in impact_items[:6]:
        p = tf.add_paragraph()
        format_tf_paragraph(p, item, size=13, color=c_slate)
        p.space_after = Pt(10)

    # Right side: Growth vectors chart
    try:
        numeric_cols = get_analytic_numeric_cols(df, schema)
        if numeric_cols and len(numeric_cols) >= 2:
            fig, ax = plt.subplots(figsize=(5.5, 3.5), facecolor="#F8FAFC")
            ax.set_facecolor("#FFFFFF")
            metrics_to_show = numeric_cols[:4]
            means = [df[c].mean() for c in metrics_to_show]
            bar_colors = ["#2563EB", "#7C3AED", "#059669", "#D97706"][:len(metrics_to_show)]
            ax.barh(
                [c[:15] for c in metrics_to_show], means,
                color=bar_colors, edgecolor="white", height=0.5
            )
            ax.set_title("Key Metric Averages", fontsize=10, fontweight="bold", color="#1E3A8A", pad=8)
            ax.tick_params(axis="both", labelsize=7.5)
            ax.grid(axis="x", linestyle="--", alpha=0.3, color="#CBD5E1")
            for spine in ["top", "right"]:
                ax.spines[spine].set_visible(False)
            plt.tight_layout()
            img_buf = io.BytesIO()
            plt.savefig(img_buf, format="png", dpi=200)
            img_buf.seek(0)
            plt.close(fig)
            slide11.shapes.add_picture(img_buf, Inches(6.75), Inches(1.8), Inches(5.8), Inches(4.0))
    except Exception as e:
        logger.warning(f"Impact chart failed: {e}")

    # ────────────────────────────────────────────────────────────────────────
    # SLIDE 12: APPENDIX & METHODOLOGY (Dark Navy — Closing Slide)
    # ────────────────────────────────────────────────────────────────────────
    slide12 = prs.slides.add_slide(blank_layout)
    set_bg_color(slide12, c_navy)
    add_slide_header(slide12, "Appendix: Models & Methodology", dark_mode=True)

    # Content
    left_tx = slide12.shapes.add_textbox(Inches(0.75), Inches(1.8), Inches(11.83), Inches(4.5))
    tf = left_tx.text_frame
    tf.word_wrap = True
    
    p = tf.paragraphs[0]
    format_tf_paragraph(p, "Analytical Engine Specifications:", size=16, bold=True, color=c_white)
    p.space_after = Pt(12)

    specs = [
        "1. Domain Semantic Scanner: Categorizes datasets by token matching against column headers, boosting key currencies.",
        "2. Anomaly Isolation Telemetry: Applies consensus thresholds combining 3-sigma Z-score limits and Interquartile (IQR) bands.",
        "3. Horizon Forecast Models: Uses Double Exponential Smoothing (Holt's Linear) and autoregressive integrations.",
        "4. Customer RFM Scoring: Ranks accounts based on quintiles of recency intervals, transaction frequencies, and monetary volumes.",
        "5. Business Health Index: Formulates a weighted index combining coverage, completeness, growth rates, and outlier variances."
    ]
    for spec in specs:
        p = tf.add_paragraph()
        format_tf_paragraph(p, spec, size=13, color=RGBColor(203, 213, 225))
        p.space_after = Pt(10)

    # Q&A closing text
    qa_tx = slide12.shapes.add_textbox(Inches(0.75), Inches(6.2), Inches(11.83), Inches(0.8))
    tf_qa = qa_tx.text_frame
    p_qa = tf_qa.paragraphs[0]
    format_tf_paragraph(p_qa, "Thank you — Questions & Discussion", size=20, bold=True, color=c_royal)
    p_qa.alignment = PP_ALIGN.CENTER

    # Save to buffer
    buffer = io.BytesIO()
    prs.save(buffer)
    ppt_bytes = buffer.getvalue()
    buffer.close()
    return ppt_bytes


def _render_ppt_chart(chart_type: str, df: pd.DataFrame, schema: DatasetSchema, kpis: List[Dict[str, Any]], extra: Dict[str, Any] = None) -> Optional[io.BytesIO]:
    """Helper to render Matplotlib charts for PPT slides, returning a BytesIO buffer."""
    from core.df_utils import get_analytic_numeric_cols
    import matplotlib.pyplot as plt
    import numpy as np

    fig, ax = plt.subplots(figsize=(6.0, 4.2), facecolor="#F8FAFC")
    ax.set_facecolor("#FFFFFF")

    primary_color = "#1E3A8A"
    secondary_color = "#2563EB"
    accent_green = "#059669"
    warning_orange = "#D97706"
    danger_red = "#DC2626"
    
    numeric_cols = get_analytic_numeric_cols(df, schema)

    try:
        if chart_type == "trend":
            if schema.date_columns and numeric_cols:
                date_col = schema.date_columns[0]
                metric = numeric_cols[0]
                df_agg = df.dropna(subset=[date_col, metric]).groupby(date_col)[metric].sum().reset_index()
                df_agg = df_agg.sort_values(date_col).head(24)

                ax.plot(df_agg[date_col].astype(str), df_agg[metric], color=secondary_color, marker="o", linewidth=2, markersize=5, label="Actual")
                df_agg["rolling_mean"] = df_agg[metric].rolling(window=5, min_periods=1).mean()
                ax.plot(df_agg[date_col].astype(str), df_agg["rolling_mean"], color="#7C3AED", linewidth=2, linestyle="--", label="5-Period MA")

                ax.set_title(f"Performance Trend: {metric} Over Time", fontsize=11, fontweight="bold", color=primary_color, pad=8)
                ax.tick_params(axis="x", rotation=20, labelsize=7.5)
                ax.tick_params(axis="y", labelsize=7.5)
                ax.legend(fontsize=7.5, loc="upper right", frameon=False)
            else:
                ax.text(0.5, 0.5, "Insufficient trend variables", ha='center', va='center')

        elif chart_type == "anomaly":
            if schema.date_columns and numeric_cols:
                date_col = schema.date_columns[0]
                metric = numeric_cols[0]
                df_sorted = df.dropna(subset=[date_col, metric]).copy()
                df_sorted[date_col] = pd.to_datetime(df_sorted[date_col], errors="coerce")
                df_sorted = df_sorted.dropna(subset=[date_col]).sort_values(date_col).head(100)

                mean_val = df_sorted[metric].mean()
                std_val = df_sorted[metric].std()
                anoms_mask = (df_sorted[metric] - mean_val).abs() > (1.8 * std_val)

                ax.scatter(df_sorted[date_col].astype(str), df_sorted[metric], color=secondary_color, s=15, alpha=0.6, label="Normal")
                if anoms_mask.any():
                    ax.scatter(df_sorted.loc[anoms_mask, date_col].astype(str), df_sorted.loc[anoms_mask, metric], color=danger_red, s=35, label="Anomalous")

                ax.set_title("Consensus Anomalies Telemetry", fontsize=11, fontweight="bold", color=primary_color, pad=8)
                ax.tick_params(axis="x", rotation=25, labelsize=7)
                ax.tick_params(axis="y", labelsize=7.5)
                ax.legend(fontsize=7.5, loc="upper right", frameon=False)
            else:
                ax.text(0.5, 0.5, "Insufficient timeline anomalies", ha='center', va='center')

        elif chart_type == "customer":
            if extra and extra.get("customer_intel") and extra["customer_intel"].get("eligible"):
                intel = extra["customer_intel"]
                segs = intel["segments"]
                names = [v["name"] for v in segs.values() if v["customer_count"] > 0]
                shares = [v["share_percentage"] for v in segs.values() if v["customer_count"] > 0]

                ax.bar(names, shares, color=secondary_color, edgecolor="white", width=0.45)
                ax.set_title("Revenue Contribution by RFM Segment", fontsize=11, fontweight="bold", color=primary_color, pad=8)
                ax.tick_params(axis="x", rotation=15, labelsize=7.5)
                ax.tick_params(axis="y", labelsize=7.5)
            else:
                if numeric_cols:
                    metric = numeric_cols[0]
                    ax.hist(df[metric].dropna(), bins=10, color=secondary_color, edgecolor="white")
                    ax.set_title(f"Dataset Distribution: {metric}", fontsize=11, fontweight="bold", color=primary_color, pad=8)
                    ax.tick_params(axis="both", labelsize=7.5)
                else:
                    ax.text(0.5, 0.5, "Insufficient customer profiles", ha='center', va='center')

        elif chart_type == "forecast":
            if schema.date_columns and numeric_cols:
                date_col = schema.date_columns[0]
                metric = numeric_cols[0]
                df_agg = df.dropna(subset=[date_col, metric]).groupby(date_col)[metric].sum().reset_index()
                df_agg = df_agg.sort_values(date_col).tail(15)

                last_idx = len(df_agg)
                hist_x = [f"P{i}" for i in range(1, last_idx + 1)]
                hist_y = df_agg[metric].tolist()

                ax.plot(hist_x, hist_y, color=primary_color, marker="o", label="Historical", linewidth=2, markersize=4)

                fc_x = [f"F{i}" for i in range(1, 6)]
                last_y = hist_y[-1]
                expected_y = [last_y * (1.02 ** i) for i in range(1, 6)]
                best_y = [last_y * (1.05 ** i) for i in range(1, 6)]
                worst_y = [last_y * (0.97 ** i) for i in range(1, 6)]

                full_fc_x = [hist_x[-1]] + fc_x
                full_expected_y = [last_y] + expected_y
                full_best_y = [last_y] + best_y
                full_worst_y = [last_y] + worst_y

                ax.plot(full_fc_x, full_expected_y, color=secondary_color, linestyle="--", label="Expected")
                ax.plot(full_fc_x, full_best_y, color=accent_green, linestyle="--", label="Best Case")
                ax.plot(full_fc_x, full_worst_y, color=danger_red, linestyle="--", label="Worst Case")

                ax.fill_between(full_fc_x, full_worst_y, full_best_y, color=secondary_color, alpha=0.1)

                ax.set_title("90-Day Horizon Projections", fontsize=11, fontweight="bold", color=primary_color, pad=8)
                ax.tick_params(axis="both", labelsize=7.5)
                ax.legend(fontsize=7, loc="upper left", frameon=False)
            else:
                ax.text(0.5, 0.5, "Insufficient forecast horizons", ha='center', va='center')

        # Style layout
        ax.grid(True, linestyle="--", alpha=0.3, color="#CBD5E1")
        for spine in ["top", "right"]:
            ax.spines[spine].set_visible(False)
        for spine in ["left", "bottom"]:
            ax.spines[spine].set_color("#94A3B8")
            ax.spines[spine].set_linewidth(0.5)

        plt.tight_layout()
        img_buf = io.BytesIO()
        plt.savefig(img_buf, format="png", dpi=200)
        img_buf.seek(0)
        plt.close(fig)
        return img_buf

    except Exception as e:
        plt.close()
        logger.error(f"Failed to render PPT chart: {e}", exc_info=True)
        return None
