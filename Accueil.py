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
st.markdown("Base de données certifiée : passoires énergétiques, détection des mandats mûrs et courriers ciblés.")

# --- INITIALISATION DE LA MÉMOIRE (SESSION STATE) ---
# Permet de ne pas perdre les données quand on navigue dans les onglets
if 'df_affichage' not in st.session_state:
    st.session_state.df_affichage = pd.DataFrame()
if 'analyse_terminee' not in st.session_state:
    st.session_state.analyse_terminee = False

# Chargement du fichier CSV
try:
    df_global = pd.read_csv('dpe_nice_fg.csv')
except Exception as e:
    df_global = pd.DataFrame()
    st.error(f"Erreur critique lors du chargement du fichier CSV : {e}")

# --- BARRE LATÉRALE DE RECHERCHE ---
st.sidebar.header("🎯 Critères de ciblage")

objectif = st.sidebar.selectbox(
    "Objectif de prospection",
    [
        "Passoires Énergétiques (F & G) - Standard",
        "Campagne de Boîtage Ciblé"
    ]
)

secteur = st.sidebar.selectbox(
    "Quartier / Secteur à Nice",
    [
        "Tous les secteurs",
        "Carré d'Or",
        "Promenade des Anglais",
        "Port / Garibaldi",
        "Mont Boron",
        "Musiciens / Gambetta",
        "Centre-ville"
    ]
)

# Gestion automatique du mois / lot
mois_actuel = datetime.now().month
if mois_actuel <= 10:
    lot_auto_index = 0
elif mois_actuel == 11:
    lot_auto_index = 1
elif mois_actuel == 12:
    lot_auto_index = 2
else:
    lot_auto_index = 3

liste_lots = [
    "Lot 1 (1 - 50)",
    "Lot 2 (51 - 100)",
    "Lot 3 (101 - 150)",
    "Lot 4 (151 - 200)",
    "Lot 5 (201 - 250)"
]

mode_manuel = st.sidebar.checkbox("🔧 Activer le choix manuel du lot", value=False)
if mode_manuel:
    tranche_mois = st.sidebar.selectbox("Choisir le lot manuellement", liste_lots)
else:
    tranche_mois = liste_lots[min(lot_auto_index, len(liste_lots) - 1)]
    st.sidebar.info(f"📅 Lot attribué (Mois en cours) : **{tranche_mois}**")

