"""
InsightIQ — PowerPoint Report Generator
"""

import io
from typing import Dict, Any, List, Optional

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor


def generate_executive_ppt(
    dataset_name: str,
    kpis: List[Dict[str, Any]],
    insights: List[Dict[str, Any]],
    health_scores: Optional[Dict[str, Any]] = None,
    executive_intel: Optional[Dict[str, Any]] = None,
) -> bytes:
    """Generate a high-fidelity PowerPoint executive summary report."""
    prs = Presentation()

    # ── SLIDE 1: Title Slide ──────────────────────────────────────────────────
    title_slide_layout = prs.slide_layouts[0]
    slide = prs.slides.add_slide(title_slide_layout)
    title = slide.shapes.title
    subtitle = slide.placeholders[1]

    title.text = "InsightIQ Executive Report"
    title.text_frame.paragraphs[0].font.color.rgb = RGBColor(30, 64, 175)  # #1E40AF
    
    sub_text = f"Strategic Dataset Intelligence: {dataset_name}\n"
    if health_scores:
        sub_text += f"Overall Business Health Index: {health_scores.get('score', 0)}%\n"
    sub_text += "Generated automatically by InsightIQ Enterprise Platform"
    subtitle.text = sub_text

    # ── SLIDE 2: Executive Summary Slide ──────────────────────────────────────
    bullet_layout = prs.slide_layouts[1]  # Title and Content
    slide = prs.slides.add_slide(bullet_layout)
    title = slide.shapes.title
    title.text = "Executive BI Narrative"
    title.text_frame.paragraphs[0].font.color.rgb = RGBColor(37, 99, 235)

    body_shape = slide.shapes.placeholders[1]
    tf = body_shape.text_frame
    tf.word_wrap = True

    # 1. Summary
    p1 = tf.paragraphs[0]
    p1.text = "Strategic Executive Summary:"
    p1.font.bold = True
    p1.font.size = Pt(18)
    p1.font.color.rgb = RGBColor(15, 23, 42)

    p2 = tf.add_paragraph()
    p2.text = executive_intel.get("summary", "N/A") if executive_intel else "No summary narrative compiled."
    p2.level = 1
    p2.font.size = Pt(14)
    p2.space_after = Pt(14)

    # 2. Data Story
    p3 = tf.add_paragraph()
    p3.text = "Operational Data Narrative:"
    p3.font.bold = True
    p3.font.size = Pt(18)
    p3.font.color.rgb = RGBColor(15, 23, 42)

    p4 = tf.add_paragraph()
    p4.text = executive_intel.get("data_story", "N/A") if executive_intel else "No data story compiled."
    p4.level = 1
    p4.font.size = Pt(14)

    # ── SLIDE 3: Business Health Scorecard Slide ──────────────────────────────
    if health_scores and health_scores.get("breakdown"):
        slide = prs.slides.add_slide(prs.slide_layouts[5])  # Title only
        title = slide.shapes.title
        title.text = f"Business Health Scorecard ({health_scores.get('score', 0)}%)"
        title.text_frame.paragraphs[0].font.color.rgb = RGBColor(37, 99, 235)

        # Explanation callout
        txBox = slide.shapes.add_textbox(Inches(1), Inches(1.5), Inches(8), Inches(0.8))
        tf_explain = txBox.text_frame
        tf_explain.word_wrap = True
        p_exp = tf_explain.paragraphs[0]
        p_exp.text = f"Diagnosis: {health_scores.get('explanation', '')}"
        p_exp.font.italic = True
        p_exp.font.size = Pt(13)
        p_exp.font.color.rgb = RGBColor(71, 85, 105)

        # Add Table for Health Breakdown
        breakdown = health_scores.get("breakdown", {})
        rows = len(breakdown) + 1
        cols = 3
        left = Inches(1)
        top = Inches(2.5)
        width = Inches(8)
        height = Inches(0.5 * rows)

        table = slide.shapes.add_table(rows, cols, left, top, width, height).table
        table.columns[0].width = Inches(3.5)
        table.columns[1].width = Inches(2.25)
        table.columns[2].width = Inches(2.25)

        # Headers
        table.cell(0, 0).text = "Assessment Factor"
        table.cell(0, 1).text = "Target Weight"
        table.cell(0, 2).text = "Contribution Score"
        for i in range(3):
            cell = table.cell(0, i)
            cell.fill.solid()
            cell.fill.fore_color.rgb = RGBColor(30, 64, 175)
            p = cell.text_frame.paragraphs[0]
            p.font.bold = True
            p.font.color.rgb = RGBColor(255, 255, 255)
            p.font.size = Pt(12)

        # Data Rows
        for i, (key, val) in enumerate(breakdown.items()):
            row_idx = i + 1
            table.cell(row_idx, 0).text = val.get("label", key)
            table.cell(row_idx, 1).text = f"{val.get('weight', 0)*100:.0f}%"
            table.cell(row_idx, 2).text = f"+{val.get('contribution', 0):.1f}%"
            for j in range(3):
                p = table.cell(row_idx, j).text_frame.paragraphs[0]
                p.font.size = Pt(11)
                p.font.color.rgb = RGBColor(15, 23, 42)

    # ── SLIDE 4: KPI Slide ────────────────────────────────────────────────────
    if kpis:
        slide = prs.slides.add_slide(prs.slide_layouts[5])  # Title only
        title = slide.shapes.title
        title.text = "Strategic Key Performance Indicators"
        title.text_frame.paragraphs[0].font.color.rgb = RGBColor(37, 99, 235)

        # Add a table
        rows = min(len(kpis) + 1, 6)
        cols = 4
        left = Inches(0.5)
        top = Inches(2.0)
        width = Inches(9.0)
        height = Inches(0.6 * rows)

        table = slide.shapes.add_table(rows, cols, left, top, width, height).table

        table.columns[0].width = Inches(3.25)
        table.columns[1].width = Inches(1.75)
        table.columns[2].width = Inches(1.75)
        table.columns[3].width = Inches(2.25)

        # Headers
        headers = ["Metric Name", "Value", "Trend", "Impact Category"]
        for i, header in enumerate(headers):
            cell = table.cell(0, i)
            cell.text = header
            cell.fill.solid()
            cell.fill.fore_color.rgb = RGBColor(219, 234, 254)  # #DBEAFE
            paragraph = cell.text_frame.paragraphs[0]
            paragraph.font.bold = True
            paragraph.font.size = Pt(12)
            paragraph.font.color.rgb = RGBColor(30, 64, 175)

        # Data Rows
        for i, kpi in enumerate(kpis[:5]):
            trend_str = f"{kpi.get('trend_value', 0)}%"
            if kpi.get("trend") == "up":
                trend_str = "+" + trend_str
            elif kpi.get("trend") == "down":
                trend_str = "-" + trend_str
            else:
                trend_str = "Stable"

            row_idx = i + 1
            table.cell(row_idx, 0).text = kpi.get("name", "N/A")
            table.cell(row_idx, 1).text = str(kpi.get("formatted_value", "N/A"))
            
            trend_cell = table.cell(row_idx, 2)
            trend_cell.text = trend_str
            
            table.cell(row_idx, 3).text = kpi.get("category", "General").capitalize()

            # Format text size
            for col_idx in range(4):
                p = table.cell(row_idx, col_idx).text_frame.paragraphs[0]
                p.font.size = Pt(11)
                p.font.color.rgb = RGBColor(15, 23, 42)

            # Highlight trend color
            trend_p = trend_cell.text_frame.paragraphs[0]
            if kpi.get("trend") == "up":
                trend_p.font.color.rgb = RGBColor(5, 150, 105)  # Green
            elif kpi.get("trend") == "down":
                trend_p.font.color.rgb = RGBColor(220, 38, 38)  # Red

    # ── SLIDE 5: Strategic Recommendations Slide ──────────────────────────────
    slide = prs.slides.add_slide(prs.slide_layouts[1])  # Title and content
    title = slide.shapes.title
    title.text = "Strategic Recommendations & Execution"
    title.text_frame.paragraphs[0].font.color.rgb = RGBColor(37, 99, 235)

    body_shape = slide.shapes.placeholders[1]
    tf = body_shape.text_frame
    tf.word_wrap = True

    recs_list = []
    if executive_intel and executive_intel.get("recommendations"):
        recs_list = executive_intel["recommendations"]
    else:
        recs_list = [
            "Align category profiles to capture high-margin segment variations.",
            "Address primary data quality completeness vectors to secure reporting integrity.",
            "Utilize predictive models inside the Forecast Center to simulate future inventories."
        ]

    for i, r in enumerate(recs_list[:4]):
        if i == 0:
            p = tf.paragraphs[0]
        else:
            p = tf.add_paragraph()

        # Split recommendation title and description
        if "—" in r:
            title_text, desc_text = r.split("—", 1)
            p.text = f"▸ {title_text.strip()}: "
            p.font.bold = True
            p.font.size = Pt(14)
            p.font.color.rgb = RGBColor(30, 64, 175)
            
            p_desc = tf.add_paragraph()
            p_desc.text = desc_text.strip()
            p_desc.level = 1
            p_desc.font.size = Pt(12)
            p_desc.font.color.rgb = RGBColor(71, 85, 105)
            p_desc.space_after = Pt(10)
        else:
            p.text = f"▸ {r}"
            p.font.bold = True
            p.font.size = Pt(14)
            p.font.color.rgb = RGBColor(15, 23, 42)
            p.space_after = Pt(10)

    buffer = io.BytesIO()
    prs.save(buffer)

    ppt_bytes = buffer.getvalue()
    buffer.close()
    return ppt_bytes
