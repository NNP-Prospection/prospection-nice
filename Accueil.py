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
st.markdown("Base de données certifiée : Passoires énergétiques, résidences secondaires et publipostage intelligent.")

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
                "Mont Boron": ["mont boron", "jean lorrain", "carnot", "germaine", "andre joly", "valrose", "cap de nice"],
                "Musiciens / Gambetta": ["gambetta", "berlioz", "gounod", "rossini", "verdi", "clemenceau", "victor hugo"],
                "Centre-ville": ["jean medecin", "gioffredo", "marechal foch", "pastorelli", "assalit", "durandy"]
            }
            mots_cles = rues_quartiers.get(secteur, [])
            if 'Adresse Exacte' in df_affichage.columns and mots_cles:
                pattern = '|'.join(mots_cles)
                df_affichage = df_affichage[df_affichage['Adresse Exacte'].astype(str).str.lower().str.contains(pattern, na=False, regex=True)]

        # Analyse des profils et détection des résidences secondaires (secteurs ciblés)
        if 'Date DPE' in df_affichage.columns:
            df_affichage = df_affichage.sort_values(by='Date DPE', ascending=False)
            date_actuelle = datetime.now()
            statuts_mandats = []
            
            for index, row in df_affichage.iterrows():
                d = row['Date DPE']
                adresse_str = str(row.get('Adresse Exacte', '')).lower()
                
                # Détection indicielle résidence secondaire (Promenade des Anglais, Mont Boron, Carré d'Or)
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
        "📊 1. Passoires F&G & Mandats Mûrs", 
        "🏖️ 2. Résidences Secondaires (~5 ans)", 
        "✉️ 3. Publipostage Intelligent"
    ])
    
    # ONGLET 1 : BASE GLOBALE
    with tab1:
        st.success(f"✅ Listing généré ! **{len(st.session_state.df_affichage)}** biens ciblés pour le secteur : *{secteur}*.")
        st.dataframe(st.session_state.df_affichage, use_container_width=True)
        st.download_button("📥 Télécharger ce lot global (CSV)", data=st.session_state.df_affichage.to_csv(index=False).encode('utf-8'), file_name="listing_global.csv", mime='text/csv')

    # ONGLET 2 : RÉSIDENCES SECONDAIRES & CYCLES DE 5 ANS
    with tab2:
        st.header("🏖️ Ciblage Résidences Secondaires & Turnover (5 ans)")
        st.write("Cet onglet isole les biens situés sur les secteurs à forte concentration de résidences secondaires (Promenade, Mont Boron, Carré d'Or) pour actionner l'approche patrimoniale et le cycle d'arbitrage.")
        
        if 'Profil & Stratégie' in st.session_state.df_affichage.columns:
            df_sec = st.session_state.df_affichage[st.session_state.df_affichage['Profil & Stratégie'].str.contains("Résidence Secondaire", na=False)]
            
            if df_sec.empty:
                st.info("ℹ️ Aucun bien ne correspond aux critères de résidence secondaire dans ce lot. Élargissez le secteur ou changez de lot.")
            else:
                st.success(f"🎯 **{len(df_sec)} biens** identifiés en zone de résidence secondaire.")
                st.dataframe(df_sec, use_container_width=True)
                
                csv_sec = df_sec.to_csv(index=False).encode('utf-8')
                st.download_button("📥 Télécharger le listing 'Résidences Secondaires' (CSV)", data=csv_sec, file_name="listing_residences_secondaires.csv", mime='text/csv')
        else:
            st.warning("Données de profil non disponibles.")

    # ONGLET 3 : LE GÉNÉRATEUR DE COURRIERS EN LOT
    with tab3:
        st.header("✉️ Générateur Automatique de Courriers en Lot")
        st.write("Sélectionnez plusieurs adresses : l'application détecte le profil et rédige instantanément le courrier adapté.")
        
        if 'Adresse Exacte' in st.session_state.df_affichage.columns:
            liste_adresses = st.session_state.df_affichage['Adresse Exacte'].dropna().unique().tolist()
            adresses_selectionnees = st.multiselect("📍 Sélectionner les adresses pour le publipostage :", liste_adresses)
            
            if not adresses_selectionnees:
                st.info("👈 Cochez une ou plusieurs adresses dans le menu ci-dessus pour générer les courriers correspondants.")
            else:
                date_jour = datetime.now().strftime("%d/%m/%Y")
                
                for adresse in adresses_selectionnees:
                    ligne_bien = st.session_state.df_affichage[st.session_state.df_affichage['Adresse Exacte'] == adresse].iloc[0]
                    profil = ligne_bien.get('Profil & Stratégie', '')
                    
                    est_sci = False
                    if 'Propriétaire' in ligne_bien.index and isinstance(ligne_bien['Propriétaire'], str):
                        if "SCI" in ligne_bien['Propriétaire'].upper():
                            est_sci = True
                            
                    # Attribution automatique du Courrier
                    if est_sci:
                        type_courrier = "🏢 Courrier 4 : Investisseur / SCI (Anticipation LMNP/PLF)"
                        sujet = f"Anticipation fiscale et arbitrage de votre actif au {adresse}"
                        corps = f"En qualité de professionnel intervenant sur la gestion patrimoniale à Nice, je m'adresse à vous concernant l'actif détenu au {adresse}.\n\nDans le cadre des révisions liées au Projet de Loi de Finances, des évolutions sont à l'étude (LMNP, SCI). Anticiper l'adoption de ces mesures est essentiel pour sécuriser la rentabilité nette de votre investissement."
                    
                    elif "Résidence Secondaire" in profil:
                        type_courrier = "🏖️ Courrier Résidence Secondaire (~Cycle 5 ans)"
                        sujet = f"Évolution du marché niçois et valorisation de votre pied-à-terre au {adresse}"
                        corps = f"Vous êtes propriétaire d'un bien immobilier dans cette résidence depuis environ cinq ans. Sur le marché niçois, cette durée de détention correspond souvent à un cap de réflexion : évolution des projets personnels, fin d'un cycle d'investissement, ou arbitrage patrimonial.\n\nEn tant que spécialiste de votre secteur, je réalise actuellement des audits de positionnement pour plusieurs propriétaires du quartier souhaitant faire un point d'étape."
                    
                    elif "Mandat Mûr" in profil:
                        type_courrier = "🎯 Courrier 3 : Mandat Mûr (Reconquête / DPE 3-6 mois)"
                        sujet = f"Stratégie de vente et positionnement de votre bien au {adresse}"
                        corps = f"En analysant les données techniques de votre secteur, j'ai noté qu'un Diagnostic de Performance Énergétique a été réalisé pour votre bien situé au {adresse} il y a quelques mois.\n\nSi votre bien est actuellement sur le marché et ne trouve pas preneur, sachez que les acquéreurs sont exigeants. Les caractéristiques énergétiques fragilisent le prix net vendeur si elles ne sont pas défendues par des arguments techniques solides."
                    
                    else:
                        type_courrier = "⏳ Courrier Passoire F/G Standard"
                        sujet = f"Impact réglementaire et optimisation de votre bien au {adresse}"
                        corps = f"Propriétaire d'un bien au sein de cette copropriété, je me permets de vous contacter car l'évolution récente du cadre légal (Loi Climat et Résilience) impose de nouvelles contraintes lourdes sur les biens énergivores (gel des loyers, interdiction de louer).\n\nCéder ce bien en l'état ou anticiper sa valorisation vous permet de vous libérer de ces contraintes techniques."
                    
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
    st.info("👉 Sélectionnez vos critères dans le menu à gauche, puis cliquez sur **'Générer le listing certifié'**.")
