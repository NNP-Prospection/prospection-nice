from datetime import datetime
import glob
import os
import xml.etree.ElementTree as ET
import pandas as pd
import pydeck as pdk
import requests
import streamlit as st

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title='Stratégie 1 - Cabinet Honorat', page_icon='🏢', layout='wide'
)


# --- MODULE DE VEILLE AUTOMATIQUE & BANDEAU D'ALERTE LMP / FISCALITÉ ---
@st.cache_data(ttl=1800)
def verifier_alerte_lmp_urgente():
  flux_officiels = [
      'https://www.service-public.fr/professionnels-entreprises/actualites/rss',
      'https://www.service-public.fr/particuliers/actualites/rss',
  ]
  mots_cles_urgents = [
      'lmp',
      'lmnp',
      'amortissement',
      'fiscal',
      'plf',
      'loi de finances',
      'plus-value',
      'bic',
      'meublé',
      'dpe',
  ]
  alertes_critiques = []
  headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

  for url in flux_officiels:
    try:
      reponse = requests.get(url, headers=headers, timeout=3)
      if reponse.status_code == 200:
        root = ET.fromstring(reponse.content)
        for item in root.findall('.//item'):
          titre = (
              item.find('title').text if item.find('title') is not None else ''
          )
          lien = item.find('link').text if item.find('link') is not None else ''
          titre_lower = titre.lower()
          if any(mot in titre_lower for mot in mots_cles_urgents):
            alertes_critiques.append({'titre': titre, 'lien': lien})
    except Exception:
      pass
  return alertes_critiques[:3]


# --- AFFICHAGE DU BANDEAU D'ALERTE SUR LA PAGE ---
urgences_veille = verifier_alerte_lmp_urgente()
if urgences_veille:
  st.error(
      '🚨 **ALERTE ROUGE - VEILLE JURIDIQUE & FISCALE LMP / LMNP /'
      ' MEUBLÉS** 🚨'
  )
  st.write(
      'Un changement ou une actualité législative majeure vient d’être'
      ' interceptée sur les flux officiels de l’État :'
  )
  for alerte in urgences_veille:
    st.markdown(
        f"- **[{alerte['titre']}]({alerte['lien']})** *(Vérifiez l'impact sur"
        ' vos portefeuilles investisseurs)*'
    )
  st.markdown('---')

st.title(
    '🏢 Stratégie 1 : Passoires F/G, Blocage Saisonnier & Cycle de Détention'
)
st.markdown(
    "Approche par l'actif : Urgences énergétiques (DPE F/G), **Impasse Airbnb"
    ' (Zone 3 Nice)**, **Alerte Travaux Copro (RNIC)** et Arbitrage (~5 ans).'
)

# --- INITIALISATION DE LA MÉMOIRE ---
if 'df_affichage' not in st.session_state:
  st.session_state.df_affichage = pd.DataFrame()
if 'analyse_terminee' not in st.session_state:
  st.session_state.analyse_terminee = False


# --- FONCTION DE NETTOYAGE DES NUMÉROS ---
def formater_numero(val):
  if pd.isna(val) or str(val).strip().lower() in [
      'nan',
      'none',
      'null',
      '',
      '<na>',
  ]:
    return ''
  val_str = str(val).strip()
  if val_str.endswith('.0'):
    return val_str[:-2]
  return val_str


# --- FONCTION API SIRENE (INPI & BODACC) ---
@st.cache_data(show_spinner=False)
def enrichir_avec_sirene(adresse_str):
  try:
    url = 'https://recherche-entreprises.api.gouv.fr/recherche'
    reponse = requests.get(
        url, params={'q': adresse_str, 'per_page': 1}, timeout=3
    )
    if reponse.status_code == 200:
      data = reponse.json()
      resultats = data.get('results', [])
      if resultats:
        entite = resultats[0]
        nom = entite.get('nom_raison_sociale', '')
        siren = entite.get('siren', '')

        dirigeants = entite.get('dirigeants', [])
        nom_gerant = ''
        annee_naissance = ''
        if dirigeants:
          nom_gerant = (
              f"{dirigeants[0].get('prenoms', '')}"
              f" {dirigeants[0].get('nom', '')}".strip().title()
          )
          date_naiss = dirigeants[0].get('date_de_naissance', '')
          if date_naiss and len(str(date_naiss)) >= 4:
            annee_naissance = str(date_naiss)[:4]

        etat_admin = entite.get('etat_administratif', 'A')
        alerte_bodacc = 'Actif'
        if etat_admin == 'C':
          alerte_bodacc = '🚨 CESSATION / LIQUIDATION (BODACC)'

        siege = entite.get('siege', {}).get('adresse', adresse_str).title()

        if nom:
          return {
              'structure': nom.title(),
              'siren': siren,
              'gerant': nom_gerant,
              'annee_naissance': annee_naissance,
              'siege': siege,
              'statut_bodacc': alerte_bodacc,
          }
  except Exception:
    pass
  return None


