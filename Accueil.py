import streamlit as st
import pandas as pd
import requests

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="Espace de Prospection - Nice",
    page_icon="🏠",
    layout="wide"
)

st.title("🏠 Mon espace de prospection immobilière - Nice")
st.markdown("Base de données certifiée : passoires énergétiques (F & G) et ciblage par quartier.")

# Chargement du fichier CSV
try:
    df_global = pd.read_csv('dpe_nice_fg.csv')
except Exception as e:
    df_global = pd.DataFrame()
    st.error(f"Erreur critique lors du chargement du fichier CSV : {e}")

# --- FONCTION D'ENRICHISSEMENT DES SOCIÉTÉS / SCI ---
def chercher_infos_entreprise(terme_recherche):
    if not terme_recherche or str(terme_recherche).lower() == "nan":
        return {"siren": "N/A", "dirigeant": "N/A", "siege": "N/A"}
        
    url = "https://recherche-entreprises.api.gouv.fr/search"
    params = {"q": terme_recherche, "per_page": 3}
    
    try:
        response = requests.get(url, params=params, timeout=3)
        if response.status_code == 200:
            resultats = response.json().get("results", [])
            if resultats:
                best_match = resultats[0]
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
        "Passoires Énergétiques (F & G) - Standard",
        "Ciblage SCI / Sociétés (Enrichissement SIRENE)"
    ]
)

# Filtre par secteur / quartier à Nice
secteur = st.sidebar.selectbox(
    "Quartier / Secteur à Nice",
    [
        "Tous les secteurs",
        "Carré d'Or",
        "Promenade des Anglais",
        "Port / Garibaldi",
        "Mont Boron",
        "Musiciens / Gambetta",
        "Centre-ville"
    ]
)

lancer = st.sidebar.button("Générer le listing certifié")

# --- TRAITEMENT ET AFFICHAGE ---
if lancer:
    if df_global.empty:
        st.error("⚠️ Le fichier `dpe_nice_fg.csv` est introuvable à la racine du dépôt GitHub.")
    else:
        df_resultats = df_global.copy()
        
        # Sélection et renommage des colonnes utiles
        colonnes_utiles = {}
        col_adresse = None
        if 'adresse_ban' in df_resultats.columns:
            col_adresse = 'adresse_ban'
            colonnes_utiles['adresse_ban'] = 'Adresse Exacte'
        elif 'adresse_brute' in df_resultats.columns:
            col_adresse = 'adresse_brute'
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

        # Filtrage sécurisé par secteur
        if secteur != "Tous les secteurs" and col_adresse:
            terme_filtre = secteur.split('/')[0].strip().lower()
            mask = df_affichage['Adresse Exacte'].astype(str).str.lower().str.contains(terme_filtre, na=False)
            df_affichage = df_affichage[mask]

        if "SCI" in objectif:
            if len(df_affichage) > 50:
                st.info("ℹ️ Pour des raisons de performance de l'API Sirene, l'enrichissement SCI est appliqué aux 50 premiers biens de cette sélection.")
                df_to_enrich = df_affichage.head(50).copy()
            else:
                df_to_enrich = df_affichage.copy()

            st.info("🔄 Interrogation de l'API Sirene en cours pour les sociétés...")
            sirens, dirigeants, sieges = [], [], []
            
            for idx, row in df_to_enrich.iterrows():
                terme_recherche = f"SCI {row.get('Adresse Exacte', '')}"
                infos = chercher_infos_entreprise(terme_recherche)
                sirens.append(infos['siren'])
                dirigeants.append(infos['dirigeant'])
                sieges.append(infos['siege'])
                
            df_to_enrich['N° SIREN'] = sirens
            df_to_enrich['Dirigeant / Gérant'] = dirigeants
            df_to_enrich['Siège Social'] = sieges
            df_affichage = df_to_enrich
        else:
            df_affichage['Propriétaire / Statut'] = "Particulier (À croiser via DVF / Cadastre)"
            df_affichage['Action Recommandée'] = "Boîtage ciblé"

        st.success(f"✅ Listing généré avec succès ! **{len(df_affichage)}** biens trouvés pour le secteur : *{secteur}*.")
        st.dataframe(df_affichage, use_container_width=True)
        
        csv = df_affichage.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Télécharger ce listing complet (CSV)",
            data=csv,
            file_name=f"listing_prospection_{secteur.lower().replace(' ', '_')}.csv",
            mime='text/csv',
        )
else:
    st.info("👉 Sélectionnez vos critères dans le menu à gauche et cliquez sur **'Générer le listing certifié'**.")
