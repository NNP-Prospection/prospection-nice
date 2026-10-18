import streamlit as st
import pandas as pd
from datetime import date



# ==============================================================================
# PENSE-BÊTE / LEXIQUE D'INGÉNIERIE PATRIMONIALE IMMOBILIÈRE (CGP)
# ==============================================================================
LEXIQUE_PATRIMONIAL_CGP = {
    "ROE": {
        "nom": "Rendement sur Fonds Propres (Return on Equity)",
        "definition": "Pourcentage de gain réel rapporté par le capital net bloqué dans le bien.",
        "utilite_rdv": "Démontrer au client que si son ROE tombe sous 2%, son capital dormant perd de la valeur face à un réemploi à 5%."
    },
    "Capital Net Immobilisé": {
        "nom": "Equity Nette Vendeur",
        "definition": "Somme nette disponible sur le compte en cas de vente immédiate.",
        "formule": "Valeur Vénale Nette Vendeur - Capital Restant Dû (CRD) - Impôt sur la Plus-Value - IRA"
    },
    "Bouclier +22,5 %": {
        "nom": "Majoration Forfaitaire du Prix d'Acquisition (Art. 150 VB CGI)",
        "definition": "Après 5 ans de détention, le prix d'achat est majoré de +7,5 % (forfait frais) et +15 % (forfait travaux) sans justificatif.",
        "utilite_rdv": "Permet à un propriétaire en Pinel de vendre jusqu'à +22,5 % au-dessus de son prix d'achat avec 0 € d'impôt de plus-value."
    },
    "CRD": {
        "nom": "Capital Restant Dû",
        "definition": "Montant total de la dette restant à rembourser à la banque.",
        "source": "Tableau d'amortissement de l'emprunt bancaire."
    },
    "IMP": {
        "nom": "Impôt sur la Plus-Value Immobilière",
        "definition": "Taxe sur la plus-value brute (Prix de vente - Prix d'acquisition majoré et corrigé).",
        "majoration": "Forfait frais d'acquisition (7,5 %) + Forfait travaux (15 % si bien > 5 ans)."
    },
    "Cash-Flow Net": {
        "nom": "Trésorerie Nette Après Impôts",
        "definition": "Flux de trésorerie réel généré ou absorbé chaque mois par le bien.",
        "formule": "Loyers - Charges (foncière, copro, PNO) - Mensualité crédit - Impôt sur les loyers."
    },
    "Capital Bancaire": {
        "nom": "Capital Amorti / Épargne Forcée",
        "definition": "Part de la mensualité de crédit qui rembourse le capital (et non les intérêts).",
        "regle": "S'ajoute au cash-flow pour mesurer l'enrichissement réel de l'année."
    },
    "BIC": {
        "nom": "Bénéfices Industriels et Commerciaux",
        "definition": "Catégorie fiscale de la location meublée (LMNP).",
        "avantage": "Permet de déduire l'amortissement comptable du bien et du mobilier (Art. 39 C CGI)."
    },
    "TMI": {
        "nom": "Tranche Marginale d'Imposition",
        "definition": "Taux personnel d'impôt sur le revenu du client (0%, 11%, 30%, 41%, 45%).",
        "cumul": "S'ajoute toujours aux 17,2 % de prélèvements sociaux en location nue ou BIC."
    },
    "Abattement IR (22 ans)": {
        "nom": "Exonération Impôt sur le Revenu Plus-Value",
        "definition": "Acquisition progressive d'abattements sur la plus-value immobilière (6%/an de la 6e à la 21e année, 4% la 22e).",
        "seuil": "Exonération totale de l'impôt (19 %) atteinte au bout de 22 ans de détention."
    },
    "Abattement PS (30 ans)": {
        "nom": "Exonération Prélèvements Sociaux Plus-Value",
        "definition": "Diminution progressive des prélèvements sociaux (1,65%/an de 6 à 21 ans, 1,6% la 22e, 9%/an de 23 à 30 ans).",
        "seuil": "Exonération totale (17,2 %) atteinte au bout de 30 ans de détention."
    },
    "Nom Propre": {
        "nom": "Détention en Personne Physique",
        "definition": "Propriété directe du bien par le particulier (ou en indivision), hors structure sociétaire."
    },
    "SCI à l'IR": {
        "nom": "Société Civile Immobilière à l'Impôt sur le Revenu",
        "definition": "Structure transparente fiscalement : les associés paient l'impôt selon leur TMI et leur quote-part.",
        "piege": "Impossibilité de passer en meublé (> 10 % recettes) sans basculer de force à l'IS (Art. 206-2 CGI)."
    }
}


