import hashlib
import json
import mimetypes
import re
import uuid
from modules.supabase_client import get_supabase

BUCKET_NAME = "aiai-media"

def _safe_json(value):
    return json.loads(json.dumps(value, ensure_ascii=False, default=str))

def _user_folder(user_id):
    return hashlib.sha256(user_id.encode("utf-8")).hexdigest()[:20]

def _safe_filename(filename):
    filename = re.sub(r"[^A-Za-z0-9._-]+", "_", filename or "file")
    return filename[:120] or "file"

def _upload_bytes(user_id, folder, filename, data, content_type=None):
    if not data:
        return None

    safe_name = _safe_filename(filename)
    path = f"{_user_folder(user_id)}/{folder}/{uuid.uuid4().hex}_{safe_name}"
    mime = content_type or mimetypes.guess_type(safe_name)[0] or "application/octet-stream"

    get_supabase().storage.from_(BUCKET_NAME).upload(
        path=path,
        file=data,
        file_options={"content-type": mime, "upsert": "false"}
    )

    return path

def save_media_project(user_id, analysis, analysis_type="회의록", uploaded_file=None):
    media_path = None
    original_name = None

    if uploaded_file is not None:
        original_name = uploaded_file.name
        media_path = _upload_bytes(
            user_id,
            "original",
            uploaded_file.name,
            uploaded_file.getvalue(),
            getattr(uploaded_file, "type", None)
        )

    payload = {
        "user_id": user_id,
        "title": analysis.get("title") or "회의·발표 분석",
        "analysis_type": analysis_type,
        "original_file_name": original_name,
        "media_path": media_path,
        "transcript": analysis.get("transcript") or "",
        "analysis": _safe_json(analysis)
    }

    response = get_supabase().table("media_projects").insert(
        payload
    ).select("id").execute()

    if not response.data:
        raise RuntimeError("분석 결과 저장에 실패했습니다.")

    return response.data[0]["id"]

def update_media_project(user_id, project_id, analysis):
    if not project_id:
        return

    get_supabase().table("media_projects").update({
        "title": analysis.get("title") or "회의·발표 분석",
        "transcript": analysis.get("transcript") or "",
        "analysis": _safe_json(analysis),
        "updated_at": "now()"
    }).eq("id", project_id).eq("user_id", user_id).execute()

def list_media_projects(user_id, limit=30):
    response = get_supabase().table("media_projects").select(
        "id,title,analysis_type,original_file_name,created_at,updated_at"
    ).eq("user_id", user_id).order("created_at", desc=True).limit(limit).execute()

    return response.data or []

def load_media_project(user_id, project_id):
    response = get_supabase().table("media_projects").select(
        "*"
    ).eq("id", project_id).eq("user_id", user_id).maybe_single().execute()

    return response.data

def save_generated_files(user_id, project_id, ppt_bytes=None, pdf_bytes=None):
    if not project_id:
        return

    updates = {}

    if ppt_bytes:
        updates["ppt_path"] = _upload_bytes(
            user_id,
            f"generated/{project_id}",
            "AIAI_meeting_report.pptx",
            ppt_bytes,
            "application/vnd.openxmlformats-officedocument.presentationml.presentation"
        )

    if pdf_bytes:
        updates["pdf_path"] = _upload_bytes(
            user_id,
            f"generated/{project_id}",
            "AIAI_meeting_report.pdf",
            pdf_bytes,
            "application/pdf"
        )

    if updates:
        get_supabase().table("media_projects").update(
            updates
        ).eq("id", project_id).eq("user_id", user_id).execute()

def download_saved_file(path):
    if not path:
        return None

    return get_supabase().storage.from_(BUCKET_NAME).download(path)
