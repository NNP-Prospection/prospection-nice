import streamlit as st
import pandas as pd
from datetime import datetime

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="Investissement Locatif & SCI - Nice",
    page_icon="🏢",
    layout="wide"
)

st.title("🏢 Espace Investissement Locatif & SCI - Nice")
st.markdown("Ciblage spécifique des structures sociétaires, des investisseurs et génération des courriers patrimoniaux.")

# --- INITIALISATION DE LA MÉMOIRE (SESSION STATE) ---
if 'df_locatif' not in st.session_state:
    st.session_state.df_locatif = pd.DataFrame()
if 'analyse_locative_terminee' not in st.session_state:
    st.session_state.analyse_locative_terminee = False

# Chargement du fichier source (on peut réutiliser le fichier DPE ou un fichier dédié si existant)
try:
    df_global = pd.read_csv('dpe_nice_fg.csv')
except Exception as e:
    df_global = pd.DataFrame()
    st.error(f"Erreur critique lors du chargement des données : {e}")

# --- BARRE LATÉRALE DE RECHERCHE INVESTISSEUR ---
st.sidebar.header("🎯 Ciblage Investisseurs & SCI")

secteur_locatif = st.sidebar.selectbox(
    "Quartier / Secteur",
    ["Tous les secteurs", "Carré d'Or", "Port / Garibaldi", "Musiciens / Gambetta", "Centre-ville"]
)

tranche_lot_loc = st.sidebar.selectbox(
    "Tranche de prospection", 
    ["Lot 1 (1 - 50)", "Lot 2 (51 - 100)", "Lot 3 (101 - 150)", "Lot 4 (151 - 200)"]
)

# Bouton de lancement
if st.sidebar.button("Générer le listing Investisseurs / SCI", type="primary"):
    if not df_global.empty:
        df_res = df_global.copy()
        
        # Filtrage ciblé sur les structures sociétaires (SCI, SARL, etc.) si la colonne existe, ou simulation d'analyse patrimoniale
        colonnes_locatif = {}
        for col in ['adresse_ban', 'adresse_brute', 'adresse_propriete']:
            if col in df_res.columns: colonnes_locatif[col] = 'Adresse Exacte'; break
            
        for col, nom in [
            ('numero_appartement', 'N° Apt'),
            ('numero_lot', 'N° Lot'),
            ('etage', 'Étage'),
            ('etiquette_dpe', 'Note DPE'),
            ('nom_proprietaire', 'Propriétaire / SCI'),
            ('raison_sociale', 'Propriétaire / SCI')
        ]:
            if col in df_res.columns: colonnes_locatif[col] = nom

        df_affichage = df_res[list(colonnes_locatif.keys())].rename(columns=colonnes_locatif)
        df_affichage = df_affichage.loc[:, ~df_affichage.columns.duplicated()]

        # Filtrage pour ne garder idéalement que les entités ou profils investisseurs si la colonne propriétaire existe
        if 'Propriétaire / SCI' in df_affichage.columns:
            # On met en avant les SCI / structures ou on garde une base qualifiée investisseur
            mask_sci = df_affichage['Propriétaire / SCI'].astype(str).str.upper().str.contains("SCI|SARL|SAS|HOLDING|IMMOBILIERE", na=False)
            if mask_sci.sum() > 0:
                df_affichage = df_affichage[mask_sci] # Priorité aux structures si présentes

        # Découpage du lot
        idx_deb = (int(tranche_lot_loc.split()[1]) - 1) * 50
        st.session_state.df_locatif = df_affichage.iloc[idx_deb:idx_deb + 50]
        st.session_state.analyse_locative_terminee = True


