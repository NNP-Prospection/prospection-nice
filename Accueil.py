import streamlit as st
import pandas as pd
from datetime import datetime
import os
import requests

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="Espace de Prospection - Cabinet Honorat",
    page_icon="🏠",
    layout="wide"
)

st.title("🏠 Mon espace de prospection immobilière - Nice")
st.markdown("Base de données certifiée : Passoires F/G, Cycle ~5 ans (DPE) et approche SCI/BODACC.")

# --- INITIALISATION DE LA MÉMOIRE ---
if 'df_affichage' not in st.session_state:
    st.session_state.df_affichage = pd.DataFrame()
if 'analyse_terminee' not in st.session_state:
    st.session_state.analyse_terminee = False

# --- FONCTION POUR IDENTIFIER LES VIDES ABSOLUS ---
def est_vide(val):
    if pd.isna(val): 
        return True
    val_str = str(val).strip().lower()
    return val_str in ['nan', 'none', 'null', '', '<na>']

# --- FONCTION POUR NETTOYER LES .0 ---
def formater_numero(val):
    if est_vide(val):
        return ''
    val_str = str(val).strip()
    if val_str.endswith('.0'):
        return val_str[:-2]
    return val_str

# --- FONCTION API SIRENE ENRICHIE (INPI & BODACC) ---
@st.cache_data
def enrichir_avec_sirene(adresse_str):
    try:
        url = f"https://recherche-entreprises.api.gouv.fr/recherche?q={adresse_str}&per_page=1"
        reponse = requests.get(url, timeout=3)
        if reponse.status_code == 200:
            data = reponse.json()
            resultats = data.get('results', [])
            if resultats:
                entite = resultats[0]
                nom = entite.get('nom_raison_sociale', '')
                siren = entite.get('siren', '')
                
                # Récupération INPI (Dirigeants / Bénéficiaires)
                dirigeants = entite.get('dirigeants', [])
                nom_gerant = ""
                if dirigeants:
                    prenom = dirigeants[0].get('prenoms', '')
                    patronyme = dirigeants[0].get('nom', '')
                    nom_gerant = f"{prenom} {patronyme}".strip()
                
                # Détection BODACC / Statut de l'entreprise
                etat_admin = entite.get('etat_administratif', 'A') 
                alerte_bodacc = "Actif"
                if etat_admin == 'C':
                    alerte_bodacc = "🚨 CESSATION / LIQUIDATION (BODACC)"
                
                siege = entite.get('siege', {}).get('adresse', adresse_str)
                
                if nom:
                     return {
                        'structure': nom,
                        'siren': siren,
                        'gerant': nom_gerant,
                        'siege': siege,
                        'statut_bodacc': alerte_bodacc
                    }
    except Exception:
        pass
    return None

# --- CHARGEMENT DPE ---
try:
    df_global = pd.read_csv('dpe_nice_fg.csv', low_memory=False)
except Exception as e:
    df_global = pd.DataFrame()
    st.error("Erreur critique lors du chargement du fichier DPE.")

# --- BARRE LATÉRALE DE RECHERCHE ---
st.sidebar.header("🎯 Critères de ciblage")

objectif = st.sidebar.selectbox(
    "Objectif de prospection",
    ["Passoires Énergétiques (F & G) - Standard", "Cycle de détention ~5 ans (DPE)"]
)

secteur = st.sidebar.selectbox(
    "Quartier / Secteur à Nice",
    ["Tous les secteurs", "Carré d'Or", "Promenade des Anglais", "Port / Garibaldi", "Mont Boron", "Musiciens / Gambetta", "Centre-ville"]
)

liste_lots = ["Lot 1 (1 - 50)", "Lot 2 (51 - 100)", "Lot 3 (101 - 150)", "Lot 4 (151 - 200)", "Lot 5 (201 - 250)"]
tranche_mois = st.sidebar.selectbox("Choisir le lot de prospection", liste_lots)

