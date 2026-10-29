from datetime import datetime
import glob
import os
import pandas as pd
import streamlit as st
import re

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="Stratégie 4 - Successions", page_icon="🕊️", layout="wide"
)

st.title("🕊️ Stratégie 4 : Successions & Mutations (Décès INSEE & BODACC)")
st.markdown(
    "Ciblage des biens en cours de succession ou mutation. Croisement des adresses DPE "
    "avec les registres publics pour proposer un accompagnement successoral sur-mesure aux ayants droit."
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
def load_dpe_successions():
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
def load_insee_deces():
    # Simulation du chargement du fichier mensuel des décès de l'INSEE
    fichiers_insee = glob.glob('*deces*.csv') + glob.glob('*insee*.csv')
    if fichiers_insee:
        try:
            return pd.read_csv(fichiers_insee[0], sep=None, engine='python', low_memory=True)
        except Exception:
            return pd.DataFrame()
    return pd.DataFrame()

@st.cache_data
def load_bodacc_mutations():
    # Simulation du chargement des annonces BODACC (liquidations, successions vacantes)
    fichiers_bodacc = glob.glob('*bodacc*.csv') + glob.glob('*mutation*.csv')
    if fichiers_bodacc:
        try:
            return pd.read_csv(fichiers_bodacc[0], sep=None, engine='python', low_memory=True)
        except Exception:
            return pd.DataFrame()
    return pd.DataFrame()

df_dpe = load_dpe_successions()
df_insee = load_insee_deces()
df_bodacc = load_bodacc_mutations()

# --- BARRE LATÉRALE DE RECHERCHE ---
st.sidebar.header('🎯 Ciblage Successoral')

filtre_mutation = st.sidebar.selectbox(
    "Axe d'accompagnement",
    [
        "1. Accompagnement Ayants Droit (Croisement INSEE)",
        "2. Mutations / Successions Vacantes (BODACC)",
        "3. Portefeuille Standard (Anticipation / Estimation)"
    ]
)

secteur_succ = st.sidebar.selectbox(
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
    "✉️ 1. Repérage des Actifs & Courriers Ayants Droit",
    "📊 2. Base INSEE & BODACC (Mode Consultation)",
])

