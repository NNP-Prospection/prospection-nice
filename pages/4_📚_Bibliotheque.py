import os
import streamlit as st
from datetime import datetime

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="Bibliothèque - Cabinet Honorat", page_icon="📚", layout="wide"
)

st.title("📚 Bibliothèque & Ressources Stratégiques")
st.markdown(
    "Centralisation des modèles de prospection, de la documentation juridique "
    "et de l'état des bases de données du Cabinet Privé Immobilier Honorat."
)

tab1, tab2, tab3 = st.tabs([
    "✉️ Modèles de Courriers", 
    "⚖️ Mémos Juridiques & Fiscaux", 
    "🗄️ État des Bases de Données"
])

# --- TAB 1 : MODÈLES DE COURRIERS ---
with tab1:
    st.subheader("Gabarits de Prospection (Téléchargeables)")
    
    date_jour = datetime.now().strftime("%d/%m/%Y")
    signature = (
        "Nathalie Parra\n\n"
        "CABINET PRIVÉ IMMOBILIER HONORAT\n"
        "AUDIT . TRANSACTION . CONSEIL\n\n"
        "---\n"
        "*Nathalie Parra — Titulaire de la carte professionnelle CPI délivrée par la CCI Nice Côte d'Azur*\n"
        "*Membre de la FNAIM*"
    )

    with st.expander("1. Stratégie DPE & Impasse Airbnb (Zone 3 Nice)"):
        lettre_airbnb = f"""Nice, le {date_jour}

Objet : Réglementation des meublés de tourisme à Nice, DPE et arbitrage

Madame, Monsieur,

Le durcissement simultané de la réglementation métropolitaine niçoise sur les meublés de tourisme (quotas stricts en Zone 3 hypercentre et obligation de justifier d’un DPE classé entre A et E) et de la fiscalité locative place aujourd’hui de nombreux propriétaires devant un choix stratégique.

Plutôt que de subir une immobilisation locative ou des travaux énergétiques lourds à la rentabilité incertaine, une cession optimisée sur le marché actuel du Carré d’Or permet de cristalliser votre plus-value nette auprès d’acquéreurs ciblés.

Je me tiens à votre disposition pour réaliser un audit confidentiel.

Bien cordialement,

{signature}"""
        st.text_area("Aperçu :", value=lettre_airbnb, height=320, key="txt_airbnb")
        st.download_button("📥 Télécharger (TXT)", data=lettre_airbnb, file_name="Modele_1_Airbnb_DPE.txt")

    with st.expander("2. Stratégie Bailleurs & Appels de Fonds (RNIC)"):
        lettre_rnic = f"""Nice, le {date_jour}

Objet : Évolution énergétique de votre copropriété et étude d’arbitrage

Madame, Monsieur,

Nous observons actuellement une forte activité diagnostique au sein de votre immeuble, signe fréquent d’une réflexion collective sur la rénovation énergétique ou le ravalement.

Dans les immeubles bourgeois niçois, le vote d’appels de fonds importants en Assemblée Générale pèse directement sur le rendement net des copropriétaires bailleurs. Étudier la valorisation de votre lot en amont de ces échéances vous permet d’arbitrer sereinement et de préserver votre capital.

Je me tiens à votre entière disposition pour un audit confidentiel de votre lot.

Bien cordialement,

{signature}"""
        st.text_area("Aperçu :", value=lettre_rnic, height=320, key="txt_rnic")
        st.download_button("📥 Télécharger (TXT)", data=lettre_rnic, file_name="Modele_2_Bailleurs_RNIC.txt")

    with st.expander("3. Stratégie SCI & Arbitrage Retraite (Exonération PV)"):
        lettre_sci = f"""Nice, le {date_jour}

À l'attention de la Gérance

Objet : Cristallisation de vos plus-values et optimisation de vos parts sociales

Madame, Monsieur le Gérant,

Après plusieurs années de détention, votre actif bénéficie désormais d'un abattement significatif sur la plus-value immobilière. 

À l'approche de la retraite ou dans une optique de transmission, la gestion locative devient souvent chronophage et la rentabilité nette s'érode. C'est le moment idéal pour envisager de cristalliser cette plus-value exonérée et de restructurer vos actifs.

Je me tiens à votre disposition pour chiffrer la valeur vénale actuelle de votre bien ainsi que la plus-value nette d'impôt en cas de cession.

Bien cordialement,

{signature}"""
        st.text_area("Aperçu :", value=lettre_sci, height=320, key="txt_sci")
        st.download_button("📥 Télécharger (TXT)", data=lettre_sci, file_name="Modele_3_SCI_Retraite.txt")

    with st.expander("4. Stratégie Successions & Ayants Droit (INSEE/BODACC)"):
        lettre_succ = f"""Nice, le {date_jour}

Objet : Accompagnement successoral et estimation de votre bien

Madame, Monsieur,

Dans le cadre du règlement d'une succession ou d'une indivision, l'évaluation précise des actifs immobiliers est une étape déterminante, tant pour le notaire que pour la déclaration fiscale.

Spécialisé dans l'accompagnement des ayants droit sur les biens de caractère à Nice, notre Cabinet se tient à votre entière disposition pour réaliser un audit de valeur vénale objectif. Nous prenons en compte les dernières réglementations pour vous fournir un dossier d'estimation complet.

Démarche confidentielle et respectueuse des situations familiales garantie.

Bien cordialement,

{signature}"""
        st.text_area("Aperçu :", value=lettre_succ, height=320, key="txt_succ")
        st.download_button("📥 Télécharger (TXT)", data=lettre_succ, file_name="Modele_4_Successions.txt")

    with st.expander("5. Stratégie Droit des Sols & Valorisation (Sitadel2)"):
        lettre_urba = f"""Nice, le {date_jour}

Objet : Valorisation de votre projet immobilier et création de valeur

Madame, Monsieur,

La modification d'un actif immobilier (division parcellaire, changement de destination, surélévation) est une excellente stratégie de création de valeur qui modifie le positionnement de votre bien sur le marché niçois.

Forte d'une parfaite connaissance des dynamiques locales, je vous propose une étude de commercialisation sur-mesure pour votre projet. Cette évaluation prendra en compte la rareté de ces surfaces restructurées sur votre secteur et les attentes des investisseurs.

Je me tiens à votre disposition pour évaluer cette plus-value potentielle.

Bien cordialement,

{signature}"""
        st.text_area("Aperçu :", value=lettre_urba, height=320, key="txt_urba")
        st.download_button("📥 Télécharger (TXT)", data=lettre_urba, file_name="Modele_5_Urbanisme.txt")

