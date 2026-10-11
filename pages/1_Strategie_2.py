import streamlit as st
import pandas as pd
from datetime import datetime
import os
import requests
import xml.etree.ElementTree as ET

st.set_page_config(
    page_title="Stratégie 2 - Investisseurs", 
    page_icon="💼",
    layout="wide"
)

st.title("💼 Stratégie 2 : Investisseurs & Veille Juridique Continue")
st.markdown("Ciblage des fins de cycles fiscaux et alertes en direct sur les évolutions législatives.")

# --- CHARGEMENT DPE ---
@st.cache_data
def load_dpe():
    try:
        return pd.read_csv('dpe_nice_fg.csv', low_memory=False)
    except:
        return pd.DataFrame()

df_dpe = load_dpe()

# --- MOTEUR DE VEILLE JURIDIQUE EN TEMPS RÉEL ---
@st.cache_data(ttl=3600)
def fetch_veille_juridique():
    flux_officiels = [
        "https://www.service-public.fr/professionnels-entreprises/actualites/rss",
        "https://www.service-public.fr/particuliers/actualites/rss"
    ]
    articles_trouves = []
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    for url in flux_officiels:
        try:
            reponse = requests.get(url, headers=headers, timeout=5)
            if reponse.status_code == 200:
                root = ET.fromstring(reponse.content)
                for item in root.findall('.//item'):
                    titre = item.find('title').text if item.find('title') is not None else ""
                    lien = item.find('link').text if item.find('link') is not None else ""
                    
                    mots_cles_immo = ['loi', 'immobilier', 'logement', 'dpe', 'fiscal', 'impôt', 'bail', 'lmnp', 'pinel', 'copropriété', 'énergie', 'taxe', 'finance', 'plus-value']
                    is_alerte = any(mot in titre.lower() for mot in mots_cles_immo)
                    
                    if is_alerte:
                        articles_trouves.append({'titre': titre, 'lien': lien})
        except:
            pass
            
    articles_uniques = []
    liens_vus = set()
    for art in articles_trouves:
        if art['lien'] not in liens_vus:
            articles_uniques.append(art)
            liens_vus.add(art['lien'])
            
    return articles_uniques[:8]

alertes_en_direct = fetch_veille_juridique()

# --- BARRE LATÉRALE : CRITÈRES DE CIBLAGE ---
st.sidebar.header("🎯 Critères de ciblage Investisseurs")

secteur = st.sidebar.selectbox(
    "Quartier / Secteur",
    ["Tous les secteurs", "Carré d'Or", "Promenade des Anglais", "Port / Garibaldi", "Mont Boron", "Musiciens / Gambetta", "Centre-ville"]
)

# --- AFFICHAGE DES ONGLETS ---
tab1, tab2 = st.tabs(["✉️ 1. Publipostage Investisseurs", "🚨 2. Veille Juridique en Temps Réel"])

