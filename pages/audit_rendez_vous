from datetime import datetime
import os
import pandas as pd
import streamlit as st

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="Audit en Rendez-Vous - Cabinet Honorat", page_icon="📝", layout="wide"
)

st.title("📝 Parcours Interactif d'Audit Patrimonial en Rendez-Vous")
st.markdown(
    "Outil d'accompagnement client en face-à-face : tronc commun, cas d'optimisation fiscale, "
    "simulation de cession et édition de la synthèse exclusive."
)

# --- MOTEUR DE CALCUL DES PLUS-VALUES ---
def calcul_abattement_plus_value(annees_detention):
    abattement_ir = 0
    abattement_ps = 0
    if annees_detention > 5:
        if annees_detention <= 21:
            abattement_ir = (annees_detention - 5) * 6
        elif annees_detention >= 22:
            abattement_ir = 100
        if annees_detention <= 21:
            abattement_ps = (annees_detention - 5) * 1.65
        elif annees_detention == 22:
            abattement_ps = 28
        elif 22 < annees_detention < 30:
            abattement_ps = 28 + ((annees_detention - 22) * 9)
        elif annees_detention >= 30:
            abattement_ps = 100
    return min(abattement_ir, 100), min(abattement_ps, 100)

# --- BARRE LATÉRALE : ÉTAPES DU RENDEZ-VOUS ---
st.sidebar.header("🧭 Navigation Rendez-Vous")
etape_rdv = st.sidebar.radio(
    "Étapes de l'entretien client :",
    [
        "1. Tronc Commun (Découverte Actif)",
        "2. Cas n°1 : Audit LMNP & Amortissements",
        "3. Cas n°2 : Fin de Pinel & Bilan Fiscal",
        "4. Cas n°3 : Bouclier Fiscal & Plus-Values",
        "5. Étape Finale : Synthèse & Mandat Exclusif"
    ]
)

# --- ÉTAPE 1 : TRONC COMMUN ---
if etape_rdv.startswith("1."):
    st.subheader("📍 Tronc Commun : Découverte et Qualification du Bien")
    st.write("Renseignez les éléments de base recueillis auprès du propriétaire pour initialiser l'étude.")
    
    col1, col2 = st.columns(2)
    with col1:
        st.session_state['client_nom'] = st.text_input("Nom du propriétaire / SCI", value=st.session_state.get('client_nom', ''))
        st.session_state['client_adresse'] = st.text_input("Adresse du bien à Nice", value=st.session_state.get('client_adresse', ''))
        st.session_state['client_surface'] = st.number_input("Surface (m²)", min_value=9.0, value=st.session_state.get('client_surface', 60.0))
    with col2:
        st.session_state['client_annee'] = st.number_input("Année d'acquisition", min_value=1950, max_value=datetime.now().year, value=st.session_state.get('client_annee', 2016))
        st.session_state['client_prix_acq'] = st.number_input("Prix d'acquisition (€)", min_value=10000, value=st.session_state.get('client_prix_acq', 200000))
        st.session_state['client_valeur_actuelle'] = st.number_input("Estimation vénale actuelle (€)", min_value=10000, value=st.session_state.get('client_valeur_actuelle', 300000))
        st.session_state['client_dpe'] = st.selectbox("Note DPE", ["A", "B", "C", "D", "E", "F", "G"], index=3)

    st.success("✅ Tronc Commun validé. Vous pouvez passer aux cas particuliers dans la barre latérale.")

# --- ÉTAPE 2 : CAS N°1 (LMNP) ---
elif etape_rdv.startswith("2."):
    st.subheader("💼 Cas n°1 : Audit LMNP & Amortissements")
    st.markdown("Analyse de la situation d'un investisseur en Loueur Meublé Non Professionnel (Réel / Amortissements).")
    
    loyer_annuel = st.number_input("Loyer annuel perçu (€)", value=12000)
    charges_annuelles = st.number_input("Charges et intérêts d'emprunt annuels (€)", value=4000)
    stock_amortissements = st.number_input("Stock d'amortissements non déduits / reportables (€)", value=15000)
    
    st.info(
        f"**Analyse LMNP :** Pour un loyer de {loyer_annuel} €, la déduction des charges et des amortissements permet généralement de neutraliser "
        f"la fiscalité (BIC). Néanmoins, la question de la sortie ou de l'arbitrage se pose dès que le stock d'amortissements arrive à saturation."
    )

