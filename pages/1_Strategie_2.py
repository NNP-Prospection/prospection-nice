import streamlit as st
import pandas as pd
from datetime import datetime
import os
import requests
import time

st.set_page_config(
    page_title="Stratégie 2 - Cabinet Honorat", 
    page_icon="💼",
    layout="wide"
)

st.title("💼 Stratégie 2 : SCI & Alertes Juridiques (Nice)")
st.markdown("Approche par l'investisseur : Ciblage des structures (SCI), détection INPI/BODACC et cartographie des ventes (DVF).")

def est_vide(val):
    if pd.isna(val): return True
    return str(val).strip().lower() in ['nan', 'none', 'null', '', '<na>']

def formater_numero(val):
    if est_vide(val): return ''
    val_str = str(val).strip()
    if val_str.endswith('.0'): return val_str[:-2]
    return val_str

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
                nom_gerant = f"{dirigeants[0].get('prenoms', '')} {dirigeants[0].get('nom', '')}".strip() if dirigeants else ""
                
                etat_admin = entite.get('etat_administratif', 'A') 
                alerte_bodacc = "🚨 CESSATION / LIQUIDATION" if etat_admin == 'C' else "Actif"
                siege = entite.get('siege', {}).get('adresse', adresse_str)
                
                if nom:
                     return {'structure': nom, 'siren': siren, 'gerant': nom_gerant, 'siege': siege, 'statut_bodacc': alerte_bodacc}
    except:
        pass
    return None

@st.cache_data
def load_dpe():
    try:
        return pd.read_csv('dpe_nice_fg.csv', low_memory=False)
    except:
        return pd.DataFrame()

@st.cache_data
def load_dvf():
    try:
        dossier = 'data_dvf'
        if os.path.exists(dossier):
            fichiers = [os.path.join(dossier, f) for f in os.listdir(dossier) if f.endswith('.csv')]
            if fichiers:
                liste_df = [pd.read_csv(os.path.join(dossier, f), sep=';', low_memory=False) for f in fichiers]
                df = pd.concat(liste_df, ignore_index=True).drop_duplicates()
                if 'latitude' in df.columns:
                    df = df.rename(columns={'latitude': 'lat', 'longitude': 'lon'})
                if 'valeur_fonciere' in df.columns and 'surface_reelle_bati' in df.columns and 'lat' in df.columns:
                    df = df.dropna(subset=['valeur_fonciere', 'surface_reelle_bati', 'lat', 'lon']).copy()
                    df['valeur_fonciere'] = pd.to_numeric(df['valeur_fonciere'].astype(str).str.replace(',', '.'), errors='coerce')
                    df['surface_reelle_bati'] = pd.to_numeric(df['surface_reelle_bati'].astype(str).str.replace(',', '.'), errors='coerce')
                    df['prix_m2'] = df['valeur_fonciere'] / df['surface_reelle_bati']
                    df = df[(df['prix_m2'] > 1000) & (df['prix_m2'] < 25000)]
                return df
        return pd.DataFrame()
    except:
        return pd.DataFrame()

df_dpe = load_dpe()
df_dvf = load_dvf()

tab1, tab2, tab3 = st.tabs(["📊 1. Radar des Actifs Locatifs", "✉️ 2. Publipostage Stratégique", "🗺️ 3. Cartographie (DVF)"])

