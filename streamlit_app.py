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


        scores_df = pd.DataFrame(user_scores, columns=["Tâche", "Score Patient"])

        # Inverser les Z-scores pour les variables de temps
        time_variables = [
        "Sémantique verbale moyenne (temps)",
        "Sémantique non-verbale moyenne (temps)",
        "Phonologie verbale moyenne (temps)",
        "Phonologie verbale rime (temps)",
        "Phonologie non-verbale moyenne (temps)",
        "Phonologie non-verbale rime (temps)",
        "Syntaxe moyenne (temps)",
        "Syntaxe Act-Aff (temps)",
        "Syntaxe Act-Neg (temps)",
        "Syntaxe Pass-Aff (temps)",
        "Syntaxe Pass-Neg (temps)",
        "Mémoire verbale NEREC moyenne (temps)",
        "Mémoire non-verbale AGDESAG moyenne (temps)",
        "Inhibition moyenne (temps)",
        "Inhibition incongruent (temps)",
        "Inhibition indice incong-cong (temps)",
        "Mise à jour en mémoire de travail moyenne (temps)",
        "Mise à jour en mémoire de travail leurre (temps)",
        "Mise à jour en mémoire de travail indice (temps)",
        "Flexibilité mentale mixte (temps)",
        "Flexibilité mentale non-mixte (temps)",
        "Flexibilité mentale diff (temps)",
        "Attention soutenue moyenne (temps)",
        "Théorie de l'esprit changeunseenmenta (temps)",
        "Visuospatial contrôle moyenne (temps)"]

     # Fusionner avec les données originales pour les calculs
    merged_data = pd.merge(sex_data, scores_df, on="Tâche", how="left")
    merged_data["Z-Score"] = (merged_data["Score Patient"] - merged_data["Moyenne"]) / merged_data["Ecart-type"]
    merged_data.loc[merged_data["Tâche"].isin(time_variables), "Z-Score"] *= -1

    merged_data["Z-Score"] = pd.to_numeric(merged_data["Z-Score"], errors="coerce")
    merged_data = merged_data.dropna(subset=["Z-Score"])

    merged_data["Percentile (%)"] = norm.cdf(merged_data["Z-Score"]) * 100

    filled_data = merged_data[~merged_data["Score Patient"].isna()]
    filled_data = filled_data.drop_duplicates(subset="Tâche")

    # Bouton pour confirmer les scores
    if st.button("Confirmer les scores et afficher les résultats"):
            st.session_state["scores_entered"] = True
            st.session_state["sex_data"] = filled_data
            st.session_state["missing_norms"] = missing_norms

# Etape 3 : Résultats

categories_mapping = {
    "Lexique et Sémantique": [
        "Dénomination NEREC (score)",
        "Sémantique verbale moyenne (score)",
        "Sémantique verbale moyenne (temps)",
        "Sémantique non-verbale moyenne (score)",
        "Sémantique non-verbale moyenne (temps)"
    ],
    "Phonologie": [
        "Phonologie verbale moyenne (score)",
        "Phonologie verbale moyenne (temps)",
        "Phonologie verbale rime (score)",
        "Phonologie verbale rime (temps)",
        "Phonologie non-verbale moyenne (score)",
        "Phonologie non-verbale moyenne (temps)",
        "Phonologie non-verbale rime (score)",
        "Phonologie non-verbale rime (temps)"
    ],
    "Syntaxe": [
        "Syntaxe moyenne (score)",
        "Syntaxe moyenne (temps)",
        "Syntaxe Act-Aff (score)",
        "Syntaxe Act-Aff (temps)",
        "Syntaxe Act-Neg (score)",
        "Syntaxe Act-Neg (temps)",
        "Syntaxe Pass-Aff (score)",
        "Syntaxe Pass-Aff (temps)",
        "Syntaxe Pass-Neg (score)",
        "Syntaxe Pass-Neg (temps)"
    ],
    "Prosodie": [
        "Prosodie moyenne (score)",
        "Prosodie focus (score)"
    ],
    "Mémoire": [
        "Mémoire verbale NEREC moyenne (score)",
        "Mémoire verbale NEREC moyenne (temps)",
        "Mémoire non-verbale AGDESAG moyenne (score)",
        "Mémoire non-verbale AGDESAG moyenne (temps)"
    ],
    "Inhibition": [
        "Inhibition moyenne (score)",
        "Inhibition moyenne (temps)",
        "Inhibition incongruent (score)",
        "Inhibition incongruent (temps)",
        "Inhibition indice incong-cong (score)",
        "Inhibition indice incong-cong (temps)"
    ],
    "Mise à jour": [
        "Mise à jour en mémoire de travail moyenne (score)",
        "Mise à jour en mémoire de travail moyenne (temps)",
        "Mise à jour en mémoire de travail leurre (score)",
        "Mise à jour en mémoire de travail leurre (temps)",
        "Mise à jour en mémoire de travail indice (score)",
        "Mise à jour en mémoire de travail indice (temps)",
        "Mise à jour en mémoire de travail FA (score)"
    ],
    "Flexibilité mentale": [
        "Flexibilité mentale mixte (score)",
        "Flexibilité mentale mixte (temps)",
        "Flexibilité mentale non-mixte (score)",
        "Flexibilité mentale non-mixte (temps)",
        "Flexibilité mentale diff (score)",
        "Flexibilité mentale diff (temps)"
    ],
    "Attention soutenue": [
        "Attention soutenue moyenne (score)",
        "Attention soutenue moyenne (temps)",
        "Attention soutenue FA (score)"
    ],
    "Théorie de l'esprit": [
        "Théorie de l'esprit (score d')",
        "Théorie de l'esprit changeunseenmenta (score)",
        "Théorie de l'esprit changeunseenmenta (temps)"
    ],
    "Visuospatial -Contrôle": [
        "Visuospatial contrôle moyenne (score)",
        "Visuospatial contrôle moyenne (temps)"
    ]
}


