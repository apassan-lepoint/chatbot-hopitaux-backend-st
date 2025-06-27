"""
This file contains configuration settings for the chatbot application.
"""

import os

# File paths for different modules in repo
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(REPO_ROOT, "data")
HISTORY_DIR = os.path.join(REPO_ROOT, "history")

PATHS={
    "mapping_word_path": os.path.join(DATA_DIR, "resultats_llm_v5.csv"),
    "ranking_file_path": os.path.join(DATA_DIR, "classments-hopitaux-cliniques-2024.xlsx"),
    "ranking_overall_private_path": os.path.join(DATA_DIR, "Tableaux_d'honneur_2024_PRIVE.csv"),
    "ranking_overall_public_path": os.path.join(DATA_DIR, "Tableaux_d'honneur_2024_PUBLIC.csv"),
    "hospital_coordinates_path": os.path.join(DATA_DIR, "fichier_hopitaux_avec_coordonnees_avec_privacitee.xlsx"),
    "history_path": os.path.join(HISTORY_DIR, "results_history.csv")
    }
