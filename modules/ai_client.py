import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

def get_ai_response(prompt_or_contents, system_prompt: str = "") -> str:
    """Google Gemini API를 호출해 AI 응답을 반환합니다. (텍스트, PDF 바이트, 이미지 등 멀티모달 지원)"""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        try:
            import streamlit as st
            api_key = st.secrets.get("GEMINI_API_KEY", "")
        except Exception:
            pass

    if not api_key or api_key == "여기에_API_키를_입력하세요":
        return (
            "❌ GEMINI_API_KEY가 설정되지 않았습니다.\n\n"
            "📌 설정 방법:\n"
            "1. https://aistudio.google.com/apikey 접속\n"
            "2. API 키 발급 (무료)\n"
            "3. .env 파일 또는 Streamlit Secrets에 입력:\n"
            "   GEMINI_API_KEY=발급받은키"
        )
    try:
        client = genai.Client(api_key=api_key)
        config = {}
        if system_prompt:
            config["system_instruction"] = system_prompt

        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt_or_contents,
            config=config if config else None
        )
        return response.text
    except Exception as e:
        return f"❌ AI 오류가 발생했습니다: {str(e)}"
