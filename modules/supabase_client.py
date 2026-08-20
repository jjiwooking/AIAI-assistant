import os
import streamlit as st

@st.cache_resource
def get_supabase():
    from supabase import create_client

    url = os.getenv("SUPABASE_URL") or st.secrets.get("SUPABASE_URL", "")
    key = os.getenv("SUPABASE_SECRET_KEY") or st.secrets.get("SUPABASE_SECRET_KEY", "")

    if not url or not key:
        raise RuntimeError(
            "Supabase 설정이 없습니다. Streamlit Secrets에 "
            "SUPABASE_URL과 SUPABASE_SECRET_KEY를 등록해주세요."
        )

    return create_client(str(url).strip(), str(key).strip())
