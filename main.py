import logging
import time
import streamlit as st
from langchain_core.messages import AIMessage, HumanMessage

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

st.title("Raggedy")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("What is up?"):
    logger.info(f"Received user message: {prompt[:100]}...")
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    logger.info(f"Calling external API: POST https://openrouter.ai/api/v1/chat/completions")
    logger.info(f"Request: model=google/gemini-1.5-flash, messages={len(st.session_state.messages)}")
    start_time = time.time()
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        assistant_response = "Hello! I'm Raggedy. How can I help you today?"
        full_response += assistant_response
        message_placeholder.markdown(full_response + "▌")
        message_placeholder.markdown(full_response)
    elapsed_ms = (time.time() - start_time) * 1000
    logger.info(f"API response received in {elapsed_ms:.2f}ms")
    logger.info(f"Response: {assistant_response[:100]}...")
    st.session_state.messages.append({"role": "assistant", "content": assistant_response})
