import streamlit as st
import pandas as pd
from datetime import datetime
import os
import requests

st.set_page_config(
    page_title="Investissement Locatif & SCI - Cabinet Honorat", 
    layout="wide"
)

st.title("🏢 Espace Investissement Locatif & SCI - Nice")
st.markdown("Ciblage spécifique des structures sociétaires (SCI), détection des situations d'arbitrage (INPI/BODACC) et publipostage.")

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
                
                # Dirigeants / INPI
                dirigeants = entite.get('dirigeants', [])
                nom_gerant = ""
                if dirigeants:
                    prenom = dirigeants[0].get('prenoms', '')
                    patronyme = dirigeants[0].get('nom', '')
                    nom_gerant = f"{prenom} {patronyme}".strip()
                
                # Détection BODACC / Statut
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

# --- CHARGEMENT DES FICHIERS ---
@st.cache_data
def load_data():
    df_dvf = pd.DataFrame()
    df_dpe = pd.DataFrame()
    try:
        dossier = 'data_dvf'
        if os.path.exists(dossier):
            fichiers = [os.path.join(dossier, f) for f in os.listdir(dossier) if f.endswith('.csv')]
            if fichiers:
                liste_df = [pd.read_csv(f, sep=';', low_memory=False) for f in fichiers]
                df_dvf = pd.concat(liste_df, ignore_index=True)
                if 'latitude' in df_dvf.columns:
                    df_dvf = df_dvf.rename(columns={'latitude': 'lat', 'longitude': 'lon'})
    except:
        pass

    try:
        df_dpe = pd.read_csv('dpe_nice_fg.csv', low_memory=False)
    except:
        pass
        
    return df_dvf, df_dpe

df_dvf, df_dpe = load_data()

# --- NAVIGATION PAR ONGLET ---
tab1, tab2, tab3 = st.tabs([
    "📊 1. Radar des SCI & Investisseurs", 
    "✉️ 2. Publipostage Stratégique", 
    "🗺️ 3. Cartographie (DVF)"
])

with tab1:
    st.subheader("Ciblage et Qualification des SCI")
    secteur = st.selectbox("Quartier / Secteur", ["Tous les secteurs", "Carré d'Or", "Promenade des Anglais", "Musiciens"])
    
    if st.button("Lancer le radar à SCI", type="primary"):
        if not df_dpe.empty:
            df_recherche = df_dpe.copy()
            col_adresse = next((col for col in ['adresse_ban', 'adresse_brute', 'adresse_propriete'] if col in df_recherche.columns), None)
            
            if col_adresse:
                if secteur != "Tous les secteurs":
                     rues_quartiers = {
                        "Carré d'Or": ["france", "massena", "paradis", "suede", "verdun", "meyerbeer", "congres", "cronstadt"],
                        "Promenade des Anglais": ["promenade des anglais", "etats-unis", "quai des etats-unis"],
                        "Musiciens": ["gambetta", "berlioz", "gounod", "rossini", "verdi", "clemenceau", "victor hugo"]
                    }
                     mots_cles = rues_quartiers.get(secteur, [])
                     if mots_cles:
                         pattern = '|'.join(mots_cles)
                         df_recherche = df_recherche[df_recherche[col_adresse].astype(str).str.lower().str.contains(pattern, na=False, regex=True)]

                # On scanne un lot pour trouver des SCI
                adresses_a_tester = df_recherche[col_adresse].dropna().unique()[:30]
                data_rows = []
                
                with st.spinner("Analyse INPI/BODACC en cours..."):
                    for adresse in adresses_a_tester:
                        infos = enrichir_avec_sirene(adresse)
                        if infos: 
                            ligne_dpe = df_recherche[df_recherche[col_adresse] == adresse].iloc[0]
                            data_rows.append({
                                'Adresse Exacte': adresse,
                                'Structure (SCI)': infos['structure'],
                                'Gérant / Contact': infos['gerant'],
                                'SIREN': infos['siren'],
                                'Statut / BODACC': infos['statut_bodacc'],
                                'Siège Social': infos['siege'],
                                'N° Apt': formater_numero(ligne_dpe.get('numero_appartement', ligne_dpe.get('numero_appt', ''))),
                                'Étage': formater_numero(ligne_dpe.get('etage', ''))
                            })
                
                st.session_state.df_locatif = pd.DataFrame(data_rows)
                if st.session_state.df_locatif.empty:
                    st.warning("Aucune structure sociétaire n'a été détectée sur cet échantillon.")
            else:
                st.error("Colonne d'adresse introuvable.")
        else:
            st.error("Fichier DPE non chargé.")

    if 'df_locatif' in st.session_state and not st.session_state.df_locatif.empty:
        st.success(f"✅ {len(st.session_state.df_locatif)} structures et SCI identifiées.")
        event_selection_loc = st.dataframe(st.session_state.df_locatif, use_container_width=True, on_select="rerun", selection_mode="multi-row")

