import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Stratégie 3 - Chasseur VEFA", page_icon="🏗️", layout="wide")

st.title("🏗️ Stratégie 3 : Radar à Programmes Neufs (Pinel 9 ans)")
st.markdown("Identification algorithmique des résidences neuves livrées autour de 2017 via l'historique DVF (Ventes en l'État Futur d'Achèvement).")

# --- MOTEUR DE RECHERCHE VEFA ---
@st.cache_data
def load_and_find_vefa():
    try:
        # 1. Trouve le dossier DVF
        dossier = next((d for d in os.listdir('.') if os.path.isdir(d) and 'dvf' in d.lower()), None)
        if not dossier: return pd.DataFrame()
            
        fichiers = [os.path.join(dossier, f) for f in os.listdir(dossier) if f.endswith('.csv') or f.endswith('.txt')]
        if not fichiers: return pd.DataFrame()
            
        liste_df = []
        for f in fichiers:
            try:
                # Lecture multi-formats
                df_temp = pd.read_csv(f, sep='|', low_memory=False) 
                if len(df_temp.columns) < 3:
                    df_temp = pd.read_csv(f, sep=',', low_memory=False)
                if len(df_temp.columns) < 3:
                    df_temp = pd.read_csv(f, sep=';', low_memory=False)
                liste_df.append(df_temp)
            except:
                pass
                
        if not liste_df: return pd.DataFrame()
        df = pd.concat(liste_df, ignore_index=True)
        
        # 2. Détecter la colonne de type de vente
        col_nature = next((col for col in ['nature_mutation', 'Nature mutation'] if col in df.columns), None)
        if not col_nature: return pd.DataFrame()
        
        # 3. Filtrer uniquement les VEFA (Achats sur plan)
        df_vefa = df[df[col_nature].astype(str).str.contains("l'état futur d'achèvement|VEFA", case=False, na=False)].copy()
        
        # 4. Reconstruire l'adresse
        def construire_adresse(row):
            num = str(row.get('No voie', row.get('adresse_numero', ''))).replace('.0', '')
            if num == 'nan': num = ''
            voie = str(row.get('Type de voie', '')) + ' ' + str(row.get('Voie', row.get('adresse_nom_voie', '')))
            if voie.startswith('nan '): voie = voie[4:]
            commune = str(row.get('Commune', row.get('nom_commune', '')))
            return f"{num} {voie} {commune}".strip()
            
        df_vefa['Adresse_Immeuble'] = df_vefa.apply(construire_adresse, axis=1)
        return df_vefa
    except:
        return pd.DataFrame()

df_vefa = load_and_find_vefa()

st.markdown("---")

if df_vefa.empty:
    st.warning("⚠️ **Aucune vente sur plan (VEFA) détectée dans vos fichiers actuels.**")
    st.info("""
    **C'est normal !** Vos fichiers DVF actuels sont probablement trop récents. 
    Pour faire apparaître les programmes Pinel qui arrivent à échéance aujourd'hui, il faut nourrir l'outil avec les archives de l'époque.
    
    **La mission :**
    1. Allez sur le site officiel : `app.dvf.etalab.gouv.fr` ou `data.gouv.fr`
    2. Téléchargez les fichiers DVF des années **2015, 2016 et 2017** pour votre secteur.
    3. Placez ces fichiers dans votre dossier `données_dvf` sur GitHub.
    4. Ce radar s'activera automatiquement !
    """)
else:
    # --- AGRÉGATION POUR TROUVER LES IMMEUBLES ---
    st.success("✅ Données historiques trouvées et analysées !")
    st.write("L'outil a regroupé les ventes sur plan par adresse. Plus il y a de lots vendus simultanément à une même adresse, plus il s'agit d'une grande résidence neuve (Programme Pinel potentiel).")
    
    # On groupe par adresse pour compter les appartements
    programmes = df_vefa.groupby('Adresse_Immeuble').agg(
        Nombre_de_Lots=('Adresse_Immeuble', 'count')
    ).reset_index()
    
    # On ne garde que les adresses avec au moins 4 ventes VEFA (pour éliminer les maisons individuelles)
    programmes = programmes[programmes['Nombre_de_Lots'] > 3]
    programmes = programmes.sort_values('Nombre_de_Lots', ascending=False)
    
    st.subheader(f"🎯 {len(programmes)} Résidences Neuves (VEFA) identifiées")
    st.dataframe(programmes.rename(columns={'Adresse_Immeuble': '📍 Adresse du Programme Neuf', 'Nombre_de_Lots': '📦 Nombre d\'appartements vendus'}), use_container_width=True, hide_index=True)
    
    st.markdown("---")
    st.subheader("🛠️ Plan d'action terrain")
    st.markdown("""
    1. **Sélectionnez une cible :** Prenez la première adresse du tableau (celle avec le plus de lots).
    2. **Identifiez les investisseurs :** Demandez la matrice cadastrale de cet immeuble. 
    3. **Triez :** Tous les propriétaires de la liste dont l'adresse personnelle de domiciliation est *différente* de l'adresse de l'immeuble sont des investisseurs locatifs.
    4. **Contactez :** Utilisez la **Stratégie 2** (Publipostage Alerte PLF 2027) pour frapper juste : leur défiscalisation Pinel de 9 ans est terminée !
    """)
