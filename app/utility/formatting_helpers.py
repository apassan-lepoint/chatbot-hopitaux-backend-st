"""
Utility functions for formatting chatbot responses and data.

This file provides helpers to convert DataFrames to text, remove accents,
    and format lists or mappings for display or prompt injection.
"""

import pandas as pd
import unicodedata

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
    if not private_df.empty:
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
    else:
        response += "<br>Aucun établissement privé trouvé.<br>"
    # Public institutions
    if not public_df.empty:
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
    else:
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


## KEEP FOLLOWING FUNCTIONS FOR NOW; DELETE AFTER TESTING

# def format_correspondance_list(specialty_list: str) -> str:
#     """
#     Format a string containing multiple specialty correspondences into 
#         a clean, deduplicated list.

#     Args:
#         specialty_list (str): String containing specialties, possibly with a prefix.

#     Returns:
#         str: Formatted string with deduplicated specialties.
#     """
#     # Handle both French and English prefixes
#     if specialty_list.startswith("plusieurs correspondances:"):
#         options_string = specialty_list.removeprefix("plusieurs correspondances:").strip()
#         prefix = "multiple matches:"
#     elif specialty_list.startswith("multiple matches:"):
#         options_string = specialty_list.removeprefix("multiple matches:").strip()
#         prefix = "multiple matches:"
#     else:
#         # If no prefix found, assume the whole string is the options
#         options_string = specialty_list.strip()
#         prefix = "multiple matches:"
    
#     # Split the string into a list by commas
#     options_list = options_string.split(',')
    
#     # Remove periods and strip whitespace from each element
#     options_list = [element.replace('.', '') for element in options_list]
#     options_list = [element.strip() for element in options_list if element.strip()]
    
#     # Remove duplicates while preserving order
#     seen = set()
#     result = []
#     for element in options_list:
#         if element not in seen:
#             seen.add(element)
#             result.append(element)
    
#     # Reconstruct the formatted specialty string
#     specialty = prefix + ",".join(result)
    
#     return specialty