# ==============================================================================
# MOTEUR DE CALCUL FISCAL & PATRIMONIAL (NORMES 2026)
# ==============================================================================

def calcul_abattements_pv(annees_detention: int) -> tuple[float, float]:
    """
    Calcule les taux d'abattement pour durée de détention (régime des particuliers, Art. 150 VC CGI).
    Retourne (abattement_ir, abattement_ps) entre 0.0 et 1.0.
    """
    if annees_detention <= 5:
        return 0.0, 0.0

    # Abattement Impôt sur le Revenu (Exonération totale à 22 ans)
    if annees_detention >= 22:
        abatt_ir = 1.0
    else:
        abatt_ir = (annees_detention - 5) * 0.06

    # Abattement Prélèvements Sociaux (Exonération totale à 30 ans)
    if annees_detention >= 30:
        abatt_ps = 1.0
    elif annees_detention <= 21:
        abatt_ps = (annees_detention - 5) * 0.0165
    elif annees_detention == 22:
        abatt_ps = (16 * 0.0165) + 0.0160
    else:
        abatt_ps = (16 * 0.0165) + 0.0160 + ((annees_detention - 22) * 0.09)

    return min(1.0, abatt_ir), min(1.0, abatt_ps)


def calcul_surtaxe_pv(pv_imposable_ir: float) -> float:
    """
    Calcule la surtaxe sur les plus-values immobilières élevées (> 50 000 €)
    selon l'article 1609 nonies G du CGI avec formules officielles de lissage.
    """
    pv = pv_imposable_ir
    if pv <= 50000:
        return 0.0
    elif pv <= 60000:
        return 0.02 * pv - (60000 - pv) * (1 / 20)
    elif pv <= 100000:
        return 0.02 * pv
    elif pv <= 110000:
        return 0.03 * pv - (110000 - pv) * (1 / 10)
    elif pv <= 150000:
        return 0.03 * pv
    elif pv <= 160000:
        return 0.04 * pv - (160000 - pv) * (15 / 100)
    elif pv <= 200000:
        return 0.04 * pv
    elif pv <= 210000:
        return 0.05 * pv - (210000 - pv) * (20 / 100)
    elif pv <= 250000:
        return 0.05 * pv
    elif pv <= 260000:
        return 0.06 * pv - (260000 - pv) * (25 / 100)
    else:
        return 0.06 * pv


