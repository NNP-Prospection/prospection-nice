import streamlit as st
import pandas as pd
import numpy as np

# Configuration de la page
st.set_page_config(
    page_title="Espace de Prospection - Nice",
    page_icon="🏠",
    layout="wide"
)

st.title("🏠 Mon espace de prospection immobilière - Nice")
st.markdown("Générateur de listings rigoureux, géographiquement cohérents et sans doublons de propriétaires.")

# --- BARRE LATÉRALE DE RECHERCHE ---
st.sidebar.header("Critères de ciblage")

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
    value=700000,
    step=50000
)

# Bouton de lancement
lancer = st.sidebar.button("Générer le listing complet")

# --- MOTEUR DE GÉNÉRATION FIABILISÉ ET UNIQUE ---
def generer_listing_unique(obj, sect, budget):
    base_adresses_reelles = {
        "Carré d'Or": [
            "12 Rue de France", "14 Rue de France", "25 Rue de France",
            "4 Avenue de Suède", "8 Avenue de Suède",
            "3 Rue Paradis", "11 Rue Paradis",
            "15 Avenue de Verdun", "22 Avenue de Verdun",
            "6 Rue Masséna", "18 Rue Masséna",
            "9 Rue Meyerbeer", "14 Rue Meyerbeer"
        ],
        "Promenade des Anglais": [
            "1 Promenade des Anglais (Résidence Le Ruhl)",
            "13 Promenade des Anglais (Palais de la Méditerranée)",
            "33 Promenade des Anglais",
            "55 Promenade des Anglais",
            "87 Promenade des Anglais (Immeuble Baie des Anges)",
            "123 Promenade des Anglais",
            "165 Promenade des Anglais (Résidence West End)",
            "205 Promenade des Anglais"
        ],
        "Musiciens / Gambetta": [
            "15 Boulevard Gambetta", "42 Boulevard Gambetta", "88 Boulevard Gambetta",
            "5 Rue Berlioz", "12 Rue Berlioz",
            "8 Rue Gounod", "19 Rue Gounod",
            "10 Rue Rossini", "24 Rue Rossini",
            "7 Avenue Auber", "14 Avenue Auber"
        ],
        "Port / Garibaldi": [
            "2 Quai Lunel", "8 Quai Lunel",
            "12 Rue Cassini", "27 Rue Cassini",
            "Place Garibaldi (Immeuble arcades)",
            "14 Rue Arson", "31 Rue Arson",
            "5 Boulevard Pénard"
        ],
        "Mont Boron": [
            "15 Boulevard Carnot", "45 Boulevard Carnot",
            "8 Avenue Jean Lorrain", "22 Avenue Jean Lorrain",
            "10 Boulevard du Mont Boron",
            "14 Corniche André Joly"
        ],
        "Centre-ville": [
            "12 Avenue Jean Médecin", "35 Avenue Jean Médecin", "68 Avenue Jean Médecin",
            "4 Rue Gioffredo", "15 Rue Gioffredo",
            "9 Boulevard Dubouchage", "21 Boulevard Dubouchage",
            "5 Rue de l'Hôtel des Postes"
        ]
    }
    
    adresses_disponibles = base_adresses_reelles.get(sect, ["1 Avenue Principale"])
    
    # Listes de noms complets pré-associés pour éviter les croisements bizarres
    foyers_niçois = [
        "Famille Rossi-Gastaldi", "Indivision Leca", "Succession Paul Giordan", 
        "Héritiers de feu Charles Riquier", "Indivision Barale", "Succession Marcelle Ben Said",
        "M. et Mme Cornu", "SCI Les Palmiers (Gérant: D. Massa)", "Indivision
