import pandas as pd
from app.services.data_processing_service import DataProcessor
from app.features.query_analysis.query_analyst import QueryAnalyst
from app.config.file_paths_config import PATHS
from app.config.features_config import (SEARCH_RADIUS_KM, ERROR_GENERAL_RANKING_MSG, ERROR_INSTITUTION_RANKING_MSG,ERROR_GEOPY_MSG, ERROR_DATA_UNAVAILABLE_MSG, ERROR_IN_CREATING_TABLE_MSG, NO_PRIVATE_INSTITUTION_MSG, NO_PUBLIC_INSTITUTION_MSG, NO_RESULTS_FOUND_IN_LOCATION_MSG)
from app.utility.logging import get_logger
from app.utility.formatting_helpers import format_response
from app.utility.distance_calc_helpers import multi_radius_search

logger = get_logger(__name__)

class PipelineOrchestrator:
    """
    Orchestrates the processing of user queries to extract hospital rankings.
    This class handles the extraction of specialties, cities, and institution types,
    retrieves relevant data from Excel files, calculates distances, and formats the final response.
    Uses the centralized number_institutionsDetector for all number_institutions related operations.
    Attributes:
        ranking_file_path (str): Path to the Excel file containing hospital rankings.
        specialty (str): The detected specialty from the user query.
        institution_type (str): The detected institution type from the user query.
        city (str): The detected city from the user query.
        df_gen (pd.DataFrame): The main DataFrame containing hospital rankings.     
        institution_mentioned (bool): Flag indicating if an institution was mentioned in the query.
        institution_name (str): The name of the institution mentioned in the query.
        data_processor (DataProcessor): Instance of DataProcessor for data extraction and transformation.       
    Methods:
        _normalize_specialty_for_display(specialty: str) -> str: Normalizes specialty format for display purposes and checks for no match.
        _format_response_with_specialty(base_message:           
            str, count: int, radius_km: int = None, city: str = None) -> str: 
            Helper method to format response messages with specialty context.
        _create_response_and_log(message: str, table_str: str, prompt: str) -> str: 
            Helper method to create final response, log it, and save to CSV.        
        _try_radius_search(df: pd.DataFrame, radius: int, number_institutions: int, prompt: str) -> str:
            Try to find results within a specific radius.
        reset_attributes(): Resets pipeline attributes for a new user query.
        extract_query_parameters(prompt: str, detected_specialty: str = None, conv_history: list = None) -> dict:
            Centralized detection: runs QueryAnalyst and sets results in DataProcessor.
        build_ranking_dataframe_with_distances(prompt: str, excel_path: str, detected_specialty: str = None, conv_history: list = None) -> pd.DataFrame:
            Retrieves the ranking DataFrame based on the user query, including distance calculations if a city is specified.
        _institution_ranking_response(df: pd.DataFrame, number_institutions: int) -> str:
            Helper for institution ranking response.
        get_filtered_and_sorted_df(df: pd.DataFrame, max_radius_km: int, number_institutions: int, prompt: str) -> str:
            Filters and sorts the ranking DataFrame by distance and score, and formats the response.
        generate_response(prompt: str, max_radius_km: int = 5, detected_specialty: str=None) -> str:
            Main entry point: processes the user question and returns a formatted answer with ranking and links.    
    """
    def __init__(self):
        logger.info("Initializing PipelineOrchestrator")
        self.ranking_file_path= PATHS["ranking_file_path"]
        self.specialty= None
        self.institution_type= None
        self.city = None
        # ...existing code...
        self.df_gen = None # DF for results 
        self.institution_mentioned=None
        self.institution_name=None
        self.data_processor=DataProcessor() # Instance of DataProcessor for data extraction and transformation


    def _normalize_specialty_for_display(self, specialty: str) -> str:
        """
        Normalize specialty format for display purposes and check for no match.
        Returns tuple: (normalized string, is_no_match)
        """
        logger.debug(f"Normalizing specialty for display: {specialty}")
        # Handle empty or no-match specialty cases
        if not specialty or specialty.lower() in ["no specialty match", "aucune correspondance", "no match", ""]:
            return "aucune correspondance", True
        # Handle multiple matches case (for UI selection)
        if specialty.startswith(("multiple matches:", "plusieurs correspondances:")):
            return specialty, False
        # Return specialty as-is for display
        return specialty, False


    def _format_response_with_specialty(self, base_message: str, count: int, radius_km: int = None, city: str = None) -> str:
        """
        Helper method to format response messages with specialty context.
        Args:
            base_message (str): The base message to format.
            count (int): The number of institutions to include in the response.
            radius_km (int, optional): The radius in kilometers for the search.
            city (str, optional): The city for the search.
        Returns:
            str: The formatted response message with specialty context. 
        """
        logger.debug(f"Formatting response with specialty: base_message='{base_message}', count={count}, radius_km={radius_km}, city={city}")
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
        """
        Helper method to create final response, log it, and save to CSV.
        Args:
            message (str): The message to include in the response.
            table_str (str): The formatted table string to include in the response.         
            prompt (str): The original user prompt.
        Returns:
            str: The final formatted response string.   
        """
        logger.info(f"Creating response and logging for prompt: {prompt}")

        # Combine message and table for final response
        response = f"{message}\n{table_str}"
        # Save response to CSV for history
        self.data_processor.create_csv(question=prompt, reponse=response)
        logger.debug(f"Formatted response: {response}")
        return response


    def _try_radius_search(self, df: pd.DataFrame, radius: int, number_institutions: int, prompt: str) -> str:
        """
        Try to find results within a specific radius.
        Args:
            df (pd.DataFrame): The DataFrame containing hospital rankings.
            radius (int): The radius in kilometers to filter results.   
            number_institutions (int): The number of institutions to return.
            prompt (str): The original user prompt.
        Returns:
            str: The formatted response string with results within the specified radius.    
        """
        logger.info(f"Trying radius search: radius={radius}, number_institutions={number_institutions}, prompt={prompt}")
        # Delegate to main filtering/sorting method
        return self.get_filtered_and_sorted_df(df, radius, number_institutions, prompt)


    def reset_attributes(self):
        """
        Resets pipeline attributes for a new user query.
        """
        logger.info("Resetting PipelineOrchestrator attributes for new query")
        # Reset all relevant attributes to None for a fresh query
        for attr in [
            "specialty", "institution_type", "city", "df_with_cities", "specialty_df",
            "city_not_specified", "institution_mentioned", "institution_name", "df_gen"
        ]:
            setattr(self, attr, None)


    def extract_query_parameters(self, prompt: str, detected_specialty: str = None, conv_history: list = None) -> dict:
        """
        Centralized detection: runs QueryAnalyst and sets results in DataProcessor.
        Returns detections dict.

        Args:
            prompt (str): The user query prompt.        
            detected_specialty (str, optional): The detected specialty from the user query.
            conv_history (list, optional): The conversation history for context.
        Returns:
            dict: A dictionary containing the results of all query parameter detections.    
        """
        logger.info(f"Extracting query parameters: prompt='{prompt}', detected_specialty='{detected_specialty}', conv_history='{conv_history}'")
        model = getattr(self.data_processor.llm_handler_service, 'model', None)
        llm_handler_service = self.data_processor.llm_handler_service
        prompt_manager = QueryAnalyst(model=model, llm_handler_service=llm_handler_service)
        institution_list = self.data_processor._get_institution_list()
        conv_history_str = "".join(conv_history) if conv_history else ""
        detections = prompt_manager.run_all_detections(prompt, conv_history=conv_history_str, institution_list=institution_list)
        logger.debug(f"Full detections dict: {detections}")
        # Set all detection results in DataProcessor
        self.data_processor.set_detection_results(
            specialty=detected_specialty if detected_specialty else detections.get('specialty'),
            city=detections.get('city'),
            city_detected=detections.get('city_detected', False),
            institution_type=detections.get('institution_type'),
            number_institutions=detections.get('number_institutions') if 'number_institutions' in detections else detections.get('number_institutions'),
            institution_name=detections.get('institution_name'),
            institution_mentioned=detections.get('institution_mentioned')
        )
        # Set orchestrator attributes for downstream use
        self.specialty = self.data_processor.specialty
        logger.debug(f"PipelineOrchestrator.specialty set to: {self.specialty!r}")
        self.city = self.data_processor.city
        logger.debug(f"PipelineOrchestrator.city set to: {self.city!r}")
        self.institution_type = self.data_processor.institution_type
        logger.debug(f"PipelineOrchestrator.institution_type set to: {self.institution_type!r}")
        self.institution_name = self.data_processor.institution_name
        logger.debug(f"PipelineOrchestrator.institution_name set to: {self.institution_name!r}")
        self.institution_mentioned = self.data_processor.institution_mentioned
        logger.debug(f"PipelineOrchestrator.institution_mentioned set to: {self.institution_mentioned!r}")
        self.number_institutions = self.data_processor.number_institutions
        logger.debug(f"PipelineOrchestrator.number_institutions set to: {self.number_institutions!r}")
        logger.debug(f"PipelineOrchestrator infos - specialty: {self.specialty}, city: {self.city}, institution_type: {self.institution_type}, institution: {self.institution_name}, institution_mentioned: {self.institution_mentioned}")
        return detections


    def build_ranking_dataframe_with_distances(self, prompt: str, excel_path: str, detected_specialty: str = None, conv_history: list = None) -> pd.DataFrame:
        """
        Retrieves the ranking DataFrame based on the user query, including distance calculations if a city is specified.
        Args:
            prompt (str): The user query prompt.    
            excel_path (str): The path to the Excel file containing hospital rankings.
            detected_specialty (str, optional): The detected specialty from the user query.
            conv_history (list, optional): The conversation history for context.
        Returns:
            pd.DataFrame: The DataFrame containing hospital rankings with distances if applicable.
        """
        logger.info(f"Building ranking DataFrame with distances: prompt='{prompt}', excel_path='{excel_path}', detected_specialty='{detected_specialty}'")
        # Centralized detection and data setup
        detections = self.extract_query_parameters(prompt, detected_specialty, conv_history)
        # Generate main DataFrame
        self.df_gen = self.data_processor.generate_data_response()
        # If ranking unavailable for specialty/type, return general DataFrame
        if self.data_processor.specialty_ranking_unavailable:
            logger.warning("Ranking not found for requested specialty/type")
            return self.df_gen
        # If no city found or invalid city value, return general DataFrame
        if not self.data_processor.city_detected:
            logger.info(f"No city detected, returning general ranking DataFrame")
            if 'Distance' in self.df_gen.columns:
                self.df_gen = self.df_gen.drop(columns=['Distance'])
            return self.df_gen
        # Otherwise, calculate distances for hospitals
        logger.info("Extracting hospital locations and calculating distances")
        self.data_processor.extract_local_hospitals()
        return self.data_processor.get_df_with_distances()


    def _institution_ranking_response(self, df: pd.DataFrame, number_institutions: int) -> str:
        """
        Helper for institution ranking response.
        Args:
            df (pd.DataFrame): The DataFrame containing hospital rankings.
            number_institutions (int): The number of institutions to return.        
        Returns:
            str: The formatted response string with the institution's ranking and details.  
        """
        logger.info(f"Institution mentioned in query: {self.institution_name}")
        # Check if institution is present in DataFrame
        if not df['Etablissement'].str.contains(self.institution_name).any():
            logger.warning(f"Institution {self.institution_name} not found in DataFrame")
            display_specialty, is_no_match = self._normalize_specialty_for_display(self.specialty)
            if is_no_match:
                return f"Cet établissement ne fait pas partie des {number_institutions} meilleurs établissements du palmarès global"
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


    def get_filtered_and_sorted_df(self, df: pd.DataFrame, max_radius_km: int, number_institutions: int, prompt:str) -> str:
        """
        Filters and sorts the ranking DataFrame by distance and score, and formats the response.
        Args:
            df (pd.DataFrame): The DataFrame containing hospital rankings.
            max_radius_km (int): The maximum radius in kilometers to filter results.
            number_institutions (int): The number of institutions to return.    
            prompt (str): The original user prompt.
        Returns:
            str: The formatted response string with the filtered and sorted results.    
        """
        logger.info(f"Filtering and sorting DataFrame with max_radius_km={max_radius_km}, number_institutions={number_institutions}, prompt={prompt}")
        # If institution is mentioned, return its ranking response
        if self.institution_mentioned:
            return self._institution_ranking_response(df, self.number_institutions)
        # Only filter by distance if city is detected and Distance column exists
        if self.data_processor.city_detected and "Distance" in df.columns:
            df = df.copy()
            df["Distance"] = pd.to_numeric(df["Distance"], errors="coerce")
            logger.info(f"[RadiusFilter] Initial DataFrame shape: {df.shape}")
            logger.info(f"[RadiusFilter] Distance column values before dropna: {df['Distance'].tolist()}")
            # Drop rows with NaN in Distance
            filtered_df = df.dropna(subset=["Distance"]).reset_index(drop=True)
            logger.info(f"[RadiusFilter] DataFrame shape after dropna on Distance: {filtered_df.shape}")
            logger.info(f"[RadiusFilter] Distance values after dropna: {filtered_df['Distance'].tolist()}")
            if max_radius_km is not None:
                logger.info(f"[RadiusFilter] Applying radius filter: max_radius_km={max_radius_km}")
                filtered_df = filtered_df[filtered_df["Distance"] <= max_radius_km].reset_index(drop=True)
                logger.info(f"[RadiusFilter] DataFrame shape after radius filter: {filtered_df.shape}")
                logger.info(f"[RadiusFilter] Distance values after radius filter: {filtered_df['Distance'].tolist()}")
        else:
            # If no city, skip distance filtering
            logger.info("No city specified or Distance column missing, skipping distance filtering.")
            filtered_df = df
        # Only filter and format the DataFrame(s) for the institution type(s) requested by the user
        institution_type = self.institution_type
        public_df = None
        private_df = None
        if institution_type == 'Public':
            public_df = filtered_df[filtered_df["Catégorie"] == "Public"].nlargest(number_institutions, "Note / 20")
            logger.debug(f"Filtered public_df shape: {public_df.shape}")
            res_str = format_response(public_df, None, number_institutions, self.city_not_specified)
        elif institution_type == 'Privé':
            private_df = filtered_df[filtered_df["Catégorie"] == "Privé"].nlargest(number_institutions, "Note / 20")
            logger.debug(f"Filtered private_df shape: {private_df.shape}")
            res_str = format_response(None, private_df, number_institutions, self.city_not_specified)
        else:
            public_df = filtered_df[filtered_df["Catégorie"] == "Public"].nlargest(number_institutions, "Note / 20")
            private_df = filtered_df[filtered_df["Catégorie"] == "Privé"].nlargest(number_institutions, "Note / 20")
            logger.debug(f"Filtered public_df shape: {public_df.shape}, private_df shape: {private_df.shape}")
            res_str = format_response(public_df, private_df, number_institutions, self.city_not_specified)
        message = self._format_response_with_specialty(
            "Voici les meilleurs établissements :",
            number_institutions, max_radius_km, self.city
        )
        return self._create_response_and_log(message, res_str, prompt)

    def generate_response(self, prompt: str, max_radius_km: int = 5, detected_specialty: str=None) -> str:
        """
        Main entry point: processes the user question and returns a formatted answer with ranking and links.
        Args:       
            prompt (str): The user query prompt.    
            max_radius_km (int, optional): The maximum radius in kilometers to filter results.
            detected_specialty (str, optional): The detected specialty from the user query.         
        Returns:
            str: The formatted response string with the hospital rankings and links.    
        """
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
        logger.debug("Calling build_ranking_dataframe_with_distances")
        try:
            df = self.build_ranking_dataframe_with_distances(prompt, relevant_file, detected_specialty)
            logger.debug(f"build_ranking_dataframe_with_distances returned DataFrame: {type(df)}")
        except Exception as e:
            logger.exception(f"Exception in build_ranking_dataframe_with_distances: {e}")
            return ERROR_IN_CREATING_TABLE_MSG, None

        # Check if DataFrame is None and return error message if so
        logger.debug("Checking if DataFrame is None")
        if df is None:
            logger.error("build_ranking_dataframe_with_distances returned None. Aborting response generation.")
            return ERROR_DATA_UNAVAILABLE_MSG, None
        logger.debug(f"Retrieved DataFrame shape: {df.shape if hasattr(df, 'shape') else 'N/A'}")

        # Handle geolocation API errors
        logger.debug("Checking for geolocation API errors")
        if self.data_processor.geolocation_api_error:
            logger.error("Geopy API error encountered, cannot calculate distances")
            return ERROR_GEOPY_MSG, None

        # Get ranking link for UI
        logger.debug("Getting ranking link for UI")
        self.link = self.data_processor.web_ranking_link

        # Handle cases where no results are found for requested specialty/type
        logger.debug("Checking for specialty_ranking_unavailable")
        if self.data_processor.specialty_ranking_unavailable:
            logger.warning("Ranking not found for requested specialty/type, suggesting alternative")
            if self.data_processor.institution_type == 'Public':
                logger.debug("No public institution for this specialty")
                return NO_PUBLIC_INSTITUTION_MSG, self.link
            elif self.data_processor.institution_type == 'Privé':
                logger.debug("No private institution for this specialty")
                return NO_PRIVATE_INSTITUTION_MSG, self.link

        # If institution is mentioned, return its ranking and link
        logger.debug("Checking if institution is mentioned")
        if self.institution_mentioned:
            logger.info("Returning result for mentioned institution")
            try:
                res = self.get_filtered_and_sorted_df(df, max_radius_km, self.number_institutions, prompt)
                logger.debug(f"Result from get_filtered_and_sorted_df: {res}, Links: {self.link}")
            except Exception as e:
                logger.exception(f"Exception in get_filtered_and_sorted_df: {e}")
                return ERROR_INSTITUTION_RANKING_MSG, self.link
            return res, self.link

        # If city found and Distance column exists, use multi-radius search utility to get enough results
        logger.debug("Checking if city is detected")
        if self.data_processor.city_detected and "Distance" in df.columns:
            logger.info("City found, searching for results using multi-radius search")
            # Prepare DataFrame for public/private split
            df = df.copy()
            df["Distance"] = pd.to_numeric(df["Distance"], errors="coerce")
            filtered_df = df.dropna(subset=["Distance"]).reset_index(drop=True)
            public_df = filtered_df[filtered_df["Catégorie"] == "Public"].nlargest(self.number_institutions, "Note / 20")
            private_df = filtered_df[filtered_df["Catégorie"] == "Privé"].nlargest(self.number_institutions, "Note / 20")
            # Use multi_radius_search to get enough results
            filtered_public_df, filtered_private_df, used_radius = multi_radius_search(public_df, private_df, self.number_institutions, self.city_detected, radii=SEARCH_RADIUS_KM)
            
            # If no results at all, return not found message
            if (filtered_public_df is None or filtered_public_df.empty) and (filtered_private_df is None or filtered_private_df.empty):
                logger.warning("No results found even at maximum radius (multi_radius_search)")
                return NO_RESULTS_FOUND_IN_LOCATION_MSG, self.link
            institution_type = getattr(self, 'institution_type', None)
            if institution_type == 'Public':
                res_str = format_response(filtered_public_df, None, self.number_institutions, not self.data_processor.city_detected)
            elif institution_type == 'Privé':
                res_str = format_response(None, filtered_private_df, self.number_institutions, not self.data_processor.city_detected)
            else:
                res_str = format_response(filtered_public_df, filtered_private_df, self.number_institutions, not self.data_processor.city_detected)
            message = self._format_response_with_specialty(
                f"Voici les meilleurs établissements (rayon utilisé : {used_radius} km)",
                self.number_institutions, used_radius, self.city
            )
            return self._create_response_and_log(message, res_str, prompt), self.link

        # General ranking response if no city found
        logger.info("No city detected, returning general ranking")
        try:
            if 'Distance' in self.df_gen.columns:
                logger.debug("Dropping Distance column from df_gen")
                self.df_gen = self.df_gen.drop(columns=['Distance'])
            public_df = self.df_gen[self.df_gen["Catégorie"] == "Public"].nlargest(self.number_institutions, "Note / 20")
            private_df = self.df_gen[self.df_gen["Catégorie"] == "Privé"].nlargest(self.number_institutions, "Note / 20")
            res_str = format_response(public_df, private_df, self.number_institutions, not self.data_processor.city_detected)
            logger.debug(f"Formatted response string: {res_str}")
            base_message = "Voici le meilleur établissement" if self.number_institutions == 1 else f"Voici les {self.number_institutions} meilleurs établissements"
            display_specialty, is_no_match = self._normalize_specialty_for_display(self.specialty)
            logger.debug(f"Display specialty: {display_specialty}, is_no_match: {is_no_match}")
            if is_no_match:
                res = f"{base_message}:<br> \n{res_str}"
            else:
                res = f"{base_message} pour la pathologie {display_specialty}<br> \n{res_str}"
            logger.debug(f"Result: {res}, Links: {self.link}")
            return res, self.link
        except Exception as e:
            logger.exception(f"Exception in general ranking response: {e}")
            return ERROR_GENERAL_RANKING_MSG, self.link
