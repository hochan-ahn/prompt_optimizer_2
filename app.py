import os
import streamlit as st
from groq import Groq

# --- 1. 시스템 프롬프트 설정 (우리가 만든 최적화 로직) ---
SYSTEM_PROMPT = """
## Role & Objective
당신은 Google Gemini API 및 LLM 활용에 통달한 **'수석 프롬프트 엔지니어(Chief Prompt Engineer)'**입니다. 
당신의 목표는 사용자의 요청을 분석하여, 상황에 맞춰 내용을 갈아 끼울 수 있는 **'최적화된 프롬프트 템플릿'**을 설계해 주는 것입니다.

## Optimization Guidelines
1. **변수 분리 (Variable Isolation):** 사용자의 입력이 구체적이지 않다면 절대로 임의로 내용을 채우지 말고, `# Input Data` 섹션에 변수 형태로 비워두십시오.
2. **명확한 지시:** 모델이 수행해야 할 작업의 본질적인 논리 구조를 설계하십시오.
3. **페르소나 부여:** 작업에 가장 적합한 전문가 페르소나를 정의하십시오.
4. **구분자 사용:** 섹션을 명확히 구분하십시오.

## Output Format (CRITICAL)
**중요: 답변 출력 시 Markdown Code Block(```)을 사용하지 말고, 인용구(>)를 사용하여 시각적으로 구분하십시오.**
`# Input Data` 섹션은 사용자가 복사 후 내용을 채워 넣을 수 있도록 안내 문구로 작성해야 합니다.

---
### 🔍 분석 및 개선 포인트
* **적용된 전략:** (예: 변수 분리, 구조화 등)
* **개선 이유:** (이유 설명)

### ✨ 최적화된 프롬프트
> # Role
> [역할 정의]
>
> # Context
> [배경 설명]
>
> # Task
> [구체적인 작업 지시]
>
> # Constraints
> [제약 조건]
>
> # Output Format
> [출력 형식]
>
> # Input Data
> - **[변수명 1]:** [입력 안내]
> - **[변수명 2]:** [입력 안내]
---
"""

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


# --- 2. 페이지 기본 설정 ---
st.set_page_config(
    page_title="프롬프트 최적화 봇 (Groq)",
    page_icon="✨",
    layout="wide"
)

st.title("✨ 프롬프트 엔지니어링 봇 (Powered by Groq)")
st.markdown("대충 적은 프롬프트를 입력하면, **고성능 프롬프트 템플릿**으로 업그레이드해 드립니다.")

# --- 3. 서버에만 API 키를 두고, 모든 사용자가 공용으로 사용 ---
with st.sidebar:
    st.header("⚙️ 설정")

    model_option = st.selectbox(
        "모델 선택",
        ("meta-llama/llama-4-maverick-17b-128e-instruct", "llama-3.3-70b-versatile", "llama-3.1-8b-instant", "qwen/qwen3-32b"),
        index=0
    )
    st.info("이 앱은 **서버에 저장된 공용 Groq API 키**로 동작하며, 사용자는 키를 입력할 필요가 없습니다.")

# 서버 측에서만 API 키 로드 (.streamlit/secrets.toml 또는 환경변수)
groq_api_key = None
try:
    groq_api_key = st.secrets["GROQ_API_KEY"]
except Exception:
    groq_api_key = os.getenv("GROQ_API_KEY")

if not groq_api_key:
    st.error(
        "서버에 Groq API Key가 설정되어 있지 않습니다.\n\n"
        "- `.streamlit/secrets.toml` 에 `GROQ_API_KEY=\"...\"` 를 추가하거나\n"
        "- OS 환경변수 `GROQ_API_KEY` 를 설정해 주세요.\n\n"
        "이 설정은 **서버 배포 시 한 번만** 해주면, 이후 모든 사용자가 별도 입력 없이 사용 가능합니다."
    )
    st.stop()

# Groq 클라이언트 초기화 (공용 서버 키 사용)
try:
    client = Groq(api_key=groq_api_key)
except Exception as e:
    st.error(f"API 연결 오류: {e}")
    st.stop()

# 세션 상태 초기화: 항상 "이번 질답 1세트"만 유지
if "messages" not in st.session_state:
    st.session_state.messages = []

# 사용자 입력
user_input = st.chat_input("프롬프트를 입력하세요 (예: 여행 계획 짜주는 봇 만들어줘)")

if user_input:
    # 새로운 질문이 들어오면 바로 이전 대화/맥락 삭제
    st.session_state.messages = []

    # 사용자 말풍선
    with st.chat_message("user"):
        st.markdown(user_input)

    # Groq로 보낼 메시지 구성 (시스템 + 사용자)
    payload_messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_input},
    ]

    with st.spinner("생각 중..."):
        try:
            completion = client.chat.completions.create(
                model=model_option,
                messages=payload_messages,
                temperature=0.7,
                max_tokens=2048,
                stream=False,
            )
            assistant_message = completion.choices[0].message.content

            # 상태에 이번 질답 저장
            st.session_state.messages.append(
                {"role": "assistant", "content": assistant_message}
            )

            # 상태 반영하여 다시 그리기
            st.rerun()

        except Exception as e:
            st.error(f"에러가 발생했습니다: {e}")

# (사용자 입력 이후 rerun 된 화면에서) 질답 1세트만 출력
for message in st.session_state.messages:
    with st.chat_message("assistant"):
        marker = "### ✨ 최적화된 프롬프트"
        content = message["content"]
        if marker in content:
            pre, post = content.split(marker, 1)
            # 설명 부분이 있으면 마크다운으로 출력
            if pre.strip():
                st.markdown(pre)
            # "최적화된 프롬프트" 이하를 코드블록(마크다운)으로 표시하되 '>' 제거
            block = strip_blockquote_prefix(f"{marker}{post}")
            st.code(block, language="markdown")
        else:
            # 마커가 없으면 전체를 코드블록으로
            block = strip_blockquote_prefix(content)
            st.code(block, language="markdown")



