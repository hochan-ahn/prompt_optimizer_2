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

# --- 2. 페이지 기본 설정 ---
st.set_page_config(
    page_title="프롬프트 최적화 봇 (Gemma 3)",
    page_icon="✨",
    layout="wide"
)

st.title("✨ 프롬프트 엔지니어링 봇 (Powered by Groq)")
st.markdown("대충 적은 프롬프트를 입력하면, **고성능 프롬프트 템플릿**으로 업그레이드해 드립니다.")

# --- 3. 사이드바: 설정 및 API 키 입력 (BYOK 방식) ---
with st.sidebar:
    st.header("⚙️ 설정")
    groq_api_key = st.text_input("Groq API Key 입력", type="password", help="[https://console.groq.com/keys](https://console.groq.com/keys) 에서 무료 발급 가능")
    
    # 모델 선택 (Gemma 3가 아직 목록에 없다면 gemma2-9b-it 사용 권장)
    model_option = st.selectbox(
        "모델 선택",
        ("gemma2-9b-it", "llama-3.3-70b-versatile", "mixtral-8x7b-32768"),
        index=0
    )
    st.info(f"선택된 모델: `{model_option}`\n\n(참고: Gemma 3가 Groq에 업데이트되면 코드 내 모델명을 변경하세요.)")
    
    st.markdown("---")
    st.markdown("### 💡 사용 팁")
    st.markdown("1. 만들고 싶은 기능을 대충 설명하세요.")
    st.markdown("2. 예: *'블로그 글 쓰는 봇 만들어줘'*, *'영어 이메일 교정해줘'*")

# --- 4. 메인 로직 ---

# API 키 확인
if not groq_api_key:
    st.warning("왼쪽 사이드바에 **Groq API Key**를 입력해야 시작할 수 있습니다.")
    st.stop()

# 클라이언트 초기화
try:
    client = Groq(api_key=groq_api_key)
except Exception as e:
    st.error(f"API 연결 오류: {e}")
    st.stop()

# 세션 상태 초기화 (대화 기록)
if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ]

# --- 5. 대화 화면 출력 ---
# 시스템 메시지는 숨기고, 사용자/어시스턴트 대화만 표시
for msg in st.session_state.messages:
    if msg["role"] != "system":
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

# --- 6. 사용자 입력 처리 ---
if prompt := st.chat_input("프롬프트를 입력하세요 (예: 여행 계획 짜주는 봇 만들어줘)"):
    # 1) 사용자 메시지 UI 표시 및 저장
    st.chat_message("user").write(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # 2) Groq API 호출 및 스트리밍 응답
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        try:
            stream = client.chat.completions.create(
                messages=st.session_state.messages,
                model=model_option,
                temperature=0.7, # 창의성 조절
                max_tokens=2048,
                stream=True,
            )
            
            # 스트리밍 청크 받아서 실시간 출력
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    message_placeholder.markdown(full_response + "▌")
            
            # 최종 완성본 출력 (커서 제거)
            message_placeholder.markdown(full_response)
            
            # 3) 어시스턴트 메시지 저장
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            
        except Exception as e:
            st.error(f"에러가 발생했습니다: {e}")
