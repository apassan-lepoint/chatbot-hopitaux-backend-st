"""
Main pipeline orchestration for chatbot query processing.

This file defines the PipelineOrchestrator class, which coordinates the extraction, filtering,
    ranking, and formatting of hospital data in response to user queries.
"""

import pandas as pd
from app.services.data_processing_service import DataProcessor
from app.features.prompt_detection.prompt_detection_manager import PromptDetectionManager
from app.utility.formatting_helpers import format_response
from app.config.file_paths_config import PATHS
from app.utility.logging import get_logger

logger = get_logger(__name__)

class PipelineOrchestrator:
    """
    Orchestrates the processing of user queries to extract hospital rankings.
    This class handles the extraction of specialties, cities, and institution types,
    retrieves relevant data from Excel files, calculates distances, and formats the final response.
    Uses the centralized TopKDetector for all top-k related operations.
    """
    def __init__(self):
        logger.info("Initializing PipelineOrchestrator")
        """
        Initializes the PipelineOrchestrator class, sets up file paths, and prepares variables for query processing.
        """
        self.ranking_file_path= PATHS["ranking_file_path"]
        self.specialty= None
        self.institution_type= None
        self.city = None
        self.city_not_specified= None # Flag indicating if no city was found in the query
        self.df_gen = None # DF for results 
        self.institution_mentioned=None
        self.institution_name=None
        self.data_processor=DataProcessor() # Instance of DataProcessor for data extraction and transformation

    def _normalize_specialty_for_display(self, specialty: str) -> str:
        logger.debug(f"Normalizing specialty for display: {specialty}")
        """
        Normalize specialty format for display purposes and check for no match.
        Returns tuple: (normalized string, is_no_match)
        """
        # Handle empty or no-match specialty cases
        if not specialty or specialty.lower() in ["no specialty match", "aucune correspondance", "no match", ""]:
            return "aucune correspondance", True
        # Handle multiple matches case (for UI selection)
        if specialty.startswith(("multiple matches:", "plusieurs correspondances:")):
            return specialty, False
        # Return specialty as-is for display
        return specialty, False

    def _format_response_with_specialty(self, base_message: str, count: int, radius_km: int = None, city: str = None) -> str:
        logger.debug(f"Formatting response with specialty: base_message='{base_message}', count={count}, radius_km={radius_km}, city={city}")
        """
        Helper method to format response messages with specialty context.
        """
        # Build location part of the message if city and radius are provided
        location_part = f" dans un rayon de {radius_km}km autour de {city}" if radius_km and city else ""
        # Normalize specialty and check for no match
        display_specialty, is_no_match = self._normalize_specialty_for_display(self.specialty)
        # Build specialty part of the message based on context
        if is_no_match:
            specialty_part = "du palmarès général" if count == 1 else ("au classement général" if "classement" in base_message else "du palmarès général")
        elif display_specialty.startswith("multiple matches:"):
            specialty_part = ""
        else:
            specialty_part = f"pour la pathologie {display_specialty}" if "pathologie" in base_message else f"pour la pathologie: {display_specialty}"
        # Format and return the final message
        return base_message.format(count=count, specialty=specialty_part, location=location_part)

    def _create_response_and_log(self, message: str, table_str: str, prompt: str) -> str:
        logger.info(f"Creating response and logging for prompt: {prompt}")
        """
        Helper method to create final response, log it, and save to CSV.
        """
        # Combine message and table for final response
        response = f"{message}\n{table_str}"
        # Save response to CSV for history
        self.data_processor.create_csv(question=prompt, reponse=response)
        logger.debug(f"Formatted response: {response}")
        return response

    def _try_radius_search(self, df: pd.DataFrame, radius: int, top_k: int, prompt: str) -> str:
        logger.info(f"Trying radius search: radius={radius}, top_k={top_k}, prompt={prompt}")
        """
        Try to find results within a specific radius.
        """
        # Delegate to main filtering/sorting method
        return self.get_filtered_and_sorted_df(df, radius, top_k, prompt)

    def reset_attributes(self):
        logger.info("Resetting PipelineOrchestrator attributes for new query")
        """
        Resets pipeline attributes for a new user query.
        """
        logger.debug("Resetting pipeline attributes for new query")
        # Reset all relevant attributes to None for a fresh query
        for attr in [
            "specialty", "institution_type", "city", "df_with_cities", "specialty_df",
            "city_not_specified", "institution_mentioned", "institution_name", "df_gen"
        ]:
            setattr(self, attr, None)

    def extract_query_parameters(self, prompt: str, detected_specialty: str = None, conv_history: list = None) -> str:
        logger.info(f"Extracting query parameters: prompt='{prompt}', detected_specialty='{detected_specialty}', conv_history='{conv_history}'")
        """
        Retrieves key aspects of the user query: city, institution type, and specialty using PromptDetectionManager.
        Updates instance variables accordingly.
        """
        logger.info(f"Getting infos from pipeline for prompt: {prompt}")
        # Get LLM model from data processor
        model = getattr(self.data_processor.llm_handler_service, 'model', None)
        # Create prompt manager for detection
        prompt_manager = PromptDetectionManager(model=model)
        # Get institution list for detection
        institution_list = self.data_processor._get_institution_list()
        # Convert conversation history to string if provided
        conv_history_str = "".join(conv_history) if conv_history else ""
        # Run all detection routines
        detections = prompt_manager.run_all_detections(prompt, conv_history=conv_history_str, institution_list=institution_list)
        # Assign detected parameters to instance variables
        self.specialty = detected_specialty if detected_specialty else detections.get('specialty')
        self.city = detections.get('city')
        logger.debug(f"[DEBUG] City detected by PromptDetectionManager: {self.city}")
        self.institution_type = detections.get('institution_type')
        self.institution_name = detections.get('institution_name')
        self.institution_mentioned = detections.get('institution_mentioned')
        self.topk = detections.get('topk')
        logger.debug(f"PipelineOrchestrator infos - specialty: {self.specialty}, city: {self.city}, institution_type: {self.institution_type}, institution: {self.institution_name}, institution_mentioned: {self.institution_mentioned}")
        logger.debug(f"[DEBUG] City value after assignment in extract_query_parameters: {self.city}")
        return self.specialty

    def build_ranking_dataframe_with_distances(self, prompt: str, excel_path: str, detected_specialty: str = None) -> pd.DataFrame:
        logger.info(f"Building ranking DataFrame with distances: prompt='{prompt}', excel_path='{excel_path}', detected_specialty='{detected_specialty}'")
        """
        Retrieves the ranking DataFrame based on the user query, including distance calculations if a city is specified.
        """
        logger.info(f"Building ranking DataFrame with distances for prompt: {prompt}")
        # Find the relevant Excel sheet and extract info
        self.df_gen = self.data_processor.find_excel_sheet_with_privacy(prompt, detected_specialty)
        # Only extract query parameters if we don't have a detected specialty
        if not detected_specialty or detected_specialty == "no specialty match":
            self.extract_query_parameters(prompt)
        else:
            self.extract_query_parameters(prompt, detected_specialty)
            self.specialty = detected_specialty
            self.data_processor.specialty = detected_specialty
        logger.debug(f"[DEBUG] City value before city validation in build_ranking_dataframe_with_distances: {self.city}")
        logger.debug(f"[DEBUG] DataProcessor city value before city validation: {self.data_processor.city}")
        # If ranking unavailable for specialty/type, return general DataFrame
        if self.data_processor.specialty_ranking_unavailable:
            logger.warning("Ranking not found for requested specialty/type")
            return self.df_gen
        # If no city found or invalid city value, return general DataFrame
        from app.config.features_config import CITY_NO_CITY_MENTIONED
        # Defensive: treat both '0' (int) and '0' (str) as no city
        if (
            self.data_processor.city is None
            or self.data_processor.city in ['aucune correspondance', 'no match', 'llm_handler_service is required for city checking.']
            or self.data_processor.city == CITY_NO_CITY_MENTIONED
            or (isinstance(self.data_processor.city, str) and self.data_processor.city.strip() == "")
            or (isinstance(self.data_processor.city, int) and self.data_processor.city == 0)
        ):
            logger.debug(f"[DEBUG] City validation failed in build_ranking_dataframe_with_distances. City value: {self.data_processor.city}")
            logger.info(f"No city found or invalid city value ('{self.data_processor.city}'), returning general ranking DataFrame")
            self.city_not_specified = True
            # Defensive: remove Distance column if present
            if 'Distance' in self.df_gen.columns:
                self.df_gen = self.df_gen.drop(columns=['Distance'])
            return self.df_gen
        # Otherwise, calculate distances for hospitals
        self.city_not_specified= False
        logger.debug(f"[DEBUG] City validation passed. Proceeding with distance calculation. City value: {self.data_processor.city}")
        logger.info("Extracting hospital locations and calculating distances")
        self.data_processor.extract_local_hospitals()
        return self.data_processor.get_df_with_distances()

    def _institution_ranking_response(self, df: pd.DataFrame, topk: int) -> str:
        logger.info(f"Generating institution ranking response for institution: {self.institution_name}")
        """Helper for institution ranking response."""
        logger.info(f"Institution mentioned in query: {self.institution_name}")
        # Check if institution is present in DataFrame
        if not df['Etablissement'].str.contains(self.institution_name).any():
            logger.warning(f"Institution {self.institution_name} not found in DataFrame")
            display_specialty, is_no_match = self._normalize_specialty_for_display(self.specialty)
            if is_no_match:
                return f"Cet établissement ne fait pas partie des {topk} meilleurs établissements du palmarès global"
            else:
                return f"Cet établissement n'est pas présent pour la pathologie {display_specialty}, vous pouvez cependant consulter le classement suivant:"
        # Find institution's position in sorted DataFrame
        df_sorted = df.sort_values(by='Note / 20', ascending=False).reset_index(drop=True)
        position = df_sorted.index[df_sorted["Etablissement"].str.contains(self.institution_name, case=False, na=False)][0] + 1
        display_specialty, is_no_match = self._normalize_specialty_for_display(self.specialty)
        response = f"{self.institution_name} est classé n°{position} "
        if is_no_match:
            response += "du palmarès général"
        else:
            response += f"du palmarès {display_specialty}."
        if self.institution_type not in ['aucune correspondance', 'no match'] and self.institution_type:
            response += f" {self.institution_type}."
        return response

    def get_filtered_and_sorted_df(self, df: pd.DataFrame, max_radius_km: int, top_k: int, prompt:str) -> str:
        logger.info(f"Filtering and sorting DataFrame: max_radius_km={max_radius_km}, top_k={top_k}, prompt={prompt}")
        """
        Filters and sorts the ranking DataFrame by distance and score, and formats the response.
        """
        logger.info(f"Filtering and sorting DataFrame with max_radius_km={max_radius_km}, top_k={top_k}, prompt={prompt}")
        # If institution is mentioned, return its ranking response
        if self.institution_mentioned:
            return self._institution_ranking_response(df, top_k)
        # Only filter by distance if city is specified and Distance column exists
        if not self.city_not_specified and "Distance" in df.columns:
            logger.debug(f"Distance column values before filtering: {df['Distance'].tolist()}")
            logger.debug(f"Rows with None in Distance before filtering: {df[df['Distance'].isnull()]}")
            filtered_df = df[df["Distance"].notnull() & (df["Distance"] <= max_radius_km)]
        else:
            # If no city, skip distance filtering
            logger.info("No city specified or Distance column missing, skipping distance filtering.")
            filtered_df = df
        # Sort by score and select top_k
        self.sorted_df = filtered_df.nlargest(top_k, "Note / 20")
        logger.debug(f"Filtered DataFrame shape: {self.sorted_df.shape}")
        # If enough results found, format and return response
        if self.sorted_df.shape[0] == top_k:
            logger.info(f"Found {top_k} results within {max_radius_km}km")
            res_str = format_response(self.sorted_df, self.city_not_specified)
            message = self._format_response_with_specialty(
                "Voici les {count} meilleurs établissements {specialty}{location}:",
                top_k, max_radius_km, self.city
            )
            return self._create_response_and_log(message, res_str, prompt)
        # If at max radius, return all found institutions
        if max_radius_km == 500:
            res_str = format_response(self.sorted_df, self.city_not_specified)
            message = self._format_response_with_specialty(
                "Voici les {count} meilleurs établissements {specialty}{location}:<br>",
                self.sorted_df.shape[0], max_radius_km, self.city
            )
            return self._create_response_and_log(message, res_str, prompt)
        # If no results found, return None
        logger.warning("No results found within current radius")
        return None

    def generate_response(self, 
        prompt: str, top_k: int = None, max_radius_km: int = 50, detected_specialty: str=None) -> str:
        """
        Main entry point: processes the user question and returns a formatted answer with ranking and links.
        """
        logger.info(f"generate_response called: prompt='{prompt}',  detected_specialty={detected_specialty}")
        logger.info(f"Starting pipeline processing - prompt: {prompt}, detected_specialty: {detected_specialty}")
        # Reset attributes for new query
        self.reset_attributes()
        self.specialty = detected_specialty
        logger.debug("Reset pipeline attributes for new query")
        # Defensive: ensure specialty is never empty or None
        if not detected_specialty or not str(detected_specialty).strip():
            detected_specialty = "no specialty match"
        # Set specialty in data processor for downstream use
        self.data_processor.specialty = detected_specialty if self.specialty is not None else None
        relevant_file = self.ranking_file_path
        # Handle multiple matches early (UI selection)
        extracted_specialty = detected_specialty if detected_specialty and detected_specialty != "no specialty match" else self.extract_query_parameters(prompt)
        if extracted_specialty and str(extracted_specialty).startswith("multiple matches:"):
            logger.info("Multiple specialty matches detected, returning for UI selection")
            specialty_list = extracted_specialty.replace("multiple matches:", "").strip()
            formatted_response = f"Plusieurs spécialités sont disponibles. Veuillez préciser laquelle vous intéresse:\n- {specialty_list.replace(',', '\n- ')}"
            logger.debug(f"Returning multiple matches response: {formatted_response}")
            return formatted_response, None
        # Build DataFrame with ranking and distances
        df = self.build_ranking_dataframe_with_distances(prompt, relevant_file, detected_specialty)
        logger.debug(f"Retrieved DataFrame shape: {df.shape if hasattr(df, 'shape') else 'N/A'}")
        # Handle geolocation API errors
        if self.data_processor.geolocation_api_error:
            logger.error("Geopy API error encountered, cannot calculate distances")
            return "Dû à une surutilisation de l'API de Geopy, le service de calcul des distances est indisponible pour le moment, merci de réessayer plus tard ou de recommencer avec une question sans localisation spécifique", None
        # Get ranking link for UI
        self.link = self.data_processor.web_ranking_link
        # Handle cases where no results are found for requested specialty/type
        if self.data_processor.specialty_ranking_unavailable:
            logger.warning("Ranking not found for requested specialty/type, suggesting alternative")
            if self.data_processor.institution_type == 'Public':
                return "Nous n'avons pas d'établissement public pour cette pathologie, mais un classement des établissements privés existe. ", self.link
            elif self.data_processor.institution_type == 'Privé':
                return "Nous n'avons pas d'établissement privé pour cette pathologie, mais un classement des établissements publics existe. ", self.link
        # If institution is mentioned, return its ranking and link
        if self.institution_mentioned:
            logger.info("Returning result for mentioned institution")
            res = self.get_filtered_and_sorted_df(df, max_radius_km, top_k, prompt)
            logger.debug(f"Result: {res}, Links: {self.link}")
            return res, self.link
        # If city found, try to find results within increasing radii
        if self.city_not_specified == False:
            logger.info("City found, searching for results within increasing radii")
            for radius in [max_radius_km, 100, 200, 500]:
                res = self._try_radius_search(df, radius, top_k, prompt)
                if res:
                    return res, self.link
            logger.warning("No results found even at maximum radius")
            return "Aucun résultat trouvé dans votre région.", self.link
        # General ranking response if no city found
        logger.info("No city found, returning general ranking")
        res_tab = self.df_gen.nlargest(top_k, "Note / 20")
        res_str = format_response(res_tab, self.city_not_specified)
        base_message = "Voici le meilleur établissement" if top_k == 1 else f"Voici les {top_k} meilleurs établissements"
        display_specialty, is_no_match = self._normalize_specialty_for_display(self.specialty)
        if is_no_match:
            res = f"{base_message}:<br> \n{res_str}"
        else:
            res = f"{base_message} pour la pathologie {display_specialty}<br> \n{res_str}"
        logger.debug(f"Result: {res}, Links: {self.link}")
        return res, self.link
