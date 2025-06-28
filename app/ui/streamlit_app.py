"""
Streamlit-based user interface for the hospital ranking chatbot.

This file defines the StreamlitChatbot class and main UI logic, enabling interactive
    conversations with the chatbot and displaying results in a web app.
"""

import sys
import os

# Go 2 levels up to add the repo root to sys.path
# This needs to happen before importing any modules from the repo
current_dir = os.path.dirname(__file__)
repo_root = os.path.abspath(os.path.join(current_dir, "../../"))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)
    print("✅ sys.path:", sys.path)

import streamlit as st
from app.services.pipeline_service import Pipeline
from app.services.llm_service import Appels_LLM
from app.utils.logging import get_logger
logger = get_logger(__name__)

class StreamlitChatbot:
    """
    Streamlit-based chatbot UI for hospital ranking queries.
    
    Provides methods to manage session state, handle user input,interact with 
        LLM services, and display conversation history.
    """
    
    def __init__(self):
        """
        Initialize LLM service and max conversation length.
        """
        
        logger.info("Initializing StreamlitChatbot")
        self.appel_LLM = Appels_LLM()
        self.MAX_MESSAGES = 4 

    def reset_session_state(self):
        """
        Reset all session state variables.
        """
        
        logger.info("Resetting session state")
        st.session_state.conversation = [] 
        st.session_state.selected_option = None
        st.session_state.prompt = ""
        st.session_state.v_speciality= None
        st.session_state.city= None
        st.session_state.slider_value=None
        st.session_state.v_spe = ""

    def reset_session_statebis(self):
        """
        Re-initialize the session state bis variables.
        """
        
        logger.info("Resetting session state-bis")
        st.session_state.conversation = []
        self.answer_instance = Pipeline()
        self.appel_LLM = Appels_LLM()

        st.session_state.selected_option = None
        st.session_state.prompt = ""
        st.session_state.v_speciality= None
        st.session_state.city= None
        st.session_state.slider_value=None
        st.session_state.v_spe = ""
    
    def check_message_length(self,message):
        """
        Check the length of the user message and reset session state if too long.

        Args:
            message (_type_): _description_
        """
        if len(message) > 200:
            self.reset_session_state()
            st.warning("Votre message est trop long. Merci de reformuler.")
            st.stop()
            
    def check_conversation_limit(self):
        """
        Check if the conversation has reached the maximum number of messages.
        
        If so, reset the session state and notify the user.
        """
        if len(st.session_state.conversation) >= self.MAX_MESSAGES:
            st.warning("La limite de messages a été atteinte. La conversation va redémarrer.")
            self.reset_session_statebis()
            st.rerun()
    
    def getofftopic(self,user_input):
        """
        This method checks if the user input is off-topic and resets the session state
            if it is.
        
        Args:
            user_input (str): The input message from the user.
            
        Returns:
            None: If the input is off-topic, the session state is reset and a warning is
            displayed to the user.
        """
        
        logger.info(f"Checking if message offtopic (1) for input: {user_input}")
        isofftopic = self.appel_LLM.get_offtopic(user_input)
        if isofftopic == 'Hors sujet':
            self.reset_session_state()
            st.warning(
                "Je n'ai pas bien saisi la nature de votre demande. Merci de reformuler."
            )
            st.stop()
    
    def getofftopicapprofondi(self,user_input):
        """
        This method checks if the user input is off-topic using a more detailed approach.
        
        Args:
            user_input (str): The input message from the user.
        
        Returns:
            None: If the input is off-topic, the session state is reset and a warning is
            displayed to the user.
        """
        logger.info(f"Checking if message offtopic (2) for input: {user_input}")
        isofftopic = self.appel_LLM.get_offtopic_approfondi(user_input)
        if isofftopic == 'hors sujet':
            self.reset_session_state()
            st.warning(
                "Cet assistant a pour but de fournir des informations sur les classements des établissements de soins de cette année. Merci de reformuler."
            )
            st.stop()
    
    def check_non_french_cities(self,user_input):
        """
        Check if the user input contains a non-French city.

        Args:
            user_input (_type_): _description_
        
        Returns:
            None: If a non-French city is detected, the session state is reset and a
            warning is displayed to the user.
        """
        
        logger.info(f"Checking for non-French city in input: {user_input}")
        self.city = self.appel_LLM.get_city(user_input)
        
        # If city is foreign, reset and warn
        if self.city == 'ville étrangère':
            self.reset_session_state()
            st.warning(
                f"Je ne peux pas répondre aux questions concernant les hôpitaux situés hors du territoire français, merci de consulter la page du palmarès. [🔗 Page du classement](https://www.lepoint.fr/hopitaux/classements)"
            )
            st.stop()
        # If city is ambiguous, reset and warn
        if self.city == 'confusion':
            self.reset_session_state()
            st.warning(
                f"Je ne parviens pas à détecter votre localisation, merci de reformuler avec une autre ville."
            )
            st.stop()
     
    def _display_conversation(self):
        """
        Display the conversation history with chat-like styling.
        """
        for user_msg, bot_msg in st.session_state.conversation:
            st.chat_message("user").write(user_msg)
            st.chat_message("assistant").write(bot_msg, unsafe_allow_html=True)
                
    def run(self):
        """
        Run the Streamlit application.
        
        This method initializes the UI, handles user input, and manages the conversation
        history.
        """
        
        logger.info("Running StreamlitChatbot application")
        st.title("🏥Assistant Hôpitaux")
        st.write("Posez votre question ci-dessous.")
        
        # Display example questions in columns for user inspiration
        col1, col2, col3 = st.columns(3)
        with col1:
            st.info("**Quel est le meilleur hôpital de France ?**")
        with col2:
            st.info("**Y a-t-il des hôpitaux publics avec un service de proctologie dans la région Nantaise ?**")
        with col3:
            st.info("**Est-ce que l'hôpital de la pitié salpétrière est un bon hôpital en cas de problèmes auditifs ?**")
        
        # Button to start a new conversation
        if st.sidebar.button("🔄 Démarrer une nouvelle conversation"):
            logger.info("User requested new conversation")
            self.reset_session_statebis()
            st.rerun()
       
        # Initialize session state variables if not already present
        if "conversation" not in st.session_state:
            st.session_state.conversation = []
        if "selected_option" not in st.session_state:
            st.session_state.selected_option = None
        if "prompt" not in st.session_state:
            st.session_state.prompt = ""
        if "v_spe" not in st.session_state:
            st.session_state.v_spe = ""
        
        # Check if conversation limit is reached
        self.check_conversation_limit()
        
        # If this is the first message in the conversation
        if len(st.session_state.conversation)==0  :
            user_input = st.chat_input("Votre message")
            if user_input:
                logger.info(f"User input: {user_input}")
                st.session_state.prompt = user_input
                self.check_message_length(st.session_state.prompt)
                self.getofftopic(st.session_state.prompt)
                self.getofftopicapprofondi(st.session_state.prompt)
                self.check_non_french_cities(st.session_state.prompt)
                
            if st.session_state.prompt:
                # Detect medical specialty if not already set
                if st.session_state.v_spe == "":
                    v_speciality = self.appel_LLM.get_speciality(st.session_state.prompt)
                    st.session_state.v_spe = v_speciality

                # If multiple specialties are detected, prompt user to select one
                if st.session_state.v_spe.startswith("plusieurs correspondances:"):
                    logger.info("Multiple specialties detected, prompting user for selection")
                    # Extract options from the string
                    options_string = st.session_state.v_spe.removeprefix("plusieurs correspondances:").strip()
                    options_list = options_string.split(',')
                    options_list = list(dict.fromkeys(options_list))

                    selected_option = st.radio(
                    "Précisez le domaine médical concerné :",
                    options=options_list,
                    index=None)

                    if selected_option is not None:
                        with st.spinner('Chargement'):
                            answer_instance = Pipeline()
                            result, link = answer_instance.final_answer(prompt=st.session_state.prompt, specialty_st=selected_option)
                            if result == 'établissement pas dans ce classement':
                                result= f"Cet hôpital n'est pas présent pour la spécialité {selected_option}"                  
                        # Add links to result    
                        for links in link:
                            result=result+f"<br>[🔗Page du classement]({links})"
                        st.session_state.conversation.append((st.session_state.prompt, result))
                        return None

                else:
                    # Only one specialty detected, proceed to answer
                    with st.spinner('Chargement'):
                        answer_instance = Pipeline()
                        result, link = answer_instance.final_answer(prompt=st.session_state.prompt, specialty_st=v_speciality)
                    for links in link:
                        result=result+f"<br>[🔗Page du classement]({links})"
                    st.session_state.conversation.append((st.session_state.prompt, result))
                    return None
        else  :
            # For subsequent messages in the conversation
            user_input = st.chat_input("Votre message")
            if user_input:
                logger.info(f"User input received: {user_input}")

                # Prepare conversation history for LLM context
                conv_history = "\n".join(
                    [f"Utilisateur: {q}\nAssistant: {r}" for q, r in st.session_state.conversation]
                ) if hasattr(st.session_state, "conversation") else ""

                # Use LLM to detect if this is a modification or a new query
                try:
                    mod_type = self.appel_LLM.detect_modification(user_input, conv_history)
                    logger.info(f"Detected query type: {mod_type}")
                except Exception as e:
                    logger.error(f"Error during modification detection: {e}")
                    mod_type = "nouvelle question"

                if mod_type == "modification":
                    st.info("Modification détectée de la question précédente.")
                    logger.info("Continuing conversation with LLM (modification case)")
                    # Continue the conversation with LLM using previous context
                    with st.spinner('Chargement'):
                        result = self.appel_LLM.continuer_conv(
                            prompt=user_input,
                            conv_history=st.session_state.conversation
                        )
                    st.session_state.conversation.append((user_input, result))
                else:
                    st.info("Nouvelle question détectée.")
                    logger.info("Starting new query pipeline with LLM")
                    # Treat as a new query and use the main pipeline
                    with st.spinner('Chargement'):
                        answer_instance = Pipeline()
                        result, link = answer_instance.final_answer(prompt=user_input)
                    for links in link:
                        result = result + f"<br>[🔗Page du classement]({links})"
                    st.session_state.conversation.append((user_input, result))
        # Display the full conversation history    
        self._display_conversation()      
            
def main():
    """
    Streamlit entry point.
    """
    chatbot = StreamlitChatbot()
    chatbot.run()

if __name__ == "__main__":
    main()