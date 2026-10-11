from datetime import datetime
import pandas as pd
import streamlit as st

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="Bibliothèque & Outils Professionnels - Cabinet Honorat",
    page_icon="📚",
    layout="wide",
)

st.title("📚 Bibliothèque & Outils Professionnels - Cabinet Honorat")
st.markdown(
    "Accès direct aux plateformes officielles d'investigation foncière,"
    " juridique et aux simulateurs experts du Cabinet."
)

# --- NAVIGATION INTERNE VIA LA BARRE LATÉRALE ---
module_choisi = st.sidebar.selectbox(
    "Choisir un module",
    [
        "🗺️ Liens & Ressources Officielles",
        "📊 Module Expert : Plus-Value & Arbitrage",
        "🏛️ Simulateur Dispositif Jeanbrun (Bailleur Privé)",
        "⚖️ Guide & Arsenal Fiscal (Pinel, Denormandie, Malraux, LMNP/LMP)",
    ],
)

if module_choisi == "🗺️ Liens & Ressources Officielles":
  st.markdown("---")

  col1, col2 = st.columns(2)

  with col1:
    st.subheader("🗺️ Foncier, Cartographie & Cadastre")
    st.markdown("""
        * 🌐 [Plan Cadastral Officiel](https://www.cadastre.gouv.fr) : Consultation des plans parcellaires.
        * 🛰️ [Géoportail National](https://www.geoportail.gouv.fr) : Vues aériennes, topographie et données géographiques.
        * 💶 [Demandes de Valeurs Foncières (DVF)](https://app.dvf.etalab.gouv.fr) : Historique officiel des transactions immobilières en France.
        * 🏙️ [Géoportail de l'Urbanisme (GPU)](https://www.geoportail-urbanisme.gouv.fr) : PLU, règlements d'urbanisme et zonages de Nice.
        """)

    st.subheader("🏢 Entreprises, SCI & R.C.S.")
    st.markdown("""
        * 🔍 [Annuaire des Entreprises (API Gouv)](https://annuaire-entreprises.data.gouv.fr) : Recherche rapide de SCI, SIREN et dirigeants.
        * ⚖️ [BODACC](https://www.bodacc.fr) : Bulletins officiels des annonces civiles et commerciales (contrôle des liquidations/cessations).
        * 🏛️ [Infogreffe / Pappers](https://www.pappers.fr) : Analyse financière et juridique des sociétés civiles immobilières.
        """)

  with col2:
    st.subheader("📜 Veille Juridique & Textes Officiels")
    st.markdown("""
        * 🇫🇷 [Service-Public Pro](https://www.service-public.fr/professionnels-entreprises) : Actualités et démarches administratives.
        * 🏛️ [Légifrance](https://www.legifrance.gouv.fr) : Le service public de la diffusion du droit (lois, décrets, codes).
        * 💶 [Impots.gouv.fr (Espace Pro)](https://www.impots.gouv.fr) : Fiscalité foncière, déclarations et régimes LMNP/LMP.
        """)

    st.subheader("🤝 Partenaires & Professionnels")
    st.markdown("""
        * 🏠 [FNAIM Côte d'Azur](https://www.fnaim.fr) : Portail de la fédération immobilière.
        * 📊 [Meilleurs Agents Pro](https://www.meilleursagents.com/pro) : Indices de prix et valorisations sectorielles à Nice.
        * 🏦 [Qonto Pro](https://qonto.com/fr) : Gestion de la trésorerie et facturation du cabinet.
        """)

  st.markdown("---")
  st.info(
      "💡 **Conseil du Cabinet :** Ces liens s'ouvrent directement dans de"
      " nouveaux onglets pour faciliter vos recherches de terrain tout en"
      " gardant votre application Streamlit active."
  )

