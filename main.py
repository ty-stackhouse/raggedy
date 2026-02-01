import os
from typing import List

import streamlit as st
from github import Github
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores.faiss import FAISS
from langchain_openai import ChatOpenAI
from langchain.schema import AIMessage, HumanMessage

# App configuration from secrets
st.set_page_config(page_title=st.secrets.get("APP_TITLE", "RAG Chat"), layout="wide")

# OpenRouter configuration
os.environ["OPENAI_API_BASE"] = "https://openrouter.ai/api/v1"
os.environ["OPENAI_API_KEY"] = st.secrets["OPENROUTER_API_KEY"]

@st.cache_resource(ttl=24*3600)
def load_knowledge_base() -> FAISS:
    """Load and process GitHub markdown files into a FAISS vector store."""
    # Initialize GitHub client
    g = Github(st.secrets["GITHUB_TOKEN"])
    repo = g.get_repo(st.secrets["GITHUB_REPO"])
    base_path = st.secrets.get("GITHUB_FOLDER", "")
    
    # Fetch all markdown files
    documents = []
    contents = repo.get_contents(base_path)
    while contents:
        content_file = contents.pop(0)
        if content_file.type == "dir":
            contents.extend(repo.get_contents(content_file.path))
        elif content_file.name.endswith(".md"):
            documents.append({
                "content": content_file.decoded_content.decode(),
                "source": content_file.path
            })
    
    # Create embeddings and vector store
    embeddings = OpenAIEmbeddings(
        model="openai/text-embedding-3-small",
        headers={
            "HTTP-Referer": st.secrets.get("APP_URL", "localhost"),
            "X-Title": st.secrets.get("APP_TITLE", "RAG Chat")
        }
    )
    
    texts = [doc["content"] for doc in documents]
    metadatas = [{"source": doc["source"]} for doc in documents]
    
    vectorstore = FAISS.from_texts(
        texts=texts,
        embedding=embeddings,
        metadatas=metadatas
    )
    
    st.session_state["doc_count"] = len(documents)
    return vectorstore

def initialize_chat() -> None:
    """Initialize chat session state variables."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
        system_prompt = st.secrets.get("SYSTEM_PROMPT", "You are a helpful AI assistant.")
        st.session_state.messages.append(AIMessage(content=system_prompt))

def main():
    initialize_chat()
    
    # Sidebar
    with st.sidebar:
        st.title("📚 Knowledge Base")
        if st.button("🔄 Refresh Data"):
            st.cache_resource.clear()
        
        vectorstore = load_knowledge_base()
        st.info(f"📑 Indexed {st.session_state.get('doc_count', 0)} documents")
    
    # Main chat interface
    st.title(st.secrets.get("APP_TITLE", "RAG Chat"))
    
    # Display chat messages
    for msg in st.session_state.messages[1:]:
        role = "assistant" if isinstance(msg, AIMessage) else "user"
        with st.chat_message(role):
            st.write(msg.content)
    
    # Chat input
    if prompt := st.chat_input():
        st.session_state.messages.append(HumanMessage(content=prompt))
        with st.chat_message("user"):
            st.write(prompt)
        
        # Search relevant documents
        docs = vectorstore.similarity_search(prompt, k=3)
        context = "\n\n".join(doc.page_content for doc in docs)
        
        # Generate response
        llm = ChatOpenAI(
            model="openai/gpt-4-turbo",
            headers={
                "HTTP-Referer": st.secrets.get("APP_URL", "localhost"),
                "X-Title": st.secrets.get("APP_TITLE", "RAG Chat")
            }
        )
        
        messages: List[HumanMessage | AIMessage] = [
            HumanMessage(content=f"Context:\n{context}\n\nQuestion: {prompt}")
        ]
        
        with st.chat_message("assistant"):
            response = llm.invoke(messages)
            st.session_state.messages.append(response)
            st.write(response.content)

if __name__ == "__main__":
    main()
