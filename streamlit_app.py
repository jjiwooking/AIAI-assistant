from modules.media_storage import (
    save_media_project,
    update_media_project,
    list_media_projects,
    load_media_project,
    save_generated_files
)

import streamlit as st
import pandas as pd
import os
import re
from google.genai import types
from modules.ai_client import get_ai_response
from modules.todo_manager import add_todo, get_todos, complete_todo, delete_todo
from modules.job_tracker import add_job, get_jobs, update_job_status

st.set_page_config(
    page_title="나만의 AI 비서 🤖",
    page_icon="🤖",
    layout="wide"
)
if "user_id" not in st.session_state:
    st.session_state.user_id = ""
if "media_project_id" not in st.session_state:
    st.session_state.media_project_id = None
if not st.session_state.user_id:
    st.title("🤖 나만의 AI 비서")
    login_name = st.text_input("사용자 이름", placeholder="예: 홍길동")
    if st.button("시작하기", type="primary"):
        if login_name.strip():
            st.session_state.user_id = login_name.strip()
            st.rerun()
        else:
            st.warning("사용자 이름을 입력해주세요.")
    st.stop()

USER_ID = st.session_state.user_id
# 커스텀 스타일 적용 (깔끔한 UI)
st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        color: #666;
        font-size: 1rem;
        margin-bottom: 1.5rem;
    }
