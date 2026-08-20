from modules.supabase_client import get_supabase

def get_tabs():
    response = get_supabase().table("app_tabs").select(
        "tab_key,label,icon,sort_order,is_visible"
    ).order("sort_order").execute()

    return response.data or []

def update_tab(tab_key, label, icon, sort_order, is_visible):
    get_supabase().table("app_tabs").update({
        "label": label.strip(),
        "icon": icon.strip(),
        "sort_order": int(sort_order),
        "is_visible": bool(is_visible)
    }).eq("tab_key", tab_key).execute()

def get_texts():
    response = get_supabase().table("app_texts").select(
        "text_key,category,label,value"
    ).order("category").execute()

    return response.data or []

def update_text(text_key, value):
    get_supabase().table("app_texts").update({
        "value": value
    }).eq("text_key", text_key).execute()

def get_text(text_key, default=""):
    response = get_supabase().table("app_texts").select(
        "value"
    ).eq("text_key", text_key).maybe_single().execute()

    if not response.data:
        return default

    return response.data.get("value") or default