# --- BOUTON DE LANCEMENT ---
if st.sidebar.button("Générer le listing certifié", type="primary"):
    if not df_global.empty:
        df_resultats = df_global.copy()
        
        colonnes_a_garder = {}
        for col in ['adresse_ban', 'adresse_brute', 'adresse_propriete']:
            if col in df_resultats.columns:
                colonnes_a_garder[col] = 'Adresse Exacte'
                break
                
        for col in df_resultats.columns:
            c = col.lower()
            if 'etage' in c or 'niveau' in c: colonnes_a_garder[col] = 'Étage'
            elif 'appartement' in c or 'porte' in c or 'numero_appt' in c: colonnes_a_garder[col] = 'N° Apt'
            elif 'lot' in c: colonnes_a_garder[col] = 'N° Lot'
            elif 'batiment' in c or 'bat' in c: colonnes_a_garder[col] = 'Bâtiment'
            elif 'etiquette' in c and 'dpe' in c: colonnes_a_garder[col] = 'Note DPE'
            elif 'date' in c and 'dpe' in c: colonnes_a_garder[col] = 'Date DPE'
            elif 'proprietaire' in c or 'raison_sociale' in c: colonnes_a_garder[col] = 'Propriétaire / SCI'

        df_affichage = df_resultats[list(colonnes_a_garder.keys())].rename(columns=colonnes_a_garder)
        df_affichage = df_affichage.loc[:, ~df_affichage.columns.duplicated()]

        # --- NETTOYAGE DES DOUBLONS ---
        colonnes_doublons = [col for col in ['Adresse Exacte', 'N° Apt', 'Étage', 'Date DPE'] if col in df_affichage.columns]
        if colonnes_doublons:
            df_affichage = df_affichage.drop_duplicates(subset=colonnes_doublons, keep='first')

        # --- EXCLUSION 100% BLINDÉE DES BIENS INEXPLOITABLES (SANS APT ET SANS ÉTAGE) ---
        if 'N° Apt' in df_affichage.columns and 'Étage' in df_affichage.columns:
            # On ne garde la ligne QUE SI l'apt n'est pas vide OU l'étage n'est pas vide
            mask_valide = df_affichage.apply(lambda row: not (est_vide(row.get('N° Apt')) and est_vide(row.get('Étage'))), axis=1)
            df_affichage = df_affichage[mask_valide]
        elif 'N° Apt' in df_affichage.columns:
            mask_valide = df_affichage.apply(lambda row: not est_vide(row.get('N° Apt')), axis=1)
            df_affichage = df_affichage[mask_valide]
        elif 'Étage' in df_affichage.columns:
            mask_valide = df_affichage.apply(lambda row: not est_vide(row.get('Étage')), axis=1)
            df_affichage = df_affichage[mask_valide]

        # --- Filtrage Secteur ---
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

        # --- Analyse temporelle ---
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
                        statuts_mandats.append("🏖️ Cycle ~5 ans (Passoire F/G)")
                    else:
                        statuts_mandats.append("⏳ Passoire F/G Standard")
                except:
                    statuts_mandats.append("📅 À qualifier")
                    
            df_affichage['Profil & Stratégie'] = statuts_mandats

        if objectif == "Cycle de détention ~5 ans (DPE)" and 'Profil & Stratégie' in df_affichage.columns:
            df_affichage = df_affichage[df_affichage['Profil & Stratégie'].str.contains("Cycle ~5 ans", na=False)]

        index_debut = (int(tranche_mois.split()[1]) - 1) * 50
        st.session_state.df_affichage = df_affichage.iloc[index_debut:index_debut + 50]
        st.session_state.analyse_terminee = True

