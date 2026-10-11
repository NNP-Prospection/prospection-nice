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
