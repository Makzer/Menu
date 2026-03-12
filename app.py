import streamlit as st
import google.generativeai as genai
import gspread
import json
import pandas as pd
from datetime import datetime, timedelta

# --- CONFIGURATION & IA ---
st.set_page_config(page_title="Nutri-Planning Pro", layout="wide")
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-2.5-flash')

# --- CONNEXION SHEETS ---
credentials = dict(st.secrets["gcp_service_account"])
gc = gspread.service_account_from_dict(credentials)
sh = gc.open("NutriPlanning_DB")

# --- RÉGLAGES FOYER ---
RATIOS = {"Papa": 1.0, "Maman": 1.0, "Enfant_4ans": 0.7, "Bebe_16mois": 0.5}

# --- MODULE PARAMÈTRES (Goûts de chacun) ---
def get_preferences():
    ws = sh.worksheet("Preferences")
    return pd.DataFrame(ws.get_all_records())

# --- INTERFACE ---
st.title("🍴 Family Menu Manager")

tab_plan, tab_fav, tab_set = st.tabs(["🗓️ Planning & Calendrier", "⭐ Mes Favoris", "⚙️ Paramètres"])

# --- TAB : PARAMÈTRES ---
with tab_set:
    st.header("👤 Préférences du Foyer")
    pref_df = get_preferences()
    st.write("Dites à l'IA ce que vous aimez ou détestez :")
    # Formulaire simplifié pour éditer les goûts
    with st.form("edit_prefs"):
        st.data_editor(pref_df, key="pref_editor", num_rows="dynamic")
        if st.form_submit_button("Sauvegarder les préférences"):
            sh.worksheet("Preferences").update([pref_df.columns.values.tolist()] + pref_df.values.tolist())
            st.success("Préférences mises à jour !")

# --- TAB : FAVORIS ---
with tab_fav:
    st.header("❤️ Recettes Favorites")
    ws_fav = sh.worksheet("Favoris")
    fav_df = pd.DataFrame(ws_fav.get_all_records())
    if not fav_df.empty:
        for idx, row in fav_df.iterrows():
            with st.expander(row['Nom']):
                st.write(row['Ingredients'])
                if st.button("Ajouter au planning", key=f"fav_{idx}"):
                    # Logique pour injecter ce favori dans le planning
                    pass
    else:
        st.info("Aucun favori pour le moment.")

# --- TAB : PLANNING & CALENDRIER ---
with tab_plan:
    # 1. Sélection des participants (Convives)
    st.sidebar.header("👥 Qui mange ?")
    participants = {}
    for membre, ratio in RATIOS.items():
        participants[membre] = st.sidebar.checkbox(membre, value=True)
    
    # Calcul du ratio total actuel
    ratio_total = sum([RATIOS[m] for m, p in participants.items() if p])
    st.sidebar.info(f"Portions calculées : {ratio_total}")

    # 2. Vue Calendrier (Grille de 7 colonnes)
    st.header("📅 Mon Planning Hebdomadaire")
    dates_semaine = [datetime.now() + timedelta(days=i) for i in range(7)]
    cols = st.columns(7)
    
    for i, date in enumerate(dates_semaine):
        with cols[i]:
            st.markdown(f"**{date.strftime('%a %d')}**")
            # Zone "Drog & Drop" simulée par un container
            with st.container(border=True):
                st.caption("Dîner")
                # Ici on affiche le repas si déjà en BDD, sinon un bouton "+"
                if st.button("➕", key=f"add_{i}"):
                    st.session_state.date_a_remplir = date
                    # Trigger vers l'IA pour ce jour précis

    # 3. Génération Assistée par IA
    st.divider()
    if st.button("🪄 Suggérer un menu basé sur nos goûts"):
        # On récupère les prefs pour le prompt
        prefs = get_preferences().to_string()
        prompt = f"""Génère un menu. 
        Participants (ratio total {ratio_total}). 
        Préférences de la famille : {prefs}.
        Réponds en JSON uniquement."""
        
        with st.spinner("L'IA concocte un menu sur-mesure..."):
            res = model.generate_content(prompt)
            # Affichage pour validation (comme vu précédemment)