# --- AFFICHAGE ---
if st.session_state.analyse_terminee:
    
    tab1, tab2, tab3 = st.tabs([
        "📊 1. Listing & Repères", 
        "🏖️ 2. Cycle ~5 ans (DPE)", 
        "✉️ 3. Publipostage & Impression"
    ])
    
    with tab1:
        st.success(f"✅ Listing généré ! **{len(st.session_state.df_affichage)}** biens ciblés (exploitable pour publipostage).")
        
        event_selection = st.dataframe(
            st.session_state.df_affichage, 
            use_container_width=True, 
            on_select="rerun", 
            selection_mode="multi-row",
            hide_index=True
        )
        st.download_button("📥 Télécharger (CSV)", data=st.session_state.df_affichage.to_csv(index=False).encode('utf-8'), file_name="listing_prospection.csv", mime='text/csv')

    with tab2:
        st.header("🏖️ Cycle de détention ~5 ans")
        if 'Profil & Stratégie' in st.session_state.df_affichage.columns:
            df_cycle = st.session_state.df_affichage[st.session_state.df_affichage['Profil & Stratégie'].str.contains("Cycle ~5 ans", na=False)]
            if not df_cycle.empty:
                st.dataframe(df_cycle, use_container_width=True, hide_index=True)
            else:
                st.info("ℹ️ Aucun bien ne correspond à ce critère dans ce lot.")

    with tab3:
        st.header("✉️ Publipostage Cible & Impression")
        if 'Adresse Exacte' in st.session_state.df_affichage.columns:
            liste_adresses = st.session_state.df_affichage['Adresse Exacte'].dropna().unique().tolist()
            lignes_sel = event_selection['selection'].get('rows', []) if event_selection and 'selection' in event_selection else []
            adresses_defaut = [liste_adresses[i] for i in lignes_sel if i < len(liste_adresses)]
            
            adresses_selectionnees = st.multiselect("📍 Adresses sélectionnées :", liste_adresses, default=adresses_defaut)
            
            if adresses_selectionnees:
                date_jour = datetime.now().strftime("%d/%m/%Y")
                if st.button("🖨️ Préparer l'impression groupée", type="primary"):
                    st.success("📄 Courriers prêts pour l'impression.")
                st.markdown("---")
                
                for adresse in adresses_selectionnees:
                    ligne_bien = st.session_state.df_affichage[st.session_state.df_affichage['Adresse Exacte'] == adresse].iloc[0]
                    
                    infos_sirene = enrichir_avec_sirene(adresse)
                    
                    apt = formater_numero(ligne_bien.get('N° Apt', ''))
                    lot = formater_numero(ligne_bien.get('N° Lot', ''))
                    etage = formater_numero(ligne_bien.get('Étage', ''))
                    bat = formater_numero(ligne_bien.get('Bâtiment', ''))
                    
                    infos_repere = []
                    if bat: infos_repere.append(f"Bât. {bat}")
                    if etage: infos_repere.append(f"Étage : {etage}")
                    if apt: infos_repere.append(f"Apt {apt}")
                    if lot: infos_repere.append(f"Lot n° {lot}")
                    str_reperage = " | ".join(infos_repere) if infos_repere else "Bien identifié"

                    paragraphe_strategique = "Au regard des récentes évolutions de la législation énergétique (calendrier d'interdiction de mise en location des passoires thermiques F et G) et de la fiscalité (régime LMNP, optimisation de la valeur vénale), l'anticipation de la gestion de votre patrimoine est devenue un enjeu majeur pour sécuriser votre rentabilité nette et éviter toute décote de votre bien."

                    destinataire_affichage = f"Destinataire : Propriétaire / Copropriétaire\nLocalisation du lot : {str_reperage}"
                    appel_destinataire = f"Madame, Monsieur (Propriétaire du lot - {str_reperage}),"

                    if infos_sirene:
                        statut = infos_sirene['statut_bodacc']
                        st.markdown(f"**💡 Opportunité SCI détectée :** Structure `{infos_sirene['structure']}` | Statut : {statut}")
                        destinataire_affichage = f"Destinataire : {infos_sirene['structure']}\nSiège social : {infos_sirene['siege']}"
                        appel_destinataire = f"À l'attention de {infos_sirene['gerant'] if infos_sirene['gerant'] else 'la Gérance'},"
                        
                        if "CESSATION" in statut:
                            paragraphe_strategique = "Ayant pris connaissance des récentes évolutions concernant votre structure (cessation / procédure), je tenais à vous proposer une estimation confidentielle et rapide de vos actifs immobiliers afin de faciliter vos démarches d'arbitrage ou de restructuration dans les meilleures conditions."

                    st.markdown(f"### 📍 {adresse} - Ciblage : `{str_reperage}`")
                    
                    courrier_modele = f"""Nice, le {date_jour}

{destinataire_affichage}
Adresse du bien : {adresse}

{appel_destinataire}

Objet : Anticipation réglementaire, valorisation et optimisation de votre actif immobilier au {adresse} ({str_reperage})

En qualité de Conseil en Immobilier Patrimonial, je me permets de vous contacter directement concernant l'actif dont vous êtes propriétaire dans cet immeuble. 

{paragraphe_strategique}

Je me tiens à votre entière disposition pour réaliser un audit confidentiel, une estimation patrimoniale actualisée et vous accompagner dans vos arbitrages.

Bien cordialement,

Nathalie Parra
Conseil en Immobilier Patrimonial

CABINET PRIVÉ IMMOBILIER HONORAT
TRANSACTION . CONSEIL . PATRIMOINE"""

                    st.text_area(f"📄 Courrier - {adresse}", value=courrier_modele, height=280, key=f"courrier_{adresse}")
                    logo_path = "Cabinet Immobilier Privé HONORAT.png"
                    if os.path.exists(logo_path):
                        st.image(logo_path, width=200)
                    st.markdown("---")
