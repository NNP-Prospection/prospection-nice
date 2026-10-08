import streamlit as st
import pandas as pd
from datetime import datetime

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="Espace de Prospection - Nice",
    page_icon="🏠",
    layout="wide"
)

st.title("🏠 Mon espace de prospection immobilière - Nice")
st.markdown("Base de données certifiée : Passoires DPE (F/G) et Cycles de Mutation DVF (~5 ans).")

# --- INITIALISATION DE LA MÉMOIRE (SESSION STATE) ---
if 'df_dpe' not in st.session_state:
    st.session_state.df_dpe = pd.DataFrame()
if 'df_dvf' not in st.session_state:
    st.session_state.df_dvf = pd.DataFrame()
if 'donnees_chargees' not in st.session_state:
    st.session_state.donnees_chargees = False

# Chargement des fichiers de données (DPE F/G et DVF mutations)
try:
    df_dpe_global = pd.read_csv('dpe_nice_fg.csv')
except:
    df_dpe_global = pd.DataFrame()

try:
    df_dvf_global = pd.read_csv('dvf_nice.csv')
except:
    df_dvf_global = pd.DataFrame() # Fichier des mutations DVF

# --- BARRE LATÉRALE DE RECHERCHE ---
st.sidebar.header("🎯 Critères de ciblage")

objectif = st.sidebar.selectbox(
    "Objectif de prospection",
    ["Passoires Énergétiques (F & G) - Standard", "Cycle Mutations DVF (~5 ans)"]
)

secteur = st.sidebar.selectbox(
    "Quartier / Secteur à Nice",
    ["Tous les secteurs", "Carré d'Or", "Promenade des Anglais", "Port / Garibaldi", "Mont Boron", "Musiciens / Gambetta", "Centre-ville"]
)

liste_lots = ["Lot 1 (1 - 50)", "Lot 2 (51 - 100)", "Lot 3 (101 - 150)", "Lot 4 (151 - 200)", "Lot 5 (201 - 250)"]
tranche_mois = st.sidebar.selectbox("Choisir le lot de prospection", liste_lots)

# Bouton de lancement
if st.sidebar.button("Générer les listings certifiés", type="primary"):
    
    # 1. Traitement de la base DPE (Passoires F/G)
    if not df_dpe_global.empty:
        df_dpe = df_dpe_global.copy()
        colonnes_dpe = {}
        for col in ['adresse_ban', 'adresse_brute', 'adresse_propriete']:
            if col in df_dpe.columns: colonnes_dpe[col] = 'Adresse Exacte'; break
        for col, nom in [('numero_appartement', 'N° Apt'), ('numero_lot', 'N° Lot'), ('batiment', 'Bâtiment'), ('etage', 'Étage'), ('etiquette_dpe', 'Note DPE'), ('date_etablissement_dpe', 'Date DPE'), ('nom_proprietaire', 'Propriétaire / SCI')]:
            if col in df_dpe.columns: colonnes_dpe[col] = nom
        
        df_dpe = df_dpe[list(colonnes_dpe.keys())].rename(columns=colonnes_dpe)
        df_dpe = df_dpe.loc[:, ~df_dpe.columns.duplicated()]
        
        # Découpage du lot DPE
        idx_deb = (int(tranche_mois.split()[1]) - 1) * 50
        st.session_state.df_dpe = df_dpe.iloc[idx_deb:idx_deb + 50]

    # 2. Traitement de la base DVF (Mutations ~5 ans / 2021)
    if not df_dvf_global.empty:
        df_dvf = df_dvf_global.copy()
        colonnes_dvf = {}
        for col in ['adresse', 'adresse_brute', 'voie']:
            if col in df_dvf.columns: colonnes_dvf[col] = 'Adresse Exacte'; break
        for col, nom in [('date_mutation', 'Date Mutation'), ('valeur_fonciere', 'Valeur (€)'), ('nombre_pieces_principales', 'Pièces'), ('type_local', 'Type')]:
            if col in df_dvf.columns: colonnes_dvf[col] = nom
            
        df_dvf = df_dvf[list(colonnes_dvf.keys())].rename(columns=colonnes_dvf)
        df_dvf = df_dvf.loc[:, ~df_dvf.columns.duplicated()]
        
        # Filtrage strict sur les mutations d'il y a environ 5 ans (année 2021)
        if 'Date Mutation' in df_dvf.columns:
            df_dvf['Annee Mutation'] = pd.to_datetime(df_dvf['Date Mutation'], errors='coerce').dt.year
            # On isole la tranche des 5 ans (2020 - 2022, centré sur 2021)
            df_dvf = df_dvf[df_dvf['Annee Mutation'].isin([2020, 2021, 2022])]
            
        st.session_state.df_dvf = df_dvf.head(50)
        
    st.session_state.donnees_chargees = True


