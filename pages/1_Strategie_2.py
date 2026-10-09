import streamlit as st
import pandas as pd
from datetime import datetime
import os

st.set_page_config(
    page_title="Stratégie 2 - Investisseurs", 
    page_icon="💼",
    layout="wide"
)

st.title("💼 Stratégie 2 : Investisseurs & Hub Juridique")
st.markdown("Ciblage des fins de cycles fiscaux (Pinel, LMNP) et base de ressources réglementaires (Urbanisme, Fiscalité, DPE).")

@st.cache_data
def load_dpe():
    try:
        return pd.read_csv('dpe_nice_fg.csv', low_memory=False)
    except:
        return pd.DataFrame()

df_dpe = load_dpe()

tab1, tab2 = st.tabs(["✉️ 1. Publipostage Investisseurs", "📚 2. Hub Juridique & Fiscal"])

with tab1:
    st.subheader("Ciblage des investisseurs : Fin d'avantage fiscal + Décote DPE")
    st.write("Ce courrier est optimisé pour les propriétaires bailleurs (LMNP, LMP, Pinel, Denormandie) qui arrivent en fin de cycle de détention et font face à l'interdiction de louer.")
    
    if not df_dpe.empty:
        col_adresse = next((col for col in ['adresse_ban', 'adresse_brute', 'adresse_propriete'] if col in df_dpe.columns), None)
        
        if col_adresse:
            adresses_dispos = df_dpe[col_adresse].dropna().unique().tolist()
            adresse_choisie = st.selectbox("📍 Choisir une adresse pour générer le courrier :", adresses_dispos)
            
            date_jour = datetime.now().strftime("%d/%m/%Y")
            
            courrier_investisseur = f"""Nice, le {date_jour}

Destinataire : Propriétaire / Investisseur Bailleur
Concerne l'actif situé au : {adresse_choisie}

Madame, Monsieur,

Objet : Stratégie d'arbitrage de votre actif au {adresse_choisie} (Fin de cycle fiscal & Loi Climat)

En qualité de Conseil en Immobilier Patrimonial, je me permets de vous contacter de manière confidentielle concernant le bien que vous proposez à la location à cette adresse.

Le marché locatif connaît actuellement un double bouleversement :
1. L'échéance des avantages fiscaux initiaux (statuts LMNP/LMP, dispositifs d'amortissement) qui impacte mécaniquement la rentabilité nette de votre investissement.
2. L'application stricte du calendrier de la Loi Climat et Résilience, qui va prochainement interdire la mise en location des biens les plus énergivores, imposant des travaux de rénovation globaux souvent lourds à supporter pour la copropriété.

Avant de subir une décote de la valeur vénale de votre bien sur un marché qui se durcit, l'anticipation est votre meilleur atout. Une revente stratégique à court terme est souvent l'arbitrage le plus judicieux pour sécuriser votre capital et le réinvestir sur des supports plus performants.

Je me tiens à votre entière disposition pour réaliser un audit de valorisation de votre bien et vous accompagner dans vos projets d'arbitrage.

Bien cordialement,

Nathalie Parra
Conseil en Immobilier Patrimonial

CABINET PRIVÉ IMMOBILIER HONORAT
TRANSACTION . CONSEIL . PATRIMOINE"""

            st.text_area(f"📄 Modèle de courrier", courrier_investisseur, height=400)
            logo_path = "Cabinet Immobilier Privé HONORAT.png"
            if os.path.exists(logo_path): 
                st.image(logo_path, width=200)

with tab2:
    st.subheader("📚 Hub Juridique, Fiscal et Urbanisme")
    st.write("Base de consultation rapide pour argumenter vos audits patrimoniaux.")
    
    with st.expander("📝 Loi Climat et Résilience (Calendrier DPE)"):
        st.markdown("""
        **Loi n° 2021-1104 du 22 août 2021 portant lutte contre le dérèglement climatique**
        *   **Geler les loyers :** Depuis le 24 août 2022, interdiction d'augmenter le loyer des logements classés F et G (lors du renouvellement du bail ou de la remise en location).
        *   **Interdiction de mise en location (Critère de décence) :**
            *   **1er janvier 2025 :** Interdiction pour les logements classés **G**.
            *   **1er janvier 2028 :** Interdiction pour les logements classés **F**.
            *   **1er janvier 2034 :** Interdiction pour les logements classés **E**.
        *   **Audit énergétique obligatoire :** Lors de la vente de maisons individuelles ou de monopropriétés classées F ou G (depuis avril 2023), et bientôt E (2025).
        """)

    with st.expander("🏛️ Urbanisme & Droit des Sols (PLU, Permis, Déclarations)"):
        st.markdown("""
        **Code de l'urbanisme et instruction des autorisations**
        *   **Plan Local d'Urbanisme (PLU) :** Définit les règles d'aménagement et d'usage des sols. Indispensable pour évaluer le potentiel de constructibilité ou d'extension d'un foncier lors de l'estimation.
        *   **Déclaration Préalable (DP) :** Obligatoire pour les modifications d'aspect extérieur, les changements de destination (sans travaux porteurs), et les extensions mineures (généralement entre 5 et 20m², ou 40m² en zone U). Délai d'instruction : 1 mois.
        *   **Permis de Construire (PC) :** Requis pour les créations de surface de plancher supérieures à 20m² (ou 40m² en zone U du PLU) et les changements de destination avec modification des structures porteuses. Délai d'instruction : 2 à 3 mois.
        *   **Certificat d'Urbanisme (CU) :** Le CU d'information (CUa) fige les règles d'urbanisme, le CU opérationnel (CUb) valide la faisabilité d'un projet précis.
        """)

    with st.expander("💶 Dispositifs Fiscaux & Amortissements (LMNP, LMP, Pinel, Denormandie)"):
        st.markdown("""
        *   **LMNP (Loueur en Meublé Non Professionnel) :** Permet d'amortir la valeur du bien et des meubles pour gommer la fiscalité des revenus locatifs. Souvent touché par les réformes fiscales récentes, c'est un point d'alerte à soulever lors de l'arbitrage.
        *   **LMP (Loueur en Meublé Professionnel) :** Exige des recettes > 23 000 € ET supérieures aux autres revenus du foyer. Conditions de revente et plus-values professionnelles spécifiques.
        *   **Loi Pinel :** Réduction d'impôt soumise à un engagement de location (6, 9 ou 12 ans). Les investisseurs arrivant au terme de leur engagement (généralement après 9 ans) sont d'excellents prospects pour la revente, l'avantage fiscal n'opérant plus.
        *   **Loi Denormandie :** Prolongement du Pinel dans l'ancien avec travaux (25% du coût total de l'opération). Mêmes logiques de sortie de cycle que le Pinel.
        *   **Dispositif Jean-Brun / Autres :** Connaître le cadre initial de l'acquisition permet de démontrer au propriétaire que son cycle de rentabilité optimal est terminé.
        """)
