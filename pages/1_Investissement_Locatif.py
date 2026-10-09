import streamlit as st
import pandas as pd
from datetime import datetime
import folium
from streamlit_folium import st_folium

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

# --- CHARGEMENT DES DONNÉES DVF (Mise en cache) ---
@st.cache_data
def load_dvf():
    url_dvf = "https://files.data.gouv.fr/geo-dvf/latest/csv/2023/departements/06.csv.gz"
    df = pd.read_csv(url_dvf, compression='gzip', low_memory=False)
    
    # Renommer les colonnes géographiques pour la compatibilité
    if 'latitude' in df.columns and 'longitude' in df.columns:
        df = df.rename(columns={'latitude': 'lat', 'longitude': 'lon'})
        
    df_nice = df[df['code_commune'] == '06088'].dropna(subset=['valeur_fonciere', 'surface_reelle_bati', 'lat', 'lon']).copy()
    df_nice['prix_m2'] = df_nice['valeur_fonciere'] / df_nice['surface_reelle_bati']
    return df_nice[(df_nice['prix_m2'] > 1000) & (df_nice['prix_m2'] < 25000)]


def filter_carre_dor(df, lat_col='lat', lon_col='lon'):
    # Boîte de délimitation pour le Carré d'Or / Promenade
    lat_min, lat_max = 43.6930, 43.6995
    lon_min, lon_max = 7.2560, 7.2670
    
    if lat_col in df.columns and lon_col in df.columns:
        mask = (df[lat_col] >= lat_min) & (df[lat_col] <= lat_max) & \
               (df[lon_col] >= lon_min) & (df[lon_col] <= lon_max)
        return df[mask]
    return pd.DataFrame()

# Chargement DVF
try:
    df_dvf = load_dvf()
except Exception as e:
    df_dvf = pd.DataFrame()
    st.error(f"Erreur lors du chargement DVF : {e}")

# Chargement DPE
try:
    df_global = pd.read_csv('dpe_nice_fg.csv')
except Exception as e:
    df_global = pd.DataFrame()
    st.error(f"Erreur critique lors du chargement des données DPE : {e}")

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
        
        # Filtrage ciblé sur les structures sociétaires (SCI, SARL, etc.)
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

        # Filtrage pour ne garder idéalement que les entités ou profils investisseurs
        if 'Propriétaire / SCI' in df_affichage.columns:
            mask_sci = df_affichage['Propriétaire / SCI'].astype(str).str.upper().str.contains("SCI|SARL|SAS|HOLDING|IMMOBILIERE", na=False)
            if mask_sci.sum() > 0:
                df_affichage = df_affichage[mask_sci] 

        # Découpage du lot
        idx_deb = (int(tranche_lot_loc.split()[1]) - 1) * 50
        st.session_state.df_locatif = df_affichage.iloc[idx_deb:idx_deb + 50]
        st.session_state.analyse_locative_terminee = True


# --- AFFICHAGE PRINCIPAL EN 3 ONGLETS ---
if st.session_state.analyse_locative_terminee:
    
    # AJOUT D'UN TROISIÈME ONGLET POUR LA CARTE
    tab1, tab2, tab3 = st.tabs([
        "📊 1. Listing Investisseurs & SCI", 
        "✉️ 2. Publipostage & Impression",
        "🗺️ 3. Cartographie DVF & DPE (Carré d'Or)"
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
                    
    with tab3:
        st.header("🗺️ Analyse Spatiale : DVF & DPE (Carré d'Or)")
        st.write("Visualisez instantanément les passoires thermiques et les dernières ventes immobilières pour repérer les meilleures opportunités de déficit foncier.")
        
        if not df_dvf.empty and not df_global.empty:
            # Filtrage sur le Carré d'Or
            dvf_carre_dor = filter_carre_dor(df_dvf)
            dpe_carre_dor = filter_carre_dor(df_global)
            
            # Affichage des métriques clés
            col1, col2 = st.columns(2)
            col1.metric("Ventes DVF (Carré d'Or)", len(dvf_carre_dor))
            col2.metric("Passoires thermiques (F/G)", len(dpe_carre_dor))
            
            # Création de la carte
            m = folium.Map(location=[43.696, 7.262], zoom_start=15, tiles="CartoDB positron")
            
            layer_dvf = folium.FeatureGroup(name="Ventes DVF (Points Bleus)")
            layer_dpe = folium.FeatureGroup(name="DPE F & G (Points Rouges)")
            
            # Intégration des points DVF
            for idx, row in dvf_carre_dor.iterrows():
                popup_text = f"<b>{row.get('type_local', 'Bien')}</b><br>Prix: {row['valeur_fonciere']:,.0f} €<br>Prix/m²: {row['prix_m2']:,.0f} €"
                folium.CircleMarker(
                    location=[row['lat'], row['lon']], radius=5, color='blue',
                    fill=True, popup=folium.Popup(popup_text, max_width=200)
                ).add_to(layer_dvf)
                
            # Intégration des points DPE
            for idx, row in dpe_carre_dor.iterrows():
                etiquette = row.get('etiquette_dpe', 'F/G')
                popup_text = f"<b>Passoire Thermique</b><br>Étiquette: {etiquette}"
                folium.CircleMarker(
                    location=[row['lat'], row['lon']], radius=4, color='red',
                    fill=True, popup=folium.Popup(popup_text, max_width=200)
                ).add_to(layer_dpe)
                
            layer_dvf.add_to(m)
            layer_dpe.add_to(m)
            folium.LayerControl().add_to(m)
            
            # Affichage dans l'application
            st_folium(m, width=900, height=500)
        else:
            st.warning("En attente du chargement complet des bases DVF et DPE.")
            
else:
    st.info("👉 Sélectionnez vos critères dans la barre latérale, puis cliquez sur **'Générer le listing Investisseurs / SCI'**.")
