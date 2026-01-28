"""
Streamlit web interface for the agent.
Run with: streamlit run app.py
"""
import streamlit as st
from dotenv import load_dotenv
from agent import build_agent, MODEL_ID
import signal
from contextlib import contextmanager
import time

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="SmolAgents + Streamlit",
    page_icon="🤖",
    layout="centered"
)


# @contextmanager
# def timeout(seconds):
#     """Context manager for timeout (Unix only)"""
#     def timeout_handler(signum, frame):
#         raise TimeoutError("Agent execution timed out")
    
#     # Only works on Unix systems
#     try:
#         signal.signal(signal.SIGALRM, timeout_handler)
#         signal.alarm(seconds)
#         try:
#             yield
#         finally:
#             signal.alarm(0)
#     except AttributeError:
#         # Windows doesn't have SIGALRM, just yield without timeout
#         yield


@st.cache_resource
def get_agent():
    """Build and cache the agent"""
    return build_agent(verbose=1)


# Header
st.title("🤖 SmolAgents Agent")
st.caption(f"📦 Model: {MODEL_ID}")

# Initialize agent
try:
    agent = get_agent()
except Exception as e:
    st.error(f"❌ Failed to build agent: {e}")
    st.info("💡 Make sure you have set HUGGINGFACEHUB_API_TOKEN in your .env file")
    st.stop()

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Sidebar
with st.sidebar:
    st.subheader("🎛️ Controls")
    
    if st.button("🗑️ Clear chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    
    st.divider()
    
    st.subheader("💭 Example Questions")
    st.markdown("""
    - What time is it in Europe/Berlin?
    - What time is it in Tokyo?
    - Count words in "Hello world"
    - What time is it in New York and London?
    """)
    
    st.divider()
    
    st.subheader("🛠️ Available Tools")
    st.markdown("""
    - **get_time**: Get current time in any timezone
    - **word_count**: Count words in text
    """)

# Render chat history
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# Chat input
user_text = st.chat_input("Ask me something…")

if user_text:
    # Add user message to history
    st.session_state.messages.append({"role": "user", "content": user_text})
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(user_text)
    
    # Generate and display assistant response
    with st.chat_message("assistant"):
        placeholder = st.empty()
        placeholder.markdown("🤔 Thinking…")
        
        start_time = time.time()
        
        try:
            # Try to use timeout (Unix only)
        #     with timeout(120):  # 2 minute timeout
        #         answer = agent.run(user_text)
            
        #     elapsed = time.time() - start_time
        #     placeholder.markdown(f"{answer}\n\n*Took {elapsed:.1f}s*")
            
        # except TimeoutError:
        #     answer = "⏱️ The agent took too long to respond. Please try a simpler question or try again."
        #     placeholder.markdown(answer)

         # Simply run the agent without signal-based timeout
            # The timeout in agent.py (90s) will handle long-running requests
            answer = agent.run(user_text)
            elapsed = time.time() - start_time
            placeholder.markdown(f"{answer}\n\n*Took {elapsed:.1f}s*")
            
        except Exception as e:
            answer = f"❌ Error: {str(e)}"
            placeholder.markdown(answer)
            
            # Show detailed error in expander
            with st.expander("🔍 See detailed error"):
                st.code(repr(e))
        
        # Add assistant message to history
        st.session_state.messages.append({"role": "assistant", "content": answer})