# Bouton de lancement
if st.sidebar.button("Générer le listing certifié", type="primary"):
    if df_global.empty:
        st.error("⚠ Le fichier `dpe_nice_fg.csv` est introuvable à la racine du dépôt GitHub.")
    else:
        df_resultats = df_global.copy()
        
        # Renommage des colonnes
        colonnes_utiles = {}
        if 'adresse_ban' in df_resultats.columns:
            colonnes_utiles['adresse_ban'] = 'Adresse Exacte'
        elif 'adresse_brute' in df_resultats.columns:
            colonnes_utiles['adresse_brute'] = 'Adresse Exacte'
            
        if 'code_postal_ban' in df_resultats.columns:
            colonnes_utiles['code_postal_ban'] = 'Code Postal'
            
        for col, nom in [
            ('numero_appartement', 'N° Appartement'), ('numero_lot', 'N° Lot'),
            ('batiment', 'Bâtiment'), ('escalier', 'Escalier'), ('etage', 'Étage'),
            ('etiquette_dpe', 'Note DPE'), ('surface_habitable_logement', 'Surface (m²)'),
            ('date_etablissement_dpe', 'Date DPE')
        ]:
            if col in df_resultats.columns:
                colonnes_utiles[col] = nom

        df_affichage = df_resultats[list(colonnes_utiles.keys())].rename(columns=colonnes_utiles) if colonnes_utiles else df_resultats 

        # Filtrage par quartier
        if secteur != "Tous les secteurs":
            rues_quartiers = {
                "Carré d'Or": ["france", "massena", "paradis", "suede", "verdun", "meyerbeer", "congres", "cronstadt", "dalpozzo", "grimaldi"],
                "Promenade des Anglais": ["promenade des anglais", "etats-unis", "quai des etats-unis"],
                "Port / Garibaldi": ["garibaldi", "lunel", "cassini", "barla", "arson", "republique", "port", "république", "catherine segurane"],
                "Mont Boron": ["mont boron", "jean lorrain", "carnot", "germaine", "andre joly", "valrose", "cap de nice", "montee"],
                "Musiciens / Gambetta": ["gambetta", "berlioz", "gounod", "rossini", "verdi", "clemenceau", "victor hugo", "offenbach", "turenne"],
                "Centre-ville": ["jean medecin", "gioffredo", "marechal foch", "pastorelli", "de chateauneuf", "assalit", "durandy"]
            }
            mots_cles = rues_quartiers.get(secteur, [])
            if 'Adresse Exacte' in df_affichage.columns and mots_cles:
                pattern = '|'.join(mots_cles)
                mask_rue = df_affichage['Adresse Exacte'].astype(str).str.lower().str.contains(pattern, na=False, regex=True)
                df_affichage = df_affichage[mask_rue]

        # Calcul Ancienneté DPE
        if 'Date DPE' in df_affichage.columns:
            df_affichage = df_affichage.sort_values(by='Date DPE', ascending=False)
            date_actuelle = datetime.now()
            statuts_mandats = []
            
            for d in df_affichage['Date DPE']:
                try:
                    dt_dpe = pd.to_datetime(d)
                    diff_mois = (date_actuelle.year - dt_dpe.year) * 12 + (date_actuelle.month - dt_dpe.month)
                    if 3 <= diff_mois <= 6:
                        statuts_mandats.append("🎯 Cible Mandat Mûr (3-6 mois)")
                    elif diff_mois < 3:
                        statuts_mandats.append("⚡ DPE récent (< 3 mois)")
                    else:
                        statuts_mandats.append("🏢 Historique (> 6 mois)")
                except:
                    statuts_mandats.append("📅 À qualifier")
            df_affichage['Statut Mandat'] = statuts_mandats

        # Découpage du lot
        index_debut = (int(tranche_mois.split()[1]) - 1) * 50
        index_fin = index_debut + 50
        df_affichage = df_affichage.iloc[index_debut:index_fin]
        
        # Sauvegarde dans la session state
        st.session_state.df_affichage = df_affichage
        st.session_state.analyse_terminee = True


