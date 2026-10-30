from datetime import datetime
import os
import pandas as pd
import streamlit as st
import pydeck as pdk

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="Audit & Avis de Valeur - Cabinet Honorat", page_icon="📝", layout="wide"
)

st.title("📝 Audit & Avis de Valeur")
st.markdown(
    "Génération d'une synthèse financière et immobilière pour le client. "
    "Calcul de plus-value, analyse de l'environnement réglementaire et comparables de marché."
)

# --- MOTEUR DE CALCUL DES PLUS-VALUES IMMOBILIÈRES ---
def calcul_abattement_plus_value(annees_detention):
    abattement_ir = 0
    abattement_ps = 0
    
    if annees_detention > 5:
        if annees_detention <= 21:
            abattement_ir = (annees_detention - 5) * 6
        elif annees_detention >= 22:
            abattement_ir = 100
            
        if annees_detention <= 21:
            abattement_ps = (annees_detention - 5) * 1.65
        elif annees_detention == 22:
            abattement_ps = 28
        elif 22 < annees_detention < 30:
            abattement_ps = 28 + ((annees_detention - 22) * 9)
        elif annees_detention >= 30:
            abattement_ps = 100

    return min(abattement_ir, 100), min(abattement_ps, 100)

# --- CHARGEMENT OPTIMISÉ DVF (LAZY LOADING) ---
@st.cache_data
def load_dvf_audit():
    try:
        dossier = next((item for item in os.listdir('.') if os.path.isdir(item) and 'dvf' in item.lower()), None)
        if not dossier: return pd.DataFrame()
        fichiers = [os.path.join(dossier, f) for f in os.listdir(dossier) if f.endswith('.csv') or f.endswith('.txt')]
        if not fichiers: return pd.DataFrame()
        
        liste_df = []
        colonnes_utiles = ['date_mutation', 'nature_mutation', 'valeur_fonciere', 'adresse_numero', 'No voie', 'adresse_nom_voie', 'Voie', 'Type de voie', 'nom_commune', 'type_local', 'surface_reelle_bati', 'latitude', 'lat', 'longitude', 'lon']
        
        for f in fichiers:
            try:
                sample = pd.read_csv(f, sep=';', nrows=0)
                sep = ',' if len(sample.columns) < 3 else ';'
                cols_a_charger = [c for c in colonnes_utiles if c in sample.columns]
                if cols_a_charger:
                    liste_df.append(pd.read_csv(f, sep=sep, usecols=cols_a_charger, low_memory=True))
            except Exception: pass
            
        if not liste_df: return pd.DataFrame()
        df = pd.concat(liste_df, ignore_index=True).drop_duplicates()
        if 'latitude' in df.columns: df = df.rename(columns={'latitude': 'lat', 'longitude': 'lon'})
        if all(c in df.columns for c in ['valeur_fonciere', 'surface_reelle_bati', 'lat']):
            df = df.dropna(subset=['valeur_fonciere', 'surface_reelle_bati', 'lat', 'lon']).copy()
            df['valeur_fonciere'] = pd.to_numeric(df['valeur_fonciere'].astype(str).str.replace(',', '.'), errors='coerce')
            df['surface_reelle_bati'] = pd.to_numeric(df['surface_reelle_bati'].astype(str).str.replace(',', '.'), errors='coerce')
            df = df[df['surface_reelle_bati'] > 0]
            df['prix_m2'] = df['valeur_fonciere'] / df['surface_reelle_bati']
            df = df[(df['prix_m2'] > 1000) & (df['prix_m2'] < 25000)]
        return df
    except Exception: 
        return pd.DataFrame()

# --- INTERFACE DE SAISIE DE L'AUDIT ---
with st.form("form_audit_patrimonial"):
    st.subheader("1. Informations du Propriétaire & de l'Actif")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        nom_client = st.text_input("Nom du ou des propriétaires / SCI")
        adresse_bien = st.text_input("Adresse exacte du bien (Nice)")
        type_bien = st.selectbox("Type de bien", ["Appartement", "Maison / Villa", "Local Commercial", "Immeuble"])
        
    with col2:
        surface_bien = st.number_input("Surface habitable / Loi Carrez (m²)", min_value=9.0, max_value=500.0, value=50.0, step=1.0)
        note_dpe = st.selectbox("Note DPE actuelle", ["A", "B", "C", "D", "E", "F", "G", "Non Soumis / Vierge"])
        statut_occupation = st.selectbox("Statut d'occupation", ["Libre de toute occupation", "Loué (Bail Nu)", "Loué (Bail Meublé)", "Location Saisonnière (Airbnb)"])

    with col3:
        annee_acquisition = st.number_input("Année d'acquisition", min_value=1950, max_value=datetime.now().year, value=2015, step=1)
        prix_acquisition = st.number_input("Prix d'acquisition estimé (€ hors frais)", min_value=10000, value=150000, step=5000)
        estimation_actuelle = st.number_input("Estimation vénale actuelle (Valeur marché €)", min_value=10000, value=250000, step=5000)

    st.markdown("---")
    st.subheader("2. Paramètres de la Copropriété & Urbanisme")
    col_copro1, col_copro2 = st.columns(2)
    
    with col_copro1:
        travaux_copro = st.radio("Appels de fonds importants à prévoir (RNIC / AG) ?", ["Non, copropriété saine", "Oui, ravalement ou toiture", "Oui, rénovation énergétique globale"])
    with col_copro2:
        zone_airbnb = st.checkbox("Bien situé en Zone 3 (Hypercentre Nice - Quotas Airbnb stricts)", value=True)
        
    submit_audit = st.form_submit_button("📊 Générer le Rapport d'Audit & Avis de Valeur")

