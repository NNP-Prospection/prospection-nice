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
st.markdown("Base de données certifiée : Passoires énergétiques, cycles de détention (5 ans) et publipostage.")

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
                "Port / Garibaldi": ["garibaldi", "lunel", "cassini", "barla", "arson", "republique", "port"],
                "Musiciens / Gambetta": ["gambetta", "berlioz", "gounod", "rossini", "verdi", "clemenceau", "victor hugo"]
            }
            mots_cles = rues_quartiers.get(secteur, [])
            if 'Adresse Exacte' in df_affichage.columns and mots_cles:
                pattern = '|'.join(mots_cles)
                df_affichage = df_affichage[df_affichage['Adresse Exacte'].astype(str).str.lower().str.contains(pattern, na=False, regex=True)]

        # Analyse combinée des profils et cycles
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
                    elif diff_mois < 3:
                        statuts_mandats.append("⚡ Turnover ~5 ans (Acquisition récente)")
                    else:
                        statuts_mandats.append("⏳ Longue détention (> 10 ans)")
                except:
                    statuts_mandats.append("📅 À qualifier")
                    
            df_affichage['Profil & Ancienneté'] = statuts_mandats

        # Découpage du lot
        index_debut = (int(tranche_mois.split()[1]) - 1) * 50
        df_affichage = df_affichage.iloc[index_debut:index_debut + 50]
        
        st.session_state.df_affichage = df_affichage
        st.session_state.analyse_terminee = True


