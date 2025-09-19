"""
file_paths_config.py
---------------------------------
This file contains the file paths configuration for the application.
"""

import os

# File paths for different modules in repo
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DATA_DIR = os.path.join(REPO_ROOT, "data")
HISTORY_DIR = os.path.join(REPO_ROOT, "history")

PATHS={
    "mapping_word_path": os.path.join(DATA_DIR, "resultats_llm_v5.csv"),
    "france_regions": os.path.join(DATA_DIR, "clean_france_regions.csv"),
    "france_departments": os.path.join(DATA_DIR, "clean_france_departments.csv"),
    "france_communes": os.path.join(DATA_DIR, "clean_france_communes.csv"),
    "ranking_file_path": os.path.join(DATA_DIR, "classments-hopitaux-cliniques-2024.xlsx"), # TODO delete 
    "ranking_overall_private_path": os.path.join(DATA_DIR, "Tableaux_d'honneur_2024_PRIVE.csv"), # TODO delete
    "ranking_overall_public_path": os.path.join(DATA_DIR, "Tableaux_d'honneur_2024_PUBLIC.csv"), # TODO delete
    "hospital_coordinates_path": os.path.join(DATA_DIR, "fichier_hopitaux_avec_coordonnees_avec_privacitee.xlsx"), # TODO delete
    "history_path": os.path.join(HISTORY_DIR, "results_history_mvp.csv")
    }