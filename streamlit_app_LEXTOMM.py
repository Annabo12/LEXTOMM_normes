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
groupe_controle = excel_data.sheet_names

if "sex_selected" not in st.session_state:
    st.session_state["sex_selected"] = False

if "scores_entered" not in st.session_state:
    st.session_state["scores_entered"] = False

if "age_data" not in st.session_state:
    st.session_state["age_data"] = pd.DataFrame()

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
sex_groups = ["Homme", "Femme", "Autre"]
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



