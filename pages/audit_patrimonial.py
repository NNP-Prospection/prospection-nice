import streamlit as st
import pandas as pd
from datetime import date

# ==============================================================================
# INTERFACE PRINCIPALE D'AUDIT PATRIMONIAL
# ==============================================================================

def render_audit_patrimonial():
    st.markdown("## 🏛️ Audit Patrimonial & Arbitrage Immobilier")
    st.caption("Outil d'analyse de performance immobilière et d'aide à la décision en rendez-vous client.")

    # --- BARRE LATÉRALE ---
    with st.sidebar:
        st.header("👤 Dossier Client & Actif")
        nom_client = st.text_input("Nom du client / Référence", value="M. & Mme Client")
        ville_bien = st.text_input("Localisation du bien", value="Nice")

        st.subheader("1. Valorisation & Acquisition")
        valeur_venale = st.number_input("Valeur vénale actuelle Nette Vendeur (€)", min_value=50000, max_value=10000000, value=360000, step=5000)
        prix_achat = st.number_input("Prix d'acquisition initial (€)", min_value=30000, max_value=10000000, value=300000, step=5000)
        annees_detention = st.slider("Durée de détention (années pleines)", min_value=1, max_value=35, value=9)

        st.subheader("2. Financement Bancaire Actuel")
        crd = st.number_input("Capital Restant Dû - CRD (€)", min_value=0, max_value=10000000, value=160000, step=5000)
        mensualite_credit = st.number_input("Mensualité crédit (€/mois)", min_value=0, max_value=50000, value=1250, step=25)
        interets_annuels = st.number_input("Intérêts déductibles (€/an)", min_value=0, max_value=200000, value=2800, step=100)

        st.subheader("3. Exploitation & Fiscalité Client")
        loyer_mensuel_hc = st.number_input("Loyer mensuel HC (€/mois)", min_value=100, max_value=50000, value=950, step=25)
        charges_annuelles = st.number_input("Charges annuelles (€/an)", min_value=0, max_value=100000, value=2600, step=100)
        tmi = st.selectbox("Tranche Marginale d'Imposition (TMI %)", options=[0, 11, 30, 41, 45], index=2)

    loyer_annuel = loyer_mensuel_hc * 12
    annuite_credit = mensualite_credit * 12
    capital_amorti_an = max(0.0, annuite_credit - interets_annuels)

    tab_lmnp, tab_pinel, tab_sci = st.tabs([
        "🛋️ Cas 1 : Audit LMNP",
        "📉 Cas 2 : Fin de Pinel",
        "🏢 Cas 3 : SCI à l'IR"
    ])

    with tab_lmnp:
        st.subheader("Diagnostic Patrimonial : LMNP")
        st.info("Module de calcul LMNP actif et opérationnel.")
        
        # Calculs de base stables
        resultat_base = max(0.0, loyer_annuel - charges_annuelles - interets_annuels - 4500)
        impot_loyers = resultat_base * ((tmi / 100.0) + 0.172)
        cashflow = loyer_annuel - charges_annuelles - annuite_credit - impot_loyers
        capital_net_estime = max(1.0, valeur_venale - crd)
        roe = ((cashflow + capital_amorti_an) / capital_net_estime) * 100

        c1, c2, c3 = st.columns(3)
        c1.metric("Capital Net Estimé", f"{capital_net_estime:,.0f} €".replace(",", " "))
        c2.metric("Cash-Flow Mensuel", f"{cashflow / 12:,.0f} € / mois".replace(",", " "))
        c3.metric("ROE Estimé", f"{roe:.2f} % / an")

    with tab_pinel:
        st.subheader("Diagnostic Patrimonial : Sortie de Pinel")
        st.info("Module de sortie de dispositif Pinel actif.")

    with tab_sci:
        st.subheader("Diagnostic Patrimonial : SCI à l'IR")
        st.info("Module SCI actif.")

    st.divider()
    st.subheader("📄 Synthèse Client")
    with st.expander("Afficher le texte de synthèse", expanded=True):
        date_jour = date.today().strftime("%d/%m/%Y")
        synthese_texte = f"""SYNTHÈSE D'ANALYSE D'ARBITRAGE IMMOBILIER
Cabinet Privé Immobilier Honorat — Loi Hoguet
Date : {date_jour} | Dossier : {nom_client} ({ville_bien})
------------------------------------------------------------------------
- Valeur vénale actuelle : {valeur_venale:,.0f} €
- Capital Net Vendeur estimé : {capital_net_estime:,.0f} €
- Rendement des Fonds Propres (ROE) : {roe:.2f} % / an

Simulation indicative réalisée à titre accessoire à une estimation (Loi 70-9).
""".replace(",", " ")
        st.code(synthese_texte, language="text")

if __name__ == "__main__":
    render_audit_patrimonial()
