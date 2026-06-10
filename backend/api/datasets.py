"""
InsightIQ — Dataset Upload & Management API

Handles file upload (CSV, Excel, Parquet, JSON), schema detection,
domain classification, and dataset management.
"""

from __future__ import annotations

import io
import logging
import uuid
from dataclasses import asdict
from typing import Any, Dict, Optional

import os
import pandas as pd
from fastapi import APIRouter, File, HTTPException, UploadFile, Depends

from intelligence.schema_detector import detect_schema
from intelligence.domain_classifier import classify_domain
from intelligence.quality_scorer import score_quality
from intelligence.kpi_generator import generate_kpis
from core.security import get_current_user
from core.settings import get_settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/datasets", tags=["datasets"])

class UploadDiagnosticsError(Exception):
    def __init__(self, message: str, stage: str, encoding: str = "N/A", parser: str = "N/A"):
        super().__init__(message)
        self.message = message
        self.stage = stage
        self.encoding = encoding
        self.parser = parser

# In-memory dataset store (for demo; production uses Supabase)
_datasets: Dict[str, Dict[str, Any]] = {}


def _get_supabase_client(user: dict):
    """Create an authorized Supabase client for the current user."""
    settings = get_settings()
    if not settings.has_supabase or not user or user.get("role") == "guest":
        return None
    try:
        from supabase import create_client, Client
        client: Client = create_client(settings.supabase_url, settings.supabase_anon_key)
        if user.get("token"):
            client.postgrest.auth(user["token"])
        return client
    except Exception as e:
        logger.warning(f"Failed to initialize Supabase client: {e}")
        return None


def _ensure_dataset_loaded(dataset_id: str, user: dict) -> Optional[Dict[str, Any]]:
    """Ensure a dataset is loaded into memory, checking local cache & DB if needed."""
    # 1. Check in-memory cache
    if dataset_id in _datasets:
        ds = _datasets[dataset_id]
        if ds.get("user_id") == user.get("id") or not ds.get("user_id"):
            return ds

    # 2. Check local parquet cache
    settings = get_settings()
    parquet_path = os.path.join(settings.upload_dir, f"{dataset_id}.parquet")
    if os.path.exists(parquet_path):
        try:
            logger.info(f"Cache miss: Reloading dataset {dataset_id} from {parquet_path}")
            df = pd.read_parquet(parquet_path)
            
            # Load metadata from JSON cache if available
            filename = f"{dataset_id}.csv"
            domain_name = "Generic"
            context = None
            import json
            meta_path = os.path.join(settings.upload_dir, f"{dataset_id}.json")
            if os.path.exists(meta_path):
                try:
                    with open(meta_path, "r") as f:
                        meta_data = json.load(f)
                        filename = meta_data.get("name", filename)
                        domain_name = meta_data.get("domain", domain_name)
                        context = meta_data.get("context", None)
                except Exception as meta_err:
                    logger.warning(f"Failed to read metadata JSON cache: {meta_err}")
            
            # Check DB permission first if Supabase is active
            supabase = _get_supabase_client(user)
            if supabase:
                try:
                    res = supabase.table("datasets").select("*").eq("id", dataset_id).execute()
                    if not res.data:
                        logger.warning(f"Dataset {dataset_id} metadata not found in Supabase or unauthorized.")
                        return None
                    db_metadata = res.data[0]
                    filename = db_metadata.get("name", filename)
                    domain_name = db_metadata.get("domain", domain_name)
                except Exception as db_err:
                    logger.error(f"Error querying dataset metadata from Supabase: {db_err}")

            # Re-run lightweight intelligence pipeline
            schema = detect_schema(df)
            domain_result = classify_domain(df, schema)
            quality = score_quality(df, schema)
            kpis = generate_kpis(df, schema, domain_result.domain)

            # Re-cache in memory
            _datasets[dataset_id] = {
                "id": dataset_id,
                "name": filename,
                "df": df,
                "schema": schema,
                "domain": domain_result,
                "quality": quality,
                "kpis": kpis,
                "user_id": user.get("id"),
                "context": context,
            }
            return _datasets[dataset_id]
        except Exception as e:
            logger.error(f"Failed to reload dataset {dataset_id} from local cache: {e}")
            return None

    return None


