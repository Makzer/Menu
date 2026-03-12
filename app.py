import streamlit as st
import google.generativeai as genai
import json
import time
import re
from datetime import datetime, timedelta

# --- CONFIGURATION IA ---
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-2.5-flash')

if 'planning_temp' not in st.session_state:
    st.session_state.planning_temp = {}

# --- FONCTION D'EXTRACTION SUR-VITAMINÉE ---
def extraire_json_robuste(texte):
    """Cherche un bloc JSON [ ] dans le texte, peu importe ce qu'il y a autour."""
    try:
        # On cherche tout ce qui est entre les premiers [ et derniers ]
        match = re.search(r'\[.*\]', texte, re.DOTALL)
        if match:
            return json.loads(match.group())
        # Si c'est un objet simple { }
        match_obj = re.search(r'\{.*\}', texte, re.DOTALL)
        if match_obj:
            return [json.loads(match_obj.group())]
    except Exception as e:
        st.error(f"Erreur de lecture JSON : {e}")
    return None

# --- INTERFACE ---
st.title("👨‍🍳 Assistant Menu Familial")

with st.sidebar:
    st.header("⚙️ Réglages")
    d_deb = st.date_input("Du", datetime.now())
    d_fin = st.date_input("Au", datetime.now() + timedelta(days=2))
    st.divider()
    outils = [k for k, v in {"Four":True, "Plaques":True, "AirFryer":False}.items() if st.checkbox(k, value=v)]

# --- BOUTON DE GÉNÉRATION ---
if st.button("🪄 Générer tout le planning par l'IA"):
    status = st.empty() # Zone de texte pour voir ce qui se passe
    status.info("⏳ Connexion à l'IA en cours...")
    
    prompt = f"""Génère un menu du {d_deb} au {d_fin} (Midi et Soir).
    Foyer : 2 adultes, 1 enfant (4 ans), 1 bébé (16 mois). Outils : {outils}.
    Réponds UNIQUEMENT avec un tableau JSON. 
    Format : [{{"date": "{d_deb}", "moment": "Midi", "plat": "Nom", "ingredients": []}}]"""
    
    try:
        response = model.generate_content(prompt)
        status.info("✅ Réponse reçue, analyse du format...")
        
        # DEBUG : Affiche la réponse brute si ça échoue (décommenter si besoin)
        # st.expander("Voir réponse brute").write(response.text)
        
        menu = extraire_json_robuste(response.text)
        
        if menu:
            st.session_state.planning_temp = {}
            for item in menu:
                d_str = item.get('date')
                mom = item.get('moment')
                if d_str and mom:
                    if d_str not in st.session_state.planning_temp:
                        st.session_state.planning_temp[d_str] = {}
                    st.session_state.planning_temp[d_str][mom] = {
                        "plat": item.get('plat', 'Sans nom'),
                        "ingredients": item.get('ingredients', []),
                        "actif": True,
                        "participants": ["Papa", "Maman", "Enfant_4ans", "Bebe_16mois"]
                    }
            status.success("✨ Menu prêt !")
            time.sleep(1)
            st.rerun()
        else:
            status.error("❌ L'IA a répondu mais le format est illisible. Réessayez.")
            st.write("Réponse reçue :", response.text) # On affiche pour comprendre
            
    except Exception as e:
        if "ResourceExhausted" in str(e):
            status.error("🛑 Quota API atteint. Attends 60 secondes sans cliquer.")
        else:
            status.error(f"💥 Erreur : {e}")

# --- AFFICHAGE CALENDRIER (Même code qu'avant) ---
# ... (Gardez la boucle d'affichage du calendrier ici)
