import logging
import time
import os
import requests
from github import Github
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores.faiss import FAISS
import streamlit as st
from langchain_core.messages import AIMessage, HumanMessage

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@st.cache_resource(ttl=24 * 3600)
def load_knowledge_base() -> FAISS:
    """Load and process GitHub markdown files into a FAISS vector store."""
    logger.info("Loading knowledge base from GitHub...")

    try:
        g = Github(st.secrets["GITHUB_TOKEN"])
        repo_path = st.secrets["GITHUB_REPO"]
        logger.info(f"Fetching repo: {repo_path}")

        repo = g.get_repo(repo_path)
        base_path = st.secrets.get("GITHUB_FOLDER", "")
        logger.info(f"Base path: {base_path}")

        # Fetch all markdown files
        documents = []
        contents = repo.get_contents(base_path)
        while contents:
            content_file = contents.pop(0)
            logger.debug(f"Processing: {content_file.path} (type: {content_file.type})")
            if content_file.type == "dir":
                contents.extend(repo.get_contents(content_file.path))
            elif content_file.name.endswith(".md"):
                logger.info(f"Found markdown file: {content_file.path}")
                documents.append({
                    "content": content_file.decoded_content.decode(),
                    "source": content_file.path
                })

        logger.info(f"Total markdown files found: {len(documents)}")

        if not documents:
            logger.warning("No markdown files found in repository")
            return None

        # Create embeddings using OpenRouter
        logger.info("Creating embeddings via OpenRouter...")
        openrouter_api_key = st.secrets.get("OPENROUTER_API_KEY")
        embeddings = OpenAIEmbeddings(
            model="openai/text-embedding-3-small",
            openai_api_key=openrouter_api_key,
            openai_api_base="https://openrouter.ai/api/v1",
            headers={
                "HTTP-Referer": st.secrets.get("APP_URL", "localhost"),
                "X-Title": st.secrets.get("APP_TITLE", "Raggedy")
            }
        )

        texts = [doc["content"] for doc in documents]
        metadatas = [{"source": doc["source"]} for doc in documents]

        logger.info(f"Building FAISS index from {len(texts)} documents...")
        vectorstore = FAISS.from_texts(
            texts=texts,
            embedding=embeddings,
            metadatas=metadatas
        )

        logger.info(f"Knowledge base loaded: {len(documents)} documents indexed")
        return vectorstore

    except Exception as e:
        logger.error(f"Failed to load knowledge base: {type(e).__name__}: {str(e)}")
        return None


def search_knowledge_base(vectorstore: FAISS, query: str, k: int = 5) -> list:
    """Search the knowledge base for relevant documents."""
    logger.info(f"Searching knowledge base for: {query[:100]}...")
    logger.info(f"Search parameters: k={k}")

    try:
        docs = vectorstore.similarity_search(query, k=k)
        logger.info(f"Found {len(docs)} relevant documents")
        for i, doc in enumerate(docs):
            logger.info(f"  Doc {i+1}: {doc.metadata.get('source', 'unknown')} (score: {doc.page_content[:50]}...)")
        return docs
    except Exception as e:
        logger.error(f"Search failed: {type(e).__name__}: {str(e)}")
        return []


st.title(st.secrets.get("APP_NAME", "Raggedy"))

# Load knowledge base at app startup
logger.info("Loading knowledge base at startup...")
vectorstore = load_knowledge_base()
if vectorstore:
    logger.info("Knowledge base loaded successfully at startup")
else:
    logger.warning("Knowledge base failed to load at startup")

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

    # Search knowledge base for relevant context
    logger.info("Searching knowledge base...")
    context = ""
    if vectorstore:
        docs = search_knowledge_base(vectorstore, prompt, k=5)
        if docs:
            context = "\n\n".join(doc.page_content for doc in docs)
            logger.info(f"Retrieved {len(docs)} documents for context")
            logger.info(f"Context length: {len(context)} characters")
        else:
            logger.warning("No relevant documents found in knowledge base")
    else:
        logger.warning("Knowledge base not available, proceeding without context")

    # Build system prompt with context
    system_prompt = st.secrets.get("SYSTEM_PROMPT", "You are a helpful AI assistant.")
    if context:
        system_prompt = f"""You are a helpful AI assistant. Use the following context from the knowledge base to answer the user's question. If the context doesn't contain relevant information, you can answer based on your general knowledge.

Knowledge Base Context:
{context}
"""
        logger.info("Including knowledge base context in request")

    logger.info(f"Calling external API: POST https://openrouter.ai/api/v1/chat/completions")
    logger.info(f"Request: model=google/gemini-2.0-flash-001, messages={len(st.session_state.messages)}")

    # Prepare API request
    api_key = st.secrets.get("OPENROUTER_API_KEY")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": st.secrets.get("APP_URL", "localhost"),
        "X-Title": st.secrets.get("APP_TITLE", "Raggedy"),
    }
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend([{"role": m["role"], "content": m["content"]} for m in st.session_state.messages])
    payload = {
        "model": "google/gemini-2.0-flash-001",
        "messages": messages,
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
