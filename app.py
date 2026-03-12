import streamlit as st
import google.generativeai as genai
import json
from datetime import datetime, timedelta

# --- CONFIGURATION ---
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-2.5-flash')

# --- INITIALISATION MÉMOIRE ---
if 'planning_temp' not in st.session_state:
    st.session_state.planning_temp = {} # Format: { "2026-03-12": {"Midi": {...}, "Soir": {...}} }

# --- INTERFACE ---
st.title("📅 Calendrier de Repas Dynamique")

# 1. Sélecteur de plage
c1, c2 = st.columns(2)
d_debut = c1.date_input("Du", datetime.now())
d_fin = c2.date_input("Au", datetime.now() + timedelta(days=3))

# Génération initiale
if st.button("🪄 Générer le planning complet"):
    # On crée la structure vide ou remplie par l'IA
    delta = (d_fin - d_debut).days + 1
    for i in range(delta):
        current_date = str(d_debut + timedelta(days=i))
        if current_date not in st.session_state.planning_temp:
            # Ici on ferait l'appel IA pour remplir d'un coup
            st.session_state.planning_temp[current_date] = {
                "Midi": {"plat": "À définir", "theme": "Rapide", "repeté": False},
                "Soir": {"plat": "À définir", "theme": "Équilibré", "repeté": False}
            }

# --- AFFICHAGE GRILLE CALENDRIER ---
if st.session_state.planning_temp:
    for date_str, repas in st.session_state.planning_temp.items():
        st.subheader(f"🗓️ {date_str}")
        col_midi, col_soir = st.columns(2)
        
        for moment, col in [("Midi", col_midi), ("Soir", col_soir)]:
            with col:
                with st.container(border=True):
                    st.write(f"**{moment}**")
                    data = repas[moment]
                    
                    # Affichage du plat actuel
                    st.markdown(f"🍴 **{data['plat']}**")
                    
                    # Logique de répétition (Cook once, eat twice)
                    data['repeté'] = st.checkbox("Répéter au repas suivant", value=data.get('repeté', False), key=f"rep_{date_str}_{moment}")
                    
                    # Boutons d'action
                    ca1, ca2 = st.columns(2)
                    if ca1.button("🔄 Régénérer", key=f"reg_{date_str}_{moment}"):
                        # Appel IA ciblé
                        prompt = f"Propose une idée de repas pour le {moment}. Équipements: Four, Plaques. Famille 4 pers."
                        new_plat = model.generate_content(prompt).text[:50] # Simplifié pour l'exemple
                        st.session_state.planning_temp[date_str][moment]['plat'] = new_plat
                        st.rerun()
                        
                    if ca2.button("⭐ Favoris", key=f"fav_{date_str}_{moment}"):
                        # Sauvegarde dans l'onglet Favoris
                        st.toast("Ajouté aux favoris !")

# --- LOGIQUE DE RÉPÉTITION AUTOMATIQUE ---
# Si "Répéter" est coché, on doit copier le contenu sur le slot suivant
# (C'est une fonction à lancer avant l'affichage ou au changement)
