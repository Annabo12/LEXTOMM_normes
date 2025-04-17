import streamlit as st
import pandas as pd
import numpy as np
import zipfile
import io
from pandas import ExcelWriter
import matplotlib.pyplot as plt
import openpyxl
from streamlit_sortables import sort_items
from scipy.stats import norm
from matplotlib.patches import FancyBboxPatch
from openpyxl.styles import PatternFill, Font
from openpyxl import Workbook


# Charger le fichier Excel
file_path = 'NORMES_FINALES_2025.xlsx'
excel_data = pd.ExcelFile(file_path)

# Liste des groupes contrôles (onglets du fichier)
sex_groups = excel_data.sheet_names

if "sex_selected" not in st.session_state:
    st.session_state["sex_selected"] = False

if "scores_entered" not in st.session_state:
    st.session_state["scores_entered"] = False

if "sex_data" not in st.session_state:
    st.session_state["sex_data"] = pd.DataFrame()

if "missing_norms" not in st.session_state:
    st.session_state["missing_norms"] = []

st.markdown(
    """
    <div style="text-align: center; font-size: 50px; font-weight: bold;">
        Batterie LEXTOMM
    </div>
    """,
    unsafe_allow_html=True
)

# Données cliniques ET ID
st.header("Étape 1 : Sélectionnez le genre du patient")
# Define the available sex groups
sex_groups = ["Hommes", "Femmes"]
selected_sex_group = st.selectbox("Sélectionnez le genre du patient :", sex_groups)
patient_id = st.text_input("Saisissez l'ID du patient :", value="", placeholder="ID du patient")

if st.button("Passer à l'étape suivante"):
    if not patient_id.strip(): 
        st.error("Veuillez saisir un ID valide avant de continuer.")
    else:
        st.session_state["sex_selected"] = True
        st.session_state["patient_id"] = patient_id 
        st.success(f"ID {patient_id} et genre {selected_sex_group} confirmés.")


def load_sex_data(sheet_name, excel_file):
    try:
        return pd.read_excel(excel_file, sheet_name=sheet_name, engine="openpyxl")
    except Exception as e:
        st.error(f"Erreur lors du chargement des données : {e}")
        return pd.DataFrame()

if st.session_state["sex_selected"]:
    st.header("Étape 2 : Entrez les scores")
    sex_data = load_sex_data(selected_sex_group, excel_data)

    if sex_data.empty:
        st.error("Impossible de charger les données pour le groupe contrôle sélectionné.")
    else:
        sex_data = sex_data[["Tâche", "Moyenne", "Ecart-type", "Minimum", 
                             "5e percentile", "10e percentile", "Q1", 
                             "Q2 - mediane", "Q3", "90e percentile", "Maximum"]].dropna()

# Liste des catégories avec les tâches regroupées par paires
        categories = {
            "Lexique et Sémantique": [
                ("Dénomination NEREC (score)", None),
                ("Sémantique verbale moyenne (score)", "Sémantique verbale moyenne (temps)"),
                ("Sémantique non-verbale moyenne (score)", "Sémantique non-verbale moyenne (temps)")
            ],
            "Phonologie": [
                ("Phonologie verbale moyenne (score)", "Phonologie verbale moyenne (temps)"),
                ("Phonologie verbale rime (score)", "Phonologie verbale rime (temps)"),
                ("Phonologie non-verbale moyenne (score)", "Phonologie non-verbale moyenne (temps)"),
                ("Phonologie non-verbale rime (score)", "Phonologie non-verbale rime (temps)")
            ],
            "Syntaxe": [
                ("Syntaxe moyenne (score)", "Syntaxe moyenne (temps)"),
                ("Syntaxe Act-Aff (score)", "Syntaxe Act-Aff (temps)"),
                ("Syntaxe Act-Neg (score)", "Syntaxe Act-Neg (temps)"),
                ("Syntaxe Pass-Aff (score)", "Syntaxe Pass-Aff (temps)"),
                ("Syntaxe Pass-Neg (score)", "Syntaxe Pass-Neg (temps)")  
            ],
            "Prosodie": [
             ("Prosodie moyenne (score)", "Prosodie focus (score)")   
            ],
            "Mémoire": [
            ("Mémoire verbale NEREC moyenne (score)", "Mémoire verbale NEREC moyenne (temps)"),
            ("Mémoire non-verbale AGDESAG moyenne (score)", "Mémoire non-verbale AGDESAG moyenne (temps)")
            ],
            "Inhibition": [
            ("Inhibition moyenne (score)", "Inhibition moyenne (temps)"),
            ("Inhibition incongruent (score)", "Inhibition incongruent (temps)"),
            ("Inhibition indice incong-cong (score)", "Inhibition indice incong-cong (temps)")
            ],
            "Mise à jour en mémoire de travail": [
            ("Mise à jour en mémoire de travail moyenne (score)", "Mise à jour en mémoire de travail moyenne (temps)"),
            ("Mise à jour en mémoire de travail leurre (score)", "Mise à jour en mémoire de travail leurre (temps)"),
            ("Mise à jour en mémoire de travail indice (score)", "Mise à jour en mémoire de travail indice (temps)"),
            ("Mise à jour en mémoire de travail FA (score)", None) 
            ],
            "Flexibilité mentale": [
            ("Flexibilité mentale mixte (score)", "Flexibilité mentale mixte (temps)"),
            ("Flexibilité mentale non-mixte (score)", "Flexibilité mentale non-mixte (temps)"),
            ("Flexibilité mentale diff (score)", "Flexibilité mentale diff (temps)")
            ],
            "Attention soutenue": [
            ("Attention soutenue moyenne (score)", "Attention soutenue moyenne (temps)"),
            ("Attention soutenue FA (score)", None)
            ],
            "Théorie de l'esprit": [
            ("Théorie de l'esprit (score d')", None),
            ("Théorie de l'esprit changeunseenmenta (score)", "Théorie de l'esprit changeunseenmenta (temps)")
            ],
            "Visuospatial -Contrôle": [
            ("Visuospatial contrôle moyenne (score)", "Visuospatial contrôle moyenne (temps)")
            ]
        }

        # Collecte des scores utilisateur
        user_scores = []
        missing_norms = []

        for category, task_pairs in categories.items():
            st.subheader(category)
            for task1, task2 in task_pairs:
                col1, col2 = st.columns(2)

                # Colonne 1 : task1
                with col1:
                    if task1 in sex_data["Tâche"].values:
                        score1 = st.text_input(f"{task1} :", value="")
                        if score1.strip():
                            try:
                                score1 = float(score1)
                                user_scores.append({"Tâche": task1, "Score Patient": score1})
                            except ValueError:
                                st.error(f"Valeur non valide pour {task1}. Veuillez entrer un nombre.")
                    else:
                        st.warning(f"Pas de normes disponibles pour {task1}")
                        missing_norms.append(task1)

                # Colonne 2 : task2 (si elle existe)
                if task2:  # vérifie qu'on n'est pas sur None ou ""
                    with col2:
                        if task2 in sex_data["Tâche"].values:
                            score2 = st.text_input(f"{task2} :", value="")
                            if score2.strip():
                                try:
                                    score2 = float(score2)
                                    user_scores.append({"Tâche": task2, "Score Patient": score2})
                                except ValueError:
                                    st.error(f"Valeur non valide pour {task2}. Veuillez entrer un nombre.")
                        else:
                            st.warning(f"Pas de normes disponibles pour {task2}")
                            missing_norms.append(task2)