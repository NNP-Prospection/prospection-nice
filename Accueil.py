# **Code Python - Application Streamlit Stratégie 1**

import streamlit as st
import pandas as pd
from datetime import datetime
import os
import requests
import pydeck as pdk

# --- CONFIGURATION DE LA PAGE ---

st.set_page_config(
    page_title="Stratégie 1 - Cabinet Honorat",
    page_icon="🏢",
    layout="wide"
)

st.title("🏢 Stratégie 1 : Passoires F/G & Cycle de Détention (5 ans)")

st.markdown("Approche par l'actif : Identification des urgences énergétiques (DPE), des opportunités d'arbitrage (~5 ans) et analyse DVF.")

# --- INITIALISATION DE LA MÉMOIRE ---

if 'df_affichage' not in st.session_state:
    st.session_state.df_affichage = pd.DataFrame()

if 'analyse_terminee' not in st.session_state:
    st.session_state.analyse_terminee = False

# --- FONCTION DE NETTOYAGE DES NUMÉROS ---

def formater_numero(val):
    if pd.isna(val) or str(val).strip().lower() in ['nan', 'none', 'null', '', '<na>']:
        return ''
    val_str = str(val).strip()
    if val_str.endswith('.0'):
        return val_str[:-2]
    return val_str

# --- FONCTION API SIRENE (INPI & BODACC) ---

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
                    alerte_bodacc = "🚨 CESSATION / LIQUIDATION (BODACC)"
                
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

# --- CHARGEMENT DPE & DVF (AVEC OPTIMISATION MÉMOIRE) ---

@st.cache_data
def load_dpe():
    try:
        return pd.read_csv('dpe_nice_fg.csv', low_memory=False)
    except:
        return pd.DataFrame()

@st.cache_data
def load_dvf():
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
        # Optimisation : On ne charge que les colonnes utiles pour éviter de saturer la RAM
        colonnes_utiles = ['date_mutation', 'nature_mutation', 'valeur_fonciere', 'adresse_numero', 'No voie', 'adresse_nom_voie', 'Voie', 'Type de voie', 'nom_commune', 'type_local', 'surface_reelle_bati', 'latitude', 'lat', 'longitude', 'lon']
        
        for f in fichiers:
            try:
                # Lecture d'un échantillon pour voir quelles colonnes existent dans ce fichier
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
        
        # Nettoyage et formatage
        if 'latitude' in df.columns:
            df = df.rename(columns={'latitude': 'lat', 'longitude': 'lon'})
        if 'valeur_fonciere' in df.columns and 'surface_reelle_bati' in df.columns and 'lat' in df.columns:
            df = df.dropna(subset=['valeur_fonciere', 'surface_reelle_bati', 'lat', 'lon']).copy()
            df['valeur_fonciere'] = pd.to_numeric(df['valeur_fonciere'].astype(str).str.replace(',', '.'), errors='coerce')
            df['surface_reelle_bati'] = pd.to_numeric(df['surface_reelle_bati'].astype(str).str.replace(',', '.'), errors='coerce')
            df = df[df['surface_reelle_bati'] > 0] 
            df['prix_m2'] = df['valeur_fonciere'] / df['surface_reelle_bati']
            df = df[(df['prix_m2'] > 1000) & (df['prix_m2'] < 25000)]
        return df
    except Exception as e:
        st.sidebar.error(f"Erreur chargement DVF : {e}")
        return pd.DataFrame()

df_global = load_dpe()
df_dvf = load_dvf()

# --- BARRE LATÉRALE DE RECHERCHE ---

st.sidebar.header("🎯 Critères de ciblage")

objectif = st.sidebar.selectbox(
    "Axe de prospection",
    ["Urgence Réglementaire (Passoires F & G)", "Arbitrage Patrimonial (Cycle ~5 ans)"]
)

secteur = st.sidebar.selectbox(
    "Quartier / Secteur",
    ["Tous les secteurs", "Carré d'Or", "Promenade des Anglais", "Port / Garibaldi", "Mont Boron", "Musiciens / Gambetta", "Centre-ville"]
)

tranche_mois = st.sidebar.selectbox("Choisir le lot à analyser", ["Lot 1 (1 - 50)", "Lot 2 (51 - 100)", "Lot 3 (101 - 150)", "Lot 4 (151 - 200)", "Lot 5 (201 - 250)"])

# --- LANCEMENT ---

