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
    st.header("📅 Générateur de Menu Intelligent")
    
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        date_debut = st.date_input("Date de début", datetime.now())
    with col_d2:
        date_fin = st.date_input("Date de fin", datetime.now())
    
    # Paramètres de génération
    st.subheader("Mes contraintes du moment")
    c1, c2 = st.columns(2)
    with c1:
        mode = st.selectbox("Style de cuisine", ["Rapide & Simple", "Équilibré / Santé", "Réconfortant", "Batch Cooking"])
    with c2:
        equipements_ok = st.multiselect("Équipements à utiliser", ["Four", "Plaques", "AirFryer", "Cookeo", "Mixeur"])

    if st.button("🚀 Générer mon menu avec l'IA"):
        with st.spinner("L'IA conçoit vos repas en tenant compte des enfants..."):
            
            # PROMPT PUISSANT POUR LA GÉNÉRATION
            prompt_menu = f"""
            Agis en tant qu'ingénieur nutritionniste. Génère un menu du {date_debut} au {date_fin} (Midi et Soir).
            Foyer : 2 adultes, 1 enfant (4 ans), 1 bébé (16 mois).
            Contraintes : {mode}, Équipements : {equipements_ok}.
            
            Format de réponse attendu (JSON uniquement) :
            [
              {{
                "date": "YYYY-MM-DD",
                "moment": "Midi/Soir",
                "plat": "Nom du plat",
                "ingredients": [ {{"item": "nom", "qty": 100, "unit": "g"}} ],
                "note_bebe": "Conseil pour le petit de 16 mois"
              }}
            ]
            """
            
            response = model.generate_content(prompt_menu)
            
            # Nettoyage et lecture du JSON
            clean_json = response.text.replace('```json', '').replace('```', '').strip()
            menu_genere = json.loads(clean_json)
            
            # Affichage et Sauvegarde
            for repas in menu_genere:
                with st.expander(f"📌 {repas['date']} - {repas['moment']} : {repas['plat']}"):
                    st.write(f"**Conseil bébé :** {repas['note_bebe']}")
                    # Bouton pour valider ce repas dans le planning réel
                    if st.button(f"Valider {repas['plat']}", key=f"{repas['date']}{repas['moment']}"):
                        ws_plan = sh.worksheet("Planning")
                        ws_plan.append_row([repas['date'], repas['moment'], repas['plat'], "NON"])
                        st.success("Ajouté au planning !")

    st.divider()
    st.subheader("🗓️ Aperçu de la semaine enregistrée")
    # (Ici on garde le code pour afficher le contenu de l'onglet Planning de ton Sheet)

with tab3:
    st.header("Ma Liste de Courses")
    st.button("Générer à partir du planning")
