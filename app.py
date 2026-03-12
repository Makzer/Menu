import streamlit as st
import google.generativeai as genai
from streamlit_gsheets import GSheetsConnection

# CONFIGURATION
st.set_page_config(page_title="Nutri-Planning Family", layout="centered")

# Connexion aux Secrets
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-1.5-flash')

# Connexion à Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# --- INTERFACE ---
st.title("🥗 Nutri-Planning Family")

tab1, tab2, tab3 = st.tabs(["📅 Planning", "📥 Importer", "🛒 Courses"])

with tab2:
    st.header("Ajouter une recette")
    url_input = st.text_input("Lien TikTok / Instagram ou capture d'écran")
    
    if st.button("Analyser et Sauvegarder"):
        # Prompt pour Gemini
        prompt = f"Extrais les ingrédients et étapes de cette recette : {url_input}. Réponds en format JSON."
        response = model.generate_content(prompt)
        
        # Simulation d'ajout (on affinera la fonction d'écriture après)
        st.success("Recette analysée ! Elle est prête à être enregistrée dans votre Google Sheet.")
        st.json(response.text)

with tab1:
    st.write("Votre planning s'affichera ici dès que nous aurons enregistré la première recette.")
