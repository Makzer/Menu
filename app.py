import streamlit as st
import google.generativeai as genai
import gspread
import json
import pandas as pd
from datetime import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="Nutri-Planning Family", layout="wide")

# Connexion Gemini & Google Sheets
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-1.5-flash')
credentials = dict(st.secrets["gcp_service_account"])
gc = gspread.service_account_from_dict(credentials)
sh = gc.open("NutriPlanning_DB") # Vérifie que c'est le nom exact de ton Sheet

# --- RÉGLAGES FAMILLE (Expertise Diététique) ---
RATIOS = {"Adulte": 1.0, "Enfant_4ans": 0.7, "Bebe_16mois": 0.5}
FAMILLE_TOTALE = (2 * RATIOS["Adulte"]) + RATIOS["Enfant_4ans"] + RATIOS["Bebe_16mois"] # 3.2 portions

# --- FONCTIONS ---
def sauvegarder_recette(data):
    ws = sh.worksheet("Recettes")
    ws.append_row([data['nom'], json.dumps(data['ingredients']), json.dumps(data['instructions']), data['portions_base']])

# --- INTERFACE ---
st.title("👨‍👩‍👧‍👦 Nutri-Planning Family")

tab1, tab2, tab3 = st.tabs(["📅 Mon Planning", "📥 Importer une idée", "🛒 Liste de Courses"])

with tab2:
    st.header("Importer une recette (TikTok, Insta, Texte)")
    source = st.text_area("Collez le contenu ici...", placeholder="Lien ou description...")
    
    col_a, col_b = st.columns(2)
    with col_a:
        prevoir_restes = st.checkbox("Prévoir des restes pour demain midi (2 adultes)")
    
    if st.button("Calculer les doses pour la famille"):
        with st.spinner("L'IA analyse et ajuste les quantités..."):
            prompt = f"""Analyse cette recette et réponds UNIQUEMENT en JSON :
            {{ "nom": "titre", "portions_base": 2, "ingredients": [{{"item": "nom", "qty": 100, "unit": "g"}}] }}
            Source : {source}"""
            
            response = model.generate_content(prompt)
            # Nettoyage du JSON (au cas où l'IA met des balises ```json)
            clean_json = response.text.replace('```json', '').replace('```', '').strip()
            recipe_data = json.loads(clean_json)
            
            # CALCUL DES DOSES RÉELLES
            cible = FAMILLE_TOTALE + (2.0 if prevoir_restes else 0.0)
            facteur = cible / recipe_data['portions_base']
            
            st.success(f"Recette : {recipe_data['nom']}")
            st.write(f"**Quantités ajustées pour {cible} portions (Famille + restes éventuels) :**")
            
            for ing in recipe_data['ingredients']:
                vrai_qty = float(ing['qty']) * facteur
                st.write(f"- {ing['item']} : {vrai_qty:.0f} {ing['unit']}")
            
            if st.button("Confirmer et ajouter au planning"):
                sauvegarder_recette(recipe_data)
                st.balloons()

with tab1:
    st.header("Choix des dates")
    date_debut = st.date_input("Du", datetime.now())
    date_fin = st.date_input("Au", datetime.now())
    st.info("Sélectionnez vos repas dans la bibliothèque ci-dessous.")
    # Ici on affichera les recettes enregistrées pour les glisser dans le planning

with tab3:
    st.header("Ma Liste de Courses")
    st.button("Générer à partir du planning")