# --- AFFICHAGE PRINCIPAL EN 2 ONGLETS ---
if st.session_state.analyse_locative_terminee:
    
    tab1, tab2 = st.tabs([
        "📊 1. Listing Investisseurs & SCI", 
        "✉️ 2. Publipostage & Impression des Courriers"
    ])
    
    with tab1:
        st.success(f"✅ Listing généré ! **{len(st.session_state.df_locatif)}** actifs identifiés pour l'investissement locatif.")
        
        event_selection_loc = st.dataframe(
            st.session_state.df_locatif, 
            use_container_width=True,
            on_select="rerun",
            selection_mode="multi-row",
            key="table_locatif"
        )
        
        st.download_button("📥 Télécharger le listing Investisseurs (CSV)", data=st.session_state.df_locatif.to_csv(index=False).encode('utf-8'), file_name="listing_investissement_locatif.csv", mime='text/csv')

    with tab2:
        st.header("✉️ Générateur de Courriers Investisseur & SCI")
        st.write("Sélectionnez vos adresses ci-dessous pour personnaliser instantanément les courriers à destination des gérants de SCI ou investisseurs.")
        
        if 'Adresse Exacte' in st.session_state.df_locatif.columns:
            liste_adresses_loc = st.session_state.df_locatif['Adresse Exacte'].dropna().unique().tolist()
            
            lignes_selectionnees_indices = []
            if event_selection_loc and 'selection' in event_selection_loc:
                lignes_selectionnees_indices = event_selection_loc['selection'].get('rows', [])
            
            adresses_par_defaut = [liste_adresses_loc[i] for i in lignes_selectionnees_indices if i < len(liste_adresses_loc)]
            
            adresses_selectionnees = st.multiselect(
                "📍 Adresses sélectionnées pour la campagne investisseur :", 
                liste_adresses_loc, 
                default=adresses_par_defaut
            )
            
            if adresses_selectionnees:
                date_jour = datetime.now().strftime("%d/%m/%Y")
                
                if st.button("🖨️ Préparer l'impression groupée", type="primary"):
                    st.success("📄 Courriers investisseurs prêts ! Utilisez `Ctrl + P` ou `Cmd + P` pour lancer l'impression.")

                st.markdown("---")
                
                for adresse in adresses_selectionnees:
                    ligne_bien = st.session_state.df_locatif[st.session_state.df_locatif['Adresse Exacte'] == adresse].iloc[0]
                    proprietaire = ligne_bien.get('Propriétaire / SCI', 'Gérant / Investisseur')
                    apt = ligne_bien.get('N° Apt', '')
                    etage = ligne_bien.get('Étage', '')
                    
                    infos_repere = []
                    if etage: infos_repere.append(f"Étage : {etage}")
                    if apt: infos_repere.append(f"Apt {apt}")
                    str_reperage = " | ".join(infos_repere) if infos_repere else "Actif identifié"

                    st.markdown(f"### 📍 {adresse} ({str_reperage})")
                    st.markdown(f"**Structure / Propriétaire :** `{proprietaire}`")
                    
                    st.text_area(
                        f"📄 Modèle de courrier Investisseur / SCI :", 
                        value=f"Nice, le {date_jour}\n\nObjet : Anticipation fiscale, arbitrage et optimisation de votre actif au {adresse}\n\nÀ l'attention de {proprietaire},\n\nEn qualité de professionnel de l'immobilier patrimonial à Nice, je me permets de vous contacter concernant l'actif que vous détenez au {adresse} ({str_reperage}).\n\nDans le cadre des évolutions de la fiscalité immobilière (régime LMNP, fiscalité des SCI, loi de finances), l'anticipation de la gestion de votre portefeuille est essentielle pour sécuriser votre rentabilité nette et optimiser la transmission ou la revente de vos actifs.\n\nJe me tiens à votre entière disposition pour réaliser un audit confidentiel de valorisation.\n\nBien cordialement,\n\nNathalie Parra\n[Votre Agence / Coordonnées]", 
                        height=260,
                        key=f"courrier_loc_{adresse}"
                    )
                    st.markdown("---")
else:
    st.info("👉 Sélectionnez vos critères dans la barre latérale, puis cliquez sur **'Générer le listing Investisseurs / SCI'**.")
