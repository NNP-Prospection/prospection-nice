import streamlit as st
import pandas as pd
from datetime import datetime
import os

st.set_page_config(
    page_title="Investissement Locatif & SCI - Cabinet Honorat", 
    layout="wide"
)

st.title("🏢 Espace Investissement Locatif & SCI - Nice")
st.markdown("Ciblage spécifique des structures sociétaires, des investisseurs et génération des courriers patrimoniaux - Cabinet Privé Immobilier Honorat.")

# --- NAVIGATION PAR ONGLET ---
tab1, tab2, tab3 = st.tabs([
    "1. Listing Investisseurs & SCI", 
    "2. Publipostage & Impression", 
    "3. Cartographie DVF & DPE (Carré d'Or)"
])

# --- CHARGEMENT DES FICHIERS DVF LOCAUX (Dossier data_dvf) ---
@st.cache_data
def load_dvf():
    try:
        dossier = 'data_dvf'
        if os.path.exists(dossier):
            fichiers = [os.path.join(dossier, f) for f in os.listdir(dossier) if f.endswith('.csv')]
        else:
            fichiers = []
            
        if not fichiers:
            return pd.DataFrame()
            
        liste_df = [pd.read_csv(f, sep=';', low_memory=False) for f in fichiers]
        df = pd.concat(liste_df, ignore_index=True)
        df = df.drop_duplicates()
        
        if 'latitude' in df.columns and 'longitude' in df.columns:
            df = df.rename(columns={'latitude': 'lat', 'longitude': 'lon'})
            
        df = df.dropna(subset=['valeur_fonciere', 'surface_reelle_bati', 'lat', 'lon']).copy()
        
        df['valeur_fonciere'] = pd.to_numeric(df['valeur_fonciere'].astype(str).str.replace(',', '.'), errors='coerce')
        df['surface_reelle_bati'] = pd.to_numeric(df['surface_reelle_bati'].astype(str).str.replace(',', '.'), errors='coerce')
        
        df['prix_m2'] = df['valeur_fonciere'] / df['surface_reelle_bati']
        
        return df[(df['prix_m2'] > 1000) & (df['prix_m2'] < 25000)]
    except Exception as e:
        st.error(f"Erreur lors du chargement des fichiers DVF : {e}")
        return pd.DataFrame()

df_dvf = load_dvf()

with tab1:
    st.subheader("Ciblage et Qualification des Actifs / SCI")
    secteur = st.selectbox("Quartier / Secteur", ["Carré d'Or", "Promenade des Anglais", "Musiciens"])
    
    if st.button("Générer le listing Investisseurs / SCI", type="primary"):
        st.success(f"Analyse du secteur : {secteur}")
        
        adresses_exemple = [
            "11 Avenue du Cap de Nice",
            "4 Avenue de Verdun (Carré d'Or)",
            "12 Rue Paradis"
        ]
        
        if 'df_locatif' not in st.session_state:
            st.session_state.df_locatif = pd.DataFrame()
            
        data_rows = []
        for adresse in adresses_exemple:
            data_rows.append({
                'Adresse Exacte': adresse,
                'Propriétaire / SCI': '',  # Laissé vide si non connu pour garder la propreté du courrier
                'N° Apt': 'Apt 22',
                'Étage': '3ème'
            })
        st.session_state.df_locatif = pd.DataFrame(data_rows)

    if not st.session_state.get('df_locatif', pd.DataFrame()).empty:
        event_selection_loc = st.dataframe(
            st.session_state.df_locatif, 
            use_container_width=True,
            on_select="rerun",
            selection_mode="multi-row",
            key="table_locatif"
        )
        st.download_button("📥 Télécharger le listing Investisseurs (CSV)", data=st.session_state.df_locatif.to_csv(index=False).encode('utf-8'), file_name="listing_investissement_locatif.csv", mime='text/csv')