# --- TRAITEMENT ET GÉNÉRATION DU RAPPORT ---
if submit_audit:
    st.markdown("---")
    
    # 1. Calculs Financiers
    annees_detention = datetime.now().year - annee_acquisition
    plus_value_brute = estimation_actuelle - prix_acquisition
    abat_ir, abat_ps = calcul_abattement_plus_value(annees_detention)
    
    montant_ir = max(0, plus_value_brute * (1 - (abat_ir / 100)) * 0.19)
    montant_ps = max(0, plus_value_brute * (1 - (abat_ps / 100)) * 0.172)
    impot_total = montant_ir + montant_ps
    capital_net_vendeur = estimation_actuelle - impot_total

    # 2. Mise en page du Rapport
    col_logo, col_titre = st.columns([1, 4])
    with col_logo:
        logo_path = "Cabinet Immobilier Privé HONORAT.png"
        if os.path.exists(logo_path):
            st.image(logo_path, use_container_width=True)
    with col_titre:
        st.markdown(f"## RAPPORT D'AUDIT & AVIS DE VALEUR")
        st.markdown(f"**Dossier :** {nom_client if nom_client else 'Confidentiel'} | **Date :** {datetime.now().strftime('%d/%m/%Y')}")
        st.markdown(f"**Actif expertisé :** {type_bien} de {surface_bien} m² situé au {adresse_bien}")

    st.markdown("### 💶 Synthèse Financière & Fiscale (Simulation de Cession)")
    
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("Valeur Vénale Estimée", f"{estimation_actuelle:,.0f} €".replace(',', ' '))
    kpi2.metric("Plus-Value Brute", f"{plus_value_brute:,.0f} €".replace(',', ' '))
    kpi3.metric("Impôt Plus-Value (IR + PS)", f"{impot_total:,.0f} €".replace(',', ' '))
    kpi4.metric("💰 CAPITAL NET REVENANT", f"{capital_net_vendeur:,.0f} €".replace(',', ' '))

    st.info(f"💡 **Note fiscale :** Le bien est détenu depuis {annees_detention} ans. Il bénéficie d'un abattement de **{abat_ir:,.1f}%** sur l'Impôt sur le Revenu et de **{abat_ps:,.1f}%** sur les Prélèvements Sociaux.")

    st.markdown("### 🏛️ Analyse Environnementale & Réglementaire")
    
    alerte_dpe = ""
    if note_dpe in ["F", "G"]:
        alerte_dpe = "🔴 **Vigilance DPE :** Actif classé en passoire thermique. Interdiction de location imminente selon la loi Climat et Résilience. Une décote de marché est à anticiper en cas de non-réalisation des travaux."
    elif note_dpe == "E":
        alerte_dpe = "🟠 **Vigilance DPE :** Actif classé E. La réglementation imposera une mise aux normes à moyen terme pour poursuivre l'exploitation locative."
    else:
        alerte_dpe = f"🟢 **DPE Conforme :** Actif classé {note_dpe}. Le bien répond aux standards énergétiques actuels, sécurisant sa valeur de revente."
        
    alerte_copro = ""
    if "Oui" in travaux_copro:
        alerte_copro = f"⚠️ **Copropriété :** Des appels de fonds importants sont à prévoir ({travaux_copro.split(', ')[1]}). L'arbitrage actuel permet d'éviter l'immobilisation de trésorerie."
    else:
        alerte_copro = "✅ **Copropriété :** Immeuble sain, aucun frein financier majeur identifié sur les parties communes."

    alerte_airbnb = ""
    if zone_airbnb and statut_occupation == "Location Saisonnière (Airbnb)":
        alerte_airbnb = "⚠️ **Réglementation Saisonnière :** Bien situé en Zone 3 hypercentre. Le maintien de l'activité est conditionné par des quotas stricts et l'obligation d'un DPE classé A à E."

    st.markdown(f"- {alerte_dpe}")
    st.markdown(f"- {alerte_copro}")
    if alerte_airbnb:
        st.markdown(f"- {alerte_airbnb}")

    st.markdown("---")
    st.markdown("### 📋 Conclusion & Préconisations du Cabinet Honorat")
    
    if note_dpe in ["F", "G"] or "Oui" in travaux_copro:
        st.warning(
            "Au regard des contraintes pesant sur cet actif (réglementation énergétique, coûts de copropriété), "
            "la rentabilité nette future est fortement menacée. **Nous préconisons un arbitrage de ce lot** "
            "afin de sécuriser votre capital net vendeur avant que les obligations légales n'impactent sa valeur vénale."
        )
    elif annees_detention >= 22:
        st.success(
            "L'actif a atteint une excellente maturité fiscale avec une exonération totale au titre de l'Impôt sur le Revenu. "
            "Les conditions de marché actuelles sont propices pour **cristalliser cette plus-value** et envisager un "
            "remploi des fonds vers des supports diversifiés."
        )
    else:
        st.info(
            "L'actif présente des fondamentaux sains. Une mise en vente peut s'envisager dans d'excellentes conditions "
            "pour réorienter votre stratégie, avec un positionnement prix optimisé pour les acquéreurs."
        )
        
    signature_cabinet = (
        "<br><p style='text-align: right;'><em>Document généré par Nathalie Parra</em><br>"
        "<strong>CABINET PRIVÉ IMMOBILIER HONORAT</strong><br>"
        "AUDIT . TRANSACTION . CONSEIL<br><br>"
        "---<br>"
        "<em>Nathalie Parra — Titulaire de la carte professionnelle CPI délivrée par la CCI Nice Côte d'Azur</em><br>"
        "<em>Membre de la FNAIM</em></p>"
    )
    st.markdown(signature_cabinet, unsafe_allow_html=True)

