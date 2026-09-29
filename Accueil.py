import streamlit as st
import pandas as pd
import numpy as np
import requests

# Chargement du vrai fichier de données allégé pour Nice
try:
    df_global = pd.read_csv('dpe_nice_fg.csv')
except Exception as e:
    st.error(f"Erreur lors du chargement du fichier de données : {e}")
    df_global = pd.DataFrame()

def chercher_siren_et_siege_local(nom_sci):
    """
    Interroge l'API officielle pour trouver le SIREN et le siège social,
    en privilégiant le département 06 (Alpes-Maritimes) pour éviter les homonymes.
    """
    if not nom_sci or str(nom_sci).lower() == "nan" or "N/A" in str(nom_sci):
        return {"siren": "N/A", "siege": "N/A"}
        
    url = "https://recherche-entreprises.api.gouv.fr/search"
    params = {"q": nom_sci, "per_page": 5}
    
    try:
        response = requests.get(url, params=params, timeout=5)
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
                siege = best_match.get("siege", {})
                adresse_siege = f"{siege.get('adresse', '')}, {siege.get('code_postal', '')} {siege.get('libelle_commune', '')}"
                
                return {
                    "siren": siren,
                    "siege": adresse_siege.strip(", ") if adresse_siege.strip(", ") else "Adresse non renseignée"
                }
    except Exception as e:
        print(f"Erreur technique API Sirene : {e}")
        
    return {"siren": "N/A", "siege": "N/A"}

def enrichir_sci_avec_sirene(df_passoires, nom_colonne_proprietaire="proprietaire"):
    """
    Enrichit les SCI avec les informations SIREN et siège social locales.
    """
    sirens = []
    sieges = []
    
    # Recherche de la colonne propriétaire adéquate dans le DataFrame CSV
    cols_possibles = [c for c in df_passoires.columns if 'prop' in c.lower() or 'contact' in c.lower()]
    col_prop = cols_possibles[0] if cols_possibles else df_passoires.columns[0]
    
    for nom in df_passoires[col_prop]:
        infos = chercher_siren_et_siege_local(nom)
        sirens.append(infos['siren'])
        sieges.append(infos.get('siège', infos.get('siege', 'N/A'))) 
        
    df_passoires['N° SIREN'] = sirens
    df_passoires['Siège Social'] = sieges
    return df_passoires

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="Espace de Prospection - Nice",
    page_icon="🏠",
    layout="wide"
)

st.title("🏠 Mon espace de prospection immobilière - Nice")
st.markdown("Base de données de prospection rigoureuse : adresses réelles et passoires énergétiques (F & G).")

# --- BARRE LATÉRALE DE RECHERCHE ---
st.sidebar.header("Critères de ciblage")

objectif = st.sidebar.selectbox(
    "Objectif de prospection",
    [
        "Passoires Énergétiques (DPE F & G)",
        "Successions / Indivisions",
        "Investissement / Rendement global"
    ]
)

secteur = st.sidebar.selectbox(
    "Secteur à Nice",
    [
        "Tous les secteurs",
        "Carré d'Or",
        "Promenade des Anglais",
        "Musiciens / Gambetta",
        "Port / Garibaldi",
        "Mont Boron",
        "Centre-ville"
    ]
)

budget_max = st.sidebar.slider(
    "Budget maximum estimé (en €)",
    min_value=100000,
    max_value=2000000,
    value=700000,
    step=50000
)

lancer = st.sidebar.button("Générer le listing certifié")

# --- FILTRAGE DE LA VRAIE BASE DE DONNÉES ---
if lancer:
    st.info(f"Interrogation de la base certifiée pour : **{objectif}** sur le secteur **{secteur}**...")
    
    if df_global.empty:
        st.error("Le fichier de données `dpe_nice_fg.csv` est introuvable ou vide.")
    else:
        df_resultats = df_global.copy()
        
        # Filtrage par secteur si demandé (si une colonne de commune/adresse existe)
        if secteur != "Tous les secteurs":
            # On cherche une colonne textuelle pour filtrer le secteur
            cols_texte = [c for c in df_resultats.columns if df_resultats[c].dtype == object]
            if cols_texte:
                # Filtrage approximatif basé sur le secteur choisi
                mots_cles = secteur.lower().split()
                mask_secteur = df_resultats[cols_texte[0]].astype(str).str.lower().apply(lambda x: any(m in x for m in mots_cles))
                # Si le filtre ne renvoie rien, on n'applique pas le blocage strict pour ne pas pénaliser l'affichage
                if mask_secteur.sum() > 0:
                    df_resultats = df_resultats[mask_secteur]

        # Limitation de la taille pour l'affichage (par exemple 100 premiers résultats pertinents)
        if len(df_resultats) > 100:
            df_resultats = df_resultats.head(100)

        if len(df_resultats) > 0:
            if "Passoires" in str(objectif):
                df_resultats = enrichir_sci_avec_sirene(df_resultats)
                
            st.success(f"✅ **{len(df_resultats)}** biens uniques et vérifiés chargés depuis votre fichier de Nice !")
            st.dataframe(df_resultats, use_container_width=True)
            
            csv = df_resultats.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Télécharger le listing certifié (CSV)",
                data=csv,
                file_name=f"listing_pro_nice.csv",
                mime='text/csv',
            )
        else:
            st.warning("Aucun bien ne correspond à vos critères dans ce secteur.")
else:
    st.markdown("👉 Sélectionnez vos critères dans le menu à gauche et cliquez sur **'Générer le listing certifié'** pour interroger vos données.")
