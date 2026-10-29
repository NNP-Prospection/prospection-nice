from datetime import datetime
import xml.etree.ElementTree as ET
import pandas as pd
import requests
import streamlit as st

st.set_page_config(
    page_title="Stratégie 2 - Investisseurs", page_icon="💼", layout="wide"
)

st.title("💼 Stratégie 2 : Investisseurs & Veille Juridique Continue")
st.markdown(
    "Ciblage précis des investisseurs (Appartement, Étage, Bâtiment, DPE) et"
    " alertes en direct sur les évolutions législatives."
)


# --- FONCTION DE NETTOYAGE DES NUMÉROS ---
def formater_numero(val):
    if pd.isna(val) or str(val).strip().lower() in [
        "nan",
        "none",
        "null",
        "",
        "<na>",
    ]:
        return ""
    val_str = str(val).strip()
    if val_str.endswith(".0"):
        return val_str[:-2]
    return val_str


# --- CHARGEMENT DPE COMPLET ---
@st.cache_data
def load_dpe():
    try:
        return pd.read_csv("dpe_nice_fg.csv", low_memory=False)
    except:
        try:
            return pd.read_csv("dpe_nice_complet.csv", low_memory=False)
        except:
            return pd.DataFrame()


df_dpe = load_dpe()


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
                    titre = (
                        item.find("title").text if item.find("title") is not None else ""
                    )
                    lien = (
                        item.find("link").text if item.find("link") is not None else ""
                    )
                    mots_cles_immo = [
                        "loi",
                        "immobilier",
                        "logement",
                        "dpe",
                        "fiscal",
                        "impôt",
                        "bail",
                        "lmnp",
                        "pinel",
                        "copropriété",
                        "énergie",
                        "taxe",
                        "finance",
                        "plus-value",
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

    return articles_uniques[:8]


alertes_en_direct = fetch_veille_juridique()

# --- AFFICHAGE DES ONGLETS ---
tab1, tab2 = st.tabs([
    "✉️ 1. Publipostage Investisseurs & Repérage",
    "🚨 2. Veille Juridique en Temps Réel",
])

with tab1:
    st.subheader(
        "Ciblage des investisseurs : Repérage précis du lot (Apt, Étage, Bâtiment)"
        " & Fin de cycle fiscal"
    )
    st.write(
        "Ce module croise l'adresse et le repérage exact de chaque lot"
        " (appartement, étage, bâtiment) pour personnaliser vos courriers aux"
        " propriétaires bailleurs."
    )

    if not df_dpe.empty:
        colonnes_a_garder = {}
        for col in ["adresse_ban", "adresse_brute", "adresse_propriete"]:
            if col in df_dpe.columns:
                colonnes_a_garder[col] = "Adresse Exacte"
                break

        cibles = {
            "Étage": False,
            "N° Apt": False,
            "N° Lot": False,
            "Bâtiment": False,
            "Note DPE": False,
        }

        for col in df_dpe.columns:
            c = col.lower()
            if not cibles["Étage"] and ("etage" in c or "niveau" in c):
                colonnes_a_garder[col] = "Étage"
                cibles["Étage"] = True
            elif not cibles["N° Apt"] and (
                "appartement" in c or "porte" in c or "numero_appt" in c
            ):
                colonnes_a_garder[col] = "N° Apt"
                cibles["N° Apt"] = True
            elif not cibles["N° Lot"] and "lot" in c:
                colonnes_a_garder[col] = "N° Lot"
                cibles["N° Lot"] = True
            elif not cibles["Bâtiment"] and ("batiment" in c or "bat" in c):
                colonnes_a_garder[col] = "Bâtiment"
                cibles["Bâtiment"] = True
            elif not cibles["Note DPE"] and "etiquette" in c and "dpe" in c:
                colonnes_a_garder[col] = "Note DPE"
                cibles["Note DPE"] = True

        df_affichage = df_dpe[list(colonnes_a_garder.keys())].rename(
            columns=colonnes_a_garder
        )

        if "Adresse Exacte" in df_affichage.columns:

            def creer_libelle_bien(row):
                adresse = str(row.get("Adresse Exacte", "")).title()
                bat = formater_numero(row.get("Bâtiment", ""))
                etage = formater_numero(row.get("Étage", ""))
                apt = formater_numero(row.get("N° Apt", ""))
                lot = formater_numero(row.get("N° Lot", ""))
                dpe = str(row.get("Note DPE", "")).strip().upper()

                details = []
                if bat:
                    details.append(f"Bât. {bat}")
                if etage:
                    details.append(f"Étage {etage}")
                if apt:
                    details.append(f"Apt {apt}")
                if lot:
                    details.append(f"Lot {lot}")
                if dpe:
                    details.append(f"DPE {dpe}")

                str_details = " | ".join(details) if details else "Lot standard"
                return f"{adresse} — [{str_details}]"

            df_affichage["Libellé Complet"] = df_affichage.apply(
                creer_libelle_bien, axis=1
            )
            biens_dispos = df_affichage["Libellé Complet"].dropna().unique().tolist()
            biens_dispos.sort()

            bien_choisi = st.selectbox(
                "📍 Sélectionner le bien et son repérage exact :", biens_dispos
            )

            if bien_choisi:
                ligne_bien = df_affichage[
                    df_affichage["Libellé Complet"] == bien_choisi
                ].iloc[0]
                adresse_brute = str(ligne_bien.get("Adresse Exacte", "")).title()
                apt = formater_numero(ligne_bien.get("N° Apt", ""))
                lot = formater_numero(ligne_bien.get("N° Lot", ""))
                etage = formater_numero(ligne_bien.get("Étage", ""))
                bat = formater_numero(ligne_bien.get("Bâtiment", ""))
                note_dpe = str(ligne_bien.get("Note DPE", "")).strip().upper()

                infos_repere = []
                if bat:
                    infos_repere.append(f"Bât. {bat}")
                if etage:
                    infos_repere.append(f"Étage : {etage}")
                if apt:
                    infos_repere.append(f"Apt {apt}")
                if lot:
                    infos_repere.append(f"Lot n° {lot}")
                if note_dpe:
                    infos_repere.append(f"DPE : {note_dpe}")

                str_reperage = (
                    " | ".join(infos_repere) if infos_repere else "Bien identifié"
                )
                date_jour = datetime.now().strftime("%d/%m/%Y")

                st.markdown(
                    f"### 📍 {adresse_brute} — Repérage : `{str_reperage}`"
                )

                courrier_investisseur = f"""Nice, le {date_jour}

Destinataire : Propriétaire / Investisseur Bailleur
Localisation du lot : {str_reperage}
Adresse du bien : {adresse_brute}

Madame, Monsieur,

Objet : Alerte fiscale et stratégie d'arbitrage de votre actif au {adresse_brute} ({str_reperage})

En qualité de Conseil en Immobilier Patrimonial, je me permets de vous contacter de manière confidentielle au sujet du bien dont vous êtes propriétaire dans cet immeuble.

Le marché de l'investissement locatif traverse actuellement une zone de mutation majeure :
1. Les évolutions de la fiscalité (LMNP, régimes réels) et les règles d'amortissement imposent une gestion proactive de vos actifs.
2. Le calendrier de la loi Climat et Résilience maintient ses exigences sur la performance énergétique des biens mis en location.

Avant que ces réglementations ne viennent impacter la rentabilité nette et la valeur vénale de votre lot ({str_reperage}), l'anticipation de votre stratégie patrimoniale est essentielle.

Je me tiens à votre entière disposition pour réaliser un audit confidentiel et étudier avec vous l'opportunité d'un arbitrage ou d'une valorisation optimale.

Bien cordialement,

Nathalie Parra
Conseil en Immobilier Patrimonial

CABINET PRIVÉ IMMOBILIER HONORAT
TRANSACTION . CONSEIL . PATRIMOINE"""

                st.text_area(
                    "📄 Courrier de prospection investisseur personnalisé :",
                    value=courrier_investisseur,
                    height=300,
                )

with tab2:
    st.subheader("🚨 Veille Juridique et Fiscale en Temps Réel")
    st.write(
        "Flux continus des actualités officielles pour sécuriser vos conseils"
        " investisseurs."
    )
    if alertes_en_direct:
        for art in alertes_en_direct:
            st.markdown(f"- **[{art['titre']}]({art['lien']})**")
    else:
        st.info("Aucune alerte récente sur les flux officiels.")