# --- MODULE INDÉPENDANT : COMPARABLES DE MARCHÉ DVF ---
st.markdown("---")
st.subheader("📍 Étude des Transactions Récentes (Base DVF)")
st.write("Appuyez sur ce bouton pour interroger la base des ventes immobilières et justifier l'estimation auprès du client.")

if st.button("🗺️ Charger et analyser le marché local (DVF)"):
    with st.spinner("Recherche des transactions foncières sécurisées..."):
        df_dvf = load_dvf_audit()
        
        if not df_dvf.empty:
            def construire_adresse(row):
                cols = row.index.tolist()
                num = str(row['adresse_numero']).replace('.0', '') if 'adresse_numero' in cols and pd.notna(row['adresse_numero']) else ''
                voie = str(row['adresse_nom_voie']) if 'adresse_nom_voie' in cols and pd.notna(row['adresse_nom_voie']) else ''
                adresse = f'{num} {voie}'.strip().title()
                return adresse if adresse else 'Adresse inconnue'

            df_dvf['Adresse Vente'] = df_dvf.apply(construire_adresse, axis=1)
            
            colonnes_dvf = ['date_mutation', 'Adresse Vente', 'type_local', 'nom_commune', 'valeur_fonciere', 'surface_reelle_bati', 'prix_m2', 'lat', 'lon']
            cols_propre = [c for c in colonnes_dvf if c in df_dvf.columns]
            
            if cols_propre:
                df_dvf_propre = df_dvf[cols_propre].copy()
                df_dvf_propre['Prix de Vente'] = df_dvf_propre['valeur_fonciere'].apply(lambda x: f'{x:,.0f} €'.replace(',', ' ') if pd.notna(x) else '')
                df_dvf_propre['Surface'] = df_dvf_propre['surface_reelle_bati'].apply(lambda x: f'{x:,.0f} m²' if pd.notna(x) else '')
                df_dvf_propre['Prix / m²'] = df_dvf_propre['prix_m2'].apply(lambda x: f'{x:,.0f} €/m²'.replace(',', ' ') if pd.notna(x) else '')

                st.markdown("#### Cartographie des comparables")
                if 'lat' in df_dvf_propre.columns and 'lon' in df_dvf_propre.columns:
                    df_map = df_dvf_propre.dropna(subset=['lat', 'lon']).copy()
                    if not df_map.empty:
                        layer = pdk.Layer(
                            'ScatterplotLayer', data=df_map, get_position='[lon, lat]',
                            get_radius=25, get_fill_color='[0, 100, 200, 160]', pickable=True, auto_highlight=True,
                        )
                        view_state = pdk.ViewState(latitude=df_map['lat'].mean(), longitude=df_map['lon'].mean(), zoom=13, pitch=0)
                        tooltip = {'html': '<b>{Adresse Vente}</b><br/>Prix : {Prix de Vente}<br/>Surface : {Surface}<br/><b>Ratio : {Prix / m²}</b>', 'style': {'backgroundColor': '#333', 'color': 'white'}}
                        st.pydeck_chart(pdk.Deck(layers=[layer], initial_view_state=view_state, tooltip=tooltip))

                st.markdown("#### Dernières transactions enregistrées")
                st.dataframe(df_dvf_propre[['date_mutation', 'Adresse Vente', 'type_local', 'Prix de Vente', 'Surface', 'Prix / m²']].head(100), use_container_width=True, hide_index=True)
        else:
            st.warning("⚠️ Les données DVF n’ont pas pu être chargées.")