elif module_choisi == "📊 Module Expert : Plus-Value & Arbitrage":
  st.subheader(
      "📊 Module Expert : Simulateur de Plus-Value Immobilière & Arbitrage"
  )
  st.markdown(
      "Calculez précisément l'impôt sur le revenu (19%) et les prélèvements"
      " sociaux (17,2%) en tenant compte du point de bascule des abattements"
      " pour durée de détention (à partir de la 6e année)."
  )

  col1, col2 = st.columns(2)

  with col1:
    prix_acquisition = st.number_input(
        "Prix d'acquisition initial (€)",
        min_value=0.0,
        value=200000.0,
        step=5000.0,
        key="pv_acq",
    )
    frais_acquisition_type = st.radio(
        "Frais d'acquisition",
        ["Forfait (7.5%)", "Frais réels notaire"],
        key="pv_frais_type",
    )
    if frais_acquisition_type == "Forfait (7.5%)":
      frais_acq = prix_acquisition * 0.075
    else:
      frais_acq = st.number_input(
          "Montant réel des frais d'acquisition (€)",
          min_value=0.0,
          value=15000.0,
          step=1000.0,
          key="pv_frais_reel",
      )

    duree_detention = st.number_input(
        "Durée de détention (en années complètes)",
        min_value=0,
        max_value=50,
        value=5,
        step=1,
        key="pv_duree",
    )

    travaux_type = st.radio(
        "Travaux",
        [
            "Aucun / Forfait 15% (si détention > 5 ans)",
            "Montant réel sur factures",
        ],
        key="pv_travaux_type",
    )
    if (
        travaux_type == "Aucun / Forfait 15% (si détention > 5 ans)"
        and duree_detention > 5
    ):
      travaux = prix_acquisition * 0.15
    elif travaux_type == "Montant réel sur factures":
      travaux = st.number_input(
          "Montant total des travaux TTC (sur factures)",
          min_value=0.0,
          value=0.0,
          step=1000.0,
          key="pv_travaux_reel",
      )
    else:
      travaux = 0.0

  with col2:
    prix_cession = st.number_input(
        "Prix de cession envisagé (Net vendeur) (€)",
        min_value=0.0,
        value=300000.0,
        step=5000.0,
        key="pv_cession",
    )
    frais_cession = st.number_input(
        "Frais de cession (honoraires agence, diagnostics) (€)",
        min_value=0.0,
        value=15000.0,
        step=1000.0,
        key="pv_frais_cession",
    )

  # Calcul de l'assiette brute
  total_acquisition = prix_acquisition + frais_acq + travaux
  net_cession = prix_cession - frais_cession
  plus_value_brute = max(0.0, net_cession - total_acquisition)

  # Calcul des abattements pour durée de détention
  # 1. Impôt sur le revenu (19%)
  if duree_detention <= 5:
    abattement_ir = 0.0
  elif duree_detention <= 21:
    abattement_ir = (duree_detention - 5) * 0.06
  elif duree_detention == 22:
    abattement_ir = 1.0  # 100% exonéré IR
  else:
    abattement_ir = 1.0

  # 2. Prélèvements sociaux (17,2%)
  if duree_detention <= 5:
    abattement_ps = 0.0
  elif duree_detention <= 21:
    abattement_ps = (duree_detention - 5) * 0.0165
  elif duree_detention == 22:
    abattement_ps = (16 * 0.0165) + 0.0160
  elif duree_detention <= 30:
    annees_sup_22 = duree_detention - 22
    abattement_ps = (16 * 0.0165) + 0.0160 + (annees_sup_22 * 0.09)
    abattement_ps = min(1.0, abattement_ps)
  else:
    abattement_ps = 1.0  # 100% exonéré PS

  # Montants imposables et impôts
  pv_imposable_ir = plus_value_brute * (1.0 - abattement_ir)
  pv_imposable_ps = plus_value_brute * (1.0 - abattement_ps)

  impot_ir = pv_imposable_ir * 0.19
  impots_sociaux = pv_imposable_ps * 0.172
  total_taxe = impot_ir + impots_sociaux

  st.markdown("---")
  st.metric("💰 Plus-Value Brute", f"{plus_value_brute:,.2f} €")

  col_res1, col_res2, col_res3 = st.columns(3)
  with col_res1:
    st.metric(
        "Impôt sur le Revenu (19%)",
        f"{impot_ir:,.2f} €",
        help=f"Abattement IR appliqué : {abattement_ir*100:.1f}%",
    )
  with col_res2:
    st.metric(
        "Prélèvements Sociaux (17,2%)",
        f"{impots_sociaux:,.2f} €",
        help=f"Abattement PS appliqué : {abattement_ps*100:.1f}%",
    )
  with col_res3:
    st.metric(
        "Total Impôts & Taxes",
        f"{total_taxe:,.2f} €",
        delta=f"-{(total_taxe/plus_value_brute*100) if plus_value_brute > 0 else 0:.1f}% de la PV",
        delta_color="inverse",
    )

  st.info(
      f"📌 **Synthèse de l'Analyse Patrimoniale :** Pour une détention de"
      f" **{duree_detention} ans**, l'abattement sur l'impôt sur le revenu est"
      f" de **{abattement_ir*100:.1f}%** et celui sur les prélèvements sociaux"
      f" est de **{abattement_ps*100:.1f}%**. "
      + (
          "⚠️ *Attention : À 5 ans ou moins, l'abattement est nul (0%). Le"
          " propriétaire subit la fiscalité au taux plein de 36,2%.*"
          if duree_detention <= 5
          else "✅ *Le cap des 5 ans est franchi : la décote fiscale commence à"
          " minorer l'impôt, optimisant ainsi le gain net de l'arbitrage.*"
      )
  )

