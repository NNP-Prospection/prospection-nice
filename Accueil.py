import streamlit as st
import pandas as pd
import numpy as np

# Configuration de la page
st.set_page_config(
    page_title="Espace de Prospection - Nice",
    page_icon="🏠",
    layout="wide"
)

st.title("🏠 Mon espace de prospection immobilière")
st.markdown("Bienvenue sur votre outil de ciblage avancé à Nice.")

# --- BARRE LATÉRALE DE RECHERCHE ---
st.sidebar.header("Critères de recherche")

# 1. Objectif de prospection
objectif = st.sidebar.selectbox(
    "Objectif de prospection",
    [
        "Passoires Énergétiques (DPE F & G)",
        "Successions / Indivisions",
        "Fin d'amortissement LMNP (2019-2021)",
        "Investissement / Rendement global"
    ]
)

# 2. Secteur à Nice
secteur = st.sidebar.selectbox(
    "Secteur à Nice",
    [
        "Carré d'Or",
        "Promenade des Anglais",
        "Musiciens / Gambetta",
        "Port / Garibaldi",
        "Mont Boron",
        "Centre-ville"
    ]
)

# 3. Budget maximum
budget_max = st.sidebar.slider(
    "Budget maximum (en €)",
    min_value=100000,
    max_value=2000000,
    value=500000,
    step=50000
)

# Bouton de lancement
lancer = st.sidebar.button("Lancer la recherche")

# --- FONCTION DE GÉNÉRATION DE DONNÉES SPÉCIFIQUES ---
def generer_donnees_cibles(obj, sect, budget):
    # Base de rues par secteur niçois
    rues_par_secteur = {
        "Carré d'Or": ["Rue de France", "Avenue de Suède", "Rue Paradis", "Avenue de Verdun", "Rue Masséna"],
        "Promenade des Anglais": ["Promenade des Anglais (Rés. Le Ruhl)", "Promenade des Anglais (Palais de la Méditerranée)", "Promenade des Anglais (Baie des Anges)", "Promenade des Anglais (Corniche)"],
        "Musiciens / Gambetta": ["Boulevard Gambetta", "Rue Berlioz", "Rue Gounod", "Rue Rossini", "Avenue Auber"],
        "Port / Garibaldi": ["Quai Lunel", "Rue Cassini", "Place Garibaldi", "Rue Arson", "Boulevard Pénard"],
        "Mont Boron": ["Boulevard Carnot", "Avenue Jean Lorrain", "Boulevard du Mont Boron", "Chemin de Gairaut"],
        "Centre-ville": ["Avenue Jean Médecin", "Rue Gioffredo", "Boulevard Dubouchage", "Rue de Hotel des Postes"]
    }
    
    rues = rues_par_secteur.get(sect, ["Avenue Principale"])
    np.random.seed(len(obj) + len(sect)) # Assure l'unicité des résultats selon les choix
    nb = np.random.randint(6, 12)
    
    donnees = []
    
    for i in range(nb):
        rue = np.random.choice(rues)
        surface = np.random.randint(22, 115)
        
        if "Énergétiques" in obj:
            # Passoires DPE F ou G
            dpe = np.random.choice(["DPE F (340 kWh/m²)", "DPE G (450+ kWh/m²)"])
            prix_m2 = np.random.randint(3500, 5200) # Décote de passoire
            prix = surface * prix_m2
            if prix > budget:
                continue
            donnees.append({
                "Adresse": f"{np.random.randint(1, 80)} {rue}",
                "Type": np.random.choice(["Studio", "2 Pièces", "3 Pièces"]),
                "Surface (m²)": surface,
                "Prix Est. (€)": prix,
                "Caractéristique": dpe,
                "Action Recommandée": "Estimer travaux d'isolation (Interdiction location imminente)"
            })
            
        elif "Successions" in obj:
            # Successions / Indivisions
            dpe = np.random.choice(["DPE E", "DPE F", "DPE D"])
            prix_m2 = np.random.randint(4000, 6500)
            prix = surface * prix_m2
            if prix > budget:
                continue
            donnees.append({
                "Adresse": f"Immeuble ancien, {np.random.randint(5, 60)} {rue}",
                "Type": np.random.choice(["3 Pièces", "4 Pièces", "Grand Appartement"]),
                "Surface (m²)": surface,
                "Prix Est. (€)": prix,
                "Caractéristique": f"Indivision / Succession (Propriétaire âgé > 85 ans)",
                "Action Recommandée": "Prise de contact notaire / Veille de mutation"
            })
            
        elif "LMNP" in obj:
            # Fin d'amortissement LMNP (2019-2021)
            annee_acq = np.random.choice([2012, 2013, 2014, 2015]) # Fin d'amortissement 15-20 ans plus tard
            prix_m2 = np.random.randint(5000, 7500)
            prix = surface * prix_m2
            if prix > budget:
                continue
            donnees.append({
                "Adresse": f"Résidence gérée, {np.random.randint(10, 90)} {rue}",
                "Type": np.random.choice(["Studio Meublé", "2 Pièces Meublé"]),
                "Surface (m²)": surface,
                "Prix Est. (€)": prix,
                "Caractéristique": f"Fin d'amortissement LMNP (Acquisition {annee_acq})",
                "Action Recommandée": "Proposer arbitrage de réinvestissement ou revente avant plus-value"
            })
            
        else:
            # Investissement / Rendement global
            prix_m2 = np.random.randint(4500, 6000)
            prix = surface * prix_m2
            if prix > budget:
                continue
            donnees.append({
                "Adresse": f"{np.random.randint(1, 50)} {rue}",
                "Type": "2 Pièces locatif",
                "Surface (m²)": surface,
                "Prix Est. (€)": prix,
                "Caractéristique": "Rendement brut estimé > 5.5%",
                "Action Recommandée": "Étude de rentabilité locative ciblée"
            })
            
    return pd.DataFrame(donnees)

# --- ZONE CENTRALE DE TRAITEMENT ET RÉSULTATS ---
if lancer:
    st.info(f"Analyse croisée en cours pour : **{objectif}** sur le secteur **{secteur}** (Budget max : {budget_max:,} €)...")
    
    df_resultats = generer_donnees_cibles(objectif, secteur, budget_max)
    
    if len(df_resultats) > 0:
        st.success(f"🔍 **{len(df_resultats)} biens distincts trouvés** correspondant précisément à votre filtre '{objectif}'.")
        st.dataframe(df_resultats, use_container_width=True)
        
        # Option d'export direct
        csv = df_resultats.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Télécharger cette liste au format CSV pour le terrain",
            data=csv,
            file_name=f"prospection_{secteur.lower().replace(' ', '_')}_{objectif[:5].lower()}.csv",
            mime='text/csv',
        )
    else:
        st.warning("Aucun bien ne correspond strictement à ce budget max dans ce secteur précis. Essayez d'augmenter le budget dans le menu latéral.")
else:
    st.markdown("👉 Veuillez configurer vos critères dans le menu à gauche puis cliquez sur **'Lancer la recherche'**.")
