"""
This module defines the UI components for the Streamlit application.
"""

import streamlit as st

from app.utility.logging import get_logger

from config.streamlit_config import (
    UI_TITLE,
    UI_SUBTITLE,
    UI_EXAMPLES_HEADER,
    UI_NEW_CONVERSATION_BUTTON,
    EXAMPLE_QUESTIONS,
    BUTTON_CSS
)

from st_utility import create_example_button, initialize_session_state



logger = get_logger(__name__)



class UIComponents:
    """
    UIComponents class to encapsulate all Streamlit UI components.
    
    Attributes:
        reset_callback: Callback function to reset session state.
   
    Methods:
        setup_ui: Sets up the main UI components.
        _setup_example_questions: Sets up the example questions section.
        _setup_sidebar: Sets up the sidebar controls.
        setup_session_state: Initializes session state with default values. 
    """
    
    def __init__(self, reset_callback):
        """
        Initialize UI components.
        
        Args:
            reset_callback: Callback function to reset session state
        """
        self.reset_callback = reset_callback
    
    
    def setup_ui(self):
        """
        Setup the main Streamlit UI components.
        """
        # Main title and subtitle
        st.title(UI_TITLE)
        st.write(UI_SUBTITLE)
        
        # Apply custom CSS
        st.markdown(BUTTON_CSS, unsafe_allow_html=True)
        
        # Example questions section
        self._setup_example_questions()
        
        # Sidebar controls
        self._setup_sidebar()
    
    
    def _setup_example_questions(self):
        """
        Setup the example questions section.
        """
        st.write(UI_EXAMPLES_HEADER)
        col1, col2, col3 = st.columns(3)
        columns = [col1, col2, col3]
        
        for i, (col, question) in enumerate(zip(columns, EXAMPLE_QUESTIONS)):
            with col:
                create_example_button(question, f"example{i+1}")
    
    
    def _setup_sidebar(self):
        """
        Setup sidebar controls.
        """
        if st.sidebar.button(UI_NEW_CONVERSATION_BUTTON):
            logger.info("User requested new conversation")
            self.reset_callback()
            st.rerun()
    
    
    def setup_session_state(self, default_values: dict):
        """
        Initialize session state with default values.
        
        Args:
            default_values: Dictionary of default session state values
        """
        initialize_session_state(default_values)