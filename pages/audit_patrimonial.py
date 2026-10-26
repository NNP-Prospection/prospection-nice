import streamlit as st
import pandas as pd
from datetime import date

# ==============================================================================
# LEXIQUE & MOTEUR DE CALCUL PATRIMONIAL (NORMES 2026)
# ==============================================================================

LEXIQUE_PATRIMONIAL_CGP = {
    "ROE": {
        "nom": "Rendement sur Fonds Propres (Return on Equity)",
        "definition": "Pourcentage de gain réel rapporté par le capital net bloqué dans le bien.",
        "utilite_rdv": "Démontrer au client que si son ROE tombe sous 2%, son capital dormant perd de la valeur."
    },
    "Capital Net Immobilisé": {
        "nom": "Equity Nette Vendeur",
        "definition": "Somme nette disponible sur le compte en cas de vente immédiate.",
        "formule": "Valeur Vénale Nette Vendeur - Capital Restant Dû (CRD) - Impôt sur la Plus-Value - IRA"
    },
    "Bouclier +22,5 %": {
        "nom": "Majoration Forfaitaire du Prix d'Acquisition (Art. 150 VB CGI)",
        "definition": "Après 5 ans de détention, le prix d'achat est majoré de +7,5 % (frais) et +15 % (travaux).",
        "utilite_rdv": "Permet de vendre au-dessus du prix d'achat initial avec 0 € d'impôt de plus-value."
    }
}

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
    if pv <= 50000: return 0.0
    elif pv <= 60000: return 0.02 * pv - (60000 - pv) * (1 / 20)
    elif pv <= 100000: return 0.02 * pv
    elif pv <= 110000: return 0.03 * pv - (110000 - pv) * (1 / 10)
    elif pv <= 150000: return 0.03 * pv
    elif pv <= 160000: return 0.04 * pv - (160000 - pv) * (15 / 100)
    elif pv <= 200000: return 0.04 * pv
    elif pv <= 210000: return 0.05 * pv - (210000 - pv) * (20 / 100)
    elif pv <= 250000: return 0.05 * pv
    elif pv <= 260000: return 0.06 * pv - (260000 - pv) * (25 / 100)
    else: return 0.06 * pv

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
    travaux = (prix_achat * 0.15) if (annees_detention > 5 and utiliser_forfait_travaux) else travaux_reels

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
        "marge_exoneree": max(0.0, prix_acq_corrige - prix_achat),
        "pv_brute": pv_brute,
        "total_impot": total_impot
    }

# ==============================================================================
# INTERFACE PRINCIPALE
# ==============================================================================

