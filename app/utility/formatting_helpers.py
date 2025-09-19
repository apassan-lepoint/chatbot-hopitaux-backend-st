"""
Utility functions for formatting chatbot responses and data.
"""

import pandas as pd
import re
from typing import List
import unidecode


def normalize_text(string, mode="string_matching"):
    """
    Normalizes text for different use cases using unidecode for accent removal.
    mode="string_matching": robust matching (accents, lowercase, remove French articles/prepositions, punctuation, collapse spaces)
    mode="web_link": accent removal and apostrophe-to-hyphen for web links
    """
    if not isinstance(string, str):
        return ""
    # Remove accents using unidecode
    string_no_accents = unidecode.unidecode(string)
    if mode == "web_link":
        return string_no_accents.replace("'", '-')
    elif mode == "string_matching":
        string_lower = string_no_accents.lower()
        string_no_prepositions = re.sub(r"\b(du|de la|de l'|de|la|le|les|au|aux|a la|a l'|a|des|pour|sur|concernant|au niveau du|au niveau de|au niveau des|question|l')\b", "", string_lower)
        string_letters_numbers = re.sub(r"[^a-z0-9 ]", " ", string_no_prepositions)
        string_fin = re.sub(r"\s+", " ", string_letters_numbers).strip()
        return string_fin


# TODO: REFACTOR
def format_response(public_df: pd.DataFrame, private_df: pd.DataFrame, number_institutions: int, city_not_specified: bool) -> str:
    """
    Format public and private DataFrames into a chatbot response, with count checks and user messages.
    """
    response = ""
    # Private institutions
    if private_df is not None and not private_df.empty:
        if len(private_df) < number_institutions:
            response += f"Seulement {len(private_df)} établissements privés trouvés :<br>"
        else:
            response += "Voici les établissements privés :<br>"
        for index, row in private_df.iterrows():
            if city_not_specified:
                response += f"{row['Etablissement']}: Un établissement {row['Catégorie']}. avec une note de {row['Note / 20']} de 20<br>"
            else:
                distance_val = row.get('Distance', None)
                if isinstance(distance_val, (int, float)) and distance_val is not None:
                    distance_str = f"{int(distance_val)} km"
                else:
                    distance_str = "distance inconnue"
                response += f"{row['Etablissement']}: Un établissement {row['Catégorie']} situé à {distance_str}. avec une note de {row['Note / 20']} de 20<br>"
    elif private_df is not None:
        response += "<br>Aucun établissement privé trouvé.<br>"
    # Public institutions
    if public_df is not None and not public_df.empty:
        if len(public_df) < number_institutions:
            response += f"Seulement {len(public_df)} établissements publics trouvés :<br>"
        else:
            response += "Voici les établissements publics :<br>"
        for index, row in public_df.iterrows():
            if city_not_specified:
                response += f"{row['Etablissement']}: Un établissement {row['Catégorie']}. avec une note de {row['Note / 20']} de 20<br>"
            else:
                distance_val = row.get('Distance', None)
                if isinstance(distance_val, (int, float)) and distance_val is not None:
                    distance_str = f"{int(distance_val)} km"
                else:
                    distance_str = "distance inconnue"
                response += f"{row['Etablissement']}: Un établissement {row['Catégorie']} situé à {distance_str}. avec une note de {row['Note / 20']} de 20<br>"
    elif public_df is not None:
        response += "<br>Aucun établissement public trouvé.<br>"
    return response.rstrip('<br>')
    
    
def format_links(result: str, links: list) -> str:
    """
    Appends formatted ranking links to the result string.
    """
    if links:
        for l in links:
            result += f"<br>[🔗Page du classement]({l})"
    return result


def extract_links_from_text(text: str) -> List[str]:
    """
    Extract all URLs from a given string using regex.
    Deduplicates automatically.
    """
    url_pattern = r"https?://[^\s\"'>]+"
    matches = re.findall(url_pattern, text)
    return list(set(matches))