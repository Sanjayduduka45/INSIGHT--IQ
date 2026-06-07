"""
InsightIQ — Export API
"""

import io
import logging
from fastapi import APIRouter, HTTPException, Depends, Response

from dataclasses import asdict
from api.datasets import get_dataset_store
from api.analytics import _generate_insights
from export.pdf_generator import generate_executive_pdf
from export.ppt_generator import generate_executive_ppt
from core.security import get_current_user
from analytics.health_score import compute_explainable_health_score
from analytics.insights import generate_executive_report
import re

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/export", tags=["export"])


def _sanitize_filename(name: str) -> str:
    """Sanitize a filename for use in Content-Disposition headers."""
    # Remove path separators and control characters
    name = re.sub(r'[\x00-\x1f\x7f/\\:*?"<>|]', '_', name)
    # Collapse multiple underscores
    name = re.sub(r'_+', '_', name).strip('_')
    return name[:200] if name else 'dataset'


def _log_report_export(dataset_id: str, name: str, format: str, user: dict):
    """Log report generation event to Supabase reports table."""
    from core.settings import get_settings
    settings = get_settings()
    if settings.has_supabase and user and user.get("role") != "guest":
        try:
            from supabase import create_client, Client
            client: Client = create_client(settings.supabase_url, settings.supabase_anon_key)
            if user.get("token"):
                client.postgrest.auth(user["token"])
            
            client.table("reports").insert({
                "user_id": user.get("id"),
                "dataset_id": dataset_id,
                "name": name,
                "format": format,
            }).execute()
            logger.info(f"Successfully logged report export ({format}) to Supabase.")
        except Exception as e:
            logger.error(f"Failed to log report export: {e}")


@router.get("/{dataset_id}/pdf")
async def export_pdf(dataset_id: str, user: dict = Depends(get_current_user)):
    """Export executive summary as PDF."""
    ds = get_dataset_store().get(dataset_id)
    if not ds:
        raise HTTPException(404, "Dataset not found")

    df = ds["df"]
    schema = ds["schema"]
    quality = ds["quality"]
    domain = ds["domain"].domain
    raw_kpis = ds.get("kpis", [])
    kpis = [asdict(k) for k in raw_kpis]
    insights = _generate_insights(df, schema, raw_kpis, domain)
    health_scores = compute_explainable_health_score(df, schema, quality, raw_kpis)
    executive_intel = generate_executive_report(df, schema, quality, raw_kpis, domain)

    try:
        pdf_bytes = generate_executive_pdf(
            ds["name"],
            kpis,
            insights,
            df=df,
            schema=schema,
            health_scores=health_scores,
            executive_intel=executive_intel
        )
        safe_name = _sanitize_filename(ds['name'])
        _log_report_export(dataset_id, f"InsightIQ_Report_{safe_name}.pdf", "pdf", user)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="InsightIQ_Report_{safe_name}.pdf"'
            },
        )
    except Exception as e:
        logger.error(f"PDF generation failed for dataset {dataset_id}: {e}", exc_info=True)
        raise HTTPException(500, "Failed to generate PDF report. Please try again or contact support.")


@router.get("/{dataset_id}/ppt")
async def export_ppt(dataset_id: str, user: dict = Depends(get_current_user)):
    """Export executive summary as PowerPoint."""
    ds = get_dataset_store().get(dataset_id)
    if not ds:
        raise HTTPException(404, "Dataset not found")

    df = ds["df"]
    schema = ds["schema"]
    quality = ds["quality"]
    domain = ds["domain"].domain
    raw_kpis = ds.get("kpis", [])
    kpis = [asdict(k) for k in raw_kpis]
    insights = _generate_insights(df, schema, raw_kpis, domain)
    health_scores = compute_explainable_health_score(df, schema, quality, raw_kpis)
    executive_intel = generate_executive_report(df, schema, quality, raw_kpis, domain)

    try:
        ppt_bytes = generate_executive_ppt(
            ds["name"],
            kpis,
            insights,
            health_scores=health_scores,
            executive_intel=executive_intel
        )
        safe_name = _sanitize_filename(ds['name'])
        _log_report_export(dataset_id, f"InsightIQ_Report_{safe_name}.pptx", "ppt", user)
        return Response(
            content=ppt_bytes,
            media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            headers={
                "Content-Disposition": f'attachment; filename="InsightIQ_Report_{safe_name}.pptx"'
            },
        )
    except Exception as e:
        logger.error(f"PPT generation failed for dataset {dataset_id}: {e}", exc_info=True)
        raise HTTPException(500, "Failed to generate PowerPoint report. Please try again or contact support.")


@router.get("/{dataset_id}/csv")
async def export_csv(dataset_id: str, user: dict = Depends(get_current_user)):
    """Export the dataset as CSV."""
    ds = get_dataset_store().get(dataset_id)
    if not ds:
        raise HTTPException(404, "Dataset not found")

    try:
        df = ds["df"]
        buffer = io.StringIO()
        df.to_csv(buffer, index=False)
        safe_name = _sanitize_filename(ds['name'])
        _log_report_export(dataset_id, f"{safe_name}_Export.csv", "csv", user)
        return Response(
            content=buffer.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{safe_name}_Export.csv"'},
        )
    except Exception as e:
        logger.error(f"CSV export failed for dataset {dataset_id}: {e}")
        raise HTTPException(500, "Failed to export CSV. Please try again or contact support.")
