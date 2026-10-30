from datetime import datetime
import glob
import os
import pandas as pd
import requests
import xml.etree.ElementTree as ET
import streamlit as st
import pydeck as pdk
import re

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="Stratégie 3 - SCI & Retraite", page_icon="🏢", layout="wide"
)

st.title("🏢 Stratégie 3 : SCI, Arbitrage Retraite & Exonération Plus-Value")
st.markdown(
    "Ciblage des structures patrimoniales (SCI) avec filtres sur l'âge des gérants (Retraite / Transmission) "
    "et simulateur intégré d'abattement pour durée de détention."
)

# --- FONCTION DE NETTOYAGE DES NUMÉROS ---
def formater_numero(val):
    if pd.isna(val) or str(val).strip().lower() in ["nan", "none", "null", "", "<na>"]:
        return ""
    val_str = str(val).strip()
    if val_str.endswith(".0"):
        return val_str[:-2]
    return val_str

# --- CHARGEMENT OPTIMISÉ DES BASES (LAZY LOADING) ---
@st.cache_data
def load_dpe_sci():
    try:
        fichiers = sorted(glob.glob('dpe_nice_part_*.csv'))
        fichier_test = fichiers[0] if fichiers else 'dpe_nice_complet.csv'
        
        if os.path.exists(fichier_test):
            sample = pd.read_csv(fichier_test, nrows=0, low_memory=False)
            mots_cles = ['adresse', 'ban', 'brute', 'propriete', 'etage', 'niveau', 'appartement', 'porte', 'numero', 'lot', 'batiment', 'bat', 'surface', 'etiquette', 'dpe']
            cols_utiles = [c for c in sample.columns if any(m in c.lower() for m in mots_cles)]
        else:
            return pd.DataFrame()

        if fichiers:
            return pd.concat(
                [pd.read_csv(f, usecols=cols_utiles, low_memory=True) for f in fichiers],
                ignore_index=True,
            )
        return pd.read_csv('dpe_nice_complet.csv', usecols=cols_utiles, low_memory=True)
    except Exception:
        return pd.DataFrame()

@st.cache_data
def load_base_sci():
    fichiers_sci = glob.glob('*sci*.csv') + glob.glob('*sirene*.csv')
    if fichiers_sci:
        try:
            return pd.read_csv(fichiers_sci[0], sep=None, engine='python', low_memory=True)
        except Exception:
            return pd.DataFrame()
    return pd.DataFrame()

@st.cache_data
def load_dvf():
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
    except Exception: return pd.DataFrame()

df_dpe = load_dpe_sci()
df_sci = load_base_sci()

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
        elif annees_detention > 22 and annees_detention < 30:
            abattement_ps = 28 + ((annees_detention - 22) * 9)
        elif annees_detention >= 30:
            abattement_ps = 100

    return min(abattement_ir, 100), min(abattement_ps, 100)

# --- MOTEUR DE VEILLE JURIDIQUE EN TEMPS RÉEL ---
@st.cache_data(ttl=3600)
def fetch_veille_juridique():
    flux_officiels = [
        "https://www.service-public.fr/professionnels-entreprises/actualites/rss",
        "https://www.service-public.fr/particuliers/actualites/rss",
    ]
    articles_trouves = []
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

    for url in flux_officiels:
        try:
            reponse = requests.get(url, headers=headers, timeout=5)
            if reponse.status_code == 200:
                root = ET.fromstring(reponse.content)
                for item in root.findall(".//item"):
                    titre = item.find("title").text if item.find("title") is not None else ""
                    lien = item.find("link").text if item.find("link") is not None else ""
                    mots_cles_immo = ["sci", "société civile", "fiscalité", "plus-value", "succession", "donation", "transmission", "démembrement", "usufruit"]
                    if any(mot in titre.lower() for mot in mots_cles_immo):
                        articles_trouves.append({"titre": titre, "lien": lien})
        except:
            pass

    articles_uniques = []
    liens_vus = set()
    for art in articles_trouves:
        if art["lien"] not in liens_vus:
            articles_uniques.append(art)
            liens_vus.add(art["lien"])

    return articles_uniques[:6]

alertes_en_direct = fetch_veille_juridique()

# --- BARRE LATÉRALE DE RECHERCHE ---
st.sidebar.header('🎯 Ciblage SCI & Transmission')

filtre_age_gerant = st.sidebar.selectbox(
    "Filtre Âge du Gérant (SIRENE)",
    [
        "Tous les âges",
        "Gérant > 62 ans (Arbitrage Retraite)",
        "Gérant > 75 ans (Anticipation Succession / Démembrement)"
    ]
)

