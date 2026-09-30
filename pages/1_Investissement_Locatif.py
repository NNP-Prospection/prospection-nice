import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="Investissement Locatif & Ciblage SCI - Nice",
    page_icon="📈",
    layout="wide"
)

st.title("📈 Espace Investisseurs & Ciblage SCI - Nice")
st.markdown("Ciblage patrimonial et enrichissement automatique des sociétés via l'API Sirene.")

# Chargement du fichier CSV
try:
    df_global = pd.read_csv('dpe_nice_fg.csv')
except Exception as e:
    df_global = pd.DataFrame()
    st.error(f"Erreur critique lors du chargement du fichier CSV : {e}")

# --- FONCTION D'ENRICHISSEMENT DES SOCIÉTÉS / SCI (Optimisée) ---
def chercher_infos_entreprise(terme_recherche, rue_secours=""):
    url = "https://recherche-entreprises.api.gouv.fr/search"
    
    queries = [terme_recherche]
    if rue_secours:
        queries.append(f"SCI {rue_secours} Nice")
        queries.append(f"Immobilier {rue_secours} Nice")
        
    for q in queries:
        if not q or str(q).lower() == "nan":
            continue
        params = {"q": q, "per_page": 3}
        try:
            response = requests.get(url, params=params, timeout=3)
            if response.status_code == 200:
                resultats = response.json().get("results", [])
                if resultats:
                    best_match = resultats[0]
                    for res in resultats:
                        siege = res.get("siege", {})
                        cp = str(siege.get("code_postal", ""))
                        if cp.startswith("06"):
                            best_match = res
                            break
                    
                    siren = best_match.get("siren", "N/A")
                    dirigeants = best_match.get("dirigeants", [])
                    nom_dirigeant = f"{dirigeants[0].get('prenoms', '')} {dirigeants[0].get('nom', '')}".strip() if dirigeants else "Non renseigné"
                    
                    siege = best_match.get("siege", {})
                    adresse_siege = f"{siege.get('adresse', '')}, {siege.get('code_postal', '')} {siege.get('libelle_commune', '')}"
                    
                    if siren != "N/A":
                        return {
                            "siren": siren,
                            "dirigeant": nom_dirigeant if nom_dirigeant else "Non renseigné",
                            "siege": adresse_siege.strip(", ") if adresse_siege.strip(", ") else "Adresse non renseignée"
                        }
        except Exception:
            pass
            
    return {"siren": "N/A", "dirigeant": "N/A", "siege": "N/A"}

# --- BARRE LATÉRALE DE RECHERCHE ---
st.sidebar.header("Filtres Investisseurs & Fiscalité")

strategie = st.sidebar.selectbox(
    "Profil de ciblage",
    [
        "Ciblage SCI / Sociétés (Enrichissement SIRENE)",
        "Fin de cycle Pinel / Ancienneté DPE (6 à 9 ans)",
        "Ciblage Typologie Investisseur (Studios / 2 pièces)"
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

mode_manuel = st.sidebar.checkbox("🔧 Activer le choix manuel du lot (secours)", value=False, key="manuel_inv")

if mode_manuel:
    tranche_mois = st.sidebar.selectbox("Choisir le lot investisseur manuellement", liste_lots, key="select_inv")
else:
    tranche_mois = liste_lots[min(lot_auto_index, len(liste_lots) - 1)]
    st.sidebar.info(f"📅 Lot investisseur attribué (Mois en cours) : **{tranche_mois}**")

lancer = st.sidebar.button("Analyser le portefeuille investisseur")

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
            
        if 'surface_habitable_logement' in df_resultats.columns:
            colonnes_utiles['surface_habitable_logement'] = 'Surface (m²)'
            
        if 'date_etablissement_dpe' in df_resultats.columns:
            colonnes_utiles['date_etablissement_dpe'] = 'Date DPE'

        if colonnes_utiles:
            df_affichage = df_resultats[list(colonnes_utiles.keys())].rename(columns=colonnes_utiles)
        else:
            df_affichage = df_resultats 

        # Filtrage par secteur
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

        # Enrichissement automatique SCI / Sociétés
        st.info("🔄 Interrogation approfondie de l'API Sirene pour ce lot de sociétés...")
        sirens, dirigeants, sieges = [], [], []
        
        for idx, row in df_affichage.iterrows():
            adresse = str(row.get('Adresse Exacte', ''))
            terme_recherche = f"SCI {adresse}"
            infos = chercher_infos_entreprise(terme_recherche, rue_secours=adresse)
            sirens.append(infos['siren'])
            dirigeants.append(infos['dirigeant'])
            sieges.append(infos['siege'])
            
        df_affichage['N° SIREN'] = sirens
        df_affichage['Gérant / Mandataire'] = dirigeants
        df_affichage['Siège Social'] = sieges

        st.success(f"✅ Analyse générée ({tranche_mois}) ! **{len(df_affichage)}** biens qualifiés pour : *{strategie}*.")
        st.dataframe(df_affichage, use_container_width=True)
        
        csv = df_affichage.to_csv(index=False).encode('utf-8')
        st.download_button(
            label=f"📥 Télécharger ce {tranche_mois} (CSV)",
            data=csv,
            file_name=f"listing_investisseurs_{secteur.lower().replace(' ', '_')}_{tranche_mois.lower().replace(' ', '_')}.csv",
            mime='text/csv',
        )
else:
    st.info("👉 Sélectionnez vos critères dans le menu latéral, puis cliquez sur **'Analyser le portefeuille investisseur'**.")