class DatasetStoreProxy:
    def get(self, dataset_id: str) -> Optional[Dict[str, Any]]:
        from core.security import current_user_var
        user = current_user_var.get()
        if not user:
            user = {"id": "dev-user", "role": "admin"}
        return _ensure_dataset_loaded(dataset_id, user)

    def __getitem__(self, dataset_id: str) -> Dict[str, Any]:
        val = self.get(dataset_id)
        if val is None:
            raise KeyError(dataset_id)
        return val

    def __contains__(self, dataset_id: str) -> bool:
        return self.get(dataset_id) is not None

    def values(self):
        return _datasets.values()


_datasets_proxy = DatasetStoreProxy()


@router.post("/upload")
async def upload_dataset(
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user),
):
    """Upload a dataset file and perform automatic analysis with diagnostics."""
    import time
    start_time = time.time()
    filename = file.filename or "unknown"
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    content_type = file.content_type or "application/octet-stream"

    stage = "initialization"
    parser_selected = "unknown"
    detected_encoding = "N/A"
    size_bytes = 0

    try:
        if not file.filename:
            raise UploadDiagnosticsError("No file provided", stage="initialization")

        if ext not in ("csv", "xlsx", "xls", "parquet", "json", "tsv", "zip"):
            raise UploadDiagnosticsError(
                "Unable to process this file.\n\nPossible reasons:\n• Unsupported format\n\nPlease try another file.",
                stage="initialization"
            )

        # Determine size by seeking
        try:
            if hasattr(file, "size") and file.size is not None:
                size_bytes = file.size
            else:
                file.file.seek(0, 2)
                size_bytes = file.file.tell()
                file.file.seek(0)
        except Exception as seek_err:
            logger.warning(f"Failed to determine size on uploaded file: {seek_err}")
            size_bytes = 0

        # Check upload limit
        settings = get_settings()
        max_size_bytes = settings.max_file_size_mb * 1024 * 1024
        if size_bytes > max_size_bytes:
            raise UploadDiagnosticsError(
                "Dataset exceeds upload limit.",
                stage="size_check"
            )

        stage = "reading"
        try:
            # If the file is extremely large (> 50MB), sample the first 20MB for analysis
            if size_bytes > 50 * 1024 * 1024 and ext in ("csv", "tsv", "json"):
                logger.info(f"Large text file detected ({size_bytes / (1024*1024):.2f} MB). Reading first 20MB sample.")
                contents = await file.read(20 * 1024 * 1024)
                # Drain the rest of the stream
                while await file.read(1024 * 1024):
                    pass
            else:
                contents = await file.read()
        except Exception as read_err:
            raise UploadDiagnosticsError(f"Failed to read file contents: {str(read_err)}", stage="reading")

        stage = "parsing"
        df, detected_encoding, parser_selected = _read_file(contents, ext, filename)

        stage = "validation"
        if df.empty or len(df.columns) == 0:
            raise UploadDiagnosticsError("No readable columns found.", stage="validation", encoding=detected_encoding, parser=parser_selected)

        # Limit rows for demo analysis to prevent server freezing
        if len(df) > 100_000:
            df = df.head(100_000)

        stage = "intelligence"
        # Run intelligence pipeline
        schema = detect_schema(df)
        domain_result = classify_domain(df, schema)
        quality = score_quality(df, schema)
        kpis = generate_kpis(df, schema, domain_result.domain)

        processing_time_ms = int((time.time() - start_time) * 1000)

        # Store dataset
        dataset_id = str(uuid.uuid4())[:8]

        # Save to local filesystem parquet cache
        try:
            os.makedirs(settings.upload_dir, exist_ok=True)
            parquet_path = os.path.join(settings.upload_dir, f"{dataset_id}.parquet")
            df.to_parquet(parquet_path, index=False)
            logger.info(f"Saved dataset DataFrame locally to {parquet_path}")
            
            # Also save JSON metadata cache locally
            import json
            meta_path = os.path.join(settings.upload_dir, f"{dataset_id}.json")
            with open(meta_path, "w") as f:
                json.dump({
                    "id": dataset_id,
                    "user_id": user.get("id"),
                    "name": filename,
                    "domain": domain_result.domain
                }, f)
            logger.info(f"Saved dataset metadata locally to {meta_path}")
        except Exception as fs_err:
            logger.error(f"Failed to save parquet or metadata cache locally: {fs_err}")

        # Store metadata in Supabase if authenticated
        supabase = _get_supabase_client(user)
        if supabase:
            try:
                metadata = {
                    "id": dataset_id,
                    "user_id": user.get("id"),
                    "name": filename,
                    "row_count": len(df),
                    "column_count": len(df.columns),
                    "domain": domain_result.domain,
                }
                supabase.table("datasets").insert(metadata).execute()
                logger.info(f"Successfully inserted dataset {dataset_id} metadata into Supabase.")
            except Exception as db_err:
                logger.error(f"Failed to save dataset metadata to Supabase: {db_err}")

        _datasets[dataset_id] = {
            "id": dataset_id,
            "name": filename,
            "df": df,
            "schema": schema,
            "domain": domain_result,
            "quality": quality,
            "kpis": kpis,
            "user_id": user.get("id"),
        }

        # Success diagnostics
        diagnostics = {
            "filename": filename,
            "extension": ext,
            "mime_type": content_type,
            "file_size_bytes": size_bytes,
            "encoding": detected_encoding,
            "parser": parser_selected,
            "rows": len(df),
            "columns": len(df.columns),
            "processing_time_ms": processing_time_ms,
            "failure_stage": None,
        }
        
        # Log successful upload diagnostics
        logger.info(f"Upload Success Diagnostics: {diagnostics}")

        return {
            "dataset_id": dataset_id,
            "name": filename,
            "rows": schema.row_count,
            "columns": schema.column_count,
            "memory_mb": round(schema.memory_mb, 2),
            "domain": {
                "name": domain_result.domain,
                "confidence": domain_result.confidence,
                "evidence": domain_result.evidence,
            },
            "quality": {
                "overall_score": quality.overall_score,
                "grade": quality.grade,
                "completeness": quality.completeness,
                "uniqueness": quality.uniqueness,
                "consistency": quality.consistency,
                "validity": quality.validity,
                "issue_count": len(quality.issues),
            },
            "schema": {
                "numeric_columns": schema.numeric_columns,
                "categorical_columns": schema.categorical_columns,
                "date_columns": schema.date_columns,
                "text_columns": schema.text_columns,
                "id_columns": schema.id_columns,
                "primary_key": schema.primary_key,
            },
            "kpi_count": len(kpis),
            "diagnostics": diagnostics,
        }

    except Exception as e:
        # Determine error details
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        if isinstance(e, UploadDiagnosticsError):
            err_msg = e.message
            err_stage = e.stage
            err_encoding = e.encoding
            err_parser = e.parser
        else:
            err_msg = str(e)
            err_stage = stage
            err_encoding = detected_encoding
            err_parser = parser_selected

        diagnostics = {
            "filename": filename,
            "extension": ext,
            "mime_type": content_type,
            "file_size_bytes": size_bytes,
            "encoding": err_encoding,
            "parser": err_parser,
            "rows": 0,
            "columns": 0,
            "processing_time_ms": processing_time_ms,
            "failure_stage": err_stage,
        }

        # Log failed upload diagnostics
        logger.error(f"Upload Failure Diagnostics: {diagnostics} | Error: {err_msg}")

        raise HTTPException(
            status_code=400,
            detail={
                "message": err_msg,
                "diagnostics": diagnostics
            }
        )


