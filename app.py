import streamlit as st
import google.generativeai as genai

# 페이지 설정
st.set_page_config(
    page_title="프롬프트 개선 테스트",
    page_icon="🤑",
    layout="wide"
)

# Blockquote 제거 유틸 (코드블록 출력 시 '>' 접두어 제거)
def strip_blockquote_prefix(text: str) -> str:
    lines = text.splitlines()
    cleaned = []
    for line in lines:
        if line.startswith("> "):
            cleaned.append(line[2:])
        elif line.startswith(">"):
            cleaned.append(line[1:])
        else:
            cleaned.append(line)
    return "\n".join(cleaned)

# CSS 스타일 적용
st.markdown("""
<style>
    .stApp {
        background-color: #f5f5f5;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        line-height: 1.5;
    }
    .user-message {
        background-color: #e3f2fd;
        border-left: 5px solid #2196f3;
    }
    .bot-message {
        background-color: #f3e5f5;
        border-left: 5px solid #9c27b0;
    }
    .main-title {
        color: #6a1b9a;
        text-align: center;
        padding: 2rem 0;
        font-size: 2.5rem;
        font-weight: bold;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }
    .description {
        text-align: center;
        color: #666;
        font-size: 1.2rem;
        margin-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# 제목과 설명
st.markdown('<h1 class="main-title">프롬프트 개선 테스트</h1>', unsafe_allow_html=True)
st.markdown('<p class="description">프롬프트 개선 테스트용 페이지입니다.</p>', unsafe_allow_html=True)

# Gemini API 설정
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
except Exception as e:
    st.error("API 키를 설정해주세요! (.streamlit/secrets.toml 파일에 GOOGLE_API_KEY를 추가해주세요)")
    st.stop()

# 모델 설정
model = genai.GenerativeModel('gemini-1.5-flash')

# 세션 상태 초기화
if "chat" not in st.session_state:
    st.session_state.chat = model.start_chat(history=[])
    st.session_state.messages = []
    # 초기 메시지 추가
    initial_message = "프롬프트를 입력해주세요"
    st.session_state.messages.append({"role": "assistant", "content": initial_message})

# 사용자 입력 (chat_input으로 말풍선 UX)
user_input = st.chat_input("문제나 답변을 입력해주세요")

if user_input:
    # 새 질문이 들어오면 즉시 이전 대화/맥락 삭제 후 새 세션으로 시작
    st.session_state.chat = model.start_chat(history=[])
    st.session_state.messages = []

    # 사용자 메시지 즉시 표시
    with st.chat_message("user"):
        st.markdown(user_input)

    # 챗봇 프롬프트 설정
    prompt = """
    ## Role & Objective
당신은 Google Gemini API 및 LLM 활용에 통달한 **'수석 프롬프트 엔지니어(Chief Prompt Engineer)'**입니다. 
당신의 목표는 사용자가 입력한 프롬프트를 Google의 [Prompting Strategies] 가이드라인에 부합하는 **'최적화된 프롬프트'**로 재작성하는 것입니다.

## Optimization Guidelines
1. **명확한 지시:** 모호함을 제거하고 구체적 행동을 지시합니다.
2. **페르소나 부여:** 모델의 역할을 정의합니다.
3. **구분자 사용:** 텍스트 간 경계를 명확히 합니다. (단, 코드 오류 방지를 위해 Backticks 대신 헤더나 특수기호를 권장합니다.)
4. **단계적 사고:** 복잡한 작업은 단계별 추론을 유도합니다.
5. **형식 지정:** 입력과 출력의 형식을 정의합니다.

## Operational Process
1. 사용자 입력 의도 파악
2. 약점 진단 (모호함, 맥락 부재 등)
3. 재작성 (Optimization Guidelines 적용)
4. 전략 설명

## Output Format (CRITICAL)
**중요: 답변을 출력할 때 Markdown Code Block(```)을 사용하지 마십시오.**
대신, 최적화된 프롬프트 내용은 **인용구(Blockquote, `>`)** 형식을 사용하여 시각적으로 구분되게 출력하십시오.

---
### 🔍 분석 및 개선 포인트
* **적용된 전략:** (전략 명시)
* **개선 이유:** (이유 설명)

### ✨ 최적화된 프롬프트
> # Role
> [역할 정의]
>
> # Context
> [배경 설명]
>
> # Task
> [작업 지시]
>
> # Constraints
> [제약 조건]
>
> # Output Format
> [출력 형식]
>
> # Input Data
> {{입력 데이터}}
---

## Initialization
지금부터 사용자가 입력하는 텍스트를 분석하고, 위 형식에 맞춰 코드 블록 없이 최적화된 프롬프트 내용만 반환하십시오.

"""

    with st.spinner("생각 중..."):
        try:
            # Gemini 모델에 메시지 전송
            response = st.session_state.chat.send_message(f"{prompt}\n\n사용자: {user_input}")
            assistant_message = response.text

            # 챗봇 메시지 상태에 저장
            st.session_state.messages.append({"role": "assistant", "content": assistant_message})

            # 응답이 준비되면 새 상태로 다시 렌더링
            st.rerun()

        except Exception as e:
            st.error(f"오류가 발생했습니다: {str(e)}")

# 채팅 히스토리 표시 (말풍선 형태로 교차 출력)
for message in st.session_state.messages:
    with st.chat_message("user" if message["role"] == "user" else "assistant"):
        if message["role"] == "assistant":
            marker = "### ✨ 최적화된 프롬프트"
            if marker in message["content"]:
                pre, post = message["content"].split(marker, 1)
                if pre.strip():
                    st.markdown(pre)
                block = strip_blockquote_prefix(f"{marker}{post}")
                st.code(block, language="markdown")
            else:
                st.code(strip_blockquote_prefix(message["content"]), language="markdown")
        else:
            st.markdown(message["content"])