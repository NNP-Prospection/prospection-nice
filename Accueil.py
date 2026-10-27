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
  """Charge le fichier RNIC (Copropriétés Nice) s'il est présent dans le dossier."""
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
        'N° Lot': False,
        'Bâtiment': False,
        'Surface m²': False,
        'Année Const.': False,
        'Note DPE': False,
        'Date DPE': False,
    }

    for col in df_resultats.columns:
      c = col.lower()
      if not cibles['Étage'] and ('etage' in c or 'niveau' in c):
        colonnes_a_garder[col] = 'Étage'
        cibles['Étage'] = True
      elif not cibles['N° Apt'] and (
          'appartement' in c or 'porte' in c or 'numero_appt' in c
      ):
        colonnes_a_garder[col] = 'N° Apt'
        cibles['N° Apt'] = True
      elif not cibles['N° Lot'] and 'lot' in c and 'surface' not in c:
        colonnes_a_garder[col] = 'N° Lot'
        cibles['N° Lot'] = True
      elif not cibles['Bâtiment'] and ('batiment' in c or 'bat' in c):
        colonnes_a_garder[col] = 'Bâtiment'
        cibles['Bâtiment'] = True
      elif not cibles['Surface m²'] and (
          'surface_habitable' in c or 'surface_thermique_lot' in c or 'surface' in c
      ):
        colonnes_a_garder[col] = 'Surface m²'
        cibles['Surface m²'] = True
      elif not cibles['Année Const.'] and (
          'annee_construction' in c or 'periode_construction' in c
      ):
        colonnes_a_garder[col] = 'Année Const.'
        cibles['Année Const.'] = True
      elif not cibles['Note DPE'] and 'etiquette' in c and 'dpe' in c:
        colonnes_a_garder[col] = 'Note DPE'
        cibles['Note DPE'] = True
      elif not cibles['Date DPE'] and 'date' in c and 'dpe' in c:
        colonnes_a_garder[col] = 'Date DPE'
        cibles['Date DPE'] = True

    df_affichage = df_resultats[list(colonnes_a_garder.keys())].rename(
        columns=colonnes_a_garder
    )

    colonnes_doublons = [
        col
        for col in ['Adresse Exacte', 'N° Apt', 'Étage', 'Date DPE']
        if col in df_affichage.columns
    ]
    if colonnes_doublons:
      df_affichage = df_affichage.drop_duplicates(
          subset=colonnes_doublons, keep='first'
      )

    # Calcul de la concentration de DPE par immeuble (Signal RNIC / AG Travaux)
    if 'Adresse Exacte' in df_affichage.columns:
      comptage_immeuble = (
          df_affichage['Adresse Exacte'].value_counts().to_dict()
      )
      df_affichage['DPE Immeuble'] = df_affichage['Adresse Exacte'].map(
          comptage_immeuble
      )
    else:
      df_affichage['DPE Immeuble'] = 1

    has_apt = 'N° Apt' in df_affichage.columns
    has_etage = 'Étage' in df_affichage.columns
    valeurs_vides = ['nan', 'none', 'null', '', '<na>']

    if has_apt and has_etage:
      mask_apt_valide = (
          ~df_affichage['N° Apt']
          .astype(str)
          .str.strip()
          .str.lower()
          .isin(valeurs_vides)
      )
      mask_etage_valide = (
          ~df_affichage['Étage']
          .astype(str)
          .str.strip()
          .str.lower()
          .isin(valeurs_vides)
      )
      df_affichage = df_affichage[mask_apt_valide | mask_etage_valide]
    elif has_apt:
      mask_apt_valide = (
          ~df_affichage['N° Apt']
          .astype(str)
          .str.strip()
          .str.lower()
          .isin(valeurs_vides)
      )
      df_affichage = df_affichage[mask_apt_valide]
    elif has_etage:
      mask_etage_valide = (
          ~df_affichage['Étage']
          .astype(str)
          .str.strip()
          .str.lower()
          .isin(valeurs_vides)
      )
      df_affichage = df_affichage[mask_etage_valide]

    # Dictionnaire enrichi des artères (Carré d'Or complet)
    rues_quartiers = {
        "Carré d'Or": [
            'france',
            'massena',
            'paradis',
            'suede',
            'verdun',
            'meyerbeer',
            'congres',
            'cronstadt',
            'buffa',
            'alphonse karr',
            'maccarani',
            'liberte',
            'longchamp',
            'grimaldi',
            'dalpozzo',
            'halevy',
            'marechal joffre',
            'rivoli',
        ],
        'Promenade des Anglais': [
            'promenade des anglais',
            'etats-unis',
            'quai des etats-unis',
        ],
        'Port / Garibaldi': [
            'garibaldi',
            'lunel',
            'cassini',
            'barla',
            'arson',
            'republique',
            'port',
            'segurane',
            'fodere',
        ],
        'Mont Boron': [
            'mont boron',
            'jean lorrain',
            'carnot',
            'germaine',
            'andre joly',
            'valrose',
            'cap de nice',
            'maeterlinck',
        ],
        'Musiciens / Gambetta': [
            'gambetta',
            'berlioz',
            'gounod',
            'rossini',
            'verdi',
            'clemenceau',
            'victor hugo',
            'mozart',
            ' paganini',
            'thiers',
        ],
        'Centre-ville': [
            'jean medecin',
            'gioffredo',
            'marechal foch',
            'pastorelli',
            'assalit',
            'durandy',
            'hotel des postes',
            'dubouchage',
        ],
    }

    if secteur != 'Tous les secteurs':
      mots_cles = rues_quartiers.get(secteur, [])
      if 'Adresse Exacte' in df_affichage.columns and mots_cles:
        pattern = '|'.join(mots_cles)
        df_affichage = df_affichage[
            df_affichage['Adresse Exacte']
            .astype(str)
            .str.lower()
            .str.contains(pattern, na=False, regex=True)
        ]

    if 'Date DPE' in df_affichage.columns:
      df_affichage = df_affichage.sort_values(by='Date DPE', ascending=False)
      date_actuelle = datetime.now()
      statuts_mandats = []
      alertes_saisonnier_copro = []

      mots_cles_zone3_airbnb = (
          rues_quartiers["Carré d'Or"]
          + rues_quartiers['Promenade des Anglais']
          + rues_quartiers['Port / Garibaldi']
          + rues_quartiers['Musiciens / Gambetta']
      )

      for index, row in df_affichage.iterrows():
        d = row.get('Date DPE', '')
        note = str(row.get('Note DPE', '')).strip().upper()
        adresse_str = str(row.get('Adresse Exacte', '')).lower()
        nb_dpe_imm = int(row.get('DPE Immeuble', 1))

        # Evaluation de la surface pour ciblage Airbnb / Location saisonnière
        surf_val = pd.to_numeric(row.get('Surface m²', None), errors='coerce')
        est_petite_surface = (pd.isna(surf_val)) or (surf_val <= 50)
        est_zone_tendue_airbnb = any(
            k in adresse_str for k in mots_cles_zone3_airbnb
        )

        # Signaux croisés : Piste 3 (Airbnb) + Piste 2 (RNIC / Copro) + Piste 5 (THRS)
        signaux = []
        if note in ['F', 'G'] and est_zone_tendue_airbnb and est_petite_surface:
          signaux.append('🚫 Impasse Airbnb (Zone 3)')
        if nb_dpe_imm >= 3:
          signaux.append(f'🏗️ Copro active ({nb_dpe_imm} DPE)')
        if any(
            k in adresse_str
            for k in rues_quartiers["Carré d'Or"]
            + rues_quartiers['Promenade des Anglais']
        ):
          signaux.append('🏛️ Cible THRS / Vacant')

        alertes_saisonnier_copro.append(
            ' | '.join(signaux) if signaux else 'Standard'
        )

        # Cycle 5 ans & Statut principal
        est_secteur_cle = any(
            k in adresse_str
            for k in [
                'promenade des anglais',
                'mont boron',
                'quai',
                'france',
                'massena',
                'paradis',
                'buffa',
                'victor hugo',
            ]
        )

        try:
          dt_dpe = pd.to_datetime(d)
          diff_annees = date_actuelle.year - dt_dpe.year
          est_cycle_5ans = 4 <= diff_annees <= 6 or est_secteur_cle

          if note in ['F', 'G']:
            if est_cycle_5ans:
              statuts_mandats.append(f'🏖️ Cycle ~5 ans (Passoire {note})')
            else:
              statuts_mandats.append(f'⏳ Passoire {note} Standard')
          else:
            note_aff = note if note and note in 'ABCDE' else 'A-E'
            if est_cycle_5ans:
              statuts_mandats.append(f'📈 Cycle ~5 ans (Classe {note_aff})')
            else:
              statuts_mandats.append(f'🏷️ Standard (Classe {note_aff})')
        except Exception:
          statuts_mandats.append('📅 À qualifier')

      df_affichage['Profil & Stratégie'] = statuts_mandats
      df_affichage['Signaux Data (Airbnb / Copro / THRS)'] = (
          alertes_saisonnier_copro
      )

    # Filtrage selon l'objectif choisi dans la barre latérale
    if (
        objectif == 'Urgence Réglementaire (Passoires F & G)'
        and 'Profil & Stratégie' in df_affichage.columns
    ):
      df_affichage = df_affichage[
          df_affichage['Profil & Stratégie'].str.contains('Passoire', na=False)
      ]
    elif (
        objectif == '🚫 Impasse Location Saisonnière / Airbnb (Nice Zone 3)'
        and 'Signaux Data (Airbnb / Copro / THRS)' in df_affichage.columns
    ):
      df_affichage = df_affichage[
          df_affichage['Signaux Data (Airbnb / Copro / THRS)'].str.contains(
              'Impasse Airbnb', na=False
          )
      ]
    elif (
        objectif == '🏗️ Alerte Travaux Copro / Concentration DPE (RNIC)'
        and 'Signaux Data (Airbnb / Copro / THRS)' in df_affichage.columns
    ):
      df_affichage = df_affichage[
          df_affichage['Signaux Data (Airbnb / Copro / THRS)'].str.contains(
              'Copro active', na=False
          )
      ]
    elif (
        objectif == 'Arbitrage Patrimonial (Cycle ~5 ans)'
        and 'Profil & Stratégie' in df_affichage.columns
    ):
      df_affichage = df_affichage[
          df_affichage['Profil & Stratégie'].str.contains(
              'Cycle ~5 ans', na=False
          )
      ]

    index_debut = (int(tranche_mois.split()[1]) - 1) * 50
    st.session_state.df_affichage = df_affichage.iloc[
        index_debut : index_debut + 50
    ]
    st.session_state.analyse_terminee = True

