import os
from langchain.chat_models import ChatOpenAI
from dotenv import load_dotenv

from app.config.file_paths_config import PATHS
from app.config.features_config import OPENAI_MODEL
from app.utility.formatting_helpers import format_mapping_words_csv
from app.utility.logging import get_logger
from app.features.conversation.conversation_analyst import ConversationAnalyst


logger = get_logger(__name__)

class LLMHandler:
    """
    Service for interacting with the language model (LLM).  
    
    This service handles all LLM-based extraction of specialties, cities, institution types,
    and other information from user queries, as well as managing conversation history.

    Attributes:
        model (ChatOpenAI): The ChatOpenAI model instance used for processing queries.
        paths (Dict[str, str]): A dictionary containing file paths for various resources.
        key_words (Dict[str, Any]): A dictionary containing keywords loaded from a CSV file.
        conversation_manager (ConversationAnalyst): An instance of ConversationAnalyst for managing conversation logic. 
    Methods:
        init_model() -> ChatOpenAI: Initializes and returns the ChatOpenAI model.
        run_conversation_checks(prompt: str, conv_history: list) -> dict: Runs all conversation-related checks and consolidates results.
        rewrite_query_merge(prompt: str, conv_history: str) -> str: Rewrites the query using the merge approach (Case 2).
        rewrite_query_add(prompt: str, conv_history: str) -> str: Rewrites the query using the add
        approach (Case 3).  
    """
    def __init__(self):
        logger.info("LLMHandler __init__ called")
        logger.info("Initializing LLMHandler")
        load_dotenv(override=False) 
        self.model = self.init_model()

        self.paths = PATHS

        # Debug: log the mapping_word_path and list files in the data directory
        logger.info(f"Trying to load mapping_word_path: {self.paths['mapping_word_path']}")
        data_dir = os.path.dirname(self.paths["mapping_word_path"])
        if os.path.exists(data_dir):
            logger.info(f"Files in data directory ({data_dir}): {os.listdir(data_dir)}")
        else:
            logger.warning(f"Data directory does not exist: {data_dir}")

        self.key_words = format_mapping_words_csv(self.paths["mapping_word_path"])
        self.conversation_manager = ConversationAnalyst(self.model)

        
    def init_model(self) -> ChatOpenAI:
        """
        Initializes and returns the ChatOpenAI model using the API key from environment variables.
        Returns:
            ChatOpenAI: An instance of the ChatOpenAI model.
        """
        logger.info("init_model called: Initializing ChatOpenAI model")
        api_key = os.getenv("OPENAI_API_KEY")
        logger.debug(f"OPENAI_API_KEY loaded: {'set' if api_key else 'not set'}")
        logger.debug("Creating ChatOpenAI instance")
        self.model = ChatOpenAI(openai_api_key=api_key, model=OPENAI_MODEL)
        logger.info("ChatOpenAI model initialized")
        return self.model
    

    def run_conversation_checks(self, prompt: str, conv_history: list) -> dict:
        """
        Runs all conversation-related checks and consolidates results into a dictionary using ConversationAnalyst.
        Args:
            prompt (str): The user's prompt.
            conv_history (list): The conversation history.  
        Returns:
            dict: A dictionary containing the results of all conversation checks.   
        """
        logger.info(f"run_conversation_checks called with prompt: {prompt}, conv_history: {conv_history}")
        return self.conversation_manager.run_all_conversation_checks(prompt, conv_history)


    def rewrite_query_merge(self, prompt: str, conv_history: str) -> str:
        """
        Rewrites the query using the merge approach (Case 2).
        
        Args:
            prompt (str): The user's prompt.
            conv_history (str): The conversation history.
        
        Returns:
            str: The rewritten query using the merge approach.
        """
        logger.info(f"Calling rewrite_query_merge called with prompt: {prompt}, conv_history: {conv_history}")
        return self.conversation_manager.conversation.rewrite_query_merge(prompt, conv_history)


    def rewrite_query_add(self, prompt: str, conv_history: str) -> str:
        """
        Rewrites the query using the add approach (Case 3).
        
        Args:
            prompt (str): The user's prompt.
            conv_history (str): The conversation history.
        
        Returns:
            str: The rewritten query using the add approach.
        """
        logger.info(f"Calling rewrite_query_add with prompt: {prompt}, conv_history: {conv_history}")
        return self.conversation_manager.conversation.rewrite_query_add(prompt, conv_history)
