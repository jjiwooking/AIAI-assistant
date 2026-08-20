from modules.app_settings import get_texts
from modules.supabase_client import get_supabase

TEXT_DEFAULTS = {
    # 공통 / 로그인
    "app_title": ("공통", "앱 제목", "나만의 AI 비서"),
    "app_subtitle": ("공통", "앱 부제", "이메일 작성 · 할 일 관리 · 데이터 분석 · 회의·발표 분석"),
    "login_title": ("공통", "로그인 제목", "🤖 나만의 AI 비서"),
    "login_name_label": ("공통", "사용자 이름 입력", "사용자 이름"),
    "login_name_placeholder": ("공통", "사용자 이름 예시", "예: 홍길동"),
    "login_start_button": ("공통", "시작 버튼", "시작하기"),
    "login_name_warning": ("공통", "사용자 이름 경고", "사용자 이름을 입력해주세요."),
    "admin_tab_label": ("공통", "관리자 탭 이름", "⚙️ 관리자 설정"),

    # 인증
    "auth_login_tab": ("인증", "로그인 탭", "로그인"),
    "auth_signup_tab": ("인증", "회원가입 탭", "회원가입"),
    "auth_id_label": ("인증", "ID 입력 제목", "ID"),
    "auth_id_placeholder": ("인증", "ID 입력 예시", "예: anthony"),
    "auth_password_label": ("인증", "PASSWORD 입력 제목", "PASSWORD"),
    "auth_password_confirm_label": ("인증", "PASSWORD 확인 제목", "PASSWORD 확인"),
    "auth_display_name_label": ("인증", "이름 입력 제목", "이름"),
    "auth_display_name_placeholder": ("인증", "이름 입력 예시", "예: 홍길동"),
    "auth_login_button": ("인증", "로그인 버튼", "로그인"),
    "auth_signup_button": ("인증", "회원가입 버튼", "회원가입"),
    "auth_logout_button": ("인증", "로그아웃 버튼", "로그아웃"),
    "auth_welcome": ("인증", "로그인 사용자 표시", "{name}님"),

    # 메인 화면
    "home_pending_title": ("공통", "진행 중 할 일 제목", "📌 오늘 해야 할 일 ({count}건 진행 중)"),
    "home_all_done": ("공통", "할 일 완료 안내", "🎉 현재 진행 중인 할 일이 모두 완료되었습니다!"),
    "home_due_prefix": ("공통", "마감일 접두어", "마감"),
    "home_no_due": ("공통", "기한 없음 문구", "기한 없음"),
    "priority_high": ("공통", "높은 우선순위 표시", "🔴 높음"),
    "priority_normal": ("공통", "보통 우선순위 표시", "🟡 보통"),
    "priority_low": ("공통", "낮은 우선순위 표시", "🟢 낮음"),

    # 이메일
    "email_title": ("이메일", "화면 제목", "✉️ AI 비즈니스 이메일 작성"),
    "email_description": ("이메일", "화면 설명", "PDF/문서를 올리거나 짧은 메모만 입력해도 상황에 맞는 정식 비즈니스 이메일로 작성합니다."),
    "email_upload_label": ("이메일", "파일 업로드 문구", "📎 PDF 또는 참고 문서 업로드 (선택)"),
    "email_situation_label": ("이메일", "메모 입력 제목", "📝 메일로 만들 내용"),
    "email_situation_placeholder": ("이메일", "메모 입력 예시", "예: T131 일정이 촉박해서 먼저 보냈고, 나머지 Batch는 데이터 준비되는 대로 추가 송부 예정이라고 고객에게 알려줘"),
    "email_language_label": ("이메일", "출력 언어 제목", "🌐 출력 언어"),
    "email_expertise_label": ("이메일", "업무 전문 모드 제목", "🧩 업무 전문 모드 (복수 선택 가능)"),
    "email_purpose_label": ("이메일", "메일 목적 제목", "🎯 메일 목적"),
    "email_recipient_label": ("이메일", "수신 대상 제목", "👤 수신 대상"),
    "email_tone_label": ("이메일", "문체 제목", "🎭 문체"),
    "email_additional_label": ("이메일", "추가 요청 제목", "➕ 추가 요청 (선택)"),
    "email_additional_placeholder": ("이메일", "추가 요청 예시", "예: The reason why로 시작 / 다음 주 초 제공 예정이라고 표현 / 너무 길지 않게 / 제목도 3개 추천"),
    "email_generate_button": ("이메일", "생성 버튼", "✨ 정식 이메일로 작성"),
    "email_result_title": ("이메일", "결과 영역 제목", "📨 완성된 이메일"),
    "email_missing_input": ("이메일", "입력 누락 경고", "⚠️ 메일로 만들 내용을 입력하거나 참고 문서를 업로드해주세요."),
    "email_spinner": ("이메일", "생성 중 문구", "AI가 메모와 문서를 분석해 업무 상황에 맞는 정식 이메일을 작성 중입니다..."),
    "email_empty_guide": ("이메일", "결과 영역 안내", "왼쪽에 짧은 메모를 입력하거나 PDF/문서를 첨부한 뒤 '정식 이메일로 작성'을 눌러주세요."),

    # 할 일
    "todo_title": ("할 일", "화면 제목", "✅ 할 일 관리"),
    "todo_add_title": ("할 일", "새 할 일 제목", "➕ 새 할 일 추가"),
    "todo_input_label": ("할 일", "할 일 입력 제목", "할 일 제목"),
    "todo_input_placeholder": ("할 일", "할 일 입력 예시", "예: 이력서 업데이트"),
    "todo_due_label": ("할 일", "마감일 입력 제목", "마감일 (선택)"),
    "todo_due_placeholder": ("할 일", "마감일 입력 예시", "예: 2026-08-30"),
    "todo_priority_label": ("할 일", "우선순위 제목", "우선순위"),
    "todo_add_button": ("할 일", "할 일 추가 버튼", "➕ 할 일 추가"),
    "todo_missing_title": ("할 일", "할 일 미입력 경고", "할 일을 입력해주세요."),
    "todo_manage_title": ("할 일", "완료 삭제 제목", "🔧 완료 / 삭제"),
    "todo_id_label": ("할 일", "처리 ID 제목", "처리할 항목 ID"),
    "todo_complete_button": ("할 일", "완료 버튼", "✅ 완료 처리"),
    "todo_delete_button": ("할 일", "삭제 버튼", "🗑️ 삭제"),
    "todo_show_completed": ("할 일", "완료 항목 표시", "완료된 항목도 보기"),
    "todo_empty": ("할 일", "빈 목록 안내", "등록된 할 일이 없습니다."),
    "todo_col_id": ("할 일", "표 - ID", "ID"),
    "todo_col_title": ("할 일", "표 - 할 일", "할 일"),
    "todo_col_due": ("할 일", "표 - 마감일", "마감일"),
    "todo_col_priority": ("할 일", "표 - 우선순위", "우선순위"),
    "todo_col_status": ("할 일", "표 - 상태", "상태"),
    "todo_status_done": ("할 일", "완료 상태", "✅ 완료"),
    "todo_status_active": ("할 일", "진행 상태", "⏳ 진행중"),

    # 데이터 분석
    "data_title": ("데이터", "화면 제목", "📊 데이터 분석"),
    "data_description": ("데이터", "화면 설명", "CSV / Excel 데이터를 분석합니다."),
    "data_upload_label": ("데이터", "파일 업로드 문구", "📁 파일 업로드 (.csv / .xlsx / .xls)"),
    "data_info_title": ("데이터", "기본 정보 제목", "📊 데이터 기본 정보"),
    "data_question_label": ("데이터", "질문 입력 제목", "❓ 궁금한 점 (선택)"),
    "data_question_placeholder": ("데이터", "질문 입력 예시", "예: 매출이 가장 높은 달은? 어떤 상품이 제일 잘 팔려?"),
    "data_analyze_button": ("데이터", "분석 버튼", "📊 분석해줘!"),
    "data_spinner": ("데이터", "분석 중 문구", "AI가 데이터를 분석 중입니다..."),
    "data_result_title": ("데이터", "분석 결과 제목", "🤖 분석 결과"),
    "data_read_error": ("데이터", "파일 오류 문구", "파일을 읽는 중 오류가 발생했습니다: {error}"),
    "data_upload_guide": ("데이터", "파일 업로드 안내", "분석할 CSV 또는 Excel 파일을 업로드해주세요."),

    # 회의·발표 공통
    "media_title": ("회의·발표", "화면 제목", "🎙️ 회의·발표 분석"),
    "media_caption": ("회의·발표", "화면 설명", "음성·영상 → Transcript → 검토 → 요약 → 시각화 → PPT/PDF"),
    "media_saved_title": ("회의·발표", "저장 기록 제목", "저장된 회의·발표 분석"),
    "media_saved_empty": ("회의·발표", "저장 기록 없음", "저장된 회의·발표 분석이 없습니다."),
    "media_saved_select": ("회의·발표", "저장 기록 선택", "불러올 분석"),
    "media_load_button": ("회의·발표", "불러오기 버튼", "📂 불러오기"),
    "media_load_success": ("회의·발표", "불러오기 성공", "저장된 분석을 불러왔습니다."),
    "media_load_fail": ("회의·발표", "불러오기 실패", "저장된 분석을 불러오지 못했습니다."),

    # 회의·발표 내부 탭
    "media_tab_upload": ("회의·발표", "내부 탭 1", "1️⃣ 업로드·분석"),
    "media_tab_review": ("회의·발표", "내부 탭 2", "2️⃣ Transcript 검토"),
    "media_tab_summary": ("회의·발표", "내부 탭 3", "3️⃣ 요약·Action Item"),
    "media_tab_visual": ("회의·발표", "내부 탭 4", "4️⃣ 시각화"),
    "media_tab_export": ("회의·발표", "내부 탭 5", "5️⃣ PPT/PDF"),

    # 업로드·분석
    "media_upload_title": ("회의·발표", "파일 업로드 제목", "음성·영상 파일 업로드"),
    "media_upload_label": ("회의·발표", "음성 영상 파일 제목", "음성 또는 영상 파일"),
    "media_analysis_type_label": ("회의·발표", "분석 유형 제목", "분석 유형"),
    "media_analysis_meeting": ("회의·발표", "분석 유형 - 회의록", "회의록"),
    "media_analysis_presentation": ("회의·발표", "분석 유형 - 발표 요약", "발표 요약"),
    "media_analysis_executive": ("회의·발표", "분석 유형 - 경영진", "경영진 보고"),
    "media_analysis_customer": ("회의·발표", "분석 유형 - 고객", "고객사 보고"),
    "media_analysis_training": ("회의·발표", "분석 유형 - 교육", "교육 내용 정리"),
    "media_language_label": ("회의·발표", "언어 제목", "언어"),
    "media_language_mixed": ("회의·발표", "언어 - 한영 혼용", "한국어 + 영어 혼용"),
    "media_language_korean": ("회의·발표", "언어 - 한국어", "한국어 중심"),
    "media_language_english": ("회의·발표", "언어 - 영어", "영어 중심"),
    "media_glossary_label": ("회의·발표", "전문용어 사전 제목", "전문용어 사전"),
    "media_glossary_help": ("회의·발표", "전문용어 도움말", "회사명, 장비명, 약어 등을 쉼표로 구분해 입력하세요."),
    "media_reference_label": ("회의·발표", "참고 이미지 제목", "PPT에 사용할 참고 이미지 (선택)"),
    "media_start_button": ("회의·발표", "분석 시작 버튼", "🎙️ 음성·영상 분석 시작"),
    "media_file_warning": ("회의·발표", "파일 선택 경고", "분석할 음성 또는 영상 파일을 먼저 선택해주세요."),
    "media_analyze_spinner": ("회의·발표", "분석 중 문구", "AI가 음성·영상을 분석하고 있습니다. 긴 영상은 시간이 조금 걸릴 수 있습니다..."),
    "media_analyze_success": ("회의·발표", "분석 완료 문구", "분석이 완료되었습니다. Transcript 검토에서 내용을 확인해주세요."),
    "media_analyze_error": ("회의·발표", "분석 오류", "분석 중 오류가 발생했습니다: {error}"),
    "media_feature_title": ("회의·발표", "분석 기능 제목", "분석 기능"),
    "media_feature_list": ("회의·발표", "분석 기능 목록", "• 한국어/영어 혼용 Transcript\n• 회사 전문용어 자동 반영\n• 애매한 표현 색상 표시\n• 핵심 내용 자동 요약\n• Action Item 자동 추출\n• 숫자 및 일정 자동 추출\n• 차트 및 Timeline 생성\n• PPT/PDF 자동 생성"),
    "media_color_legend": ("회의·발표", "색상 안내", "🟡 노란색 = 확인 권장 · 🔴 빨간색 = 수정 권장"),

    # Transcript
    "media_review_empty": ("회의·발표", "Transcript 빈 화면 안내", "먼저 업로드·분석에서 파일을 분석해주세요."),
    "media_uncertain_title": ("회의·발표", "애매 표현 제목", "애매한 표현 확인"),
    "media_ai_correction_title": ("회의·발표", "AI 교정 제목", "AI 교정 후보"),
    "media_direct_edit_title": ("회의·발표", "직접 수정 제목", "Transcript 직접 수정"),
    "media_direct_edit_label": ("회의·발표", "직접 수정 안내", "필요한 문장을 직접 수정할 수 있습니다."),
    "media_transcript_save_button": ("회의·발표", "Transcript 저장 버튼", "💾 Transcript 수정 저장"),
    "media_transcript_saved": ("회의·발표", "Transcript 저장 완료", "수정 내용을 저장했습니다."),
    "media_rebuild_button": ("회의·발표", "다시 정리 버튼", "🔄 수정본 기준 다시 정리"),
    "media_rebuild_spinner": ("회의·발표", "다시 정리 중", "수정한 Transcript를 기준으로 다시 정리하고 있습니다..."),
    "media_rebuild_success": ("회의·발표", "다시 정리 완료", "수정한 내용 기준으로 다시 정리했습니다."),
    "media_rebuild_error": ("회의·발표", "다시 정리 오류", "재분석 중 오류가 발생했습니다: {error}"),

    # 요약
    "media_summary_empty": ("회의·발표", "요약 화면 빈 안내", "먼저 음성 또는 영상 파일을 분석해주세요."),
    "media_summary_title": ("회의·발표", "핵심 요약 제목", "핵심 요약"),
    "media_summary_none": ("회의·발표", "요약 없음", "추출된 요약 내용이 없습니다."),
    "media_action_title": ("회의·발표", "Action Item 제목", "Action Items"),
    "media_action_none": ("회의·발표", "Action Item 없음", "추출된 Action Item이 없습니다."),
    "media_keypoint_title": ("회의·발표", "중요 포인트 제목", "중요 포인트"),
    "media_keypoint_none": ("회의·발표", "중요 포인트 없음", "추출된 중요 포인트가 없습니다."),
    "media_summary_save_button": ("회의·발표", "요약 저장 버튼", "💾 요약·Action Item 저장"),
    "media_summary_saved": ("회의·발표", "요약 저장 완료", "요약과 Action Item을 저장했습니다."),

    # 시각화
    "media_visual_empty": ("회의·발표", "시각화 빈 안내", "먼저 음성 또는 영상 파일을 분석해주세요."),
    "media_visual_title": ("회의·발표", "자동 시각화 제목", "자동 시각화"),
    "media_chart_type_label": ("회의·발표", "차트 유형 제목", "차트 유형"),
    "media_chart_bar": ("회의·발표", "막대그래프 이름", "막대그래프"),
    "media_chart_line": ("회의·발표", "선그래프 이름", "선그래프"),
    "media_chart_table": ("회의·발표", "표 이름", "표"),
    "media_no_numbers": ("회의·발표", "수치 없음 안내", "음성·영상에서 확인된 수치가 없어 임의의 그래프를 만들지 않았습니다."),
    "media_timeline_title": ("회의·발표", "Timeline 제목", "Timeline / Process"),
    "media_slide_plan_title": ("회의·발표", "슬라이드 제안 제목", "AI 슬라이드 구성 제안"),
    "media_visual_save_button": ("회의·발표", "시각화 저장 버튼", "💾 시각화 수정 저장"),
    "media_visual_saved": ("회의·발표", "시각화 저장 완료", "시각화 수정 내용을 저장했습니다."),

    # PPT/PDF
    "media_export_empty": ("회의·발표", "PPT/PDF 빈 안내", "먼저 음성 또는 영상 파일을 분석해주세요."),
    "media_export_title": ("회의·발표", "PPT PDF 제목", "PPT / PDF 생성"),
    "media_ppt_design_label": ("회의·발표", "PPT 디자인 제목", "PPT 디자인"),
    "media_report_title_label": ("회의·발표", "보고서 제목 입력", "보고서 제목"),
    "media_report_title_default": ("회의·발표", "기본 보고서 제목", "회의·발표 분석"),
    "media_export_caption": ("회의·발표", "파일 생성 안내", "PPT/PDF를 생성하기 전에 Transcript, 요약, Action Item, 시각화를 최종 확인해주세요."),
    "media_generate_button": ("회의·발표", "PPT PDF 생성 버튼", "✨ PPT / PDF 파일 생성"),
    "media_export_spinner": ("회의·발표", "PPT PDF 생성 중", "PPT와 PDF를 생성하고 있습니다..."),
    "media_export_success": ("회의·발표", "PPT PDF 생성 완료", "PPT와 PDF 생성이 완료되었습니다."),
    "media_export_error": ("회의·발표", "PPT PDF 생성 오류", "PPT/PDF 생성 중 오류가 발생했습니다: {error}"),
    "media_ppt_download": ("회의·발표", "PPT 다운로드 버튼", "📥 PPT 다운로드"),
    "media_pdf_download": ("회의·발표", "PDF 다운로드 버튼", "📥 PDF 다운로드"),

    # 관리자
    "admin_title": ("관리자", "관리자 제목", "⚙️ 관리자 설정"),
    "admin_caption": ("관리자", "관리자 설명", "탭 이름, 아이콘, 순서, 표시 여부와 앱 문구를 직접 수정할 수 있습니다."),
    "admin_tab_name_label": ("관리자", "탭 이름 입력", "탭 이름"),
    "admin_icon_label": ("관리자", "아이콘 입력", "아이콘"),
    "admin_order_label": ("관리자", "순서 입력", "순서"),
    "admin_visible_label": ("관리자", "표시 토글", "탭 표시"),
    "admin_save_button": ("관리자", "탭 저장 버튼", "💾 저장"),
    "admin_save_success": ("관리자", "탭 저장 완료", "설정을 저장했습니다."),
    "admin_no_tabs": ("관리자", "탭 설정 없음", "등록된 탭 설정이 없습니다."),
    "admin_text_title": ("관리자", "문구 관리 제목", "✏️ 앱 문구 관리"),
    "admin_text_caption": ("관리자", "문구 관리 설명", "앱에서 사용하는 문구를 카테고리별로 직접 수정할 수 있습니다."),
    "admin_category_label": ("관리자", "문구 카테고리", "문구 카테고리"),
    "admin_text_value_label": ("관리자", "표시 문구 입력", "표시 문구"),
    "admin_text_save_button": ("관리자", "문구 저장 버튼", "💾 문구 저장"),
    "admin_text_save_success": ("관리자", "문구 저장 완료", "문구를 저장했습니다."),
    "admin_no_texts": ("관리자", "문구 설정 없음", "등록된 문구 설정이 없습니다.")
}


def ensure_text_defaults():
    """Supabase app_texts에 없는 기본 문구만 자동 등록합니다."""
    try:
        response = get_supabase().table("app_texts").select("text_key").execute()
        existing = {row["text_key"] for row in (response.data or [])}
        missing = [
            {"text_key": key, "category": category, "label": label, "value": value}
            for key, (category, label, value) in TEXT_DEFAULTS.items()
            if key not in existing
        ]
        if missing:
            get_supabase().table("app_texts").insert(missing).execute()
    except Exception:
        pass


def load_text_map():
    """앱 문구를 한 번에 읽어 dict로 반환합니다."""
    return {
        item["text_key"]: item.get("value", "")
        for item in get_texts()
    }


def get_text_value(text_map, key, default):
    value = text_map.get(key, "")
    return value if value else default
