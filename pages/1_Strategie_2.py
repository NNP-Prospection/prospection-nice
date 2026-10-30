from datetime import datetime
import glob
import os
import pandas as pd
import requests
import xml.etree.ElementTree as ET
import streamlit as st
import re

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="Stratégie 2 - Bailleurs & Copropriétés", page_icon="💼", layout="wide"
)

st.title("💼 Stratégie 2 : Bailleurs, Copropriétés Lourdes (RNIC) & Vacance (LOVAC)")
st.markdown(
    "Ciblage des investisseurs face aux appels de fonds (travaux RNIC), à l'urgence énergétique (DPE) "
    "et à la taxation sur la vacance locative (THLV / LOVAC)."
)

# --- FONCTION DE NETTOYAGE DES NUMÉROS ---
def formater_numero(val):
    if pd.isna(val) or str(val).strip().lower() in ["nan", "none", "null", "", "<na>"]:
        return ""
    val_str = str(val).strip()
    if val_str.endswith(".0"):
        return val_str[:-2]
    return val_str

# --- CHARGEMENT OPTIMISÉ DES BASES (LAZY LOADING & USECOLS) ---
@st.cache_data
def load_dpe_invest():
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
def load_rnic():
    fichiers_rnic = glob.glob('*rnic*.csv') + glob.glob('*copro*.csv')
    if fichiers_rnic:
        try:
            sample = pd.read_csv(fichiers_rnic[0], sep=None, engine='python', nrows=0)
            mots_cles = ['nom', 'adresse', 'lot', 'syndic', 'date', 'immatriculation', 'travaux', 'budget']
            cols_utiles = [c for c in sample.columns if any(m in c.lower() for m in mots_cles)]
            
            if cols_utiles:
                return pd.read_csv(fichiers_rnic[0], sep=None, engine='python', usecols=cols_utiles, low_memory=True)
            return pd.read_csv(fichiers_rnic[0], sep=None, engine='python', low_memory=True)
        except Exception:
            return pd.DataFrame()
    return pd.DataFrame()

@st.cache_data
def load_lovac():
    fichiers_lovac = glob.glob('*lovac*.csv') + glob.glob('*vacant*.csv')
    if fichiers_lovac:
        try:
            return pd.read_csv(fichiers_lovac[0], sep=None, engine='python', low_memory=True)
        except Exception:
            return pd.DataFrame()
    return pd.DataFrame()

df_dpe = load_dpe_invest()
df_rnic = load_rnic()
df_lovac = load_lovac()

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
                    mots_cles_immo = [
                        "loi", "immobilier", "logement", "dpe", "fiscal", "impôt", "bail", 
                        "lmnp", "pinel", "copropriété", "énergie", "taxe", "finance", "plus-value", "vacance"
                    ]
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
st.sidebar.header('🎯 Ciblage Bailleurs')

filtre_strategie = st.sidebar.selectbox(
    "Axe de ciblage (Croisement de données)",
    [
        "1. Risque Travaux Copro (DPE + RNIC)",
        "2. Urgence Vacance Locative (LOVAC)",
        "3. Investisseurs Standards (DPE F/G)"
    ]
)