</style>
""", unsafe_allow_html=True)

def clean_email_text(text: str) -> str:
    """메일 프로그램(네이버, 아웃룩, 지메일 등)에 바로 복사하여 보낼 수 있도록 마크다운 기호를 정돈합니다."""
    if not text:
        return ""
    cleaned = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    cleaned = re.sub(r'\*(.*?)\*', r'\1', cleaned)
    cleaned = re.sub(r'^#{1,6}\s*', '', cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r'^[-*_]{3,}\s*$', '', cleaned, flags=re.MULTILINE)
    cleaned = cleaned.replace('`', '')
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
    return cleaned.strip()

st.markdown('<div class="main-title">🤖 나만의 AI 비서</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title"><i>이메일 작성 · 할 일 관리 · 데이터 분석 · 채용 관리</i></div>', unsafe_allow_html=True)

# ─────────────────────────────────────────
# 📌 메인 화면: 진행 중인 할 일 브리핑
# ─────────────────────────────────────────
pending_todos = get_todos(USER_ID, show_completed=False)
if pending_todos:
    with st.expander(f"📌 **오늘 해야 할 일 ({len(pending_todos)}건 진행 중)**", expanded=True):
        cols = st.columns(min(len(pending_todos), 3))
        for idx, (t_id, t_title, t_due, t_pri, _) in enumerate(pending_todos):
            c = cols[idx % min(len(pending_todos), 3)]
            pri_badge = "🔴 높음" if t_pri == "높음" else ("🟡 보통" if t_pri == "보통" else "🟢 낮음")
            due_badge = f"마감: {t_due}" if t_due else "기한 없음"
            with c:
                st.info(f"**{t_title}**\n\n`{pri_badge}` · `{due_badge}` · `ID: {t_id}`")
else:
    st.success("🎉 **현재 진행 중인 할 일이 모두 완료되었습니다!** (새로운 할 일은 '✅ 할 일 관리' 탭에서 등록하세요)")

st.markdown("<br>", unsafe_allow_html=True)

tabs = st.tabs(["✉️ 이메일 작성", "✅ 할 일 관리", "📊 데이터 분석", "💼 채용 관리", "🎙️ 회의·발표 분석"])

# ─────────────────────────────────────────
# 탭 1: 이메일 작성 (PDF / 공문 변환)
# ─────────────────────────────────────────
with tabs[0]:
    st.markdown("### 📄 PDF 공문/문서를 올리거나 텍스트를 입력하면 깔끔한 비즈니스 메일로 자동 변환해 드려요!")
    
    col1, col2 = st.columns([1, 1], gap="large")

    with col1:
        uploaded_file = st.file_uploader(
            "📄 PDF 또는 문서 파일 업로드 (선택)",
            type=["pdf", "txt", "csv", "png", "jpg", "jpeg", "webp"]
        )
        
        email_situation = st.text_area(
            "📝 상황 설명 / 공문 본문 / 추가 지시사항",
            placeholder="예 1: PDF 파일 올린 후 -> '사내 팀원들에게 핵심 일정 위주로 전달하는 메일 써줘'\n\n예 2: 텍스트 직접 입력 -> '거래처에 계약서 서명 요청 메일 정중하게 작성'",
            height=140
        )
        
        email_tone = st.radio(
            "🎭 톤 및 변환 목적",
            options=[
                "공식적·정중하게",
                "📜 공문/안내문 → 핵심 요약 전달 메일",
                "🏢 사내/팀 공지 메일",
                "🤝 거래처/고객사 협조 요청",
                "친근하고 부드럽게",
                "간결하게 (핵심만)",
                "사과/양해 구하기"
            ],
            index=0
        )
        
        email_additional = st.text_input(
            "➕ 추가 요청 (선택)",
            placeholder="예: 마감일 강조 / 3줄 요약 포함 / 영문 번역 병기"
        )
        
        generate_btn = st.button("✉️ 이메일 자동 생성 / PDF 변환", type="primary", use_container_width=True)

    with col2:
        st.markdown("**📨 완성된 이메일 (마크다운 기호 없이 복사해서 바로 붙여넣기 가능)**")
        
        if generate_btn:
            contents_list = []
            has_file = False

            if uploaded_file is not None:
                file_bytes = uploaded_file.read()
                fname = uploaded_file.name.lower()
                if fname.endswith(".pdf"):
                    part = types.Part.from_bytes(data=file_bytes, mime_type="application/pdf")
                    contents_list.append(part)
                    has_file = True
                elif fname.endswith((".png", ".jpg", ".jpeg", ".webp")):
                    mime = "image/png" if fname.endswith(".png") else "image/jpeg"
                    part = types.Part.from_bytes(data=file_bytes, mime_type=mime)
                    contents_list.append(part)
                    has_file = True
                else:
                    text_data = file_bytes.decode("utf-8", errors="ignore")
                    contents_list.append(f"[첨부 파일 텍스트 전문]\n{text_data}")
                    has_file = True

            if not has_file and not email_situation.strip():
                st.warning("⚠️ PDF 파일을 업로드하거나 상황/공문 내용을 텍스트로 입력해주세요.")
            else:
                with st.spinner("AI가 PDF 원본 문서를 정밀 분석하여 이메일을 작성 중입니다..."):
                    system_prompt = (
                        "당신은 비즈니스 이메일 및 공문서 전문 AI 비서입니다.\n"
                        "제공된 첨부 PDF/문서의 실제 내용(기관/대학명, 학기, 마감 기한, 대상자, 제출 서류, 세부 절차 등)을 "
                        "빠짐없이 꼼꼼하게 읽고 분석하여, 받는 사람이 한눈에 파악하기 쉬운 세련되고 정중한 비즈니스 이메일을 작성합니다.\n\n"
                        "[가장 중요한 원칙]\n"
                        "1. 첨부 문서가 제공된 경우 임의의 가상 데이터(예: 00대학교, 202X년, 0월 0일)를 사용하지 말고, "
                        "문서에 적힌 실제 고유 명칭, 실제 날짜, 실제 제출 방법, 세부 항목을 정확하게 반영하세요.\n"
                        "2. 메일 프로그램(네이버, 아웃룩, 지메일 등)에 바로 복사하여 보낼 수 있도록 마크다운 기호(**, ###, ---, ` 등)를 일체 사용하지 마세요.\n"
                        "3. 강조가 필요한 부분은 [대괄호], 【핵심안내】, <필수>, '작은따옴표' 등으로 자연스럽게 표기하세요.\n"
                        "4. 구분선(---) 대신 적절한 빈 줄(줄바꿈)을 활용하여 시각적으로 시원하게 작성하세요.\n"
                        "5. 내용 요약 및 항목 나열 시에는 '•', '-', '1.', '2.' 등의 표준 기호를 사용하세요.\n"
                        "6. 반드시 [제목]과 [본문]을 구분하여 작성하세요."
                    )
                    
                    prompt_text = f"""[사용자 요청 / 추가 지시사항]
{email_situation.strip() if email_situation.strip() else "첨부된 문서 내용을 바탕으로 수신자에게 전달할 완성된 이메일을 작성해주세요."}