# --- ÉTAPE 3 : CAS N°2 (PINEL) ---
elif etape_rdv.startswith("3."):
    st.subheader("📊 Cas n°2 : Fin de Pinel & Bilan Fiscal")
    st.markdown("Étude de sortie pour les investisseurs dont l'engagement fiscal de 6 ou 9 ans arrive à échéance.")
    
    annees_coulees = st.number_input("Nombre d'années écoulées depuis l'achat", min_value=1, max_value=15, value=9)
    
    if annees_coulees >= 9:
        st.warning("⚠️ **Sortie de dispositif Pinel :** L'avantage fiscal s'arrête. Le rendement net baisse mécaniquement et la fiscalité s'applique.")
    else:
        st.info("ℹ️ L'engagement fiscal est toujours en cours. Aucune urgence de cession immédiate, sauf opportunité de marché.")

# --- ÉTAPE 4 : CAS N°3 (BOUCLIER FISCAL & PLUS-VALUES) ---
elif etape_rdv.startswith("4."):
    st.subheader("⚖️ Cas n°3 : Bouclier Fiscal, Plus-Values & Exonération")
    st.markdown("Simulation précise de la fiscalité de cession en fonction de la durée de détention.")
    
    annee_acq = st.session_state.get('client_annee', 2016)
    val_actuelle = st.session_state.get('client_valeur_actuelle', 300000)
    prix_acq = st.session_state.get('client_prix_acq', 200000)
    
    detention = datetime.now().year - annee_acq
    pv_brute = val_actuelle - prix_acq
    abat_ir, abat_ps = calcul_abattement_plus_value(detention)
    
    impot_ir = max(0, pv_brute * (1 - abat_ir/100) * 0.19)
    impot_ps = max(0, pv_brute * (1 - abat_ps/100) * 0.172)
    total_impot = impot_ir + impot_ps
    net_vendeur = val_actuelle - total_impot
    
    col_res1, col_res2, col_res3 = st.columns(3)
    col_res1.metric("Plus-Value Brute", f"{pv_brute:,.0f} €")
    col_res2.metric("Impôt Total (IR + PS)", f"{total_impot:,.0f} €")
    col_res3.metric("Capital Net Vendeur", f"{net_vendeur:,.0f} €")
    
    st.write(f"Durée de détention : **{detention} ans** (Abattement IR : {abat_ir}% | Abattement PS : {abat_ps}%)")

# --- ÉTAPE 5 : ÉTAPE FINALE (SYNTHÈSE & MANDAT EXCLUSIF) ---
elif etape_rdv.startswith("5."):
    st.subheader("📄 Étape Finale : Synthèse de l'Entretien & Mandat Exclusif")
    st.write("Générez la synthèse complète à remettre au client et préparez la signature du mandat exclusif de vente.")
    
    nom = st.session_state.get('client_nom', 'Propriétaire')
    adresse = st.session_state.get('client_adresse', 'Nice')
    valeur = st.session_state.get('client_valeur_actuelle', 300000)
    
    st.markdown("---")
    st.markdown(f"### 📋 SYNTHÈSE DU CABINET HONORAT — Dossier de {nom}")
    st.write(f"**Bien :** {adresse} | **Avis de valeur retenu :** {valeur:,.0f} €")
    
    st.markdown("#### 🚀 Proposition de Mandat Exclusif de Représentation")
    st.success(
        f"En signant un mandat exclusif avec le **Cabinet Privé Immobilier Honorat**, vous bénéficiez d'une "
        "stratégie de commercialisation sur-mesure pour garantir la vente au meilleur prix net vendeur."
    )
    
    signature_cabinet = (
        "<br><p style='text-align: right;'><em>Document établi par Nathalie Parra</em><br>"
        "<strong>CABINET PRIVÉ IMMOBILIER HONORAT</strong><br>"
        "AUDIT . TRANSACTION . CONSEIL<br><br>"
        "---<br>"
        "<em>Nathalie Parra — Titulaire de la carte professionnelle CPI délivrée par la CCI Nice Côte d'Azur</em><br>"
        "<em>Membre de la FNAIM</em></p>"
    )
    st.markdown(signature_cabinet, unsafe_allow_html=True)