secteur_sci = st.sidebar.selectbox(
    'Quartier / Secteur',
    [
        "Tous les secteurs",
        "Carré d'Or",
        'Promenade des Anglais',
        'Musiciens / Gambetta',
        'Port / Garibaldi',
        'Mont Boron',
        'Centre-ville',
    ],
)

# --- AFFICHAGE DES ONGLETS ---
tab1, tab2, tab3 = st.tabs([
    "✉️ 1. Portefeuilles SCI & Simulateur Plus-Value",
    "💶 2. Carte des Ventes DVF",
    "🚨 3. Veille Fiscale Patrimoniale",
])

with tab1:
    st.subheader("Ciblage Patrimonial & Calculateur de Plus-Value Nette")

    if not df_dpe.empty:
        colonnes_a_garder = {}
        for col in ["adresse_ban", "adresse_brute", "adresse_propriete"]:
            if col in df_dpe.columns:
                colonnes_a_garder[col] = "Adresse Exacte"
                break

        cibles = {"Étage": False, "N° Apt": False, "N° Lot": False, "Bâtiment": False, "Note DPE": False, "Surface m²": False}

        for col in df_dpe.columns:
            c = col.lower()
            if not cibles["Étage"] and ("etage" in c or "niveau" in c):
                colonnes_a_garder[col] = "Étage"
                cibles["Étage"] = True
            elif not cibles["N° Apt"] and ("appartement" in c or "porte" in c or "numero_appt" in c):
                colonnes_a_garder[col] = "N° Apt"
                cibles["N° Apt"] = True
            elif not cibles["N° Lot"] and "lot" in c and "surface" not in c:
                colonnes_a_garder[col] = "N° Lot"
                cibles["N° Lot"] = True
            elif not cibles["Bâtiment"] and ("batiment" in c or "bat" in c):
                colonnes_a_garder[col] = "Bâtiment"
                cibles["Bâtiment"] = True
            elif not cibles["Note DPE"] and "etiquette" in c and "dpe" in c:
                colonnes_a_garder[col] = "Note DPE"
                cibles["Note DPE"] = True
            elif not cibles["Surface m²"] and ("surface" in c):
                colonnes_a_garder[col] = "Surface m²"
                cibles["Surface m²"] = True

        df_affichage = df_dpe[list(colonnes_a_garder.keys())].rename(columns=colonnes_a_garder)

        if 'Adresse Exacte' in df_affichage.columns:
            df_affichage = df_affichage[
                df_affichage['Adresse Exacte']
                .astype(str)
                .str.lower()
                .str.contains(r'nice|06\d{3}', regex=True, na=False)
            ]

        rues_quartiers = {
            "Carré d'Or": ['france', 'massena', 'paradis', 'suede', 'verdun', 'meyerbeer', 'congres', 'cronstadt', 'buffa', 'alphonse karr', 'maccarani', 'liberte', 'longchamp', 'grimaldi', 'dalpozzo', 'halevy', 'marechal joffre', 'rivoli'],
            'Promenade des Anglais': ['promenade des anglais', 'etats-unis', 'quai des etats-unis'],
            'Port / Garibaldi': ['garibaldi', 'lunel', 'cassini', 'barla', 'arson', 'republique', 'port', 'segurane', 'fodere'],
            'Mont Boron': ['mont boron', 'jean lorrain', 'carnot', 'germaine', 'andre joly', 'valrose', 'cap de nice', 'maeterlinck'],
            'Musiciens / Gambetta': ['gambetta', 'berlioz', 'gounod', 'rossini', 'verdi', 'clemenceau', 'victor hugo', 'mozart', ' paganini', 'thiers'],
            'Centre-ville': ['jean medecin', 'gioffredo', 'marechal foch', 'pastorelli', 'assalit', 'durandy', 'hotel des postes', 'dubouchage'],
        }

        if secteur_sci != 'Tous les secteurs':
            mots_cles = rues_quartiers.get(secteur_sci, [])
            if 'Adresse Exacte' in df_affichage.columns and mots_cles:
                pattern = '|'.join([fr'\b{re.escape(mot)}\b' for mot in mots_cles])
                df_affichage = df_affichage[
                    df_affichage['Adresse Exacte']
                    .astype(str)
                    .str.lower()
                    .str.contains(pattern, na=False, regex=True)
                ]

        if "Adresse Exacte" in df_affichage.columns and not df_affichage.empty:

            def creer_libelle_bien(row):
                adresse = str(row.get("Adresse Exacte", "")).title()
                bat = formater_numero(row.get("Bâtiment", ""))
                etage = formater_numero(row.get("Étage", ""))
                apt = formater_numero(row.get("N° Apt", ""))
                surf = formater_numero(row.get("Surface m²", ""))

                details = []
                if bat: details.append(f"Bât. {bat}")
                if etage: details.append(f"Étage {etage}")
                if apt: details.append(f"Apt {apt}")
                if surf: details.append(f"{surf} m²")

                str_details = " | ".join(details) if details else "Lot"
                return f"{adresse} — [{str_details}]"

            df_affichage["Libellé Complet"] = df_affichage.apply(creer_libelle_bien, axis=1)
            biens_dispos = df_affichage["Libellé Complet"].dropna().unique().tolist()[:1000]
            biens_dispos.sort()

            bien_choisi = st.selectbox(
                "📍 Sélectionner l'actif SCI à expertiser :", biens_dispos
            )

            if bien_choisi:
                ligne_bien = df_affichage[df_affichage["Libellé Complet"] == bien_choisi].iloc[0]
                adresse_brute = str(ligne_bien.get("Adresse Exacte", "")).title()
                
                st.markdown("---")
                st.markdown("### 🧮 Simulateur Rapide d'Exonération (Plus-Value Immobilière)")
                
                col_sim1, col_sim2 = st.columns(2)
                with col_sim1:
                    annee_acquisition = st.number_input("Année d'acquisition du bien (Estimée)", min_value=1950, max_value=datetime.now().year, value=2010)
                
                annees_detention = datetime.now().year - annee_acquisition
                abat_ir, abat_ps = calcul_abattement_plus_value(annees_detention)
                
                with col_sim2:
                    st.metric("Durée de détention", f"{annees_detention} ans")
                
                st.info(f"**Abattements acquis à ce jour :** Exonération Impôt sur le Revenu : **{abat_ir:,.1f}%** | Exonération Prélèvements Sociaux : **{abat_ps:,.1f}%**")
                
                if annees_detention >= 30:
                    st.success("🏆 **Exonération totale atteinte.** La SCI peut céder cet actif en franchise totale d'impôt sur la plus-value.")
                elif annees_detention >= 22:
                    st.warning("⚠️ **Exonération IR totale atteinte (19%), mais Prélèvements Sociaux (17.2%) toujours dus.**")

                date_jour = datetime.now().strftime("%d/%m/%Y")
                
                if "> 75 ans" in filtre_age_gerant:
                    objet_courrier = f"Stratégie de transmission, démembrement et optimisation de votre actif au {adresse_brute}"
                    paragraphe_cible = (
                        "L'anticipation de la transmission du patrimoine immobilier détenu en SCI est une étape cruciale pour "
                        "protéger vos héritiers des lourds droits de succession.\n\n"
                        "Au regard de la localisation de votre actif et des abattements légaux de transmission qui se renouvellent "
                        "tous les 15 ans, une stratégie de donation de parts sociales avec réserve d'usufruit ou un arbitrage "
                        "vers des supports plus liquides pourrait s'avérer extrêmement pertinente aujourd'hui."
                    )
                elif "> 62 ans" in filtre_age_gerant:
                    objet_courrier = f"Cristallisation de vos plus-values et préparation à la retraite — Actif au {adresse_brute}"
                    paragraphe_cible = (
                        f"Après {annees_detention} années de détention, votre actif bénéficie désormais d'un abattement "
                        f"significatif sur la plus-value immobilière ({abat_ir}% sur l'IR et {abat_ps}% sur les prélèvements sociaux).\n\n"
                        "À l'approche ou au moment de la retraite, la gestion locative devient souvent chronophage et la "
                        "rentabilité nette s'érode face aux nouvelles réglementations. C'est le moment idéal pour envisager "
                        "de cristalliser cette plus-value exonérée et de restructurer votre patrimoine vers des revenus garantis."
                    )
                else:
                    objet_courrier = f"Valorisation de vos parts sociales et arbitrage de votre actif au {adresse_brute}"
                    paragraphe_cible = (
                        "Le marché immobilier du secteur traverse une phase de normalisation. Pour les Sociétés Civiles Immobilières, "
                        "l'arbitrage d'actifs vieillissants ou fortement fiscalisés est aujourd'hui une priorité de gestion.\n\n"
                        "Nous réalisons pour nos clients des audits précis de leurs portefeuilles "
                        "afin d'identifier les actifs ayant atteint leur maturité financière."
                    )

                courrier_sci = f"""Nice, le {date_jour}

À l'attention de la Gérance
SCI propriétaire du lot situé au {adresse_brute}

Madame, Monsieur le Gérant,

Objet : {objet_courrier}

En ma qualité de professionnel de l'immobilier au sein du Cabinet Privé Immobilier Honorat, j'accompagne les dirigeants de sociétés civiles dans l'optimisation et la restructuration de leur parc immobilier niçois.

{paragraphe_cible}

Je me tiens à votre entière disposition pour vous remettre, en toute confidentialité, un audit de ce bien. Cette étude inclura un chiffrage de sa valeur vénale actuelle ainsi qu'une simulation précise de la plus-value nette d'impôt en cas de cession.

Dans l'attente de nos échanges, je vous prie d'agréer, Madame, Monsieur le Gérant, l'expression de mes salutations distinguées.

Nathalie Parra

CABINET PRIVÉ IMMOBILIER HONORAT
AUDIT . TRANSACTION . CONSEIL

---
*Nathalie Parra — Titulaire de la carte professionnelle CPI délivrée par la CCI Nice Côte d'Azur*
*Membre de la FNAIM*"""

                st.markdown("---")
                st.text_area(
                    "📄 Modèle de Lettre Gérant SCI :",
                    value=courrier_sci,
                    height=450,
                )
                
                logo_path = "Cabinet Immobilier Privé HONORAT.png"
                if os.path.exists(logo_path):
                    st.image(logo_path, width=200)

        else:
            st.info("⚠️ Aucun lot trouvé pour ces critères.")
    else:
        st.warning("⚠️ Base de données introuvable ou vide.")