with tab1:
    st.subheader("Ciblage des actifs et recherche de propriétaires (INPI)")
    
    col1, col2 = st.columns(2)
    with col1:
        secteur = st.selectbox("Quartier / Secteur", ["Tous les secteurs", "Carré d'Or", "Promenade des Anglais", "Musiciens", "Mont Boron", "Port / Garibaldi"])
    with col2:
        tranche_mois = st.selectbox("Choisir le lot à analyser", ["Lot 1 (1 - 50)", "Lot 2 (51 - 100)", "Lot 3 (101 - 150)", "Lot 4 (151 - 200)", "Lot 5 (201 - 250)"])
    
    if st.button("Lancer le radar", type="primary"):
        if not df_dpe.empty:
            df_recherche = df_dpe.copy()
            
            col_adresse = next((col for col in ['adresse_ban', 'adresse_brute', 'adresse_propriete'] if col in df_recherche.columns), None)
            col_apt = next((col for col in df_recherche.columns if 'appartement' in col.lower() or 'porte' in col.lower() or 'numero_appt' in col.lower()), None)
            col_etage = next((col for col in df_recherche.columns if 'etage' in col.lower() or 'niveau' in col.lower()), None)
            
            if col_adresse:
                if secteur != "Tous les secteurs":
                     rues_quartiers = {
                        "Carré d'Or": ["france", "massena", "paradis", "suede", "verdun", "meyerbeer", "congres", "cronstadt"],
                        "Promenade des Anglais": ["promenade des anglais", "etats-unis", "quai des etats-unis"],
                        "Musiciens": ["gambetta", "berlioz", "gounod", "rossini", "verdi", "clemenceau", "victor hugo"],
                        "Mont Boron": ["mont boron", "jean lorrain", "carnot", "germaine", "andre joly", "valrose", "cap de nice"],
                        "Port / Garibaldi": ["garibaldi", "lunel", "cassini", "barla", "arson", "republique", "port"]
                    }
                     mots_cles = rues_quartiers.get(secteur, [])
                     if mots_cles:
                         pattern = '|'.join(mots_cles)
                         df_recherche = df_recherche[df_recherche[col_adresse].astype(str).str.lower().str.contains(pattern, na=False, regex=True)]

                index_debut = (int(tranche_mois.split()[1]) - 1) * 50
                adresses_uniques = df_recherche[col_adresse].dropna().unique()
                adresses_a_tester = adresses_uniques[index_debut:index_debut + 50]
                
                data_rows = []
                
                if len(adresses_a_tester) > 0:
                    st.write(f"🔍 **Analyse de {len(adresses_a_tester)} actifs immobiliers...**")
                    progress_bar = st.progress(0)
                    
                    for i, adresse in enumerate(adresses_a_tester):
                        infos = enrichir_avec_sirene(adresse)
                        ligne_dpe = df_recherche[df_recherche[col_adresse] == adresse].iloc[0]
                        
                        apt = formater_numero(ligne_dpe[col_apt] if col_apt else '')
                        etage = formater_numero(ligne_dpe[col_etage] if col_etage else '')
                        
                        if apt or etage:
                            if infos:
                                statut_inpi = f"✅ Siège trouvé : {infos['structure']}"
                                alerte = infos['statut_bodacc']
                            else:
                                statut_inpi = "Domicilié ailleurs (Voir Cadastre)"
                                alerte = "-"

                            data_rows.append({
                                'Adresse de l\'actif': adresse,
                                'N° Apt': apt,
                                'Étage': etage,
                                'Statut INPI': statut_inpi,
                                'BODACC': alerte
                            })
                        time.sleep(0.1)
                        progress_bar.progress((i + 1) / len(adresses_a_tester))
                
                st.session_state.df_locatif = pd.DataFrame(data_rows)
                if st.session_state.df_locatif.empty:
                    st.warning("Aucun actif exploitable (avec numéro d'appartement ou étage) trouvé dans ce lot.")
            else:
                st.error("Colonne d'adresse introuvable.")
        else:
            st.error("Fichier DPE non chargé.")

    if 'df_locatif' in st.session_state and not st.session_state.df_locatif.empty:
        st.success(f"🎯 {len(st.session_state.df_locatif)} lots d'investissement identifiés !")
        event_selection_loc = st.dataframe(st.session_state.df_locatif, use_container_width=True, on_select="rerun", selection_mode="multi-row", hide_index=True)

