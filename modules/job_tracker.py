from modules.supabase_client import get_supabase

def add_job(user_id, company, position, status="지원 예정", deadline="", notes=""):
    if not company.strip() or not position.strip():
        return "⚠️ 기업명과 직무를 입력해주세요."

    get_supabase().table("jobs").insert({
        "user_id": user_id,
        "company": company.strip(),
        "position": position.strip(),
        "status": status,
        "deadline": deadline.strip() or None,
        "notes": notes.strip() or None
    }).execute()

    return f"✅ {company} - {position} 추가 완료!"

def get_jobs(user_id):
    response = get_supabase().table("jobs").select(
        "id,company,position,status,deadline,notes"
    ).eq("user_id", user_id).order("created_at", desc=True).execute()

    return [
        (
            row["id"],
            row["company"],
            row["position"],
            row.get("status") or "지원 예정",
            row.get("deadline") or "",
            row.get("notes") or ""
        )
        for row in (response.data or [])
    ]

def update_job_status(user_id, job_id, status):
    response = get_supabase().table("jobs").update({
        "status": status
    }).eq("id", int(job_id)).eq("user_id", user_id).select("id").execute()

    if not response.data:
        return "⚠️ 해당 채용 정보를 찾을 수 없습니다."

    return f"✅ ID {int(job_id)} 상태를 '{status}'로 변경!"
