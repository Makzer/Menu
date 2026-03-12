import streamlit as st
import google.generativeai as genai
import json
from datetime import datetime, timedelta

# --- CONFIGURATION LOCALE ---
# Configuration des noms de jours en français
JOURS = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]

# --- INITIALISATION MÉMOIRE ---
if 'planning_temp' not in st.session_state:
    st.session_state.planning_temp = {}

# --- INTERFACE ---
st.title("📅 Mon Organiseur de Repas")

# Sélecteur de plage
col_d1, col_d2 = st.columns(2)
d_deb = col_d1.date_input("Date de début", datetime.now())
d_fin = col_d2.date_input("Date de fin", datetime.now() + timedelta(days=3))

if st.button("✨ Générer / Préparer le calendrier"):
    delta = (d_fin - d_deb).days + 1
    for i in range(delta):
        current_date = d_deb + timedelta(days=i)
        d_str = str(current_date)
        if d_str not in st.session_state.planning_temp:
            st.session_state.planning_temp[d_str] = {
                "Midi": {"plat": "Pâtes fraîches pesto", "participants": ["Papa", "Maman", "Enfant_4ans", "Bebe_16mois"], "actif": True},
                "Soir": {"plat": "Gratin de courgettes", "participants": ["Papa", "Maman", "Enfant_4ans", "Bebe_16mois"], "actif": True}
            }

# --- AFFICHAGE DU CALENDRIER ---
if st.session_state.planning_temp:
    for d_str, moments in st.session_state.planning_temp.items():
        # Formater la date : "Lundi 12 Mars"
        dt_obj = datetime.strptime(d_str, '%Y-%m-%d')
        nom_jour = JOURS[dt_obj.weekday()]
        st.markdown(f"### 🗓️ {nom_jour} {dt_obj.strftime('%d/%m')}")
        
        col_midi, col_soir = st.columns(2)
        
        for moment, col in [("Midi", col_midi), ("Soir", col_soir)]:
            with col:
                data = moments[moment]
                
                # Système de corbeille : On affiche la carte seulement si 'actif' est True
                if data.get("actif", True):
                    with st.container(border=True):
                        # En-tête de la vignette avec bouton Corbeille
                        head1, head2 = st.columns([4, 1])
                        head1.subheader(f"🍴 {moment}")
                        if head2.button("🗑️", key=f"del_{d_str}_{moment}"):
                            data["actif"] = False
                            st.rerun()

                        # MISE EN VALEUR DU NOM DU REPAS
                        st.markdown(f"""
                            <div style="background-color: #f0f2f6; padding: 10px; border-radius: 5px; border-left: 5px solid #ff4b4b; margin-bottom: 10px;">
                                <h2 style="margin: 0; color: #31333F; font-size: 20px;">{data['plat']}</h2>
                            </div>
                        """, unsafe_allow_html=True)

                        # Sélection des participants
                        parts = st.multiselect(
                            "Qui mange ?", 
                            options=["Papa", "Maman", "Enfant_4ans", "Bebe_16mois"],
                            default=data["participants"],
                            key=f"parts_{d_str}_{moment}"
                        )
                        data["participants"] = parts
                        
                        # Options
                        c_reg, c_rep = st.columns(2)
                        if c_reg.button("🔄 Changer", key=f"reg_{d_str}_{moment}"):
                            # Logique IA de régénération ici
                            data["plat"] = "Nouveau plat suggéré..."
                            st.rerun()
                        
                        rep = c_rep.checkbox("🔁 Répéter", key=f"rep_{d_str}_{moment}")
                else:
                    # Bouton pour restaurer si on a supprimé par erreur
                    if st.button(f"➕ Prévoir un repas pour ce {moment}", key=f"rest_{d_str}_{moment}"):
                        data["actif"] = True
                        data["plat"] = "À définir"
                        st.rerun()