elif module_choisi == "🏛️ Simulateur Dispositif Jeanbrun (Bailleur Privé)":
  st.header("🏛️ Simulateur du Dispositif Jeanbrun (Statut de Bailleur Privé)")
  st.markdown(
      "Estimez l’avantage fiscal et l’amortissement d’un logement loué nu sous"
      " le régime du bailleur privé (engagement 9 ans avec loyer maîtrisé)."
  )

  col1, col2 = st.columns(2)

  with col1:
    valeur_bien = st.number_input(
        "Valeur d'acquisition du bien (€)",
        min_value=50000,
        max_value=5000000,
        value=300000,
        step=10000,
    )
    travaux = st.number_input(
        "Montant des travaux de rénovation (€)",
        min_value=0,
        max_value=500000,
        value=30000,
        step=5000,
    )
    loyer_mensuel = st.number_input(
        "Loyer mensuel estimé (€)",
        min_value=200,
        max_value=10000,
        value=1200,
        step=50,
    )

  with col2:
    tranche_tmi = st.selectbox(
        "Tranche Marginale d’Imposition (TMI)", [11, 30, 41, 45], index=1
    )
    duree_engagement = st.selectbox(
        "Durée d'engagement locatif", ["9 ans (Standard)", "12 ans (Majoré)"]
    )
    niveau_loyer = st.selectbox(
        "Niveau de décote du loyer (par rapport au marché)",
        ["Intermédiaire (15%)", "Social / Très social (30%+)"],
    )

  if st.button("Calculer la simulation Jeanbrun", type="primary"):
    investissement_total = valeur_bien + travaux
    taux_amortissement = 0.035
    base_amortissable = (valeur_bien * 0.8) + travaux
    amortissement_annuel = base_amortissable * taux_amortissement
    loyer_annuel = loyer_mensuel * 12
    rentabilite_brute = (loyer_annuel / investissement_total) * 100

    st.markdown("---")
    st.subheader("📊 Résultats de la Simulation")

    m1, m2, m3 = st.columns(3)
    m1.metric(
        "Investissement Global",
        f"{investissement_total:,.0f} €".replace(",", " "),
    )
    m2.metric("Rentabilité Brute", f"{rentabilite_brute:.2f} %")
    m3.metric(
        "Amortissement Annuel Déductible",
        f"{amortissement_annuel:,.0f} €".replace(",", " "),
    )

    st.info(
        f"💡 **Analyse du Cabinet Honorat :** Sous le régime du bailleur privé"
        f" (Dispositif Jeanbrun), pour un investissement de"
        f" {investissement_total:,.0f} €, l'amortissement annuel de"
        f" {amortissement_annuel:,.0f} € vient optimiser fiscalement vos"
        " revenus fonciers sur la durée de l’engagement."
    )

else:
  st.header("⚖️ Guide & Arsenal Fiscal des Dispositifs Immobiliers")
  st.markdown(
      "Panorama complet et stratégique des dispositifs d'investissement locatif"
      " et de défiscalisation (Pinel, Denormandie, Malraux, Monuments"
      " Historiques, LMNP/LMP)."
  )

  tab_pinel, tab_denormandie, tab_malraux, tab_lmnp = st.tabs([
      "📌 Pinel (Fin de cycle & Arbitrage)",
      "🏡 Denormandie (Ancien Rénové)",
      "🏛️ Malraux & Monuments Historiques",
      "🛋️ LMNP / LMP & Veille Fiscale",
  ])

  with tab_pinel:
    st.subheader("Dispositif Pinel (Extinction & Fins d'Engagement)")
    st.markdown("""
        * **Contexte :** Le dispositif Pinel s'achève définitivement. De nombreux investisseurs arrivent au terme de leur engagement (6, 9 ou 12 ans).
        * **Opportunité pour le Cabinet Honorat :** C'est le moment idéal pour proposer un audit patrimonial aux propriétaires bailleurs dont l'avantage fiscal s'éteint, afin de basculer sur un arbitrage, une revente (plus-value) ou un réinvestissement (ex: Statut de Bailleur Privé / Jeanbrun).
        """)

  with tab_denormandie:
    st.subheader("Dispositif Denormandie (Rénovation dans l'Ancien)")
    st.markdown("""
        * **Cible :** Logements anciens situés dans les communes labellisées "Cœur de Ville" ou ayant signé une Opération de Revitalisation du Territoire (ORT).
        * **Avantage :** Réduction d'impôt sur le revenu équivalente au Pinel (jusqu'à 21% sur 12 ans), à condition que les travaux représentent au moins 25% du coût total de l'opération.
        """)

  with tab_malraux:
    st.subheader("Loi Malraux & Monuments Historiques (Patrimoine d'Exception)")
    st.markdown("""
        * **Loi Malraux :** Restauration d'immeubles bâtis situés dans les Quartiers Antiques Remarquables (QAD) ou Sites Remarquables. Réduction d'impôt de 22% à 30% du montant des travaux, **hors plafonnement global des niches fiscales** (plafond de 400 000 € sur 4 ans).
        * **Monuments Historiques :** Déduction intégrale des charges foncières et des travaux sur le revenu global sans aucun plafond. Un outil puissant pour les contribuables fortement fiscalisés (TMI 41% - 45%).
        """)

  with tab_lmnp:
    st.subheader(
        "LMNP / LMP (Loueur Meublé Non Professionnel / Professionnel)"
    )
    st.markdown("""
        * **Régime Réel :** Amortissement du bien immobilier, des travaux et du mobilier, permettant d'annuler ou de fortement réduire l'imposition des loyers perçus (BIC).
        * **Veille Juridique & Fiscale :** En lien direct avec votre module de veille, le cabinet surveille de près les évolutions réglementaires (comme les projets de plafonnement des amortissements dans le cadre des lois de finances) pour conseiller au mieux les investisseurs.
        """)