secteur_invest = st.sidebar.selectbox(
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
tab1, tab2 = st.tabs([
    "✉️ 1. Croisement Data & Publipostage Investisseurs",
    "🚨 2. Veille Juridique en Temps Réel",
])

with tab1:
    st.subheader("Analyse des lots & Génération de courriers stratégiques")

    if not df_dpe.empty:
        colonnes_a_garder = {}
        for col in ["adresse_ban", "adresse_brute", "adresse_propriete"]:
            if col in df_dpe.columns:
                colonnes_a_garder[col] = "Adresse Exacte"
                break

        cibles = {"Étage": False, "N° Apt": False, "N° Lot": False, "Bâtiment": False, "Note DPE": False}

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

        df_affichage = df_dpe[list(colonnes_a_garder.keys())].rename(columns=colonnes_a_garder)

        # Filtre Nice Uniquement (Sécurité géographique)
        if 'Adresse Exacte' in df_affichage.columns:
            df_affichage = df_affichage[
                df_affichage['Adresse Exacte']
                .astype(str)
                .str.lower()
                .str.contains(r'nice|06\d{3}', regex=True, na=False)
            ]

        # Filtre Secteur par Regex stricte (Mots entiers)
        rues_quartiers = {
            "Carré d'Or": ['france', 'massena', 'paradis', 'suede', 'verdun', 'meyerbeer', 'congres', 'cronstadt', 'buffa', 'alphonse karr', 'maccarani', 'liberte', 'longchamp', 'grimaldi', 'dalpozzo', 'halevy', 'marechal joffre', 'rivoli'],
            'Promenade des Anglais': ['promenade des anglais', 'etats-unis', 'quai des etats-unis'],
            'Port / Garibaldi': ['garibaldi', 'lunel', 'cassini', 'barla', 'arson', 'republique', 'port', 'segurane', 'fodere'],
            'Mont Boron': ['mont boron', 'jean lorrain', 'carnot', 'germaine', 'andre joly', 'valrose', 'cap de nice', 'maeterlinck'],
            'Musiciens / Gambetta': ['gambetta', 'berlioz', 'gounod', 'rossini', 'verdi', 'clemenceau', 'victor hugo', 'mozart', ' paganini', 'thiers'],
            'Centre-ville': ['jean medecin', 'gioffredo', 'marechal foch', 'pastorelli', 'assalit', 'durandy', 'hotel des postes', 'dubouchage'],
        }

        if secteur_invest != 'Tous les secteurs':
            mots_cles = rues_quartiers.get(secteur_invest, [])
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
                lot = formater_numero(row.get("N° Lot", ""))
                dpe = str(row.get("Note DPE", "")).strip().upper()

                details = []
                if bat: details.append(f"Bât. {bat}")
                if etage: details.append(f"Étage {etage}")
                if apt: details.append(f"Apt {apt}")
                if lot: details.append(f"Lot {lot}")
                if dpe: details.append(f"DPE {dpe}")

                str_details = " | ".join(details) if details else "Lot standard"
                return f"{adresse} — [{str_details}]"

            df_affichage["Libellé Complet"] = df_affichage.apply(creer_libelle_bien, axis=1)
            
            biens_dispos = df_affichage["Libellé Complet"].dropna().unique().tolist()[:1000]
            biens_dispos.sort()

            bien_choisi = st.selectbox(
                "📍 Sélectionner le bien d'investissement ciblé :", biens_dispos
            )

            if bien_choisi:
                ligne_bien = df_affichage[df_affichage["Libellé Complet"] == bien_choisi].iloc[0]
                adresse_brute = str(ligne_bien.get("Adresse Exacte", "")).title()
                apt = formater_numero(ligne_bien.get("N° Apt", ""))
                lot = formater_numero(ligne_bien.get("N° Lot", ""))
                etage = formater_numero(ligne_bien.get("Étage", ""))
                bat = formater_numero(ligne_bien.get("Bâtiment", ""))
                note_dpe = str(ligne_bien.get("Note DPE", "")).strip().upper()

                infos_repere = []
                if bat: infos_repere.append(f"Bât. {bat}")
                if etage: infos_repere.append(f"Étage : {etage}")
                if apt: infos_repere.append(f"Apt {apt}")
                if lot: infos_repere.append(f"Lot n° {lot}")
                if note_dpe: infos_repere.append(f"DPE : {note_dpe}")

                str_reperage = " | ".join(infos_repere) if infos_repere else "Bien identifié"
                date_jour = datetime.now().strftime("%d/%m/%Y")

                is_rnic = not df_rnic.empty and any(mot in adresse_brute.lower() for mot in ['france', 'massena', 'promenade'])
                is_lovac = not df_lovac.empty and 'vacance' in filtre_strategie.lower()

                st.markdown(f"### 📍 {adresse_brute} — Repérage : `{str_reperage}`")
                
                col_tag1, col_tag2 = st.columns(2)
                if filtre_strategie.startswith("1.") or is_rnic:
                    col_tag1.warning("🏗️ **Alerte RNIC :** Immeuble identifié avec potentiel d'appels de fonds lourds à court terme.")
                if filtre_strategie.startswith("2.") or is_lovac:
                    col_tag2.error("📉 **Alerte LOVAC :** Bien potentiellement concerné par la Taxe sur les Logements Vacants.")

                if filtre_strategie.startswith("1."):
                    objet = f"Appels de fonds de copropriété, travaux énergétiques et arbitrage de votre actif au {adresse_brute}"
                    paragraphe_cible = (
                        "Le croisement des registres de copropriété (RNIC) et des audits énergétiques révèle une "
                        "accélération imminente des appels de fonds dans les immeubles de votre secteur. Entre le vote "
                        "de ravalements, la mise aux normes des parties communes et l'obligation d'améliorer les "
                        f"performances des parties privatives (votre lot est actuellement estimé en DPE {note_dpe or 'F/G'}), "
                        "la rentabilité nette des bailleurs est directement menacée.\n\n"
                        "Plutôt que d'immobiliser votre trésorerie dans ces travaux structurels, une stratégie de cession "
                        "anticipée permet de sécuriser votre capital et de le réallouer vers des supports plus performants."
                    )
                elif filtre_strategie.startswith("2."):
                    objet = f"Taxation sur la vacance locative et optimisation de votre actif au {adresse_brute}"
                    paragraphe_cible = (
                        "Les services fiscaux renforcent actuellement le recouvrement de la Taxe sur les Logements Vacants (TLV/THLV) "
                        "sur la commune de Nice. Maintenir un bien inoccupé génère aujourd'hui une double perte : l'absence de revenus "
                        "locatifs combinée à une pénalité fiscale croissante, sans compter l'usure naturelle du lot.\n\n"
                        "Si ce bien ne s'inscrit plus dans votre stratégie de rendement à court terme, le marché niçois actuel "
                        "offre une excellente fenêtre de liquidité. Revendre cet actif vous permet de neutraliser cette charge fiscale "
                        "et de dégager un capital net immédiat."
                    )
                else:
                    objet = f"Alerte fiscale, rentabilité et stratégie d'arbitrage de votre actif au {adresse_brute}"
                    paragraphe_cible = (
                        "Le marché de l'investissement locatif traverse actuellement une zone de mutation majeure :\n"
                        "1. Les évolutions de la fiscalité (LMNP, régimes réels) et les règles d'amortissement imposent une gestion proactive de vos actifs.\n"
                        "2. Le calendrier de la loi Climat et Résilience maintient ses exigences strictes sur la performance énergétique des biens mis en location.\n\n"
                        f"Avant que ces réglementations ne viennent impacter la valeur vénale de votre lot ({str_reperage}), l'anticipation de votre stratégie est essentielle."
                    )

                courrier_investisseur = f"""Nice, le {date_jour}

Destinataire : Propriétaire Bailleur / Investisseur
Localisation du lot : {str_reperage}
Adresse du bien : {adresse_brute}

Madame, Monsieur,

Objet : {objet}

En qualité de professionnel de l'immobilier, je me permets de vous contacter de manière confidentielle au sujet du bien dont vous êtes propriétaire dans cet immeuble.

{paragraphe_cible}

Je me tiens à votre entière disposition pour réaliser un audit confidentiel de votre lot et étudier avec vous l'opportunité d'une valorisation optimale sur le marché actuel.

Bien cordialement,

Nathalie Parra

CABINET PRIVÉ IMMOBILIER HONORAT
AUDIT . TRANSACTION . CONSEIL

---
*Nathalie Parra — Titulaire de la carte professionnelle CPI délivrée par la CCI Nice Côte d'Azur*
*Membre de la FNAIM*"""

                st.text_area(
                    "📄 Courrier de prospection investisseur personnalisé :",
                    value=courrier_investisseur,
                    height=380,
                )
                
                logo_path = "Cabinet Immobilier Privé HONORAT.png"
                if os.path.exists(logo_path):
                    st.image(logo_path, width=200)

        else:
            st.info("⚠️ Aucun lot d'investissement trouvé pour ces critères. Modifiez le secteur.")
    else:
        st.warning("⚠️ Base de données DPE / RNIC introuvable ou vide. Vérifiez vos fichiers sources.")

with tab2:
    st.subheader("🚨 Veille Juridique et Fiscale (Bailleurs & Investisseurs)")
    st.write("Flux continus des actualités officielles pour sécuriser vos conseils professionnels.")
    if alertes_en_direct:
        for art in alertes_en_direct:
            st.markdown(f"- **[{art['titre']}]({art['lien']})**")
    else:
        st.info("Aucune alerte récente sur les flux officiels.")
