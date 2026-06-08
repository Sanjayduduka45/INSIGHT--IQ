"""
InsightIQ — Gemini API Utilities

Abstracts generation calls and provides automatic fallback support
for both legacy google-generativeai and modern google-genai SDKs.
"""

from __future__ import annotations

import logging
import io
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

import concurrent.futures

# Global executor to prevent blocking the main thread on context exit when timeouts occur
_GEMINI_EXECUTOR = concurrent.futures.ThreadPoolExecutor(max_workers=10)

def generate_content_with_gemini(
    prompt: str,
    model_name: str,
    api_key: str,
    response_mime_type: str = "text/plain",
    temperature: float = 0.7
) -> str:
    """Generate content using Gemini API with a strict 5-second timeout."""
    future = _GEMINI_EXECUTOR.submit(
        _generate_content_raw,
        prompt,
        model_name,
        api_key,
        response_mime_type,
        temperature
    )
    try:
        return future.result(timeout=5.0)
    except concurrent.futures.TimeoutError:
        logger.error("Gemini API call timed out after 5.0 seconds.")
        raise RuntimeError("Gemini API call timed out.")

def _generate_content_raw(
    prompt: str,
    model_name: str,
    api_key: str,
    response_mime_type: str = "text/plain",
    temperature: float = 0.7
) -> str:
    """Generate content using Gemini API, automatically routing to the installed SDK.

    Supports both legacy google-generativeai and new google-genai libraries.
    """
    if not api_key:
        raise ValueError("Google API key must be configured to use Gemini.")

    # 1. Try modern google-genai library
    try:
        from google import genai
        from google.genai import types
        
        logger.info("Initializing modern google-genai client...")
        client = genai.Client(api_key=api_key)
        
        config = types.GenerateContentConfig(
            temperature=temperature
        )
        if response_mime_type == "application/json":
            config.response_mime_type = "application/json"
            
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=config
        )
        if response and response.text:
            return response.text.strip()
        raise ValueError("Empty response received from google-genai client.")
        
    except (ImportError, AttributeError, ValueError) as sdk_err:
        logger.info("google-genai import or execution failed: %s. Falling back to legacy google-generativeai...", sdk_err)

    # 2. Try legacy google-generativeai library
    try:
        import google.generativeai as genai
        
        logger.info("Configuring legacy google-generativeai client...")
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name)
        
        generation_config: Dict[str, Any] = {
            "temperature": temperature
        }
        if response_mime_type == "application/json":
            generation_config["response_mime_type"] = "application/json"
            
        response = model.generate_content(
            prompt,
            generation_config=generation_config
        )
        if response and response.text:
            return response.text.strip()
        raise ValueError("Empty response received from google-generativeai client.")
        
    except Exception as legacy_err:
        logger.error("Both modern and legacy Gemini SDK clients failed: %s", legacy_err, exc_info=True)
        raise RuntimeError(f"Gemini API request failed on all SDK interfaces: {legacy_err}")

