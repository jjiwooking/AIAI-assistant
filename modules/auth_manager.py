import os
import re

import streamlit as st
from supabase import create_client
from supabase.lib.client_options import ClientOptions

from modules.supabase_client import get_supabase


LOGIN_ID_PATTERN = re.compile(r"^[a-zA-Z0-9._-]{4,30}$")
INTERNAL_DOMAIN = "aiai.app"


def normalize_login_id(login_id):
    return login_id.strip().lower()


def login_id_to_email(login_id):
    return f"{normalize_login_id(login_id)}@{INTERNAL_DOMAIN}"


def get_auth_client():
    url = os.getenv("SUPABASE_URL") or st.secrets.get("SUPABASE_URL", "")
    key = (
        os.getenv("SUPABASE_PUBLISHABLE_KEY")
        or st.secrets.get("SUPABASE_PUBLISHABLE_KEY", "")
        or os.getenv("SUPABASE_ANON_KEY")
        or st.secrets.get("SUPABASE_ANON_KEY", "")
    )

    if not url or not key:
        raise RuntimeError(
            "Streamlit Secrets에 SUPABASE_URL과 "
            "SUPABASE_PUBLISHABLE_KEY를 등록해주세요."
        )

    return create_client(
        str(url).strip(),
        str(key).strip(),
        options=ClientOptions(auto_refresh_token=False, persist_session=False)
    )


def get_profile(auth_user_id):
    response = get_supabase().table("profiles").select(
        "auth_user_id,login_id,display_name,role"
    ).eq("auth_user_id", str(auth_user_id)).maybe_single().execute()

    return response.data or None


def register_user(login_id, password, password_confirm, display_name):
    login_id = normalize_login_id(login_id)
    display_name = display_name.strip()

    if not LOGIN_ID_PATTERN.fullmatch(login_id):
        return False, "ID는 영문, 숫자, ., _, - 만 사용해 4~30자로 입력해주세요.", None

    if len(password) < 8:
        return False, "PASSWORD는 8자 이상으로 입력해주세요.", None

    if password != password_confirm:
        return False, "PASSWORD 확인이 일치하지 않습니다.", None

    if not display_name:
        return False, "이름을 입력해주세요.", None

    auth = get_auth_client()

    try:
        response = auth.auth.sign_up({
            "email": login_id_to_email(login_id),
            "password": password,
            "options": {
                "data": {
                    "login_id": login_id,
                    "display_name": display_name,
                }
            }
        })
    except Exception as error:
        message = str(error)
        if "already registered" in message.lower():
            return False, "이미 사용 중인 ID입니다.", None
        return False, f"회원가입 중 오류가 발생했습니다: {message}", None

    if not response.user:
        return False, "회원가입에 실패했습니다.", None

    if response.session is None:
        return False, (
            "Supabase의 Confirm email이 켜져 있습니다. "
            "Authentication → Providers → Email에서 Confirm email을 OFF로 바꿔주세요."
        ), None

    try:
        get_supabase().table("profiles").insert({
            "auth_user_id": str(response.user.id),
            "login_id": login_id,
            "display_name": display_name,
            "role": "user",
        }).execute()
    except Exception as error:
        return False, f"프로필 생성 중 오류가 발생했습니다: {error}", None

    profile = get_profile(response.user.id)
    session = response.session

    return True, "회원가입이 완료되었습니다.", {
        "user_id": str(response.user.id),
        "profile": profile,
        "access_token": session.access_token,
        "refresh_token": session.refresh_token,
    }


def login_user(login_id, password):
    login_id = normalize_login_id(login_id)

    if not login_id or not password:
        return False, "ID와 PASSWORD를 입력해주세요.", None

    auth = get_auth_client()

    try:
        response = auth.auth.sign_in_with_password({
            "email": login_id_to_email(login_id),
            "password": password,
        })
    except Exception:
        return False, "ID 또는 PASSWORD를 확인해주세요.", None

    if not response.user or not response.session:
        return False, "로그인에 실패했습니다.", None

    profile = get_profile(response.user.id)

    if not profile:
        return False, "사용자 프로필을 찾을 수 없습니다. 관리자에게 문의해주세요.", None

    return True, "로그인되었습니다.", {
        "user_id": str(response.user.id),
        "profile": profile,
        "access_token": response.session.access_token,
        "refresh_token": response.session.refresh_token,
    }


def restore_user(access_token, refresh_token):
    if not access_token or not refresh_token:
        return None

    try:
        auth = get_auth_client()
        response = auth.auth.set_session(access_token, refresh_token)
        user_response = auth.auth.get_user(response.session.access_token)

        if not user_response.user:
            return None

        profile = get_profile(user_response.user.id)
        if not profile:
            return None

        return {
            "user_id": str(user_response.user.id),
            "profile": profile,
            "access_token": response.session.access_token,
            "refresh_token": response.session.refresh_token,
        }
    except Exception:
        return None


def logout_user(access_token="", refresh_token=""):
    try:
        if access_token and refresh_token:
            auth = get_auth_client()
            auth.auth.set_session(access_token, refresh_token)
            auth.auth.sign_out()
    except Exception:
        pass
