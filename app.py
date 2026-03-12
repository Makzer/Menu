import streamlit as st
import google.generativeai as genai
import json
from datetime import datetime, timedelta

# --- CONFIGURATION ---
st.set_page_config(page_title="Nutri-Planning Family", layout="wide")
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
st.write("### Modèles disponibles :")
try:
    available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    st.write(available_models)
except Exception as e:
    st.error(f"Erreur lors du listage des modèles : {e}")