# --- AFFICHAGE PRINCIPAL EN ONGLETS ---
if st.session_state.analyse_terminee:
    
    # Création des deux onglets
    tab1, tab2 = st.tabs(["📊 1. Base de données & Ciblage", "✉️ 2. Générateur de Courriers"])
    
    # ONGLET 1 : LE TABLEAU DE DONNÉES
    with tab1:
        st.success(f"✅ Listing généré ! **{len(st.session_state.df_affichage)}** biens ciblés.")
        st.dataframe(st.session_state.df_affichage, use_container_width=True)
        
        csv = st.session_state.df_affichage.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Télécharger ce lot (CSV)",
            data=csv,
            file_name=f"listing_prospection.csv",
            mime='text/csv',
        )

    # ONGLET 2 : LE GÉNÉRATEUR DE COURRIERS
    with tab2:
        st.header("Générateur de Courrier Sur-Mesure")
        st.write("Croisez les données DPE (tableau) et DVF (ancienneté) pour générer l'argumentaire parfait.")
        
        col_gauche, col_droite = st.columns([1, 2])
        
        with col_gauche:
            if 'Adresse Exacte' in st.session_state.df_affichage.columns:
                liste_adresses = st.session_state.df_affichage['Adresse Exacte'].dropna().unique().tolist()
                adresse_selectionnee = st.selectbox("📍 Sélectionner l'adresse :", liste_adresses)
            else:
                adresse_selectionnee = "[Adresse du bien]"
                
            angle_attaque = st.radio(
                "🎯 Choisir l'angle stratégique :",
                [
                    "1️⃣ Turnover 5 ans (Lassitude & Arbitrage)",
                    "2️⃣ Longue détention (> 10 ans) + Passoire F/G",
                    "3️⃣ Mandat Mûr (Reconquête DPE 3-6 mois)",
                    "4️⃣ Investisseur / SCI (Anticipation LMNP/PLF)"
                ]
            )
            
        with col_droite:
            date_jour = datetime.now().strftime("%d/%m/%Y")
            
            if "Turnover" in angle_attaque:
                sujet = "Évolution du marché niçois et valorisation de votre bien au " + adresse_selectionnee
                corps = f"""Vous êtes propriétaire d'un bien immobilier dans cette résidence depuis environ cinq ans. Sur le marché niçois, cette durée de détention correspond souvent à un cap de réflexion : évolution des projets personnels, fin d'un cycle d'investissement, ou anticipation des nouvelles normes énergétiques.

Depuis votre acquisition, le marché a connu de profondes mutations, notamment avec l'entrée en vigueur de la Loi Climat et Résilience. Ces nouvelles exigences modifient aujourd'hui la rentabilité et la valeur de revente des biens.

En tant que professionnelle de votre secteur, je réalise actuellement des audits de positionnement pour plusieurs propriétaires du quartier. Si vous souhaitez connaître la valeur actualisée de votre bien, je vous propose un échange confidentiel."""
                
            elif "Longue détention" in angle_attaque:
                sujet = "Impact réglementaire et optimisation fiscale de votre bien au " + adresse_selectionnee
                corps = f"""Propriétaire de longue date au sein de cette copropriété, vous avez su capitaliser sur un secteur recherché de Nice. 

Je me permets de vous contacter car l'évolution récente du cadre légal (Loi Climat et Résilience) impose de nouvelles contraintes lourdes sur les biens immobiliers, avec notamment un gel des loyers et l'interdiction progressive de louer selon l'étiquette énergétique. À Nice, engager des travaux de rénovation en copropriété s'avère souvent complexe.

De nombreux propriétaires font aujourd'hui le choix de l'arbitrage. Céder ce bien en l'état vous permet de vous libérer de ces contraintes tout en bénéficiant de l'abattement fiscal sur les plus-values lié à votre longue durée de détention.

Je vous propose de réaliser gracieusement une étude pour chiffrer l'impact de ces réglementations sur votre actif."""
                
            elif "Mandat Mûr" in angle_attaque:
                sujet = "Stratégie de vente et positionnement de votre bien au " + adresse_selectionnee
                corps = f"""En analysant les données techniques de votre secteur, j'ai noté qu'un Diagnostic de Performance Énergétique a été réalisé pour votre bien situé au {adresse_selectionnee} il y a quelques mois.

Si votre bien est actuellement sur le marché et ne trouve pas preneur, sachez que les acquéreurs sont devenus extrêmement exigeants. Les caractéristiques énergétiques, si elles ne sont pas défendues par des arguments techniques solides, allongent les délais et fragilisent le prix net vendeur.

Une commercialisation efficace ne se résume plus à publier une annonce. Je ne viens pas vous proposer une estimation au rabais, mais un véritable audit de commercialisation. Je me tiens à votre disposition pour vous partager mon analyse."""
                
            else:
                sujet = "Anticipation fiscale et arbitrage de votre actif au " + adresse_selectionnee
                corps = f"""En qualité de professionnel intervenant sur la gestion patrimoniale à Nice, je m'adresse à vous concernant l'actif détenu au {adresse_selectionnee}.

Dans le cadre des révisions actuelles liées au Projet de Loi de Finances (PLF 2027), des évolutions structurelles sont à l'étude concernant le régime des plus-values et le traitement des amortissements (LMNP, SCI). Ces réformes pourraient impacter significativement la rentabilité de votre investissement.

Anticiper l'adoption de ces mesures est aujourd'hui essentiel pour sécuriser la valeur de vos actifs. 

J'accompagne mes clients investisseurs dans l'audit de leur portefeuille. Je serais ravie de vous proposer une consultation pour évaluer le positionnement de votre bien dans ce nouveau contexte."""
            
            st.text_area("📄 Aperçu du courrier (Copiez ce texte pour l'imprimer) :", 
                         value=f"Date : {date_jour}\n\nObjet : {sujet}\n\nMadame, Monsieur,\n\n{corps}\n\nBien cordialement,\n\n[Votre Nom]\n[Votre Agence]", 
                         height=450)
else:
    st.info("👉 Sélectionnez vos critères dans le menu à gauche, puis cliquez sur **'Générer le listing certifié'**.")
