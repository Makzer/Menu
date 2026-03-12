import streamlit as st
import google.generativeai as genai
import json
from datetime import datetime, timedelta

# --- CONFIGURATION ---
st.set_page_config(page_title="Nutri-Planning Family", layout="wide")
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-1.5-flash-latest')

# --- INITIALISATION DE LA MÉMOIRE (Session State) ---
if 'menu_temporaire' not in st.session_state:
    st.session_state.menu_temporaire = []

# --- BARRE LATÉRALE : ÉQUIPEMENTS ---
with st.sidebar:
    st.header("🛠️ Ma Cuisine")
    eq_four = st.checkbox("Four", value=True)
    eq_plaques = st.checkbox("Plaques Induction", value=True)
    eq_airfryer = st.checkbox("Air Fryer")
    eq_cookeo = st.checkbox("Cookeo / Multi-cuiseur")
    eq_mixeur = st.checkbox("Mixeur (pour bébé)")
    
    liste_eq = [e for e, v in {"Four":eq_four, "Plaques":eq_plaques, "AirFryer":eq_airfryer, "Cookeo":eq_cookeo, "Mixeur":eq_mixeur}.items() if v]

# --- INTERFACE PRINCIPALE ---
st.title("🥗 Assistant Menu de Famille")

# 1. Sélection des dates
col_d1, col_d2 = st.columns(2)
date_deb = col_d1.date_input("Début", datetime.now())
date_fin = col_d2.date_input("Fin", datetime.now() + timedelta(days=3))

if st.button("✨ Générer une proposition de menu complète"):
    with st.spinner("L'IA réfléchit au menu..."):
        # Prompt pour générer la structure
        prompt = f"Génère un menu du {date_deb} au {date_fin} (Midi et Soir) pour 2 adultes, un enfant de 4 ans et un bébé de 16 mois. Équipements : {liste_eq}. Réponds en JSON uniquement."
        response = model.generate_content(prompt)
        # On nettoie et on stocke dans la mémoire de la session
        clean_json = response.text.replace('```json', '').replace('```', '').strip()
        st.session_state.menu_temporaire = json.loads(clean_json)

# 2. Affichage et Modification "au cas par cas"
if st.session_state.menu_temporaire:
    st.divider()
    st.subheader("📝 Ajustez votre menu avant validation")
    
    for i, repas in enumerate(st.session_state.menu_temporaire):
        with st.expander(f"📅 {repas['date']} - {repas['moment']} : {repas['plat']}", expanded=True):
            c1, c2, c3 = st.columns([2, 1, 1])
            
            with c1:
                st.write(f"**Ingrédients principaux :** {', '.join([ing['item'] for ing in repas['ingredients']])}")
                st.caption(f"💡 Conseil Bébé : {repas.get('note_bebe', 'N/A')}")
            
            with c2:
                nouveau_theme = st.selectbox("Changer le thème", ["Rapide", "Batch Cooking", "Végétarien", "Plaisir"], key=f"theme_{i}")
            
            with c3:
                if st.button("🔄 Régénérer ce plat", key=f"btn_{i}"):
                    # Ici, on demande à l'IA de ne changer QUE ce repas précis
                    nouveau_prompt = f"Propose une autre idée de plat {nouveau_theme} pour le {repas['moment']} (Famille avec bébé). Équipements : {liste_eq}. Réponds en JSON."
                    new_resp = model.generate_content(nouveau_prompt)
                    # Mise à jour de la mémoire
                    clean_new = new_resp.text.replace('```json', '').replace('```', '').strip()
                    st.session_state.menu_temporaire[i] = json.loads(clean_new)
                    st.rerun() # On rafraîchit l'affichage

    if st.button("✅ Valider tout le menu et l'ajouter au planning"):
        # Ici on écrit dans Google Sheets (ton onglet Planning)
        st.success("Menu enregistré dans Google Sheets ! Préparez vos courses.")