with tab2:
    st.subheader("✉️ Publipostage Investisseur")
    if 'df_locatif' in st.session_state and not st.session_state.df_locatif.empty:
        liste_adresses_loc = st.session_state.df_locatif['Adresse de l\'actif'].dropna().unique().tolist()
        lignes_sel = event_selection_loc['selection'].get('rows', []) if 'event_selection_loc' in locals() and event_selection_loc and 'selection' in event_selection_loc else []
        adresses_defaut = [liste_adresses_loc[i] for i in lignes_sel if i < len(liste_adresses_loc)]

        adresses_selectionnees = st.multiselect("📍 Actifs sélectionnés :", liste_adresses_loc, default=adresses_defaut)
        
        if adresses_selectionnees:
            date_jour = datetime.now().strftime("%d/%m/%Y")
            if st.button("🖨️ Préparer l'impression groupée", type="primary"):
                st.success("📄 Courriers prêts.")
            st.markdown("---")
            
            for adresse in adresses_selectionnees:
                ligne_bien = st.session_state.df_locatif[st.session_state.df_locatif['Adresse de l\'actif'] == adresse].iloc[0]
                statut_inpi = ligne_bien.get('Statut INPI', '')
                alerte_bodacc = ligne_bien.get('BODACC', '')
                apt = formater_numero(ligne_bien.get('N° Apt', ''))
                etage = formater_numero(ligne_bien.get('Étage', ''))
                
                infos_repere = []
                if etage: infos_repere.append(f"Étage : {etage}")
                if apt: infos_repere.append(f"Apt {apt}")
                str_reperage = " | ".join(infos_repere) if infos_repere else "Actif identifié"

                if "Siège trouvé" in statut_inpi:
                    nom_sci = statut_inpi.split(": ")[1]
                    en_tete = f"Destinataire : {nom_sci}\nSiège social : {adresse}"
                    appel = "À l'attention de la Gérance,"
                else:
                    en_tete = f"Destinataire : Propriétaire / Investisseur\nLocalisation de l'actif : {str_reperage}"
                    appel = f"Madame, Monsieur (Investisseur - {str_reperage}),"
                
                strategie = "Dans le cadre des évolutions de la fiscalité immobilière (loi de finances, DPE), l'anticipation de la gestion de votre portefeuille est essentielle pour sécuriser votre rentabilité nette et optimiser vos actifs."
                
                if "CESSATION" in alerte_bodacc:
                    strategie = "Ayant pris connaissance des évolutions récentes concernant l'état administratif de votre structure, je tenais à vous proposer une estimation confidentielle de vos actifs immobiliers afin de faciliter vos démarches d'arbitrage dans les meilleures conditions."

                st.markdown(f"### 📍 {adresse}")
                courrier_texte = f"""Nice, le {date_jour}

{en_tete}
Concerne l'actif situé au : {adresse}

{appel}

Objet : Stratégie patrimoniale, arbitrage et optimisation de votre actif au {adresse} ({str_reperage})

En qualité de Conseil en Immobilier Patrimonial, je me permets de vous contacter de manière totalement confidentielle concernant l'actif que vous détenez. 

{strategie}

Je me tiens à votre entière disposition pour réaliser un audit de valorisation et vous accompagner dans vos projets d'arbitrage.

Bien cordialement,

Nathalie Parra
Conseil en Immobilier Patrimonial

CABINET PRIVÉ IMMOBILIER HONORAT
TRANSACTION . CONSEIL . PATRIMOINE"""
                st.text_area(f"Modèle de courrier - {adresse}", courrier_texte, height=350, key=f"courrier_loc_{adresse}")
                logo_path = "Cabinet Immobilier Privé HONORAT.png"
                if os.path.exists(logo_path): st.image(logo_path, width=200)
                st.markdown("---")

with tab3:
    st.subheader("🗺️ Cartographie des Ventes Récentes (DVF)")
    if not df_dvf.empty and 'lat' in df_dvf.columns and 'lon' in df_dvf.columns:
        st.write("Visualisation des dernières transactions immobilières actées sur le secteur.")
        st.map(df_dvf[['lat', 'lon']].dropna())
    else:
        st.warning("⚠️ Les données cartographiques DVF ne sont pas disponibles. Vérifiez que les fichiers `.csv` se trouvent bien dans le dossier `data_dvf`.")
