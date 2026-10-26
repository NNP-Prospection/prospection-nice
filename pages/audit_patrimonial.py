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
        "definition": "Structure transparente fiscalement : les associés paient l'impôt selon leur TMI et leur quote-part.",
        "piege": "Impossibilité de passer en meublé (> 10 % recettes) sans basculer de force à l'IS (Art. 206-2 CGI)."
    }
}


# ==============================================================================
# MOTEUR DE CALCUL FISCAL & PATRIMONIAL (NORMES 2026)
# ==============================================================================

def calcul_abattements_pv(annees_detention: int) -> tuple[float, float]:
    if annees_detention <= 5:
        return 0.0, 0.0
    if annees_detention >= 22:
        abatt_ir = 1.0
    else:
        abatt_ir = (annees_detention - 5) * 0.06

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

    # --- BARRE LATÉRALE ---
    with st.sidebar:
        st.header("👤 Dossier Client & Actif")
        nom_client = st.text_input("Nom du client / Référence", value="M. & Mme Client")
        ville_bien = st.text_input("Localisation du bien", value="Nice")

        st.subheader("1. Valorisation & Acquisition")
        valeur_venale = st.number_input("Valeur vénale actuelle Nette Vendeur (€)", min_value=50000, max_value=10000000, value=360000, step=5000)
        prix_achat = st.number_input("Prix d'acquisition initial (€)", min_value=30000, max_value=10000000, value=300000, step=5000)
        annees_detention = st.slider("Durée de détention (années pleines)", min_value=1, max_value=35, value=9)

        forfait_frais = st.checkbox("Forfait frais d'acquisition (7,5 %)", value=True)
        frais_reels = st.number_input("Montant réel des frais (€)", min_value=0, max_value=1000000, value=0, step=500) if not forfait_frais else 0.0
        
        forfait_travaux = st.checkbox("Forfait travaux (15 % acquis > 5 ans)", value=True) if annees_detention > 5 else False
        travaux_reels = st.number_input("Montant réel des travaux (€)", min_value=0, max_value=2000000, value=0, step=1000) if not forfait_travaux else 0.0

        st.subheader("2. Financement Bancaire Actuel")
        crd = st.number_input("Capital Restant Dû - CRD (€)", min_value=0, max_value=10000000, value=160000, step=5000)
        mensualite_credit = st.number_input("Mensualité crédit assurance incluse (€/mois)", min_value=0, max_value=50000, value=1250, step=25)
        interets_annuels = st.number_input("Intérêts & assurance déductibles (€/an)", min_value=0, max_value=200000, value=2800, step=100)
        ira_estimees = st.number_input("Indemnités remboursement anticipé - IRA (€)", min_value=0, max_value=50000, value=0, step=100)

        st.subheader("3. Exploitation & Fiscalité Client")
        loyer_mensuel_hc = st.number_input("Loyer mensuel hors charges (€/mois)", min_value=100, max_value=50000, value=950, step=25)
        charges_annuelles = st.number_input("Charges annuelles non récupérables (€/an)", min_value=0, max_value=100000, value=2600, step=100)
        tmi = st.selectbox("Tranche Marginale d'Imposition (TMI %)", options=[0, 11, 30, 41, 45], index=2)
        taux_reemploi = st.slider("Rendement net cible en cas de réemploi (%)", min_value=2.0, max_value=9.0, value=5.0, step=0.25)

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

    loyer_annuel = loyer_mensuel_hc * 12
    annuite_credit = mensualite_credit * 12
    capital_amorti_an = max(0.0, annuite_credit - interets_annuels)

    tab_lmnp, tab_pinel, tab_sci = st.tabs([
        "🛋️ Cas 1 : Audit LMNP (Réforme 2025/2026)",
        "📉 Cas 2 : Fin de Pinel (Nom Propre)",
        "🏢 Cas 3 : SCI en Fin de Pinel (IR vs IS)"
    ])

    # --- ONGLET 1 : LMNP ---
    with tab_lmnp:
        st.subheader("Diagnostic Patrimonial : Loueur en Meublé Non Professionnel (LMNP)")
        col_p1, col_p2, col_p3 = st.columns(3)
        with col_p1:
            regime_lmnp = st.radio("Régime fiscal actuel", ["Réel Simplifié (Amortissement)", "Micro-BIC (Abattement 50 %)"])
        with col_p2:
            amort_cumules = st.number_input("Cumul des amortissements déduits (€)", min_value=0, max_value=2000000, value=65000, step=2500)
        with col_p3:
            amort_annuel_restant = st.number_input("Dotation d'amortissement actuelle (€/an)", min_value=0, max_value=200000, value=4500, step=250)
            exception_residence = st.checkbox("Résidence étudiante / EHPAD", value=False)

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
            frais_acquisition_reels=frais_reels, utiliser_forfait_frais=forfait_frais,
            travaux_reels=travaux_reels, utiliser_forfait_travaux=forfait_travaux,
            amortissements_reintegres=amort_a_reintegrer
        )
        pv_lmnp_ancienne = calcul_plus_value_immobiliere(
            valeur_venale, prix_achat, annees_detention,
            frais_acquisition_reels=frais_reels, utiliser_forfait_frais=forfait_frais,
            travaux_reels=travaux_reels, utiliser_forfait_travaux=forfait_travaux,
            amortissements_reintegres=0.0
        )
        surcout_reforme_pv = pv_lmnp_actuelle["total_impot"] - pv_lmnp_ancienne["total_impot"]

        capital_net_lmnp = max(1.0, valeur_venale - crd - pv_lmnp_actuelle["total_impot"] - ira_estimees)
        roe_lmnp = (enrichissement_lmnp / capital_net_lmnp) * 100
        revenu_reemploi_lmnp = capital_net_lmnp * (taux_reemploi / 100.0)

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Capital Net Immobilisé", f"{capital_net_lmnp:,.0f} €".replace(",", " "))
        m2.metric("Cash-Flow Mensuel Net-Net", f"{cashflow_annuel_lmnp / 12:,.0f} € / mois".replace(",", " "))
        m3.metric("Impact Réforme PV (Art. 150 VB)", f"{pv_lmnp_actuelle['total_impot']:,.0f} €".replace(",", " "))
        m4.metric("ROE (Rendement Fonds Propres)", f"{roe_lmnp:.2f} % / an")

        st.markdown("#### 📊 Tableau Comparatif : LMNP vs Vente & Réemploi")
        df_lmnp = pd.DataFrame({
            "Critère": ["Prix acquisition majoré", "Prix acquisition corrigé", "Plus-value brute", "Impôt PV total", "Capital net vendeur", "Revenu BIC imposable", "Impôt loyers", "Cash-flow mensuel", "Enrichissement annuel", "ROE"],
            "Maintien LMNP": [
                f"{pv_lmnp_actuelle['prix_acq_majore']:,.0f} €".replace(",", " "),
                f"{pv_lmnp_actuelle['prix_acq_corrige']:,.0f} €".replace(",", " "),
                f"{pv_lmnp_actuelle['pv_brute']:,.0f} €".replace(",", " "),
                f"{pv_lmnp_actuelle['total_impot']:,.0f} €".replace(",", " "),
                f"{capital_net_lmnp:,.0f} €".replace(",", " "),
                f"{base_imposable_lmnp:,.0f} € / an".replace(",", " "),
                f"{impot_loyers_lmnp:,.0f} € / an".replace(",", " "),
                f"{cashflow_annuel_lmnp / 12:,.0f} € / mois".replace(",", " "),
                f"{enrichissement_lmnp:,.0f} € / an".replace(",", " "),
                f"{roe_lmnp:.2f} % / an"
            ],
            f"Vente & Réemploi ({taux_reemploi:.1f}%)": [
                "Acquis", "Stoppe l'amortissement", "Purge définitive", f"Réglé ({pv_lmnp_actuelle['total_impot']:,.0f} €)".replace(",", " "),
                f"{capital_net_lmnp:,.0f} € dispo".replace(",", " "), "Selon réemploi", "Maîtrisé",
                f"+ {revenu_reemploi_lmnp / 12:,.0f} € / mois".replace(",", " "), f"+ {revenu_reemploi_lmnp:,.0f} € / an".replace(",", " "), f"{taux_reemploi:.2f} % / an"
            ]
        })
        st.table(df_lmnp)

    # --- ONGLET 2 : PINEL NOM PROPRE ---
    with tab_pinel:
        st.subheader("Diagnostic Patrimonial : Sortie de Dispositif Pinel (Nom Propre)")
        cp1, cp2, cp3 = st.columns(3)
        with cp1:
            horizon_pinel = st.selectbox("Échéance Pinel", ["Fin des 6 ans (2%/an)", "Fin des 9 ans (2%/an)", "Fin des 12 ans (1%/an)"], index=1)
        with cp2:
            base_pinel = st.number_input("Assiette Pinel initiale (€)", min_value=50000, max_value=300000, value=min(300000, int(prix_achat)), step=5000)
        with cp3:
            loyer_meuble_potentiel = st.number_input("Loyer potentiel LMNP (€/mois)", min_value=100, max_value=50000, value=int(loyer_mensuel_hc * 1.15), step=25)
            cout_ameublement = st.number_input("Coût ameublement LMNP (€)", min_value=0, max_value=100000, value=8000, step=1000)

        taux_reduc_avant = 0.02 if "2%" in horizon_pinel else 0.01
        reduction_pinel_perdue = base_pinel * taux_reduc_avant

        revenu_foncier_imposable = max(0.0, loyer_annuel - charges_annuelles - interets_annuels)
        impot_foncier_nu = revenu_foncier_imposable * ((tmi / 100.0) + 0.172)

        cf_pendant_pinel = loyer_annuel - charges_annuelles - annuite_credit - impot_foncier_nu + reduction_pinel_perdue
        cf_apres_pinel = loyer_annuel - charges_annuelles - annuite_credit - impot_foncier_nu
        enrichissement_apres_pinel = cf_apres_pinel + capital_amorti_an

        pv_pinel = calcul_plus_value_immobiliere(
            valeur_venale, prix_achat, annees_detention,
            frais_acquisition_reels=frais_reels, utiliser_forfait_frais=forfait_frais,
            travaux_reels=travaux_reels, utiliser_forfait_travaux=forfait_travaux,
            amortissements_reintegres=0.0
        )
        capital_net_pinel = max(1.0, valeur_venale - crd - pv_pinel["total_impot"] - ira_estimees)
        roe_pinel = (enrichissement_apres_pinel / capital_net_pinel) * 100
        revenu_reemploi_pinel = capital_net_pinel * (taux_reemploi / 100.0)

        loyer_annuel_meuble = loyer_meuble_potentiel * 12
        amort_potentiel_bascule = (valeur_venale * 0.80) / 30.0 + (cout_ameublement / 7.0)
        base_bic_bascule = max(0.0, loyer_annuel_meuble - charges_annuelles - interets_annuels - amort_potentiel_bascule)
        impot_bic_bascule = base_bic_bascule * ((tmi / 100.0) + 0.172)
        cf_bascule_lmnp = loyer_annuel_meuble - charges_annuelles - annuite_credit - impot_bic_bascule
        roe_bascule_lmnp = ((cf_bascule_lmnp + capital_amorti_an) / (capital_net_pinel + cout_ameublement)) * 100

        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Perte Réduction Pinel", f"- {reduction_pinel_perdue:,.0f} € / an".replace(",", " "))
        k2.metric("Effort Épargne Après Pinel", f"{cf_apres_pinel / 12:,.0f} € / mois".replace(",", " "))
        k3.metric("Plafond Vente 0 € Impôt PV", f"{pv_pinel['prix_acq_majore']:,.0f} €".replace(",", " "))
        k4.metric("ROE Post-Pinel (Nu)", f"{roe_pinel:.2f} % / an")

        st.success(f"🛡️ **Bouclier Fiscal (+22,5 %) :** Prix d'achat majoré à {pv_pinel['prix_acq_majore']:,.0f} € (soit +{pv_pinel['marge_exoneree']:,.0f} € exonérés d'impôt PV).".replace(",", " "))

        df_pinel = pd.DataFrame({
            "Indicateur": ["Prix acquisition fiscal", "Loyers bruts", "Réduction Pinel", "Impôt loyers", "Cash-flow mensuel", "Enrichissement annuel", "ROE", "Contraintes"],
            "1. Location Nue (Statu Quo)": [
                f"{pv_pinel['prix_acq_majore']:,.0f} €".replace(",", " "), f"{loyer_annuel:,.0f} €".replace(",", " "), f"0 € (-{reduction_pinel_perdue:,.0f}€)".replace(",", " "),
                f"- {impot_foncier_nu:,.0f} €".replace(",", " "), f"{cf_apres_pinel / 12:,.0f} € / mois".replace(",", " "), f"+ {enrichissement_apres_pinel:,.0f} €".replace(",", " "),
                f"{roe_pinel:.2f} %".replace(",", " "), "Effort d'épargne lourd"
            ],
            "2. Bascule LMNP": [
                "Amortissable", f"{loyer_annuel_meuble:,.0f} €".replace(",", " "), "0 €", f"- {impot_bic_bascule:,.0f} €".replace(",", " "),
                f"{cf_bascule_lmnp / 12:,.0f} € / mois".replace(",", " "), f"+ {(cf_bascule_lmnp + capital_amorti_an):,.0f} €".replace(",", " "),
                f"{roe_bascule_lmnp:.2f} %".replace(",", " "), "Locataire en place / ameublement"
            ],
            f"3. Vente & Réemploi ({taux_reemploi:.1f}%)": [
                f"Exonéré jusqu'à {pv_pinel['prix_acq_majore']:,.0f} €".replace(",", " "), f"{revenu_reemploi_pinel:,.0f} €".replace(",", " "), "N/A", f"Impôt PV : {pv_pinel['total_impot']:,.0f} €".replace(",", " "),
                f"+ {revenu_reemploi_pinel / 12:,.0f} € / mois".replace(",", " "), f"+ {revenu_reemploi_pinel:,.0f} €".replace(",", " "), f"{taux_reemploi:.2f} %".replace(",", " "), "Libération immédiate du capital"
            ]
        })
        st.table(df_pinel)

    # --- ONGLET 3 : SCI FIN DE PINEL ---
    with tab_sci:
        st.subheader("Diagnostic Patrimonial : SCI à l'IR en Fin de Pinel")
        cs1, cs2, cs3 = st.columns(3)
        with cs1:
            quote_part_sci = st.slider("Quote-part client (%)", min_value=1, max_value=100, value=100)
        with cs2:
            cca_montant = st.number_input("Compte Courant d'Associé - CCA (€)", min_value=0, max_value=5000000, value=30000, step=5000)
        with cs3:
            reduc_pinel_sci = st.number_input("Réduction Pinel finissante (€/an)", min_value=0, max_value=18000, value=6000, step=500)

        qp = quote_part_sci / 100.0
        resultat_foncier_client = max(0.0, loyer_annuel - charges_annuelles - interets_annuels) * qp
        impot_associe_ir = resultat_foncier_client * ((tmi / 100.0) + 0.172)
        tresorerie_client_avant_impot = (loyer_annuel - charges_annuelles - annuite_credit) * qp
        tresorerie_nette_client_ir = tresorerie_client_avant_impot - impot_associe_ir
        effet_tresorerie_fantome_client = max(0.0, resultat_foncier_client - tresorerie_client_avant_impot)

        amort_sci_is = (valeur_venale * 0.80) / 30.0
        resultat_fiscal_is = max(0.0, loyer_annuel - charges_annuelles - interets_annuels - amort_sci_is)
        impot_societe_is = resultat_fiscal_is * 0.15 if resultat_fiscal_is <= 42500 else (42500 * 0.15 + (resultat_fiscal_is - 42500) * 0.25)
        tresorerie_sci_is_client = (loyer_annuel - charges_annuelles - annuite_credit - impot_societe_is) * qp

        pv_sci_ir = calcul_plus_value_immobiliere(
            valeur_venale, prix_achat, annees_detention,
            frais_acquisition_reels=frais_reels, utiliser_forfait_frais=forfait_frais,
            travaux_reels=travaux_reels, utiliser_forfait_travaux=forfait_travaux,
            amortissements_reintegres=0.0
        )
        capital_net_sci_global = max(1.0, valeur_venale - crd - pv_sci_ir["total_impot"] - ira_estimees)
        solde_apres_cca = max(0.0, capital_net_sci_global - cca_montant)
        capital_net_client_sci = min(capital_net_sci_global, cca_montant * qp + solde_apres_cca * qp)
        enrichissement_client_sci_ir = tresorerie_nette_client_ir + (capital_amorti_an * qp)
        roe_sci_ir = (enrichissement_client_sci_ir / max(1.0, capital_net_client_sci)) * 100
        revenu_reemploi_client_sci = capital_net_client_sci * (taux_reemploi / 100.0)

        s1, s2, s3, s4 = st.columns(4)
        s1.metric("Trésorerie Fantôme Taxée", f"{effet_tresorerie_fantome_client:,.0f} € / an".replace(",", " "))
        s2.metric("Impôt Associé (IR)", f"{impot_associe_ir:,.0f} € / an".replace(",", " "))
        s3.metric("Effort Mensuel Associé", f"{tresorerie_nette_client_ir / 12:,.0f} € / mois".replace(",", " "))
        s4.metric("Capital Net Associé", f"{capital_net_client_sci:,.0f} €".replace(",", " "))

        st.warning("⚠️ **Alerte SCI à l'IR (Art. 206-2 CGI) :** Interdiction de basculer en LMNP (> 10% de recettes) sous peine de contamination et passage forcé à l'IS.")

        df_sci = pd.DataFrame({
            "Critère": ["Meublé (LMNP)", "Résultat imposable", "Impôt annuel", "Trésorerie mensuelle", "Régime PV", "Sortie du cash vers l'associé", "Synthèse"],
            "1. SCI à l'IR (Nue)": [
                "Interdit", f"{resultat_foncier_client:,.0f} €".replace(",", " "), f"{impot_associe_ir:,.0f} €".replace(",", " "),
                f"{tresorerie_nette_client_ir / 12:,.0f} € / mois".replace(",", " "), f"Particuliers (Exonéré jusqu'à {pv_sci_ir['prix_acq_majore']:,.0f} €)".replace(",", " "),
                "0 € d'impôt sur remontée", f"ROE {roe_sci_ir:.2f}% / Trésorerie fantôme"
            ],
            "2. SCI option IS": [
                "Autorisé", f"{resultat_fiscal_is * qp:,.0f} €".replace(",", " "), f"{impot_societe_is * qp:,.0f} €".replace(",", " "),
                f"{tresorerie_sci_is_client / 12:,.0f} € / mois".replace(",", " "), "Professionnelle sur VNC",
                f"CCA ({cca_montant:,.0f} €) à 0%, puis Flat Tax 30%".replace(",", " "), "Piège à la revente (Double taxation IS + Flat Tax)"
            ],
            f"3. Vente SCI à l'IR ({taux_reemploi:.1f}%)": [
                "N/A", "Extinction friction", f"PV : {pv_sci_ir['total_impot'] * qp:,.0f} €".replace(",", " "),
                f"+ {revenu_reemploi_client_sci / 12:,.0f} € / mois".replace(",", " "), f"Bouclier +22,5% ({pv_sci_ir['prix_acq_majore']:,.0f} €)".replace(",", " "),
                f"Distribution des {capital_net_client_sci:,.0f} € à 0% Flat Tax".replace(",", " "), "Sortie optimale sans Flat Tax"
            ]
        })
        st.table(df_sci)

    # --- RAPPORT IMPRIMABLE SÉCURISÉ LOI HOGUET ---
    st.divider()
    st.subheader("📄 Édition du Rapport de Synthèse Client")
    cas_selectionne = st.radio("Sélectionner le profil client :", ["Cas 1 : Détention en LMNP", "Cas 2 : Fin de Pinel (Nom Propre)", "Cas 3 : SCI à l'IR en Fin de Pinel"], horizontal=True)

    if cas_selectionne == "Cas 1 : Détention en LMNP":
        cap_net_rapport = capital_net_lmnp
        impot_pv_rapport = pv_lmnp_actuelle["total_impot"]
        prix_corrige_rapport = pv_lmnp_actuelle["prix_acq_corrige"]
        roe_rapport = roe_lmnp
        cf_mensuel_rapport = cashflow_annuel_lmnp / 12
        impot_annuel_rapport = impot_loyers_lmnp
        revenu_cible_rapport = revenu_reemploi_lmnp
        detail_specifique = f"- Régime LMNP : {regime_lmnp} (Amortissements : {amort_a_reintegrer:,.0f} €)\n- Prix d'acquisition fiscal corrigé (Art. 150 VB) : {prix_corrige_rapport:,.0f} €\n- Impôt PV estimé : {impot_pv_rapport:,.0f} €".replace(",", " ")
    elif cas_selectionne == "Cas 2 : Fin de Pinel (Détention en Nom Propre)":
        cap_net_rapport = capital_net_pinel
        impot_pv_rapport = pv_pinel["total_impot"]
        prix_corrige_rapport = pv_pinel["prix_acq_majore"]
        roe_rapport = roe_pinel
        cf_mensuel_rapport = cf_apres_pinel / 12
        impot_annuel_rapport = impot_foncier_nu
        revenu_cible_rapport = revenu_reemploi_pinel
        detail_specifique = f"- Échéance Pinel : {horizon_pinel}\n- Plafond vente exonéré (+22,5%) : {prix_corrige_rapport:,.0f} € (Gain exonéré : +{pv_pinel['marge_exoneree']:,.0f} €)\n- Impôt PV estimé : {impot_pv_rapport:,.0f} €".replace(",", " ")
    else:
        cap_net_rapport = capital_net_client_sci
        impot_pv_rapport = pv_sci_ir["total_impot"] * qp
        prix_corrige_rapport = pv_sci_ir["prix_acq_majore"]
        roe_rapport = roe_sci_ir
        cf_mensuel_rapport = tresorerie_nette_client_ir / 12
        impot_annuel_rapport = impot_associe_ir
        revenu_cible_rapport = revenu_reemploi_client_sci
        detail_specifique = f"- SCI à l'IR (Quote-part : {quote_part_sci}% | CCA : {cca_montant:,.0f} €)\n- Trésorerie fantôme taxée : {effet_tresorerie_fantome_client:,.0f} €/an\n- Plafond vente exonéré : {prix_corrige_rapport:,.0f} € (Impôt PV quote-part : {impot_pv_rapport:,.0f} €)".replace(",", " ")

    with st.expander("📋 Afficher et copier la Synthèse d'Audit Patrimonial", expanded=True):
        date_jour = date.today().strftime("%d/%m/%Y")
        synthese_texte = f"""SYNTHÈSE D'ANALYSE D'ARBITRAGE IMMOBILIER (DOCUMENT PRÉPARATOIRE INDICATIF)
Cabinet Privé Immobilier Honorat — Transaction Immobilière (Carte T - Loi Hoguet)
Date de l'étude : {date_jour}
Dossier : {nom_client} | Localisation : {ville_bien}
Profil audité : {cas_selectionne}
------------------------------------------------------------------------
1. VALORISATION & CAPITAL NET IMMOBILISÉ
- Valeur vénale actuelle (Nette Vendeur) : {valeur_venale:,.0f} €
- Prix d'acquisition initial ({annees_detention} ans) : {prix_achat:,.0f} €
- Capital Restant Dû (CRD) : {crd:,.0f} € (Mensualité : {mensualite_credit:,.0f} €/mois)
{detail_specifique}
- CAPITAL NET VENDEUR DISPONIBLE : {cap_net_rapport:,.0f} €

2. DIAGNOSTIC DE PERFORMANCE SUR FONDS PROPRES (ROE)
- Loyers annuels HC : {loyer_annuel:,.0f} €/an ({loyer_mensuel_hc:,.0f} €/mois)
- Charges & Taxe foncière : {charges_annuelles:,.0f} €/an
- Intérêts d'emprunt déductibles : {interets_annuels:,.0f} €/an
- TMI retenue : {tmi} % (+ 17,2 % PS)
- Frottement fiscal annuel : - {impot_annuel_rapport:,.0f} € / an
- Flux de trésorerie mensuel : {cf_mensuel_rapport:,.0f} € / mois
- RENDEMENT DES FONDS PROPRES (ROE) : {roe_rapport:.2f} % / an

3. PROJECTION RÉEMPLOI ({taux_reemploi:.2f} % NET/AN)
- Capital net libéré : {cap_net_rapport:,.0f} €
- Revenus annuels potentiels après réemploi : + {revenu_cible_rapport:,.0f} € / an (+ {revenu_cible_rapport / 12:,.0f} € / mois)

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
Le calcul définitif de la plus-value relève de la compétence exclusive du notaire rédacteur.
""".replace(",", " ")
        st.code(synthese_texte, language="text")

if __name__ == "__main__":
    render_audit_patrimonial()
