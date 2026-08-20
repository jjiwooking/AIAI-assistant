import os
import re

import streamlit as st
from supabase import create_client

from modules.supabase_client import get_supabase


LOGIN_ID_PATTERN = re.compile(r"^[a-zA-Z0-9._-]{4,30}$")
INTERNAL_EMAIL_DOMAIN = "aiai.app"


def normalize_login_id(login_id):
    return (login_id or "").strip().lower()


def login_id_to_email(login_id):
    return f"{normalize_login_id(login_id)}@{INTERNAL_EMAIL_DOMAIN}"


def _secret(name, default=""):
    return os.getenv(name) or st.secrets.get(name, default)


def get_auth_client():
    url = str(_secret("SUPABASE_URL")).strip()
    key = str(
        _secret("SUPABASE_PUBLISHABLE_KEY")
        or _secret("SUPABASE_ANON_KEY")
    ).strip()

    if not url or not key:
        raise RuntimeError(
            "Streamlit Secrets에 SUPABASE_URL과 "
            "SUPABASE_PUBLISHABLE_KEY를 등록해주세요."
        )

    return create_client(url, key)


def get_profile(auth_user_id):
    response = (
        get_supabase()
        .table("profiles")
        .select("auth_user_id,login_id,display_name,role")
        .eq("auth_user_id", str(auth_user_id))
        .execute()
    )

    rows = response.data or []
    return rows[0] if rows else None


def _get_profile_by_login_id(login_id):
    response = (
        get_supabase()
        .table("profiles")
        .select("auth_user_id,login_id,display_name,role")
        .eq("login_id", normalize_login_id(login_id))
        .execute()
    )

    rows = response.data or []
    return rows[0] if rows else None


def _ensure_profile(auth_user_id, login_id, display_name):
    profile = get_profile(auth_user_id)

    if profile:
        return profile

    get_supabase().table("profiles").upsert(
        {
            "auth_user_id": str(auth_user_id),
            "login_id": normalize_login_id(login_id),
            "display_name": display_name.strip(),
            "role": "user",
        },
        on_conflict="auth_user_id",
    ).execute()

    return get_profile(auth_user_id)


def register_user(login_id, password, password_confirm, display_name):
    login_id = normalize_login_id(login_id)
    display_name = (display_name or "").strip()

    if not LOGIN_ID_PATTERN.fullmatch(login_id):
        return (
            False,
            "ID는 영문, 숫자, ., _, -만 사용하여 4~30자로 입력해주세요.",
            None,
        )

    if len(password or "") < 8:
        return False, "PASSWORD는 8자 이상으로 입력해주세요.", None

    if password != password_confirm:
        return False, "PASSWORD 확인이 일치하지 않습니다.", None

    if not display_name:
        return False, "이름을 입력해주세요.", None

    if _get_profile_by_login_id(login_id):
        return False, "이미 사용 중인 ID입니다.", None

    try:
        admin_client = get_supabase()

        created = admin_client.auth.admin.create_user(
            {
                "email": login_id_to_email(login_id),
                "password": password,
                "email_confirm": True,
                "user_metadata": {
                    "login_id": login_id,
                    "display_name": display_name,
                },
            }
        )

        if not created.user:
            return False, "회원가입에 실패했습니다.", None

        profile = _ensure_profile(
            created.user.id,
            login_id,
            display_name,
        )

        signed_in = get_auth_client().auth.sign_in_with_password(
            {
                "email": login_id_to_email(login_id),
                "password": password,
            }
        )

        if not signed_in.user or not signed_in.session:
            return (
                False,
                "회원가입은 완료됐지만 자동 로그인에 실패했습니다. "
                "로그인 화면에서 다시 로그인해주세요.",
                None,
            )

        return (
            True,
            "회원가입이 완료되었습니다.",
            {
                "user_id": str(signed_in.user.id),
                "profile": profile,
                "access_token": signed_in.session.access_token,
                "refresh_token": signed_in.session.refresh_token,
            },
        )

    except Exception as error:
        message = str(error)
        lowered = message.lower()

        if (
            "already registered" in lowered
            or "already been registered" in lowered
            or "user already exists" in lowered
        ):
            return False, "이미 사용 중인 ID입니다.", None

        return False, f"회원가입 오류: {message}", None


def login_user(login_id, password):
    login_id = normalize_login_id(login_id)

    if not login_id or not password:
        return False, "ID와 PASSWORD를 입력해주세요.", None

    try:
        response = get_auth_client().auth.sign_in_with_password(
            {
                "email": login_id_to_email(login_id),
                "password": password,
            }
        )

    except Exception as error:
        message = str(error)
        lowered = message.lower()

        if "email not confirmed" in lowered or "email_not_confirmed" in lowered:
            return (
                False,
                "계정 이메일 확인이 완료되지 않았습니다. 관리자에게 문의해주세요.",
                None,
            )

        if (
            "invalid login credentials" in lowered
            or "invalid_credentials" in lowered
        ):
            return False, "ID 또는 PASSWORD가 올바르지 않습니다.", None

        return False, f"로그인 오류: {message}", None

    if not response.user or not response.session:
        return False, "로그인에 실패했습니다.", None

    profile = get_profile(response.user.id)

    if not profile:
        metadata = response.user.user_metadata or {}
        display_name = metadata.get("display_name") or login_id

        try:
            profile = _ensure_profile(
                response.user.id,
                login_id,
                display_name,
            )
        except Exception as error:
            return (
                False,
                f"사용자 프로필 생성 오류: {error}",
                None,
            )

    return (
        True,
        "로그인되었습니다.",
        {
            "user_id": str(response.user.id),
            "profile": profile,
            "access_token": response.session.access_token,
            "refresh_token": response.session.refresh_token,
        },
    )


def restore_user(access_token, refresh_token):
    if not access_token or not refresh_token:
        return None

    try:
        client = get_auth_client()
        response = client.auth.set_session(access_token, refresh_token)

        if not response.user or not response.session:
            return None

        profile = get_profile(response.user.id)

        if not profile:
            return None

        return {
            "user_id": str(response.user.id),
            "profile": profile,
            "access_token": response.session.access_token,
            "refresh_token": response.session.refresh_token,
        }

    except Exception:
        return None


def logout_user(access_token="", refresh_token=""):
    try:
        client = get_auth_client()

        if access_token and refresh_token:
            client.auth.set_session(access_token, refresh_token)

        client.auth.sign_out()

    except Exception:
        pass