# --- AFFICHAGE PRINCIPAL EN 3 ONGLETS ---
if st.session_state.donnees_chargees:
    
    tab1, tab2, tab3 = st.tabs([
        "📊 1. Passoires F&G (DPE)", 
        "🏖️ 2. Cycles 5 ans / Mutations (DVF 2021)", 
        "✉️ 3. Publipostage & Impression"
    ])
    
    # ONGLET 1 : PASSOIRES DPE
    with tab1:
        st.header("📊 Passoires Énergétiques (F & G)")
        st.success(f"**{len(st.session_state.df_dpe)}** biens thermiques ciblés.")
        event_selection = st.dataframe(st.session_state.df_dpe, use_container_width=True, on_select="rerun", selection_mode="multi-row", key="table_dpe")
        st.download_button("📥 Télécharger les Passoires (CSV)", data=st.session_state.df_dpe.to_csv(index=False).encode('utf-8'), file_name="passoires_fg.csv", mime='text/csv')

    # ONGLET 2 : CYCLE 5 ANS BASÉ SUR DVF (TOUTES NOTES DPE)
    with tab2:
        st.header("🏖️ Cycle de détention ~5 ans (Données Notariales DVF - Achats en 2021)")
        st.write("Cet onglet s'appuie exclusivement sur les mutations enregistrées il y a 5 ans (indépendamment de la note DPE), parfait pour cibler les résidences secondaires et les arbitrages de premier cycle.")
        
        if st.session_state.df_dvf.empty:
            st.info("ℹ️ Le fichier `dvf_nice.csv` n'est pas encore chargé sur le dépôt GitHub. Veuillez y verser votre extrait DVF pour activer ce moteur de recherche.")
        else:
            st.success(f"🎯 **{len(st.session_state.df_dvf)} biens** identifiés avec une date d'acquisition de ~5 ans.")
            st.dataframe(st.session_state.df_dvf, use_container_width=True)
            st.download_button("📥 Télécharger le listing DVF 5 ans (CSV)", data=st.session_state.df_dvf.to_csv(index=False).encode('utf-8'), file_name="cycle_5ans_dvf.csv", mime='text/csv')

    # ONGLET 3 : PUBLIPOSTAGE ET IMPRESSION
    with tab3:
        st.header("✉️ Publipostage Intelligent & Impression")
        
        # On combine les adresses des deux sources pour le publipostage
        adresses_dispo = []
        if not st.session_state.df_dpe.empty and 'Adresse Exacte' in st.session_state.df_dpe.columns:
            adresses_dispo.extend(st.session_state.df_dpe['Adresse Exacte'].dropna().unique().tolist())
        if not st.session_state.df_dvf.empty and 'Adresse Exacte' in st.session_state.df_dvf.columns:
            adresses_dispo.extend(st.session_state.df_dvf['Adresse Exacte'].dropna().unique().tolist())
            
        adresses_dispo = list(set(adresses_dispo)) # Supprimer les doublons
        
        if adresses_dispo:
            selection_indices = []
            if event_selection and 'selection' in event_selection:
                selection_indices = event_selection['selection'].get('rows', [])
            
            defauts = [st.session_state.df_dpe.iloc[i]['Adresse Exacte'] for i in selection_indices if i < len(st.session_state.df_dpe) and 'Adresse Exacte' in st.session_state.df_dpe.columns]
            
            adresses_selectionnees = st.multiselect("📍 Adresses sélectionnées pour le courrier :", adresses_dispo, default=defauts)
            
            if adresses_selectionnees:
                date_jour = datetime.now().strftime("%d/%m/%Y")
                if st.button("🖨️ Préparer l'impression groupée", type="primary"):
                    st.success("📄 Prêt pour l'impression (utilisez Ctrl+P / Cmd+P).")
                    
                st.markdown("---")
                for adresse in adresses_selectionnees:
                    st.markdown(f"### 📍 {adresse}")
                    st.text_area(
                        f"📄 Modèle de courrier :", 
                        value=f"Nice, le {date_jour}\n\nObjet : Évolution de votre patrimoine au {adresse}\n\nMadame, Monsieur,\n\nNous nous permettons de vous contacter concernant votre bien...\n\nBien cordialement,\n\nNathalie Parra", 
                        height=180,
                        key=f"courrier_{adresse}"
                    )
                    st.markdown("---")
        else:
            st.info("👉 Générez un listing pour commencer.")
else:
    st.info("👉 Sélectionnez vos critères à gauche puis cliquez sur **'Générer les listings certifiés'**.")
