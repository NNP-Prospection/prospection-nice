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
st.markdown("Base de données certifiée : Repères de copropriété (Étage, Appartement) et publipostage.")

# --- INITIALISATION DE LA MÉMOIRE (SESSION STATE) ---
if 'df_affichage' not in st.session_state:
    st.session_state.df_affichage = pd.DataFrame()
if 'analyse_terminee' not in st.session_state:
    st.session_state.analyse_terminee = False

# Chargement du fichier CSV global
try:
    df_global = pd.read_csv('dpe_nice_fg.csv')
except Exception as e:
    df_global = pd.DataFrame()
    st.error(f"Erreur critique lors du chargement du fichier DPE : {e}")

# --- BARRE LATÉRALE DE RECHERCHE ---
st.sidebar.header("🎯 Critères de ciblage")

objectif = st.sidebar.selectbox(
    "Objectif de prospection",
    ["Passoires Énergétiques (F & G) - Standard", "Campagne de Boîtage Ciblé"]
)

secteur = st.sidebar.selectbox(
    "Quartier / Secteur à Nice",
    ["Tous les secteurs", "Carré d'Or", "Promenade des Anglais", "Port / Garibaldi", "Mont Boron", "Musiciens / Gambetta", "Centre-ville"]
)

liste_lots = ["Lot 1 (1 - 50)", "Lot 2 (51 - 100)", "Lot 3 (101 - 150)", "Lot 4 (151 - 200)", "Lot 5 (201 - 250)"]
tranche_mois = st.sidebar.selectbox("Choisir le lot de prospection", liste_lots)

# Bouton de lancement
if st.sidebar.button("Générer le listing certifié", type="primary"):
    if not df_global.empty:
        df_resultats = df_global.copy()
        
        # Sélection unique et propre des colonnes pour éviter les doublons
        colonnes_a_garder = {}
        
        for col in ['adresse_ban', 'adresse_brute', 'adresse_propriete']:
            if col in df_resultats.columns:
                colonnes_a_garder[col] = 'Adresse Exacte'
                break # On prend la première trouvée pour éviter les doublons
                
        for col, nom in [
            ('numero_appartement', 'N° Apt'),
            ('numero_lot', 'N° Lot'),
            ('batiment', 'Bâtiment'),
            ('etage', 'Étage'),
            ('etiquette_dpe', 'Note DPE'),
            ('date_etablissement_dpe', 'Date DPE'),
            ('nom_proprietaire', 'Propriétaire / SCI')
        ]:
            if col in df_resultats.columns and nom not in colonnes_a_garder.values():
                colonnes_a_garder[col] = nom

        df_affichage = df_resultats[list(colonnes_a_garder.keys())].rename(columns=colonnes_a_garder)

        # Nettoyage de sécurité ultime anti-doublons de colonnes
        df_affichage = df_affichage.loc[:, ~df_affichage.columns.duplicated()]

        # Filtrage par quartier
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

        # Analyse des profils
        if 'Date DPE' in df_affichage.columns:
            df_affichage = df_affichage.sort_values(by='Date DPE', ascending=False)
            date_actuelle = datetime.now()
            statuts_mandats = []
            
            for index, row in df_affichage.iterrows():
                d = row['Date DPE']
                adresse_str = str(row.get('Adresse Exacte', '')).lower()
                est_residence_secondaire = any(k in adresse_str for k in ["promenade des anglais", "mont boron", "quai", "france", "massena", "paradis"])
                
                try:
                    dt_dpe = pd.to_datetime(d)
                    diff_mois = (date_actuelle.year - dt_dpe.year) * 12 + (date_actuelle.month - dt_dpe.month)
                    
                    if 3 <= diff_mois <= 6:
                        statuts_mandats.append("🎯 Mandat Mûr (3-6 mois)")
                    elif est_residence_secondaire:
                        statuts_mandats.append("🏖️ Résidence Secondaire (~Cycle 5 ans)")
                    else:
                        statuts_mandats.append("⏳ Passoire F/G Standard")
                except:
                    statuts_mandats.append("📅 À qualifier")
                    
            df_affichage['Profil & Stratégie'] = statuts_mandats

        # Découpage du lot
        index_debut = (int(tranche_mois.split()[1]) - 1) * 50
        df_affichage = df_affichage.iloc[index_debut:index_debut + 50]
        
        st.session_state.df_affichage = df_affichage
        st.session_state.analyse_terminee = True


