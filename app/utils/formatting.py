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

def format_correspondance_list(specialty_list: str) -> str:
    """
    Format a string containing multiple specialty correspondences into 
        a clean, deduplicated list.

    Args:
        liste_spe (str): String containing specialties, possibly with a prefix.

    Returns:
        str: Formatted string with deduplicated specialties.
    """

    # Remove the prefix and strip whitespace
    options_string = specialty_list.removeprefix("plusieurs correspondances:").strip()
    # Split the string into a list by commas
    options_list = options_string.split(',')
    # Remove periods and strip whitespace from each element
    options_list = [element.replace('.', '') for element in options_list]
    options_list = [element.strip() for element in options_list]
    # Filter elements that are present in the original string (deduplication logic)
    result = [element for element in options_list if element in specialty_list]
    # Reconstruct the formatted specialty string
    specialty="plusieurs correspondances:"+",".join(result)
    return specialty
    
def enlever_accents(original_string: str)-> str:
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
    
def tableau_en_texte(df: pd.DataFrame, no_city: bool)-> str:
    """
    Convert a DataFrame of hospital results into a formatted text response.

    Args:
        df (pd.DataFrame): DataFrame containing hospital results.

    Returns:
        str: Formatted string for chatbot response.
    """
    descriptions = []
    # Format results without city information
    if no_city:
        for index, row in df.iterrows():
            description = (
                f"{row['Etablissement']}:"
                f"Un établissement {row['Catégorie']}. "
                f"avec une note de {row['Note / 20']}"
            )
            descriptions.append(description)
        
        # Join all descriptions with line breaks for chatbot display
        joined_text = "<br>\n".join(descriptions)
        
        return joined_text
    # Format results with city and distance information
    else:  
        for index, row in df.iterrows():
            description = (
                f"{row['Etablissement']}:"
                f"Un établissement {row['Catégorie']} situé à {int(row['Distance'])} km. "
                f"avec une note de {row['Note / 20']}"
            )
            descriptions.append(description)
        
        # Join all descriptions with line breaks for chatbot display
        joined_text = "<br>\n".join(descriptions)
        
        return joined_text