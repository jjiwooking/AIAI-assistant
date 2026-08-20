from modules.supabase_client import get_supabase

def add_todo(user_id, title, due_date="", priority="보통"):
    if not title.strip():
        return "⚠️ 할 일을 입력해주세요."

    get_supabase().table("todos").insert({
        "user_id": user_id,
        "title": title.strip(),
        "due_date": due_date.strip() or None,
        "priority": priority,
        "completed": False
    }).execute()

    return f"✅ '{title}' 추가 완료!"

def get_todos(user_id, show_completed=False):
    query = get_supabase().table("todos").select(
        "id,title,due_date,priority,completed"
    ).eq("user_id", user_id)

    if not show_completed:
        query = query.eq("completed", False)

    response = query.order("completed").order("created_at", desc=True).execute()

    return [
        (
            row["id"],
            row["title"],
            row.get("due_date") or "",
            row.get("priority") or "보통",
            1 if row.get("completed") else 0
        )
        for row in (response.data or [])
    ]

def complete_todo(user_id, todo_id):
    response = get_supabase().table("todos").update({
        "completed": True
    }).eq("id", int(todo_id)).eq("user_id", user_id).select("id").execute()

    if not response.data:
        return "⚠️ 해당 할 일을 찾을 수 없습니다."

    return f"✅ ID {int(todo_id)} 완료 처리!"

def delete_todo(user_id, todo_id):
    response = get_supabase().table("todos").delete().eq(
        "id", int(todo_id)
    ).eq("user_id", user_id).select("id").execute()

    if not response.data:
        return "⚠️ 해당 할 일을 찾을 수 없습니다."

    return f"🗑️ ID {int(todo_id)} 삭제 완료!"
