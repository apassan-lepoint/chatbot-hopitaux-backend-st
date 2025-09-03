from typing import Dict, Any
from app.utility.logging import get_logger
from app.utility.wrappers import prompt_formatting
from app.utility.llm_helpers import invoke_llm_and_parse_boolean
from app.config.features_config import ERROR_MESSAGES

logger = get_logger(__name__)

class MultiTurn:
    """
    Class for handling multi-turn conversation logic.
    Implements 4-check system to determine conversation handling approach.
    
    Attributes:
        model: The language model used for analysis.
        case_responses: Dictionary mapping case identifiers to responses. 
    Methods:
        analyze_subsequent_message: Analyzes a user's subsequent message.
        _check_pertinence: Checks if the message is pertinent to the chatbot.
        _check_continuity: Checks if the message is a continuation of the conversation.
        _check_search_needed: Checks if the message requires search in ranking data.
        _check_merge_query: Checks how to merge queries (TRUE=merge, FALSE=add).
        determine_case: Determines which case applies based on analysis results.        
    """
    def __init__(self, model):
        logger.info("Initializing MultiTurn")
        self.model = model
        self.case_responses = {
            "case1": ERROR_MESSAGES["message_pertinence"],
        }
    

    def analyze_subsequent_message(self, prompt: str, conv_history: str) -> Dict[str, Any]:
        logger.debug(f"analyze_subsequent_message called: prompt={prompt}, conv_history={conv_history}")
        """
        Analyzes subsequent message to determine how to handle it. 
        Returns a dictionary with analysis results:     
        - on_topic: "TRUE" or "FALSE"
        - continuity: "TRUE" or "FALSE"
        - search_needed: "TRUE" or "FALSE"
        - merge_query: "TRUE" or "FALSE" (only if continuity and search_needed
        """
        logger.info(f"Analyzing subsequent message: {prompt}")
        
        # Track token/cost for each LLM call
        token_usage = {}
        cost = 0.0
        detection_method = 'llm'

        # Check 1: Is message pertinent to chatbot?
        formatted_prompt_pertinence = prompt_formatting("sanity_check_chatbot_pertinence_prompt", prompt=prompt, conv_history=conv_history)
        pertinence_response = self.model.invoke(formatted_prompt_pertinence)
        pertinence_content = pertinence_response.content.strip() if hasattr(pertinence_response, "content") else str(pertinence_response).strip()
        on_topic = pertinence_content == "1" or pertinence_content.upper() == "TRUE"
        usage = getattr(pertinence_response, 'usage', None)
        if usage:
            token_usage['pertinence'] = usage.get('total_tokens', None)
            cost += usage.get('cost', 0.0) if hasattr(usage, 'cost') else 0.0

        logger.debug(f"Check 1 - on_topic: {on_topic}")
        if not on_topic:
            return {"on_topic": "FALSE", "cost": cost, "token_usage": token_usage, "detection_method": detection_method}

        # Check 2: Is it continuation of conversation?
        formatted_prompt_continuity = prompt_formatting("continuity_check_prompt", prompt=prompt, conv_history=conv_history)
        continuity_response = self.model.invoke(formatted_prompt_continuity)
        continuity_content = continuity_response.content.strip() if hasattr(continuity_response, "content") else str(continuity_response).strip()
        continuity = continuity_content == "1" or continuity_content.upper() == "TRUE"
        usage = getattr(continuity_response, 'usage', None)
        if usage:
            token_usage['continuity'] = usage.get('total_tokens', None)
            cost += usage.get('cost', 0.0) if hasattr(usage, 'cost') else 0.0

        logger.debug(f"Check 2 - continuity: {continuity}")

        # Check 3: Does it need search in ranking data?
        formatted_prompt_search = prompt_formatting("search_needed_check_prompt", prompt=prompt, conv_history=conv_history)
        search_response = self.model.invoke(formatted_prompt_search)
        search_content = search_response.content.strip() if hasattr(search_response, "content") else str(search_response).strip()
        search_needed = search_content == "1" or search_content.upper() == "TRUE"
        usage = getattr(search_response, 'usage', None)
        if usage:
            token_usage['search_needed'] = usage.get('total_tokens', None)
            cost += usage.get('cost', 0.0) if hasattr(usage, 'cost') else 0.0

        logger.debug(f"Check 3 - search_needed: {search_needed}")

        result = {
            "on_topic": "TRUE",
            "continuity": str(continuity).upper(),
            "search_needed": str(search_needed).upper(),
            "cost": cost,
            "token_usage": token_usage,
            "detection_method": detection_method
        }

        # Check 4: How to merge queries? (only if continuation and search needed)
        if continuity and search_needed:
            formatted_prompt_merge = prompt_formatting("merge_query_check_prompt", prompt=prompt, conv_history=conv_history)
            merge_response = self.model.invoke(formatted_prompt_merge)
            merge_content = merge_response.content.strip() if hasattr(merge_response, "content") else str(merge_response).strip()
            result["merge_query"] = merge_content.upper()
            usage = getattr(merge_response, 'usage', None)
            if usage:
                token_usage['merge_query'] = usage.get('total_tokens', None)
                cost += usage.get('cost', 0.0) if hasattr(usage, 'cost') else 0.0
            result['cost'] = cost
            result['token_usage'] = token_usage

        return result
    

    def _check_pertinence(self, prompt: str, conv_history: str = "") -> bool:
        """
        Check if message is pertinent to chatbot.
        Returns True if pertinent, False otherwise.
        """
        formatted_prompt = prompt_formatting(
            "sanity_check_chatbot_pertinence_prompt",
            prompt=prompt,
            conv_history=conv_history
        )
        return invoke_llm_and_parse_boolean(self.model, formatted_prompt, "check_pertinence")
    

    def _check_continuity(self, prompt: str, conv_history: str) -> bool:
        """
        Check if message is continuation of conversation.
        Returns True if it is, False otherwise.
        """
        formatted_prompt = prompt_formatting(
            "continuity_check_prompt",
            prompt=prompt,
            conv_history=conv_history
        )
        return invoke_llm_and_parse_boolean(self.model, formatted_prompt, "check_continuity")
    

    def _check_search_needed(self, prompt: str, conv_history: str = "") -> bool:
        """
        Check if message requires search in ranking data.
        """
        formatted_prompt = prompt_formatting(
            "search_needed_check_prompt",
            prompt=prompt,
            conv_history=conv_history
        )
        return invoke_llm_and_parse_boolean(self.model, formatted_prompt, "check_search_needed")
    

    def _check_merge_query(self, prompt: str, conv_history: str) -> bool:
        """
        Check how to merge queries (TRUE=merge, FALSE=add).
        """
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