# --- TAB 2 : MÉMOS JURIDIQUES ---
with tab2:
    st.subheader("Mémos Réglementaires (Nice & National)")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### 🚫 Réglementation Meublés de Tourisme (Nice)")
        st.info(
            "**Zone 3 (Hypercentre / Carré d'Or / Port) :**\n"
            "- Quota strict sur les changements d'usage.\n"
            "- Renouvellement d'autorisation limité.\n"
            "- **Obligation DPE :** Classe A à E exigée pour toute nouvelle autorisation ou renouvellement.\n"
            "- **Impact Marché :** Blocage des petites surfaces (F/G) destinées à la location saisonnière."
        )
        
        st.markdown("#### 🌍 Calendrier DPE (Loi Climat)")
        st.warning(
            "- **1er janvier 2025 :** Interdiction de location des logements classés **G**.\n"
            "- **1er janvier 2028 :** Interdiction de location des logements classés **F**.\n"
            "- **1er janvier 2034 :** Interdiction de location des logements classés **E**."
        )

    with col2:
        st.markdown("#### 💶 Fiscalité Plus-Value Immobilière")
        st.success(
            "**Abattements pour durée de détention :**\n"
            "- **Impôt sur le revenu (19%) :** Exonération totale après **22 ans**.\n"
            "- **Prélèvements sociaux (17.2%) :** Exonération totale après **30 ans**.\n"
            "- *Rappel :* Surtaxe applicable pour les plus-values nettes imposables supérieures à 50 000 €."
        )
        
        st.markdown("#### 🏗️ Urbanisme & Cadre Local (Nice 06000)")
        st.info(
            "- **Secteur Sauvegardé / SPR :** Hyper-centre, Vieux-Nice, Port.\n"
            "- **Délais d'instruction majorés :** +1 mois pour consultation des Architectes des Bâtiments de France.\n"
            "- **Changement de destination :** DP requise (sans modification façade) ou PC (si modification structures porteuses/façade)."
        )

# --- TAB 3 : ÉTAT DES DONNÉES ---
with tab3:
    st.subheader("Vérification de l'environnement de travail (Data)")
    st.write("Statut des fichiers CSV nécessaires au fonctionnement optimal des 5 stratégies :")
    
    fichiers_attendus = {
        "Base DPE (dpe_nice_*.csv)": ['dpe_nice_complet.csv', 'dpe_nice_part_1.csv', 'dpe_nice_fg.csv'],
        "Base Ventes (Dossier DVF / *dvf*.csv)": ['dvf'],
        "Base Copropriétés (*rnic*.csv / *copro*.csv)": ['rnic', 'copro'],
        "Base Logements Vacants (*lovac*.csv / *vacant*.csv)": ['lovac', 'vacant'],
        "Base Sociétés / SCI (*sci*.csv / *sirene*.csv)": ['sci', 'sirene'],
        "Base Décès INSEE (*deces*.csv / *insee*.csv)": ['deces', 'insee'],
        "Base Mutations BODACC (*bodacc*.csv / *mutation*.csv)": ['bodacc', 'mutation'],
        "Base Urbanisme Sitadel (*sitadel*.csv / *urba*.csv)": ['sitadel', 'urbanisme']
    }

    fichiers_presents = os.listdir('.')
    
    for nom_base, mots_cles in fichiers_attendus.items():
        trouve = False
        if nom_base == "Base Ventes (Dossier DVF / *dvf*.csv)":
            trouve = any(os.path.isdir(f) and 'dvf' in f.lower() for f in fichiers_presents)
        else:
            trouve = any(any(mot in f.lower() for mot in mots_cles) for f in fichiers_presents if f.endswith('.csv'))
            
        if trouve:
            st.success(f"✅ **{nom_base}** : Détectée et opérationnelle.")
        else:
            st.error(f"❌ **{nom_base}** : Manquante. Chargez ce fichier pour activer la stratégie correspondante.")