def calcul_plus_value_immobiliere(
    prix_vente: float,
    prix_achat: float,
    annees_detention: int,
    frais_acquisition_reels: float = 0.0,
    utiliser_forfait_frais: bool = True,
    travaux_reels: float = 0.0,
    utiliser_forfait_travaux: bool = True,
    amortissements_reintegres: float = 0.0,
    taux_ps: float = 0.172
) -> dict:
    """
    Calcule la plus-value immobilière nette et l'impôt total (IR + PS + Surtaxe).
    Intègre la réforme LF 2025/2026 (Art. 150 VB CGI) pour la réintégration
    des amortissements LMNP.
    """
    frais_acq = prix_achat * 0.075 if utiliser_forfait_frais else frais_acquisition_reels
    if annees_detention > 5 and utiliser_forfait_travaux:
        travaux = prix_achat * 0.15
    else:
        travaux = travaux_reels

    prix_acq_majore = prix_achat + frais_acq + travaux
    prix_acq_corrige = max(0.0, prix_acq_majore - amortissements_reintegres)

    pv_brute = max(0.0, prix_vente - prix_acq_corrige)
    abatt_ir, abatt_ps = calcul_abattements_pv(annees_detention)

    pv_nette_ir = pv_brute * (1.0 - abatt_ir)
    pv_nette_ps = pv_brute * (1.0 - abatt_ps)

    impot_ir = pv_nette_ir * 0.19
    impot_ps = pv_nette_ps * taux_ps
    surtaxe = calcul_surtaxe_pv(pv_nette_ir)
    total_impot = impot_ir + impot_ps + surtaxe

    return {
        "frais_acq_retenus": frais_acq,
        "travaux_retenus": travaux,
        "prix_acq_majore": prix_acq_majore,
        "prix_acq_corrige": prix_acq_corrige,
        "marge_exoneree": max(0.0, prix_acq_corrige - prix_achat),
        "pv_brute": pv_brute,
        "abatt_ir_pct": abatt_ir * 100,
        "abatt_ps_pct": abatt_ps * 100,
        "pv_nette_ir": pv_nette_ir,
        "pv_nette_ps": pv_nette_ps,
        "impot_ir": impot_ir,
        "impot_ps": impot_ps,
        "surtaxe": surtaxe,
        "total_impot": total_impot
    }


# ==============================================================================
# INTERFACE PRINCIPALE D'AUDIT PATRIMONIAL
# ==============================================================================

