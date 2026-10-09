import streamlit as st
import pandas as pd
from datetime import datetime
import os

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="Espace de Prospection - Cabinet Honorat",
    page_icon="🏠",
    layout="wide"
)

st.title("🏠 Mon espace de prospection immobilière - Nice")
st.markdown("Base de données certifiée : Passoires F/G, Cycle ~5 ans (DPE) et Publipostage patrimonial.")

# --- INITIALISATION DE LA MÉMOIRE (SESSION STATE) ---
if 'df_affichage' not in st.session_state:
    st.session_state.df_affichage = pd.DataFrame()
if 'analyse_terminee' not in st.session_state:
    st.session_state.analyse_terminee = False

# Chargement propre du fichier DPE existant
try:
    df_global = pd.read_csv('dpe_nice_fg.csv', low_memory=False)
except Exception as e:
    df_global = pd.DataFrame()
    st.error(f"Erreur critique lors du chargement du fichier DPE : {e}")

# --- FONCTION POUR NETTOYER LES .0 ---
def formater_numero(val):
    if pd.isna(val) or str(val).lower() in ['nan', 'none', '']:
        return ''
    val_str = str(val).strip()
    if val_str.endswith('.0'):
        return val_str[:-2]
    return val_str

# --- BARRE LATÉRALE DE RECHERCHE ---
st.sidebar.header("🎯 Critères de ciblage")

