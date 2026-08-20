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
pending_todos = get_todos(show_completed=False)
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

tabs = st.tabs(["✉️ 이메일 작성", "✅ 할 일 관리", "📊 데이터 분석", "💼 채용 관리"])

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
                msg = add_todo(todo_title, todo_due, todo_priority)
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
                msg = complete_todo(todo_id)
                st.success(msg)
                st.rerun()
        with bcol2:
            if st.button("🗑️ 삭제", use_container_width=True, key="btn_delete_todo"):
                msg = delete_todo(todo_id)
                st.success(msg)
                st.rerun()

    with tcol2:
        show_all = st.checkbox("완료된 항목도 보기", key="chk_show_all_todos")
        todos = get_todos(show_completed=show_all)
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
                msg = add_job(j_company, j_pos, j_stat, j_dead, j_note)
                st.success(msg)
                st.rerun()
            else:
                st.warning("기업명과 직무를 입력해주세요.")

    with jcol2:
        jobs = get_jobs()
        if jobs:
            df_jobs = pd.DataFrame(jobs, columns=["ID", "기업명", "직무", "상태", "마감일", "메모"])
            st.dataframe(df_jobs, use_container_width=True, hide_index=True)
        else:
            st.info("등록된 채용 정보가 없습니다.")
