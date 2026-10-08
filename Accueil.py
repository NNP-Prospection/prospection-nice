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
st.markdown("Base de données certifiée : Passoires énergétiques, résidences secondaires (turnover 5 ans) et publipostage ciblé.")

# --- INITIALISATION DE LA MÉMOIRE (SESSION STATE) ---
if 'df_affichage' not in st.session_state:
    st.session_state.df_affichage = pd.DataFrame()
if 'analyse_terminee' not in st.session_state:
    st.session_state.analyse_terminee = False

# Chargement du fichier CSV
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
        
        # Renommage des colonnes
        colonnes_utiles = {}
        if 'adresse_ban' in df_resultats.columns: colonnes_utiles['adresse_ban'] = 'Adresse Exacte'
        elif 'adresse_brute' in df_resultats.columns: colonnes_utiles['adresse_brute'] = 'Adresse Exacte'
            
        for col, nom in [('etiquette_dpe', 'Note DPE'), ('date_etablissement_dpe', 'Date DPE'), ('nom_proprietaire', 'Propriétaire')]:
            if col in df_resultats.columns: colonnes_utiles[col] = nom

        df_affichage = df_resultats[list(colonnes_utiles.keys())].rename(columns=colonnes_utiles) if colonnes_utiles else df_resultats 

        # Filtrage par quartier
        if secteur != "Tous les secteurs":
            rues_quartiers = {
                "Carré d'Or": ["france", "massena", "paradis", "suede", "verdun", "meyerbeer", "congres", "cronstadt"],
                "Promenade des Anglais": ["promenade des anglais", "etats-unis", "quai des etats-unis"],
                "Port / Garibaldi": ["garibaldi", "lunel", "cassini", "barla", "arson", "republique", "port"],
                "Mont Boron": ["mont boron", "jean lorrain", "carnot", "germaine", "andre joly", "valrose"],
                "Musiciens / Gambetta": ["gambetta", "berlioz", "gounod", "rossini", "verdi", "clemenceau", "victor hugo"]
            }
            mots_cles = rues_quartiers.get(secteur, [])
            if 'Adresse Exacte' in df_affichage.columns and mots_cles:
                pattern = '|'.join(mots_cles)
                df_affichage = df_affichage[df_affichage['Adresse Exacte'].astype(str).str.lower().str.contains(pattern, na=False, regex=True)]

        # Analyse des statuts
        if 'Date DPE' in df_affichage.columns:
            df_affichage = df_affichage.sort_values(by='Date DPE', ascending=False)
            date_actuelle = datetime.now()
            statuts_mandats = []
            
            for index, row in df_affichage.iterrows():
                d = row['Date DPE']
                try:
                    dt_dpe = pd.to_datetime(d)
                    diff_mois = (date_actuelle.year - dt_dpe.year) * 12 + (date_actuelle.month - dt_dpe.month)
                    
                    if 3 <= diff_mois <= 6:
                        statuts_mandats.append("🎯 Mandat Mûr (3-6 mois)")
                    else:
                        statuts_mandats.append("🏢 Standard / Autre")
                except:
                    statuts_mandats.append("📅 À qualifier")
                    
            df_affichage['Statut Mandat'] = statuts_mandats

        # Découpage du lot
        index_debut = (int(tranche_mois.split()[1]) - 1) * 50
        df_affichage = df_affichage.iloc[index_debut:index_debut + 50]
        
        st.session_state.df_affichage = df_affichage
        st.session_state.analyse_terminee = True


