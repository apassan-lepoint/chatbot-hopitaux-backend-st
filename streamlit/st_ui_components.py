import streamlit as st
from app.utility.logging import get_logger
from st_utility import create_example_button
from st_config import (UI_TITLE, UI_SUBTITLE, UI_EXAMPLES_HEADER, UI_NEW_CONVERSATION_BUTTON, EXAMPLE_QUESTIONS,BUTTON_CSS)

# Initialize logger
logger = get_logger(__name__)


class UIComponents:
    """
    UIComponents class to manage Streamlit UI elements. 
    This class handles the setup of example questions, sidebar controls,
    and session state initialization.   

    Attributes:
        reset_callback: Callback function to reset session state.           

    Methods:
        _setup_example_questions: Setup the example questions section.
        _setup_sidebar: Setup sidebar controls.
        setup_ui: Setup the main Streamlit UI components.
        setup_session_state: Initialize session state with default values.      
    """
    def __init__(self, reset_callback):
        logger.info("Initializing UIComponents")
        self.reset_callback = reset_callback
    
    
    def _setup_example_questions(self):
        logger.debug("Setting up example questions in UI")
        """
        Setup the example questions section in the UI. 
        """
        st.write(UI_EXAMPLES_HEADER)
        col1, col2, col3, col4 = st.columns(4)
        columns = [col1, col2, col3, col4]
        
        for i, (col, question) in enumerate(zip(columns, EXAMPLE_QUESTIONS)):
            with col:
                create_example_button(question, f"example{i+1}")
    
    
    def _setup_sidebar(self):
        logger.debug("Setting up sidebar UI")
        """
        Setup sidebar controls for the UI.
        This includes a button to reset the conversation.   
        """
        if st.sidebar.button(UI_NEW_CONVERSATION_BUTTON):
            logger.info("User requested new conversation")
            # Directly reset all relevant session state keys here
            st.session_state.conversation = []
            st.session_state.selected_specialty = None
            st.session_state.multiple_specialties = None
            st.session_state.prompt = ""
            st.session_state.specialty = ""
            st.session_state.specialty_context = None
            st.session_state.selected_option = None
            st.session_state.original_prompt = ""
            st.rerun()
    
    
    def setup_ui(self):
        logger.debug("Setting up main UI components")
        """
        Setup the main Streamlit UI components.
        """
        st.title(UI_TITLE)
        st.write(UI_SUBTITLE)
        st.markdown(BUTTON_CSS, unsafe_allow_html=True) # Apply custom CSS
        self._setup_example_questions() # Example questions section
        self._setup_sidebar() # Sidebar controls
        
        
    def setup_session_state(self, default_values: dict):
        logger.debug(f"Setting up session state with defaults: {default_values}")
        """
        Initialize session state with default values.   
        """
        for key, value in default_values.items():
            if key == "conversation":
                if key not in st.session_state:
                    st.session_state[key] = []  # Always use a new empty list
            else:
                if key not in st.session_state:
                    st.session_state[key] = value