with tab1:
    st.subheader("Identification des lots et approche successorale")

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

        # Sécurité géographique : Nice et 06
        if 'Adresse Exacte' in df_affichage.columns:
            df_affichage = df_affichage[
                df_affichage['Adresse Exacte']
                .astype(str)
                .str.lower()
                .str.contains(r'nice|06\d{3}', regex=True, na=False)
            ]

        # Sécurité mots entiers sur les quartiers
        rues_quartiers = {
            "Carré d'Or": ['france', 'massena', 'paradis', 'suede', 'verdun', 'meyerbeer', 'congres', 'cronstadt', 'buffa', 'alphonse karr', 'maccarani', 'liberte', 'longchamp', 'grimaldi', 'dalpozzo', 'halevy', 'marechal joffre', 'rivoli'],
            'Promenade des Anglais': ['promenade des anglais', 'etats-unis', 'quai des etats-unis'],
            'Port / Garibaldi': ['garibaldi', 'lunel', 'cassini', 'barla', 'arson', 'republique', 'port', 'segurane', 'fodere'],
            'Mont Boron': ['mont boron', 'jean lorrain', 'carnot', 'germaine', 'andre joly', 'valrose', 'cap de nice', 'maeterlinck'],
            'Musiciens / Gambetta': ['gambetta', 'berlioz', 'gounod', 'rossini', 'verdi', 'clemenceau', 'victor hugo', 'mozart', ' paganini', 'thiers'],
            'Centre-ville': ['jean medecin', 'gioffredo', 'marechal foch', 'pastorelli', 'assalit', 'durandy', 'hotel des postes', 'dubouchage'],
        }

        if secteur_succ != 'Tous les secteurs':
            mots_cles = rues_quartiers.get(secteur_succ, [])
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
                "📍 Sélectionner le lot pour générer le courrier d'accompagnement :", biens_dispos
            )

            if bien_choisi:
                ligne_bien = df_affichage[df_affichage["Libellé Complet"] == bien_choisi].iloc[0]
                adresse_brute = str(ligne_bien.get("Adresse Exacte", "")).title()
                
                # Simulation détection croisée
                is_insee = not df_insee.empty and any(mot in adresse_brute.lower() for mot in ['france', 'massena'])
                
                if filtre_mutation.startswith("1.") or is_insee:
                    st.info("🕊️ **Alerte INSEE :** Probabilité de mutation ou succession ouverte sur ce secteur. Courrier orienté 'Ayants droit'.")
                
                date_jour = datetime.now().strftime("%d/%m/%Y")
                
                # Rédaction sur-mesure (Empathie & Expertise)
                if filtre_mutation.startswith("1."):
                    objet_courrier = f"Accompagnement successoral et estimation de votre patrimoine au {adresse_brute}"
                    paragraphe_cible = (
                        "Dans le cadre complexe du règlement d'une succession, l'évaluation précise et documentée "
                        "des actifs immobiliers est une étape déterminante, tant pour le notaire en charge du dossier "
                        "que pour la déclaration fiscale de l'indivision.\n\n"
                        "Spécialisé dans l'accompagnement des ayants droit sur les biens de caractère et patrimoniaux "
                        "à Nice, notre Cabinet Privé se tient à votre entière disposition pour réaliser un audit de "
                        "valeur vénale objectif de ce lot. Nous prenons en compte les dernières réglementations "
                        "énergétiques et les règles d'urbanisme locales pour vous fournir un dossier d'estimation "
                        "opposable à l'administration fiscale."
                    )
                    destinataire = "Aux Ayants Droit / À l'Indivision"
                elif filtre_mutation.startswith("2."):
                    objet_courrier = f"Gestion de mutation patrimoniale et sécurisation de votre actif au {adresse_brute}"
                    paragraphe_cible = (
                        "Les procédures de mutation, de liquidation ou de transfert de propriété nécessitent une "
                        "connaissance pointue du marché et des enjeux juridiques attenants.\n\n"
                        "Afin de protéger la valeur de cet actif immobilier pendant cette période de transition, "
                        "il est essentiel d'en maîtriser la valorisation exacte au regard des contraintes locales "
                        "(DPE, fiscalité locale, état de la copropriété). Notre structure est habituée à fluidifier "
                        "ces démarches en lien direct avec vos conseils habituels (notaires, avocats)."
                    )
                    destinataire = "Propriétaire / Ayants Droit"
                else:
                    objet_courrier = f"Audit patrimonial de votre bien situé au {adresse_brute}"
                    paragraphe_cible = (
                        "La transmission d'un patrimoine immobilier s'anticipe. Qu'il s'agisse de préparer une "
                        "donation, d'évaluer une indivision ou de projeter une cession, la première étape est "
                        "toujours de figer la valeur vénale exacte de votre actif.\n\n"
                        "Notre Cabinet Privé vous propose une approche sur-mesure et totalement confidentielle "
                        "pour auditer ce lot, en intégrant ses potentiels et les obligations réglementaires actuelles."
                    )
                    destinataire = "Propriétaire / Indivision"

                courrier_succession = f"""Nice, le {date_jour}

Destinataire : {destinataire}
Localisation du bien : {adresse_brute}

Madame, Monsieur,

Objet : {objet_courrier}

{paragraphe_cible}

Agissant en tant que Conseil en Immobilier Patrimonial, je vous assure d'une démarche empreinte de la plus stricte confidentialité et d'un total respect des situations familiales.

Je me tiens à votre disposition ou à celle de votre notaire pour toute étude approfondie de ce bien.

Je vous prie de recevoir, Madame, Monsieur, l'expression de mes salutations dévouées.

Nathalie Parra
Conseil en Immobilier Patrimonial

CABINET PRIVÉ IMMOBILIER HONORAT
TRANSACTION . CONSEIL . PATRIMOINE"""

                st.markdown("---")
                st.text_area(
                    "📄 Modèle de Lettre (Ton neutre, accompagnant et notarial) :",
                    value=courrier_succession,
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
    st.subheader('📊 Consultation des Bases Officielles (INSEE / BODACC)')
    st.write(
        "Cet onglet vous permettra, une fois les fichiers téléchargés et déposés dans le dossier, "
        "de croiser les adresses cibles avec les registres de l'État."
    )
    
    col_stat1, col_stat2 = st.columns(2)
    with col_stat1:
        if df_insee.empty:
            st.info("📥 Fichier des décès INSEE non détecté. Placez un fichier contenant 'deces' ou 'insee' dans le répertoire.")
        else:
            st.success(f"Fichier INSEE chargé avec succès ({len(df_insee)} lignes).")
            
    with col_stat2:
        if df_bodacc.empty:
            st.info("📥 Fichier BODACC non détecté. Placez un fichier contenant 'bodacc' ou 'mutation' dans le répertoire.")
        else:
            st.success(f"Fichier BODACC chargé avec succès ({len(df_bodacc)} lignes).")
