import streamlit as st
import google.generativeai as genai
import gspread
import pandas as pd
from datetime import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="Nutri-Planning Family", layout="wide")

# Connexion Gemini
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-1.5-flash')

# Connexion Google Sheets (Via Service Account)
credentials = dict(st.secrets["gcp_service_account"])
gc = gspread.service_account_from_dict(credentials)
# Remplacez par le nom EXACT de votre fichier Google Sheets
sh = gc.open("NutriPlanning_DB") 

# --- LOGIQUE DIÉTÉTIQUE ---
# Ratios basés sur les besoins caloriques moyens par âge
RATIOS = {
    "Adulte": 1.0,
    "Enfant (4 ans)": 0.7,
    "Bébé (16 mois)": 0.5
}
FOYER_BASE = (2 * RATIOS["Adulte"]) + RATIOS["Enfant (4 ans)"] + RATIOS["Bébé (16 mois)"] # = 3.2 portions

# --- INTERFACE ---
st.title("🥗 Nutri-Planning Family")

tab1, tab2, tab3 = st.tabs(["📅 Planning", "📥 Importer & Calculer", "🛒 Courses"])

with tab2:
    st.header("Nouvelle Recette")
    source = st.text_area("Collez le lien ou le texte de la recette")
    
    col1, col2 = st.columns(2)
    with col1:
        faire_plus = st.checkbox("Prévoir des restes pour demain (2 adultes)")
    
    if st.button("Analyser et Ajuster les doses"):
        with st.spinner("L'IA calcule les portions pour votre famille..."):
            # 1. Extraction par l'IA
            prompt = f"Extrais cette recette en JSON. Donne 'portions_origine' et la liste 'ingredients' avec 'item', 'qty', 'unit'. Source: {source}"
            response = model.generate_content(prompt)
            # (Note : Dans un vrai code on parserait le JSON ici)
            
            # 2. Calcul du multiplicateur
            nb_personnes_ce_soir = FOYER_BASE
            nb_personnes_demain = 2.0 if faire_plus else 0.0
            total_portions_voulues = nb_personnes_ce_soir + nb_personnes_demain
            
            st.success(f"Doses calculées pour {total_portions_voulues} portions (Famille + restes)")
            st.write(f"Multiplier les quantités d'origine par : **{total_portions_voulues:.2f} / portions_origine**")
            
            # 3. Sauvegarde dans Google Sheets
            worksheet = sh.worksheet("Recettes")
            # Logique d'écriture simplifiée
            worksheet.append_row([datetime.now().strftime("%d/%m/%Y"), "Nom du plat", str(response.text)])
            st.balloons()

with tab3:
    st.header("🛒 Liste de Courses Automatique")
    if st.button("Générer la liste de la semaine"):
        st.write("L'app additionne tous les ingrédients du planning...")
        # Ici on fera la somme des ingrédients de la table Planning
