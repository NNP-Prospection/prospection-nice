from datetime import datetime
import glob
import os
import pandas as pd
import pydeck as pdk
import requests
import streamlit as st

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title='Stratégie 1 - Cabinet Honorat', page_icon='🏢', layout='wide'
)

import xml.etree.ElementTree as ET


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
        val_imm = row.get('DPE Immeuble', 1)
nb_dpe_imm = int(val_imm) if pd.notna(val_imm) and str(val_imm).isdigit() else 1

        surf_val = pd.to_numeric(row.get('Surface m²', None), errors='coerce')
        est_petite_surface = (pd.isna(surf_val)) or (surf_val <= 50)
        est_zone_tendue_airbnb = any(
            k in adresse_str for k in mots_cles_zone3_airbnb
        )

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
        '🔍 Filtre rapide : Biens en Impasse Saisonnière ou Cycle ~5 ans'
    )
    if 'Profil & Stratégie' in st.session_state.df_affichage.columns:
      df_cycle = st.session_state.df_affichage[
          st.session_state.df_affichage['Profil & Stratégie'].str.contains(
              'Cycle ~5 ans', na=False
          )
          | st.session_state.df_affichage[
              'Signaux Data (Airbnb / Copro / THRS)'
          ].str.contains('Impasse Airbnb', na=False)
      ]
      if not df_cycle.empty:
        st.dataframe(df_cycle, use_container_width=True, hide_index=True)
      else:
        st.info('ℹ️ Aucun bien correspondant dans ce lot.')

  with tab3:
    if "Adresse Exacte" in st.session_state.df_affichage.columns:
      liste_adresses = (
          st.session_state.df_affichage["Adresse Exacte"]
          .dropna()
          .unique()
          .tolist()
      )

      lignes_sel = []
      if 'event_selection' in locals() and event_selection and isinstance(event_selection, dict):
          lignes_sel = event_selection.get('selection', {}).get('rows', [])

      adresses_defaut = [
          liste_adresses[i] for i in lignes_sel if i < len(liste_adresses)
      ]
      if not adresses_defaut and liste_adresses:
          adresses_defaut = liste_adresses[:5]

      col_sel, col_angle = st.columns([2, 1])
      with col_sel:
          adresses_selectionnees = st.multiselect(
              "📍 Adresses sélectionnées pour le publipostage :",
              liste_adresses,
              default=adresses_defaut,
              key="multiselect_adresses_publi"
          )
      with col_angle:
          angle_courrier = st.selectbox(
              "🎯 Angle d’attaque du courrier :",
              [
                  "Automatique (Selon les signaux du bien)",
                  "1. Impasse Location Saisonnière & Quotas Nice (Zone 3)",
                  "2. Travaux de Copropriété & Rénovation Énergétique (RNIC)",
                  "3. Pression Fiscale Résidence Secondaire (THRS) & Vacance",
                  "4. Arbitrage Patrimonial Classique (Cycle ~5 ans / Plus-value)",
              ],
              key="select_angle_courrier"
          )

      if adresses_selectionnees:
          date_jour = datetime.now().strftime("%d/%m/%Y")
          if st.button("🖨️ Préparer l'impression groupée", type="primary", key="btn_impression_gp"):
              st.success("📄 Courriers prêts pour l’impression.")

          for adresse in adresses_selectionnees:
              df_filtre_adr = st.session_state.df_affichage[
                  st.session_state.df_affichage["Adresse Exacte"] == adresse
              ]
              if df_filtre_adr.empty:
                  continue
              ligne_bien = df_filtre_adr.iloc[0]

              infos_sirene = enrichir_avec_sirene(adresse)

              apt = formater_numero(ligne_bien.get("N° Apt", ""))
              lot = formater_numero(ligne_bien.get("N° Lot", ""))
              etage = formater_numero(ligne_bien.get("Étage", ""))
              bat = formater_numero(ligne_bien.get("Bâtiment", ""))
              surf = formater_numero(ligne_bien.get("Surface m²", ""))
              note_dpe = str(ligne_bien.get("Note DPE", "")).strip().upper()
              profil_bien = str(ligne_bien.get("Profil & Stratégie", ""))
              signaux_bien = str(
                  ligne_bien.get("Signaux Data (Airbnb / Copro / THRS)", "")
              )
              nb_dpe_imm = int(ligne_bien.get("DPE Immeuble", 1))

              infos_repere = []
              if bat:
                  infos_repere.append(f"Bât. {bat}")
              if etage:
                  infos_repere.append(f"Étage : {etage}")
              if apt:
                  infos_repere.append(f"Apt {apt}")
              if lot:
                  infos_repere.append(f"Lot n° {lot}")
              if surf:
                  infos_repere.append(f"{surf} m²")
              str_reperage = (
                  " | ".join(infos_repere) if infos_repere else "Bien identifié"
              )

              st.markdown(f"### 📍 {adresse.title()} — Ciblage : `{str_reperage}`")

              destinataire_nom = "Propriétaire / Copropriétaire"
              appel_destinataire = (
                  f"Madame, Monsieur (Propriétaire du lot - {str_reperage}),"
              )
              if infos_sirene:
                  annee_info = (
                      f" (Né en {infos_sirene['annee_naissance']})"
                      if infos_sirene.get("annee_naissance")
                      else ""
                  )
                  st.info(
                      f"🏢 **Entité détectée à cette adresse (API INPI) :**"
                      f" {infos_sirene['structure']} (SIREN : {infos_sirene['siren']})"
                      f" | **Dirigeant :** {infos_sirene['gerant'] or 'Non renseigné'}{annee_info}"
                      f" | **Statut :** {infos_sirene['statut_bodacc']}"
                  )
                  if infos_sirene.get("gerant"):
                      utiliser_gerant = st.checkbox(
                          f"Adresser le courrier à {infos_sirene['gerant']} ({infos_sirene['structure']})",
                          value=False,
                          key=f"chk_sirene_{adresse}",
                      )
                      if utiliser_gerant:
                          destinataire_nom = (
                              f"{infos_sirene['structure']} - À l'attention de"
                              f" {infos_sirene['gerant']}"
                          )
                          appel_destinataire = f"Madame, Monsieur {infos_sirene['gerant']},"

              choix_effectif = angle_courrier
              if angle_courrier == "Automatique (Selon les signaux du bien)":
                  if "Impasse Airbnb" in signaux_bien:
                      choix_effectif = (
                          "1. Impasse Location Saisonnière & Quotas Nice (Zone 3)"
                      )
                  elif "Copro active" in signaux_bien:
                      choix_effectif = (
                          "2. Travaux de Copropriété & Rénovation Énergétique (RNIC)"
                      )
                  elif "Passoire" in profil_bien or note_dpe in ['F', 'G']:
                      choix_effectif = (
                          "3. Pression Fiscale Résidence Secondaire (THRS) & Vacance"
                      )
                  else:
                      choix_effectif = (
                          "4. Arbitrage Patrimonial Classique (Cycle ~5 ans / Plus-value)"
                      )

              if choix_effectif.startswith("1."):
                  objet_courrier = (
                      "Réglementation des meublés de tourisme à Nice, DPE et"
                      f" arbitrage patrimonial — {adresse.title()} ({str_reperage})"
                  )
                  paragraphe_strategique = (
                      "Le durcissement simultané de la réglementation métropolitaine"
                      " niçoise sur les meublés de tourisme (quotas stricts en Zone"
                      " 3 hypercentre et obligation de justifier d’un DPE classé"
                      " entre A et E pour obtenir ou renouveler une autorisation de"
                      " changement d’usage) et de la fiscalité locative place"
                      " aujourd’hui de nombreux propriétaires devant un choix"
                      " stratégique.\n\nPlutôt que de subir une immobilisation"
                      " locative ou des travaux énergétiques lourds à la rentabilité"
                      " incertaine, une cession optimisée sur le marché actuel du"
                      " Carré d’Or permet de cristalliser votre plus-value nette"
                      " auprès d’acquéreurs patrimoniaux ciblés."
                  )
              elif choix_effectif.startswith("2."):
                  objet_courrier = (
                      "Évolution énergétique de votre copropriété et étude"
                      f" d’arbitrage — {adresse.title()} ({str_reperage})"
                  )
                  paragraphe_strategique = (
                      f"Nous observons actuellement une forte activité diagnostique"
                      f" au sein de votre immeuble ({nb_dpe_imm} diagnostics"
                      " enregistrés récemment), signe fréquent d’une réflexion"
                      " collective sur la rénovation énergétique, le ravalement ou la"
                      " mise en conformité des lots.\n\nDans les immeubles bourgeois"
                      " niçois, le vote d’appels de fonds importants en Assemblée"
                      " Générale pèse directement sur le rendement net des"
                      " copropriétaires. Étudier la valorisation de votre lot en"
                      " amont de ces échéances vous permet d’arbitrer sereinement et"
                      " de préserver votre capital."
                  )
              elif choix_effectif.startswith("3."):
                  objet_courrier = (
                      "Pression fiscale (THRS / DPE) et valorisation de votre actif"
                      f" au {adresse.title()} ({str_reperage})"
                  )
                  paragraphe_strategique = (
                      "La détention d’un actif immobilier dans le cœur de Nice fait"
                      " face aujourd’hui à une double pression : les contraintes du"
                      " calendrier énergétique (classes F et G) et la majoration"
                      " maximale de la Taxe d’Habitation sur les Résidences"
                      " Secondaires et logements peu occupés.\n\nAfin d’éviter que"
                      " ces charges et obligations de travaux n’érodent votre"
                      " patrimoine, notre Cabinet réalise pour vous une simulation"
                      " complète comparant le coût de conservation (travaux, fiscalité)"
                      " au capital net que vous dégageriez immédiatement en cas de"
                      " cession."
                  )
              else:
                  objet_courrier = (
                      "Optimisation patrimoniale et opportunité d’arbitrage pour"
                      f" votre actif au {adresse.title()} ({str_reperage})"
                  )
                  paragraphe_strategique = (
                      "Dans le cadre d’une gestion dynamique de votre patrimoine"
                      " immobilier et au regard des conditions de marché actuelles"
                      " sur les secteurs les plus recherchés de Nice (notamment après"
                      " un cycle de détention d’environ 5 ans), l’étude d’un"
                      " arbitrage ou d’une valorisation optimale de votre actif"
                      " représente une opportunité stratégique pour sécuriser vos"
                      " plus-values et réallouer vos capitaux."
                  )

              destinataire_affichage = (
                  f"Destinataire : {destinataire_nom}\nLocalisation du"
                  f" lot : {str_reperage}"
              )

              nom_champ_courrier = f"📄 Courrier - {adresse.title()}"

              courrier_modele = (
                  f"Nice, le {date_jour}\n\n"
                  f"{destinataire_affichage}\n"
                  f"Adresse du bien : {adresse.title()}\n\n"
                  f"{appel_destinataire}\n\n"
                  f"Objet : {objet_courrier}\n\n"
                  "En qualité de Conseil en Immobilier Patrimonial et forte d'une expertise pointue en droit de l'urbanisme, je me permets de vous contacter directement concernant l'actif dont vous êtes propriétaire dans cet immeuble.\n\n"
                  f"{paragraphe_strategique}\n\n"
                  "Je me tiens à votre entière disposition pour réaliser un audit patrimonial confidentiel (incluant le chiffrage précis de votre plus-value nette et des potentiels de votre lot) et vous accompagner dans vos réflexions.\n\n"
                  "Bien cordialement,\n\n"
                  "Nathalie Parra\n"
                  "Conseil en Immobilier Patrimonial\n\n"
                  "CABINET PRIVÉ IMMOBILIER HONORAT\n"
                  "TRANSACTION . CONSEIL . PATRIMOINE"
              )

              st.text_area(
                  nom_champ_courrier,
                  value=courrier_modele,
                  height=340,
                  key=f"courrier_{adresse}",
              )
              logo_path = "Cabinet Immobilier Privé HONORAT.png"
              if os.path.exists(logo_path):
                  st.image(logo_path, width=200)
      else:
          st.info("ℹ️ Veuillez sélectionner au moins une adresse dans le menu ci-dessus pour afficher les courriers.")
  with tab4:
    st.subheader('💶 Base de données des Ventes (DVF) & Carte Interactive')
    if not df_dvf.empty:

      def construire_adresse(row):
        cols = row.index.tolist()
        num = ''
        voie = ''
        if 'adresse_numero' in cols and pd.notna(row['adresse_numero']):
          num = str(row['adresse_numero']).replace('.0', '')
        elif 'No voie' in cols and pd.notna(row['No voie']):
          num = str(row['No voie']).replace('.0', '')
        if 'adresse_nom_voie' in cols and pd.notna(row['adresse_nom_voie']):
          voie = str(row['adresse_nom_voie'])
        elif 'Voie' in cols and pd.notna(row['Voie']):
          voie = str(row['Voie'])
          if 'Type de voie' in cols and pd.notna(row['Type de voie']):
            voie = str(row['Type de voie']) + ' ' + voie

        adresse = f'{num} {voie}'.strip().title()
        return adresse if adresse else 'Adresse inconnue'

      df_dvf['Adresse Vente'] = df_dvf.apply(construire_adresse, axis=1)

      colonnes_dvf = [
          'date_mutation',
          'Adresse Vente',
          'type_local',
          'nom_commune',
          'valeur_fonciere',
          'surface_reelle_bati',
          'prix_m2',
          'lat',
          'lon',
      ]
      colonnes_presentes = [
          col for col in colonnes_dvf if col in df_dvf.columns
      ]

      if colonnes_presentes:
        df_dvf_propre = df_dvf[colonnes_presentes].copy()

        df_dvf_propre['Prix de Vente'] = df_dvf_propre[
            'valeur_fonciere'
        ].apply(
            lambda x: f'{x:,.0f} €'.replace(',', ' ') if pd.notna(x) else ''
        )
        df_dvf_propre['Surface'] = df_dvf_propre['surface_reelle_bati'].apply(
            lambda x: f'{x:,.0f} m²' if pd.notna(x) else ''
        )
        df_dvf_propre['Prix / m²'] = df_dvf_propre['prix_m2'].apply(
            lambda x: f'{x:,.0f} €/m²'.replace(',', ' ') if pd.notna(x) else ''
        )

        st.markdown(
            '### 📍 Cartographie des transactions (Passez la souris sur les'
            ' points)'
        )
        if 'lat' in df_dvf_propre.columns and 'lon' in df_dvf_propre.columns:
          df_map = df_dvf_propre.dropna(subset=['lat', 'lon']).copy()

          if not df_map.empty:
            view_state = pdk.ViewState(
                latitude=df_map['lat'].mean(),
                longitude=df_map['lon'].mean(),
                zoom=13,
                pitch=0,
            )

            layer = pdk.Layer(
                'ScatterplotLayer',
                data=df_map,
                get_position='[lon, lat]',
                get_radius=20,
                get_fill_color='[200, 30, 0, 160]',
                pickable=True,
                auto_highlight=True,
            )

            tooltip = {
                'html': (
                    '<b>{Adresse Vente}</b><br/>Date : {date_mutation}<br/>Prix'
                    ' : {Prix de Vente}<br/>Surface : {Surface}<br/><b>Ratio :'
                    ' {Prix / m²}</b>'
                ),
                'style': {
                    'backgroundColor': 'steelblue',
                    'color': 'white',
                    'font-family': 'sans-serif',
                },
            }

            st.pydeck_chart(
                pdk.Deck(
                    layers=[layer],
                    initial_view_state=view_state,
                    tooltip=tooltip,
                )
            )
          else:
            st.info('Aucune coordonnée GPS trouvée pour afficher la carte.')

        st.markdown('---')
        st.markdown('### 📋 Tableau de bord DVF')
        df_tableau = df_dvf_propre[[
            'date_mutation',
            'Adresse Vente',
            'type_local',
            'nom_commune',
            'Prix de Vente',
            'Surface',
            'Prix / m²',
        ]].rename(
            columns={
                'date_mutation': 'Date Acte',
                'Adresse Vente': 'Adresse',
                'type_local': 'Type de Bien',
                'nom_commune': 'Commune',
            }
        )

        st.dataframe(
            df_tableau.head(200), use_container_width=True, hide_index=True
        )
    else:
      st.warning(
          '⚠️ Les données DVF n’ont pas pu être chargées. Vérifiez le nom du'
          ' dossier et vos fichiers.'
      )
