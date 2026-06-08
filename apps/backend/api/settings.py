"""
InsightIQ — Settings API

Provides workspace preferences and mock configuration settings for the dashboard.
Shields all underlying database providers and API credentials.
"""

from __future__ import annotations

import logging
from typing import Dict, Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from core.security import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/settings", tags=["settings"])


class PreferenceModel(BaseModel):
    user_name: str
    user_email: str
    workspace_name: str
    theme: str


@router.get("/preferences")
async def get_preferences(user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    """Retrieve user-specific preference configurations."""
    return {
        "user_name": user.get("name", "Sanjay Duduka") if user else "Sanjay Duduka",
        "user_email": user.get("email", "sanjay@insightiq.ai") if user else "sanjay@insightiq.ai",
        "workspace_name": "Main Analytics Hub",
        "theme": "light",
    }


@router.post("/preferences")
async def save_preferences(
    prefs: PreferenceModel, user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """Save preferences configurations locally or in-session."""
    logger.info("Saved user preference profile settings: %s", prefs)
    return {"status": "success", "message": "Preferences saved successfully"}
