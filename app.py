import streamlit as st
import google.generativeai as genai
import json
import time
from datetime import datetime, timedelta

# --- 1. CONFIGURATION & IA ---
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-2.5-flash')

# --- 2. INITIALISATION MÉMOIRE ---
if 'planning_temp' not in st.session_state:
    st.session_state.planning_temp = {}

# --- 3. FONCTION IA ROBUSTE ---
def generer_via_ia(prompt):
    """Tente de générer du contenu avec 3 essais en cas de saturation (Quota)."""
    for tentative in range(3):
        try:
            response = model.generate_content(prompt)
            texte = response.text
            # Nettoyage JSON
            if "```json" in texte:
                texte = texte.split("```json")[1].split("```")[0]
            elif "```" in texte:
                texte = texte.split("```")[1].split("```")[0]
            return json.loads(texte.strip())
        except Exception as e:
            if "ResourceExhausted" in str(e) or "429" in str(e):
                time.sleep(5) # On attend 5s si Google sature
                continue
            st.error(f"Erreur IA : {e}")
            return None
    return None

# --- 4. RÉGLAGES (SIDEBAR) ---
with st.sidebar:
    st.header("⚙️ Réglages")
    d_deb = st.date_input("Du", datetime.now())
    d_fin = st.date_input("Au", datetime.now() + timedelta(days=3))
    st.divider()
    st.write("🛠️ Équipements disponibles :")
    eq_four = st.checkbox("Four", value=True)
    eq_plaques = st.checkbox("Plaques", value=True)
    eq_airfryer = st.checkbox("AirFryer")
    eq_cookeo = st.checkbox("Cookeo")
    outils_ok = [k for k, v in {"Four":eq_four, "Plaques":eq_plaques, "AirFryer":eq_airfryer, "Cookeo":eq_cookeo}.items() if v]

# --- 5. INTERFACE PRINCIPALE ---
st.title("👨‍🍳 Assistant Menu Familial")

# Bouton de génération globale
if st.button("🪄 Générer tout le planning par l'IA"):
    with st.spinner("L'IA prépare tous les repas d'un coup..."):
        prompt_batch = f"""
        Génère un menu du {d_deb} au {d_fin} (Midi et Soir).
        Foyer : 2 adultes, 1 enfant (4 ans), 1 bébé (16 mois).
        Équipements : {outils_ok}.
        Réponds UNIQUEMENT en JSON sous forme de liste :
        [ {{"date": "YYYY-MM-DD", "moment": "Midi", "plat": "Nom", "ingredients": []}} ]
        """
        menu = generer_via_ia(prompt_batch)
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
            st.success("Menu généré !")
            st.rerun()

# --- 6. AFFICHAGE CALENDRIER ---
JOURS = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]

if st.session_state.planning_temp:
    for d_str, moments in sorted(st.session_state.planning_temp.items()):
        dt_obj = datetime.strptime(d_str, '%Y-%m-%d')
        st.markdown(f"### 🗓️ {JOURS[dt_obj.weekday()]} {dt_obj.strftime('%d/%m')}")
        
        col_midi, col_soir = st.columns(2)
        for moment, col in [("Midi", col_midi), ("Soir", col_soir)]:
            with col:
                if moment in moments:
                    data = moments[moment]
                    if data.get("actif", True):
                        with st.container(border=True):
                            # Header
                            h1, h2 = st.columns([4, 1])
                            h1.subheader(moment)
                            if h2.button("🗑️", key=f"del_{d_str}_{moment}"):
                                data["actif"] = False
                                st.rerun()

                            # Nom du plat
                            st.info(f"#### {data['plat']}")

                            # Participants
                            data["participants"] = st.multiselect(
                                "Qui mange ?", 
                                ["Papa", "Maman", "Enfant_4ans", "Bebe_16mois"],
                                default=data["participants"],
                                key=f"p_{d_str}_{moment}"
                            )

                            # Actions
                            c_ch, c_rep = st.columns(2)
                            if c_ch.button("🔄 Changer", key=f"reg_{d_str}_{moment}"):
                                with st.spinner("Nouvelle idée..."):
                                    prompt_single = f"Propose un autre plat pour le {moment} ({d_str}) pour {data['participants']}. Équipements: {outils_ok}. JSON: {{'plat': 'Nom', 'ingredients': []}}"
                                    nouveau = generer_via_ia(prompt_single)
                                    if nouveau:
                                        st.session_state.planning_temp[d_str][moment].update(nouveau)
                                        st.rerun()
                            
                            data["repeté"] = c_rep.checkbox("🔁 Répéter", value=data.get("repeté", False), key=f"rep_{d_str}_{moment}")
                    else:
                        if st.button(f"➕ Prévoir {moment}", key=f"add_{d_str}_{moment}"):
                            data["actif"] = True
                            st.rerun()
