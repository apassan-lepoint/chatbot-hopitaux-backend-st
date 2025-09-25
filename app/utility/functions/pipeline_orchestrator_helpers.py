"""
Utility functions for the Pipeline Orchestrator. 
"""

from datetime import datetime
from uuid import uuid4
from app.config.features_config import INSTITUTION_TYPE_URL_MAPPING
from app.utility.functions.logging import get_logger
from app.utility.functions.formatting_helpers import normalize_text

logger = get_logger(__name__)


def _sum_keys_with_substring(d, substr):
        if not isinstance(d, dict):
            return 0.0
        return sum(
            v if isinstance(v, (int, float)) else 0
            for k, v in d.items() if substr in k
        )


def get_costs_and_tokens(sanity_checks_results, query_analyst_results, conversation_analyst_results=None):
    """
    Aggregate total costs and token usage from sanity checks, query analyst, and conversation analyst.
    Returns only total variables for each step and overall.
    """
    logger.debug(f"Sanity check results for costs/tokens aggregation: {sanity_checks_results}")
    logger.debug(f"Query analyst results for costs/tokens aggregation: {query_analyst_results}")
    logger.debug(f"Conversation analyst results for costs/tokens aggregation: {conversation_analyst_results}")

    total_cost_sanity_checks_analyst = _sum_keys_with_substring(sanity_checks_results, 'cost') if sanity_checks_results is not None else 0.0
    total_token_usage_sanity_checks_analyst = _sum_keys_with_substring(sanity_checks_results, 'tokens') if sanity_checks_results is not None else 0

    total_cost_query_analyst = _sum_keys_with_substring(query_analyst_results, 'cost') if query_analyst_results is not None else 0.0
    total_token_usage_query_analyst = _sum_keys_with_substring(query_analyst_results, 'tokens') if query_analyst_results is not None else 0

    total_cost_conversation_analyst = _sum_keys_with_substring(conversation_analyst_results, 'cost') if conversation_analyst_results is not None else 0.0
    total_token_usage_conversation_analyst = _sum_keys_with_substring(conversation_analyst_results, 'tokens') if conversation_analyst_results is not None else 0

    total_cost = total_cost_sanity_checks_analyst + total_cost_query_analyst + total_cost_conversation_analyst
    total_token_usage = total_token_usage_sanity_checks_analyst + total_token_usage_query_analyst + total_token_usage_conversation_analyst
    costs_token_usage_dict = {
        'total_cost_sanity_checks_analyst': total_cost_sanity_checks_analyst,
        'total_cost_query_analyst': total_cost_query_analyst,
        'total_cost_conversation_analyst': total_cost_conversation_analyst,
        'total_cost': total_cost,
        'total_token_usage_sanity_checks_analyst': total_token_usage_sanity_checks_analyst,
        'total_token_usage_query_analyst': total_token_usage_query_analyst,
        'total_token_usage_conversation_analyst': total_token_usage_conversation_analyst,
        'total_token_usage': total_token_usage
    }
    logger.info(f"Aggregated costs and token usage: {costs_token_usage_dict}")

    return costs_token_usage_dict


def handle_variable_selection(variable_name: str, user_selected_value, detections: dict):
        """
        Generic handler for variable selection logic.
        Returns:
            (success: bool, value or response dict)
            - success=True → variable resolved (value may be None if nothing detected).
            - success=False → multiple options found, return dict with message + options.
        """
        if user_selected_value:
            logger.info(f"User selected {variable_name}: {user_selected_value}, using it directly.")
            return True, user_selected_value

        if variable_name not in detections:
            logger.debug(f"No detections found for {variable_name}.")
            return True, None  # no detection → leave unset

        detected = detections[variable_name]

        if isinstance(detected, list):
            if variable_name == "specialty":
                if len(detected) > 1:
                    logger.info(f"Multiple {variable_name} matches detected, returning for UI selection")
                    return False, {"message": f"Plusieurs spécialités correspondent à votre requête : {', '.join(detected)}", "multiple_specialty": detected}
                elif len(detected) == 1:
                    logger.info(f"Single specialty detected, returning as dict for consistency")
                    return True, {"specialty": detected[0]}
                else:
                    logger.info(f"No specialties detected, returning None")
                    return True, {"specialty": None}
            else:
                if len(detected) > 1:
                    logger.info(f"Multiple {variable_name} matches detected, returning for UI selection")
                    return False, {"message": f"Multiple {variable_name} options detected: {', '.join(detected)}", f"multiple_{variable_name}s": detected}
                elif len(detected) == 1:
                    return True, detected[0]  # single item list → auto-pick
                else:
                    return True, None
        return True, detected  # scalar (string, etc.)

def format_rows(df, label, number_institutions, location_not_specified):
    """
    Helper to format a DataFrame into chatbot response rows.
    """
    if df is None or df.empty:
        return f"<br>Aucun établissement {label} trouvé.<br>" if label else "<br>Aucun établissement trouvé.<br>"
    msg = (
        f"Seulement {len(df)} établissements {label} trouvés :<br>"
        if label and len(df) < number_institutions
        else f"Voici les établissements {label} :<br>" if label
        else f"Seulement {len(df)} établissements trouvés :<br>" if len(df) < number_institutions
        else "Voici les établissements trouvés :<br>"
    )
    for _, row in df.iterrows():
        name = row.get("ETABLISSEMENT_NOM", row.get("ETABLISSEMENT", "Nom inconnu"))
        type_ = row.get("ETABLISSEMENT_TYPE", row.get("Catégorie", label if label else "Type inconnu"))
        score = row.get("CLASSEMENT_NOTE", row.get("Note / 20", "score inconnu"))
        if location_not_specified:
            msg += f"{name}: Un établissement {type_} avec une note de {score} sur 20<br>"
        else:
            distance_val = row.get("distance_km", row.get("Distance", None))
            distance_str = f"{int(distance_val)} km" if isinstance(distance_val, (int, float)) and distance_val is not None else "distance inconnue"
            msg += f"{name}: Un établissement {type_} situé à {distance_str} avec une note de {score} sur 20<br>"
    return msg

def generate_web_link(specialty: str, institution_type: str) -> str:
    """
    Helper method to generate a single web ranking link.
    """
    logger.debug(f"Generating web link for specialty '{specialty}' and institution_type '{institution_type}'")
    web_link = specialty.replace(' ', '-')
    web_link = f'https://www.lepoint.fr/hopitaux/classements/{web_link}-{institution_type}.php'
    web_link = web_link.lower()
    return normalize_text(string=web_link, mode="web_link")


def get_institution_type_for_url(institution_type: str) -> str:
        """
        Convert institution type to format expected by web URLs. Assumes input is already normalized.
        Args:
            institution_type (str): The institution type to convert.
        Returns:
            str: Converted institution type for URL, or the original if not found in mapping.   
        """
        logger.debug(f"Mapping institution type for URL: {institution_type}")
        return INSTITUTION_TYPE_URL_MAPPING.get(institution_type, institution_type.lower())