objectif = st.sidebar.selectbox(
    "Objectif de prospection",
    ["Passoires Énergétiques (F & G) - Standard", "Cycle de détention ~5 ans (DPE)"]
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
        
        colonnes_a_garder = {}
        for col in ['adresse_ban', 'adresse_brute', 'adresse_propriete']:
            if col in df_resultats.columns:
                colonnes_a_garder[col] = 'Adresse Exacte'
                break
                
        for col in df_resultats.columns:
            col_lower = col.lower()
            if 'etage' in col_lower or 'niveau' in col_lower:
                colonnes_a_garder[col] = 'Étage'
            elif 'appartement' in col_lower or 'porte' in col_lower or 'numero_appt' in col_lower:
                colonnes_a_garder[col] = 'N° Apt'
            elif 'lot' in col_lower:
                colonnes_a_garder[col] = 'N° Lot'
            elif 'batiment' in col_lower or 'bat' in col_lower:
                colonnes_a_garder[col] = 'Bâtiment'
            elif 'etiquette' in col_lower and 'dpe' in col_lower:
                colonnes_a_garder[col] = 'Note DPE'
            elif 'date' in col_lower and 'dpe' in col_lower:
                colonnes_a_garder[col] = 'Date DPE'
            elif 'proprietaire' in col_lower or 'raison_sociale' in col_lower:
                colonnes_a_garder[col] = 'Propriétaire / SCI'

        df_affichage = df_resultats[list(colonnes_a_garder.keys())].rename(columns=colonnes_a_garder)
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

        # Analyse temporelle basée sur le DPE
        if 'Date DPE' in df_affichage.columns:
            df_affichage = df_affichage.sort_values(by='Date DPE', ascending=False)
            date_actuelle = datetime.now()
            statuts_mandats = []
            
            for index, row in df_affichage.iterrows():
                d = row['Date DPE']
                adresse_str = str(row.get('Adresse Exacte', '')).lower()
                est_secteur_cle = any(k in adresse_str for k in ["promenade des anglais", "mont boron", "quai", "france", "massena", "paradis"])
                
                try:
                    dt_dpe = pd.to_datetime(d)
                    diff_annees = date_actuelle.year - dt_dpe.year
                    
                    if 4 <= diff_annees <= 6 or est_secteur_cle:
                        statuts_mandats.append("🏖️ Cycle ~5 ans (Passoire F/G)")
                    else:
                        statuts_mandats.append("⏳ Passoire F/G Standard")
                except:
                    statuts_mandats.append("📅 À qualifier")
                    
            df_affichage['Profil & Stratégie'] = statuts_mandats

        if objectif == "Cycle de détention ~5 ans (DPE)" and 'Profil & Stratégie' in df_affichage.columns:
            df_affichage = df_affichage[df_affichage['Profil & Stratégie'].str.contains("Cycle ~5 ans", na=False)]

        index_debut = (int(tranche_mois.split()[1]) - 1) * 50
        df_affichage = df_affichage.iloc[index_debut:index_debut + 50]
        
        st.session_state.df_affichage = df_affichage
        st.session_state.analyse_terminee = True


# --- AFFICHAGE PRINCIPAL EN 3 ONGLETS ---
if st.session_state.analyse_terminee:
    
    tab1, tab2, tab3 = st.tabs([
        "📊 1. Listing & Repères Copropriété", 
        "🏖️ 2. Cycle de détention ~5 ans (DPE)", 
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
        
        st.download_button("📥 Télécharger ce lot (CSV)", data=st.session_state.df_affichage.to_csv(index=False).encode('utf-8'), file_name="listing_prospection.csv", mime='text/csv')

    with tab2:
        st.header("🏖️ Cycle de détention ~5 ans (Basé sur les DPE F/G)")
        st.write("Biens identifiés sur les zones clés et approchants d'un cycle de détention de 5 ans via l'historique DPE.")
        
        if 'Profil & Stratégie' in st.session_state.df_affichage.columns:
            df_cycle = st.session_state.df_affichage[st.session_state.df_affichage['Profil & Stratégie'].str.contains("Cycle ~5 ans", na=False)]
            if df_cycle.empty:
                st.info("ℹ️ Aucun bien ne correspond à ce critère dans ce lot.")
            else:
                st.success(f"🎯 **{len(df_cycle)} biens** identifiés.")
                st.dataframe(df_cycle, use_container_width=True)
                st.download_button("📥 Télécharger le listing Cycle 5 ans (CSV)", data=df_cycle.to_csv(index=False).encode('utf-8'), file_name="cycle_5ans_dpe.csv", mime='text/csv')

    with tab3:
        st.header("✉️ Publipostage Cible & Impression")
        
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
                    st.success("📄 Courriers prêts pour l'impression (utilisez `Ctrl + P` ou `Cmd + P`).")

                st.markdown("---")
                
                for adresse in adresses_selectionnees:
                    ligne_bien = st.session_state.df_affichage[st.session_state.df_affichage['Adresse Exacte'] == adresse].iloc[0]
                    profil = ligne_bien.get('Profil & Stratégie', '')
                    proprietaire = ligne_bien.get('Propriétaire / SCI', '')
                    
                    # Application du nettoyage pour enlever les .0
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

                    # Gestion propre du destinataire
                    if proprietaire and str(proprietaire).lower() != 'nan' and len(str(proprietaire).strip()) > 1:
                        destinataire_affichage = f"Destinataire : {proprietaire}"
                        appel_destinataire = f"À l'attention de {proprietaire},"
                    else:
                        destinataire_affichage = f"Destinataire : Propriétaire / Copropriétaire\nLocalisation du lot : {str_reperage}"
                        appel_destinataire = f"Madame, Monsieur (Propriétaire du lot - {str_reperage}),"

                    st.markdown(f"### 📍 {adresse}")
                    st.markdown(f"**Ciblage :** `{str_reperage}` | **Profil :** `{profil}`")
                    
                    courrier_modele = f"""Nice, le {date_jour}

{destinataire_affichage}
Adresse du bien : {adresse}

{appel_destinataire}

Objet : Anticipation réglementaire, valorisation et optimisation de votre actif immobilier au {adresse} ({str_reperage})

En qualité de Conseil en Immobilier Patrimonial, je me permets de vous contacter directement concernant l'actif dont vous êtes propriétaire dans cet immeuble. 

Au regard des récentes évolutions de la législation énergétique (calendrier d'interdiction de mise en location des passoires thermiques F et G) et de la fiscalité (régime LMNP, optimisation de la valeur vénale), l'anticipation de la gestion de votre patrimoine est devenue un enjeu majeur pour sécuriser votre rentabilité nette et éviter toute décote de votre bien.

Je me tiens à votre entière disposition pour réaliser un audit confidentiel, une estimation patrimoniale actualisée et vous accompagner dans vos arbitrages.

Bien cordialement,

Nathalie Parra
Conseil en Immobilier Patrimonial

CABINET PRIVÉ IMMOBILIER HONORAT
TRANSACTION . CONSEIL . PATRIMOINE"""

                    st.text_area(
                        f"📄 Modèle de courrier - {adresse}", 
                        value=courrier_modele, 
                        height=280,
                        key=f"courrier_{adresse}"
                    )
                    
                    # Affichage du logo sous le texte du courrier
                    logo_path = "Cabinet Immobilier Privé HONORAT.png"
                    if os.path.exists(logo_path):
                        st.image(logo_path, width=200)
                        
                    st.markdown("---")
else:
    st.info("👉 Sélectionnez vos critères à gauche, puis cliquez sur **'Générer le listing certifié'**.")