@router.get("/list")
async def list_datasets(user: dict = Depends(get_current_user)):
    """List all uploaded datasets."""
    supabase = _get_supabase_client(user)
    if supabase:
        try:
            res = supabase.table("datasets").select("*").eq("user_id", user.get("id")).execute()
            if res.data:
                return [
                    {
                        "id": d["id"],
                        "name": d["name"],
                        "rows": d["row_count"],
                        "columns": d["column_count"],
                        "domain": d["domain"],
                    }
                    for d in res.data
                ]
        except Exception as e:
            logger.error(f"Failed to list datasets from Supabase: {e}")

    # Fallback/Guest listing
    return [
        {
            "id": d["id"],
            "name": d["name"],
            "rows": d["schema"].row_count,
            "columns": d["df"].shape[1],
            "domain": d["domain"].domain,
        }
        for d in _datasets.values()
        if d.get("user_id") == user.get("id") or not d.get("user_id")
    ]


@router.get("/{dataset_id}")
async def get_dataset(dataset_id: str, user: dict = Depends(get_current_user)):
    """Get dataset metadata."""
    ds = _ensure_dataset_loaded(dataset_id, user)
    if not ds:
        raise HTTPException(404, "Dataset not found")

    return {
        "id": ds["id"],
        "name": ds["name"],
        "rows": ds["schema"].row_count,
        "columns": ds["schema"].column_count,
        "domain": asdict(ds["domain"]),
        "quality": {
            "overall_score": ds["quality"].overall_score,
            "grade": ds["quality"].grade,
            "summary": ds["quality"].summary,
            "issues": [asdict(i) for i in ds["quality"].issues[:10]],
        },
        "schema": {
            "columns": [
                {
                    "name": c.name,
                    "type": c.semantic_type,
                    "role": c.role,
                    "missing_pct": c.missing_pct,
                    "unique_count": c.unique_count,
                }
                for c in ds["schema"].columns
            ],
        },
        "context": ds.get("context", None),
    }


