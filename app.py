import streamlit as st
from dotenv import load_dotenv

from agent import build_agent, MODEL_ID

load_dotenv()

st.set_page_config(page_title="SmolAgents + Streamlit", layout="centered")
st.title("SmolAgents Agent (HF Mistral 7B Instruct)")
st.caption(f"Model: {MODEL_ID}")

@st.cache_resource
def get_agent():
    return build_agent()

agent = get_agent()

if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    st.subheader("Controls")
    if st.button("Clear chat"):
        st.session_state.messages = []
        st.rerun()

# render history
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

user_text = st.chat_input("Ask me something…")
if user_text:
    st.session_state.messages.append({"role": "user", "content": user_text})
    with st.chat_message("user"):
        st.markdown(user_text)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        placeholder.markdown("Thinking…")

        try:
            # CodeAgent uses .run()
            answer = agent.run(user_text)
        except Exception as e:
            answer = f"Error: {e}"

        placeholder.markdown(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer})
