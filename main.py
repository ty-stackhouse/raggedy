import logging
import streamlit as st
from langchain_core.messages import AIMessage, HumanMessage

# Configure logging
logging.basicConfig(level=logging.INFO)
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

    logger.info("Calling external API for assistant response...")
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        assistant_response = "Hello! I'm Raggedy. How can I help you today?"
        full_response += assistant_response
        message_placeholder.markdown(full_response + "▌")
        message_placeholder.markdown(full_response)
    logger.info(f"Received assistant response: {assistant_response[:100]}...")
    st.session_state.messages.append({"role": "assistant", "content": assistant_response})
