import streamlit as st
import google.generativeai as genai

# CONFIGURATION
st.set_page_config(page_title="Nutri-Planning Family", layout="centered")
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-1.5-flash')

# INTERFACE
st.title("🥗 Nutri-Planning Family")
st.sidebar.header("🏠 Mon Foyer")
st.sidebar.write("2 Adultes, 2 Enfants (4a, 16m)")

# MENU PRINCIPAL
tab1, tab2, tab3 = st.tabs(["📅 Planning", "📥 Importer", "🛒 Courses"])

with tab2:
    st.header("Ajouter une recette")
    source = st.radio("Source :", ["Lien Social Media / Texte", "Suggestion IA"])
    
    if source == "Lien Social Media / Texte":
        input_text = st.text_area("Collez le lien ou le texte ici...")
        if st.button("Analyser la recette"):
            st.info("L'IA analyse votre lien... (Bientôt connecté à Sheets)")
            # Ici on appellera la fonction d'extraction JSON
            
    else:
        st.subheader("Besoin d'inspiration ?")
        temps = st.slider("Temps dispo (min)", 10, 60, 20)
        equipement = st.multiselect("Équipement disponible", ["Four", "Plaques", "AirFryer", "Cookeo"])
        
        if st.button("Générer des suggestions"):
            prompt = f"Suggère 3 idées de repas pour une famille avec 2 enfants. Temps: {temps}min. Équipement: {equipement}."
            response = model.generate_content(prompt)
            st.write(response.text)

with tab3:
    st.header("Ma Liste de Courses")
    st.write("Votre liste sera générée ici à partir du planning.")
