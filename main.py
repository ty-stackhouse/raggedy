import logging
import time
import os
import requests
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

    # Prepare API request
    api_key = st.secrets.get("OPENROUTER_API_KEY")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": st.secrets.get("APP_URL", "localhost"),
        "X-Title": st.secrets.get("APP_TITLE", "Raggedy"),
    }
    payload = {
        "model": "google/gemini-1.5-flash",
        "messages": [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
        "max_tokens": 1024,
    }
    logger.info(f"Request headers: {list(headers.keys())}")
    logger.info(f"Request body: {payload}")

    start_time = time.time()
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        elapsed_ms = (time.time() - start_time) * 1000
        logger.info(f"API response: status={response.status_code}, time={elapsed_ms:.2f}ms")
        logger.info(f"Response headers: {dict(response.headers)}")

        if response.status_code == 200:
            response_data = response.json()
            assistant_response = response_data["choices"][0]["message"]["content"]
            logger.info(f"Response content: {assistant_response[:200]}...")
        else:
            logger.error(f"API error: {response.status_code} - {response.text}")
            assistant_response = f"Error: API request failed with status {response.status_code}"
    except requests.exceptions.Timeout:
        logger.error("API request timed out after 30s")
        assistant_response = "Error: Request timed out"
    except Exception as e:
        logger.error(f"API request failed: {type(e).__name__}: {str(e)}")
        assistant_response = f"Error: {type(e).__name__}"

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = assistant_response
        message_placeholder.markdown(full_response + "▌")
        message_placeholder.markdown(full_response)
    st.session_state.messages.append({"role": "assistant", "content": assistant_response})
