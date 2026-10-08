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
st.markdown("Base de données certifiée : Passoires DPE (F/G), Cycles DVF (~5 ans) et Publipostage intelligent.")

# --- INITIALISATION DE LA MÉMOIRE (SESSION STATE) ---
if 'df_dpe' not in st.session_state:
    st.session_state.df_dpe = pd.DataFrame()
if 'df_dvf' not in st.session_state:
    st.session_state.df_dvf = pd.DataFrame()
if 'donnees_chargees' not in st.session_state:
    st.session_state.donnees_chargees = False

# Chargement des fichiers de données
try:
    df_dpe_global = pd.read_csv('dpe_nice_fg.csv')
except:
    df_dpe_global = pd.DataFrame()

try:
    df_dvf_global = pd.read_csv('dvf_nice.csv')
except:
    df_dvf_global = pd.DataFrame()

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
    
    # 1. Traitement DPE
    if not df_dpe_global.empty:
        df_dpe = df_dpe_global.copy()
        colonnes_dpe = {}
        
        for col in ['adresse_ban', 'adresse_brute', 'adresse_propriete']:
            if col in df_dpe.columns: colonnes_dpe[col] = 'Adresse Exacte'; break
            
        for col in df_dpe.columns:
            col_lower = col.lower()
            if 'etage' in col_lower or 'niveau' in col_lower:
                colonnes_dpe[col] = 'Étage'
            elif 'appartement' in col_lower or 'porte' in col_lower or 'numero_appt' in col_lower:
                colonnes_dpe[col] = 'N° Apt'
            elif 'lot' in col_lower:
                colonnes_dpe[col] = 'N° Lot'
            elif 'batiment' in col_lower or 'bat' in col_lower:
                colonnes_dpe[col] = 'Bâtiment'
            elif 'etiquette' in col_lower and 'dpe' in col_lower:
                colonnes_dpe[col] = 'Note DPE'
            elif 'date' in col_lower and 'dpe' in col_lower:
                colonnes_dpe[col] = 'Date DPE'
            elif 'proprietaire' in col_lower or 'raison_sociale' in col_lower:
                colonnes_dpe[col] = 'Propriétaire / SCI'
        
        df_dpe = df_dpe[list(colonnes_dpe.keys())].rename(columns=colonnes_dpe)
        df_dpe = df_dpe.loc[:, ~df_dpe.columns.duplicated()]
        
        # Filtrage par secteur
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
            if 'Adresse Exacte' in df_dpe.columns and mots_cles:
                pattern = '|'.join(mots_cles)
                df_dpe = df_dpe[df_dpe['Adresse Exacte'].astype(str).str.lower().str.contains(pattern, na=False, regex=True)]

        idx_deb = (int(tranche_mois.split()[1]) - 1) * 50
        st.session_state.df_dpe = df_dpe.iloc[idx_deb:idx_deb + 50]

    # 2. Traitement DVF (~5 ans)
    if not df_dvf_global.empty:
        df_dvf = df_dvf_global.copy()
        colonnes_dvf = {}
        for col in ['adresse', 'adresse_brute', 'voie']:
            if col in df_dvf.columns: colonnes_dvf[col] = 'Adresse Exacte'; break
        for col, nom in [('date_mutation', 'Date Mutation'), ('valeur_fonciere', 'Valeur (€)'), ('nombre_pieces_principales', 'Pièces'), ('type_local', 'Type')]:
            if col in df_dvf.columns: colonnes_dvf[col] = nom
            
        df_dvf = df_dvf[list(colonnes_dvf.keys())].rename(columns=colonnes_dvf)
        df_dvf = df_dvf.loc[:, ~df_dvf.columns.duplicated()]
        
        if 'Date Mutation' in df_dvf.columns:
            df_dvf['Annee Mutation'] = pd.to_datetime(df_dvf['Date Mutation'], errors='coerce').dt.year
            df_dvf = df_dvf[df_dvf['Annee Mutation'].isin([2020, 2021, 2022])]
            
        st.session_state.df_dvf = df_dvf.head(50)
        
    st.session_state.donnees_chargees = True


