import streamlit as st
import google.generativeai as genai
import json
from datetime import datetime, timedelta

# --- CONFIGURATION IA ---
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-2.5-flash')

# --- LOGIQUE IA (Le cœur du système) ---
def generer_planning_complet_ia(date_debut, date_fin, outils, theme="Équilibré"):
    prompt = f"""
    Agis en tant que planificateur de repas familial. 
    Génère un menu complet du {date_debut} au {date_fin} (Midi et Soir).
    Foyer : 2 adultes, 1 enfant (4 ans), 1 bébé (16 mois).
    Équipements : {outils}. Style : {theme}.
    
    Réponds EXCLUSIVEMENT en JSON. Le format doit être une liste d'objets :
    [
      {{
        "date": "YYYY-MM-DD",
        "moment": "Midi",
        "plat": "Nom du plat",
        "ingredients": [{{"item": "nom", "qty": 100, "unit": "g"}}]
      }},
      ...
    ]
    """
    try:
        response = model.generate_content(prompt)
        clean_json = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(clean_json)
    except Exception as e:
        st.error(f"Erreur : {e}")
        return []

# --- INITIALISATION MÉMOIRE ---
if st.button("🪄 Générer tout le planning par l'IA"):
    with st.spinner("L'IA cuisine tout votre menu de la semaine en une fois..."):
        # Un seul appel API ici !
        menu_complet = generer_planning_complet_ia(d_deb, d_fin, outils)
        
        # On remplit le session_state avec les résultats
        for item in menu_complet:
            d_str = item['date']
            moment = item['moment']
            if d_str not in st.session_state.planning_temp:
                st.session_state.planning_temp[d_str] = {}
            
            st.session_state.planning_temp[d_str][moment] = {
                "plat": item['plat'],
                "ingredients": item['ingredients'],
                "actif": True,
                "participants": ["Papa", "Maman", "Enfant_4ans", "Bebe_16mois"]
            }
        st.rerun()

# --- INTERFACE ---
st.title("👨‍🍳 Assistant Menu Familial")

# 1. Pilotage (Dates & Outils)
with st.sidebar:
    st.header("⚙️ Réglages")
    d_deb = st.date_input("Du", datetime.now())
    d_fin = st.date_input("Au", datetime.now() + timedelta(days=2))
    st.divider()
    outils = [k for k, v in {"Four":True, "Plaques":True, "AirFryer":False, "Cookeo":False}.items() if st.checkbox(k, value=v)]

# BOUTON GÉNÉRATION GLOBALE
if st.button("🪄 Générer tout le planning par l'IA"):
    delta = (d_fin - d_deb).days + 1
    with st.spinner("L'IA prépare vos menus..."):
        for i in range(delta):
            d_str = str(d_deb + timedelta(days=i))
            # On génère Midi et Soir d'un coup
            st.session_state.planning_temp[d_str] = {
                "Midi": {**generer_suggestion_ia("Midi", "Toute la famille", outils), "actif": True, "participants": ["Papa", "Maman", "Enfant_4ans", "Bebe_16mois"]},
                "Soir": {**generer_suggestion_ia("Soir", "Toute la famille", outils), "actif": True, "participants": ["Papa", "Maman", "Enfant_4ans", "Bebe_16mois"]}
            }

# --- AFFICHAGE CALENDRIER ---
JOURS = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]

for d_str, moments in list(st.session_state.planning_temp.items()):
    dt_obj = datetime.strptime(d_str, '%Y-%m-%d')
    st.markdown(f"### 🗓️ {JOURS[dt_obj.weekday()]} {dt_obj.strftime('%d/%m')}")
    
    col_midi, col_soir = st.columns(2)
    for moment, col in [("Midi", col_midi), ("Soir", col_soir)]:
        with col:
            data = moments[moment]
            if data.get("actif", True):
                with st.container(border=True):
                    h1, h2 = st.columns([4, 1])
                    h1.subheader(moment)
                    if h2.button("🗑️", key=f"del_{d_str}_{moment}"):
                        data["actif"] = False
                        st.rerun()

                    # NOM DU REPAS (Mise en valeur)
                    st.info(f"#### {data['plat']}")

                    # Participants
                    data["participants"] = st.multiselect("Qui mange ?", ["Papa", "Maman", "Enfant_4ans", "Bebe_16mois"], default=data["participants"], key=f"p_{d_str}_{moment}")

                    # ACTIONS
                    c1, c2 = st.columns(2)
                    if c1.button("🔄 Changer", key=f"reg_{d_str}_{moment}"):
                        with st.spinner("Nouvelle idée..."):
                            nouveau = generer_suggestion_ia(moment, data["participants"], outils)
                            st.session_state.planning_temp[d_str][moment].update(nouveau)
                            st.rerun()
                    
                    data["repeté"] = c2.checkbox("🔁 Répéter", value=data.get("repeté", False), key=f"rep_{d_str}_{moment}")
            else:
                if st.button(f"➕ Prévoir {moment}", key=f"add_{d_str}_{moment}"):
                    data["actif"] = True
                    st.rerun()
