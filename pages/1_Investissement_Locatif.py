import streamlit as st
import pandas as pd
import requests

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="Investissement Locatif & Fin de Défiscalisation - Nice",
    page_icon="📈",
    layout="wide"
)

st.title("📈 Espace Investisseurs & Fin de Défiscalisation - Nice")
st.markdown("Ciblage patrimonial : biens en fin d'engagement fiscal (Pinel / amortissements) – Opportunités de revente & réinvestissement.")

# Chargement du fichier CSV
try:
    df_global = pd.read_csv('dpe_nice_fg.csv')
except Exception as e:
    df_global = pd.DataFrame()
    st.error(f"Erreur critique lors du chargement du fichier CSV : {e}")

# --- FONCTION D'ENRICHISSEMENT DES SOCIÉTÉS / SCI ---
def chercher_infos_entreprise(terme_recherche):
    if not terme_recherche or str(terme_recherche).lower() == "nan":
        return {"siren": "N/A", "dirigeant": "N/A", "siege": "N/A"}
        
    url = "https://recherche-entreprises.api.gouv.fr/search"
    params = {"q": terme_recherche, "per_page": 3}
    
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
        "Fin de cycle Pinel / Ancienneté DPE (6 à 9 ans)",
        "Ciblage Typologie Investisseur (Studios / 2 pièces)",
        "SCI Immobilières Détenues en Local"
    ]
)

# Filtre par secteur / quartier à Nice
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

lancer = st.sidebar.button("Analyser le portefeuille investisseur")

# --- TRAITEMENT ET AFFICHAGE ---
if lancer:
    if df_global.empty:
        st.error("⚠️ Le fichier `dpe_nice_fg.csv` est introuvable à la racine du dépôt GitHub.")
    else:
        df_resultats = df_global.copy()
        
        # Sélection et renommage des colonnes utiles
        colonnes_utiles = {}
        col_adresse = None
        if 'adresse_ban' in df_resultats.columns:
            col_adresse = 'adresse_ban'
            colonnes_utiles['adresse_ban'] = 'Adresse Exacte'
        elif 'adresse_brute' in df_resultats.columns:
            col_adresse = 'adresse_brute'
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

        # Filtrage par secteur si demandé
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

        # Application des filtres spécifiques selon la stratégie investisseur choisie
        if "Pinel" in strategie and 'Date DPE' in df_affichage.columns:
            # On cherche par exemple les DPE réalisés entre 2017 et 2020 (correspondant aux investissements de 6 à 9 ans arrivant à échéance)
            df_affichage['Année DPE'] = pd.to_datetime(df_affichage['Date DPE'], errors='coerce').dt.year
            df_affichage = df_affichage[(df_affichage['Année DPE'] >= 2017) & (df_affichage['Année DPE'] <= 2020)]
            df_affichage['Horizon Fiscal'] = "Fin de cycle Pinel / Amortissement (Vente ou Réinvestissement potentiel)"
            
        elif "Typologie" in strategie and 'Surface (m²)' in df_affichage.columns:
            # Typique investisseur : studios et petits 2 pièces (inférieur à 50 m²)
            df_affichage = df_affichage[df_affichage['Surface (m²)'] <= 50]
            df_affichage['Profil Investisseur'] = "Petite surface locative (Cible type studio/2P)"
            
        else:
            df_affichage['Analyse Patrimoniale'] = "Portefeuille Global Investisseur"

        # Option d'enrichissement SCI orientée investisseurs
        if "SCI" in strategie or st.sidebar.checkbox("Activer l'enrichissement SCI (Sociétés)", value=False):
            if len(df_affichage) > 30:
                st.info("ℹ️ L'enrichissement SCI est appliqué aux 30 premiers biens pour optimiser la vitesse de l'API.")
                df_to_enrich = df_affichage.head(30).copy()
            else:
                df_to_enrich = df_affichage.copy()

            st.info("🔄 Interrogation de l'API Sirene pour identifier les structures...")
            sirens, dirigeants, sieges = [], [], []
            
            for idx, row in df_to_enrich.iterrows():
                terme_recherche = f"SCI {row.get('Adresse Exacte', '')}"
                infos = chercher_infos_entreprise(terme_recherche)
                sirens.append(infos['siren'])
                dirigeants.append(infos['dirigeant'])
                sieges.append(infos['siege'])
                
            df_to_enrich['N° SIREN'] = sirens
            df_to_enrich['Gérant / Mandataire'] = dirigeants
            df_to_enrich['Siège Social'] = sieges
            df_affichage = df_to_enrich

        st.success(f"✅ Analyse générée ! **{len(df_affichage)}** biens qualifiés pour la stratégie : *{strategie}*.")
        st.dataframe(df_affichage, use_container_width=True)
        
        csv = df_affichage.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Télécharger le listing investisseurs (CSV)",
            data=csv,
            file_name=f"listing_investisseurs_{secteur.lower().replace(' ', '_')}.csv",
            mime='text/css' if False else 'text/csv',
        )
else:
    st.info("👉 Sélectionnez vos critères patrimoniaux dans le menu latéral et cliquez sur **'Analyser le portefeuille investisseur'**.")