# --- AFFICHAGE ---
if st.session_state.analyse_terminee:
  tab1, tab2, tab3, tab4 = st.tabs([
      '📊 1. Listing & Signaux Croisés',
      '🏖️ 2. Focus Saisonnier & Cycle ~5 ans',
      '✉️ 3. Publipostage Sur-Mesure & SIRENE',
      '💶 4. Valeurs Foncières (DVF & Cartographie)',
  ])

  with tab1:
    col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
    nb_total = len(st.session_state.df_affichage)
    nb_airbnb = (
        st.session_state.df_affichage['Signaux Data (Airbnb / Copro / THRS)']
        .str.contains('Impasse Airbnb', na=False)
        .sum()
        if 'Signaux Data (Airbnb / Copro / THRS)'
        in st.session_state.df_affichage.columns
        else 0
    )
    nb_copro = (
        st.session_state.df_affichage['Signaux Data (Airbnb / Copro / THRS)']
        .str.contains('Copro active', na=False)
        .sum()
        if 'Signaux Data (Airbnb / Copro / THRS)'
        in st.session_state.df_affichage.columns
        else 0
    )

    col_kpi1.metric('🎯 Biens routables (Lot actif)', f'{nb_total} lots')
    col_kpi2.metric(
        '🚫 Impasse Airbnb (Zone 3 F/G)',
        f'{nb_airbnb} cibles',
        'Changement usage bloqué',
    )
    col_kpi3.metric(
        '🏗️ Copropriétés sous tension (≥3 DPE)',
        f'{nb_copro} lots',
        'Potentiel appel de fonds / AG',
    )

    event_selection = st.dataframe(
        st.session_state.df_affichage,
        use_container_width=True,
        on_select='rerun',
        selection_mode='multi-row',
        hide_index=True,
    )
    st.download_button(
        '📥 Télécharger ce lot qualifié (CSV)',
        data=st.session_state.df_affichage.to_csv(index=False).encode('utf-8'),
        file_name='listing_dpe_enrichi_honorat.csv',
        mime='text/csv',
    )

  with tab2:
    st.subheader(
        "🔍 Filtre rapide : Biens en Impasse Saisonnière ou Cycle ~5 ans"
    )
    if "Profil & Stratégie" in st.session_state.df_affichage.columns:
      df_cycle = st.session_state.df_affichage[
          st.session_state.df_affichage["Profil & Stratégie"].str.contains(
              "Cycle ~5 ans", na=False
          )
          | st.session_state.df_affichage[
              "Signaux Data (Airbnb / Copro / THRS)"
          ].str.contains("Impasse Airbnb", na=False)
      ]
      if not df_cycle.empty:
        st.dataframe(df_cycle, use_container_width=True, hide_index=True)
      else:
        st.info("ℹ️ Aucun bien correspondant dans ce lot.")
        
