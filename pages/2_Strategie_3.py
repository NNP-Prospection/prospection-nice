import streamlit as st
import pandas as pd
from datetime import datetime
import os
import requests
import pydeck as pdk

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="Stratégie 3 - Radar VEFA",
    page_icon="🏗️",
    layout="wide"
)

st.title("🏗️ Stratégie 3 : Radar VEFA (Pinel & Fins de Cycles)")
st.markdown("Identification chirurgicale des immeubles neufs (2015-2017) dont les propriétaires bailleurs arrivent en fin d'engagement fiscal (9 ans).")

# --- INITIALISATION DE LA MÉMOIRE ---
if 'df_vefa' not in st.session_state:
    st.session_state.df_vefa = pd.DataFrame()
if 'analyse_vefa_terminee' not in st.session_state:
    st.session_state.analyse_vefa_terminee = False

# --- FONCTION API SIRENE ---
@st.cache_data(show_spinner=False)
def enrichir_avec_sirene(adresse_str):
    try:
        url = "https://recherche-entreprises.api.gouv.fr/recherche"
        reponse = requests.get(url, params={'q': adresse_str, 'per_page': 1}, timeout=3)
        if reponse.status_code == 200:
            data = reponse.json()
            resultats = data.get('results', [])
            if resultats:
                entite = resultats[0]
                nom = entite.get('nom_raison_sociale', '')
                siren = entite.get('siren', '')
                
                dirigeants = entite.get('dirigeants', [])
                nom_gerant = ""
                if dirigeants:
                    nom_gerant = f"{dirigeants[0].get('prenoms', '')} {dirigeants[0].get('nom', '')}".strip().title()
                
                etat_admin = entite.get('etat_administratif', 'A') 
                alerte_bodacc = "Actif"
                if etat_admin == 'C':
                    alerte_bodacc = "🚨 CESSATION / LIQUIDATION"
                
                siege = entite.get('siege', {}).get('adresse', adresse_str).title()
                
                if nom:
                     return {
                        'structure': nom.title(),
                        'siren': siren,
                        'gerant': nom_gerant,
                        'siege': siege,
                        'statut_bodacc': alerte_bodacc
                    }
    except Exception:
        pass
    return None

# --- CHARGEMENT DVF OPTIMISÉ POUR LA VEFA ---
@st.cache_data
def load_dvf_vefa():
    try:
        dossier = None
        for item in os.listdir('.'):
            if os.path.isdir(item) and 'dvf' in item.lower():
                dossier = item
                break
                
        if not dossier:
            return pd.DataFrame() 
            
        fichiers = [os.path.join(dossier, f) for f in os.listdir(dossier) if f.endswith('.csv') or f.endswith('.txt')]
        if not fichiers:
            return pd.DataFrame() 
            
        liste_df = []
        colonnes_utiles = ['date_mutation', 'nature_mutation', 'valeur_fonciere', 'adresse_numero', 'No voie', 'adresse_nom_voie', 'Voie', 'Type de voie', 'nom_commune', 'type_local', 'surface_reelle_bati', 'latitude', 'lat', 'longitude', 'lon']
        
        for f in fichiers:
            try:
                sample = pd.read_csv(f, sep=';', nrows=0)
                if len(sample.columns) < 3:
                     sample = pd.read_csv(f, sep=',', nrows=0)
                     sep = ','
                else:
                     sep = ';'
                     
                cols_a_charger = [c for c in colonnes_utiles if c in sample.columns]
                
                if cols_a_charger:
                    df_temp = pd.read_csv(f, sep=sep, usecols=cols_a_charger, low_memory=False)
                    liste_df.append(df_temp)
            except:
                pass
                
        if not liste_df:
            return pd.DataFrame()
            
        df = pd.concat(liste_df, ignore_index=True).drop_duplicates()
        
        if 'latitude' in df.columns:
            df = df.rename(columns={'latitude': 'lat', 'longitude': 'lon'})
            
        # Filtre STRICT sur la VEFA (Vente en l'État Futur d'Achèvement)
        if 'nature_mutation' in df.columns:
            mask_vefa = df['nature_mutation'].astype(str).str.lower().str.contains("vefa|futur|achèvement", na=False)
            df = df[mask_vefa]
            
        if 'valeur_fonciere' in df.columns and 'surface_reelle_bati' in df.columns and 'lat' in df.columns:
            df = df.dropna(subset=['valeur_fonciere', 'surface_reelle_bati', 'lat', 'lon']).copy()
            df['valeur_fonciere'] = pd.to_numeric(df['valeur_fonciere'].astype(str).str.replace(',', '.'), errors='coerce')
            df['surface_reelle_bati'] = pd.to_numeric(df['surface_reelle_bati'].astype(str).str.replace(',', '.'), errors='coerce')
            df = df[df['surface_reelle_bati'] > 0] 
            df['prix_m2'] = df['valeur_fonciere'] / df['surface_reelle_bati']
            df = df[(df['prix_m2'] > 1000) & (df['prix_m2'] < 25000)]
            
        # --- SUPER DÉTECTEUR D'ADRESSE ---
        def construire_adresse(row):
            cols = row.index.tolist()
            num = ""
            voie = ""
            if 'adresse_numero' in cols and pd.notna(row['adresse_numero']):
                num = str(row['adresse_numero']).replace('.0', '')
            elif 'No voie' in cols and pd.notna(row['No voie']):
                num = str(row['No voie']).replace('.0', '')
            if 'adresse_nom_voie' in cols and pd.notna(row['adresse_nom_voie']):
                voie = str(row['adresse_nom_voie'])
            elif 'Voie' in cols and pd.notna(row['Voie']):
                voie = str(row['Voie'])
                if 'Type de voie' in cols and pd.notna(row['Type de voie']):
                    voie = str(row['Type de voie']) + " " + voie
            
            adresse = f"{num} {voie}".strip().title()
            return adresse if adresse else "Adresse inconnue"
            
        df['Adresse Vente'] = df.apply(construire_adresse, axis=1)
            
        return df
    except Exception as e:
        st.sidebar.error(f"Erreur chargement DVF VEFA : {e}")
        return pd.DataFrame()

