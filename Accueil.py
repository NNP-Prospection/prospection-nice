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
st.markdown("Base de données certifiée : Passoires F/G, Open Data (Airbnb/BODACC) et Publipostage patrimonial.")

# --- INITIALISATION DE LA MÉMOIRE (SESSION STATE) ---
if 'df_affichage' not in st.session_state:
    st.session_state.df_affichage = pd.DataFrame()
if 'analyse_terminee' not in st.session_state:
    st.session_state.analyse_terminee = False

# --- FONCTION POUR NETTOYER LES .0 ---
def formater_numero(val):
    if pd.isna(val) or str(val).lower() in ['nan', 'none', '']:
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
                etat_admin = entite.get('etat_administratif', 'A') # A = Actif, C = Cessée
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

# --- CHARGEMENT DES FICHIERS ---
@st.cache_data
def load_data():
    df_dpe = pd.DataFrame()
    df_airbnb = pd.DataFrame()
    try:
        df_dpe = pd.read_csv('dpe_nice_fg.csv', low_memory=False)
    except:
        pass
    try:
        # Fichier issu de l'Open Data de la Ville de Nice (Meublés de Tourisme)
        df_airbnb = pd.read_csv('airbnb_nice.csv', low_memory=False)
    except:
        pass
    return df_dpe, df_airbnb

df_global, df_airbnb = load_data()

# --- BARRE LATÉRALE DE RECHERCHE ---
st.sidebar.header("🎯 Critères de ciblage")

objectif = st.sidebar.selectbox(
    "Objectif de prospection",
    [
        "Passoires Énergétiques (F & G) - Standard", 
        "Cycle de détention ~5 ans (DPE)",
        "Risque Interdiction Airbnb (DPE + Meublé)"
    ]
)

secteur = st.sidebar.selectbox(
    "Quartier / Secteur à Nice",
    ["Tous les secteurs", "Carré d'Or", "Promenade des Anglais", "Port / Garibaldi", "Mont Boron", "Musiciens / Gambetta", "Centre-ville"]
)

tranche_mois = st.sidebar.selectbox("Choisir le lot de prospection", ["Lot 1 (1 - 50)", "Lot 2 (51 - 100)", "Lot 3 (101 - 150)"])

# Bouton de lancement
if st.sidebar.button("Générer le listing certifié", type="primary"):
    if not df_global.empty:
        df_resultats = df_global.copy()
        
        # Extraction de l'adresse
        col_adresse = next((col for col in ['adresse_ban', 'adresse_brute', 'adresse_propriete'] if col in df_resultats.columns), None)
        
        if col_adresse:
            # Filtrage par quartier
            if secteur != "Tous les secteurs":
                rues_quartiers = {
                    "Carré d'Or": ["france", "massena", "paradis", "suede", "verdun", "meyerbeer", "congres", "cronstadt"],
                    "Promenade des Anglais": ["promenade des anglais", "etats-unis", "quai des etats-unis"]
                    # (Ajoutez les autres rues au besoin)
                }
                mots_cles = rues_quartiers.get(secteur, [])
                if mots_cles:
                    pattern = '|'.join(mots_cles)
                    df_resultats = df_resultats[df_resultats[col_adresse].astype(str).str.lower().str.contains(pattern, na=False, regex=True)]
            
            # Croisement Airbnb si sélectionné
            if objectif == "Risque Interdiction Airbnb (DPE + Meublé)":
                if not df_airbnb.empty and 'adresse' in df_airbnb.columns:
                    adresses_airbnb = df_airbnb['adresse'].str.lower().tolist()
                    df_resultats = df_resultats[df_resultats[col_adresse].str.lower().isin(adresses_airbnb)]
                else:
                    st.warning("⚠️ Fichier 'airbnb_nice.csv' introuvable. Affichez les passoires classiques en attendant.")

            # Mise en forme finale du tableau
            colonnes_finales = {col_adresse: 'Adresse Exacte'}
            for col in df_resultats.columns:
                c = col.lower()
                if 'etage' in c or 'niveau' in c: colonnes_finales[col] = 'Étage'
                elif 'appartement' in c or 'porte' in c or 'numero_appt' in c: colonnes_finales[col] = 'N° Apt'
                elif 'lot' in c: colonnes_finales[col] = 'N° Lot'
                elif 'batiment' in c or 'bat' in c: colonnes_finales[col] = 'Bâtiment'
                elif 'etiquette' in c and 'dpe' in c: colonnes_finales[col] = 'Note DPE'

            df_affichage = df_resultats[list(colonnes_finales.keys())].rename(columns=colonnes_finales)
            df_affichage = df_affichage.loc[:, ~df_affichage.columns.duplicated()]
            
            index_debut = (int(tranche_mois.split()[1]) - 1) * 50
            st.session_state.df_affichage = df_affichage.iloc[index_debut:index_debut + 50]
            st.session_state.analyse_terminee = True
            st.session_state.objectif_en_cours = objectif
        else:
            st.error("Colonne d'adresse introuvable.")

