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
import pandas as pd
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


def _get_clean_dataset_name(name: str) -> str:
    """Removes common dataset extensions and cleans name."""
    dataset_name = name
    for ext in ['.csv', '.xlsx', '.xls', '.parquet', '.json', '.tsv', '.zip']:
        if dataset_name.lower().endswith(ext):
            dataset_name = dataset_name[:-len(ext)]
            break
    return _sanitize_filename(dataset_name)


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
    context = ds.get("context")

    # Generate context-driven KPIs
    if context:
        from intelligence.kpi_generator import generate_context_driven_kpis
        raw_kpis = generate_context_driven_kpis(df, schema, domain, context)
    else:
        raw_kpis = ds.get("kpis", [])

    kpis = [asdict(k) for k in raw_kpis]
    insights = _generate_insights(df, schema, raw_kpis, domain, context)
    health_scores = compute_explainable_health_score(df, schema, quality, raw_kpis)
    executive_intel = generate_executive_report(df, schema, quality, raw_kpis, domain, context)

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
        if not pdf_bytes or not pdf_bytes.startswith(b"%PDF"):
            raise ValueError("Generated PDF bytes are invalid or missing %PDF header.")

        clean_name = _get_clean_dataset_name(ds['name'])
        filename = f"InsightIQ_Executive_Report_{clean_name}.pdf"
        _log_report_export(dataset_id, filename, "pdf", user)
        
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Length": str(len(pdf_bytes))
            },
        )
    except Exception as e:
        logger.error(f"PDF generation failed for dataset {dataset_id}: {e}", exc_info=True)
        raise HTTPException(500, f"Failed to generate PDF report: {str(e)}")


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
    context = ds.get("context")

    # Generate context-driven KPIs
    if context:
        from intelligence.kpi_generator import generate_context_driven_kpis
        raw_kpis = generate_context_driven_kpis(df, schema, domain, context)
    else:
        raw_kpis = ds.get("kpis", [])

    kpis = [asdict(k) for k in raw_kpis]
    insights = _generate_insights(df, schema, raw_kpis, domain, context)
    health_scores = compute_explainable_health_score(df, schema, quality, raw_kpis)
    executive_intel = generate_executive_report(df, schema, quality, raw_kpis, domain, context)

    try:
        ppt_bytes = generate_executive_ppt(
            ds["name"],
            kpis,
            insights,
            df=df,
            schema=schema,
            health_scores=health_scores,
            executive_intel=executive_intel,
            context=context
        )
        import zipfile
        if not ppt_bytes or not zipfile.is_zipfile(io.BytesIO(ppt_bytes)):
            raise ValueError("Generated PowerPoint bytes are invalid or corrupt zip structure.")

        clean_name = _get_clean_dataset_name(ds['name'])
        filename = f"InsightIQ_Executive_Report_{clean_name}.pptx"
        _log_report_export(dataset_id, filename, "ppt", user)
        
        return Response(
            content=ppt_bytes,
            media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Length": str(len(ppt_bytes))
            },
        )
    except Exception as e:
        logger.error(f"PPT generation failed for dataset {dataset_id}: {e}", exc_info=True)
        raise HTTPException(500, f"Failed to generate PowerPoint report: {str(e)}")


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
        csv_bytes = buffer.getvalue().encode('utf-8')
        clean_name = _get_clean_dataset_name(ds['name'])
        filename = f"InsightIQ_Raw_Data_{clean_name}.csv"
        _log_report_export(dataset_id, filename, "csv", user)
        
        return Response(
            content=csv_bytes,
            media_type="text/csv",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Length": str(len(csv_bytes))
            },
        )
    except Exception as e:
        logger.error(f"CSV export failed for dataset {dataset_id}: {e}")
        raise HTTPException(500, f"Failed to export CSV: {str(e)}")


@router.get("/{dataset_id}/xlsx")
async def export_xlsx(dataset_id: str, user: dict = Depends(get_current_user)):
    """Export the dataset as Excel XLSX."""
    ds = get_dataset_store().get(dataset_id)
    if not ds:
        raise HTTPException(404, "Dataset not found")

    try:
        df = ds["df"]
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name="Dataset")
        xlsx_bytes = buffer.getvalue()
        clean_name = _get_clean_dataset_name(ds['name'])
        filename = f"InsightIQ_Raw_Data_{clean_name}.xlsx"
        _log_report_export(dataset_id, filename, "xlsx", user)
        
        return Response(
            content=xlsx_bytes,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Length": str(len(xlsx_bytes))
            },
        )
    except Exception as e:
        logger.error(f"XLSX export failed for dataset {dataset_id}: {e}")
        raise HTTPException(500, f"Failed to export Excel: {str(e)}")