from pydantic import BaseModel

class DatasetContextUpdate(BaseModel):
    business_problem: str
    analysis_goal: str
    success_metric: str

@router.post("/{dataset_id}/context")
async def update_dataset_context(
    dataset_id: str,
    payload: DatasetContextUpdate,
    user: dict = Depends(get_current_user),
):
    """Update active business context for a dataset."""
    ds = _ensure_dataset_loaded(dataset_id, user)
    if not ds:
        raise HTTPException(404, "Dataset not found")

    import json
    context_data = payload.model_dump()
    ds["context"] = context_data

    # Save to local JSON metadata cache
    try:
        settings = get_settings()
        meta_path = os.path.join(settings.upload_dir, f"{dataset_id}.json")
        meta_data = {}
        if os.path.exists(meta_path):
            with open(meta_path, "r") as f:
                meta_data = json.load(f)
        meta_data["context"] = context_data
        with open(meta_path, "w") as f:
            json.dump(meta_data, f)
        logger.info(f"Successfully saved context for dataset {dataset_id} in JSON cache.")
    except Exception as fs_err:
        logger.error(f"Failed to update dataset context JSON cache: {fs_err}")

    return {"status": "success", "context": ds["context"]}



@router.get("/{dataset_id}/preview")
async def preview_dataset(dataset_id: str, rows: int = 100, user: dict = Depends(get_current_user)):
    """Preview dataset rows."""
    ds = _ensure_dataset_loaded(dataset_id, user)
    if not ds:
        raise HTTPException(404, "Dataset not found")

    df: pd.DataFrame = ds["df"]
    preview = df.head(min(rows, 500))

    return {
        "columns": list(preview.columns),
        "data": preview.fillna("").to_dict(orient="records"),
        "total_rows": len(df),
        "showing": len(preview),
    }


@router.delete("/{dataset_id}")
async def delete_dataset(dataset_id: str, user: dict = Depends(get_current_user)):
    """Delete a dataset."""
    ds = _ensure_dataset_loaded(dataset_id, user)
    if not ds:
        raise HTTPException(404, "Dataset not found")

    supabase = _get_supabase_client(user)
    if supabase:
        try:
            supabase.table("datasets").delete().eq("id", dataset_id).execute()
            logger.info(f"Deleted dataset {dataset_id} metadata from Supabase.")
        except Exception as db_err:
            logger.error(f"Failed to delete dataset {dataset_id} from Supabase: {db_err}")

    # Remove local parquet and JSON cache files
    try:
        settings = get_settings()
        parquet_path = os.path.join(settings.upload_dir, f"{dataset_id}.parquet")
        if os.path.exists(parquet_path):
            os.remove(parquet_path)
            logger.info(f"Deleted local parquet cache file {parquet_path}")
        meta_path = os.path.join(settings.upload_dir, f"{dataset_id}.json")
        if os.path.exists(meta_path):
            os.remove(meta_path)
            logger.info(f"Deleted local metadata cache file {meta_path}")
    except Exception as fs_err:
        logger.error(f"Failed to delete local cache files: {fs_err}")

    if dataset_id in _datasets:
        del _datasets[dataset_id]

    return {"status": "deleted"}


def get_dataset_store():
    """Get the dataset store (used by other API modules)."""
    return _datasets_proxy