df_vefa_brut = load_dvf_vefa()

# --- BARRE LATÉRALE ---
st.sidebar.header("🎯 Ciblage Pinel / VEFA")

secteur = st.sidebar.selectbox(
    "Quartier / Secteur",
    ["Tous les secteurs", "Musiciens (Verdi / Berlioz)", "Centre-ville (Alberti / Angleterre)", "Gustave de Loy", "Louis Cochois / Colonel Musso"]
)

# --- LANCEMENT DE L'ANALYSE VEFA ---
if st.sidebar.button("Détecter les programmes (Lots de ventes groupées)", type="primary"):
    if not df_vefa_brut.empty:
        df_travail = df_vefa_brut.copy()
        
        # Filtre par secteur
        if secteur != "Tous les secteurs":
            rues_quartiers = {
                "Musiciens (Verdi / Berlioz)": ["verdi", "berlioz"],
                "Centre-ville (Alberti / Angleterre)": ["alberti", "angleterre"],
                "Gustave de Loy": ["gustave de loy", "de loy"],
                "Louis Cochois / Colonel Musso": ["louis cochois", "cochois", "colonel musso", "musso"]
            }
            mots_cles = rues_quartiers.get(secteur, [])
            if mots_cles:
                pattern = '|'.join(mots_cles)
                df_travail = df_travail[df_travail['Adresse Vente'].astype(str).str.lower().str.contains(pattern, na=False, regex=True)]

        # Aggrégation pour détecter les programmes neufs (plusieurs ventes à la même adresse)
        df_groupes = df_travail.groupby('Adresse Vente').agg(
            Nombre_Transactions=('Adresse Vente', 'count'),
            Date_Premiere_Vente=('date_mutation', 'min'),
            Date_Derniere_Vente=('date_mutation', 'max'),
            Prix_Moyen=('valeur_fonciere', 'mean'),
            Surface_Moyenne=('surface_reelle_bati', 'mean'),
            Lat=('lat', 'first'),
            Lon=('lon', 'first')
        ).reset_index()
        
        # On ne garde que les adresses avec au moins 3 transactions (signe d'un programme VEFA)
        df_programmes = df_groupes[df_groupes['Nombre_Transactions'] >= 3].sort_values(by='Nombre_Transactions', ascending=False)
        
        st.session_state.df_vefa = df_programmes
        st.session_state.analyse_vefa_terminee = True

# --- AFFICHAGE ---
if st.session_state.analyse_vefa_terminee:
    
    tab1, tab2, tab3 = st.tabs([
        "🏢 1. Programmes Identifiés (Matrice)", 
        "🗺️ 2. Cartographie VEFA",
        "✉️ 3. Plan d'Action Terrain (Publipostage PNO)"
    ])
    
    with tab1:
        st.success(f"✅ Radar activé ! **{len(st.session_state