with tab2:
    st.subheader('💶 Chargement des Valeurs Foncières (DVF)')
    st.write("Visualisez les transactions récentes pour estimer le prix de cession de la SCI.")
    
    if st.button("🗺️ Charger la carte des ventes DVF"):
        with st.spinner("Chargement sécurisé des données..."):
            df_dvf = load_dvf()
            
        if not df_dvf.empty:
            def construire_adresse(row):
                cols = row.index.tolist()
                num = str(row['adresse_numero']).replace('.0', '') if 'adresse_numero' in cols and pd.notna(row['adresse_numero']) else ''
                voie = str(row['adresse_nom_voie']) if 'adresse_nom_voie' in cols and pd.notna(row['adresse_nom_voie']) else ''
                adresse = f'{num} {voie}'.strip().title()
                return adresse if adresse else 'Adresse inconnue'

            df_dvf['Adresse Vente'] = df_dvf.apply(construire_adresse, axis=1)
            cols_propre = [c for c in ['date_mutation', 'Adresse Vente', 'type_local', 'nom_commune', 'valeur_fonciere', 'surface_reelle_bati', 'prix_m2', 'lat', 'lon'] if c in df_dvf.columns]
            
            if cols_propre:
                df_dvf_propre = df_dvf[cols_propre].copy()
                df_dvf_propre['Prix de Vente'] = df_dvf_propre['valeur_fonciere'].apply(lambda x: f'{x:,.0f} €'.replace(',', ' ') if pd.notna(x) else '')
                df_dvf_propre['Surface'] = df_dvf_propre['surface_reelle_bati'].apply(lambda x: f'{x:,.0f} m²' if pd.notna(x) else '')
                df_dvf_propre['Prix / m²'] = df_dvf_propre['prix_m2'].apply(lambda x: f'{x:,.0f} €/m²'.replace(',', ' ') if pd.notna(x) else '')

                if 'lat' in df_dvf_propre.columns and 'lon' in df_dvf_propre.columns:
                    df_map = df_dvf_propre.dropna(subset=['lat', 'lon']).copy()
                    if not df_map.empty:
                        layer = pdk.Layer(
                            'ScatterplotLayer', data=df_map, get_position='[lon, lat]',
                            get_radius=20, get_fill_color='[200, 30, 0, 160]', pickable=True, auto_highlight=True,
                        )
                        view_state = pdk.ViewState(latitude=df_map['lat'].mean(), longitude=df_map['lon'].mean(), zoom=13, pitch=0)
                        tooltip = {'html': '<b>{Adresse Vente}</b><br/>Prix : {Prix de Vente}<br/>Surface : {Surface}<br/><b>Ratio : {Prix / m²}</b>', 'style': {'backgroundColor': 'steelblue', 'color': 'white'}}
                        st.pydeck_chart(pdk.Deck(layers=[layer], initial_view_state=view_state, tooltip=tooltip))

                st.dataframe(df_dvf_propre[['date_mutation', 'Adresse Vente', 'type_local', 'Prix de Vente', 'Surface', 'Prix / m²']].head(100), use_container_width=True, hide_index=True)
        else:
            st.warning("⚠️ Données DVF introuvables.")

with tab3:
    st.subheader("🚨 Veille Juridique (Succession, Donation & SCI)")
    if alertes_en_direct:
        for art in alertes_en_direct:
            st.markdown(f"- **[{art['titre']}]({art['lien']})**")
    else:
        st.info("Aucune alerte récente sur les flux officiels liée aux SCI ou à la transmission.")
