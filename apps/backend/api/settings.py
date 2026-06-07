"""
InsightIQ — Settings API

Provides infrastructure connection status and testing for administrators.
Never exposes raw secrets to the frontend.
"""

from __future__ import annotations

import logging
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from core.settings import get_settings
from core.security import require_admin

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/settings", tags=["settings"])


class ConnectionTestRequest(BaseModel):
    service: str


@router.get("/infrastructure")
async def get_infrastructure_status(user: dict = Depends(require_admin)) -> Dict[str, Any]:
    """Get high-level status of infrastructure components without exposing secrets."""
    settings = get_settings()

    return {
        "ai": {
            "provider": "Gemini",
            "connected": settings.has_gemini,
            "status": "Healthy" if settings.has_gemini else "Fallback/Not Configured",
        },
        "database": {
            "provider": "Supabase" if settings.has_supabase else "Local In-Memory",
            "connected": True,  # In-memory is always "connected" if supabase is not
            "status": "Healthy",
        },
        "storage": {
            "provider": "Supabase" if settings.has_supabase else "Local FileSystem",
            "connected": True,
            "status": "Healthy",
        },
    }


@router.post("/test-connection")
async def test_connection(
    req: ConnectionTestRequest, user: dict = Depends(require_admin)
) -> Dict[str, Any]:
    """Safely test connections to external services."""
    settings = get_settings()

    if req.service == "ai":
        if not settings.has_gemini:
            raise HTTPException(400, "Gemini API is not configured on the server.")
        try:
            # Simple test to check if the API key is valid
            from google import genai as google_genai

            client = google_genai.Client(api_key=settings.google_api_key)
            # Generate a minimal token to test connection quickly
            client.models.generate_content(model="gemini-2.0-flash", contents="Ping")
            return {"status": "success", "message": "Connection Successful"}
        except Exception as e:
            # We log the raw error for observability, but NEVER send it to the client
            error_msg = str(e)
            if settings.google_api_key and settings.google_api_key in error_msg:
                masked_key = (
                    f"{settings.google_api_key[:4]}***{settings.google_api_key[-4:]}"
                    if len(settings.google_api_key) > 8
                    else "***"
                )
                error_msg = error_msg.replace(settings.google_api_key, masked_key)
            logger.error("AI Connection Test Failed: %s", error_msg)
            return {"status": "error", "message": "Connection Failed"}

    elif req.service == "database" or req.service == "storage":
        if not settings.has_supabase:
            return {"status": "success", "message": "Using local in-memory/filesystem (Healthy)"}
        try:
            from supabase import create_client, Client

            supabase: Client = create_client(settings.supabase_url, settings.supabase_anon_key)
            # Test storage bucket or DB connection lightly
            supabase.storage.list_buckets()
            return {"status": "success", "message": "Connection Successful"}
        except Exception as e:
            error_msg = str(e)
            if settings.supabase_anon_key and settings.supabase_anon_key in error_msg:
                masked_key = (
                    f"{settings.supabase_anon_key[:4]}***{settings.supabase_anon_key[-4:]}"
                    if len(settings.supabase_anon_key) > 8
                    else "***"
                )
                error_msg = error_msg.replace(settings.supabase_anon_key, masked_key)
            if settings.supabase_url and settings.supabase_url in error_msg:
                error_msg = error_msg.replace(settings.supabase_url, "[MASKED_URL]")
            logger.error("Supabase Connection Test Failed for %s: %s", req.service, error_msg)
            return {"status": "error", "message": "Connection Failed"}

    else:
        raise HTTPException(400, "Unknown service")
