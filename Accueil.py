import streamlit as st

st.set_page_config(page_title="Espace de Prospection", page_icon="🏠", layout="wide")

st.title("🏠 Mon espace de prospection")
st.write("Bienvenue sur votre outil de ciblage immobilier à Nice.")

# Menu latéral de prospection
st.sidebar.header("Critères de recherche")
type_bien = st.sidebar.selectbox("Type de bien", ["Appartement", "Immeuble entier", "Locaux commerciaux"])
secteur = st.sidebar.selectbox("Secteur à Nice", ["Carré d'Or", "Cimiez", "Musiciens", "Port", "Mont Boron"])
budget_max = st.sidebar.slider("Budget maximum (€)", 100000, 2000000, 500000, step=50000)

if st.sidebar.button("Lancer la recherche"):
    st.success(f"Recherche lancée pour : {type_bien} à {secteur} (Budget max : {budget_max:,} €)")
    st.info("Les résultats correspondants s'afficheront ici prochainement.")
else:
    st.info("👈 Veuillez configurer vos critères dans le menu à gauche puis cliquez sur 'Lancer la recherche'.")