if st.session_state["scores_entered"]:
    st.header("Étape 3 : Résultats du patient")

    results_df = st.session_state["sex_data"]

    # Séparer les scores et les temps
    scores_only_df = results_df[~results_df["Tâche"].isin(time_variables)]
    times_only_df = results_df[results_df["Tâche"].isin(time_variables)]

    # === Tableau des variables de type SCORE ===
    st.subheader("📊 Résultats - Scores (ACC)")
    st.dataframe(scores_only_df[["Tâche", "Score Patient", "Moyenne", "Ecart-type", "Z-Score", "Percentile (%)"]])

    # Bouton téléchargement CSV - scores
    csv_scores = scores_only_df.to_csv(index=False, sep=";")
    st.download_button(
        label="📥 Télécharger le tableau des scores (CSV)",
        data=csv_scores,
        file_name=f"scores_{st.session_state['patient_id']}.csv",
        mime="text/csv"
    )

    # === Tableau des variables de type TEMPS (optionnel) ===
    st.subheader("⏱️ Temps de réaction (TR)")
    st.dataframe(times_only_df[["Tâche", "Score Patient", "Moyenne", "Ecart-type", "Z-Score", "Percentile (%)"]])

    # Bouton téléchargement CSV - temps
    csv_times = times_only_df.to_csv(index=False, sep=";")
    st.download_button(
        label="📥 Télécharger le tableau des temps de réaction (CSV)",
        data=csv_times,
        file_name=f"temps_{st.session_state['patient_id']}.csv",
        mime="text/csv"
    )

       # === Tâches sans normes ===
    st.subheader("Tâches sans normes disponibles")
    if st.session_state["missing_norms"]:
        st.warning(", ".join(st.session_state["missing_norms"]))
    else:
        st.success("Toutes les tâches ont été associées à des normes ✅")


# Création des représentations graphiques pour les scores (ACC)

# === Sélection initiale avec noms et catégories ===
task_labels_and_categories = {
    "Dénomination NEREC (score)": ("Dénomination", "Langage"),
    "Sémantique non-verbale moyenne (score)": ("Sémantique non-verbale", "Langage"),
    "Phonologie non-verbale rime (score)": ("Phonologie non-verbale", "Langage"),
    "Syntaxe moyenne (score)": ("Syntaxe", "Langage"),
    "Mémoire verbale NEREC moyenne (score)": ("Mémoire verbale", "Mémoire"),
    "Mémoire non-verbale AGDESAG moyenne (score)": ("Mémoire non-verbale", "Mémoire"),
    "Inhibition incongruent (score)": ("Inhibition", "Fonctions exécutives"),
    "Mise à jour en mémoire de travail moyenne (score)": ("Mise à jour", "Fonctions exécutives"),
    "Flexibilité mentale mixte (score)": ("Flexibilité", "Fonctions exécutives"),
    "Attention soutenue moyenne (score)": ("Attention soutenue", "Fonctions exécutives"),
    "Théorie de l'esprit (score d')": ("Théorie de l'esprit", "TOM")
}

# Couleurs associées aux domaines
domain_colors = {
    "Langage": "#6FBF73",  # vert
    "Mémoire": "#64A6FF",  # bleu
    "Fonctions exécutives": "#9361B7",  # violet
    "TOM": "#F8B400",  # orange
    "Autre": "gray"
}

# === Fonction améliorée avec couleurs et export PDF ===
import io
from matplotlib.backends.backend_pdf import PdfPages

