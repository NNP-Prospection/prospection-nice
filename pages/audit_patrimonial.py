import streamlit as st
import pandas as pd
from datetime import date

# Configuration de la page
st.set_page_config(
    page_title="Audit Patrimonial Immobilier",
    page_icon="🏛️",
    layout="wide"
)

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
        "formule": "Valeur Vénale - Capital Restant Dû (CRD) - Impôt sur la Plus-Value - IRA"
    },
    "CRD": {
        "nom": "Capital Restant Dû",
        "definition": "Montant total de la dette restant à rembourser à la banque.",
        "source": "Tableau d'amortissement de l'emprunt bancaire."
    },
    "IMP": {
        "nom": "Impôt sur la Plus-Value Immobilière",
        "definition": "Taxe sur la plus-value brute (Prix de vente - Prix d'acquisition majoré).",
        "majoration": "Forfait frais d'acquisition (7,5 %) + Forfait travaux (15 % si bien > 5 ans)."
    },
    "Cash-Flow Net": {
        "nom": "Trésorerie Nette Après Impôts",
        "definition": "Flux de trésorerie réel généré chaque mois par le bien.",
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
        "avantage": "Permet de déduire l'amortissement comptable du bien et du mobilier pour effacer l'impôt."
    },
    "TMI": {
        "nom": "Tranche Marginale d'Imposition",
        "definition": "Taux personnel d'impôt sur le revenu du client (0%, 11%, 30%, 41%, 45%).",
        "cumul": "S'ajoute toujours aux 17,2 % de prélèvements sociaux en location nue ou BIC."
    },
    "Abattement IR (22 ans)": {
        "nom": "Exonération Impôt sur le Revenu Plus-Value",
        "definition": "Acquisition progressive d'abattements sur la plus-value immobilière.",
        "seuil": "Exonération totale de l'impôt (19 %) atteinte au bout de 22 ans de détention."
    },
    "Abattement PS (30 ans)": {
        "nom": "Exonération Prélèvements Sociaux Plus-Value",
        "definition": "Diminution progressive des prélèvements sociaux (17,2 %).",
        "seuil": "Exonération totale atteinte au bout de 30 ans de détention."
    },
    "Nom Propre": {
        "nom": "Détention en Personne Physique",
        "definition": "Propriété directe du bien par le particulier (ou en indivision), hors structure sociétaire."
    },
    "SCI à l'IR": {
        "nom": "Société Civile Immobilière à l'Impôt sur le Revenu",
        "definition": "Structure transparente fiscalement : les associés paient l'impôt selon leur TMI.",
        "piege": "Impossibilité de passer en meublé (> 10 % recettes) sans basculer de force à l'IS."
    }
}


# ==============================================================================
# MOTEUR DE CALCUL FISCAL & PATRIMONIAL (NORMES 2026)
# ==============================================================================

