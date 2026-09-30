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
st.markdown("Base de données certifiée : passoires énergétiques (F & G) et ciblage par quartier.")

# Chargement du fichier CSV
try:
    df_global = pd.read_csv('dpe_nice_fg.csv')
except Exception as e:
    df_global = pd.DataFrame()
    st.error(f"Erreur critique lors du chargement du fichier CSV : {e}")

# --- BARRE LATÉRALE DE RECHERCHE ---
st.sidebar.header("Critères de ciblage")

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

# Gestion automatique du mois / lot avec option de secours manuelle
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

mode_manuel = st.sidebar.checkbox("🔧 Activer le choix manuel du lot (secours)", value=False)

if mode_manuel:
    tranche_mois = st.sidebar.selectbox("Choisir le lot manuellement", liste_lots)
else:
    tranche_mois = liste_lots[min(lot_auto_index, len(liste_lots) - 1)]
    st.sidebar.info(f"📅 Lot attribué automatiquement (Mois en cours) : **{tranche_mois}**")

lancer = st.sidebar.button("Générer le listing certifié")

# --- TRAITEMENT ET AFFICHAGE ---
if lancer:
    if df_global.empty:
        st.error("⚠️ Le fichier `dpe_nice_fg.csv` est introuvable à la racine du dépôt GitHub.")
    else:
        df_resultats = df_global.copy()
        
        colonnes_utiles = {}
        if 'adresse_ban' in df_resultats.columns:
            colonnes_utiles['adresse_ban'] = 'Adresse Exacte'
        elif 'adresse_brute' in df_resultats.columns:
            colonnes_utiles['adresse_brute'] = 'Adresse Exacte'
            
        if 'code_postal_ban' in df_resultats.columns:
            colonnes_utiles['code_postal_ban'] = 'Code Postal'
            
        if 'etiquette_dpe' in df_resultats.columns:
            colonnes_utiles['etiquette_dpe'] = 'Note DPE'
            
        if 'surface_habitable_logement' in df_resultats.columns:
            colonnes_utiles['surface_habitable_logement'] = 'Surface (m²)'
            
        if 'date_etablissement_dpe' in df_resultats.columns:
            colonnes_utiles['date_etablissement_dpe'] = 'Date DPE'

        if colonnes_utiles:
            df_affichage = df_resultats[list(colonnes_utiles.keys())].rename(columns=colonnes_utiles)
        else:
            df_affichage = df_resultats 

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

        # Tri chronologique par date de DPE
        if 'Date DPE' in df_affichage.columns:
            df_affichage = df_affichage.sort_values(by='Date DPE', ascending=False)

        # Découpage par tranche de 50
        index_debut = (int(tranche_mois.split()[1]) - 1) * 50
        index_fin = index_debut + 50
        df_affichage = df_affichage.iloc[index_debut:index_fin]

        # Colonnes de qualification pour la prospection terrain
        df_affichage['Propriétaire / Statut'] = "Particulier (Croisement DVF / Cadastre conseillé)"
        df_affichage['Action Recommandée'] = "Boîtage ciblé / Courrier personnalisé"

        st.success(f"✅ Listing généré ({tranche_mois}) ! **{len(df_affichage)}** biens affichés pour le secteur : *{secteur}*.")
        st.dataframe(df_affichage, use_container_width=True)
        
        csv = df_affichage.to_csv(index=False).encode('utf-8')
        st.download_button(
            label=f"📥 Télécharger ce {tranche_mois} (CSV)",
            data=csv,
            file_name=f"listing_{secteur.lower().replace(' ', '_')}_{tranche_mois.lower().replace(' ', '_')}.csv",
            mime='text/csv',
        )
else:
    st.info("👉 Sélectionnez vos critères dans le menu à gauche, puis cliquez sur **'Générer le listing certifié'**.")
