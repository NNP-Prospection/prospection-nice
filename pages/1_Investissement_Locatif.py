import streamlit as st
import pandas as pd
from datetime import datetime
import os
import requests

st.set_page_config(
    page_title="Investissement Locatif & SCI - Cabinet Honorat", 
    layout="wide"
)

st.title("🏢 Espace Investissement Locatif & SCI - Nice")
st.markdown("Ciblage spécifique des structures sociétaires, des investisseurs et génération des courriers patrimoniaux.")

# --- NAVIGATION PAR ONGLET ---
tab1, tab2, tab3 = st.tabs([
    "1. Listing Investisseurs & SCI", 
    "2. Publipostage & Impression", 
    "3. Cartographie DVF & DPE"
])

# --- FONCTION DE CROISEMENT OPEN DATA SIRENE ---
@st.cache_data
def enrichir_avec_sirene(adresse_str):
    """
    Interroge l'API Open Data officielle (Recherche Entreprises / SIRENE)
    pour récupérer la SCI, le gérant et le siège social à partir de l'adresse.
    """
    try:
        url = f"https://recherche-entreprises.api.gouv.fr/recherche?q={adresse_str}&per_page=1"
        reponse = requests.get(url, timeout=3)
        if reponse.status_code == 200:
            data = reponse.json()
            resultats = data.get('results', [])
            if resultats:
                entite = resultats[0]
                nom = entite.get('nom_raison_sociale', '')
                siren = entite.get('siren', '')
                
                dirigeants = entite.get('dirigeants', [])
                nom_gerant = ""
                if dirigeants:
                    prenom = dirigeants[0].get('prenoms', '')
                    patronyme = dirigeants[0].get('nom', '')
                    nom_gerant = f"{prenom} {patronyme}".strip()
                
                siege = entite.get('siege', {})
                adresse_siege = siege.get('adresse', adresse_str)
                
                # On ne retourne que si c'est potentiellement une SCI ou entreprise
                if nom:
                     return {
                        'structure': nom,
                        'siren': siren,
                        'gerant': nom_gerant,
                        'siege': adresse_siege
                    }
    except Exception:
        pass
        
    return None

# --- CHARGEMENT DES FICHIERS ---
@st.cache_data
def load_data():
    df_dvf = pd.DataFrame()
    df_dpe = pd.DataFrame()
    
    # Chargement DVF
    try:
        dossier = 'data_dvf'
        if os.path.exists(dossier):
            fichiers = [os.path.join(dossier, f) for f in os.listdir(dossier) if f.endswith('.csv')]
            if fichiers:
                liste_df = [pd.read_csv(f, sep=';', low_memory=False) for f in fichiers]
                df_dvf = pd.concat(liste_df, ignore_index=True)
                if 'latitude' in df_dvf.columns and 'longitude' in df_dvf.columns:
                    df_dvf = df_dvf.rename(columns={'latitude': 'lat', 'longitude': 'lon'})
    except Exception as e:
        pass

    # Chargement DPE
    try:
        df_dpe = pd.read_csv('dpe_nice_fg.csv', low_memory=False)
    except Exception as e:
        pass
        
    return df_dvf, df_dpe

df_dvf, df_dpe = load_data()

with tab1:
    st.subheader("Ciblage et Qualification des Actifs / SCI")
    secteur = st.selectbox("Quartier / Secteur", ["Tous les secteurs", "Carré d'Or", "Promenade des Anglais", "Musiciens"])
    
    if st.button("Générer le listing Investisseurs / SCI", type="primary"):
        if not df_dpe.empty:
            df_recherche = df_dpe.copy()
            
            # Récupération de l'adresse
            col_adresse = next((col for col in ['adresse_ban', 'adresse_brute', 'adresse_propriete'] if col in df_recherche.columns), None)
            
            if col_adresse:
                # Filtrage par secteur
                if secteur != "Tous les secteurs":
                     rues_quartiers = {
                        "Carré d'Or": ["france", "massena", "paradis", "suede", "verdun", "meyerbeer", "congres", "cronstadt"],
                        "Promenade des Anglais": ["promenade des anglais", "etats-unis", "quai des etats-unis"],
                        "Musiciens": ["gambetta", "berlioz", "gounod", "rossini", "verdi", "clemenceau", "victor hugo"]
                    }
                     mots_cles = rues_quartiers.get(secteur, [])
                     if mots_cles:
                         pattern = '|'.join(mots_cles)
                         df_recherche = df_recherche[df_recherche[col_adresse].astype(str).str.lower().str.contains(pattern, na=False, regex=True)]

                # On prend un échantillon pour ne pas surcharger l'API (ex: les 20 premières adresses)
                adresses_a_tester = df_recherche[col_adresse].dropna().unique()[:20]
                
                data_rows = []
                with st.spinner("Recherche des structures (SCI) en cours..."):
                    for adresse in adresses_a_tester:
                        infos = enrichir_avec_sirene(adresse)
                        if infos: # On ne garde que si l'API a trouvé une structure
                            # Recherche des repères dans le DPE pour cette adresse
                            ligne_dpe = df_recherche[df_recherche[col_adresse] == adresse].iloc[0]
                            apt = ligne_dpe.get('numero_appartement', ligne_dpe.get('numero_appt', ''))
                            etage = ligne_dpe.get('etage', '')
                            
                            data_rows.append({
                                'Adresse Exacte': adresse,
                                'Propriétaire / SCI': infos['structure'],
                                'Gérant': infos['gerant'],
                                'SIREN': infos['siren'],
                                'Siège Social': infos['siege'],
                                'N° Apt': apt,
                                'Étage': etage
                            })
                
                st.session_state.df_locatif = pd.DataFrame(data_rows)
                if st.session_state.df_locatif.empty:
                    st.warning("Aucune structure sociétaire n'a été trouvée automatiquement pour cet échantillon d'adresses. L'API Sirene n'a peut-être pas de correspondance exacte.")
            else:
                st.error("Colonne d'adresse introuvable dans le fichier DPE.")
        else:
            st.error("Fichier DPE non chargé.")

    if 'df_locatif' in st.session_state and not st.session_state.df_locatif.empty:
        st.success(f"✅ {len(st.session_state.df_locatif)} structures trouvées.")
        event_selection_loc = st.dataframe(
            st.session_state.df_locatif, 
            use_container_width=True,
            on_select="rerun",
            selection_mode="multi-row",
            key="table_locatif"
        )
        st.download_button("📥 Télécharger le listing", data=st.session_state.df_locatif.to_csv(index=False).encode('utf-8'), file_name="listing_investissement_locatif.csv", mime='text/csv')

