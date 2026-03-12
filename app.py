import streamlit as st
import google.generativeai as genai
import gspread
import json
from datetime import datetime, timedelta

# --- CONFIGURATION ---
st.set_page_config(page_title="Nutri-Planning Family", layout="wide")

# Connexion Gemini (Utilisation du nom confirmé par tes tests)
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-2.5-flash')

# Connexion Google Sheets (Méthode Cloud Console)
credentials = dict(st.secrets["gcp_service_account"])
gc = gspread.service_account_from_dict(credentials)
sh = gc.open("NutriPlanning_DB")

# --- ÉQUIPEMENTS (Barre latérale) ---
with st.sidebar:
    st.header("🛠️ Ma Cuisine")
    eq_four = st.checkbox("Four", value=True)
    eq_plaques = st.checkbox("Plaques", value=True)
    eq_airfryer = st.checkbox("Air Fryer")
    eq_cookeo = st.checkbox("Cookeo / Multi-cuiseur")
    eq_mixeur = st.checkbox("Mixeur / Vapeur Bébé")
    
    outils = [k for k, v in {"Four":eq_four, "Plaques":eq_plaques, "AirFryer":eq_airfryer, "Cookeo":eq_cookeo, "Mixeur":eq_mixeur}.items() if v]

# --- MÉMOIRE DE L'APP (Session State) ---
if 'menu_propose' not in st.session_state:
    st.session_state.menu_propose = []

# --- INTERFACE PRINCIPALE ---
st.title("🥗 Assistant Menu & Courses")

# 1. Pilotage des dates
col1, col2 = st.columns(2)
date_debut = col1.date_input("Date de début", datetime.now())
date_fin = col2.date_input("Date de fin", datetime.now() + timedelta(days=3))

if st.button("🚀 Générer une proposition complète"):
    with st.spinner("L'IA conçoit vos repas..."):
        prompt = f"""Génère un menu du {date_debut} au {date_fin} (Midi et Soir).
        Foyer : 2 adultes, 1 enfant (4 ans), 1 bébé (16 mois).
        Équipements : {outils}.
        Réponds UNIQUEMENT en JSON avec cette structure : 
        [ {{"date": "YYYY-MM-DD", "moment": "Soir", "plat": "Nom", "theme": "Rapide", "ingredients": [{{"item": "Pommes", "qty": 2, "unit": "unite"}}]}} ]"""
        
        response = model.generate_content(prompt)
        # Nettoyage et stockage
        clean_json = response.text.replace('```json', '').replace('```', '').strip()
        st.session_state.menu_propose = json.loads(clean_json)

# 2. Ajustement "Au cas par cas"
if st.session_state.menu_propose:
    st.divider()
    st.subheader("📝 Personnalisez votre semaine")
    
    for i, repas in enumerate(st.session_state.menu_propose):
        with st.expander(f"📌 {repas['date']} - {repas['moment']} : **{repas['plat']}**", expanded=True):
            c_info, c_action = st.columns([3, 1])
            
            with c_info:
                st.write(f"**Style :** {repas['theme']}")
                ings = ", ".join([ing['item'] for ing in repas['ingredients']])
                st.caption(f"🛒 Ingrédients : {ings}")
            
            with c_action:
                style_unitaire = st.selectbox("Nouveau style", ["Rapide", "Batchcooking", "Santé", "Plaisir"], key=f"s_{i}")
                if st.button("🔄 Régénérer ce plat", key=f"btn_{i}"):
                    new_prompt = f"Propose une autre idée de plat {style_unitaire} pour le {repas['moment']} avec {outils}. Famille avec bébé. Format JSON."
                    res = model.generate_content(new_prompt)
                    clean_res = res.text.replace('```json', '').replace('```', '').strip()
                    st.session_state.menu_propose[i] = json.loads(clean_res)
                    st.rerun()

    # 3. Validation finale
    if st.button("💾 Valider et enregistrer tout le planning"):
        ws = sh.worksheet("Planning")
        for r in st.session_state.menu_propose:
            # On stocke les détails pour la liste de courses future
            ws.append_row([r['date'], r['moment'], r['plat'], json.dumps(r['ingredients'])])
        st.success("Planning enregistré ! Rendez-vous dans l'onglet Courses.")
