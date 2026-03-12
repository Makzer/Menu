import time
import streamlit as st
import google.generativeai as genai
import json
from datetime import datetime, timedelta

# --- 1. CONFIGURATION & MODÈLE ---
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-2.5-flash')

# --- 2. INITIALISATION DE LA MÉMOIRE ---
if 'planning_temp' not in st.session_state:
    st.session_state.planning_temp = {}

# --- 3. FONCTIONS LOGIQUES (IA) ---

def nettoyer_et_charger_json(texte):
    """Extrait proprement le JSON du texte de l'IA."""
    try:
        if "```json" in texte:
            texte = texte.split("```json")[1].split("```")[0]
        elif "```" in texte:
            texte = texte.split("```")[1].split("```")[0]
        return json.loads(texte.strip())
    except:
        return None

def generer_menu_ia(prompt_type, dates=None, moment=None, outils=None):
    # On tente l'opération jusqu'à 3 fois en cas de saturation
    for tentative in range(3):
        try:
            if prompt_type == "BATCH":
                prompt = f"Génère un menu du {dates[0]} au {dates[1]} (Midi et Soir). Foyer: 2 adultes, 1 enf (4a), 1 béb (16m). Outils: {outils}. Réponds UNIQUEMENT en JSON: [{{'date': 'YYYY-MM-DD', 'moment': 'Midi', 'plat': 'Nom', 'ingredients': []}}]"
            else:
                prompt = f"Propose une idée de plat pour le {moment}. Foyer: 2 adultes, 1 enf (4a), 1 béb (16m). Outils: {outils}. Réponds UNIQUEMENT en JSON: {{'plat': 'Nom', 'ingredients': []}}"
            
            response = model.generate_content(prompt)
            return nettoyer_et_charger_json(response.text)
            
        except Exception as e:
            if "429" in str(e) or "ResourceExhausted" in str(e):
                # On attend 5 secondes avant de réessayer
                time.sleep(5)
                continue 
            else:
                st.error(f"Erreur : {e}")
                return None
    
    st.error("L'IA est vraiment trop occupée. Réessaye dans une minute.")
    return None
    
    except Exception as e:
        if "429" in str(e) or "ResourceExhausted" in str(e):
            st.error("⚠️ L'IA est un peu fatiguée (Quota atteint). Attendez 1 minute avant de cliquer à nouveau.")
        else:
            st.error(f"Désolé, j'ai eu un petit souci : {e}")
        return None

# --- 4. INTERFACE (SIDEBAR) ---
with st.sidebar:
    st.header("⚙️ Réglages")
    d_deb = st.date_input("Du", datetime.now())
    d_fin = st.date_input("Au", datetime.now() + timedelta(days=2))
    st.divider()
    outils_liste = {"Four":True, "Plaques":True, "AirFryer":False, "Cookeo":False}
    outils_ok = [k for k, v in outils_liste.items() if st.checkbox(k, value=v)]

# --- 5. INTERFACE PRINCIPALE ---
st.title("👨‍🍳 Assistant Menu Familial")

# BOUTON GÉNÉRATION (Placé après la définition des dates)
if st.button("🪄 Générer tout le planning par l'IA"):
    with st.spinner("L'IA prépare tous les repas d'un coup..."):
        menu = generer_menu_ia("BATCH", dates=(d_deb, d_fin), outils=outils_ok)
        if menu:
            st.session_state.planning_temp = {} # Reset
            for item in menu:
                d_str = item['date']
                if d_str not in st.session_state.planning_temp:
                    st.session_state.planning_temp[d_str] = {}
                st.session_state.planning_temp[d_str][item['moment']] = {
                    "plat": item['plat'],
                    "ingredients": item.get('ingredients', []),
                    "actif": True,
                    "participants": ["Papa", "Maman", "Enfant_4ans", "Bebe_16mois"]
                }
            st.rerun()

# --- 6. AFFICHAGE DU CALENDRIER ---
JOURS = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]

for d_str, moments in list(st.session_state.planning_temp.items()):
    dt_obj = datetime.strptime(d_str, '%Y-%m-%d')
    st.markdown(f"### 🗓️ {JOURS[dt_obj.weekday()]} {dt_obj.strftime('%d/%m')}")
    
    col_midi, col_soir = st.columns(2)
    for moment, col in [("Midi", col_midi), ("Soir", col_soir)]:
        with col:
            # Sécurité si le moment n'existe pas dans le JSON de l'IA
            if moment not in moments: continue
            
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
                    data["participants"] = st.multiselect(
                        "Qui mange ?", 
                        ["Papa", "Maman", "Enfant_4ans", "Bebe_16mois"], 
                        default=data["participants"], 
                        key=f"p_{d_str}_{moment}"
                    )

                    # ACTIONS
                    c1, c2 = st.columns(2)
                    if c1.button("🔄 Changer", key=f"reg_{d_str}_{moment}"):
                        with st.spinner("Nouvelle idée..."):
                            nouveau = generer_menu_ia("SINGLE", moment=moment, outils=outils_ok)
                            if nouveau:
                                st.session_state.planning_temp[d_str][moment].update(nouveau)
                                st.rerun()
                    
                    data["repeté"] = c2.checkbox("🔁 Répéter", value=data.get("repeté", False), key=f"rep_{d_str}_{moment}")
            else:
                if st.button(f"➕ Prévoir {moment}", key=f"add_{d_str}_{moment}"):
                    data["actif"] = True
                    st.rerun()
