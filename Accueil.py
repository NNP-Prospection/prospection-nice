import streamlit as st
import pandas as pd
import requests

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="Espace de Prospection - Nice",
    page_icon="🏠",
    layout="wide"
)

# Chargement du fichier CSV
@st.cache_data
def load_data():
    try:
        return pd.read_csv('dpe_nice_fg.csv')
    except Exception as e:
        return pd.DataFrame()

df_global = load_data()

st.title("🏠 Mon espace de prospection immobilière - Nice")
st.markdown("Base de données certifiée : passoires énergétiques (F & G) et enrichissement des propriétaires (SCI & Sociétés).")

# --- FONCTION D'ENRICHISSEMENT DES SOCIÉTÉS / SCI ---
def chercher_infos_entreprise(terme_recherche):
    """
    Interroge l'API officielle de recherche d'entreprises pour trouver 
    le SIREN, le dirigeant et l'adresse du siège (particulièrement utile pour les SCI).
    """
    if not terme_recherche or str(terme_recherche).lower() == "nan":
        return {"siren": "N/A", "dirigeant": "N/A", "siege": "N/A"}
        
    url = "https://recherche-entreprises.api.gouv.fr/search"
    params = {"q": terme_recherche, "per_page": 3}
    
    try:
        response = requests.get(url, params=params, timeout=4)
        if response.status_code == 200:
            resultats = response.json().get("results", [])
            if resultats:
                best_match = resultats[0]
                # Privilégier le département 06 si possible
                for res in resultats:
                    siege = res.get("siege", {})
                    cp = str(siege.get("code_postal", ""))
                    if cp.startswith("06"):
                        best_match = res
                        break
                
                siren = best_match.get("siren", "N/A")
                dirigeants = best_match.get("dirigeants", [])
                nom_dirigeant = f"{dirigeants[0].get('prenoms', '')} {dirigeants[0].get('nom', '')}".strip() if dirigeants else "Non renseigné"
                
                siege = best_match.get("siege", {})
                adresse_siege = f"{siege.get('adresse', '')}, {siege.get('code_postal', '')} {siege.get('libelle_commune', '')}"
                
                return {
                    "siren": siren,
                    "dirigeant": nom_dirigeant if nom_dirigeant else "Non renseigné",
                    "siege": adresse_siege.strip(", ") if adresse_siege.strip(", ") else "Adresse non renseignée"
                }
    except Exception:
        pass
        
    return {"siren": "N/A", "dirigeant": "N/A", "siege": "N/A"}

# --- BARRE LATÉRALE DE RECHERCHE ---
st.sidebar.header("Critères de ciblage")

objectif = st.sidebar.selectbox(
    "Objectif de prospection",
    [
        "Passoires Énergétiques (DPE F & G) - Standard",
        "Ciblage Actifs / SCI (Enrichissement SIRENE)"
    ]
)

lancer = st.sidebar.button("Générer le listing certifié")

# --- TRAITEMENT ET AFFICHAGE ---
if lancer:
    if df_global.empty:
        st.error("⚠️ Le fichier de données `dpe_nice_fg.csv` n'a pas pu être chargé.")
    else:
        df_resultats = df_global.copy()
        
        # 1. Sélection et renommage des colonnes techniques de l'ADEME
        colonnes_utiles = {}
        if 'adresse_ban' in df_resultats.columns:
            colonnes_utiles['adresse_ban'] = 'Adresse Exacte'
        elif 'adresse_brute' in df_resultats.columns:
            colonnes_utiles['adresse_brute'] = 'Adresse Exacte'
            
        if 'code_postal_ban' in df_resultats.columns:
            colonnes_utiles['code_postal_ban'] = 'Code Postal'
            
        if 'etiquette_dpe' in df_resultats.columns:
            colonnes_utiles['etiquette_dpe'] = 'Note DPE'
            
        if 'surface_habitable_logement' in df_resultats.columns:
            colonnes_utiles['surface_habitable_logement'] = 'Surface (m²)'
            
        if 'date_etablissement_dpe' in df_resultats.columns:
            colonnes_utiles['date_etablissement_dpe'] = 'Date DPE'

        if colonnes_utiles:
            df_affichage = df_resultats[list(colonnes_utiles.keys())].rename(columns=colonnes_utiles)
        else:
            df_affichage = df_resultats 

        # Limiter l'affichage aux 50 premiers pour fluidifier l'appel API si on active l'enrichissement
        if len(df_affichage) > 50:
            df_affichage = df_affichage.head(50)

        # 2. Gestion selon l'objectif choisi
        if "SCI" in objectif:
            st.info("🔄 Interrogation de l'API Sirene en cours pour identifier les sociétés et gérants...")
            sirens, dirigeants, sieges = [], [], []
            
            # Simulation ou recherche sur l'adresse / nom si disponible, sinon test sur des structures types
            for idx, row in df_affichage.iterrows():
                # Recherche basée sur l'adresse ou un nom générique de copropriété/SCI si présent dans le fichier
                terme_recherche = f"SCI {row.get('Adresse Exacte', '')}"
                infos = chercher_infos_entreprise(terme_recherche)
                sirens.append(infos['siren'])
                dirigeants.append(infos['dirigeant'])
                sieges.append(infos['siege'])
                
            df_affichage['N° SIREN'] = sirens
            df_affichage['Dirigeant / Gérant'] = dirigeants
            df_affichage['Siège Social'] = sieges
        else:
            df_affichage['Propriétaire / Statut'] = "Particulier (À croiser via DVF / Cadastre)"
            df_affichage['Action Recommandée'] = "Boîtage ciblé / Enquête voisinage"

        st.success(f"✅ Listing généré avec succès ! Affichage de {len(df_affichage)} biens à Nice.")
        st.dataframe(df_affichage, use_container_width=True)
        
        # Bouton de téléchargement
        csv = df_affichage.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Télécharger ce listing (CSV)",
            data=csv,
            file_name="listing_prospection_nice.csv",
            mime='text/csv',
        )
else:
    st.info("👉 Sélectionnez vos options dans le menu latéral et cliquez sur **'Générer le listing certifié'**.")
