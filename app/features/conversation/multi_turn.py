"""
Service for handling multi-turn conversation logic with 6-case approach.
"""
from typing import Dict, Any
from app.utility.logging import get_logger
from app.utility.prompt_formatting_helpers import prompt_formatting
from app.utility.llm_helpers import invoke_llm_and_parse_boolean

logger = get_logger(__name__)

class MultiTurn:
    """
    Service for handling multi-turn conversation logic.
    Implements 4-check system to determine conversation handling approach.
    
    Attributes:
        model: The language model used for analysis.
        case_responses: Dictionary mapping case identifiers to responses.     
    """
    
    def __init__(self, model):
        logger.info("Initializing MultiTurn")
        self.model = model
        self.case_responses = {
            "case1": "Je n'ai pas bien saisi la nature de votre demande. Merci de reformuler une question relative aux classements des hôpitaux."
        }
    
    def analyze_subsequent_message(self, prompt: str, conv_history: str) -> Dict[str, Any]:
        logger.debug(f"analyze_subsequent_message called: prompt={prompt}, conv_history={conv_history}")
        """
        Analyzes subsequent message and returns case dictionary.
        
        Args:
            prompt: User's subsequent message
            conv_history: Formatted conversation history
            
        Returns:
            Dict containing case analysis results
        """
        logger.info(f"Analyzing subsequent message: {prompt[:50]}...")
        
        # Check 1: Is message pertinent to chatbot?
        on_topic = self._check_pertinence(prompt, conv_history)
        logger.debug(f"Check 1 - on_topic: {on_topic}")
        
        if not on_topic:
            return {"on_topic": "FALSE"}
        
        # Check 2: Is it continuation of conversation?
        continuity = self._check_continuity(prompt, conv_history)
        logger.debug(f"Check 2 - continuity: {continuity}")
        
        # Check 3: Does it need search in ranking data?
        search_needed = self._check_search_needed(prompt, conv_history)
        logger.debug(f"Check 3 - search_needed: {search_needed}")
        
        # Build result dictionary
        result = {
            "on_topic": "TRUE",
            "continuity": str(continuity).upper(),
            "search_needed": str(search_needed).upper()
        }
        
        # Check 4: How to merge queries? (only if continuation and search needed)
        if continuity and search_needed:
            merge_query = self._check_merge_query(prompt, conv_history)
            logger.debug(f"Check 4 - merge_query: {merge_query}")
            result["merge_query"] = str(merge_query).upper()
        
        return result
    
    def _check_pertinence(self, prompt: str, conv_history: str = "") -> bool:
        """Check if message is pertinent to chatbot."""
        formatted_prompt = prompt_formatting(
            "sanity_check_chatbot_pertinence_prompt",
            prompt=prompt,
            conv_history=conv_history
        )
        return invoke_llm_and_parse_boolean(self.model, formatted_prompt, "check_pertinence")
    
    def _check_continuity(self, prompt: str, conv_history: str) -> bool:
        """Check if message is continuation of conversation."""
        formatted_prompt = prompt_formatting(
            "continuity_check_prompt",
            prompt=prompt,
            conv_history=conv_history
        )
        return invoke_llm_and_parse_boolean(self.model, formatted_prompt, "check_continuity")
    
    def _check_search_needed(self, prompt: str, conv_history: str = "") -> bool:
        """Check if message requires search in ranking data."""
        formatted_prompt = prompt_formatting(
            "search_needed_check_prompt",
            prompt=prompt,
            conv_history=conv_history
        )
        return invoke_llm_and_parse_boolean(self.model, formatted_prompt, "check_search_needed")
    
    def _check_merge_query(self, prompt: str, conv_history: str) -> bool:
        """Check how to merge queries (TRUE=merge, FALSE=add)."""
        formatted_prompt = prompt_formatting(
            "merge_query_check_prompt",
            prompt=prompt,
            conv_history=conv_history
        )
        return invoke_llm_and_parse_boolean(self.model, formatted_prompt, "check_merge_query")
    
    def determine_case(self, analysis: Dict[str, Any]) -> str:
        logger.debug(f"determine_case called: analysis={analysis}")
        """Determine which case applies based on analysis."""
        # Extract boolean values for easier comparison
        on_topic = analysis.get("on_topic") == "TRUE"
        continuity = analysis.get("continuity") == "TRUE"
        search_needed = analysis.get("search_needed") == "TRUE"
        merge_query = analysis.get("merge_query") == "TRUE"
        
        # Case mapping based on boolean combinations
        case_mapping = {
            (False, None, None, None): "case1",  # off-topic
            (True, True, True, True): "case2",   # continuation + search + merge
            (True, True, True, False): "case3",  # continuation + search + add
            (True, True, False, None): "case4",  # continuation + no search
            (True, False, True, None): "case5",  # new question + search
        }
        
        # Create key for lookup
        key = (on_topic, continuity if on_topic else None, 
            search_needed if on_topic else None, 
            merge_query if (on_topic and continuity and search_needed) else None)
        
        return case_mapping.get(key, "case6")  # default to case6
