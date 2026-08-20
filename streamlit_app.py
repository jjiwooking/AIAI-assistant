import html
import re

import pandas as pd
import streamlit as st
from google.genai import types

from modules.ai_client import get_ai_response
from modules.app_config import ensure_text_defaults, load_text_map, get_text_value
from modules.app_settings import get_tabs, update_tab, get_texts, update_text
from modules.auth_manager import login_user, register_user, restore_user, logout_user
from modules.media_report import analyze_media, rebuild_from_transcript, build_pptx, build_pdf
from modules.media_storage import (
    save_media_project, update_media_project, list_media_projects,
    load_media_project, save_generated_files
)
from modules.todo_manager import add_todo, get_todos, complete_todo, delete_todo


# =========================================================
# 기본 설정
# =========================================================
st.set_page_config(page_title="AIAI Assistant", page_icon="🤖", layout="wide")

ensure_text_defaults()
TEXT_MAP = load_text_map()


def t(key, default):
    return get_text_value(TEXT_MAP, key, default)


def clean_email_text(text):
    if not text:
        return ""
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = re.sub(r"\*(.*?)\*", r"\1", text)
    text = re.sub(r"^#{1,6}\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"^[-*_]{3,}\s*$", "", text, flags=re.MULTILINE)
    text = text.replace("`", "")
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def init_state():
    defaults = {
        "user_id": "",
        "user_profile": None,
        "auth_access_token": "",
        "auth_refresh_token": "",
        "media_project_id": None,
        "media_analysis": None,
        "media_transcript": "",
        "media_glossary": "Micron, APTD, TCB, RMS, Ejector, Flipper, Auto Tool Change, EFEM, BOC, FAC, T131",
        "media_ppt_bytes": None,
        "media_pdf_bytes": None,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def save_auth_session(auth_data):
    st.session_state.user_id = auth_data["user_id"]
    st.session_state.user_profile = auth_data["profile"]
    st.session_state.auth_access_token = auth_data["access_token"]
    st.session_state.auth_refresh_token = auth_data["refresh_token"]


def clear_auth_session():
    logout_user(
        st.session_state.get("auth_access_token", ""),
        st.session_state.get("auth_refresh_token", "")
    )
    st.session_state.user_id = ""
    st.session_state.user_profile = None
    st.session_state.auth_access_token = ""
    st.session_state.auth_refresh_token = ""
    st.session_state.media_project_id = None
    st.session_state.media_analysis = None
    st.session_state.media_transcript = ""
    st.session_state.media_ppt_bytes = None
    st.session_state.media_pdf_bytes = None


def restore_auth():
    if st.session_state.user_id:
        return

    auth_data = restore_user(
        st.session_state.get("auth_access_token", ""),
        st.session_state.get("auth_refresh_token", "")
    )

    if auth_data:
        save_auth_session(auth_data)


def render_auth():
    if st.session_state.user_id:
        return

    st.title(t("login_title", "🤖 나만의 AI 비서"))
    login_tab, signup_tab = st.tabs([
        t("auth_login_tab", "로그인"),
        t("auth_signup_tab", "회원가입")
    ])

    with login_tab:
        login_id = st.text_input(
            t("auth_id_label", "ID"),
            placeholder=t("auth_id_placeholder", "예: anthony"),
            key="login_id"
        )
        password = st.text_input(
            t("auth_password_label", "PASSWORD"),
            type="password",
            key="login_password"
        )

        if st.button(t("auth_login_button", "로그인"), type="primary", use_container_width=True, key="btn_login"):
            ok, message, auth_data = login_user(login_id, password)

            if ok:
                save_auth_session(auth_data)
                st.rerun()

            st.error(message)

    with signup_tab:
        display_name = st.text_input(
            t("auth_display_name_label", "이름"),
            placeholder=t("auth_display_name_placeholder", "예: 홍길동"),
            key="signup_display_name"
        )
        signup_id = st.text_input(
            t("auth_id_label", "ID"),
            placeholder=t("auth_id_placeholder", "예: anthony"),
            key="signup_id"
        )
        signup_password = st.text_input(
            t("auth_password_label", "PASSWORD"),
            type="password",
            key="signup_password"
        )
        signup_password_confirm = st.text_input(
            t("auth_password_confirm_label", "PASSWORD 확인"),
            type="password",
            key="signup_password_confirm"
        )

        if st.button(t("auth_signup_button", "회원가입"), type="primary", use_container_width=True, key="btn_signup"):
            ok, message, auth_data = register_user(
                signup_id,
                signup_password,
                signup_password_confirm,
                display_name
            )

            if ok:
                save_auth_session(auth_data)
                st.success(message)
                st.rerun()

            st.error(message)

    st.stop()


def apply_style():
    st.markdown("""
    <style>
    .main-title{font-size:2.2rem;font-weight:700;margin-bottom:.2rem}
    .sub-title{color:#666;font-size:1rem;margin-bottom:1.5rem}
    .media-title{font-size:1.05rem;font-weight:700;margin-bottom:.4rem}
    .media-yellow{background:#FFF0A6;color:#594700;padding:2px 5px;border-radius:4px;font-weight:700}
    .media-red{background:#FFD1D1;color:#8B1E1E;padding:2px 5px;border-radius:4px;font-weight:700}
    .media-transcript{line-height:1.85;padding:16px;border:1px solid #DFE3E8;border-radius:12px;background:#FAFBFC;margin-bottom:10px}
    </style>
    """, unsafe_allow_html=True)


def render_header():
    title_col, user_col = st.columns([5, 1])

    with title_col:
        st.markdown(
            f'<div class="main-title">🤖 {t("app_title", "나만의 AI 비서")}</div>',
            unsafe_allow_html=True
        )
        st.markdown(
            f'<div class="sub-title"><i>{t("app_subtitle", "이메일 작성 · 할 일 관리 · 데이터 분석 · 회의·발표 분석")}</i></div>',
            unsafe_allow_html=True
        )

    with user_col:
        profile = st.session_state.user_profile or {}
        display_name = profile.get("display_name") or profile.get("login_id") or "User"
        st.caption(t("auth_welcome", "{name}님").format(name=display_name))

        if st.button(t("auth_logout_button", "로그아웃"), use_container_width=True, key="btn_logout"):
            clear_auth_session()
            st.rerun()


def render_home(user_id):
    pending_todos = get_todos(user_id, show_completed=False)

    if not pending_todos:
        st.success(t("home_all_done", "🎉 현재 진행 중인 할 일이 모두 완료되었습니다!"))
        st.markdown("<br>", unsafe_allow_html=True)
        return

    title = t("home_pending_title", "📌 오늘 해야 할 일 ({count}건 진행 중)").format(count=len(pending_todos))

    with st.expander(title, expanded=True):
        cols = st.columns(min(len(pending_todos), 3))
        priority_map = {
            "높음": t("priority_high", "🔴 높음"),
            "보통": t("priority_normal", "🟡 보통"),
            "낮음": t("priority_low", "🟢 낮음"),
        }

        for idx, (todo_id, title, due, priority, _) in enumerate(pending_todos):
            due_text = f'{t("home_due_prefix", "마감")}: {due}' if due else t("home_no_due", "기한 없음")
            with cols[idx % len(cols)]:
                st.info(f"**{title}**\n\n`{priority_map.get(priority, priority)}` · `{due_text}` · `ID: {todo_id}`")

    st.markdown("<br>", unsafe_allow_html=True)


# =========================================================
# 이메일 작성
# =========================================================
def render_email_tab():
    st.markdown(f"### {t('email_title', '📄 PDF 메일 작성!')}")
    left, right = st.columns(2, gap="large")

    with left:
        uploaded_file = st.file_uploader(
            t("email_upload_label", "📄 PDF 또는 문서 파일 업로드 (선택)"),
            type=["pdf", "txt", "csv", "png", "jpg", "jpeg", "webp"],
            key="email_file_uploader"
        )

        situation = st.text_area(
            t("email_situation_label", "📝 상황 설명 / 공문 본문 / 추가 지시사항"),
            placeholder=t("email_situation_placeholder", "예: 거래처에 계약서 서명 요청 메일을 정중하게 작성"),
            height=140
        )

        tone_values = ["formal", "summary", "internal", "customer", "friendly", "concise", "apology"]
        tone_labels = {
            "formal": t("email_tone_formal", "공식적·정중하게"),
            "summary": t("email_tone_summary", "📜 공문/안내문 → 핵심 요약 전달 메일"),
            "internal": t("email_tone_internal", "🏢 사내/팀 공지 메일"),
            "customer": t("email_tone_customer", "🤝 거래처/고객사 협조 요청"),
            "friendly": t("email_tone_friendly", "친근하고 부드럽게"),
            "concise": t("email_tone_concise", "간결하게 (핵심만)"),
            "apology": t("email_tone_apology", "사과/양해 구하기"),
        }
        tone_key = st.radio(
            t("email_tone_label", "🎭 톤 및 변환 목적"),
            tone_values, index=0, format_func=lambda value: tone_labels[value]
        )
        additional = st.text_input(
            t("email_additional_label", "➕ 추가 요청 (선택)"),
            placeholder=t("email_additional_placeholder", "예: 마감일 강조 / 3줄 요약 포함 / 영문 번역 병기")
        )
        generate = st.button(
            t("email_generate_button", "✉️ 이메일 자동 생성 / PDF 변환"),
            type="primary", use_container_width=True, key="email_generate_button"
        )

    with right:
        st.markdown(f"**{t('email_result_title', '📨 완성된 이메일')}**")

        if not generate:
            st.info(t("email_empty_guide", "왼쪽에서 PDF 파일을 올리거나 내용을 입력한 뒤 이메일 생성 버튼을 눌러주세요."))
            return

        contents = []
        has_file = False

        if uploaded_file:
            data = uploaded_file.read()
            name = uploaded_file.name.lower()

            if name.endswith(".pdf"):
                contents.append(types.Part.from_bytes(data=data, mime_type="application/pdf"))
            elif name.endswith((".png", ".jpg", ".jpeg", ".webp")):
                mime = "image/png" if name.endswith(".png") else "image/jpeg"
                contents.append(types.Part.from_bytes(data=data, mime_type=mime))
            else:
                contents.append(f"[첨부 파일 텍스트 전문]\n{data.decode('utf-8', errors='ignore')}")
            has_file = True

        if not has_file and not situation.strip():
            st.warning(t("email_missing_input", "⚠️ PDF 파일을 업로드하거나 상황/공문 내용을 텍스트로 입력해주세요."))
            return

        system_prompt = (
            "당신은 비즈니스 이메일 및 공문서 전문 AI 비서입니다.\n"
            "첨부 문서의 실제 내용을 빠짐없이 분석하여 정중하고 읽기 쉬운 비즈니스 이메일을 작성합니다.\n"
            "실제 고유 명칭, 날짜, 제출 방법, 세부 항목을 정확히 반영하고 마크다운 기호는 사용하지 않습니다.\n"
            "반드시 제목과 본문을 구분합니다."
        )

        prompt = f"""[사용자 요청 / 추가 지시사항]
{situation.strip() or "첨부된 문서 내용을 바탕으로 수신자에게 전달할 완성된 이메일을 작성해주세요."}

[희망 톤 및 목적]
{tone_labels[tone_key]}

[추가 요청사항]
{additional.strip() or "없음"}

첨부 문서의 실제 내용과 일정, 대상자, 제출 항목을 정확히 분석하여 완성본으로 작성해주세요."""

        contents.append(prompt)

        with st.spinner(t("email_spinner", "AI가 PDF 원본 문서를 정밀 분석하여 이메일을 작성 중입니다...")):
            result = clean_email_text(get_ai_response(contents, system_prompt))

        st.text_area("", result, height=450, key="email_result_text")


# =========================================================
# 할 일 관리
# =========================================================
def render_todo_tab(user_id):
    st.markdown(f"### {t('todo_title', '✅ 할 일 관리')}")
    left, right = st.columns([1, 2], gap="large")

    with left:
        st.markdown(f"**{t('todo_add_title', '➕ 새 할 일 추가')}**")
        title = st.text_input(
            t("todo_input_label", "할 일 제목"),
            placeholder=t("todo_input_placeholder", "예: 이력서 업데이트")
        )
        due = st.text_input(
            t("todo_due_label", "마감일 (선택)"),
            placeholder=t("todo_due_placeholder", "예: 2026-08-30")
        )

        priority_labels = {
            "높음": t("priority_high", "🔴 높음"),
            "보통": t("priority_normal", "🟡 보통"),
            "낮음": t("priority_low", "🟢 낮음"),
        }
        priority = st.radio(
            t("todo_priority_label", "우선순위"),
            ["높음", "보통", "낮음"], index=1, horizontal=True,
            format_func=lambda value: priority_labels[value]
        )

        if st.button(t("todo_add_button", "➕ 할 일 추가"), type="primary", use_container_width=True, key="btn_add_todo"):
            if title.strip():
                st.success(add_todo(user_id, title, due, priority))
                st.rerun()
            st.warning(t("todo_missing_title", "할 일을 입력해주세요."))

        st.markdown("---")
        st.markdown(f"**{t('todo_manage_title', '🔧 완료 / 삭제')}**")
        todo_id = st.number_input(t("todo_id_label", "처리할 항목 ID"), min_value=1, step=1, key="input_todo_id")
        complete_col, delete_col = st.columns(2)

        with complete_col:
            if st.button(t("todo_complete_button", "✅ 완료 처리"), use_container_width=True, key="btn_complete_todo"):
                st.success(complete_todo(user_id, todo_id))
                st.rerun()

        with delete_col:
            if st.button(t("todo_delete_button", "🗑️ 삭제"), use_container_width=True, key="btn_delete_todo"):
                st.success(delete_todo(user_id, todo_id))
                st.rerun()

    with right:
        show_all = st.checkbox(t("todo_show_completed", "완료된 항목도 보기"), key="chk_show_all_todos")
        todos = get_todos(user_id, show_completed=show_all)

        if not todos:
            st.info(t("todo_empty", "등록된 할 일이 없습니다."))
            return

        df = pd.DataFrame(todos, columns=["ID", "할 일", "마감일", "우선순위", "완료여부"])
        df["상태"] = df["완료여부"].apply(
            lambda value: t("todo_status_done", "✅ 완료") if value else t("todo_status_active", "⏳ 진행중")
        )
        df = df[["ID", "할 일", "마감일", "우선순위", "상태"]].rename(columns={
            "ID": t("todo_col_id", "ID"),
            "할 일": t("todo_col_title", "할 일"),
            "마감일": t("todo_col_due", "마감일"),
            "우선순위": t("todo_col_priority", "우선순위"),
            "상태": t("todo_col_status", "상태"),
        })
        st.dataframe(df, use_container_width=True, hide_index=True)


# =========================================================
# 데이터 분석
# =========================================================
def render_data_tab():
    st.markdown(f"### {t('data_title', '📊 데이터 분석')}")
    st.write(t("data_description", "CSV / Excel 데이터를 분석합니다."))

    data_file = st.file_uploader(
        t("data_upload_label", "📁 파일 업로드 (.csv / .xlsx / .xls)"),
        type=["csv", "xlsx", "xls"], key="uploader_data_file"
    )

    if data_file is None:
        st.info(t("data_upload_guide", "분석할 CSV 또는 Excel 파일을 업로드해주세요."))
        return

    try:
        df = pd.read_csv(data_file, encoding="utf-8-sig") if data_file.name.endswith(".csv") else pd.read_excel(data_file)
        st.write(
            f"**{t('data_info_title', '📊 데이터 기본 정보')}**: "
            f"행 {len(df):,}개 | 열 {len(df.columns)}개 ({', '.join(df.columns.tolist())})"
        )
        st.dataframe(df.head(20), use_container_width=True)

        question = st.text_input(
            t("data_question_label", "❓ 궁금한 점 (선택)"),
            placeholder=t("data_question_placeholder", "예: 매출이 가장 높은 달은? 어떤 상품이 제일 잘 팔려?"),
            key="input_data_question"
        )

        if st.button(t("data_analyze_button", "📊 분석해줘!"), type="primary", key="btn_analyze_data"):
            prompt = f"""다음 데이터를 분석해주세요.
행 수: {len(df)}, 열 수: {len(df.columns)}
컬럼: {', '.join(df.columns.tolist())}

[데이터 샘플 상위 30행]
{df.head(30).to_string()}

[질문]
{question.strip() or "전체적인 데이터 분석 요약 및 핵심 인사이트를 설명해주세요."}"""

            with st.spinner(t("data_spinner", "AI가 데이터를 분석 중입니다...")):
                answer = get_ai_response(prompt)

            st.markdown(f"### {t('data_result_title', '🤖 분석 결과')}")
            st.markdown(answer)

    except Exception as error:
        st.error(t("data_read_error", "파일을 읽는 중 오류가 발생했습니다: {error}").format(error=error))


# =========================================================
# 회의·발표 분석
# =========================================================
def highlight_transcript(text, uncertain_items):
    safe_text = html.escape(text)

    for item in sorted(uncertain_items, key=lambda x: len(str(x.get("text", ""))), reverse=True):
        word = str(item.get("text", "")).strip()
        if not word:
            continue

        css_class = "media-red" if item.get("severity") == "red" else "media-yellow"
        safe_word = html.escape(word)
        safe_text = safe_text.replace(safe_word, f'<span class="{css_class}">{safe_word}</span>')

    return safe_text.replace("\n", "<br>")


def render_saved_media(user_id):
    with st.expander(f"📚 {t('media_saved_title', '저장된 회의·발표 분석')}", expanded=False):
        projects = list_media_projects(user_id)

        if not projects:
            st.info(t("media_saved_empty", "저장된 회의·발표 분석이 없습니다."))
            return

        options = {
            f"{item['title']} · {item.get('created_at', '')[:10]}": item["id"]
            for item in projects
        }
        selected = st.selectbox(t("media_saved_select", "불러올 분석"), list(options), key="media_saved_project_select")

        if st.button(t("media_load_button", "📂 불러오기"), use_container_width=True, key="btn_media_load_project"):
            project = load_media_project(user_id, options[selected])

            if not project:
                st.warning(t("media_load_fail", "저장된 분석을 불러오지 못했습니다."))
                return

            analysis = project.get("analysis") or {}
            st.session_state.media_project_id = project["id"]
            st.session_state.media_analysis = analysis
            st.session_state.media_transcript = project.get("transcript") or analysis.get("transcript", "")
            st.session_state.media_ppt_bytes = None
            st.session_state.media_pdf_bytes = None
            st.success(t("media_load_success", "저장된 분석을 불러왔습니다."))
            st.rerun()


def render_media_upload(user_id):
    left, right = st.columns([1.4, 0.8], gap="large")

    with left:
        st.markdown(f'<div class="media-title">{t("media_upload_title", "음성·영상 파일 업로드")}</div>', unsafe_allow_html=True)

        media_file = st.file_uploader(
            t("media_upload_label", "음성 또는 영상 파일"),
            type=["mp3", "wav", "m4a", "aac", "flac", "mp4", "mov", "mpeg", "mpg", "webm"],
            key="media_file_uploader"
        )

        analysis_values = ["회의록", "발표 요약", "경영진 보고", "고객사 보고", "교육 내용 정리"]
        analysis_labels = {
            "회의록": t("media_analysis_meeting", "회의록"),
            "발표 요약": t("media_analysis_presentation", "발표 요약"),
            "경영진 보고": t("media_analysis_executive", "경영진 보고"),
            "고객사 보고": t("media_analysis_customer", "고객사 보고"),
            "교육 내용 정리": t("media_analysis_training", "교육 내용 정리"),
        }
        analysis_type = st.selectbox(
            t("media_analysis_type_label", "분석 유형"),
            analysis_values, format_func=lambda value: analysis_labels[value],
            key="media_analysis_type"
        )

        language_values = ["한국어 + 영어 혼용", "한국어 중심", "영어 중심"]
        language_labels = {
            "한국어 + 영어 혼용": t("media_language_mixed", "한국어 + 영어 혼용"),
            "한국어 중심": t("media_language_korean", "한국어 중심"),
            "영어 중심": t("media_language_english", "영어 중심"),
        }
        language_mode = st.selectbox(
            t("media_language_label", "언어"),
            language_values, format_func=lambda value: language_labels[value],
            key="media_language_mode"
        )

        glossary = st.text_area(
            t("media_glossary_label", "전문용어 사전"),
            value=st.session_state.media_glossary,
            height=100,
            help=t("media_glossary_help", "회사명, 장비명, 약어 등을 쉼표로 구분해 입력하세요."),
            key="media_glossary_text"
        )
        st.session_state.media_glossary = glossary

        st.file_uploader(
            t("media_reference_label", "PPT에 사용할 참고 이미지 (선택)"),
            type=["png", "jpg", "jpeg", "webp"], accept_multiple_files=True,
            key="media_reference_images"
        )

        if st.button(
            t("media_start_button", "🎙️ 음성·영상 분석 시작"),
            type="primary", use_container_width=True, key="btn_media_analyze"
        ):
            if media_file is None:
                st.warning(t("media_file_warning", "분석할 음성 또는 영상 파일을 먼저 선택해주세요."))
                return

            glossary_items = [item.strip() for item in glossary.split(",") if item.strip()]

            try:
                with st.spinner(t("media_analyze_spinner", "AI가 음성·영상을 분석하고 있습니다. 긴 영상은 시간이 조금 걸릴 수 있습니다...")):
                    result = analyze_media(media_file, analysis_type, language_mode, glossary_items)

                st.session_state.media_analysis = result
                st.session_state.media_transcript = result.get("transcript", "")
                st.session_state.media_project_id = save_media_project(
                    user_id, result, analysis_type=analysis_type, uploaded_file=media_file
                )
                st.session_state.media_ppt_bytes = None
                st.session_state.media_pdf_bytes = None
                st.success(t("media_analyze_success", "분석이 완료되었습니다. Transcript 검토에서 내용을 확인해주세요."))

            except Exception as error:
                st.error(t("media_analyze_error", "분석 중 오류가 발생했습니다: {error}").format(error=error))

    with right:
        st.markdown(f'<div class="media-title">{t("media_feature_title", "분석 기능")}</div>', unsafe_allow_html=True)
        st.info(t(
            "media_feature_list",
            "• 한국어/영어 혼용 Transcript\n• 회사 전문용어 자동 반영\n• 애매한 표현 색상 표시\n"
            "• 핵심 내용 자동 요약\n• Action Item 자동 추출\n• 숫자 및 일정 자동 추출\n"
            "• 차트 및 Timeline 생성\n• PPT/PDF 자동 생성"
        ))
        st.caption(t("media_color_legend", "🟡 노란색 = 확인 권장 · 🔴 빨간색 = 수정 권장"))


def render_media_review(user_id):
    result = st.session_state.media_analysis
    if not result:
        st.info(t("media_review_empty", "먼저 업로드·분석에서 파일을 분석해주세요."))
        return

    uncertain_terms = result.get("uncertain_terms", [])
    transcript = st.session_state.media_transcript

    st.markdown(f"#### {t('media_uncertain_title', '애매한 표현 확인')}")
    st.markdown(
        f'<div class="media-transcript">{highlight_transcript(transcript, uncertain_terms)}</div>',
        unsafe_allow_html=True
    )
    st.caption(t("media_color_legend", "🟡 노란색 = 확인 권장 · 🔴 빨간색 = 수정 권장"))

    if uncertain_terms:
        st.markdown(f"#### {t('media_ai_correction_title', 'AI 교정 후보')}")

        for index, item in enumerate(uncertain_terms):
            col1, col2, col3 = st.columns([1, 1, 2])
            col1.write(f"**{item.get('text', '')}**")
            col2.write(f"→ {item.get('suggestion', '확인 필요')}")
            col3.caption(item.get("reason", ""))

            original = str(item.get("text", "")).strip()
            suggestion = str(item.get("suggestion", "")).strip()

            if original and suggestion and st.button(f"'{suggestion}'로 변경", key=f"media_fix_word_{index}"):
                st.session_state.media_transcript = st.session_state.media_transcript.replace(original, suggestion)
                st.session_state.media_analysis["transcript"] = st.session_state.media_transcript
                st.session_state.media_analysis["uncertain_terms"] = [
                    term for i, term in enumerate(uncertain_terms) if i != index
                ]
                st.session_state.media_ppt_bytes = None
                st.session_state.media_pdf_bytes = None

                if st.session_state.media_project_id:
                    update_media_project(user_id, st.session_state.media_project_id, st.session_state.media_analysis)
                st.rerun()

    st.markdown(f"#### {t('media_direct_edit_title', 'Transcript 직접 수정')}")
    edited = st.text_area(
        t("media_direct_edit_label", "필요한 문장을 직접 수정할 수 있습니다."),
        value=st.session_state.media_transcript, height=380, key="media_transcript_editor"
    )

    save_col, rebuild_col = st.columns(2)

    with save_col:
        if st.button(t("media_transcript_save_button", "💾 Transcript 수정 저장"), use_container_width=True, key="btn_media_save_transcript"):
            st.session_state.media_transcript = edited
            st.session_state.media_analysis["transcript"] = edited
            st.session_state.media_ppt_bytes = None
            st.session_state.media_pdf_bytes = None

            if st.session_state.media_project_id:
                update_media_project(user_id, st.session_state.media_project_id, st.session_state.media_analysis)
            st.success(t("media_transcript_saved", "수정 내용을 저장했습니다."))

    with rebuild_col:
        if st.button(
            t("media_rebuild_button", "🔄 수정본 기준 다시 정리"),
            type="primary", use_container_width=True, key="btn_media_rebuild"
        ):
            glossary = [item.strip() for item in st.session_state.media_glossary.split(",") if item.strip()]

            try:
                with st.spinner(t("media_rebuild_spinner", "수정한 Transcript를 기준으로 다시 정리하고 있습니다...")):
                    rebuilt = rebuild_from_transcript(
                        edited, st.session_state.get("media_analysis_type", "회의록"), glossary
                    )

                rebuilt["transcript"] = edited
                st.session_state.media_analysis = rebuilt
                st.session_state.media_transcript = edited
                st.session_state.media_ppt_bytes = None
                st.session_state.media_pdf_bytes = None

                if st.session_state.media_project_id:
                    update_media_project(user_id, st.session_state.media_project_id, rebuilt)
                st.success(t("media_rebuild_success", "수정한 내용 기준으로 다시 정리했습니다."))

            except Exception as error:
                st.error(t("media_rebuild_error", "재분석 중 오류가 발생했습니다: {error}").format(error=error))


def render_media_summary(user_id):
    result = st.session_state.media_analysis
    if not result:
        st.info(t("media_summary_empty", "먼저 음성 또는 영상 파일을 분석해주세요."))
        return

    st.markdown(f"#### {t('media_summary_title', '핵심 요약')}")
    summary = result.get("summary", [])

    if summary:
        for index, item in enumerate(summary, start=1):
            st.write(f"**{index}.** {item}")
    else:
        st.info(t("media_summary_none", "추출된 요약 내용이 없습니다."))

    st.markdown(f"#### {t('media_action_title', 'Action Items')}")
    actions = result.get("action_items", [])

    if actions:
        action_df = pd.DataFrame(actions)
        for column in ["owner", "task", "due", "status"]:
            if column not in action_df.columns:
                action_df[column] = ""

        edited_df = st.data_editor(
            action_df[["owner", "task", "due", "status"]],
            use_container_width=True, num_rows="dynamic",
            column_config={"owner": "담당", "task": "업무", "due": "기한", "status": "상태"},
            key="media_action_editor"
        )
        result["action_items"] = edited_df.to_dict("records")
        st.session_state.media_analysis = result
    else:
        st.info(t("media_action_none", "추출된 Action Item이 없습니다."))

    st.markdown(f"#### {t('media_keypoint_title', '중요 포인트')}")
    key_points = result.get("key_points", [])

    if key_points:
        for item in key_points:
            st.write(f"• {item}")
    else:
        st.info(t("media_keypoint_none", "추출된 중요 포인트가 없습니다."))

    if st.button(t("media_summary_save_button", "💾 요약·Action Item 저장"), use_container_width=True, key="btn_media_save_summary"):
        if st.session_state.media_project_id:
            update_media_project(user_id, st.session_state.media_project_id, st.session_state.media_analysis)
        st.success(t("media_summary_saved", "요약과 Action Item을 저장했습니다."))


def render_media_visual(user_id):
    result = st.session_state.media_analysis
    if not result:
        st.info(t("media_visual_empty", "먼저 음성 또는 영상 파일을 분석해주세요."))
        return

    st.markdown(f"#### {t('media_visual_title', '자동 시각화')}")
    rows = []

    for item in result.get("numbers", []):
        try:
            rows.append({
                "항목": item.get("label", ""),
                "값": float(item.get("value", 0)),
                "단위": item.get("unit", ""),
                "설명": item.get("context", "")
            })
        except (TypeError, ValueError):
            pass

    if rows:
        number_df = st.data_editor(pd.DataFrame(rows), use_container_width=True, num_rows="dynamic", key="media_number_editor")
        number_df["값"] = pd.to_numeric(number_df["값"], errors="coerce")
        valid_df = number_df.dropna(subset=["값"])

        chart_values = ["막대그래프", "선그래프", "표"]
        chart_labels = {
            "막대그래프": t("media_chart_bar", "막대그래프"),
            "선그래프": t("media_chart_line", "선그래프"),
            "표": t("media_chart_table", "표"),
        }
        chart_type = st.radio(
            t("media_chart_type_label", "차트 유형"),
            chart_values, horizontal=True,
            format_func=lambda value: chart_labels[value], key="media_chart_type"
        )

        if not valid_df.empty:
            source = valid_df.set_index("항목")[["값"]]
            if chart_type == "막대그래프":
                st.bar_chart(source, use_container_width=True)
            elif chart_type == "선그래프":
                st.line_chart(source, use_container_width=True)
            else:
                st.dataframe(valid_df, use_container_width=True, hide_index=True)

        result["numbers"] = [
            {
                "label": row["항목"], "value": float(row["값"]),
                "unit": row["단위"], "context": row["설명"]
            }
            for _, row in valid_df.iterrows()
        ]
        st.session_state.media_analysis = result
    else:
        st.info(t("media_no_numbers", "음성·영상에서 확인된 수치가 없어 임의의 그래프를 만들지 않았습니다."))

    timeline = result.get("timeline", [])
    if timeline:
        st.markdown(f"#### {t('media_timeline_title', 'Timeline / Process')}")
        cols = st.columns(min(len(timeline), 4))
        for index, item in enumerate(timeline):
            with cols[index % len(cols)]:
                st.markdown(f"**{item.get('label', '')}**")
                st.caption(item.get("detail", ""))

    slide_plan = result.get("slide_plan", [])
    if slide_plan:
        st.markdown(f"#### {t('media_slide_plan_title', 'AI 슬라이드 구성 제안')}")
        slide_df = pd.DataFrame([
            {
                "제목": item.get("title", ""),
                "레이아웃": item.get("layout", ""),
                "내용": " / ".join(item.get("bullets", []))
            }
            for item in slide_plan
        ])
        st.dataframe(slide_df, use_container_width=True, hide_index=True)

    if st.button(t("media_visual_save_button", "💾 시각화 수정 저장"), use_container_width=True, key="btn_media_save_visual"):
        if st.session_state.media_project_id:
            update_media_project(user_id, st.session_state.media_project_id, st.session_state.media_analysis)
        st.success(t("media_visual_saved", "시각화 수정 내용을 저장했습니다."))


def render_media_export(user_id):
    result = st.session_state.media_analysis
    if not result:
        st.info(t("media_export_empty", "먼저 음성 또는 영상 파일을 분석해주세요."))
        return

    st.markdown(f"#### {t('media_export_title', 'PPT / PDF 생성')}")
    theme = st.selectbox(
        t("media_ppt_design_label", "PPT 디자인"),
        ["Corporate Basic", "Executive", "Technical Report", "Minimal"],
        key="media_ppt_theme"
    )
    report_title = st.text_input(
        t("media_report_title_label", "보고서 제목"),
        value=result.get("title", t("media_report_title_default", "회의·발표 분석")),
        key="media_report_title"
    )
    st.caption(t("media_export_caption", "PPT/PDF를 생성하기 전에 Transcript, 요약, Action Item, 시각화를 최종 확인해주세요."))

    if st.button(
        t("media_generate_button", "✨ PPT / PDF 파일 생성"),
        type="primary", use_container_width=True, key="btn_generate_media_files"
    ):
        references = []
        for image_file in st.session_state.get("media_reference_images", []) or []:
            try:
                references.append({"name": image_file.name, "bytes": image_file.getvalue()})
            except Exception:
                pass

        try:
            with st.spinner(t("media_export_spinner", "PPT와 PDF를 생성하고 있습니다...")):
                st.session_state.media_ppt_bytes = build_pptx(result, theme_name=theme, reference_images=references)
                st.session_state.media_pdf_bytes = build_pdf(result, report_title=report_title)

                if st.session_state.media_project_id:
                    save_generated_files(
                        user_id, st.session_state.media_project_id,
                        ppt_bytes=st.session_state.media_ppt_bytes,
                        pdf_bytes=st.session_state.media_pdf_bytes
                    )

            st.success(t("media_export_success", "PPT와 PDF 생성이 완료되었습니다."))

        except Exception as error:
            st.session_state.media_ppt_bytes = None
            st.session_state.media_pdf_bytes = None
            st.error(t("media_export_error", "PPT/PDF 생성 중 오류가 발생했습니다: {error}").format(error=error))

    if not (st.session_state.media_ppt_bytes or st.session_state.media_pdf_bytes):
        return

    ppt_col, pdf_col = st.columns(2)

    with ppt_col:
        if st.session_state.media_ppt_bytes:
            st.download_button(
                t("media_ppt_download", "📥 PPT 다운로드"),
                data=st.session_state.media_ppt_bytes,
                file_name="AIAI_meeting_report.pptx",
                mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                use_container_width=True,
                key="download_media_ppt"
            )

    with pdf_col:
        if st.session_state.media_pdf_bytes:
            st.download_button(
                t("media_pdf_download", "📥 PDF 다운로드"),
                data=st.session_state.media_pdf_bytes,
                file_name="AIAI_meeting_report.pdf",
                mime="application/pdf",
                use_container_width=True,
                key="download_media_pdf"
            )


def render_media_tab(user_id):
    st.markdown(f"### {t('media_title', '🎙️ 회의·발표 분석')}")
    st.caption(t("media_caption", "음성·영상 → Transcript → 검토 → 요약 → 시각화 → PPT/PDF"))
    render_saved_media(user_id)

    tabs = st.tabs([
        t("media_tab_upload", "1️⃣ 업로드·분석"),
        t("media_tab_review", "2️⃣ Transcript 검토"),
        t("media_tab_summary", "3️⃣ 요약·Action Item"),
        t("media_tab_visual", "4️⃣ 시각화"),
        t("media_tab_export", "5️⃣ PPT/PDF"),
    ])

    with tabs[0]:
        render_media_upload(user_id)
    with tabs[1]:
        render_media_review(user_id)
    with tabs[2]:
        render_media_summary(user_id)
    with tabs[3]:
        render_media_visual(user_id)
    with tabs[4]:
        render_media_export(user_id)


# =========================================================
# 관리자 설정
# =========================================================
def render_admin_tab():
    st.markdown(f"### {t('admin_title', '⚙️ 관리자 설정')}")
    st.caption(t("admin_caption", "탭 이름, 아이콘, 순서, 표시 여부와 앱 문구를 직접 수정할 수 있습니다."))

    tab_settings = get_tabs()

    if not tab_settings:
        st.info(t("admin_no_tabs", "등록된 탭 설정이 없습니다."))
    else:
        for item in tab_settings:
            with st.expander(f"{item.get('icon', '')} {item['label']}", expanded=False):
                label = st.text_input(
                    t("admin_tab_name_label", "탭 이름"),
                    value=item["label"],
                    key=f"admin_label_{item['tab_key']}"
                )
                icon = st.text_input(
                    t("admin_icon_label", "아이콘"),
                    value=item.get("icon", ""),
                    key=f"admin_icon_{item['tab_key']}"
                )
                order = st.number_input(
                    t("admin_order_label", "순서"),
                    min_value=1, max_value=20, value=int(item.get("sort_order", 1)), step=1,
                    key=f"admin_order_{item['tab_key']}"
                )
                visible = st.toggle(
                    t("admin_visible_label", "탭 표시"),
                    value=bool(item.get("is_visible", True)),
                    key=f"admin_visible_{item['tab_key']}"
                )

                if st.button(t("admin_save_button", "💾 저장"), use_container_width=True, key=f"admin_save_{item['tab_key']}"):
                    update_tab(item["tab_key"], label, icon, order, visible)
                    st.success(t("admin_save_success", "설정을 저장했습니다."))
                    st.rerun()

    st.markdown("---")
    st.markdown(f"### {t('admin_text_title', '✏️ 앱 문구 관리')}")
    st.caption(t("admin_text_caption", "앱에서 사용하는 문구를 카테고리별로 직접 수정할 수 있습니다."))

    text_settings = get_texts()

    if not text_settings:
        st.info(t("admin_no_texts", "등록된 문구 설정이 없습니다."))
        return

    categories = sorted({item.get("category", "기타") for item in text_settings})
    category = st.selectbox(t("admin_category_label", "문구 카테고리"), categories, key="admin_text_category")

    for item in [row for row in text_settings if row.get("category", "기타") == category]:
        with st.expander(item["label"], expanded=False):
            st.caption(f"설정 키: {item['text_key']}")
            value = st.text_area(
                t("admin_text_value_label", "표시 문구"),
                value=item.get("value", ""),
                key=f"admin_text_{item['text_key']}"
            )

            if st.button(
                t("admin_text_save_button", "💾 문구 저장"),
                use_container_width=True,
                key=f"admin_text_save_{item['text_key']}"
            ):
                update_text(item["text_key"], value)
                st.success(t("admin_text_save_success", "문구를 저장했습니다."))
                st.rerun()


# =========================================================
# 실행
# =========================================================
def main():
    init_state()
    restore_auth()
    render_auth()

    user_id = st.session_state.user_id
    profile = st.session_state.user_profile or {}
    is_admin = profile.get("role") == "admin"

    apply_style()
    render_header()
    render_home(user_id)

    tab_config = [tab for tab in get_tabs() if tab.get("is_visible", True)]
    tab_labels = [f"{tab.get('icon', '')} {tab['label']}".strip() for tab in tab_config]

    if is_admin:
        tab_labels.append(t("admin_tab_label", "⚙️ 관리자 설정"))

    tabs = st.tabs(tab_labels)
    tab_map = {tab["tab_key"]: tabs[index] for index, tab in enumerate(tab_config)}

    if "email" in tab_map:
        with tab_map["email"]:
            render_email_tab()

    if "todo" in tab_map:
        with tab_map["todo"]:
            render_todo_tab(user_id)

    if "data" in tab_map:
        with tab_map["data"]:
            render_data_tab()

    if "media" in tab_map:
        with tab_map["media"]:
            render_media_tab(user_id)

    if is_admin:
        with tabs[-1]:
            render_admin_tab()


if __name__ == "__main__":
    main()