with tab2:
    st.subheader("✉️ Publipostage Investisseur & SCI")
    
    if 'df_locatif' in st.session_state and not st.session_state.df_locatif.empty:
        liste_adresses_loc = st.session_state.df_locatif['Adresse Exacte'].dropna().unique().tolist()
        adresses_selectionnees = st.multiselect("📍 SCI sélectionnées :", liste_adresses_loc, default=liste_adresses_loc)
        
        if adresses_selectionnees:
            date_jour = datetime.now().strftime("%d/%m/%Y")
            if st.button("🖨️ Préparer l'impression groupée", type="primary"):
                st.success("📄 Courriers SCI prêts.")
            st.markdown("---")
            
            for adresse in adresses_selectionnees:
                ligne_bien = st.session_state.df_locatif[st.session_state.df_locatif['Adresse Exacte'] == adresse].iloc[0]
                structure = ligne_bien.get('Structure (SCI)', '')
                gerant = ligne_bien.get('Gérant / Contact', '')
                siege = ligne_bien.get('Siège Social', adresse)
                statut = ligne_bien.get('Statut / BODACC', '')
                apt = ligne_bien.get('N° Apt', '')
                etage = ligne_bien.get('Étage', '')
                
                infos_repere = []
                if etage: infos_repere.append(f"Étage : {etage}")
                if apt: infos_repere.append(f"Apt {apt}")
                str_reperage = " | ".join(infos_repere) if infos_repere else "Actif identifié"

                # En-tête ciblé SCI
                en_tete = f"Destinataire : {structure}\nSiège social : {siege}\n"
                appel = f"À l'attention de {gerant}," if gerant else "À l'attention de la Gérance,"
                
                # Stratégie textuelle adaptée
                strategie = "Dans le cadre des évolutions de la fiscalité immobilière (régime LMNP, fiscalité des SCI, loi de finances), l'anticipation de la gestion de votre portefeuille est essentielle pour sécuriser votre rentabilité nette et optimiser la transmission ou la revente de vos actifs."
                
                if "CESSATION" in statut:
                    strategie = "Ayant pris connaissance des évolutions récentes concernant l'état administratif de votre structure, je tenais à vous proposer une estimation confidentielle de vos actifs immobiliers afin de faciliter vos démarches d'arbitrage ou de restructuration dans les meilleures conditions."

                st.markdown(f"### 📍 {adresse} - `{structure}`")
                
                courrier_texte = f"""Nice, le {date_jour}

{en_tete}

{appel}

Objet : Stratégie patrimoniale, arbitrage et optimisation de votre actif au {adresse} ({str_reperage})

En qualité de Conseil en Immobilier Patrimonial, je me permets de vous contacter de manière totalement confidentielle concernant l'actif que détient votre structure. 

{strategie}

Je me tiens à votre entière disposition pour réaliser un audit de valorisation et vous accompagner dans vos projets d'arbitrage.

Bien cordialement,

Nathalie Parra
Conseil en Immobilier Patrimonial

CABINET PRIVÉ IMMOBILIER HONORAT
TRANSACTION . CONSEIL . PATRIMOINE"""
                
                st.text_area(f"Modèle de courrier - {adresse}", courrier_texte, height=350, key=f"courrier_loc_{adresse}")
                
                # Logo en signature
                logo_path = "Cabinet Immobilier Privé HONORAT.png"
                if os.path.exists(logo_path):
                    st.image(logo_path, width=200)
                st.markdown("---")

with tab3:
    st.subheader("🗺️ Cartographie des Ventes Récentes (DVF)")
    if not df_dvf.empty:
        st.map(df_dvf[['lat', 'lon']].dropna())
    else:
        st.info("Placez vos fichiers DVF dans le dossier 'data_dvf' pour afficher la carte.")
