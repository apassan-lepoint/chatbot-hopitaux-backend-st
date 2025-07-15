"""
This module defines a dictionary mapping medical specialties to 
    associated words that a user could refer to in their prompt. 

This dictionary is used to help identify the medical specialty

Attributes:
    specialties_dict (dict): 
        Keys (str): main medical specialties .
        Values (List[str]): lists of sub-specialties, procedures, and associated terms.
"""
import pandas as pd
from app.utils.config import PATHS

# Attempt to read the specialties from the Excel file
# If the file or sheet does not exist, specialties_dict will be an empty list
try:
    df_specialty = pd.read_excel(PATHS["ranking_file_path"], sheet_name="Palmarès")
    specialty_list = df_specialty.iloc[:, 0].drop_duplicates().dropna().tolist()
except Exception as e:
    specialty_list = []


# Dictionary mapping main specialties to their sub-specialties or procedures
specialty_categories_dict = {
        "Maternités": ["Accouchements normaux", "Accouchements à risques"],
        "Cardiologie": ["Angioplastie coronaire", "Cardiologie interventionnelle", "Chirurgie cardiaque adulte", "Chirurgie cardiaque de l’enfant et de l’adolescent", "Infarctus du myocarde", "Insuffisance cardiaque", "Rythmologie"],
        "Veines et artères": ["Ablation des varices", "Chirurgie des artères", "Chirurgie des carotides", "Hypertension artérielle", "Médecine vasculaire"],
        "Orthopédie": ["Arthrose de la main", "Chirurgie de l'épaule", "Chirurgie de la cheville", "Chirurgie du canal carpien", "Chirurgie du dos de l'adulte", "Chirurgie du dos de l'enfant et de l’adolescent", "Chirurgie du pied", "Ligaments du genou", "Prothèse de genou", "Prothèse de hanche"],
        "Ophtalmologie": ["Cataracte", "Chirurgie de la cornée", "Chirurgie de la rétine", "Glaucome", "Strabisme"],
        "Gynécologie et cancers de la femme": ["Cancer de l'ovaire", "Cancer de l'utérus", "Cancer du sein", "Endométriose", "Fibrome utérin"],
        "Appareil digestif": ["Appendicite", "Cancer de l'estomac ou de l'œsophage", "Cancer du côlon ou de l'intestin", "Cancer du foie", "Cancer du pancréas", "Chirurgie de l'obésité", "Chirurgie du rectum", "Hernies de l'abdomen", "Maladies inflammatoires chroniques de l'intestin (MICI)", "Proctologie"],
        "Psychiatrie": ["Dépression", "Schizophrénie"],
        "Urologie": ["Adénome de la prostate", "Calculs urinaires", "Cancer de la prostate", "Cancer de la vessie", "Cancer du rein", "Chirurgie des testicules de l’adulte", "Chirurgie des testicules de l’enfant et de l’adolescent"],
        "Tête et cou": ["Amygdales et végétations", "Audition", "Cancer ORL", "Chirurgie dentaire et orale de l’adulte", "Chirurgie dentaire et orale de l’enfant et de l’adolescent", "Chirurgie du nez et des sinus", "Chirurgie maxillo-faciale", "Glandes salivaires"],
        "Neurologie": ["Accidents vasculaires cérébraux", "Epilepsie de l’adulte", "Epilepsie de l’enfant et de l’adolescent", "Maladie de Parkinson"],
        "Cancerologie": ["Cancer de la thyroïde", "Cancer des os de l’enfant et de l’adolescent", "Cancer du poumon", "Cancers de la peau", "Chirurgie des cancers osseux de l'adulte", "Chirurgie des sarcomes des tissus mous", "Leucémie de l'adulte", "Leucémie de l'enfant et de l’adolescent", "Lymphome-myélome de l’adulte", "Tumeurs du cerveau de l'adulte"],
        "Diabète": ["Diabète de l'adulte", "Diabète de l'enfant et de l’adolescent"]
    }


def get_all_cancer_specialties():
    """
    Extract all cancer-related specialties from the specialty_categories_dict.
    Excludes surgical procedures and focuses on actual cancer types.
    
    Returns:
        list: List of all cancer-related specialty names
    """
    cancer_specialties = []
    
    # Exclude surgical procedures that contain "cancer" but are not cancer types
    excluded_terms = ["chirurgie", "surgery", "surgical"]
    
    for category, specialties in specialty_categories_dict.items():
        for specialty in specialties:
            # Check if specialty contains "cancer" (case-insensitive)
            if "cancer" in specialty.lower():
                # Exclude surgical procedures
                if not any(excluded_term in specialty.lower() for excluded_term in excluded_terms):
                    cancer_specialties.append(specialty)
    
    return cancer_specialties


