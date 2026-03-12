import streamlit as st
import google.generativeai as genai
import json
from datetime import datetime, timedelta

# --- CONFIGURATION ---
RATIOS = {"Papa": 1.0, "Maman": 1.0, "Enfant_4ans": 0.7, "Bebe_16mois": 0.5}

if 'planning_temp' not in st.session_state:
    st.session_state.planning_temp = {}

# --- FONCTION DE CALCUL DES PORTIONS ---
def calculer_portions_repas(participants_choisis):
    return sum([RATIOS[p] for p in participants_choisis])

# --- INTERFACE ---
st.title("📅 Calendrier Familial Intelligent")

# Choix de la plage
c1, c2 = st.columns(2)
d_deb = c1.date_input("Du", datetime.now())
d_fin = c2.date_input("Au", datetime.now() + timedelta(days=3))

if st.button("🪄 Générer le planning initial"):
    delta = (d_fin - d_deb).days + 1
    for i in range(delta):
        d_str = str(d_deb + timedelta(days=i))
        if d_str not in st.session_state.planning_temp:
            st.session_state.planning_temp[d_str] = {
                "Midi": {"plat": "Pâtes au pesto", "participants": list(RATIOS.keys()), "repeté": False},
                "Soir": {"plat": "Soupe de légumes", "participants": list(RATIOS.keys()), "repeté": False}
            }

# --- AFFICHAGE DU CALENDRIER ---
if st.session_state.planning_temp:
    for d_str, moments in st.session_state.planning_temp.items():
        st.subheader(f"🗓️ {d_str}")
        col_midi, col_soir = st.columns(2)
        
        for moment, col in [("Midi", col_midi), ("Soir", col_soir)]:
            with col:
                with st.container(border=True):
                    # 1. QUI MANGE ? (La sélection granulaire)
                    data = moments[moment]
                    st.write(f"**{moment}**")
                    
                    # Sélection des participants (par défaut tous cochés)
                    participants_reels = st.multiselect(
                        "Participants :", 
                        options=list(RATIOS.keys()), 
                        default=data["participants"],
                        key=f"parts_{d_str}_{moment}"
                    )
                    data["participants"] = participants_reels
                    
                    # Calcul de la portion affichée en temps réel
                    p_reelles = calculer_portions_repas(participants_reels)
                    st.caption(f"📈 Portions : {p_reelles}")

                    # 2. LE PLAT
                    st.markdown(f"🍴 **{data['plat']}**")
                    
                    # 3. OPTIONS
                    data['repeté'] = st.checkbox("🔄 Répéter sur le repas suivant", value=data.get('repeté', False), key=f"rep_{d_str}_{moment}")
                    
                    c_reg, c_fav = st.columns(2)
                    if c_reg.button("♻️ Changer", key=f"reg_{d_str}_{moment}"):
                        # Appel IA pour régénérer un plat selon les goûts
                        st.session_state.planning_temp[d_str][moment]['plat'] = "Nouveau plat suggéré..."
                        st.rerun()