# --- AFFICHAGE PRINCIPAL EN 3 ONGLETS ---
if st.session_state.analyse_terminee:
    
    tab1, tab2, tab3 = st.tabs([
        "📊 1. Passoires F&G & Mandats Mûrs", 
        "⏳ 2. Turnover ~5 ans & Cycles", 
        "✉️ 3. Publipostage Intelligent"
    ])
    
    # ONGLET 1 : BASE GLOBALE ET MANDATS MÛRS
    with tab1:
        st.success(f"✅ Listing généré ! **{len(st.session_state.df_affichage)}** biens ciblés pour le secteur : *{secteur}*.")
        st.dataframe(st.session_state.df_affichage, use_container_width=True)
        st.download_button("📥 Télécharger ce lot global (CSV)", data=st.session_state.df_affichage.to_csv(index=False).encode('utf-8'), file_name="listing_global.csv", mime='text/csv')

    # ONGLET 2 : CIBLAGE DÉDIÉ AU TURNOVER DE 5 ANS
    with tab2:
        st.header("⏳ Analyse des cycles de détention (~5 ans)")
        st.write("Cet onglet isole spécifiquement les biens dont le profil correspond au turnover de 5 ans (fin de premier cycle d'investissement ou arbitrage de résidence secondaire).")
        
        if 'Profil & Ancienneté' in st.session_state.df_affichage.columns:
            df_5ans = st.session_state.df_affichage[st.session_state.df_affichage['Profil & Ancienneté'].str.contains("Turnover ~5 ans", na=False)]
            
            if df_5ans.empty:
                st.info("ℹ️ Aucun bien ne correspond strictement au profil 'Turnover ~5 ans' dans ce lot de 50. Essayez un autre lot ou un autre secteur.")
            else:
                st.success(f"🎯 **{len(df_5ans)} biens** identifiés avec un profil de détention de type 'Turnover ~5 ans'.")
                st.dataframe(df_5ans, use_container_width=True)
                
                csv_5ans = df_5ans.to_csv(index=False).encode('utf-8')
                st.download_button("📥 Télécharger ce listing 'Turnover 5 ans' (CSV)", data=csv_5ans, file_name="listing_turnover_5ans.csv", mime='text/csv')
        else:
            st.warning("Données d'ancienneté non disponibles.")

    # ONGLET 3 : LE GÉNÉRATEUR DE COURRIERS EN LOT
    with tab3:
        st.header("✉️ Générateur Automatique de Courriers en Lot")
        st.write("Sélectionnez plusieurs adresses : l'application détecte le profil exact (Turnover 5 ans, Longue détention, Mandat mûr ou SCI) et rédige instantanément le courrier adapté.")
        
        if 'Adresse Exacte' in st.session_state.df_affichage.columns:
            liste_adresses = st.session_state.df_affichage['Adresse Exacte'].dropna().unique().tolist()
            adresses_selectionnees = st.multiselect("📍 Sélectionner les adresses pour le publipostage :", liste_adresses)
            
            if not adresses_selectionnees:
                st.info("👈 Cochez une ou plusieurs adresses dans le menu ci-dessus pour générer les courriers correspondants.")
            else:
                date_jour = datetime.now().strftime("%d/%m/%Y")
                
                for adresse in adresses_selectionnees:
                    ligne_bien = st.session_state.df_affichage[st.session_state.df_affichage['Adresse Exacte'] == adresse].iloc[0]
                    profil = ligne_bien.get('Profil & Ancienneté', '')
                    
                    est_sci = False
                    if 'Propriétaire' in ligne_bien.index and isinstance(ligne_bien['Propriétaire'], str):
                        if "SCI" in ligne_bien['Propriétaire'].upper():
                            est_sci = True
                            
                    # Attribution automatique du Courrier selon l'angle stratégique
                    if est_sci:
                        type_courrier = "🏢 Courrier 4 : Investisseur / SCI (Anticipation LMNP/PLF)"
                        sujet = f"Anticipation fiscale et arbitrage de votre actif au {adresse}"
                        corps = f"En qualité de professionnel intervenant sur la gestion patrimoniale à Nice, je m'adresse à vous concernant l'actif détenu au {adresse}.\n\nDans le cadre des révisions liées au Projet de Loi de Finances, des évolutions sont à l'étude (LMNP, SCI). Anticiper l'adoption de ces mesures est essentiel pour sécuriser la rentabilité nette de votre investissement."
                    
                    elif "Turnover" in profil:
                        type_courrier = "⚡ Courrier 1 : Turnover ~5 ans (Lassitude & Arbitrage)"
                        sujet = f"Évolution du marché niçois et valorisation de votre bien au {adresse}"
                        corps = f"Vous êtes propriétaire d'un bien immobilier dans cette résidence depuis environ cinq ans. Sur le marché niçois, ce cap correspond souvent à une réflexion sur votre patrimoine ou vos projets d'investissement...\n\nDepuis votre acquisition, le marché a connu de profondes mutations réglementaires (Loi Climat). En tant que spécialiste de votre secteur, je réalise actuellement des audits de positionnement pour plusieurs propriétaires du quartier."
                    
                    elif "Longue détention" in profil:
                        type_courrier = "⏳ Courrier 2 : Longue détention (> 10 ans) + Passoire F/G"
                        sujet = f"Impact réglementaire et optimisation fiscale de votre bien au {adresse}"
                        corps = f"Propriétaire de longue date au sein de cette copropriété, vous avez su capitaliser sur un secteur recherché de Nice.\n\nL'évolution récente du cadre légal impose de nouvelles contraintes lourdes (gel des loyers, interdiction de louer). Céder ce bien en l'état vous permet de vous libérer de ces contraintes tout en bénéficiant de l'abattement fiscal sur les plus-values lié à votre longue durée de détention."
                    
                    else:
                        type_courrier = "🎯 Courrier 3 : Mandat Mûr (Reconquête / DPE 3-6 mois)"
                        sujet = f"Stratégie de vente et positionnement de votre bien au {adresse}"
                        corps = f"En analysant les données techniques de votre secteur, j'ai noté qu'un Diagnostic de Performance Énergétique a été réalisé pour votre bien situé au {adresse} il y a quelques mois.\n\nSi votre bien est actuellement sur le marché et ne trouve pas preneur, sachez que les acquéreurs sont exigeants. Les caractéristiques énergétiques fragilisent le prix net vendeur si elles ne sont pas défendues par des arguments techniques solides."
                    
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