# --- AFFICHAGE PRINCIPAL EN 3 ONGLETS ---
if st.session_state.donnees_chargees:
    
    tab1, tab2, tab3 = st.tabs([
        "📊 1. Passoires F&G (DPE)", 
        "🏖️ 2. Cycles 5 ans / Mutations (DVF)", 
        "✉️ 3. Publipostage & Impression"
    ])
    
    with tab1:
        st.header("📊 Passoires Énergétiques (F & G)")
        st.success(f"**{len(st.session_state.df_dpe)}** biens thermiques ciblés avec repères.")
        event_selection = st.dataframe(
            st.session_state.df_dpe, 
            use_container_width=True, 
            on_select="rerun", 
            selection_mode="multi-row", 
            key="table_dpe"
        )
        st.download_button("📥 Télécharger les Passoires (CSV)", data=st.session_state.df_dpe.to_csv(index=False).encode('utf-8'), file_name="passoires_fg.csv", mime='text/csv')

    with tab2:
        st.header("🏖️ Cycle de détention ~5 ans (Données Notariales DVF)")
        if st.session_state.df_dvf.empty:
            st.info("ℹ️ Le fichier `dvf_nice.csv` n'est pas encore présent sur le dépôt GitHub. Déposez-le pour activer ce module.")
        else:
            st.success(f"🎯 **{len(st.session_state.df_dvf)} biens** identifiés avec une date d'acquisition de ~5 ans.")
            st.dataframe(st.session_state.df_dvf, use_container_width=True)
            st.download_button("📥 Télécharger le listing DVF 5 ans (CSV)", data=st.session_state.df_dvf.to_csv(index=False).encode('utf-8'), file_name="cycle_5ans_dvf.csv", mime='text/csv')

    with tab3:
        st.header("✉️ Publipostage Intelligent & Impression")
        
        adresses_dispo = []
        if not st.session_state.df_dpe.empty and 'Adresse Exacte' in st.session_state.df_dpe.columns:
            adresses_dispo.extend(st.session_state.df_dpe['Adresse Exacte'].dropna().unique().tolist())
        if not st.session_state.df_dvf.empty and 'Adresse Exacte' in st.session_state.df_dvf.columns:
            adresses_dispo.extend(st.session_state.df_dvf['Adresse Exacte'].dropna().unique().tolist())
            
        adresses_dispo = list(set(adresses_dispo))
        
        if adresses_dispo:
            selection_indices = []
            if event_selection and 'selection' in event_selection:
                selection_indices = event_selection['selection'].get('rows', [])
            
            defauts = [st.session_state.df_dpe.iloc[i]['Adresse Exacte'] for i in selection_indices if i < len(st.session_state.df_dpe) and 'Adresse Exacte' in st.session_state.df_dpe.columns]
            
            adresses_selectionnees = st.multiselect("📍 Adresses sélectionnées pour le courrier :", adresses_dispo, default=defauts)
            
            if adresses_selectionnees:
                date_jour = datetime.now().strftime("%d/%m/%Y")
                
                col_btn1, col_btn2 = st.columns([1, 4])
                with col_btn1:
                    if st.button("🖨️ Préparer l'impression groupée", type="primary"):
                        st.success("📄 Prêt pour l'impression (utilisez Ctrl+P / Cmd+P).")
                    
                st.markdown("---")
                
                for adresse in adresses_selectionnees:
                    ligne_bien = pd.Series()
                    if not st.session_state.df_dpe.empty and adresse in st.session_state.df_dpe['Adresse Exacte'].values:
                        ligne_bien = st.session_state.df_dpe[st.session_state.df_dpe['Adresse Exacte'] == adresse].iloc[0]
                    
                    proprietaire = ligne_bien.get('Propriétaire / SCI', 'Propriétaire')
                    apt = ligne_bien.get('N° Apt', '')
                    etage = ligne_bien.get('Étage', '')
                    bat = ligne_bien.get('Bâtiment', '')
                    
                    infos_repere = []
                    if bat: infos_repere.append(f"Bât. {bat}")
                    if etage: infos_repere.append(f"Étage : {etage}")
                    if apt: infos_repere.append(f"Apt {apt}")
                    str_reperage = " | ".join(infos_repere) if infos_repere else "Bien identifié"

                    st.markdown(f"### 📍 {adresse}")
                    st.markdown(f"**Repères :** `{str_reperage}`")
                    st.text_area(
                        f"📄 Modèle de courrier :", 
                        value=f"Nice, le {date_jour}\n\nObjet : Évolution de votre patrimoine au {adresse}\n\nMadame, Monsieur ({str_reperage}),\n\nNous nous permettons de vous contacter concernant votre bien...\n\nBien cordialement,\n\nNathalie Parra", 
                        height=200,
                        key=f"courrier_{adresse}"
                    )
                    st.markdown("---")
        else:
            st.info("👉 Générez un listing depuis la barre latérale pour commencer.")
else:
    st.info("👉 Sélectionnez vos critères à gauche puis cliquez sur **'Générer les listings certifiés'**.")