def detect_general_cancer_query(message: str) -> bool:
    """
    Detect if the user is asking about cancer in general without specifying a particular type.
    
    Args:
        message (str): The user's query message
        
    Returns:
        bool: True if this is a general cancer query, False otherwise
    """
    message_lower = message.lower().strip()
    
    # Common ways users might ask about cancer in general in French
    general_cancer_terms = [
        "cancer",
        "cancers", 
        "le cancer",
        "les cancers",
        "du cancer",
        "des cancers",
        "pour cancer",
        "pour le cancer",
        "pour les cancers",
        "concernant le cancer",
        "concernant les cancers",
        "sur le cancer",
        "sur les cancers",
        "au niveau du cancer",
        "au niveau des cancers",
        "question cancer",
        "question cancers"
    ]
    
    # Check if the message contains general cancer terms
    for term in general_cancer_terms:
        if term in message_lower:
            # Make sure it's not already a specific cancer type
            all_cancer_specialties = get_all_cancer_specialties()
            for specific_cancer in all_cancer_specialties:
                if specific_cancer.lower() in message_lower:
                    return False  # It's a specific cancer, not general
            return True  # It's a general cancer query
    
    return False


def extract_specialty_keywords(message, specialty_categories_dict): # extract this to utility 
    # First check if this is a general cancer query
    if detect_general_cancer_query(message):
        all_cancer_specialties = get_all_cancer_specialties()
        if all_cancer_specialties:
            return "multiple matches:" + f"{','.join(all_cancer_specialties)}"
    
    # Check for specific specialty matches first (exact or close matches)
    message_lower = message.lower()
    for category, keywords in specialty_categories_dict.items():
        for keyword in keywords:
            if keyword.lower() in message_lower:
                # Return specific matches for multi-word specialties or exact single-word matches
                if len(keyword.split()) > 1 or keyword.lower() == message_lower.strip():
                    return keyword
                    
    # Check for category-level matches with flexible matching
    for category, keywords in specialty_categories_dict.items():
        category_lower = category.lower()
        
        # Direct category match
        if category_lower in message_lower:
            return "multiple matches:" + f"{','.join(keywords)}"
            
        # Handle common French variations and synonyms
        category_variations = {
            "maternités": ["maternité", "maternités", "accouchement", "accouchements", "grossesse", "enceinte", "bébé", "nouveau-né"],
            "gynécologie et cancers de la femme": ["gynécologie", "gynéco", "femme", "femmes", "utérus", "ovaires", "sein", "seins", "gynécologique"],
            "ophtalmologie": ["ophtalmologie", "ophtalmologique", "yeux", "œil", "oeil", "vision", "vue", "regard", "ophtalmo"],
            "appareil digestif": ["digestif", "digestion", "intestin", "intestins", "estomac", "ventre", "abdomen", "abdominal", "gastro"],
            "tête et cou": ["tête", "cou", "orl", "oreille", "nez", "gorge", "bouche", "dents", "dentaire", "maxillo"],
            "veines et artères": ["veines", "artères", "vasculaire", "circulation", "sang", "vaisseaux", "cardio-vasculaire"],
            "orthopédie": ["orthopédie", "orthopédique", "os", "articulation", "articulations", "squelette", "fracture", "prothèse", "prothèses"],
            "cardiologie": ["cardiologie", "cardiaque", "cardiaques", "cœur", "coeur", "cardio", "circulation", "tension", "artérielle"],
            "urologie": ["urologie", "urologique", "urine", "vessie", "rein", "reins", "prostate", "urinaire"],
            "psychiatrie": ["psychiatrie", "psychiatrique", "mental", "mentale", "psychologique", "dépression", "anxiété", "stress"],
            "cancerologie": ["cancérologie", "cancero", "oncologie", "oncologique", "tumeur", "tumeurs", "métastase", "chimiothérapie"],
            "neurologie": ["neurologie", "neurologique", "neuro", "cerveau", "système nerveux", "parkinson", "alzheimer", "avc"],
            "diabète": ["diabète", "diabétique", "sucre", "glycémie", "insuline", "endocrinologie"]
        }
        
        if category_lower in category_variations:
            for variation in category_variations[category_lower]:
                # Use word boundaries for single words to avoid partial matches
                # But allow substring matches for multi-word terms
                if len(variation.split()) == 1:
                    import re
                    pattern = r'\b' + re.escape(variation) + r'\b'
                    if re.search(pattern, message_lower, re.IGNORECASE):
                        return "multiple matches:" + f"{','.join(keywords)}"
                else:
                    # For multi-word terms, use substring matching
                    if variation in message_lower:
                        return "multiple matches:" + f"{','.join(keywords)}"