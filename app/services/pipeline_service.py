"""
Main pipeline orchestration for chatbot query processing.

This file defines the Pipeline class, which coordinates the extraction, filtering,
    ranking, and formatting of hospital data in response to user queries.
"""

import pandas as pd
from app.services.processing_service import Processing
from app.utils.formatting import tableau_en_texte
from app.utils.config import PATHS
from app.utils.logging import get_logger
logger = get_logger(__name__)

class Pipeline:
    """
    Orchestrates the processing of user queries to extract hospital rankings.
    This class handles the extraction of specialties, cities, and institution types,
    retrieves relevant data from Excel files, calculates distances, and formats the final response.

    Attributes:
        ranking_file_path (str): Path to the Excel file containing hospital rankings.
        specialty (str): The medical specialty extracted from the user query.   
        institution_type (str): Type of institution (public/private) mentioned in the query.
        city (str): The city or department extracted from the user query.
        city_not_specified (bool): Flag indicating if no city was found in the query.
        df_gen (pd.DataFrame): DataFrame containing general hospital rankings.
        institution_mentioned (bool): Flag indicating if a specific institution was mentioned in the query.
        institution_name (str): Name of the institution mentioned in the query.
        answer (Processing): Instance of Processing class for data extraction and transformation.
      """
    def __init__(self):
        """
        Initializes the Pipeline class, sets up file paths, and prepares variables for query processing.
        """
        self.ranking_file_path= PATHS["ranking_file_path"]
        self.specialty= None
        self.institution_type= None
        self.city = None
        self.city_not_specified= None # Flag indicating if no city was found in the query
        self.df_gen = None # DF for results 
        self.institution_mentioned=None
        self.institution_name=None
        self.answer=Processing() # Instance of Processing for data extraction and transformation

    def _normalize_specialty_for_display(self, specialty: str) -> str:
        """
        Normalize specialty format for display purposes.
        Converts various specialty formats to user-friendly display format.
        
        Args:
            specialty (str): The specialty string to normalize
            
        Returns:
            str: Normalized specialty string for display
        """
        if not specialty:
            return "aucune correspondance"
            
        # Handle no match cases - standardize to French for display
        if specialty.lower() in ["no specialty match", "aucune correspondance", "no match", ""]:
            return "aucune correspondance"
            
        # Handle multiple matches format - DON'T normalize these, return as-is
        if specialty.startswith(("multiple matches:", "plusieurs correspondances:")):
            return specialty  # Return the full multiple matches string
            
        return specialty

    def _is_no_specialty_match(self, specialty: str) -> bool:
        """
        Check if specialty indicates no match.
        
        Args:
            specialty (str): The specialty string to check
            
        Returns:
            bool: True if specialty indicates no match
        """
        if not specialty:
            return True
        # Standardize check to handle both languages but prioritize English
        return specialty.lower() in ["no specialty match", "aucune correspondance", "no match", ""]

    
    def _format_response_with_specialty(self, base_message: str, count: int, radius_km: int = None, city: str = None) -> str:
        """
        Helper method to format response messages with specialty context.
        
        Args:
            base_message: Base message template
            count: Number of establishments
            radius_km: Search radius in kilometers (optional)
            city: City name (optional)
        
        Returns:
            str: Formatted response message
        """
        if radius_km and city:
            location_part = f" dans un rayon de {radius_km}km autour de {city}"
        else:
            location_part = ""
        
        if self._is_no_specialty_match(self.specialty):
            if count == 1:
                specialty_part = "du palmarès général"
            else:
                specialty_part = "au classement général" if "classement" in base_message else "du palmarès général"
        else:
            display_specialty = self._normalize_specialty_for_display(self.specialty)
            specialty_part = f"pour la pathologie {display_specialty}" if "pathologie" in base_message else f"pour la pathologie: {display_specialty}"
        
        return base_message.format(count=count, specialty=specialty_part, location=location_part)

    def _create_response_and_log(self, message: str, table_str: str, prompt: str) -> str:
        """
        Helper method to create final response, log it, and save to CSV.
        
        Args:
            message: Response message
            table_str: Formatted table string
            prompt: Original user prompt
        
        Returns:
            str: Complete formatted response
        """
        response = f"{message}\n{table_str}"
        self.answer.create_csv(question=prompt, reponse=response)
        logger.debug(f"Formatted response: {response}")
        return response

    
    def _try_radius_search(self, df: pd.DataFrame, radius: int, top_k: int, prompt: str) -> str:
        """
        Try to find results within a specific radius.
        
        Args:
            df (pd.DataFrame): DataFrame with hospitals and distances
            radius (int): Search radius in kilometers
            top_k (int): Number of top hospitals to return
            prompt (str): The user's question
            
        Returns:
            str: Formatted response string if results found, None otherwise
        """
        return self.get_filtered_and_sorted_df(df, radius, top_k, prompt)

    
    def reset_attributes(self):
        """
        Resets pipeline attributes for a new user query.
        """
        logger.debug("Resetting pipeline attributes for new query")
        for attr in [
            "specialty", "institution_type", "city", "df_with_cities", "specialty_df",
            "city_not_specified", "institution_mentioned", "institution_name", "df_gen"
        ]:
            setattr(self, attr, None)

    
    def extract_query_parameters(self, prompt: str, detected_specialty: str = None)->str:
        """
        Retrieves key aspects of the user query: city, institution type, and specialty.
        Updates instance variables accordingly.
        Args:
            prompt (str): The user's question.
            detected_specialty (str, optional): Pre-detected specialty to preserve user's selection.
        Returns:
            str: The detected specialty.
        """
        logger.info(f"Getting infos from pipeline for prompt: {prompt}")
        self.answer.get_infos(prompt, detected_specialty)
        for attr in ["specialty", "city", "institution_type", "institution_mentioned", "institution_name"]:
            setattr(self, attr, getattr(self.answer, attr))
        logger.debug(f"Pipeline infos - specialty: {self.specialty}, city: {self.city}, institution_type: {self.institution_type}, institution: {self.institution_name}")
        return self.specialty

    
    def build_ranking_dataframe_with_distances(self, prompt: str, excel_path: str, detected_specialty: str = None) -> pd.DataFrame:
        """
        Retrieves the ranking DataFrame based on the user query, including distance calculations if a city is specified.
        Args:
            prompt (str): The user's question.
            excel_path (str): Path to the ranking Excel file.
            detected_specialty (str, optional): Pre-detected specialty from conversation context.
        Returns:
            pd.DataFrame: DataFrame with ranking and distance information, or general results if no city is found.
        """
        logger.info(f"Building ranking DataFrame with distances for prompt: {prompt}")
        
        # Find the relevant Excel sheet and extract info
        self.df_gen = self.answer.find_excel_sheet_with_privacy(prompt, detected_specialty)
        
        # Only extract query parameters if we don't have a detected specialty
        # This prevents overriding user's specialty selection
        if not detected_specialty or detected_specialty == "no specialty match":
            self.extract_query_parameters(prompt)
        else:
            # If we have a detected specialty, we still need to extract other parameters (city, institution_type, etc.)
            # but we must preserve the specialty
            original_specialty = self.specialty
            self.extract_query_parameters(prompt, detected_specialty)
            # Restore the detected specialty
            self.specialty = detected_specialty
            self.answer.specialty = detected_specialty
            
        if self.answer.specialty_ranking_unavailable:
            logger.warning("Ranking not found for requested specialty/type")
            return self.df_gen
        if self.answer.city in ['aucune correspondance', 'no match'] or not self.answer.city:
            logger.info("No city found in the query, returning general ranking DataFrame")
            self.city_not_specified= True
            return self.df_gen
    
        self.city_not_specified= False
        logger.info("Extracting hospital locations and calculating distances")
        self.answer.extract_local_hospitals()
        return self.answer.get_df_with_distances()
        
    
    def get_filtered_and_sorted_df(self, df: pd.DataFrame, max_radius_km: int, top_k: int, prompt:str) -> str:
        """
        Filters and sorts the ranking DataFrame by distance and score, and formats the response.
        Args:
            df (pd.DataFrame): DataFrame with hospitals and their distances.
            max_radius_km (int): Maximum search radius in kilometers.
            top_k (int): Number of top hospitals to return.
            prompt (str): The user's question.
        Returns:
            str: Formatted response string.
        """
        logger.info(f"Filtering and sorting DataFrame with max_radius_km={max_radius_km}, top_k={top_k}, prompt={prompt}")
        
        # Default value to avoid UnboundLocalError
        reponse = "Aucun résultat trouvé."  
        
        # If an institution was mentioned in user's query, check if it exists in the DataFrame.
        if self.institution_mentioned==True:
            logger.info(f"Institution mentioned in query: {self.institution_name}")
            validity=False
            
            # Check if the institution is present in the DataFrame
            if df['Etablissement'].str.contains(self.institution_name).any():
                validity=True
            
            # If not present, return an appropriate message depending on specialty context
            if validity == False:
                logger.warning(f"Institution {self.institution_name} not found in DataFrame")
                display_specialty = self._normalize_specialty_for_display(self.specialty)
                if self._is_no_specialty_match(self.specialty):
                    return f"Cet établissement ne fait pas partie des 50 meilleurs établissements du palmarès global"
                else: 
                    return f"Cet établissement n'est pas présent pour la pathologie {display_specialty}, vous pouvez cependant consulter le classement suivant:"
            
            # If present, find its position in the sorted DataFrame
            df_sorted=df.sort_values(by='Note / 20', ascending=False).reset_index(drop=True)
            position = df_sorted.index[df_sorted["Etablissement"].str.contains(self.institution_name, case=False, na=False)][0] + 1  # +1 for human-readable ranking (starts at 1)
            
            # Build a detailed description of all ranked institutions
            descriptions = []
            for index, row in df_sorted.iterrows():
                description=row[['Etablissement','Catégorie','Note / 20']]

                descriptions.append(str(description))
            response = "<br>\n".join(descriptions)

            #  Build the response string with the institution's rank and context
            response=f"{self.institution_name} est classé n°{position} "
            display_specialty = self._normalize_specialty_for_display(self.specialty)
            if self._is_no_specialty_match(self.specialty):
                response=response+f"du palmarès général"
            else:
                response=response+f"du palmarès {display_specialty}."
            if self.institution_type not in ['aucune correspondance', 'no match'] and self.institution_type:
                        response=response+f" {self.institution_type}."
            logger.debug(f"Formatted response: {reponse}")
            return response

        # If no specific institution is mentioned, filter hospitals by distance and select the top_k by score
        filtered_df = df[df["Distance"] <= max_radius_km]
        self.sorted_df = filtered_df.nlargest(top_k, "Note / 20")
        logger.debug(f"Filtered DataFrame shape: {self.sorted_df.shape}")
        
        if self.sorted_df.shape[0] == top_k:
            logger.info(f"Found {top_k} results within {max_radius_km}km")
            # Format the top_k results as a text table
            res_str = tableau_en_texte(self.sorted_df, self.city_not_specified)
            message = self._format_response_with_specialty(
                "Voici les {count} meilleurs établissements {specialty}{location}:",
                top_k, max_radius_km, self.city
            )
            return self._create_response_and_log(message, res_str, prompt)
        
        # If the search radius is at its maximum, return all found institutions (even if less than top_k)
        elif max_radius_km == 500:
            res_str = tableau_en_texte(self.sorted_df, self.city_not_specified)
            message = self._format_response_with_specialty(
                "Voici les {count} meilleurs établissements {specialty}{location}:<br>",
                self.sorted_df.shape[0], max_radius_km, self.city
            )
            return self._create_response_and_log(message, res_str, prompt)
        
        # If no results found, return None so the caller can try with a larger radius
        logger.warning("No results found within current radius")
        return None

    
    def generate_response(self, 
        prompt: str, top_k: int = 3, max_radius_km: int = 50, detected_specialty: str=None) -> str:
        """
        Main entry point: processes the user question and returns a formatted answer with ranking and links.

        Args:
            prompt (str): The user's question.
            top_k (int, optional): Number of top hospitals to return. Defaults to 3.
            max_radius_km (int, optional): Search radius in kilometers. Defaults to 50.
            detected_specialty (str, optional): Specialty to use if already known.

        Returns:
            str or tuple: The formatted answer and any relevant links.
        """

        logger.info(f"Starting pipeline processing - prompt: {prompt[:50]}..., top_k: {top_k}, max_radius_km: {max_radius_km}, detected_specialty: {detected_specialty}")
        
        # Reset relevant attributes for a new query
        self.reset_attributes()
        self.specialty= detected_specialty
        logger.debug("Reset pipeline attributes for new query")

        # Check if the user specified a different top_k in their prompt
        logger.debug("Detecting top_k from prompt")
        detected_topk = self.answer.llm_service.detect_topk(prompt)
        if detected_topk!='non mentionné':
            top_k=detected_topk
            logger.debug(f"Top_k updated from prompt: {top_k}")

        # Defensive insertion: ensure detected_specialty is never empty or None
        if not detected_specialty or (isinstance(detected_specialty, str) and detected_specialty.strip() == ""):
            detected_specialty = "no specialty match"
        
        # Set the specialty in the processing service
        if self.specialty is not None:
            self.answer.specialty= detected_specialty
            logger.debug(f"Set specialty to: {detected_specialty}")
        else:
            self.answer.specialty= None
            logger.debug("Set specialty to None")
        relevant_file=self.ranking_file_path
        
        # If we have a detected_specialty that's not "no specialty match", use it directly
        if detected_specialty and detected_specialty != "no specialty match":
            logger.info(f"Using provided detected_specialty: {detected_specialty}")
            extracted_specialty = detected_specialty
            # Also set it in the answer object to ensure consistency
            self.answer.specialty = detected_specialty
            # When we have a detected specialty, we still need to extract other parameters (city, institution_type, etc.)
            # but NOT the specialty itself, so we call extract_query_parameters to get other info
            self.extract_query_parameters(prompt, detected_specialty)
            # But then reset the specialty to the provided one to avoid overwriting
            self.specialty = detected_specialty
            self.answer.specialty = detected_specialty
        else:
            # Extract query parameters to get the specialty only if we don't have a detected one
            extracted_specialty = self.extract_query_parameters(prompt)
            
            # Check if multiple specialties were detected and return early for UI handling
            if extracted_specialty and extracted_specialty.startswith("multiple matches:"):
                logger.info("Multiple specialty matches detected, returning for UI selection")
                specialty_list = extracted_specialty.replace("multiple matches:", "").strip()
                formatted_response = f"Plusieurs spécialités cardiaques sont disponibles. Veuillez préciser laquelle vous intéresse:\n{specialty_list.replace(',', '\n- ')}"
                logger.debug(f"Returning multiple matches response: {formatted_response}")
                return formatted_response, None
        
        # Retrieve the DataFrame with ranking and (if applicable) distances
        logger.debug("Retrieving ranking DataFrame with distances")
        df = self.build_ranking_dataframe_with_distances(prompt, relevant_file, detected_specialty)
        logger.debug(f"Retrieved DataFrame shape: {df.shape if hasattr(df, 'shape') else 'N/A'}")
        
        # Handle geolocation API errors
        if self.answer.geolocation_api_error:
            logger.error("Geopy API error encountered, cannot calculate distances")
            return "Dû à une surutilisation de l'API de Geopy, le service de calcul des distances est indisponible pour le moment, merci de réessayer plus tard ou de recommencer avec une question sans localisation spécifique", None

        self.link=self.answer.web_ranking_link

        # Handle cases where no results are found for the requested specialty/type
        if self.answer.specialty_ranking_unavailable :
            logger.warning("Ranking not found for requested specialty/type, suggesting alternative")
            if self.answer.institution_type=='Public':   
                return "Nous n'avons pas d'établissement public pour cette pathologie, mais un classement des établissements privés existe. ", self.link
            elif self.answer.institution_type=='Privé': 
                return "Nous n'avons pas d'établissement privé pour cette pathologie, mais un classement des établissements publics existe. ", self.link

        # If a specific institution is mentioned, return its ranking and the link
        if self.institution_mentioned:
            logger.info("Returning result for mentioned institution")
            res=self.get_filtered_and_sorted_df(df, max_radius_km, top_k,prompt)
            logger.debug(f"Result: {res}, Links: {self.link}")
            return res, self.link
        
        # If a city was found, try to find results within increasing radii
        if self.city_not_specified == False:
            logger.info("City found, searching for results within increasing radii")
            # Try with progressively larger radii: 50km, 100km, 200km, 500km
            for radius in [max_radius_km, 100, 200, 500]:
                res = self._try_radius_search(df, radius, top_k, prompt)
                if res:
                    return res, self.link
            # If we get here, no results were found even at maximum radius
            logger.warning("No results found even at maximum radius")
            return "Aucun résultat trouvé dans votre région.", self.link
        
        else:
            logger.info("No city found, returning general ranking")
            # If no city was found, return the top_k institutions from the general ranking 
            # Note: Don't call extract_query_parameters again here as it would override user's specialty selection
            # All parameters should have been extracted earlier in the pipeline
            res_tab = self.df_gen.nlargest(top_k, "Note / 20")
            res_str = tableau_en_texte(res_tab, self.city_not_specified)
            
            base_message = "Voici le meilleur établissement" if top_k == 1 else f"Voici les {top_k} meilleurs établissements"
            display_specialty = self._normalize_specialty_for_display(self.specialty)
            if self._is_no_specialty_match(self.specialty):
                res = f"{base_message}:<br> \n{res_str}"
            else:
                res = f"{base_message} pour la pathologie {display_specialty}<br> \n{res_str}"
            
            logger.debug(f"Result: {res}, Links: {self.link}")
            return (res, self.link)
