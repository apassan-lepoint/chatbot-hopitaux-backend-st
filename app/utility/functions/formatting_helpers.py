"""
Utility functions for formatting chatbot responses and data.
"""

import pandas as pd
import re
from typing import List
import unidecode
from app.utility.functions.logging import get_logger


logger = get_logger(__name__)


def normalize_text(string, mode="string_matching"):
    """
    Normalizes text for different use cases using unidecode for accent removal.
    mode="string_matching": robust matching (accents, lowercase, remove French articles/prepositions, punctuation, collapse spaces)
    mode="web_link": accent removal, apostrophe-to-hyphen, spaces-to-hyphen, lowercase for web links
    """
    logger.debug(f"Normalizing text: '{string}' with mode='{mode}'")
    if not isinstance(string, str):
        return ""
    # Remove accents using unidecode
    string_no_accents = unidecode.unidecode(string)
    logger.debug(f"After unidecode: '{string_no_accents}'")
    if mode == "web_link":
        string_fin = string_no_accents.replace("'", '-').lower().replace(' ', '-')
        logger.debug(f"Web link normalized: '{string_fin}'")
        return string_fin
    elif mode == "string_matching":
        string_lower = string_no_accents.lower()
        string_no_prepositions = re.sub(r"\b(du|de la|de l'|de|la|le|les|au|aux|a la|a l'|a|des|pour|sur|concernant|au niveau du|au niveau de|au niveau des|question|l')\b", "", string_lower)
        string_letters_numbers = re.sub(r"[^a-z0-9 ]", " ", string_no_prepositions)
        string_fin = re.sub(r"\s+", " ", string_letters_numbers).strip()
        return string_fin


    
def format_links(result: str, links: list) -> str:
    """
    Appends formatted ranking links to the result string.
    """
    if links:
        for l in links:
            result += f"<br>[🔗Page du classement]({l})"
    return result

