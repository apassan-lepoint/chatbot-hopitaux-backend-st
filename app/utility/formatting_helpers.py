"""
Utility functions for formatting chatbot responses and data.

This file provides helpers to convert DataFrames to text, remove accents,
    and format lists or mappings for display or prompt injection.
"""

import pandas as pd
import unicodedata
import re
from typing import List

def format_mapping_words_csv(file_path: str) -> str:
    """
    Convert a CSV file of specialty mapping words into a string for prompt injection.

    Args:
        file_path (str): Path to the CSV file containing specialty mapping words.

    Returns:
        str: A string with each value separated by a newline.
    """
    # Read the CSV file and extract the 'Valeurs' column, dropping any NaN values
    df = pd.read_csv(file_path)
    column = df['Valeurs'].dropna()
    
    # Concatenate all values into a single string separated by newlines  
    resultat = column.astype(str).str.cat(sep="\n")
    
    return resultat

    
def remove_accents(original_string: str)-> str:
    """
    Remove accents from a string and replace apostrophes with hyphens.

    Args:
        chaine (str): Input string.

    Returns:
        str: Normalized string without accents.
    """
    # Normalize the string to separate accents
    normalized_string = unicodedata.normalize('NFD', original_string)
    
    # Remove all accent characters
    string_no_accents = ''.join(c for c in normalized_string if unicodedata.category(c) != 'Mn')
    
    # Replace apostrophes with hyphens
    string_no_accents = string_no_accents.replace("'", '-')
    
    return string_no_accents


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

    Args:
        result (str): The main result string.
        links (list): List of links to append.

    Returns:
        str: The formatted result string with links.
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
    # Regex with no capturing groups
    url_pattern = r"https?://[^\s\"'>]+"
    matches = re.findall(url_pattern, text)
    return list(set(matches))