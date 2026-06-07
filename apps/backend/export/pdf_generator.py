"""
InsightIQ — Professional McKinsey-Style PDF Report Generator

Generates high-fidelity executive summaries, dataset metadata,
tabular reports, and custom matplotlib visual charts.
"""

from __future__ import annotations

import io
import datetime
from typing import Any, Dict, List, Optional

import pandas as pd
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.pyplot as plt

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

from intelligence.schema_detector import DatasetSchema


def generate_executive_pdf(
    dataset_name: str,
    kpis: List[Dict[str, Any]],
    insights: List[Dict[str, Any]],
    df: Optional[pd.DataFrame] = None,
    schema: Optional[DatasetSchema] = None,
    health_scores: Optional[Dict[str, Any]] = None,
    executive_intel: Optional[Dict[str, Any]] = None,
) -> bytes:
    """Generate a high-fidelity McKinsey-style PDF report with cover page, health scorecard, and embedded metrics charts."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=45,
        bottomMargin=45
    )

    styles = getSampleStyleSheet()

    # Define color scheme
    primary_color = colors.HexColor("#1E3A8A")   # Navy/Slate Blue
    secondary_color = colors.HexColor("#3B82F6") # Royal Blue
    neutral_dark = colors.HexColor("#0F172A")    # Charcoal
    neutral_light = colors.HexColor("#F8FAFC")   # Slate 50
    border_color = colors.HexColor("#E2E8F0")    # Slate 200

    # Custom Typography Styles
    title_style = ParagraphStyle(
        "CoverTitle",
        parent=styles["Heading1"],
        fontSize=26,
        leading=32,
        textColor=colors.white,
        spaceAfter=15,
    )
    subtitle_style = ParagraphStyle(
        "CoverSubtitle",
        parent=styles["Normal"],
        fontSize=12,
        leading=18,
        textColor=colors.HexColor("#93C5FD"),
        spaceAfter=30,
    )
    section_heading = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontSize=14,
        leading=20,
        textColor=primary_color,
        spaceBefore=14,
        spaceAfter=10,
        keepWithNext=True,
    )
    body_style = ParagraphStyle(
        "ReportBody",
        parent=styles["Normal"],
        fontSize=9.5,
        leading=14,
        textColor=neutral_dark,
    )
    bullet_style = ParagraphStyle(
        "ReportBullet",
        parent=body_style,
        leftIndent=15,
        firstLineIndent=-10,
        spaceBefore=4,
    )

    elements = []

    # ── COVER PAGE ──────────────────────────────────────────────────────────
    elements.append(Spacer(1, 30))
    
    banner_data = [
        [
            Paragraph("<b>INSIGHTIQ PLATFORM v2</b>", ParagraphStyle("BannerMini", parent=styles["Normal"], fontSize=8, textColor=colors.HexColor("#60A5FA"), leading=9)),
        ],
        [
            Paragraph("ENTERPRISE AI DATA INTELLIGENCE REPORT", title_style),
        ],
        [
            Paragraph(f"Strategic Diagnostic Report for {dataset_name}", subtitle_style),
        ]
    ]
    banner_table = Table(banner_data, colWidths=[530])
    banner_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), primary_color),
                ("TOPPADDING", (0, 0), (-1, -1), 25),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 30),
                ("LEFTPADDING", (0, 0), (-1, -1), 25),
                ("RIGHTPADDING", (0, 0), (-1, -1), 25),
            ]
        )
    )
    elements.append(banner_table)
    elements.append(Spacer(1, 40))

    # Metadata Card
    meta_data = [
        ["Report Security", "Restricted - Executive Summary"],
        ["Generated At", datetime.date.today().strftime("%B %d, %Y")],
        ["Dataset Name", dataset_name],
    ]
    if df is not None and schema is not None:
        meta_data.append(["Row Count", f"{schema.row_count:,} rows"])
        meta_data.append(["Column Count", f"{schema.column_count} columns"])
        meta_data.append(["Completeness", f"{100 - (df.isna().mean().mean() * 100):.1f}%"])
    if health_scores:
        meta_data.append(["Business Health Index", f"{health_scores.get('score', 0)}%"])

    meta_table = Table(meta_data, colWidths=[160, 290])
    meta_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), neutral_light),
                ("GRID", (0, 0), (-1, -1), 1, border_color),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("TEXTCOLOR", (0, 0), (-1, -1), neutral_dark),
                ("PADDING", (0, 0), (-1, -1), 8),
                ("FONTSIZE", (0, 0), (-1, -1), 9.5),
            ]
        )
    )
    elements.append(meta_table)
    elements.append(Spacer(1, 100))

    disclaimer_style = ParagraphStyle(
        "Disclaimer",
        parent=body_style,
        fontSize=8,
        textColor=colors.HexColor("#64748B"),
        alignment=TA_CENTER
    )
    elements.append(Paragraph("This document contains proprietary strategic business intelligence. All recommendations are derived from structured statistical trends. Verify all assumptions prior to implementation.", disclaimer_style))
    elements.append(PageBreak())

    # ── SECTION 1: EXECUTIVE AI BRAIN & STORYTELLING ─────────────────────────
    elements.append(Paragraph("Executive BI Summary & Narrative", section_heading))
    summary_text = "N/A"
    data_story_text = ""
    if executive_intel:
        summary_text = executive_intel.get("summary", "")
        data_story_text = executive_intel.get("data_story", "")
    
    elements.append(Paragraph(f"<b>Strategic Executive Summary:</b> {summary_text}", body_style))
    elements.append(Spacer(1, 10))
    if data_story_text:
        elements.append(Paragraph(f"<b>Data Storytelling Narrative:</b> {data_story_text}", body_style))
        elements.append(Spacer(1, 15))

    # ── SECTION 2: EXPLAINABLE BUSINESS HEALTH SCORE ─────────────────────────
    if health_scores:
        elements.append(Paragraph("Business Health Index Scorecard", section_heading))
        health_score_val = health_scores.get("score", 0)
        explanation_val = health_scores.get("explanation", "")
        
        elements.append(Paragraph(f"The overall Business Health Score is evaluated at <b>{health_score_val}%</b>. {explanation_val}", body_style))
        elements.append(Spacer(1, 8))
        
        breakdown = health_scores.get("breakdown", {})
        if breakdown:
            health_table_data = [["Assessment Factor", "Assigned Weight", "Contribution Score", "Factor Performance"]]
            for factor_key, factor_val in breakdown.items():
                health_table_data.append([
                    factor_val.get("label", factor_key),
                    f"{factor_val.get('weight', 0)*100:.0f}%",
                    f"+{factor_val.get('contribution', 0):.1f}%",
                    f"{factor_val.get('score', 0):.1f}%"
                ])
            
            ht = Table(health_table_data, colWidths=[180, 100, 130, 120])
            ht.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), primary_color),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("GRID", (0, 0), (-1, -1), 1, border_color),
                        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, neutral_light]),
                        ("PADDING", (0, 0), (-1, -1), 6),
                        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                    ]
                )
            )
            elements.append(ht)
            elements.append(Spacer(1, 15))

    elements.append(PageBreak())

    # ── SECTION 3: KEY PERFORMANCE INDICATORS ───────────────────────────────
    elements.append(Paragraph("Strategic Key Performance Indicators", section_heading))
    elements.append(Paragraph("Below are the primary computed indicators resolved from the source dataset, tracking performance trends over time.", body_style))
    elements.append(Spacer(1, 10))

    if kpis:
        kpi_table_data = [["Metric Name", "Value", "Trend", "Impact Category"]]
        for kpi in kpis:
            trend_val = kpi.get("trend_value", 0)
            trend_dir = kpi.get("trend", "stable")
            trend_str = "Stable"
            if trend_dir == "up":
                trend_str = f"▲ +{trend_val:.1f}%"
            elif trend_dir == "down":
                trend_str = f"▼ {trend_val:.1f}%"

            kpi_table_data.append([
                kpi.get("name", "N/A"),
                str(kpi.get("formatted_value", "N/A")),
                trend_str,
                kpi.get("category", "General").capitalize()
            ])

        t = Table(kpi_table_data, colWidths=[180, 100, 110, 140])
        t.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), primary_color),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
                    ("GRID", (0, 0), (-1, -1), 1, border_color),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, neutral_light]),
                    ("PADDING", (0, 0), (-1, -1), 6),
                    ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                ]
            )
        )
        elements.append(t)
        elements.append(Spacer(1, 15))

    # ── SECTION 4: CHARTS & VISUALIZATIONS (RELEVANCE FILTERED) ─────────────
    if df is not None and schema is not None:
        from core.df_utils import get_analytic_numeric_cols
        analytic_nums = get_analytic_numeric_cols(df, schema)
        
        # Verify if a high-relevance metric is available (strip ID variables)
        if analytic_nums:
            elements.append(Paragraph("Performance Visualizations", section_heading))
            elements.append(Paragraph("Visual representation of the primary business drivers over time, excluding low-relevance variables.", body_style))
            elements.append(Spacer(1, 10))

            try:
                fig, ax = plt.subplots(figsize=(6.5, 2.5))
                metric_col = analytic_nums[0]
                
                # If we have dates, plot trend line
                if schema.date_columns:
                    date_col = schema.date_columns[0]
                    df_agg = df.dropna(subset=[date_col, metric_col]).groupby(date_col)[metric_col].sum().reset_index()
                    df_agg = df_agg.sort_values(date_col).head(25)
                    
                    ax.plot(df_agg[date_col].astype(str), df_agg[metric_col], color="#2563EB", marker="o", linewidth=1.5, markersize=4)
                    ax.set_title(f"{metric_col} Trend Over Time", fontsize=9.5, fontweight="bold", color="#1E3A8A")
                    ax.set_xlabel(date_col, fontsize=7.5)
                    ax.set_ylabel(metric_col, fontsize=7.5)
                    ax.tick_params(axis="x", rotation=25, labelsize=6.5)
                    ax.tick_params(axis="y", labelsize=6.5)
                    plt.grid(True, linestyle="--", alpha=0.4, color="#CBD5E1")
                    plt.tight_layout()
                else:
                    # Otherwise, plot distribution histogram of the primary metric
                    ax.hist(df[metric_col].dropna(), bins=15, color="#7C3AED", edgecolor="white", alpha=0.8)
                    ax.set_title(f"Distribution of {metric_col}", fontsize=9.5, fontweight="bold", color="#1E3A8A")
                    ax.set_xlabel(metric_col, fontsize=7.5)
                    ax.set_ylabel("Frequency", fontsize=7.5)
                    ax.tick_params(axis="both", labelsize=6.5)
                    plt.grid(True, linestyle="--", alpha=0.4, color="#CBD5E1")
                    plt.tight_layout()

                img_buf = io.BytesIO()
                plt.savefig(img_buf, format="png", dpi=200)
                img_buf.seek(0)
                plt.close(fig)

                elements.append(Image(img_buf, width=480, height=185))
                elements.append(Spacer(1, 15))
            except Exception as plot_err:
                plt.close()
                logger.error(f"Failed to render chart inside PDF report: {plot_err}")

    # ── SECTION 5: STRATEGIC RECOMMENDATIONS ─────────────────────────────────
    elements.append(Paragraph("Strategic Action Plan & Recommendations", section_heading))
    
    recs_list = []
    if executive_intel and executive_intel.get("recommendations"):
        recs_list = executive_intel["recommendations"]
    else:
        recs_list = [
            "Align category profiles to capture high-margin segment variations.",
            "Address primary data quality completeness vectors to secure reporting integrity.",
            "Utilize predictive models inside the Forecast Center to simulate future inventories."
        ]
        
    for r in recs_list[:4]:
        elements.append(Paragraph(f"▸ <b>{r.split('—')[0]}</b> — {r.split('—')[1] if '—' in r else ''}", ParagraphStyle("SubRec", parent=body_style, leftIndent=12, firstLineIndent=-8, spaceAfter=5)))

    # ── FOOTER ──────────────────────────────────────────────────────────────
    elements.append(Spacer(1, 40))
    elements.append(
        Paragraph(
            "Report compiled automatically by InsightIQ Enterprise Intelligence Engine. All rights reserved.",
            ParagraphStyle(
                "FooterText",
                parent=styles["Normal"],
                fontSize=8,
                textColor=colors.HexColor("#94A3B8"),
                alignment=TA_CENTER,
            ),
        )
    )

    doc.build(elements)

    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