def plot_percentile_profile_named(data, task_dict, title="Profil – scores percentiles", key_suffix=""):
    valid_tasks = [t for t in task_dict if t in data["Tâche"].values]
    df = data[data["Tâche"].isin(valid_tasks)].copy()

    df["Label"] = df["Tâche"].map(lambda t: task_dict[t][0])
    df["Catégorie"] = df["Tâche"].map(lambda t: task_dict[t][1])

    cat_order = ["Langage", "Mémoire", "Fonctions exécutives", "TOM", "Visuospatial"]
    df["Catégorie"] = pd.Categorical(df["Catégorie"], categories=cat_order, ordered=True)
    df = df.sort_values(["Catégorie", "Label"]).reset_index(drop=True)

    fig, ax = plt.subplots(figsize=(8, 6))

    ax.axvspan(0, 5, color="#f8d7da")
    ax.axvspan(5, 15, color="#fff3cd")
    ax.axvspan(15, 85, color="#d4edda")
    ax.axvspan(85, 100, color="#c3e6cb")
    ax.axvline(x=50, linestyle="--", color="black")
    ax.plot(df["Percentile (%)"], df["Label"], marker="o", color="dodgerblue")

    y_labels = ax.get_yticklabels()
    for label in y_labels:
        label_text = label.get_text()
        matched_row = df[df["Label"] == label_text]
        if not matched_row.empty:
            cat = matched_row["Catégorie"].values[0]
            label.set_color(domain_colors.get(cat, "black"))

    ax.set_xlim(0, 100)
    ax.set_xlabel("Percentile")
    ax.set_title(title)
    st.pyplot(fig)

    # Ajout d'un identifiant unique avec suffixe
    pdf_buffer = io.BytesIO()
    with PdfPages(pdf_buffer) as pdf:
        pdf.savefig(fig, bbox_inches='tight')
    st.download_button(
        label="📥 Télécharger le graphique en PDF",
        data=pdf_buffer.getvalue(),
        file_name=f"{title.replace(' ', '_').lower()}.pdf",
        mime="application/pdf",
        key=f"download_pdf_{title}_{key_suffix}"
    )

# === Profil structuré – sélection initiale ===
st.subheader("Profil cognitif global - 📊 Scores")
plot_percentile_profile_named(scores_only_df, task_labels_and_categories, title="Profil – scores", key_suffix="score_initial")

# === Profil interactif ===
st.subheader("Profil cognitif détaillé - 📊 Scores")
selected_tasks_custom = st.multiselect(
    label="Sélectionnez les tâches à afficher :",
    options=scores_only_df["Tâche"].unique()
)

if selected_tasks_custom:
    dynamic_task_dict = {t: (t, "Autre") for t in selected_tasks_custom}
    plot_percentile_profile_named(scores_only_df, dynamic_task_dict, title="Profil – scores", key_suffix="score_custom")
else:
    st.info("Sélectionnez au moins une tâche pour générer un graphique personnalisé.")


# Création des représentations graphiques pour les scores (ACC)

# Mapping noms + catégories pour les variables de temps
time_labels_and_categories = {
    "Sémantique non-verbale moyenne (temps)": ("Sémantique non-verbale", "Langage"),
    "Phonologie non-verbale rime (temps)": ("Phonologie non-verbale", "Langage"),
    "Syntaxe moyenne (temps)": ("Syntaxe", "Langage"),
    "Mémoire verbale NEREC moyenne (temps)": ("Mémoire verbale", "Mémoire"),
    "Mémoire non-verbale AGDESAG moyenne (temps)": ("Mémoire non-verbale", "Mémoire"),
    "Inhibition incongruent (temps)": ("Inhibition", "Fonctions exécutives"),
    "Mise à jour en mémoire de travail moyenne (temps)": ("Mise à jour", "Fonctions exécutives"),
    "Flexibilité mentale mixte (temps)": ("Flexibilité", "Fonctions exécutives"),
    "Attention soutenue moyenne (temps)": ("Attention soutenue", "Fonctions exécutives"),
    "Théorie de l'esprit changeunseenmenta (temps)": ("Théorie de l'esprit", "TOM")
}

# === PROFIL STRUCTURÉ POUR LES TEMPS ===
st.subheader("Profil cognitif global – ⏱️ Temps de réaction")
plot_percentile_profile_named(times_only_df, time_labels_and_categories, title="Profil – temps de réaction", key_suffix="temps_initial")

# === PROFIL INTERACTIF POUR LES TEMPS ===
st.subheader("Profil cognitif détaillé - ⏱️ Temps de réaction")
selected_times_custom = st.multiselect(
    label="Sélectionnez les tâches temporelles à afficher :",
    options=times_only_df["Tâche"].unique()
)

if selected_times_custom:
    dynamic_time_task_dict = {t: (t, "Autre") for t in selected_times_custom}
    plot_percentile_profile_named(times_only_df, dynamic_time_task_dict, title="Profil – temps de réaction", key_suffix="temps_custom")
else:
    st.info("Sélectionnez au moins une tâche pour générer un graphique.")


# Footer avec citation APA 7
st.markdown(
    """
    <hr style="border:1px solid #eee; margin-top: 50px; margin-bottom: 10px;">
    <div style="text-align: center; font-size: 14px; color: gray;">
    <p><strong>Projet LEXTOMM</strong> - Pour citer le protocole, veuillez utiliser la référence suivante :</p>
        <p style="text-align: center;">
            Perrone-Bertolotti, M., Borne, A., Meunier, L., El Bouzaïdi Tiali, S., Bulteau, C., & Baciu, M. (2021). 
            <em>Computerized LEXTOMM Battery (Language, EXecutive functions, Theory Of Mind, episodic Memory)</em>. 
            <a href="https://osf.io/y2sdp" target="_blank">https://osf.io/y2sdp</a>
        </p>

    </div>
    """,
    unsafe_allow_html=True
)