[희망 톤 및 목적]
{email_tone}

[추가 요청사항]
{email_additional.strip() if email_additional.strip() else "없음"}

첨부 문서의 실제 내용과 일정, 대상자, 제출 항목을 정확히 분석하여 불필요한 마크다운 별표(**) 없이 완성본으로 작성해주세요."""

                    contents_list.append(prompt_text)
                    raw_res = get_ai_response(contents_list, system_prompt)
                    final_res = clean_email_text(raw_res)
                    st.text_area("", final_res, height=450)
        else:
            st.info("왼쪽에서 PDF 파일을 올리거나 내용을 입력한 뒤 [✉️ 이메일 자동 생성 / PDF 변환] 버튼을 눌러주세요.")

# ─────────────────────────────────────────
# 탭 2: 할 일 관리
# ─────────────────────────────────────────
with tabs[1]:
    st.markdown("### ✅ 할 일 관리")
    tcol1, tcol2 = st.columns([1, 2], gap="large")

    with tcol1:
        st.markdown("**➕ 새 할 일 추가**")
        todo_title = st.text_input("할 일 제목", placeholder="예: 이력서 업데이트")
        todo_due = st.text_input("마감일 (선택)", placeholder="예: 2026-08-30")
        todo_priority = st.radio("우선순위", ["높음", "보통", "낮음"], index=1, horizontal=True)
        if st.button("➕ 할 일 추가", type="primary", use_container_width=True, key="btn_add_todo"):
            if todo_title.strip():
                msg = add_todo(USER_ID, todo_title, todo_due, todo_priority)
                st.success(msg)
                st.rerun()
            else:
                st.warning("할 일을 입력해주세요.")

        st.markdown("---")
        st.markdown("**🔧 완료 / 삭제**")
        todo_id = st.number_input("처리할 항목 ID", min_value=1, step=1, key="input_todo_id")
        bcol1, bcol2 = st.columns(2)
        with bcol1:
            if st.button("✅ 완료 처리", use_container_width=True, key="btn_complete_todo"):
                msg = complete_todo(USER_ID, todo_id)
                st.success(msg)
                st.rerun()
        with bcol2:
            if st.button("🗑️ 삭제", use_container_width=True, key="btn_delete_todo"):
                msg = delete_todo(USER_ID, todo_id)
                st.success(msg)
                st.rerun()

    with tcol2:
        show_all = st.checkbox("완료된 항목도 보기", key="chk_show_all_todos")
        todos = get_todos(USER_ID, show_completed=show_all)
        if todos:
            df_todos = pd.DataFrame(todos, columns=["ID", "할 일", "마감일", "우선순위", "완료여부"])
            df_todos["상태"] = df_todos["완료여부"].apply(lambda x: "✅ 완료" if x else "⏳ 진행중")
            st.dataframe(df_todos[["ID", "할 일", "마감일", "우선순위", "상태"]], use_container_width=True, hide_index=True)
        else:
            st.info("등록된 할 일이 없습니다.")

# ─────────────────────────────────────────
# 탭 3: 데이터 분석
# ─────────────────────────────────────────
with tabs[2]:
    st.markdown("### 📊 데이터 분석")
    st.write("CSV / Excel 파일을 올리면 AI가 데이터를 분석해 드려요!")
    data_file = st.file_uploader("📁 파일 업로드 (.csv / .xlsx / .xls)", type=["csv", "xlsx", "xls"], key="uploader_data_file")
    if data_file is not None:
        try:
            if data_file.name.endswith(".csv"):
                df = pd.read_csv(data_file, encoding="utf-8-sig")
            else:
                df = pd.read_excel(data_file)
            
            st.write(f"📊 **데이터 기본 정보**: 행 {len(df):,}개 | 열 {len(df.columns)}개 ({', '.join(df.columns.tolist())})")
            st.dataframe(df.head(20), use_container_width=True)

            data_q = st.text_input("❓ 궁금한 점 (선택)", placeholder="예: 매출이 가장 높은 달은? 어떤 상품이 제일 잘 팔려?", key="input_data_question")
            if st.button("📊 분석해줘!", type="primary", key="btn_analyze_data"):
                with st.spinner("AI가 데이터를 분석 중입니다..."):
                    sample_text = df.head(30).to_string()
                    prompt = f"""다음 데이터를 분석해주세요.
