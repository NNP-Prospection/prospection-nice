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
st.markdown("Base de données certifiée : Repères de copropriété, résidences secondaires et publipostage.")

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
        
        # Mappage large pour récupérer TOUS les repères d'identification du bien
        colonnes_utiles = {}
        
        # Adresses et codes postaux
        for col in ['adresse_ban', 'adresse_brute', 'adresse_propriete']:
            if col in df_resultats.columns: colonnes_utiles[col] = 'Adresse Exacte'
        for col in ['code_postal_ban', 'code_postal']:
            if col in df_resultats.columns: colonnes_utiles[col] = 'Code Postal'
            
        # Repères de copropriété essentiels pour le boîtage
        for col, nom in [
            ('numero_appartement', 'N° Apt'),
            ('numero_lot', 'N° Lot'),
            ('batiment', 'Bâtiment'),
            ('escalier', 'Escalier'),
            ('etage', 'Étage'),
            ('surface_habitable_logement', 'Surface (m²)'),
            ('etiquette_dpe', 'Note DPE'),
            ('date_etablissement_dpe', 'Date DPE'),
            ('nom_proprietaire', 'Propriétaire / SCI'),
            ('raison_sociale', 'Propriétaire / SCI')
        ]:
            if col in df_resultats.columns:
                colonnes_utiles[col] = nom

        # Application du renommage sur les colonnes présentes
        colonnes_finales_presentes = {k: v for k, v in colonnes_utiles.items() if k in df_resultats.columns}
        df_affichage = df_resultats[list(colonnes_finales_presentes.keys())].rename(columns=colonnes_finales_presentes)

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

        # Analyse des profils et repérage géographique des résidences secondaires
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
    
    # ONGLET 1 : BASE GLOBALE AVEC REPÈRES COMPLETS ET SÉLECTION
    with tab1:
        st.success(f"✅ Listing généré ! **{len(st.session_state.df_affichage)}** biens ciblés avec repères pour le secteur : *{secteur}*.")
        st.info("💡 *Le tableau affiche désormais les numéros de lots, d'appartements, d'étages et les noms de SCI lorsqu'ils sont renseignés.*")
        
        event_selection = st.dataframe(
            st.session_state.df_affichage, 
            use_container_width=True,
            on_select="rerun",
            selection_mode="multi-row",
            key="table_passoires"
        )
        
        st.download_button("📥 Télécharger ce lot complet (CSV)", data=st.session_state.df_affichage.to_csv(index=False).encode('utf-8'), file_name="listing_copropriete.csv", mime='text/csv')

    # ONGLET 2 : RÉSIDENCES SECONDAIRES
    with tab2:
        st.header("🏖️ Ciblage Résidences Secondaires & Turnover (5 ans)")
        st.write("Biens localisés sur les grands axes de villégiature niçoise.")
        
        if 'Profil & Stratégie' in st.session_state.df_affichage.columns:
            df_sec = st.session_state.df_affichage[st.session_state.df_affichage['Profil & Stratégie'].str.contains("Résidence Secondaire", na=False)]
            
            if df_sec.empty:
                st.info("ℹ️ Aucun bien ne correspond aux critères de résidence secondaire dans ce lot.")
            else:
                st.success(f"🎯 **{len(df_sec)} biens** identifiés.")
                st.dataframe(df_sec, use_container_width=True)
                csv_sec = df_sec.to_csv(index=False).encode('utf-8')
                st.download_button("📥 Télécharger le listing (CSV)", data=csv_sec, file_name="listing_residences_secondaires.csv", mime='text/csv')
        else:
            st.warning("Données de profil non disponibles.")

    # ONGLET 3 : IMPRESSION ET COURRIERS
    with tab3:
        st.header("✉️ Publipostage Intelligent & Impression")
        st.write("Générez vos courriers personnalisés avec les informations de lot, d'étage et de structure juridique.")
        
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
            
            if not adresses_selectionnees:
                st.info("👈 Cochez des lignes dans le tableau de l'onglet 1 ou sélectionnez des adresses ci-dessus.")
            else:
                date_jour = datetime.now().strftime("%d/%m/%Y")
                
                if st.button("🖨️ Préparer l'impression groupée", type="primary"):
                    st.success("📄 Courriers prêts pour l'impression (utilisez Ctrl+P / Cmd+P).")

                st.markdown("---")
                
                for adresse in adresses_selectionnees:
                    ligne_bien = st.session_state.df_affichage[st.session_state.df_affichage['Adresse Exacte'] == adresse].iloc[0]
                    profil = ligne_bien.get('Profil & Stratégie', '')
                    
                    # Récupération propre des repères s'ils existent dans la ligne
                    proprietaire = ligne_bien.get('Propriétaire / SCI', 'Propriétaire')
                    apt = ligne_bien.get('N° Apt', '')
                    lot = ligne_bien.get('N° Lot', '')
                    etage = ligne_bien.get('Étage', '')
                    bat = ligne_bien.get('Bâtiment', '')
                    
                    # Constitution d'une mention de repérage pour l'en-tête du courrier
                    infos_repere = []
                    if bat: infos_repere.append(f"Bât. {bat}")
                    if etage: infos_repere.append(f"Étage : {etage}")
                    if apt: infos_repere.append(f"Apt {apt}")
                    if lot: infos_repere.append(f"Lot n° {lot}")
                    str_reperage = " | ".join(infos_repere) if infos_repere else "Bien identifié"

                    est_sci = False
                    if isinstance(proprietaire, str) and ("SCI" in proprietaire.upper() or "SARL" in proprietaire.upper() or "SAS" in proprietaire.upper()):
                        est_sci = True
                            
                    # Attribution automatique du Courrier
                    if est_sci:
                        type_courrier = f"🏢 Courrier 4 : Investisseur / SCI ({proprietaire})"
                        sujet = f"Anticipation fiscale et arbitrage de votre actif au {adresse}"
                        corps = f"À l'attention de la société {proprietaire},\n\nConcernant l'actif détenu au {adresse} ({str_reperage}), dans le cadre des révisions liées au Projet de Finances (LMNP/SCI), anticiper l'évolution des amortissements est essentiel pour sécuriser la valeur de votre investissement."
                    
                    elif "Résidence Secondaire" in profil:
                        type_courrier = "🏖️ Courrier Résidence Secondaire (~Cycle 5 ans)"
                        sujet = f"Évolution du marché niçois et valorisation de votre pied-à-terre au {adresse}"
                        corps = f"Madame, Monsieur (Propriétaire - {str_reperage}),\n\nPropriétaire de ce pied-à-terre depuis environ cinq ans, ce cap correspond souvent sur Nice à une réflexion sur l'arbitrage ou la valorisation patrimoniale avant d'entamer de nouveaux cycles de gestion."
                    
                    elif "Mandat Mûr" in profil:
                        type_courrier = "🎯 Courrier 3 : Mandat Mûr (Reconquête / DPE 3-6 mois)"
                        sujet = f"Stratégie de vente et positionnement de votre bien au {adresse}"
                        corps = f"Madame, Monsieur (Propriétaire - {str_reperage}),\n\nEn analysant votre secteur, un DPE a été réalisé il y a quelques mois pour ce bien. Si la commercialisation stagne, c'est que les critères énergétiques exigent une défense technique irréprochable."
                    
                    else:
                        type_courrier = "⏳ Courrier Passoire F/G Standard"
                        sujet = f"Impact réglementaire et optimisation de votre bien au {adresse}"
                        corps = f"Madame, Monsieur (Propriétaire - {str_reperage}, {str_reperage}),\n\nL'évolution de la Loi Climat impose des contraintes lourdes sur ce bien énergivore. Anticiper sa cession en l'état vous permet de purger votre plus-value sans subir les coûts de rénovation de copropriété."
                    
                    st.markdown(f"### 📍 {adresse}")
                    st.markdown(f"**Repères :** `{str_reperage}` | **Cible :** `{type_courrier}`")
                    st.text_area(
                        f"📄 Courrier publiposté :", 
                        value=f"Nice, le {date_jour}\n\nObjet : {sujet}\n\n{corps}\n\nBien cordialement,\n\nNathalie Parra\n[Votre Agence / Coordonnées]", 
                        height=240,
                        key=f"courrier_{adresse}"
                    )
                    st.markdown("---")
else:
    st.info("👉 Sélectionnez vos critères à gauche, puis cliquez sur **'Générer le listing certifié'**.")
