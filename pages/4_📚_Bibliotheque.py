import streamlit as st

st.set_page_config(
    page_title="Bibliothèque - Cabinet Honorat",
    page_icon="📚",
    layout="wide"
)

st.title("📚 Bibliothèque & Outils Professionnels")
st.markdown("Accès direct aux plateformes officielles d'investigation foncière, juridique et institutionnelle.")

st.markdown("---")

col1, col2 = st.columns(2)

with col1:
    st.subheader("🗺️ Foncier, Cartographie & Cadastre")
    st.markdown(
        """
        * 🌐 [Plan Cadastral Officiel](https://www.cadastre.gouv.fr) : Consultation des plans parcellaires.
        * 🛰️ [Géoportail National](https://www.geoportail.gouv.fr) : Vues aériennes, topographie et données géographiques.
        * 💶 [Demandes de Valeurs Foncières (DVF)](https://app.dvf.etalab.gouv.fr) : Historique officiel des transactions immobilières en France.
        * 🏙️ [Géoportail de l'Urbanisme (GPU)](https://www.geoportail-urbanisme.gouv.fr) : PLU, règlements d'urbanisme et zonages de Nice.
        """
    )
    
    st.subheader("🏢 Entreprises, SCI & R.C.S.")
    st.markdown(
        """
        * 🔍 [Annuaire des Entreprises (API Gouv)](https://annuaire-entreprises.data.gouv.fr) : Recherche rapide de SCI, SIREN et dirigeants.
        * ⚖️ [BODACC](https://www.bodacc.fr) : Bulletins officiels des annonces civiles et commerciales (contrôle des liquidations/cessations).
        * 🏛️ [Infogreffe / Pappers](https://www.pappers.fr) : Analyse financière et juridique des sociétés civiles immobilières.
        """
    )

with col2:
    st.subheader("📜 Veille Juridique & Textes Officiels")
    st.markdown(
        """
        * 🇫🇷 [Service-Public Pro](https://www.service-public.fr/professionnels-entreprises) : Actualités et démarches administratives.
        * 🏛️ [Légifrance](https://www.legifrance.gouv.fr) : Le service public de la diffusion du droit (lois, décrets, codes).
        * 💶 [Impots.gouv.fr (Espace Pro)](https://www.impots.gouv.fr) : Fiscalité foncière, déclarations et régimes LMNP/LMP.
        """
    )
    
    st.subheader("🤝 Partenaires & Professionnels")
    st.markdown(
        """
        * 🏠 [FNAIM Côte d'Azur](https://www.fnaim.fr) : Portail de la fédération immobilière.
        * 📊 [Meilleurs Agents Pro](https://www.meilleursagents.com/pro) : Indices de prix et valorisations sectorielles à Nice.
        * 🏦 [Qonto Pro](https://qonto.com/fr) : Gestion de la trésorerie et facturation du cabinet.
        """
    )

st.markdown("---")
st.info("💡 **Conseil du Cabinet :** Ces liens s'ouvrent directement dans de nouveaux onglets pour faciliter vos recherches de terrain tout en gardant votre application Streamlit active.")

# =====================================================================
# CELLULE DÉDIÉE : SIMULATEUR DE PLUS-VALUE IMMOBILIÈRE & ARBITRAGE
# Cabinet Privé Immobilier Honorat
# =====================================================================

import streamlit as st


def afficher_module_plus_value():
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


# Appel de la fonction pour l'affichage dans la cellule dédiée
afficher_module_plus_value()
