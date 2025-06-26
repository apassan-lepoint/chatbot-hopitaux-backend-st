"""
This file contains configuration settings for the chatbot application.
"""

import os

# File paths for different modules in repo
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
DATA_DIR = os.path.join(REPO_ROOT, "data")
HISTORY_DIR = os.path.join(REPO_ROOT, "historique")