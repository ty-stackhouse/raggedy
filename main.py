#!/usr/bin/env python3
"""
Raggedy: A Streamlit app for managing and exploring LLM context windows.
"""

import os
import streamlit as st
from typing import Optional

# Page configuration
st.set_page_config(
    page_title="Raggedy",
    page_icon="📏",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Application metadata
APP_TITLE = os.environ.get("APP_TITLE", "Raggedy")

# Page title - should come from APP_TITLE if present
st.title(f"{APP_TITLE} 📏")