행 수: {len(df)}, 열 수: {len(df.columns)}
컬럼: {', '.join(df.columns.tolist())}

[데이터 샘플 상위 30행]
{sample_text}

[질문]
{data_q if data_q.strip() else "전체적인 데이터 분석 요약 및 핵심 인사이트를 설명해주세요."}"""
                    ans = get_ai_response(prompt)
                    st.markdown("### 🤖 분석 결과")
                    st.markdown(ans)
        except Exception as e:
            st.error(f"파일을 읽는 중 오류가 발생했습니다: {e}")
    else:
        st.info("분석할 CSV 또는 Excel 파일을 업로드해주세요.")

# ─────────────────────────────────────────
# 탭 4: 채용 관리
# ─────────────────────────────────────────
with tabs[3]:
    st.markdown("### 💼 채용 관리")
    st.write("관심 기업 및 지원 현황을 한눈에 관리하세요!")
    
    jcol1, jcol2 = st.columns([1, 2], gap="large")
    with jcol1:
        st.markdown("**➕ 새 채용 정보 추가**")
        j_company = st.text_input("기업명", placeholder="예: 카카오", key="input_job_company")
        j_pos = st.text_input("직무", placeholder="예: 데이터 분석가", key="input_job_position")
        j_stat = st.selectbox("현재 상태", ["지원 예정", "서류 지원", "서류 합격", "면접 예정", "면접 완료", "최종 합격", "불합격"], key="select_job_status")
        j_dead = st.text_input("마감일", placeholder="예: 2026-08-30", key="input_job_deadline")
        j_note = st.text_area("메모", placeholder="연봉, 복지, 전형 특이사항 등...", height=100, key="textarea_job_note")
        if st.button("➕ 채용 정보 등록", type="primary", use_container_width=True, key="btn_add_job"):
            if j_company.strip() and j_pos.strip():
                msg = add_job(USER_ID, j_company, j_pos, j_stat, j_dead, j_note)
                st.success(msg)
                st.rerun()
            else:
                st.warning("기업명과 직무를 입력해주세요.")

    with jcol2:
        jobs = get_jobs(USER_ID)
        if jobs:
            df_jobs = pd.DataFrame(jobs, columns=["ID", "기업명", "직무", "상태", "마감일", "메모"])
            st.dataframe(df_jobs, use_container_width=True, hide_index=True)
        else:
            st.info("등록된 채용 정보가 없습니다.")
# =========================================================
# 탭 5 : 회의·발표 분석
# =========================================================
with tabs[4]:
    import html
    import pandas as pd
    from modules.media_report import analyze_media, rebuild_from_transcript, build_pptx, build_pdf

    st.markdown("### 🎙️ 회의·발표 분석")
    st.caption("음성·영상 → Transcript → 검토 → 요약 → 시각화 → PPT/PDF")

    # 기본 상태값
    if "media_analysis" not in st.session_state:
        st.session_state.media_analysis = None
    if "media_transcript" not in st.session_state:
        st.session_state.media_transcript = ""
    if "media_glossary" not in st.session_state:
        st.session_state.media_glossary = "Micron, APTD, TCB, RMS, Ejector, Flipper, Auto Tool Change, EFEM, BOC, FAC, T131"
    if "media_ppt_bytes" not in st.session_state:
        st.session_state.media_ppt_bytes = None
    if "media_pdf_bytes" not in st.session_state:
        st.session_state.media_pdf_bytes = None

# 👇 여기 추가
    with st.expander("📚 저장된 회의·발표 분석", expanded=False):
    saved_projects = list_media_projects(USER_ID)

    if not saved_projects:
        st.info("저장된 회의·발표 분석이 없습니다.")
    else:
        project_options = {
            f"{item['title']} · {item.get('created_at', '')[:10]}": item["id"]
            for item in saved_projects
        }

        selected_project = st.selectbox(
            "불러올 분석",
            options=list(project_options.keys()),
            key="media_saved_project_select"
        )

        if st.button("📂 불러오기", use_container_width=True, key="btn_media_load_project"):
            project = load_media_project(
                USER_ID,
                project_options[selected_project]
            )

            if project:
                analysis = project.get("analysis") or {}

                st.session_state.media_project_id = project["id"]
                st.session_state.media_analysis = analysis
                st.session_state.media_transcript = project.get("transcript") or analysis.get("transcript", "")
                st.session_state.media_ppt_bytes = None
                st.session_state.media_pdf_bytes = None

                st.success("저장된 분석을 불러왔습니다.")
                st.rerun()
            else:
                st.warning("저장된 분석을 불러오지 못했습니다.")

# 디자인
    # 디자인
    st.markdown("""
    <style>
    .media-title{font-size:1.05rem;font-weight:700;margin-bottom:0.4rem}
    .media-yellow{background:#FFF0A6;color:#594700;padding:2px 5px;border-radius:4px;font-weight:700}
    .media-red{background:#FFD1D1;color:#8B1E1E;padding:2px 5px;border-radius:4px;font-weight:700}
    .media-transcript{line-height:1.85;padding:16px;border:1px solid #DFE3E8;border-radius:12px;background:#FAFBFC;margin-bottom:10px}
    </style>
    """, unsafe_allow_html=True)

    media_tabs = st.tabs([
        "1️⃣ 업로드·분석",
        "2️⃣ Transcript 검토",
        "3️⃣ 요약·Action Item",
        "4️⃣ 시각화",
        "5️⃣ PPT/PDF"
    ])

    # =====================================================
    # 1. 업로드·분석
    # =====================================================
    with media_tabs[0]:
        left, right = st.columns([1.4, 0.8], gap="large")

        with left:
            st.markdown('<div class="media-title">음성·영상 파일 업로드</div>', unsafe_allow_html=True)

            media_file = st.file_uploader(
                "음성 또는 영상 파일",
                type=["mp3", "wav", "m4a", "aac", "flac", "mp4", "mov", "mpeg", "mpg", "webm"],
                key="media_file_uploader"
            )

            analysis_type = st.selectbox(
                "분석 유형",
                ["회의록", "발표 요약", "경영진 보고", "고객사 보고", "교육 내용 정리"],
                key="media_analysis_type"
            )

            language_mode = st.selectbox(
                "언어",
                ["한국어 + 영어 혼용", "한국어 중심", "영어 중심"],
                key="media_language_mode"
            )

            glossary_text = st.text_area(
                "전문용어 사전",
                value=st.session_state.media_glossary,
                height=100,
                help="회사명, 장비명, 약어 등을 쉼표로 구분해 입력하세요.",
                key="media_glossary_text"
            )
            st.session_state.media_glossary = glossary_text

            st.file_uploader(
                "PPT에 사용할 참고 이미지 (선택)",
                type=["png", "jpg", "jpeg", "webp"],
                accept_multiple_files=True,
                key="media_reference_images"
            )

            if st.button("🎙️ 음성·영상 분석 시작", type="primary", use_container_width=True, key="btn_media_analyze"):
                if media_file is None:
                    st.warning("분석할 음성 또는 영상 파일을 먼저 선택해주세요.")
                else:
                    glossary = [item.strip() for item in glossary_text.split(",") if item.strip()]

                    try:
                        with st.spinner("AI가 음성·영상을 분석하고 있습니다. 긴 영상은 시간이 조금 걸릴 수 있습니다..."):
                            result = analyze_media(media_file, analysis_type, language_mode, glossary)

                        st.session_state.media_analysis = result
                        st.session_state.media_transcript = result.get("transcript", "")
                        st.session_state.media_project_id = save_media_project(
                            USER_ID,
                            result,
                            analysis_type=analysis_type,
                            uploaded_file=media_file
)
                        st.session_state.media_ppt_bytes = None
                        st.session_state.media_pdf_bytes = None

                        st.success("분석이 완료되었습니다. 2️⃣ Transcript 검토에서 내용을 확인해주세요.")

                    except Exception as e:
                        st.error(f"분석 중 오류가 발생했습니다: {e}")

        with right:
            st.markdown('<div class="media-title">분석 기능</div>', unsafe_allow_html=True)

            st.info(
                "• 한국어/영어 혼용 Transcript\n"
                "• 회사 전문용어 자동 반영\n"
                "• 애매한 표현 색상 표시\n"
                "• 핵심 내용 자동 요약\n"
                "• Action Item 자동 추출\n"
                "• 숫자 및 일정 자동 추출\n"
                "• 차트 및 Timeline 생성\n"
                "• PPT/PDF 자동 생성"
            )

            st.caption("🟡 노란색 = 확인 권장\n🔴 빨간색 = 수정 권장")

    # =====================================================
    # 2. Transcript 검토
    # =====================================================
    with media_tabs[1]:
        result = st.session_state.media_analysis

        if not result:
            st.info("먼저 1️⃣ 업로드·분석에서 파일을 분석해주세요.")
        else:
            uncertain_terms = result.get("uncertain_terms", [])
            transcript = st.session_state.media_transcript

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

            st.markdown("#### 애매한 표현 확인")

            st.markdown(
                f'<div class="media-transcript">{highlight_transcript(transcript, uncertain_terms)}</div>',
                unsafe_allow_html=True
            )

            st.caption("🟡 확인 권장 · 🔴 수정 권장")

            if uncertain_terms:
                st.markdown("#### AI 교정 후보")

                for index, item in enumerate(uncertain_terms):
                    col1, col2, col3 = st.columns([1, 1, 2])

                    col1.write(f"**{item.get('text', '')}**")
                    col2.write(f"→ {item.get('suggestion', '확인 필요')}")
                    col3.caption(item.get("reason", ""))

                    original = str(item.get("text", "")).strip()
                    suggestion = str(item.get("suggestion", "")).strip()

                    if original and suggestion:
                        if st.button(f"'{suggestion}'로 변경", key=f"media_fix_word_{index}"):
                            st.session_state.media_transcript = st.session_state.media_transcript.replace(original, suggestion)
                            st.session_state.media_analysis["uncertain_terms"] = [
                                term for i, term in enumerate(uncertain_terms) if i != index
                            ]
                            st.session_state.media_ppt_bytes = None
                            st.session_state.media_pdf_bytes = None
                            st.rerun()

            st.markdown("#### Transcript 직접 수정")

            edited_transcript = st.text_area(
                "필요한 문장을 직접 수정할 수 있습니다.",
                value=st.session_state.media_transcript,
                height=380,
                key="media_transcript_editor"
            )

            save_col, rebuild_col = st.columns(2)

            with save_col:
                if st.button("💾 Transcript 수정 저장", use_container_width=True, key="btn_media_save_transcript"):
                    st.session_state.media_transcript = edited_transcript
                    st.session_state.media_analysis["transcript"] = edited_transcript
                    st.session_state.media_ppt_bytes = None
                    st.session_state.media_pdf_bytes = None
                    if st.session_state.media_project_id:
                        update_media_project(
                            USER_ID,
                            st.session_state.media_project_id,
                            st.session_state.media_analysis
            )
                    st.success("수정 내용을 저장했습니다.")

            with rebuild_col:
                if st.button("🔄 수정본 기준 다시 정리", type="primary", use_container_width=True, key="btn_media_rebuild"):
                    glossary = [item.strip() for item in st.session_state.media_glossary.split(",") if item.strip()]

                    try:
                        with st.spinner("수정한 Transcript를 기준으로 다시 정리하고 있습니다..."):
                            rebuilt = rebuild_from_transcript(
                                edited_transcript,
                                st.session_state.get("media_analysis_type", "회의록"),
                                glossary
                            )

                        st.session_state.media_analysis = rebuilt
                        st.session_state.media_transcript = edited_transcript
                        st.session_state.media_ppt_bytes = None
                        st.session_state.media_pdf_bytes = None

                        st.success("수정한 내용 기준으로 다시 정리했습니다.")

                    except Exception as e:
                        st.error(f"재분석 중 오류가 발생했습니다: {e}")

    # =====================================================
    # 3. 요약·Action Item
    # =====================================================
    with media_tabs[2]:
        result = st.session_state.media_analysis

        if not result:
            st.info("먼저 음성 또는 영상 파일을 분석해주세요.")
        else:
            st.markdown("#### 핵심 요약")

            summary = result.get("summary", [])

            if summary:
                for index, item in enumerate(summary, start=1):
                    st.write(f"**{index}.** {item}")
            else:
                st.info("추출된 요약 내용이 없습니다.")

            st.markdown("#### Action Items")

            actions = result.get("action_items", [])

            if actions:
                action_df = pd.DataFrame(actions)

                for column in ["owner", "task", "due", "status"]:
                    if column not in action_df.columns:
                        action_df[column] = ""

                edited_action_df = st.data_editor(
                    action_df[["owner", "task", "due", "status"]],
                    use_container_width=True,
                    num_rows="dynamic",
                    column_config={
                        "owner": "담당",
                        "task": "업무",
                        "due": "기한",
                        "status": "상태"
                    },
                    key="media_action_editor"
                )

                result["action_items"] = edited_action_df.to_dict("records")
                st.session_state.media_analysis = result
            else:
                st.info("추출된 Action Item이 없습니다.")

            st.markdown("#### 중요 포인트")

            key_points = result.get("key_points", [])

            if key_points:
                for item in key_points:
                    st.write(f"• {item}")
            else:
                st.info("추출된 중요 포인트가 없습니다.")

    # =====================================================
    # 4. 시각화
    # =====================================================
    with media_tabs[3]:
        result = st.session_state.media_analysis

        if not result:
            st.info("먼저 음성 또는 영상 파일을 분석해주세요.")
        else:
            st.markdown("#### 자동 시각화")

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
                number_df = pd.DataFrame(rows)

                edited_number_df = st.data_editor(
                    number_df,
                    use_container_width=True,
                    num_rows="dynamic",
                    key="media_number_editor"
                )

                edited_number_df["값"] = pd.to_numeric(edited_number_df["값"], errors="coerce")
                valid_chart_df = edited_number_df.dropna(subset=["값"])

                chart_type = st.radio(
                    "차트 유형",
                    ["막대그래프", "선그래프", "표"],
                    horizontal=True,
                    key="media_chart_type"
                )

                if not valid_chart_df.empty:
                    chart_source = valid_chart_df.set_index("항목")[["값"]]

                    if chart_type == "막대그래프":
                        st.bar_chart(chart_source, use_container_width=True)
                    elif chart_type == "선그래프":
                        st.line_chart(chart_source, use_container_width=True)
                    else:
                        st.dataframe(valid_chart_df, use_container_width=True, hide_index=True)

                result["numbers"] = [
                    {
                        "label": row["항목"],
                        "value": float(row["값"]),
                        "unit": row["단위"],
                        "context": row["설명"]
                    }
                    for _, row in valid_chart_df.iterrows()
                ]

                st.session_state.media_analysis = result
            else:
                st.info("음성·영상에서 확인된 수치가 없어 임의의 그래프를 만들지 않았습니다.")

            # Timeline
            timeline = result.get("timeline", [])

            if timeline:
                st.markdown("#### Timeline / Process")

                column_count = min(len(timeline), 4)
                timeline_columns = st.columns(column_count)

                for index, item in enumerate(timeline):
                    with timeline_columns[index % column_count]:
                        st.markdown(f"**{item.get('label', '')}**")
                        st.caption(item.get("detail", ""))

            # 슬라이드 구성 제안
            slide_plan = result.get("slide_plan", [])

            if slide_plan:
                st.markdown("#### AI 슬라이드 구성 제안")

                slide_plan_df = pd.DataFrame([
                    {
                        "제목": item.get("title", ""),
                        "레이아웃": item.get("layout", ""),
                        "내용": " / ".join(item.get("bullets", []))
                    }
                    for item in slide_plan
                ])

                st.dataframe(slide_plan_df, use_container_width=True, hide_index=True)

    # =====================================================
    # 5. PPT / PDF
    # =====================================================
    with media_tabs[4]:
        result = st.session_state.media_analysis

        if not result:
            st.info("먼저 음성 또는 영상 파일을 분석해주세요.")
        else:
            st.markdown("#### PPT / PDF 생성")

            theme_name = st.selectbox(
                "PPT 디자인",
                ["Corporate Basic", "Executive", "Technical Report", "Minimal"],
                key="media_ppt_theme"
            )

            report_title = st.text_input(
                "보고서 제목",
                value=result.get("title", "회의·발표 분석"),
                key="media_report_title"
            )

            st.caption("PPT/PDF를 생성하기 전에 Transcript, 요약, Action Item, 시각화를 최종 확인해주세요.")

            if st.button("✨ PPT / PDF 파일 생성", type="primary", use_container_width=True, key="btn_generate_media_files"):
                reference_payload = []

                for image_file in st.session_state.get("media_reference_images", []) or []:
                    try:
                        reference_payload.append({
                            "name": image_file.name,
                            "bytes": image_file.getvalue()
                        })
                    except Exception:
                        pass

                try:
                    with st.spinner("PPT와 PDF를 생성하고 있습니다..."):
                        st.session_state.media_ppt_bytes = build_pptx(
                            result,
                            theme_name=theme_name,
                            reference_images=reference_payload
                        )

                        st.session_state.media_pdf_bytes = build_pdf(
                            result,
                            report_title=report_title
                        )
                        if st.session_state.media_project_id:
                            save_generated_files(
                                USER_ID,
                                st.session_state.media_project_id,
                                ppt_bytes=st.session_state.media_ppt_bytes,
                                pdf_bytes=st.session_state.media_pdf_bytes
                        )
                    st.success("PPT와 PDF 생성이 완료되었습니다.")

                except Exception as e:
                    st.session_state.media_ppt_bytes = None
                    st.session_state.media_pdf_bytes = None
                    st.error(f"PPT/PDF 생성 중 오류가 발생했습니다: {e}")

            if st.session_state.media_ppt_bytes or st.session_state.media_pdf_bytes:
                ppt_col, pdf_col = st.columns(2)

                with ppt_col:
                    if st.session_state.media_ppt_bytes:
                        st.download_button(
                            "📥 PPT 다운로드",
                            data=st.session_state.media_ppt_bytes,
                            file_name="AIAI_meeting_report.pptx",
                            mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                            use_container_width=True,
                            key="download_media_ppt"
                        )

                with pdf_col:
                    if st.session_state.media_pdf_bytes:
                        st.download_button(
                            "📥 PDF 다운로드",
                            data=st.session_state.media_pdf_bytes,
                            file_name="AIAI_meeting_report.pdf",
                            mime="application/pdf",
                            use_container_width=True,
                            key="download_media_pdf"
                        )    
   