# --- AFFICHAGE PRINCIPAL EN 4 ONGLETS ---
if st.session_state.analyse_terminee:
    
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 1. Passoires F&G & Mandats Mûrs", 
        "🏖️ 2. Résidences Secondaires (~5 ans)", 
        "🏢 3. Investisseurs & SCI",
        "✉️ 4. Publipostage Intelligent"
    ])
    
    # ONGLET 1 : PASSOIRES & MANDATS MÛRS
    with tab1:
        st.success(f"✅ Listing généré ! **{len(st.session_state.df_affichage)}** biens ciblés pour le secteur : *{secteur}*.")
        st.dataframe(st.session_state.df_affichage, use_container_width=True)
        st.download_button("📥 Télécharger ce lot (CSV)", data=st.session_state.df_affichage.to_csv(index=False).encode('utf-8'), file_name="listing_passoires.csv", mime='text/csv')

    # ONGLET 2 : RÉSIDENCES SECONDAIRES / TURNOVER 5 ANS
    with tab2:
        st.header("🏖️ Ciblage Résidences Secondaires (Cycle des 5 ans)")
        st.write("Cet onglet cible spécifiquement les zones de villégiature et de résidences secondaires (Promenade des Anglais, Mont Boron, Carré d'Or) pour les propriétaires arrivant au bout d'un cycle d'environ 5 ans.")
        
        # Filtrage spécifique pour les résidences secondaires basé sur les secteurs géographiques clés
        if not st.session_state.df_affichage.empty and 'Adresse Exacte' in st.session_state.df_affichage.columns:
            mots_cles_secondaires = ["promenade des anglais", "mont boron", "france", "massena", "quai des etats-unis", "jean lorrain"]
            pattern_sec = '|'.join(mots_cles_secondaires)
            df_res_sec = st.session_state.df_affichage[st.session_state.df_affichage['Adresse Exacte'].astype(str).str.lower().str.contains(pattern_sec, na=False, regex=True)]
            
            if df_res_sec.empty:
                st.info("ℹ️ Aucun bien correspondant dans ce lot. Essayez de sélectionner 'Promenade des Anglais' ou 'Mont Boron' dans le menu de gauche.")
            else:
                st.success(f"🎯 **{len(df_res_sec)} biens** identifiés en zone de résidence secondaire potentielle.")
                st.dataframe(df_res_sec, use_container_width=True)
                st.download_button("📥 Télécharger le listing Résidences Secondaires (CSV)", data=df_res_sec.to_csv(index=False).encode('utf-8'), file_name="listing_residences_secondaires.csv", mime='text/csv')
        else:
            st.warning("Veuillez d'abord générer le listing depuis la barre latérale.")

    # ONGLET 3 : INVESTISSEURS & SCI
    with tab3:
        st.header("🏢 Investisseurs & Structures SCI")
        st.write("Isolation des biens détenus par des personnes morales ou SCI, sensibles aux évolutions fiscales (PLF 2027 / LMNP).")
        
        if 'Propriétaire' in st.session_state.df_affichage.columns:
            df_sci = st.session_state.df_affichage[st.session_state.df_affichage['Propriétaire'].astype(str).str.upper().str.contains("SCI", na=False)]
            if df_sci.empty:
                st.info("Aucune SCI explicitement détectée dans ce lot de 50.")
            else:
                st.dataframe(df_sci, use_container_width=True)
        else:
            st.info("Information propriétaire non chargée pour ce fichier.")

    # ONGLET 4 : LE GÉNÉRATEUR DE COURRIERS EN LOT
    with tab4:
        st.header("✉️ Générateur Automatique de Courriers en Lot")
        st.write("Sélectionnez vos adresses : l'application adapte le courrier selon qu'il s'agit d'une résidence secondaire, d'une passoire, d'un mandat mûr ou d'une SCI.")
        
        if 'Adresse Exacte' in st.session_state.df_affichage.columns:
            liste_adresses = st.session_state.df_affichage['Adresse Exacte'].dropna().unique().tolist()
            adresses_selectionnees = st.multiselect("📍 Sélectionner les adresses pour le publipostage :", liste_adresses)
            
            if not adresses_selectionnees:
                st.info("👈 Cochez une ou plusieurs adresses dans le menu ci-dessus pour générer les courriers correspondants.")
            else:
                date_jour = datetime.now().strftime("%d/%m/%Y")
                
                for adresse in adresses_selectionnees:
                    ligne_bien = st.session_state.df_affichage[st.session_state.df_affichage['Adresse Exacte'] == adresse].iloc[0]
                    statut = ligne_bien.get('Statut Mandat', '')
                    
                    # Détection contextuelle de l'angle
                    adresse_lower = str(adresse).lower()
                     est_residence_secondaire = any(k in adresse_lower for k in ["promenade des anglais", "mont boron", "quai"])
                    
                    if est_residence_secondaire:
                        type_courrier = "🏖️ Courrier Résidence Secondaire (~5 ans - Arbitrage & Gestion)"
                        sujet = f"Votre bien au {adresse} : Bilan patrimonial et projet de cession à Nice"
                        corps = f"Vous êtes propriétaire d'un pied-à-terre ou d'une résidence secondaire dans cette résidence prisée de Nice depuis plusieurs années. Ce cap de détention (autour de 5 ans) correspond souvent à une évolution de vos usages, une lassitude de la gestion à distance ou l'envie de réorienter votre épargne immobilière.\n\nLe marché niçois actuel offre de belles opportunités d'arbitrage pour les propriétaires désireux de valoriser leur actif au plus haut.\n\nJe vous propose un échange confidentiel pour évaluer la valeur de votre bien et discuter de vos projets."
                    elif "3-6 mois" in statut:
                        type_courrier = "🎯 Courrier Mandat Mûr (Reconquête)"
                        sujet = f"Stratégie de vente et positionnement de votre bien au {adresse}"
                        corps = f"En analysant les données de votre secteur, j'ai noté qu'un diagnostic a été réalisé pour votre bien situé au {adresse} il y a quelques mois. S'il est actuellement sur le marché sans succès, je peux vous apporter un regard neuf et technique."
                    else:
                        type_courrier = "⏳ Courrier Passoire Thermique (Loi Climat & Résilience)"
                        sujet = f"Impact de la Loi Climat sur votre bien au {adresse}"
                        corps = f"Propriétaire d'un bien classé F ou G au {adresse}, vous faites face aux nouvelles obligations de la Loi Climat (gel des loyers, interdiction de louer). Céder ce bien en l'état permet de purger votre plus-value et d'éviter les contraintes de travaux."
                    
                    st.markdown(f"### 📍 {adresse}")
                    st.markdown(f"**Stratégie appliquée :** `{type_courrier}`")
                    st.text_area(
                        f"📄 Modèle de courrier prêt à imprimer :", 
                        value=f"Nice, le {date_jour}\n\nObjet : {sujet}\n\nMadame, Monsieur,\n\n{corps}\n\nBien cordialement,\n\nNathalie Parra\n[Votre Agence / Coordonnées]", 
                        height=260,
                        key=f"courrier_{adresse}"
                    )
                    st.markdown("---")
else:
    st.info("👉 Sélectionnez vos critères à gauche, puis cliquez sur **'Générer le listing certifié'**.")