with tab2:
    st.subheader("✉️ Générateur de Courriers Investisseur & SCI - Cabinet Honorat")
    
    # Affichage du logo si présent dans le dossier du projet
    logo_path = "Cabinet Immobilier Privé HONORAT.png"
    if os.path.exists(logo_path):
        st.image(logo_path, width=300)
    else:
        st.markdown("### **CABINET PRIVÉ IMMOBILIER HONORAT**\n*TRANSACTION . CONSEIL . PATRIMOINE*")
    
    if 'df_locatif' in st.session_state and not st.session_state.df_locatif.empty and 'Adresse Exacte' in st.session_state.df_locatif.columns:
        liste_adresses_loc = st.session_state.df_locatif['Adresse Exacte'].dropna().unique().tolist()
        
        adresses_selectionnees = st.multiselect(
            "📍 Adresses sélectionnées pour la campagne investisseur :", 
            liste_adresses_loc, 
            default=liste_adresses_loc
        )
        
        if adresses_selectionnees:
            date_jour = datetime.now().strftime("%d/%m/%Y")
            
            if st.button("🖨️ Préparer l'impression groupée", type="primary"):
                st.success("📄 Courriers investisseurs prêts ! Utilisez `Ctrl + P` ou `Cmd + P` pour lancer l'impression.")

            st.markdown("---")
            
            for adresse in adresses_selectionnees:
                ligne_bien = st.session_state.df_locatif[st.session_state.df_locatif['Adresse Exacte'] == adresse].iloc[0]
                proprietaire = ligne_bien.get('Propriétaire / SCI', '')
                apt = ligne_bien.get('N° Apt', '')
                etage = ligne_bien.get('Étage', '')
                
                infos_repere = []
                if etage and str(etage).lower() != 'nan': infos_repere.append(f"Étage : {etage}")
                if apt and str(apt).lower() != 'nan': infos_repere.append(f"Apt {apt}")
                str_reperage = " | ".join(infos_repere) if infos_repere else "Actif identifié"

                # Gestion propre du destinataire
                if proprietaire and str(proprietaire).lower() != 'nan' and len(str(proprietaire).strip()) > 1:
                    destinataire_affichage = f"Destinataire : {proprietaire}"
                    appel_destinataire = f"À l'attention de {proprietaire},"
                else:
                    destinataire_affichage = f"Destinataire : Propriétaire / Investisseur\nLocalisation de l'actif : {str_reperage}"
                    appel_destinataire = f"Madame, Monsieur (Investisseur - {str_reperage}),"

                st.markdown(f"### 📍 {adresse}")
                st.markdown(f"**Ciblage de l'actif :** `{str_reperage}`")
                
                courrier_texte = f"""CABINET PRIVÉ IMMOBILIER HONORAT
TRANSACTION . CONSEIL . PATRIMOINE
Nice, le {date_jour}

{destinataire_affichage}
Adresse de l'actif : {adresse}

{appel_destinataire}

Objet : Anticipation fiscale, arbitrage et optimisation de votre actif au {adresse} ({str_reperage})

En qualité de Conseil en Immobilier Patrimonial pour le Cabinet Privé Immobilier Honorat à Nice, je me permets de vous contacter concernant l'actif que vous détenez. 

Dans le cadre des évolutions de la fiscalité immobilière (régime LMNP, fiscalité des SCI, loi de finances), l'anticipation de la gestion de votre portefeuille est essentielle pour sécuriser votre rentabilité nette et optimiser la transmission ou la revente de vos actifs.

Je me tiens à votre entière disposition pour réaliser un audit confidentiel de valorisation et vous accompagner dans vos projets d'arbitrage.

Bien cordialement,

Nathalie Parra
Conseil en Immobilier Patrimonial
Cabinet Privé Immobilier Honorat - Nice"""

                st.text_area(f"Modèle de courrier - {adresse}", courrier_texte, height=270, key=f"courrier_loc_{adresse}")
                st.markdown("---")
    else:
        st.info("👉 Générez d'abord le listing dans l'onglet 1.")

with tab3:
    st.subheader("🗺️ Analyse Spatiale : DVF & DPE (Carré d'Or)")
    if not df_dvf.empty:
        st.metric("Ventes DVF chargées", len(df_dvf))
        st.map(df_dvf[['lat', 'lon']].dropna())
    else:
        st.warning("En attente des données DVF dans le dossier data_dvf.")
