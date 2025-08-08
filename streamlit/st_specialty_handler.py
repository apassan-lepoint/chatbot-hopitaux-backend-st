# """
# Handles specialty detection and selection logic for Streamlit UI.
# """
# import sys
# import os
# import streamlit as st

# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# from datetime import datetime
# from app.utility.logging import get_logger
# from app.features.query_analysis.specialty.specialty_detection import SpecialtyDetector
# from st_config import (SESSION_STATE_KEYS, UI_SPECIALTY_SELECTION_PROMPT, UI_INVALID_SELECTION_ERROR, NO_SPECIALTY_MATCH)
# from st_utility import handle_specialty_selection