def calcul_abattements_pv(annees_detention: int) -> tuple[float, float]:
    """
    Calcule les taux d'abattement pour durée de détention (régime des particuliers).
    Retourne (abattement_ir, abattement_ps) entre 0.0 et 1.0.
    """
    if annees_detention <= 5:
        return 0.0, 0.0

    # Abattement Impôt sur le Revenu (Exonération totale à 22 ans)
    if annees_detention >= 22:
        abatt_ir = 1.0
    elif annees_detention <= 21:
        abatt_ir = (annees_detention - 5) * 0.06
    else:
        abatt_ir = 1.0

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
    selon l'article 1609 nonies G du CGI avec formules de lissage.
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
        "prix_acq_majore": prix_acq_majore,
        "prix_acq_corrige": prix_acq_corrige,
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
        valeur_venale = st.number_input("Valeur vénale actuelle estimée (€)", min_value=50000, max_value=10000000, value=360000, step=5000)
        prix_achat = st.number_input("Prix d'acquisition initial (€)", min_value=30000, max_value=10000000, value=300000, step=5000)
        annees_detention = st.slider("Durée de détention (années)", min_value=1, max_value=35, value=9)
        forfait_frais = st.checkbox("Forfait frais d'acquisition (7,5 %)", value=True)
        forfait_travaux = st.checkbox("Forfait travaux (15 % si > 5 ans)", value=True)

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
            base_imposable_lmnp = max(0.0, resultat_avant_amort - amort_annuel_restant)
        else:
            base_imposable_lmnp = loyer_annuel * 0.50

        impot_loyers_lmnp = base_imposable_lmnp * ((tmi / 100.0) + taux_ps_lmnp)
        cashflow_annuel_lmnp = loyer_annuel - charges_annuelles - annuite_credit - impot_loyers_lmnp
        enrichissement_lmnp = cashflow_annuel_lmnp + capital_amorti_an

        amort_a_reintegrer = 0.0 if (regime_lmnp.startswith("Micro") or exception_residence) else amort_cumules
        pv_lmnp_actuelle = calcul_plus_value_immobiliere(
            valeur_venale, prix_achat, annees_detention,
            utiliser_forfait_frais=forfait_frais,
            utiliser_forfait_travaux=forfait_travaux,
            amortissements_reintegres=amort_a_reintegrer
        )
        pv_lmnp_ancienne = calcul_plus_value_immobiliere(
            valeur_venale, prix_achat, annees_detention,
            utiliser_forfait_frais=forfait_frais,
            utiliser_forfait_travaux=forfait_travaux,
            amortissements_reintegres=0.0
        )
        surcout_reforme_pv = pv_lmnp_actuelle["total_impot"] - pv_lmnp_ancienne["total_impot"]

        capital_net_lmnp = max(1.0, valeur_venale - crd - pv_lmnp_actuelle["total_impot"] - ira_estimees)
        roe_lmnp = (enrichissement_lmnp / capital_net_lmnp) * 100
        revenu_reemploi_lmnp = capital_net_lmnp * (taux_reemploi / 100.0)

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Capital Net Immobilisé", f"{capital_net_lmnp:,.0f} €".replace(",", " "), help="Valeur vénale nette de CRD et de fiscalité PV")
        m2.metric("Cash-Flow Mensuel Net-Net", f"{cashflow_annuel_lmnp / 12:,.0f} € / mois".replace(",", " "), delta=f"Impôt BIC : -{impot_loyers_lmnp:,.0f} €/an".replace(",", " "), delta_color="inverse")
        m3.metric("Impact Réforme PV (Art. 150 VB)", f"{pv_lmnp_actuelle['total_impot']:,.0f} €".replace(",", " "), delta=f"+{surcout_reforme_pv:,.0f} € vs avant 2025".replace(",", " "), delta_color="inverse")
        m4.metric("ROE (Rendement Fonds Propres)", f"{roe_lmnp:.2f} % / an", delta=f"Cible réemploi : {taux_reemploi:.2f} %")

        st.markdown("#### 📊 Tableau Comparatif : Conserver le LMNP vs Arbitrer (Vendre)")
        df_lmnp = pd.DataFrame({
            "Critère d'Analyse Patrimoniale": [
                "Prix d'acquisition corrigé retenu pour la PV",
                "Plus-value brute imposable",
                "Impôt total sur la plus-value (IR 19% + PS 17,2% + Surtaxe)",
                "Capital Net Vendeur disponible (Equity nette)",
                "Revenu imposable annuel (BIC)",
                "Fiscalité annuelle sur les loyers (TMI + PS)",
                "Trésorerie nette mensuelle (Cash-Flow)",
                "Enrichissement net annuel (Cash-flow + Capital remboursé)",
                "Rendement réel sur les fonds propres immobilisés (ROE)"
            ],
            "Situation Actuelle (Maintien LMNP)": [
                f"{pv_lmnp_actuelle['prix_acq_corrige']:,.0f} €".replace(",", " "),
                f"{pv_lmnp_actuelle['pv_brute']:,.0f} €".replace(",", " "),
                f"{pv_lmnp_actuelle['total_impot']:,.0f} € (si vente aujourd'hui)".replace(",", " "),
                f"{capital_net_lmnp:,.0f} € bloqués dans les murs".replace(",", " "),
                f"{base_imposable_lmnp:,.0f} € / an".replace(",", " "),
                f"{impot_loyers_lmnp:,.0f} € / an".replace(",", " "),
                f"{cashflow_annuel_lmnp / 12:,.0f} € / mois".replace(",", " "),
                f"{enrichissement_lmnp:,.0f} € / an".replace(",", " "),
                f"{roe_lmnp:.2f} % / an"
            ],
            f"Arbitrage : Vente & Réemploi ({taux_reemploi:.1f} % net)": [
                "Purge des amortissements passés",
                "Extinction du risque d'accumulation d'amortissements",
                f"Réglé à la cession ({pv_lmnp_actuelle['total_impot']:,.0f} €)".replace(",", " "),
                f"{capital_net_lmnp:,.0f} € liquides et réalloués".replace(",", " "),
                "Selon nouvel arbitrage patrimonial ou immobilier",
                "Fiscalité maîtrisée / nouveau cycle d'investissement",
                f"+ {revenu_reemploi_lmnp / 12:,.0f} € / mois (projection théorique)".replace(",", " "),
                f"+ {revenu_reemploi_lmnp:,.0f} € / an".replace(",", " "),
                f"{taux_reemploi:.2f} % / an"
            ]
        })
        st.table(df_lmnp)

        st.info(
            f"💡 **Point d'analyse ({nom_client}) :** "
            f"Chaque année supplémentaire où le bien est conservé avec un amortissement comptable réduit ({amort_annuel_restant:,.0f} €/an) "
            f"cumule deux effets défavorables : d'une part vos loyers commencent à être taxés à **{tmi + 17.2:.1f} %**, "
            f"et d'autre part les **{amort_cumules:,.0f} € d'amortissements déjà déduits** viennent majorer votre base de plus-value "
            f"(surcoût fiscal actuel de **{surcout_reforme_pv:,.0f} €**). Vos **{capital_net_lmnp:,.0f} €** de fonds propres nets ne travaillent "
            f"plus qu'à **{roe_lmnp:.2f} % par an**.".replace(",", " ")
        )

    # ==========================================================================
    # ONGLET 2 : AUDIT FIN DE LOI PINEL (NOM PROPRE)
    # ==========================================================================
    with tab_pinel:
        st.subheader("Diagnostic Patrimonial : Sortie de Dispositif Pinel (Détention en Nom Propre)")
        cp1, cp2, cp3 = st.columns(3)
        with cp1:
            horizon_pinel = st.selectbox("Échéance Pinel atteinte", ["Fin des 6 ans", "Fin des 9 ans", "Fin des 12 ans"], index=1)
        with cp2:
            base_pinel = st.number_input("Assiette fiscale Pinel initiale (€, plafonnée à 300 000 €)", min_value=50000, max_value=300000, value=min(300000, int(prix_achat)), step=5000)
        with cp3:
            loyer_meuble_potentiel = st.number_input("Loyer mensuel potentiel si bascule en LMNP (€/mois)", min_value=100, max_value=50000, value=int(loyer_mensuel_hc * 1.15), step=25)

        taux_reduc_avant = 0.02 if horizon_pinel in ["Fin des 6 ans", "Fin des 9 ans"] else 0.01
        reduction_pinel_perdue = base_pinel * taux_reduc_avant

        revenu_foncier_imposable = max(0.0, loyer_annuel - charges_annuelles - interets_annuels)
        impot_foncier_nu = revenu_foncier_imposable * ((tmi / 100.0) + 0.172)

        cf_pendant_pinel = loyer_annuel - charges_annuelles - annuite_credit - impot_foncier_nu + reduction_pinel_perdue
        cf_apres_pinel = loyer_annuel - charges_annuelles - annuite_credit - impot_foncier_nu
        enrichissement_apres_pinel = cf_apres_pinel + capital_amorti_an

        pv_pinel = calcul_plus_value_immobiliere(
            valeur_venale, prix_achat, annees_detention,
            utiliser_forfait_frais=forfait_frais,
            utiliser_forfait_travaux=forfait_travaux,
            amortissements_reintegres=0.0
        )
        capital_net_pinel = max(1.0, valeur_venale - crd - pv_pinel["total_impot"] - ira_estimees)
        roe_pinel = (enrichissement_apres_pinel / capital_net_pinel) * 100
        revenu_reemploi_pinel = capital_net_pinel * (taux_reemploi / 100.0)

        loyer_annuel_meuble = loyer_meuble_potentiel * 12
        amort_potentiel_bascule = (valeur_venale * 0.80) / 30.0
        base_bic_bascule = max(0.0, loyer_annuel_meuble - charges_annuelles - interets_annuels - amort_potentiel_bascule)
        impot_bic_bascule = base_bic_bascule * ((tmi / 100.0) + 0.172)
        cf_bascule_lmnp = loyer_annuel_meuble - charges_annuelles - annuite_credit - impot_bic_bascule

        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Perte Réduction Pinel", f"- {reduction_pinel_perdue:,.0f} € / an".replace(",", " "), delta=horizon_pinel, delta_color="inverse")
        k2.metric("Effort d'Épargne Après Pinel", f"{cf_apres_pinel / 12:,.0f} € / mois".replace(",", " "), delta=f"Avant : {cf_pendant_pinel / 12:,.0f} €/mois".replace(",", " "), delta_color="inverse")
        k3.metric("Pression Fiscale Foncière", f"{impot_foncier_nu:,.0f} € / an".replace(",", " "), delta=f"Taux global : {tmi + 17.2:.1f} %", delta_color="inverse")
        k4.metric("ROE Post-Pinel (Nu)", f"{roe_pinel:.2f} % / an", delta=f"Capital net : {capital_net_pinel:,.0f} €".replace(",", " "))

        st.markdown("#### ⚖️ Matrice d'Arbitrage Post-Pinel : 3 Stratégies Comparées")
        df_pinel = pd.DataFrame({
            "Indicateur": [
                "Loyers annuels bruts",
                "Réduction d'impôt Pinel",
                "Impôt annuel sur les loyers (IR + PS)",
                "Cash-Flow / Effort d'épargne mensuel",
                "Enrichissement net annuel (Capital + Cash-flow)",
                "Rendement sur les Fonds Propres (ROE)",
                "Contraintes & Risques"
            ],
            "1. Conserver en Location Nue (Statu Quo)": [
                f"{loyer_annuel:,.0f} € / an".replace(",", " "),
                "0 € (Éteinte)",
                f"- {impot_foncier_nu:,.0f} € / an (TMI {tmi}% + 17,2%)".replace(",", " "),
                f"{cf_apres_pinel / 12:,.0f} € / mois".replace(",", " "),
                f"+ {enrichissement_apres_pinel:,.0f} € / an".replace(",", " "),
                f"{roe_pinel:.2f} % / an",
                "Effort d'épargne maximal et fiscalité foncière"
            ],
            "2. Basculer en LMNP (Si départ locataire)": [
                f"{loyer_annuel_meuble:,.0f} € / an".replace(",", " "),
                "0 €",
                f"- {impot_bic_bascule:,.0f} € / an (Amort. ~{amort_potentiel_bascule:,.0f} €/an)".replace(",", " "),
                f"{cf_bascule_lmnp / 12:,.0f} € / mois".replace(",", " "),
                f"+ {(cf_bascule_lmnp + capital_amorti_an):,.0f} € / an".replace(",", " "),
                f"{((cf_bascule_lmnp + capital_amorti_an) / capital_net_pinel) * 100:.2f} % / an",
                "Impossible tant que le locataire reste ; réintégration amort. à la revente (LF 2025)"
            ],
            f"3. Vendre & Réallouer ({taux_reemploi:.1f} % net)": [
                f"{revenu_reemploi_pinel:,.0f} € / an (Revenus théoriques)".replace(",", " "),
                "Capital purgé d'impôt PV (Forfaits 22,5 % acquis)",
                f"Impôt PV à la vente : {pv_pinel['total_impot']:,.0f} €".replace(",", " "),
                f"+ {revenu_reemploi_pinel / 12:,.0f} € / mois (projection)".replace(",", " "),
                f"+ {revenu_reemploi_pinel:,.0f} € / an".replace(",", " "),
                f"{taux_reemploi:.2f} % / an",
                "Vente libre valorisée à 100 % sans décote d'occupation"
            ]
        })
        st.table(df_pinel)

    # ==========================================================================
    # ONGLET 3 : AUDIT SCI EN FIN DE PINEL (IR vs IS)
    # ==========================================================================
    with tab_sci:
        st.subheader("Diagnostic Patrimonial : SCI à l'IR en Fin de Dispositif Pinel")
        cs1, cs2, cs3 = st.columns(3)
        with cs1:
            quote_part_sci = st.slider("Quote-part du client dans la SCI (%)", min_value=1, max_value=100, value=100)
        with cs2:
            cca_montant = st.number_input("Compte Courant d'Associé (CCA) à rembourser (€)", min_value=0, max_value=5000000, value=30000, step=5000)
        with cs3:
            reduc_pinel_sci = st.number_input("Réduction Pinel annuelle qui prend fin (€/an)", min_value=0, max_value=18000, value=6000, step=500)

        resultat_foncier_sci = max(0.0, loyer_annuel - charges_annuelles - interets_annuels)
        impot_associes_ir = resultat_foncier_sci * ((tmi / 100.0) + 0.172)
        tresorerie_nette_sci_avant_impot = loyer_annuel - charges_annuelles - annuite_credit
        tresorerie_nette_associes_ir = tresorerie_nette_sci_avant_impot - impot_associes_ir

        effet_tresorerie_fantome = resultat_foncier_sci - tresorerie_nette_sci_avant_impot

        amort_sci_is = (valeur_venale * 0.80) / 30.0
        resultat_fiscal_is = max(0.0, loyer_annuel - charges_annuelles - interets_annuels - amort_sci_is)
        impot_societe_is = resultat_fiscal_is * 0.15 if resultat_fiscal_is <= 42500 else (42500 * 0.15 + (resultat_fiscal_is - 42500) * 0.25)
        tresorerie_sci_is = loyer_annuel - charges_annuelles - annuite_credit - impot_societe_is

        pv_sci_ir = calcul_plus_value_immobiliere(
            valeur_venale, prix_achat, annees_detention,
            utiliser_forfait_frais=forfait_frais,
            utiliser_forfait_travaux=forfait_travaux,
            amortissements_reintegres=0.0
        )
        capital_net_sci = max(1.0, valeur_venale - crd - pv_sci_ir["total_impot"] - ira_estimees)
        enrichissement_sci_ir = tresorerie_nette_associes_ir + capital_amorti_an
        roe_sci_ir = (enrichissement_sci_ir / capital_net_sci) * 100

        s1, s2, s3, s4 = st.columns(4)
        s1.metric("Trésorerie Fantôme Taxée", f"{effet_tresorerie_fantome:,.0f} € / an".replace(",", " "), help="Bénéfice fiscal taxé à l'IR alors que l'argent sert à rembourser le capital de la banque")
        s2.metric("Impôt Associés (SCI à l'IR)", f"{impot_associes_ir:,.0f} € / an".replace(",", " "), delta=f"TMI {tmi}% + 17,2% PS", delta_color="inverse")
        s3.metric("Effort Mensuel Associés (IR)", f"{tresorerie_nette_associes_ir / 12:,.0f} € / mois".replace(",", " "), delta=f"Perte Pinel : -{reduc_pinel_sci:,.0f} €/an".replace(",", " "), delta_color="inverse")
        s4.metric("ROE Actuel de la SCI (IR)", f"{roe_sci_ir:.2f} % / an", delta=f"Net vendeur SCI : {capital_net_sci:,.0f} €".replace(",", " "))

        st.warning(
            "⚠️ **Alerte Juridique & Fiscale SCI à l'IR (Art. 206-2 du CGI) :** "
            "Contrairement à un bien détenu en direct, **la SCI à l'IR ne peut pas basculer ce bien en location meublée (LMNP)** "
            "sans franchir le seuil de 10 % de recettes commerciales, ce qui entraînerait la **contamination fiscale et le passage forcé à l'IS**."
        )

        df_sci = pd.DataFrame({
            "Critère Décisionnel": [
                "Possibilité de passer le bien en Meublé (LMNP)",
                "Résultat imposable annuel",
                "Impôt annuel à payer",
                "Trésorerie nette mensuelle pour les associés",
                "Régime de Plus-Value en cas de vente du bien",
                "Fiscalité pour sortir le cash de la SCI vers les associés",
                "Synthèse Comparative"
            ],
            "Voie 1 : Maintien SCI à l'IR (Location Nue)": [
                "Interdit (risque de bascule IS forcée > 10 % recettes)",
                f"{resultat_foncier_sci:,.0f} € / an (Transparence fiscale)".replace(",", " "),
                f"{impot_associes_ir:,.0f} € / an payés par les associés".replace(",", " "),
                f"{tresorerie_nette_associes_ir / 12:,.0f} € / mois".replace(",", " "),
                f"Plus-value des particuliers (Impôt actuel : {pv_sci_ir['total_impot']:,.0f} €)".replace(",", " "),
                "0 € (Remontée libre du prix de vente net en SCI à l'IR)",
                f"ROE faible ({roe_sci_ir:.2f} %) et effet 'trésorerie fantôme' pénalisant"
            ],
            "Voie 2 : Option irrévocable de la SCI pour l'IS": [
                "Autorisé (activité commerciale possible à l'IS)",
                f"{resultat_fiscal_is:,.0f} € / an (après amortissement)".replace(",", " "),
                f"{impot_societe_is:,.0f} € / an payés par la SCI (IS 15 %/25 %)".replace(",", " "),
                f"{tresorerie_sci_is / 12:,.0f} € / mois (bloqués dans la SCI hors CCA)".replace(",", " "),
                "Plus-value professionnelle sur VNC (sans abattement futur)",
                "Flat Tax 30 % sur dividendes (hors remboursement du CCA)",
                "Piège à la sortie : double taxation (IS sur PV + Flat Tax 30 %)"
            ],
            "Voie 3 : Vente de l'actif par la SCI à l'IR": [
                "Sans objet (Cession du bien libre)",
                "Extinction de la friction fiscale foncière",
                "0 € d'impôt annuel futur",
                f"+ {(capital_net_sci * (taux_reemploi / 100.0)) / 12:,.0f} € / mois après réemploi".replace(",", " "),
                f"Exonération des amortissements + Abattements acquis ({pv_sci_ir['total_impot']:,.0f} €)".replace(",", " "),
                f"Distribution libre des {capital_net_sci:,.0f} € aux associés (0 % Flat Tax)".replace(",", " "),
                "Sortie optimale : capte la PV des particuliers et libère le cash sans Flat Tax"
            ]
        })
        st.table(df_sci)

    # ==========================================================================
    # SYNTHÈSE EXÉCUTIVE IMPRIMABLE / COPIABLE POUR LE CLIENT (SÉCURISÉE LOI HOGUET)
    # ==========================================================================
    st.divider()
    with st.expander("📄 Générer la Synthèse d'Audit Patrimonial (Prête à copier / remettre au client)", expanded=False):
        date_jour = date.today().strftime("%d/%m/%Y")
        synthese_texte = f"""SYNTHÈSE D'ANALYSE D'ARBITRAGE IMMOBILIER (DOCUMENT PRÉPARATOIRE INDICATIF)
Cabinet Privé Immobilier Honorat — Transaction Immobilière (Carte T - Loi Hoguet)
Date de l'étude : {date_jour}
Dossier : {nom_client} | Localisation de l'actif : {ville_bien}
------------------------------------------------------------------------
1. VALORISATION & CAPITAL NET IMMOBILISÉ (ESTIMATION)
- Valeur vénale actuelle estimée : {valeur_venale:,.0f} €
- Prix d'acquisition initial ({annees_detention} ans de détention) : {prix_achat:,.0f} €
- Capital Restant Dû (CRD déclaré) : {crd:,.0f} € (Mensualité : {mensualite_credit:,.0f} €/mois)
- Capital Net Vendeur estimé (Fonds propres nets récupérables) : {capital_net_pinel:,.0f} €

2. ANALYSE DU RENDEMENT SUR FONDS PROPRES IMMOBILISÉS (ROE)
- Loyers annuels hors charges : {loyer_annuel:,.0f} €/an ({loyer_mensuel_hc:,.0f} €/mois)
- Charges non récupérables & Taxe foncière : {charges_annuelles:,.0f} €/an
- Intérêts d'emprunt résiduels déductibles : {interets_annuels:,.0f} €/an
- Hypothèse de Tranche Marginale d'Imposition retenue (TMI) : {tmi} % (+ 17,2 % PS)

3. SIMULATION COMPARATIVE DES SCÉNARIOS IMMOBILIERS
- Hypothèse A — Maintien en LMNP (avec réintégration amortissements Art. 150 VB CGI) :
  * Capital Net Vendeur estimé après impôt PV : {capital_net_lmnp:,.0f} €
  * Rendement indicatif sur fonds propres (ROE) : {roe_lmnp:.2f} % / an
- Hypothèse B — Sortie de Pinel (Location nue / SCI à l'IR) :
  * Frottement fiscal foncier annuel estimé : {impot_foncier_nu:,.0f} € / an
  * Effort de trésorerie mensuel post-Pinel : {cf_apres_pinel / 12:,.0f} € / mois
  * Rendement indicatif sur fonds propres (ROE) : {roe_pinel:.2f} % / an
- Hypothèse C — Mise en vente de l'actif & Réemploi théorique ({taux_reemploi:.2f} % net/an) :
  * Capital net vendeur libérable : {capital_net_pinel:,.0f} €
  * Projection théorique de revenus après réallocation : + {revenu_reemploi_pinel:,.0f} € / an (+ {revenu_reemploi_pinel / 12:,.0f} € / mois)

------------------------------------------------------------------------
MENTIONS LÉGALES & CADRE RÉGLEMENTAIRE (LOI HOGUET) :
Ce document constitue une simulation mathématique et indicative d'aide à la décision,
réalisée à titre gracieux et strictement accessoire à une estimation immobilière en vue
d'un projet de transaction (Loi n° 70-9 du 2 janvier 1970 dite « Loi Hoguet » et art. 59
de la loi n° 71-1130 du 31 décembre 1971). Les calculs reposent sur les éléments déclaratifs
communiqués par le propriétaire et sur les barèmes fiscaux en vigueur à titre d'illustration.
Ce document ne constitue ni une consultation juridique ou fiscale personnalisée (relevant
d'un notaire, avocat fiscaliste ou expert-comptable), ni une prestation de Conseil en
Investissement Financier (CIF) au sens de l'article L. 541-1 du Code monétaire et financier.
Le calcul définitif de la plus-value immobilière relève de la compétence exclusive du
notaire rédacteur de l'acte authentique de vente.
""".replace(",", " ")
        st.code(synthese_texte, language="text")


render_audit_patrimonial()