# --- AFFICHAGE PRINCIPAL EN 3 ONGLETS ---
if st.session_state.analyse_terminee:
    
    tab1, tab2, tab3 = st.tabs([
        "📊 1. Base & Repères Copropriété", 
        "🏖️ 2. Résidences Secondaires (~5 ans)", 
        "✉️ 3. Publipostage & Impression"
    ])
    
    with tab1:
        st.success(f"✅ Listing généré ! **{len(st.session_state.df_affichage)}** biens ciblés avec repères.")
        
        event_selection = st.dataframe(
            st.session_state.df_affichage, 
            use_container_width=True,
            on_select="rerun",
            selection_mode="multi-row",
            key="table_passoires"
        )
        
        st.download_button("📥 Télécharger ce lot complet (CSV)", data=st.session_state.df_affichage.to_csv(index=False).encode('utf-8'), file_name="listing_copropriete.csv", mime='text/csv')

    with tab2:
        st.header("🏖️ Ciblage Résidences Secondaires & Turnover (5 ans)")
        if 'Profil & Stratégie' in st.session_state.df_affichage.columns:
            df_sec = st.session_state.df_affichage[st.session_state.df_affichage['Profil & Stratégie'].str.contains("Résidence Secondaire", na=False)]
            if df_sec.empty:
                st.info("ℹ️ Aucun bien ne correspond aux critères de résidence secondaire dans ce lot.")
            else:
                st.success(f"🎯 **{len(df_sec)} biens** identifiés.")
                st.dataframe(df_sec, use_container_width=True)
                st.download_button("📥 Télécharger le listing (CSV)", data=df_sec.to_csv(index=False).encode('utf-8'), file_name="listing_residences_secondaires.csv", mime='text/csv')

    with tab3:
        st.header("✉️ Publipostage Intelligent & Impression")
        if 'Adresse Exacte' in st.session_state.df_affichage.columns:
            liste_adresses = st.session_state.df_affichage['Adresse Exacte'].dropna().unique().tolist()
            
            lignes_selectionnees_indices = []
            if event_selection and 'selection' in event_selection:
                lignes_selectionnees_indices = event_selection['selection'].get('rows', [])
            
            adresses_par_defaut = [liste_adresses[i] for i in lignes_selectionnees_indices if i < len(liste_adresses)]
            
            adresses_selectionnees = st.multiselect(
                "📍 Adresses sélectionnées pour le courrier :", 
                liste_adresses, 
                default=adresses_par_defaut
            )
            
            if adresses_selectionnees:
                date_jour = datetime.now().strftime("%d/%m/%Y")
                if st.button("🖨️ Préparer l'impression groupée", type="primary"):
                    st.success("📄 Courriers prêts pour l'impression (utilisez Ctrl+P / Cmd+P).")

                st.markdown("---")
                
                for adresse in adresses_selectionnees:
                    ligne_bien = st.session_state.df_affichage[st.session_state.df_affichage['Adresse Exacte'] == adresse].iloc[0]
                    profil = ligne_bien.get('Profil & Stratégie', '')
                    proprietaire = ligne_bien.get('Propriétaire / SCI', 'Propriétaire')
                    apt = ligne_bien.get('N° Apt', '')
                    lot = ligne_bien.get('N° Lot', '')
                    etage = ligne_bien.get('Étage', '')
                    bat = ligne_bien.get('Bâtiment', '')
                    
                    infos_repere = []
                    if bat: infos_repere.append(f"Bât. {bat}")
                    if etage: infos_repere.append(f"Étage : {etage}")
                    if apt: infos_repere.append(f"Apt {apt}")
                    if lot: infos_repere.append(f"Lot n° {lot}")
                    str_reperage = " | ".join(infos_repere) if infos_repere else "Bien identifié"

                    st.markdown(f"### 📍 {adresse}")
                    st.markdown(f"**Repères :** `{str_reperage}`")
                    st.text_area(
                        f"📄 Courrier publiposté :", 
                        value=f"Nice, le {date_jour}\n\nObjet : Stratégie patrimoniale au {adresse}\n\nMadame, Monsieur ({str_reperage}),\n\nNous nous permettons de vous contacter concernant votre bien...\n\nBien cordialement,\n\nNathalie Parra", 
                        height=200,
                        key=f"courrier_{adresse}"
                    )
                    st.markdown("---")
else:
    st.info("👉 Sélectionnez vos critères à gauche, puis cliquez sur **'Générer le listing certifié'**.")
