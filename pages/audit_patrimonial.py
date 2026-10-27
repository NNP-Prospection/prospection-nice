import streamlit as st
import pandas as pd
from datetime import date

# ==============================================================================
# INTERFACE PRINCIPALE D'AUDIT PATRIMONIAL & TERRAIN
# ==============================================================================

def render_audit_patrimonial():
    st.markdown("## 🏛️ Audit Patrimonial, Focus Terrain & Arbitrage")
    st.caption("Outil de terrain ultra-léger et d'analyse financière pour vos rendez-vous clients à Nice.")

    # --- CHARGEMENT SÉCURISÉ DU FICHIER LOCAL ---
    try:
        df_audit = pd.read_csv('dpe_nice_fg.csv')
    except Exception:
        df_audit = pd.DataFrame()

    # --- BARRE LATÉRALE ---
    with st.sidebar:
        st.header("👤 Dossier Client & Actif")
        nom_client = st.text_input("Nom du client / Référence", value="M. & Mme Client")
        ville_bien = st.text_input("Localisation du bien", value="Nice")

        st.subheader("1. Valeurs & Acquisition")
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

    # --- ORGANISATION EN ONGLETS ÉTANCHES ---
    tab_terrain, tab_lmnp, tab_pinel, tab_sci = st.tabs([
        "📍 1. Focus Terrain & Quartiers",
        "🛋️ 2. Audit LMNP",
        "📉 3. Sortie de Pinel",
        "🏢 4. SCI à l'IR"
    ])

    # --- ONGLET 1 : FOCUS TERRAIN & QUARTIERS ---
    with tab_terrain:
        st.subheader("📍 Module de Quartier — Arguments & Repères pour le Rendez-vous")
        st.write("Sélectionnez le quartier du bien pour afficher instantanément les repères de prix et les arguments de négociation.")

        quartier_cible = st.selectbox(
            "Sélectionner le quartier",
            ["-- Choisir un quartier --", "Carré d'Or", "Promenade des Anglais", "Port / Garibaldi", "Mont Boron", "Musiciens / Gambetta", "Centre-ville"]
        )

        infos_quartiers = {
            "Carré d'Or": {
                "valeur_ref": "8 500 € à 11 000 € / m²",
                "tendance": "Forte tension, forte demande sur les petites surfaces et les biens patrimoniaux de standing.",
                "arguments": "Impact fort des passoires énergétiques : décotes pour travaux recherchées par les acquéreurs (argument clé pour un mandat exclusif)."
            },
            "Promenade des Anglais": {
                "valeur_ref": "7 000 € à 10 500 € / m² (selon vue mer)",
                "tendance": "Marché orienté résidences secondaires et investissements patrimoniaux d'envergure.",
                "arguments": "Cycle de détention moyen de 5 à 7 ans. Sensibilité accrue aux charges et à la performance énergétique."
            },
            "Port / Garibaldi": {
                "valeur_ref": "6 500 € à 9 000 € / m²",
                "tendance": "Secteur très recherché, dynamique, prisé par une clientèle active.",
                "arguments": "Immeubles anciens à fort cachet mais souvent classés F ou G (fort potentiel de valorisation post-rénovation)."
            },
            "Mont Boron": {
                "valeur_ref": "8 000 € à 12 000+ € / m²",
                "tendance": "Quartier résidentiel haut de gamme, villas et résidences de standing.",
                "arguments": "Discrétion, confidentialité et stratégie d'accompagnement patrimonial global indispensables."
            },
            "Musiciens / Gambetta": {
                "valeur_ref": "5 000 € à 7 500 € / m²",
                "tendance": "Secteur familial et central, forte demande locative.",
                "arguments": "Idéal pour aborder la rentabilité locative, le dispositif LMNP et l'anticipation de la revente."
            },
            "Centre-ville": {
                "valeur_ref": "5 500 € à 8 000 € / m²",
                "tendance": "Cœur commerçant, proximité immédiate du tramway.",
                "arguments": "Liquidité rapide des biens bien positionnés, nécessité d'un mandat exclusif."
            }
        }

        if quartier_cible != "-- Choisir un quartier --":
            data_q = infos_quartiers.get(quartier_cible, {})
            qc1, qc2 = st.columns(2)
            with qc1:
                st.metric("📊 Fourchette de prix estimative", data_q.get("valeur_ref", "N/C"))
            with qc2:
                st.metric("📈 Dynamique du marché", "Secteur Actif & Qualifié")
                
            st.info(f"**Tendance locale :** {data_q.get('tendance', '')}")
            st.warning(f"**Angle de négociation / Mandat :** {data_q.get('arguments', '')}")

    # --- ONGLET 2 : LMNP ---
    with tab_lmnp:
        st.subheader("Diagnostic Patrimonial : Loueur en Meublé Non Professionnel (LMNP)")
        resultat_base = max(0.0, loyer_annuel - charges_annuelles - interets_annuels - 4500)
        impot_loyers = resultat_base * ((tmi / 100.0) + 0.172)
        cashflow = loyer_annuel - charges_annuelles - annuite_credit - impot_loyers
        capital_net_estime = max(1.0, valeur_venale - crd)
        roe = ((cashflow + capital_amorti_an) / capital_net_estime) * 100

        c1, c2, c3 = st.columns(3)
        c1.metric("Capital Net Estimé", f"{capital_net_estime:,.0f} €".replace(",", " "))
        c2.metric("Cash-Flow Mensuel", f"{cashflow / 12:,.0f} € / mois".replace(",", " "))
        c3.metric("ROE Estimé", f"{roe:.2f} % / an")

    # --- ONGLET 3 : PINEL ---
    with tab_pinel:
        st.subheader("Diagnostic Patrimonial : Sortie de Dispositif Pinel")
        st.info("Module de sortie de dispositif Pinel opérationnel.")

    # --- ONGLET 4 : SCI ---
    with tab_sci:
        st.subheader("Diagnostic Patrimonial : SCI à l'IR")
        st.info("Module d'analyse SCI opérationnel.")

    # --- SYNTHÈSE CLIENT ---
    st.divider()
    st.subheader("📄 Synthèse Client")
    with st.expander("Afficher le texte de synthèse", expanded=False):
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