def _read_file(contents: bytes, ext: str, filename: str) -> tuple[pd.DataFrame, str, str]:
    """Read file bytes into a DataFrame using magic bytes, returning (df, encoding, parser)."""
    if not contents:
        raise UploadDiagnosticsError("The uploaded file is empty.", stage="reading")

    # 1. Detect ZIP format or extension
    is_zip = False
    import zipfile
    if ext == "zip":
        is_zip = True
    elif contents.startswith(b"PK\x03\x04") and ext not in ("xlsx", "xlsm"):
        try:
            with zipfile.ZipFile(io.BytesIO(contents)) as z:
                if "[Content_Types].xml" not in z.namelist():
                    is_zip = True
        except Exception:
            pass

    buf = io.BytesIO(contents)

    if is_zip:
        try:
            with zipfile.ZipFile(buf) as z:
                valid_files = []
                for name in z.namelist():
                    if name.endswith("/") or name.startswith("__MACOSX") or "/." in name or name.split("/")[-1].startswith("."):
                        continue
                    sub_ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
                    if sub_ext in ("csv", "xlsx", "xls", "parquet", "json", "tsv"):
                        valid_files.append((name, sub_ext))
                
                if not valid_files:
                    raise UploadDiagnosticsError(
                        "The ZIP archive does not contain any supported tabular dataset files (CSV, Excel, TSV, JSON, Parquet).",
                        stage="parsing",
                        parser="zip_extractor"
                    )
                
                # Sort alphabetically to be deterministic
                valid_files.sort(key=lambda x: x[0])
                target_name, target_ext = valid_files[0]
                logger.info(f"Extracting '{target_name}' from uploaded ZIP archive.")
                with z.open(target_name) as f:
                    extracted_contents = f.read()
                
                # Recursively parse the extracted file
                return _read_file(extracted_contents, target_ext, target_name)
        except Exception as e:
            if isinstance(e, UploadDiagnosticsError):
                raise e
            raise UploadDiagnosticsError(f"Failed to read ZIP archive: {str(e)}", stage="parsing", parser="zip_extractor")

    # 2. Magic byte parsing & extension verification
    parser_selected = "unknown"
    if contents.startswith(b"PK\x03\x04"):
        parser_selected = "pandas_excel"
        if ext == "xls":
            raise UploadDiagnosticsError(
                "File extension: XLS. Parser expected: XLSX.",
                stage="parser_selection",
                parser="pandas_excel"
            )
    elif contents.startswith(b"\xd0\xcf\x11\xe0"):
        parser_selected = "pandas_excel"
        if ext == "xlsx":
            raise UploadDiagnosticsError(
                "File extension: XLSX. Parser expected: XLS.",
                stage="parser_selection",
                parser="pandas_excel"
            )
    elif contents.startswith(b"PAR1"):
        parser_selected = "pandas_parquet"
    elif ext in ("xlsx", "xls"):
        parser_selected = "pandas_excel"
    elif ext == "parquet":
        parser_selected = "pandas_parquet"
    elif ext == "json":
        parser_selected = "pandas_json"
    elif ext == "tsv":
        parser_selected = "pandas_tsv"
    elif ext == "csv":
        parser_selected = "pandas_csv"

    # Excel Parsing
    if parser_selected == "pandas_excel":
        try:
            df = pd.read_excel(buf)
            if df.empty or len(df.columns) == 0:
                raise UploadDiagnosticsError("No readable columns found.", stage="validation", encoding="binary", parser="pandas_excel")
            return _clean_and_convert_dtypes(df), "binary", "pandas_excel"
        except Exception as excel_err:
            if isinstance(excel_err, UploadDiagnosticsError):
                raise excel_err
            err_msg = str(excel_err).lower()
            if "password" in err_msg or "encrypted" in err_msg:
                raise UploadDiagnosticsError("The Excel file is password-protected or encrypted.", stage="parsing", encoding="binary", parser="pandas_excel")
            elif "bad zip file" in err_msg or "not a zip file" in err_msg:
                raise UploadDiagnosticsError("The file appears to be corrupted or is not a valid Excel spreadsheet.", stage="parsing", encoding="binary", parser="pandas_excel")
            else:
                raise UploadDiagnosticsError(f"Unable to read Excel workbook: {str(excel_err)}", stage="parsing", encoding="binary", parser="pandas_excel")

    # Parquet Parsing
    elif parser_selected == "pandas_parquet":
        try:
            df = pd.read_parquet(buf)
            if df.empty or len(df.columns) == 0:
                raise UploadDiagnosticsError("No readable columns found.", stage="validation", encoding="binary", parser="pandas_parquet")
            return _clean_and_convert_dtypes(df), "binary", "pandas_parquet"
        except Exception as e:
            if isinstance(e, UploadDiagnosticsError):
                raise e
            raise UploadDiagnosticsError("Failed to parse Parquet format. The file might be corrupted.", stage="parsing", encoding="binary", parser="pandas_parquet")

    # Text formats
    if parser_selected not in ("pandas_json", "pandas_csv", "pandas_tsv"):
        if ext in ("csv", "tsv", "json"):
            parser_selected = f"pandas_{ext}"
        else:
            raise UploadDiagnosticsError(f"Unsupported file format: {ext}", stage="parser_selection")

    # Multi-Encoding Fallback
    encoding_list = ["utf-8", "utf-8-sig", "cp1252", "latin1", "iso-8859-1", "utf-16"]
    
    detected_first = None
    try:
        import charset_normalizer
        detected = charset_normalizer.detect(contents)
        if detected and detected.get("encoding"):
            detected_first = detected["encoding"].lower().replace("_", "-")
    except Exception:
        pass

    cjk_and_utf = {"utf-8", "utf-8-sig", "utf-16", "utf-16-le", "utf-16-be", "gbk", "gb18030", "gb2312", "shift-jis", "shift_jis", "euc-jp", "euc-kr"}

    encodings_to_try = []
    # If the detected encoding is CJK or UTF, try it first
    if detected_first and detected_first in cjk_and_utf:
        encodings_to_try.append(detected_first)

    # Add standard encodings in order
    for enc in encoding_list:
        if enc not in encodings_to_try:
            encodings_to_try.append(enc)

    # Finally, if detected_first was not tried yet, append it as a last resort
    if detected_first and detected_first not in encodings_to_try:
        encodings_to_try.append(detected_first)

    decoded_str = None
    successful_encoding = None
    utf8_failed = False

    for enc in encodings_to_try:
        try:
            decoded_str = contents.decode(enc)
            successful_encoding = enc
            if enc not in ("utf-8", "utf-8-sig") and ("utf-8" in encodings_to_try or "utf-8-sig" in encodings_to_try):
                utf8_failed = True
            break
        except (UnicodeDecodeError, ValueError):
            if enc in ("utf-8", "utf-8-sig"):
                utf8_failed = True
            continue

    if decoded_str is None:
        raise UploadDiagnosticsError(
            message="Unicode decoding failed for all supported encodings. File contents appear to be malformed or binary.",
            stage="encoding_detection",
            parser=parser_selected
        )

    final_encoding_name = successful_encoding
    if utf8_failed and successful_encoding not in ("utf-8", "utf-8-sig"):
        final_encoding_name = f"{successful_encoding.upper()} (UTF-8 decoding failed)"

    # JSON Parsing
    if parser_selected == "pandas_json":
        try:
            df = pd.read_json(io.StringIO(decoded_str))
            if df.empty or len(df.columns) == 0:
                raise UploadDiagnosticsError("No readable columns found.", stage="validation", encoding=final_encoding_name, parser="pandas_json")
            return _clean_and_convert_dtypes(df), final_encoding_name, "pandas_json"
        except Exception as json_err:
            if isinstance(json_err, UploadDiagnosticsError):
                raise json_err
            raise UploadDiagnosticsError(f"Failed to parse JSON content: {str(json_err)}", stage="parsing", encoding=final_encoding_name, parser="pandas_json")

    # CSV/TSV Parsing
    try:
        first_line = decoded_str.split("\n", 1)[0]
        counts = {s: first_line.count(s) for s in (",", ";", "\t", "|")}
        sorted_seps = sorted(counts.keys(), key=lambda s: counts[s], reverse=True)
        default_sep = "\t" if parser_selected == "pandas_tsv" else ","
        seps_to_try = [s for s in sorted_seps if counts[s] > 0]
        if default_sep not in seps_to_try:
            seps_to_try.append(default_sep)
    except Exception:
        seps_to_try = ["\t", ",", ";", "|"] if parser_selected == "pandas_tsv" else [",", ";", "\t", "|"]

    last_error = None
    for sep in seps_to_try:
        try:
            df = pd.read_csv(
                io.StringIO(decoded_str), sep=sep, low_memory=False, on_bad_lines="error"
            )
            if df.empty or len(df.columns) == 0:
                raise UploadDiagnosticsError("No readable columns found.", stage="validation", encoding=final_encoding_name, parser=parser_selected)
            return _clean_and_convert_dtypes(df), final_encoding_name, parser_selected
        except Exception as e:
            if isinstance(e, UploadDiagnosticsError):
                raise e
            last_error = e
            continue

    # Try skipping bad lines to detect if it's a malformed rows issue
    for sep in seps_to_try:
        try:
            df = pd.read_csv(
                io.StringIO(decoded_str), sep=sep, low_memory=False, on_bad_lines="skip"
            )
            if not df.empty and len(df.columns) > 0:
                raise UploadDiagnosticsError(
                    "Dataset contains malformed rows.",
                    stage="parsing",
                    encoding=final_encoding_name,
                    parser=parser_selected
                )
        except Exception as sub_err:
            if isinstance(sub_err, UploadDiagnosticsError):
                raise sub_err
            continue

    raise UploadDiagnosticsError(
        message=f"Unable to parse text dataset: {str(last_error)}",
        stage="parsing",
        encoding=final_encoding_name,
        parser=parser_selected
    )


