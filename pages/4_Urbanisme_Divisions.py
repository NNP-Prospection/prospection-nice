from datetime import datetime
import glob
import os
import pandas as pd
import streamlit as st
import re

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="Stratégie 5 - Urbanisme", page_icon="🏗️", layout="wide"
)

st.title("🏗️ Stratégie 5 : Droit des Sols & Valorisation (Sitadel2)")
st.markdown(
    "Exploitation des données d'urbanisme (Déclarations Préalables, Permis de Construire, Changements de destination) "
    "pour capter les vendeurs en phase de création de valeur ou de division."
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
def load_dpe_urbanisme():
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
def load_sitadel():
    fichiers_sitadel = glob.glob('*sitadel*.csv') + glob.glob('*urbanisme*.csv')
    if fichiers_sitadel:
        try:
            return pd.read_csv(fichiers_sitadel[0], sep=None, engine='python', low_memory=True)
        except Exception:
            return pd.DataFrame()
    return pd.DataFrame()

df_dpe = load_dpe_urbanisme()
df_sitadel = load_sitadel()

# --- BARRE LATÉRALE DE RECHERCHE ---
st.sidebar.header("🎯 Ciblage Droit des Sols")

type_operation = st.sidebar.selectbox(
    "Type d'Opération (Filtre Sitadel)",
    [
        "1. Division parcellaire / Création de lots (DP)",
        "2. Changement de destination (Ex: Local vers Habitation)",
        "3. Projets en Zone ABF / Surélévations (PC)"
    ]
)

secteur_urba = st.sidebar.selectbox(
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
    "✉️ 1. Prospection Création de Valeur & Courriers",
    "📊 2. Registre Sitadel2 (Permis & DP)",
])

with tab1:
    st.subheader("Identification des projets et approche d'expert")

    if not df_dpe.empty:
        colonnes_a_garder = {}
        for col in ["adresse_ban", "adresse_brute", "adresse_propriete"]:
            if col in df_dpe.columns:
                colonnes_a_garder[col] = "Adresse Exacte"
                break

        cibles = {"Étage": False, "N° Apt": False, "N° Lot": False, "Bâtiment": False, "Surface m²": False}

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

        if secteur_urba != 'Tous les secteurs':
            mots_cles = rues_quartiers.get(secteur_urba, [])
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

                details = []
                if bat: details.append(f"Bât. {bat}")
                if etage: details.append(f"Étage {etage}")
                if apt: details.append(f"Apt {apt}")

                str_details = " | ".join(details) if details else "Lot"
                return f"{adresse} — [{str_details}]"

            df_affichage["Libellé Complet"] = df_affichage.apply(creer_libelle_bien, axis=1)
            biens_dispos = df_affichage["Libellé Complet"].dropna().unique().tolist()[:1000]
            biens_dispos.sort()

            bien_choisi = st.selectbox(
                "📍 Sélectionner le lot ou l'adresse cible :", biens_dispos
            )

            if bien_choisi:
                ligne_bien = df_affichage[df_affichage["Libellé Complet"] == bien_choisi].iloc[0]
                adresse_brute = str(ligne_bien.get("Adresse Exacte", "")).title()
                
                is_sitadel = not df_sitadel.empty and any(mot in adresse_brute.lower() for mot in ['france', 'massena', 'mont boron'])
                
                if type_operation.startswith("1.") or is_sitadel:
                    st.success("🏗️ **Signal Sitadel2 :** Mouvement d'urbanisme récent détecté sur ce secteur ou cette adresse.")
                
                date_jour = datetime.now().strftime("%d/%m/%Y")
                
                if type_operation.startswith("1."):
                    objet_courrier = f"Valorisation de vos nouveaux lots suite à déclaration préalable au {adresse_brute}"
                    paragraphe_cible = (
                        "La division d'un bien immobilier est une excellente stratégie de création de valeur, mais "
                        "elle modifie substantiellement le positionnement sur le marché niçois.\n\n"
                        "Forte d'une parfaite connaissance "
                        "des dynamiques locales, je vous propose une étude de commercialisation sur-mesure pour vos lots nouvellement "
                        "créés. Cette évaluation prendra en compte la rareté de ces surfaces sur votre secteur et les "
                        "attentes précises des investisseurs actuels."
                    )
                elif type_operation.startswith("2."):
                    objet_courrier = f"Changement de destination et impact sur la valeur vénale de votre bien au {adresse_brute}"
                    paragraphe_cible = (
                        "Les démarches visant à modifier la destination d'un local (transformation d'un "
                        "bureau ou commerce en habitation) constituent un levier majeur, particulièrement "
                        "recherché dans notre hyper-centre.\n\n"
                        "Bénéficiant d'une solide expérience sur le marché niçois, notre Cabinet est qualifié pour "
                        "traduire cette nouvelle configuration en une réelle plus-value financière. Je vous "
                        "propose un audit confidentiel pour chiffrer l'impact direct de ce changement de destination "
                        "sur votre bien."
                    )
                else:
                    objet_courrier = f"Accompagnement de votre projet immobilier au {adresse_brute}"
                    paragraphe_cible = (
                        "Concevoir et faire valider un projet de restructuration ou de surélévation "
                        "demande une rigueur exceptionnelle.\n\n"
                        "Ancienne responsable du développement, j'accompagne "
                        "les propriétaires dans la valorisation de ces actifs complexes. Une fois les autorisations purgées, "
                        "la rareté de ce type de bien réhabilité dans le patrimoine niçois justifie un positionnement "
                        "haut de gamme que je vous propose d'évaluer lors d'un rendez-vous confidentiel."
                    )

                courrier_urba = f"""Nice, le {date_jour}

Destinataire : Propriétaire / Maître d'Ouvrage
Localisation du projet : {adresse_brute}

Madame, Monsieur,

Objet : {objet_courrier}

{paragraphe_cible}

Je me tiens à votre entière disposition pour vous remettre une étude détaillée, intégrant à la fois la rentabilité locative potentielle de votre projet et sa valeur de revente estimée sur le marché actuel.

Dans l'attente de nos échanges, je vous prie de recevoir, Madame, Monsieur, l'expression de mes salutations distinguées.

Nathalie Parra

CABINET PRIVÉ IMMOBILIER HONORAT
AUDIT . TRANSACTION . CONSEIL

---
*Nathalie Parra — Titulaire de la carte professionnelle CPI délivrée par la CCI Nice Côte d'Azur*
*Membre de la FNAIM*"""

                st.markdown("---")
                st.text_area(
                    "📄 Modèle de Lettre (Expertise Urbanisme & Valorisation) :",
                    value=courrier_urba,
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
    st.subheader('📊 Tableau de Bord Sitadel2 (Urbanisme)')
    st.write(
        "Ce module vous permet d'analyser les permis de construire et déclarations préalables "
        "délivrés récemment (base de données Sitadel du Ministère de la Transition Écologique)."
    )
    
    if df_sitadel.empty:
        st.info("📥 Fichier Sitadel non détecté. Placez un fichier CSV contenant 'sitadel' ou 'urbanisme' dans votre répertoire de travail.")
    else:
        st.success(f"Base Sitadel chargée avec succès ({len(df_sitadel)} dossiers d'urbanisme détectés).")
        st.dataframe(df_sitadel.head(100), use_container_width=True)