# --- AFFICHAGE PRINCIPAL ---
if st.session_state.analyse_terminee:
    
    tab1, tab2 = st.tabs(["📊 1. Listing & Repères", "✉️ 2. Publipostage Stratégique"])
    
    with tab1:
        st.success(f"✅ Listing généré ! **{len(st.session_state.df_affichage)}** actifs ciblés.")
        event_selection = st.dataframe(st.session_state.df_affichage, use_container_width=True, on_select="rerun", selection_mode="multi-row")
        st.download_button("📥 Télécharger ce lot", data=st.session_state.df_affichage.to_csv(index=False).encode('utf-8'), file_name="listing_prospection.csv", mime='text/csv')

    with tab2:
        st.header("✉️ Publipostage Stratégique & Impression")
        
        if 'Adresse Exacte' in st.session_state.df_affichage.columns:
            liste_adresses = st.session_state.df_affichage['Adresse Exacte'].dropna().unique().tolist()
            lignes_selectionnees_indices = event_selection['selection'].get('rows', []) if event_selection and 'selection' in event_selection else []
            adresses_par_defaut = [liste_adresses[i] for i in lignes_selectionnees_indices if i < len(liste_adresses)]
            
            adresses_selectionnees = st.multiselect("📍 Adresses sélectionnées :", liste_adresses, default=adresses_par_defaut)
            
            if adresses_selectionnees:
                date_jour = datetime.now().strftime("%d/%m/%Y")
                if st.button("🖨️ Préparer l'impression groupée", type="primary"):
                    st.success("📄 Courriers prêts.")
                st.markdown("---")
                
                for adresse in adresses_selectionnees:
                    ligne_bien = st.session_state.df_affichage[st.session_state.df_affichage['Adresse Exacte'] == adresse].iloc[0]
                    
                    # Interrogation de l'API (INPI / BODACC)
                    infos_sirene = enrichir_avec_sirene(adresse)
                    
                    # Repères nettoyés
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

                    # Construction dynamique du texte selon la stratégie
                    paragraphe_strategique = "Au regard des récentes évolutions de la législation énergétique et de la fiscalité (régime LMNP, optimisation de la valeur vénale), l'anticipation de la gestion de votre patrimoine est devenue un enjeu majeur pour sécuriser votre rentabilité nette."
                    
                    if st.session_state.objectif_en_cours == "Risque Interdiction Airbnb (DPE + Meublé)":
                        paragraphe_strategique = "Votre actif étant actuellement exploité en location meublée de courte durée (type Airbnb), les futures interdictions de location liées à son étiquette énergétique (DPE) imposent un arbitrage rapide. Il est essentiel d'anticiper pour ne pas subir de vacance locative forcée ou de décote à la revente."

                    destinataire_affichage = f"Destinataire : Propriétaire / Copropriétaire\nLocalisation du lot : {str_reperage}"
                    appel_destinataire = f"Madame, Monsieur (Propriétaire du lot - {str_reperage}),"
                    
                    st.markdown(f"### 📍 {adresse}")
                    st.markdown(f"**Ciblage :** `{str_reperage}`")

                    if infos_sirene:
                        statut = infos_sirene['statut_bodacc']
                        st.markdown(f"**Données INPI/BODACC :** Structure `{infos_sirene['structure']}` | Gérant : `{infos_sirene['gerant']}` | {statut}")
                        destinataire_affichage = f"Destinataire : {infos_sirene['structure']}\nSiège social : {infos_sirene['siege']}"
                        appel_destinataire = f"À l'attention de {infos_sirene['gerant'] if infos_sirene['gerant'] else 'la Gérance'},"
                        
                        if "CESSATION" in statut:
                            paragraphe_strategique = "Ayant pris connaissance des récentes évolutions concernant votre structure (cessation / procédure), je tenais à vous proposer une estimation confidentielle et rapide de vos actifs immobiliers afin de faciliter vos démarches de liquidation ou de restructuration dans les meilleures conditions."
                    
                    courrier_modele = f"""Nice, le {date_jour}

{destinataire_affichage}
Adresse de l'actif concerné : {adresse}

{appel_destinataire}

Objet : Valorisation, arbitrage et stratégie concernant votre actif immobilier au {adresse} ({str_reperage})

En qualité de Conseil en Immobilier Patrimonial, je me permets de vous contacter de manière confidentielle concernant l'actif que vous détenez dans cet immeuble. 

{paragraphe_strategique}

Je me tiens à votre entière disposition pour réaliser un audit de valorisation et vous accompagner dans vos arbitrages, en toute discrétion.

Bien cordialement,

Nathalie Parra
Conseil en Immobilier Patrimonial

CABINET PRIVÉ IMMOBILIER HONORAT
TRANSACTION . CONSEIL . PATRIMOINE"""

                    st.text_area(f"📄 Modèle de courrier - {adresse}", value=courrier_modele, height=330, key=f"courrier_{adresse}")
                    
                    # Affichage du logo
                    logo_path = "Cabinet Immobilier Privé HONORAT.png"
                    if os.path.exists(logo_path):
                        st.image(logo_path, width=200)
                        
                    st.markdown("---")