def render_audit_patrimonial():
    st.markdown("## 💼 Audit Patrimonial & Simulation d'Arbitrage")
    st.caption("Outil d'analyse de performance immobilière et d'aide à la décision en rendez-vous.")

    # --- BARRE LATÉRALE ---
    with st.sidebar:
        st.header("👤 Dossier Client & Actif")
        nom_client = st.text_input("Nom du client", value="M. & Mme Client")
        ville_bien = st.text_input("Localisation", value="Nice")

        st.subheader("1. Valeurs & Acquisition")
        valeur_venale = st.number_input("Valeur vénale actuelle (€)", min_value=50000, max_value=10000000, value=360000, step=5000)
        prix_achat = st.number_input("Prix d'acquisition initial (€)", min_value=30000, max_value=10000000, value=300000, step=5000)
        annees_detention = st.slider("Durée de détention (années)", min_value=1, max_value=35, value=9)

        forfait_frais = st.checkbox("Forfait frais d'acquisition (7,5 %)", value=True)
        forfait_travaux = st.checkbox("Forfait travaux (15 % si > 5 ans)", value=True) if annees_detention > 5 else False

        st.subheader("2. Financement & Crédit")
        crd = st.number_input("Capital Restant Dû - CRD (€)", min_value=0, max_value=10000000, value=160000, step=5000)
        mensualite_credit = st.number_input("Mensualité crédit (€/mois)", min_value=0, max_value=50000, value=1250, step=25)
        interets_annuels = st.number_input("Intérêts déductibles (€/an)", min_value=0, max_value=200000, value=2800, step=100)
        ira_estimees = st.number_input("IRA (€)", min_value=0, max_value=50000, value=0, step=100)

        st.subheader("3. Exploitation & Fiscalité")
        loyer_mensuel_hc = st.number_input("Loyer mensuel HC (€/mois)", min_value=100, max_value=50000, value=950, step=25)
        charges_annuelles = st.number_input("Charges annuelles (€/an)", min_value=0, max_value=100000, value=2600, step=100)
        tmi = st.selectbox("TMI (%)", options=[0, 11, 30, 41, 45], index=2)
        taux_reemploi = st.slider("Rendement net cible réemploi (%)", min_value=2.0, max_value=9.0, value=5.0, step=0.25)

    loyer_annuel = loyer_mensuel_hc * 12
    annuite_credit = mensualite_credit * 12
    capital_amorti_an = max(0.0, annuite_credit - interets_annuels)

    tab_lmnp, tab_pinel, tab_sci = st.tabs([
        "🛋️ Cas 1 : LMNP",
        "📉 Cas 2 : Fin de Pinel",
        "🏢 Cas 3 : SCI à l'IR"
    ])

    # --- ONGLET 1 : LMNP ---
    with tab_lmnp:
        st.subheader("Diagnostic : Loueur en Meublé Non Professionnel (LMNP)")
        regime_lmnp = st.radio("Régime fiscal", ["Réel Simplifié", "Micro-BIC"], horizontal=True)
        
        base_imposable_lmnp = (loyer_annuel - charges_annuelles - interets_annuels - 4500) if regime_lmnp == "Réel Simplifié" else (loyer_annuel * 0.50)
        base_imposable_lmnp = max(0.0, base_imposable_lmnp)
        
        impot_loyers_lmnp = base_imposable_lmnp * ((tmi / 100.0) + 0.172)
        cashflow_annuel_lmnp = loyer_annuel - charges_annuelles - annuite_credit - impot_loyers_lmnp
        enrichissement_lmnp = cashflow_annuel_lmnp + capital_amorti_an

        pv_lmnp = calcul_plus_value_immobiliere(valeur_venale, prix_achat, annees_detention, utiliser_forfait_frais=forfait_frais, utiliser_forfait_travaux=forfait_travaux)
        capital_net_lmnp = max(1.0, valeur_venale - crd - pv_lmnp["total_impot"] - ira_estimees)
        roe_lmnp = (enrichissement_lmnp / capital_net_lmnp) * 100

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Capital Net Vendeur", f"{capital_net_lmnp:,.0f} €".replace(",", " "))
        m2.metric("Cash-Flow Mensuel", f"{cashflow_annuel_lmnp / 12:,.0f} € / mois".replace(",", " "))
        m3.metric("Impôt Plus-Value", f"{pv_lmnp['total_impot']:,.0f} €".replace(",", " "))
        m4.metric("ROE (Fonds Propres)", f"{roe_lmnp:.2f} % / an")

    # --- ONGLET 2 : PINEL ---
    with tab_pinel:
        st.subheader("Diagnostic : Sortie de Dispositif Pinel")
        revenu_foncier_imposable = max(0.0, loyer_annuel - charges_annuelles - interets_annuels)
        impot_foncier_nu = revenu_foncier_imposable * ((tmi / 100.0) + 0.172)
        cf_apres_pinel = loyer_annuel - charges_annuelles - annuite_credit - impot_foncier_nu
        
        pv_pinel = calcul_plus_value_immobiliere(valeur_venale, prix_achat, annees_detention, utiliser_forfait_frais=forfait_frais, utiliser_forfait_travaux=forfait_travaux)
        capital_net_pinel = max(1.0, valeur_venale - crd - pv_pinel["total_impot"] - ira_estimees)
        roe_pinel = ((cf_apres_pinel + capital_amorti_an) / capital_net_pinel) * 100

        k1, k2, k3 = st.columns(3)
        k1.metric("Effort Épargne Post-Pinel", f"{cf_apres_pinel / 12:,.0f} € / mois".replace(",", " "))
        k2.metric("Plafond Vente Exonéré", f"{pv_pinel['prix_acq_majore']:,.0f} €".replace(",", " "))
        k3.metric("ROE Post-Pinel", f"{roe_pinel:.2f} % / an")

    # --- ONGLET 3 : SCI ---
    with tab_sci:
        st.subheader("Diagnostic : SCI à l'IR")
        qp = 1.0
        resultat_foncier_client = max(0.0, loyer_annuel - charges_annuelles - interets_annuels) * qp
        impot_associe_ir = resultat_foncier_client * ((tmi / 100.0) + 0.172)
        tresorerie_nette_client_ir = ((loyer_annuel - charges_annuelles - annuite_credit) * qp) - impot_associe_ir

        pv_sci = calcul_plus_value_immobiliere(valeur_venale, prix_achat, annees_detention, utiliser_forfait_frais=forfait_frais, utiliser_forfait_travaux=forfait_travaux)
        capital_net_sci = max(1.0, valeur_venale - crd - pv_sci["total_impot"] - ira_estimees)
        roe_sci = ((tresorerie_nette_client_ir + (capital_amorti_an * qp)) / capital_net_sci) * 100

        s1, s2, s3 = st.columns(3)
        s1.metric("Impôt Associé (IR)", f"{impot_associe_ir:,.0f} € / an".replace(",", " "))
        s2.metric("Trésorerie Nette", f"{tresorerie_nette_client_ir / 12:,.0f} € / mois".replace(",", " "))
        s3.metric("ROE SCI", f"{roe_sci:.2f} % / an")

    # --- SYNTHÈSE HOGUET ---
    st.divider()
    st.subheader("📄 Synthèse & Rapport Client")
    with st.expander("Afficher le texte de synthèse préparatoire", expanded=False):
        date_jour = date.today().strftime("%d/%m/%Y")
        synthese_texte = f"""SYNTHÈSE D'ANALYSE D'ARBITRAGE IMMOBILIER
Cabinet Privé Immobilier Honorat — Loi Hoguet
Date : {date_jour} | Dossier : {nom_client} ({ville_bien})
------------------------------------------------------------------------
- Valeur vénale actuelle : {valeur_venale:,.0f} €
- Capital Net Vendeur estimé : {capital_net_lmnp:,.0f} €
- Rendement des Fonds Propres (ROE) : {roe_lmnp:.2f} % / an

CADRE LÉGAL : Simulation indicative réalisée à titre accessoire à une estimation immobilière (Loi 70-9 du 2 janvier 1970).
""".replace(",", " ")
        st.code(synthese_texte, language="text")

if __name__ == "__main__":
    render_audit_patrimonial()
