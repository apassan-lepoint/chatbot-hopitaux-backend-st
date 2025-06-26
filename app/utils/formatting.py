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

    df = pd.read_csv(file_path)
    colonne = df['Valeurs'].dropna()  
    resultat = colonne.astype(str).str.cat(sep="\n")
    return resultat

def format_correspondance_list(liste_spe: str) -> str:
    """
    Format a string containing multiple specialty correspondences into 
        a clean, deduplicated list.

    Args:
        liste_spe (str): String containing specialties, possibly with a prefix.

    Returns:
        str: Formatted string with deduplicated specialties.
    """

    options_string = liste_spe.removeprefix("plusieurs correspondances:").strip()
    options_list = options_string.split(',')
    options_list = [element.replace('.', '') for element in options_list]
    options_list = [element.strip() for element in options_list]
    resultat = [element for element in options_list if element in liste_spe]
    specialty="plusieurs correspondances:"+",".join(resultat)
    return specialty
    
def enlever_accents(chaine: str)-> str:
    """
    Remove accents from a string and replace apostrophes with hyphens.

    Args:
        chaine (str): Input string.

    Returns:
        str: Normalized string without accents.
    """
    
    chaine_normalisee = unicodedata.normalize('NFD', chaine)
    chaine_sans_accents = ''.join(c for c in chaine_normalisee if unicodedata.category(c) != 'Mn')
    chaine_sans_accents = chaine_sans_accents.replace("'", '-')
    return chaine_sans_accents
    
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
        
        # Joindre toutes les descriptions avec des sauts de ligne
        texte_final = "<br>\n".join(descriptions)
        
        return texte_final
    # Format results with city and distance information
    else:  
        for index, row in df.iterrows():
            description = (
                f"{row['Etablissement']}:"
                f"Un établissement {row['Catégorie']} situé à {int(row['Distance'])} km. "
                f"avec une note de {row['Note / 20']}"
            )
            descriptions.append(description)
        
        # Join all descriptions with line breaks
        texte_final = "<br>\n".join(descriptions)
        
        return texte_final