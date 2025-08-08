# """
# Defines the MessageHandler class for processing messages in the Streamlit UI.
# """

# import streamlit as st
# from app.utility.formatting_helpers import format_links
# from app.utility.logging import get_logger
# from st_config import (CASE_MESSAGES, SPINNER_MESSAGES, OFF_TOPIC_RESPONSE, ERROR_MESSAGES, NO_SPECIALTY_MATCH)
# from st_utility import (execute_with_spinner, append_to_conversation, get_conversation_list)
# from st_specialty_handler import SpecialtyHandler


# # Initialize logger for this module
# logger = get_logger(__name__)

# from st_utility import process_message