# RAG Application

A production-ready RAG (Retrieval-Augmented Generation) application that connects a private GitHub repository to a chatbot using OpenRouter for AI operations.

## Features

- GitHub markdown document ingestion with daily caching
- OpenRouter integration for embeddings and chat
- FAISS vector store for efficient retrieval
- Streamlit-based chat interface
- Configurable via secrets.toml

## Setup

1. Create a `.streamlit/secrets.toml` file with the following structure:

```toml
# GitHub Configuration
GITHUB_TOKEN = "your-github-token"
GITHUB_REPO = "username/repository"
GITHUB_FOLDER = "optional/subfolder"

# OpenRouter Configuration
OPENROUTER_API_KEY = "your-openrouter-key"

# App Configuration
APP_TITLE = "Your App Title"
APP_URL = "https://your-app-url"
SYSTEM_PROMPT = "Custom system prompt for the assistant"
```

2. Set up the Python environment:

```bash
uv venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
uv pip install -r requirements.txt
```

3. Run the application:

```bash
streamlit run main.py
```

## Development

- Python 3.11 is required for FAISS compatibility
- The application uses daily caching to minimize embedding costs
- Manual cache refresh available via sidebar button

## Security Note

This application relies on URL privacy for access control. Ensure the deployment URL remains private and is only shared with authorized users.