def render_audit_patrimonial():
    st.markdown("## 🏛️ Audit Patrimonial & Arbitrage Immobilier")
    st.caption(
        "Outil d'analyse de performance immobilière en rendez-vous client — "
        "Calcul du Rendement sur Fonds Propres Immobilisés (ROE), Fiscalité & Scénarios d'Arbitrage (Normes 2026)"
    )

    # --- BARRE LATÉRALE : PARAMÈTRES COMMUNS DU DOSSIER CLIENT ---
    with st.sidebar:
        st.header("👤 Dossier Client & Actif")
        nom_client = st.text_input("Nom du client / Référence", value="M. & Mme Client")
        ville_bien = st.text_input("Localisation du bien", value="Nice")

        st.subheader("1. Valorisation & Acquisition")
        valeur_venale = st.number_input(
            "Valeur vénale actuelle Nette Vendeur (€)",
            help="Prix de vente estimé net de frais d'agence (base de calcul de la plus-value).",
            min_value=50000, max_value=10000000, value=360000, step=5000
        )
        prix_achat = st.number_input("Prix d'acquisition initial (€)", min_value=30000, max_value=10000000, value=300000, step=5000)
        annees_detention = st.slider("Durée de détention (années pleines)", min_value=1, max_value=35, value=9)

        forfait_frais = st.checkbox("Forfait frais d'acquisition (7,5 %)", value=True)
        if not forfait_frais:
            frais_reels = st.number_input("Montant réel des frais d'acquisition (€)", min_value=0, max_value=1000000, value=int(prix_achat * 0.025), step=500)
        else:
            frais_reels = 0.0

        if annees_detention > 5:
            forfait_travaux = st.checkbox("Forfait travaux (15 % acquis > 5 ans)", value=True)
        else:
            st.caption("ℹ️ Détention ≤ 5 ans : forfait travaux 15 % non applicable.")
            forfait_travaux = False

        if not forfait_travaux:
            travaux_reels = st.number_input("Montant réel des travaux sur factures (€)", min_value=0, max_value=2000000, value=0, step=1000)
        else:
            travaux_reels = 0.0

        st.subheader("2. Financement Bancaire Actuel")
        crd = st.number_input("Capital Restant Dû - CRD (€)", min_value=0, max_value=10000000, value=160000, step=5000)
        mensualite_credit = st.number_input("Mensualité de crédit assurance incluse (€/mois)", min_value=0, max_value=50000, value=1250, step=25)
        interets_annuels = st.number_input("Dont intérêts & assurance déductibles (€/an)", min_value=0, max_value=200000, value=2800, step=100)
        ira_estimees = st.number_input("Indemnités remboursement anticipé - IRA (€)", min_value=0, max_value=50000, value=0, step=100)

        st.subheader("3. Exploitation & Fiscalité Client")
        loyer_mensuel_hc = st.number_input("Loyer mensuel actuel hors charges (€/mois)", min_value=100, max_value=50000, value=950, step=25)
        charges_annuelles = st.number_input(
            "Charges annuelles non récupérables (€/an)",
            help="Taxe foncière + Copropriété non récupérable + PNO + Frais de gestion / comptabilité",
            min_value=0, max_value=100000, value=2600, step=100
        )
        tmi = st.selectbox("Tranche Marginale d'Imposition (TMI %)", options=[0, 11, 30, 41, 45], index=2)
        taux_reemploi = st.slider("Rendement net cible en cas de réemploi (%)", min_value=2.0, max_value=9.0, value=5.0, step=0.25)

        # --- PENSE-BÊTE CGP INTÉGRÉ ---
        st.divider()
        with st.expander("📖 Pense-bête & Lexique CGP"):
            terme_choisi = st.selectbox("Rechercher un terme", list(LEXIQUE_PATRIMONIAL_CGP.keys()))
            infos = LEXIQUE_PATRIMONIAL_CGP[terme_choisi]
            st.markdown(f"**{infos['nom']}**")
            st.write(infos["definition"])
            if "formule" in infos:
                st.caption(f"Formule : {infos['formule']}")
            if "utilite_rdv" in infos:
                st.info(infos["utilite_rdv"])

    # Calculs de base communs
    loyer_annuel = loyer_mensuel_hc * 12
    annuite_credit = mensualite_credit * 12
    capital_amorti_an = max(0.0, annuite_credit - interets_annuels)

    # Création des 3 onglets métiers
    tab_lmnp, tab_pinel, tab_sci = st.tabs([
        "🛋️ Cas 1 : Audit LMNP (Réforme 2025/2026)",
        "📉 Cas 2 : Fin de Pinel (Nom Propre)",
        "🏢 Cas 3 : SCI en Fin de Pinel (IR vs IS)"
    ])

    # ==========================================================================
    # ONGLET 1 : AUDIT LMNP
    # ==========================================================================
    with tab_lmnp:
        st.subheader("Diagnostic Patrimonial : Loueur en Meublé Non Professionnel (LMNP)")
        col_p1, col_p2, col_p3 = st.columns(3)
        with col_p1:
            regime_lmnp = st.radio("Régime fiscal actuel", ["Réel Simplifié (Amortissement)", "Micro-BIC (Abattement 50 %)"])
        with col_p2:
            amort_cumules = st.number_input(
                "Cumul des amortissements déduits (€)",
                help="Réintégrés dans la plus-value depuis la LF 2025 (Art. 150 VB CGI)",
                min_value=0, max_value=2000000, value=65000, step=2500
            )
        with col_p3:
            amort_annuel_restant = st.number_input(
                "Dotation d'amortissement actuelle (€/an)",
                help="Souvent en baisse après 7-10 ans (mobilier et frais d'acte totalement amortis)",
                min_value=0, max_value=200000, value=4500, step=250
            )
            exception_residence = st.checkbox("Résidence étudiante / EHPAD (Exonéré de réintégration art. 150 VB)", value=False)

        taux_ps_lmnp = 0.172
        if regime_lmnp == "Réel Simplifié (Amortissement)":
            resultat_avant_amort = loyer_annuel - charges_annuelles - interets_annuels
            # Art. 39 C CGI : l'amortissement ne peut pas créer de déficit fiscal
            base_imposable_lmnp = max(0.0, resultat_avant_amort - amort_annuel_restant)
        else:
            base_imposable_lmnp = loyer_annuel * 0.50