# --- CHARGEMENT DPE, RNIC (COPROS) & DVF ---
@st.cache_data
def load_dpe():
  try:
    fichiers = sorted(glob.glob('dpe_nice_part_*.csv'))
    if fichiers:
      df_total = pd.concat(
          [pd.read_csv(f, low_memory=False) for f in fichiers],
          ignore_index=True,
      )
      return df_total
    return pd.read_csv('dpe_nice_complet.csv', low_memory=False)
  except Exception as e:
    st.sidebar.error(f'Erreur chargement DPE : {e}')
    return pd.DataFrame()


@st.cache_data
def load_rnic():
  fichiers_rnic = glob.glob('*rnic*.csv') + glob.glob('*copro*.csv')
  if fichiers_rnic:
    try:
      df_r = pd.read_csv(fichiers_rnic[0], sep=None, engine='python', low_memory=False)
      return df_r
    except Exception:
      return pd.DataFrame()
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

    fichiers = [
        os.path.join(dossier, f)
        for f in os.listdir(dossier)
        if f.endswith('.csv') or f.endswith('.txt')
    ]
    if not fichiers:
      return pd.DataFrame()

    liste_df = []
    colonnes_utiles = [
        'date_mutation',
        'nature_mutation',
        'valeur_fonciere',
        'adresse_numero',
        'No voie',
        'adresse_nom_voie',
        'Voie',
        'Type de voie',
        'nom_commune',
        'type_local',
        'surface_reelle_bati',
        'latitude',
        'lat',
        'longitude',
        'lon',
    ]

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
          df_temp = pd.read_csv(
              f, sep=sep, usecols=cols_a_charger, low_memory=False
          )
          liste_df.append(df_temp)
      except Exception:
        pass

    if not liste_df:
      return pd.DataFrame()

    df = pd.concat(liste_df, ignore_index=True).drop_duplicates()

    if 'latitude' in df.columns:
      df = df.rename(columns={'latitude': 'lat', 'longitude': 'lon'})
    if (
        'valeur_fonciere' in df.columns
        and 'surface_reelle_bati' in df.columns
        and 'lat' in df.columns
    ):
      df = df.dropna(
          subset=['valeur_fonciere', 'surface_reelle_bati', 'lat', 'lon']
      ).copy()
      df['valeur_fonciere'] = pd.to_numeric(
          df['valeur_fonciere'].astype(str).str.replace(',', '.'),
          errors='coerce',
      )
      df['surface_reelle_bati'] = pd.to_numeric(
          df['surface_reelle_bati'].astype(str).str.replace(',', '.'),
          errors='coerce',
      )
      df = df[df['surface_reelle_bati'] > 0]
      df['prix_m2'] = df['valeur_fonciere'] / df['surface_reelle_bati']
      df = df[(df['prix_m2'] > 1000) & (df['prix_m2'] < 25000)]
    return df
  except Exception as e:
    st.sidebar.error(f'Erreur chargement DVF : {e}')
    return pd.DataFrame()


df_global = load_dpe()
df_rnic = load_rnic()
df_dvf = load_dvf()

# --- BARRE LATÉRALE DE RECHERCHE ---
st.sidebar.header('🎯 Critères de ciblage')

objectif = st.sidebar.selectbox(
    'Axe de prospection',
    [
        'Urgence Réglementaire (Passoires F & G)',
        '🚫 Impasse Location Saisonnière / Airbnb (Nice Zone 3)',
        '🏗️ Alerte Travaux Copro / Concentration DPE (RNIC)',
        'Arbitrage Patrimonial (Cycle ~5 ans)',
    ],
)

secteur = st.sidebar.selectbox(
    'Quartier / Secteur',
    [
        "Carré d'Or",
        'Tous les secteurs',
        'Promenade des Anglais',
        'Musiciens / Gambetta',
        'Port / Garibaldi',
        'Mont Boron',
        'Centre-ville',
    ],
)

tranche_mois = st.sidebar.selectbox(
    'Choisir le lot à analyser',
    [
        'Lot 1 (1 - 50)',
        'Lot 2 (51 - 100)',
        'Lot 3 (101 - 150)',
        'Lot 4 (151 - 200)',
        'Lot 5 (201 - 250)',
    ],
)

# --- LANCEMENT ---
if st.sidebar.button('Générer le listing certifié', type='primary'):
  if not df_global.empty:
    df_resultats = df_global.copy()

    colonnes_a_garder = {}
    for col in ['adresse_ban', 'adresse_brute', 'adresse_propriete']:
      if col in df_resultats.columns:
        colonnes_a_garder[col] = 'Adresse Exacte'
        break

    cibles = {
        'Étage': False,
        'N° Apt': False,
        '
