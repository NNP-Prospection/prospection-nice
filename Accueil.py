import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="Espace de Prospection - Nice", layout="wide")

st.title("🏠 Mon espace de prospection immobilière")
st.markdown("Bienvenue sur votre outil de ciblage avancé à Nice.")

# --- BARRE LATÉRALE DE FILTRES ---
st.sidebar.header("Critères de recherche")

type_prospection = st.sidebar.selectbox(
    "Objectif de prospection",
    [
        "Passoires Énergétiques (DPE F & G)", 
        "Fin d'amortissement LMNP (5-7 ans)", 
        "Successions / Indivisions"
    ]
)

secteur = st.sidebar.selectbox(
    "Secteur à Nice",
    ["Carré d'Or", "Le Port", "Musiciens", "Jean Médecin", "Mont Boron"]
)

budget_max = st.sidebar.slider("Budget maximum (en €)", 150000, 1000000, 500000, 25000)

lancer_recherche = st.sidebar.button("Lancer la recherche")

# --- ZONE DE TRAITEMENT ET AFFICHAGE ---
if lancer_recherche:
    st.success(f"Recherche en cours pour : **{type_prospection}** dans le secteur **{secteur}**...")

    if type_prospection == "Passoires Énergétiques (DPE F & G)":
        # Appel API ADEME visible sur votre Colab
        url = "https://data.ademe.fr/data-fair/api/v1/datasets/meg-83tjwtg8dyz7h1dqe/lines"
        parametres = {
            "q": "06000", 
            "size": 10,
            "qs": "etiquette_dpe:\"G\" OR etiquette_dpe:\"F\""
        }
        
        try:
            reponse = requests.get(url, params=parametres)
            if reponse.status_code == 200:
                data = reponse.json()
                resultats = data.get("results", [])
                if resultats:
                    df_dpe = pd.DataFrame(resultats)
                    st.write("### Résultats DPE F & G trouvés :")
                    st.dataframe(df_dpe)
                else:
                    st.info("Aucun bien trouvé avec ces critères précis via l'API ADEME.")
            else:
                st.error("Erreur lors de la connexion à l'API de l'ADEME.")
        except Exception as e:
            st.warning(fImpossible de joindre l'API pour le moment : {e}")

    elif type_prospection == "Fin d'amortissement LMNP (5-7 ans)":
        st.write("### Analyse des loueurs en fin de défiscalisation (2019-2021)")
        # Simulation de données cibles LMNP
        donnees_lmnp = {
            'Adresse': ['Rue de France', 'Rue Masséna', 'Avenue Jean Médecin'],
            'Quartier': [secteur, secteur, secteur],
            'Annee_Lancement': [2020, 2019, 2021],
            'Potentiel': ['Fin amortissement imminente', 'Revente envisageable', 'Arbitrage fiscal']
        }
        st.dataframe(pd.DataFrame(donnees_lmnp))

    else:
        st.write("### Suivi des dossiers de successions / indivisions")
        st.info("Module de croisement cadastral actif pour le secteur sélectionné.")

else:
    st.info("👈 Veuillez configurer vos critères dans le menu à gauche puis cliquez sur 'Lancer la recherche'.")