with tab1:
    st.subheader("Ciblage des investisseurs : Fin d'avantage fiscal + Décote DPE")
    st.write("Ce courrier est optimisé pour les propriétaires bailleurs (LMNP, LMP, Pinel) qui arrivent en fin de cycle de détention et font face aux nouvelles mesures coercitives.")
    
    if not df_dpe.empty:
        col_adresse = next((col for col in ['adresse_ban', 'adresse_brute', 'adresse_propriete'] if col in df_dpe.columns), None)
        
        if col_adresse:
            df_travail = df_dpe.copy()
            
            # --- FILTRE PAR SECTEUR RETABLI ---
            if secteur != "Tous les secteurs":
                rues_quartiers = {
                    "Carré d'Or": ["france", "massena", "paradis", "suede", "verdun", "meyerbeer", "congres", "cronstadt"],
                    "Promenade des Anglais": ["promenade des anglais", "etats-unis", "quai des etats-unis"],
                    "Port / Garibaldi": ["garibaldi", "lunel", "cassini", "barla", "arson", "republique", "port"],
                    "Mont Boron": ["mont boron", "jean lorrain", "carnot", "germaine", "andre joly", "valrose", "cap de nice"],
                    "Musiciens / Gambetta": ["gambetta", "berlioz", "gounod", "rossini", "verdi", "clemenceau", "victor hugo"],
                    "Centre-ville": ["jean medecin", "gioffredo", "marechal foch", "pastorelli", "assalit", "durandy"]
                }
                mots_cles = rues_quartiers.get(secteur, [])
                if mots_cles:
                    pattern = '|'.join(mots_cles)
                    df_travail = df_travail[df_travail[col_adresse].astype(str).str.lower().str.contains(pattern, na=False, regex=True)]

            adresses_dispos = df_travail[col_adresse].dropna().unique().tolist()
            adresses_dispos.sort()
            
            if adresses_dispos:
                adresse_choisie = st.selectbox(f"📍 Choisir une adresse ({secteur}) :", adresses_dispos)
                
                date_jour = datetime.now().strftime("%d/%m/%Y")
                adresse_propre = adresse_choisie.title() if adresse_choisie else ""
                
                courrier_investisseur = f"""Nice, le {date_jour}

Destinataire : Propriétaire / Investisseur Bailleur
Concerne l'actif situé au : {adresse_propre}

Madame, Monsieur,

Objet : Alerte fiscale PLF 2027 et stratégie d'arbitrage de votre actif au {adresse_propre}

En qualité de Conseil en Immobilier Patrimonial, je me permets de vous contacter de manière confidentielle au sujet du bien que vous proposez à la location.

Le marché de l'investissement locatif traverse actuellement une zone de turbulence majeure :
1. Le Projet de Loi de Finances (PLF) pour 2027 prévoit un plafonnement drastique des amortissements liés au statut LMNP (limités à 2,5 % par an et 7 000 € maximum). Les amortissements non déduits risquent d'être définitivement perdus.
2. La Loi Climat maintient son calendrier strict : interdiction de mise en location imminente pour les biens les plus énergivores, imposant des travaux de rénovation globaux à la charge du bailleur.

Avant que ces nouvelles réglementations ne soient définitivement promulguées et ne viennent amputer la rentabilité et la valeur vénale de votre bien, l'anticipation est votre meilleur atout. 

Je vous propose de réaliser un audit gratuit et confidentiel de votre situation afin d'étudier l'opportunité d'un arbitrage ou d'une revente stratégique avant la fin de l'année.

Bien cordialement,

Nathalie Parra
Conseil en Immobilier Patrimonial

CABINET PRIVÉ IMMOBILIER HONORAT
TRANSACTION . CONSEIL . PATRIMOINE"""

                st.text_area(f"📄 Modèle de courrier (Actualisé Loi Finance)", courrier_investisseur, height=400)
                logo_path = "Cabinet Immobilier Privé HONORAT.png"
                if os.path.exists(logo_path): 
                    st.image(logo_path, width=200)
            else:
                st.warning(f"⚠️ Aucune adresse trouvée pour le secteur : **{secteur}**.")

with tab2:
    st.subheader("📡 Flux d'Actualités Officielles (Mis à jour automatiquement)")
    st.write("Votre application scanne en direct les publications de l'État pour détecter les nouveautés liées à l'immobilier, au logement et à la fiscalité.")
    
    if alertes_en_direct:
        for alerte in alertes_en_direct:
            st.error(f"🚨 **LANTERNE ROUGE NOUVELLE LOI/MESURE :** [{alerte['titre']}]({alerte['lien']})")
    else:
        st.success("✅ Aucun nouveau décret ou loi majeure impactant l'immobilier détecté aujourd'hui sur les flux officiels.")
        
    st.markdown("---")
    st.subheader("📌 Dossiers Chauds & Argumentaires en cours")
    
    with st.expander("🚨 DOSSIER PRIORITAIRE : Projet de Loi de Finances (PLF) 2027", expanded=True):
        st.markdown("""
        **L'argumentaire à donner d'urgence à vos clients (S'applique dès le 1er janvier 2027 si voté) :**
        *   **Plafonnement des amortissements LMNP :** L'article 7 du PLF prévoit de limiter la déduction de l'amortissement des locaux au régime réel à **2,5 % par an et 7 000 € par foyer fiscal** (et même 1,5 % et 5 000 € pour les meublés de tourisme). Un client avec un bien de 300 000 € va perdre une part massive de son avantage fiscal.
        *   **Fin du report illimité :** C'est la mesure la plus punitive. Aujourd'hui, un amortissement non utilisé est reportable. Demain (dès 2027), les amortissements écartés par le nouveau plafond seraient **définitivement perdus**. 
        *   **Action requise :** "Monsieur le client, il faut revendre avant le 31 décembre 2026 pour sécuriser votre capital avant que les acheteurs n'intègrent cette perte de rentabilité dans leurs offres."
        *   **Bonne nouvelle (Nouveau Dispositif Jeanbrun) :** Le statut de bailleur privé vient d'être voté. Il permet d'amortir un logement loué **nu** en contrepartie d'un loyer encadré sur 9 ans. Une excellente piste de réinvestissement post-revente.
        """)

    with st.expander("📝 Rappel Climat & Dispositifs en fin de vie (Pinel, DPE)"):
        st.markdown("""
        *   **DPE 2027 :** Le coefficient d'énergie primaire de l'électricité passera à 1,7 en 2027. Cela pourrait légèrement améliorer la note de certains biens chauffés à l'électrique.
        *   **Calendrier des interdictions de louer :** G (1er janvier 2025), F (1er janvier 2028), E (1er janvier 2034).
        *   **Loi Pinel :** Le dispositif s'est éteint fin 2024. Les investisseurs Pinel arrivant au terme de leur engagement (6 ou 9 ans) n'ont **plus aucun avantage fiscal** à conserver le bien.
        """)