def _clean_and_convert_dtypes(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and convert object/string columns that should be numeric or datetime.
    - Standardizes currency, commas, percentages, and handles mixed numeric formats.
    - Converts columns to datetime if they match date-like string formats.
    """
    import numpy as np

    for col in df.columns:
        series = df[col]
        # Skip if already numeric or datetime
        if pd.api.types.is_numeric_dtype(series) or pd.api.types.is_datetime64_any_dtype(series):
            continue
            
        if pd.api.types.is_object_dtype(series) or pd.api.types.is_string_dtype(series):
            # Drop na to check actual values
            non_null = series.dropna()
            if non_null.empty:
                continue
                
            # Convert sample to string and check if it looks numeric
            sample = non_null.head(100).astype(str).str.strip()
            
            # Helper to clean string values
            def clean_numeric_str(val):
                if pd.isna(val) or not isinstance(val, str):
                    return val
                val_clean = val.strip()
                if not val_clean:
                    return np.nan
                
                # Check for accounting negative format: (123.45) -> -123.45
                is_negative = False
                if val_clean.startswith('(') and val_clean.endswith(')'):
                    val_clean = val_clean[1:-1].strip()
                    is_negative = True
                    
                # Remove currency symbols and formatting commas/spaces
                val_clean = val_clean.replace(',', '').replace(' ', '')
                for sym in ('$', '€', '£', '¥'):
                    val_clean = val_clean.replace(sym, '')
                    
                # Handle percentage signs
                is_pct = False
                if val_clean.endswith('%'):
                    val_clean = val_clean[:-1].strip()
                    is_pct = True
                    
                try:
                    num_val = float(val_clean)
                    if is_negative:
                        num_val = -num_val
                    if is_pct:
                        num_val = num_val / 100.0
                    return num_val
                except ValueError:
                    return val

            # Try to convert a sample first to see if it's mostly numeric
            cleaned_sample = sample.apply(clean_numeric_str)
            
            # Check how many sample elements successfully converted to numeric (float/int)
            is_numeric = cleaned_sample.apply(lambda x: isinstance(x, (int, float)) and not pd.isna(x))
            
            if is_numeric.mean() >= 0.8:
                # Apply cleaning to the entire column
                df[col] = series.apply(clean_numeric_str)
                df[col] = pd.to_numeric(df[col], errors='coerce')
                logger.info(f"Converted column '{col}' to numeric after cleaning.")
                continue
                
            # Check if it's a date-like column
            try:
                # Use pd.to_datetime with format='mixed' to be robust to mixed formats
                parsed_dates = pd.to_datetime(sample, errors='coerce', format='mixed')
                if (parsed_dates.notna().sum() / len(sample)) >= 0.8:
                    df[col] = pd.to_datetime(series, errors='coerce', format='mixed')
                    logger.info(f"Converted column '{col}' to datetime.")
            except Exception as e:
                logger.debug(f"Date conversion check failed for column '{col}': {e}")
                
    return df
