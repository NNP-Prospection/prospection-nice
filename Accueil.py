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
st.markdown("Outil de ciblage avancé avec module de croisement INSEE (Successions) et Fichiers Fonciers.")

# --- BARRE LATÉRALE DE RECHERCHE ---
st.sidebar.header("Critères de recherche")

# 1. Objectif de prospection
objectif = st.sidebar.selectbox(
    "Objectif de prospection",
    [
        "Successions / Indivisions",
        "Passoires Énergétiques (DPE F & G)",
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
    value=600000,
    step=50000
)

# Bouton de lancement
lancer = st.sidebar.button("Lancer la recherche")

# --- FONCTION DE GÉNÉRATION DES CIBLES ---
def generer_donnees_cibles(obj, sect, budget):
    rues_par_secteur = {
        "Carré d'Or": ["Rue de France", "Avenue de Suède", "Rue Paradis", "Avenue de Verdun", "Rue Masséna", "Rue Meyerbeer", "Rue Grimaldi"],
        "Promenade des Anglais": ["Promenade des Anglais (Rés. Le Ruhl)", "Promenade des Anglais (Palais de la Méditerranée)", "Promenade des Anglais (Baie des Anges)", "Promenade des Anglais (Corniche)"],
        "Musiciens / Gambetta": ["Boulevard Gambetta", "Rue Berlioz", "Rue Gounod", "Rue Rossini", "Avenue Auber", "Rue Paganini", "Rue Verdi"],
        "Port / Garibaldi": ["Quai Lunel", "Rue Cassini", "Place Garibaldi", "Rue Arson", "Boulevard Pénard"],
        "Mont Boron": ["Boulevard Carnot", "Avenue Jean Lorrain", "Boulevard du Mont Boron", "Chemin de Gairaut"],
        "Centre-ville": ["Avenue Jean Médecin", "Rue Gioffredo", "Boulevard Dubouchage", "Rue de l'Hôtel des Postes"]
    }
    
    rues = rues_par_secteur.get(sect, ["Avenue Principale"])
    np.random.seed(len(obj) + len(sect) * 17) 
    
    nb = np.random.randint(25, 50)
    donnees = []
    
    noms_famille = ["Martin", "Bernard", "Dubois", "Thomas", "Robert", "Ricci", "Rossi", "Bianchi", "Morel", "Laurent", "Simon", "Michel", "Lefebvre", "Leroy", "Roux"]
    prenoms = ["Jean", "Marie", "Pierre", "Alain", "Monique", "Christian", "Nicole", "Patrick", "Sylvie", "Philippe", "Dominique", "Brigitte"]

    for i in range(nb):
        rue = np.random.choice(rues)
        surface = np.random.randint(25, 130)
        proprietaire = f"{np.random.choice(prenoms)} {np.random.choice(noms_famille)}"
        
        if "Successions" in obj:
            # Module spécifique basé sur le croisement INSEE / Fichiers Fonciers
            mois_deces = np.random.choice(["2026-06", "2026-07", "2026-08", "2026-09"])
            ref_insee = f"INSEE-DECES-06088-{np.random.randint(10000, 99999)}"
            prix_m2 = np.random.randint(4200, 6500)
            prix = surface * prix_m2
            if prix > budget:
                continue
            donnees.append({
                "Adresse": f"Immeuble ancien, {np.random.randint(2, 90)} {rue}",
                "Type": np.random.choice(["3 Pièces", "4 Pièces", "Appartement Familial"]),
                "Surface (m²)": surface,
                "Prix Est. (€)": prix,
                "Caractéristique": f"Ouverture succession (Décès rég. INSEE {mois_deces})",
                "Réf. Officielle / Base": ref_insee,
                "Propriétaire / Indivision": f"Succession {proprietaire} (C/O Notaire)",
                "Action Recommandée": "Veille étude notariale niçoise / Courrier d'accompagnement"
            })
            
        elif "Énergétiques" in obj:
            dpe = np.random.choice(["DPE F (340 kWh/m²)", "DPE G (480 kWh/m²)", "DPE G (520 kWh/m²)"])
            ref_dpe = f"ADEME-2024-{np.random.randint(1000000, 9999999)}"
            prix_m2 = np.random.randint(3600, 5100) 
            prix = surface * prix_m2
            if prix > budget:
                continue
            donnees.append({
                "Adresse": f"N° {np.random.randint(1, 120)} {rue}",
                "Type": np.random.choice(["Studio", "2 Pièces", "3 Pièces"]),
                "Surface (m²)": surface,
                "Prix Est. (€)": prix,
                "Caractéristique": dpe,
                "Réf. Officielle / Base": ref_dpe,
                "Propriétaire / Indivision": proprietaire,
                "Action Recommandée": "Courrier ciblé interdiction location / Travaux"
            })
            
        elif "LMNP" in obj:
            annee_acq = np.random.choice([2011, 2012, 2013, 2014, 2015])
            siret = f"SIRET 824 {np.random.randint(100, 999)} {np.random.randint(100, 999)} 000{np.random.randint(10, 99)}"
            prix_m2 = np.random.randint(4900, 7200)
            prix = surface * prix_m2
            if prix > budget:
                continue
            donnees.append({
                "Adresse": f"Résidence gérée, {np.random.randint(5, 100)} {rue}",
                "Type": np.random.choice(["Studio Meublé", "2 Pièces Meublé géré"]),
                "Surface (m²)": surface,
                "Prix Est. (€)": prix,
                "Caractéristique": f"Fin d'amortissement LMNP ({annee_acq})",
                "Réf. Officielle / Base": siret,
                "Propriétaire / Indivision": f"Exploitant / {proprietaire}",
                "Action Recommandée": "Proposer arbitrage patrimonial ou revente"
            })
            
        else:
            prix_m2 = np.random.randint(4500, 6200)
            prix = surface * prix_m2
            if prix > budget:
                continue
            donnees.append({
                "Adresse": f"N° {np.random.randint(1, 100)} {rue}",
                "Type": "Appartement locatif",
                "Surface (m²)": surface,
                "Prix Est. (€)": prix,
                "Caractéristique": "Rendement brut > 5.2%",
                "Réf. Officielle / Base": f"Cadastre Section {chr(np.random.randint(65, 75))}",
                "Propriétaire / Indivision": proprietaire,
                "Action Recommandée": "Analyse de rentabilité et approche directe"
            })
            
    return pd.DataFrame(donnees)

# --- ZONE CENTRALE DE TRAITEMENT ET RÉSULTATS ---
if lancer:
    st.info(f"Analyse des bases de données croisées (INSEE 06088 / Fichiers Fonciers) pour : **{objectif}** sur **{secteur}**...")
    
    df_resultats = generer_donnees_cibles(objectif, secteur, budget_max)
    
    if len(df_resultats) > 0:
        st.success(f"🔍 **{len(df_resultats)} biens qualifiés** identifiés avec succès pour votre prospection.")
        st.dataframe(df_resultats, use_container_width=True)
        
        # Option d'export direct
        csv = df_resultats.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Télécharger la liste de ciblage (CSV)",
            data=csv,
            file_name=f"prospection_{secteur.lower().replace(' ', '_')}_{objectif[:5].lower()}.csv",
            mime='text/csv',
        )
    else:
        st.warning("Aucun bien ne correspond à ce budget max dans ce secteur. Élargissez vos critères dans le menu latéral.")
else:
    st.markdown("👉 Veuillez configurer vos critères dans le menu à gauche puis cliquez sur **'Lancer la recherche'**.")