with tab2:
    st.subheader("✉️ Générateur de Courriers Investisseur & SCI")
    
    if 'df_locatif' in st.session_state and not st.session_state.df_locatif.empty and 'Adresse Exacte' in st.session_state.df_locatif.columns:
        liste_adresses_loc = st.session_state.df_locatif['Adresse Exacte'].dropna().unique().tolist()
        
        adresses_selectionnees = st.multiselect(
            "📍 Adresses sélectionnées :", 
            liste_adresses_loc, 
            default=liste_adresses_loc
        )
        
        if adresses_selectionnees:
            date_jour = datetime.now().strftime("%d/%m/%Y")
            
            if st.button("🖨️ Préparer l'impression groupée", type="primary"):
                st.success("📄 Courriers prêts.")

            st.markdown("---")
            
            for adresse in adresses_selectionnees:
                ligne_bien = st.session_state.df_locatif[st.session_state.df_locatif['Adresse Exacte'] == adresse].iloc[0]
                structure = ligne_bien.get('Propriétaire / SCI', '')
                gerant = ligne_bien.get('Gérant', '')
                siege = ligne_bien.get('Siège Social', adresse)
                apt = ligne_bien.get('N° Apt', '')
                etage = ligne_bien.get('Étage', '')
                
                infos_repere = []
                if etage and str(etage).lower() != 'nan': infos_repere.append(f"Étage : {etage}")
                if apt and str(apt).lower() != 'nan': infos_repere.append(f"Apt {apt}")
                str_reperage = " | ".join(infos_repere) if infos_repere else "Actif identifié"

                # Construction du destinataire
                if structure:
                    en_tete = f"Destinataire : {structure}\nSiège social : {siege}\n"
                    if gerant:
                         en_tete += f"À l'attention de {gerant},"
                    else:
                         en_tete += "À l'attention de la Gérance,"
                else:
                    en_tete = f"Destinataire : Propriétaire / Investisseur\nLocalisation de l'actif : {str_reperage}\nMadame, Monsieur (Investisseur - {str_reperage}),"

                st.markdown(f"### 📍 {adresse}")
                
                courrier_texte = f"""Nice, le {date_jour}

{en_tete}

Objet : Anticipation fiscale, arbitrage et optimisation de votre actif au {adresse} ({str_reperage})

En qualité de Conseil en Immobilier Patrimonial, je me permets de vous contacter concernant l'actif que vous détenez. 

Dans le cadre des évolutions de la fiscalité immobilière, l'anticipation de la gestion de votre portefeuille est essentielle pour sécuriser votre rentabilité nette et optimiser la transmission ou la revente de vos actifs.

Je me tiens à votre entière disposition pour réaliser un audit confidentiel de valorisation et vous accompagner dans vos projets d'arbitrage.

Bien cordialement,

Nathalie Parra
Conseil en Immobilier Patrimonial

CABINET PRIVÉ IMMOBILIER HONORAT
TRANSACTION . CONSEIL . PATRIMOINE"""
                
                st.text_area(f"Modèle de courrier - {adresse}", courrier_texte, height=350, key=f"courrier_loc_{adresse}")
                
                # Affichage du logo sous le texte
                logo_path = "Cabinet Immobilier Privé HONORAT.png"
                if os.path.exists(logo_path):
                    st.image(logo_path, width=200)
                
                st.markdown("---")
    else:
        st.info("👉 Générez d'abord le listing dans l'onglet 1.")

with tab3:
    st.subheader("🗺️ Cartographie")
    if not df_dvf.empty:
        st.map(df_dvf[['lat', 'lon']].dropna())
    else:
        st.warning("Données non disponibles.")