if st.sidebar.button("Générer le listing certifié", type="primary"):
    if not df_global.empty:
        df_resultats = df_global.copy()
        
        colonnes_a_garder = {}
        for col in ['adresse_ban', 'adresse_brute', 'adresse_propriete']:
            if col in df_resultats.columns:
                colonnes_a_garder[col] = 'Adresse Exacte'
                break
                
        cibles = {'Étage': False, 'N° Apt': False, 'N° Lot': False, 'Bâtiment': False, 'Note DPE': False, 'Date DPE': False}
        
        for col in df_resultats.columns:
            c = col.lower()
            if not cibles['Étage'] and ('etage' in c or 'niveau' in c):
                colonnes_a_garder[col] = 'Étage'
                cibles['Étage'] = True
            elif not cibles['N° Apt'] and ('appartement' in c or 'porte' in c or 'numero_appt' in c):
                colonnes_a_garder[col] = 'N° Apt'
                cibles['N° Apt'] = True
            elif not cibles['N° Lot'] and ('lot' in c):
                colonnes_a_garder[col] = 'N° Lot'
                cibles['N° Lot'] = True
            elif not cibles['Bâtiment'] and ('batiment' in c or 'bat' in c):
                colonnes_a_garder[col] = 'Bâtiment'
                cibles['Bâtiment'] = True
            elif not cibles['Note DPE'] and ('etiquette' in c and 'dpe' in c):
                colonnes_a_garder[col] = 'Note DPE'
                cibles['Note DPE'] = True
            elif not cibles['Date DPE'] and ('date' in c and 'dpe' in c):
                colonnes_a_garder[col] = 'Date DPE'
                cibles['Date DPE'] = True
        df_affichage = df_resultats[list(colonnes_a_garder.keys())].rename(columns=colonnes_a_garder)
        
        colonnes_doublons = [col for col in ['Adresse Exacte', 'N° Apt', 'Étage', 'Date DPE'] if col in df_affichage.columns]
        if colonnes_doublons:
            df_affichage = df_affichage.drop_duplicates(subset=colonnes_doublons, keep='first')
        has_apt = 'N° Apt' in df_affichage.columns
        has_etage = 'Étage' in df_affichage.columns
        valeurs_vides = ['nan', 'none', 'null', '', '<na>']
        if has_apt and has_etage:
            mask_apt_valide = ~df_affichage['N° Apt'].astype(str).str.strip().str.lower().isin(valeurs_vides)
            mask_etage_valide = ~df_affichage['Étage'].astype(str).str.strip().str.lower().isin(valeurs_vides)
            df_affichage = df_affichage[mask_apt_valide | mask_etage_valide]
        elif has_apt:
            mask_apt_valide = ~df_affichage['N° Apt'].astype(str).str.strip().str.lower().isin(valeurs_vides)
            df_affichage = df_affichage[mask_apt_valide]
        elif has_etage:
            mask_etage_valide = ~df_affichage['Étage'].astype(str).str.strip().str.lower().isin(valeurs_vides)
            df_affichage = df_affichage[mask_etage_valide]
        if secteur != "Tous les secteurs":
            rues_quartiers = {
                "Carré d'Or": ["france", "massena", "paradis", "suede", "verdun", "meyerbeer", "congres", "cronstadt"],
                "Promenade des Anglais": ["promenade des anglais", "etats-unis", "quai des etats-unis"],
                "Port / Garibaldi": ["garibaldi", "lunel", "cassini", "barla", "arson", "republique", "port"],
                "Mont Boron": ["mont boron", "jean lorrain", "carnot", "germaine", "andre joly", "valrose", "cap de nice"],
                "Musiciens / Gambetta": ["gambetta", "berlioz", "gounod", "rossini", "verdi", "clemenceau", "victor hugo"],
                "Centre-ville": ["jean medecin", "gioffredo", "marechal foch", "pastorelli", "assalit", "durandy"]
            }
            mots_cles = rues_quartiers.get(secteur, [])
            if 'Adresse Exacte' in df_affichage.columns and mots_cles:
                pattern = '|'.join(mots_cles)
                df_affichage = df_affichage[df_affichage['Adresse Exacte'].astype(str).str.lower().str.contains(pattern, na=False, regex=True)]
        if 'Date DPE' in df_affichage.columns:
            df_affichage = df_affichage.sort_values(by='Date DPE', ascending=False)
            date_actuelle = datetime.now()
            statuts_mandats = []
            
            for index, row in df_affichage.iterrows():
                d = row['Date DPE']
                adresse_str = str(row.get('Adresse Exacte', '')).lower()
                est_secteur_cle = any(k in adresse_str for k in ["promenade des anglais", "mont boron", "quai", "france", "massena", "paradis"])
                
                try:
                    dt_dpe = pd.to_datetime(d)
                    diff_annees = date_actuelle.year - dt_dpe.year
                    if 4 <= diff_annees <= 6 or est_secteur_cle:
                        statuts_mandats.append("🗖️ Cycle ~5 ans (Passoire F/G)")
                    else:
                        statuts_mandats.append("⏳ Passoire F/G Standard")
                except:
                    statuts_mandats.append("📅 À qualifier")
                    
            df_affichage['Profil & Stratégie'] = statuts_mandats
        if objectif == "Arbitrage Patrimonial (Cycle ~5 ans)" and 'Profil & Stratégie' in df_affichage.columns:
            df_affichage = df_affichage[df_affichage['Profil & Stratégie'].str.contains("Cycle ~5 ans", na=False)]
        index_debut = (int(tranche_mois.split()[1]) - 1) * 50
        st.session_state.df_affichage = df_affichage.iloc[index_debut:index_debut + 50]
        st.session_state.analyse_terminee = True

# --- AFFICHAGE ---

if st.session_state.analyse_terminee:
    
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 1. Listing & Repères", 
        "🗖️ 2. Cycle ~5 ans (DPE)", 
        "✉️ 3. Publipostage & Impression",
        "🗶️ 4. Valeurs Foncières (DVF & Cartographie)"
    ])
    
    with tab1:
        st.success(f"✅ Listing généré ! **{len(st.session_state.df_affichage)}** biens routables ciblés.")
        event_selection = st.dataframe(st.session_state.df_affichage, use_container_width=True, on_select="rerun", selection_mode="multi-row", hide_index=True)
        st.download_button("📥 Télécharger (CSV)", data=st.session_state.df_affichage.to_csv(index=False).encode('utf-8'), file_name="listing_dpe.csv", mime='text/csv')
    with tab2:
        if 'Profil & Stratégie' in st.session_state.df_affichage.columns:
            df_cycle = st.session_state.df_affichage[st.session_state.df_affichage['Profil & Stratégie'].str.contains("Cycle ~5 ans", na=False)]
