"""
This file contains configuration settings for the chatbot application.
"""

import os

# File paths for different modules in repo
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
DATA_DIR = os.path.join(REPO_ROOT, "data")
HISTORY_DIR = os.path.join(REPO_ROOT, "historique")

PATHS={
    "mapping_word_path": os.path.join(DATA_DIR, "resultats_llm_v5.csv"),
    "palmares_path": os.path.join(DATA_DIR, "classments-hopitaux-cliniques-2024.xlsx"),
    "palmares_general_private_path": os.path.join(DATA_DIR, "Tableaux_d'honneur_2024_PRIVE.csv"),
    "palmares_general_public_path": os.path.join(DATA_DIR, "Tableaux_d'honneur_2024_PUBLIC.csv"),
    "coordonnees_path": os.path.join(DATA_DIR,"data", "fichier_hopitaux_avec_coordonnees_avec_privacitée.xlsx"),
    "history_path": os.path.join(HISTORY_DIR,"data", "results_history.csv")
    }