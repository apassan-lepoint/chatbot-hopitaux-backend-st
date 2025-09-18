""" 
pipeline_orchestrator_service.py
---------------------------------
This file contains the PipelineOrchestrator class which orchestrates the processing of user queries related to hospital rankings.
"""

from datetime import datetime
import pandas as pd
import unicodedata
from uuid import uuid4
from app.config.features_config import (SEARCH_RADIUS_KM, NON_ERROR_MESSAGES, ERROR_MESSAGES, METHODOLOGY_WEB_LINK)
from app.config.file_paths_config import PATHS
from app.features.query_analysis.query_analyst import QueryAnalyst
from app.features.sanity_checks.conversation_limit_check import ConversationLimitCheckException
from app.features.sanity_checks.message_length_check import MessageLengthCheckException
from app.features.sanity_checks.message_pertinence_check import MessagePertinenceCheckException
from app.features.sanity_checks.sanity_checks_analyst import SanityChecksAnalyst
from app.services.data_processing_service import DataProcessor
from app.utility.logging import get_logger
from app.utility.formatting_helpers import format_response, extract_links_from_text

logger = get_logger(__name__)

class PipelineOrchestrator:
    """
    Orchestrates the processing of user queries related to hospital rankings.
    Attributes:
        ranking_file_path (str): Path to the hospital ranking Excel file.
        specialty (str): The medical specialty detected from the user query.
        institution_type (str): The type of institution (e.g., public, private) detected from the user query.
        city (str): The city detected from the user query.
        city_detected (bool): Flag indicating if a city was detected in the user query.
        df_gen (pd.DataFrame): The DataFrame containing hospital rankings.
        number_institutions (int): The number of institutions to return based on the user query.
        institution_name_mentioned (str): The name of the institution mentioned in the user query, if any.
        institution_names (list): List of institution names detected in the user query.
        data_processor (DataProcessor): Instance of DataProcessor for data extraction and transformation.
        sanity_checks_analyst (SanityChecksAnalyst): Instance of SanityChecksAnalyst for performing sanity checks on queries.
        query_analyst_results (dict): Results from the QueryAnalyst containing detected parameters from the user query.
        link (list): List of hyperlinks extracted from the response text.       
    Methods:    
        __init__: Initializes the PipelineOrchestrator with default values and instances of helper classes.
        extract_query_parameters: Extracts parameters from the user query using QueryAnalyst and sets them in DataProcessor.
        build_ranking_dataframe_with_distances: Builds the ranking DataFrame, including distance calculations if a city is specified.
        get_filtered_and_sorted_df: Filters and sorts the ranking DataFrame by distance and score, and formats the response.
        compare_institutions: Compares multiple institutions based on their rankings and formats the comparison response.
        reset_attributes: Resets the orchestrator's attributes for a new user query.
        _normalize_specialty_for_display: Normalizes specialty format for display purposes and checks for no match.
        _format_response_with_specialty: Formats response messages with specialty context.
        _create_response_and_log: Creates final response, logs it, and saves to CSV.
        _try_radius_search: Tries to find results within a specific radius.
        _institution_ranking_response: Helper for institution ranking response.
        sum_keys_with_substring: Sums values in a dictionary where keys contain a specific substring.
        _normalize_str: Normalizes a string for comparison by lowercasing, stripping, and removing accents.
        get_costs_and_tokens: Aggregates costs and token usage from various analysts.
        build_comparison_dataframe: Builds a DataFrame for comparing multiple institutions.
        handle_sanity_check_exceptions: Handles exceptions from sanity checks and formats error responses.
        run_sanity_checks: Runs sanity checks on the user query using SanityChecksAnalyst.
    """
    def __init__(self):
        logger.info("Initializing PipelineOrchestrator")
        self.ranking_file_path= PATHS["ranking_file_path"]
        self.specialty= None
        self.institution_type= None
        self.city = None
        self.city_detected = False  # Flag to indicate if a city was detected
        self.df_gen = None # DF for results 
        self.number_institutions = 3 # Default number of institutions to return
        self.institution_name_mentioned=None
        self.institution_names=[]
        self.data_processor=DataProcessor() # Instance of DataProcessor for data extraction and transformation
        self.sanity_checks_analyst_results = SanityChecksAnalyst(self.data_processor.llm_handler_service)
        self.query_analyst_results = None
        self.link = []


    def _normalize_specialty_for_display(self, specialty: str) -> str:
        """
        Normalize specialty format for display purposes and check for no match.
        Returns tuple: (normalized string, is_no_match)
        """
        logger.debug(f"Normalizing specialty for display: {specialty}")
        # Handle empty or no-match specialty cases
        if not specialty or specialty in ["no specialty match", "aucune correspondance", "no match", ""]:
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


    def _create_response_and_log(self, message: str, table_str: str, prompt: str, ranking_link: str = None, conversation_analyst_results=None) -> str:
        """
        Helper method to create final response, log it, and save to CSV.
        Args:
            message (str): The message to include in the response.
            table_str (str): The formatted table string to include in the response.         
            prompt (str): The original user prompt.
            ranking_link (str, optional): The hyperlink to include in the response.
        Returns:
            str: The final formatted response string.   
        """
        logger.info(f"Creating response and logging for prompt: {prompt}")

        # Combine message and table for final response
        response = f"{message}\n{table_str}"
        if ranking_link:
            response += f"\n\n🔗 Consultez la méthodologie de palmarès hopitaux <a href=\"{ranking_link}\" target=\"_blank\">ici</a>."
        # Aggregate costs and tokens
        aggregation = self.get_costs_and_tokens(getattr(self, 'sanity_checks_analyst_result', None), getattr(self, 'query_analyst_results', None), conversation_analyst_results=None)
        logger.info(f"Final cost/token usage aggregation: {aggregation}")
        logger.info(f"Detected variables: specialty={self.specialty}, city={self.city}, institution_type={self.institution_type}, institution_names={self.institution_names}, number_institutions={self.number_institutions}")

        csv_data = {
            'uuid': str(uuid4()),
            'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'question': prompt,
            'response': response,
            'conversation_list': conversation_analyst_results.get('conversation', []) if conversation_analyst_results else [],
            'city': self.data_processor.city,
            'institution_type': self.data_processor.institution_type,
            'institution_names': self.data_processor.institution_names,
            'specialty': self.data_processor.specialty,
            'number_institutions': self.data_processor.number_institutions,
            'total_cost_sanity_checks': aggregation.get('total_cost_sanity_checks_analyst'),
            'total_cost_query_analyst': aggregation.get('total_cost_query_analyst'),
            'total_cost_conversation_analyst': aggregation.get('total_cost_conversation_analyst'),
            'total_cost': aggregation.get('total_cost'),
            'total_tokens_sanity_checks': aggregation.get('total_token_usage_sanity_checks_analyst'),
            'total_tokens_query_analyst': aggregation.get('total_token_usage_query_analyst'),
            'total_tokens_conversation_analyst': aggregation.get('total_token_usage_conversation_analyst'),
            'total_tokens': aggregation.get('total_token_usage')
        }
        self.data_processor.create_csv(result_data=csv_data)
        logger.debug(f"Formatted response: {response}")
        self.link = extract_links_from_text(response)
        return response, self.link


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
            "city_not_specified", "institution_name_mentioned", "institution_names", "df_gen"
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
        
        # Setup QueryAnalyst
        model = getattr(self.data_processor.llm_handler_service, 'model', None)
        llm_handler_service = self.data_processor.llm_handler_service
        prompt_manager = QueryAnalyst(model=model, llm_handler_service=llm_handler_service)

        # Prepare institution list + history
        institution_list = self.data_processor._get_institution_list()
        conv_history_str = "".join(conv_history) if conv_history else ""

        # Run all detections
        detections = prompt_manager.run_all_detections(prompt, conv_history=conv_history_str, institution_list=institution_list)
        self.query_analyst_results = detections
        logger.debug(f"Full detections dict: {detections}")

        # Only use a valid specialty for assignment
        invalid_specialties = ["no match", "no specialty match", "aucune correspondance", ""]
        specialty_to_set = None
        # Prefer detected_specialty if valid
        if detected_specialty and detected_specialty not in invalid_specialties:
            specialty_to_set = detected_specialty
        elif detections.get('specialty') and detections.get('specialty') not in invalid_specialties:
            specialty_to_set = detections.get('specialty')
        # Otherwise, keep existing value (do not overwrite)
        self.data_processor.set_detection_results(
            specialty=specialty_to_set,
            city=detections.get('city'),
            city_detected=detections.get('city_detected', False),
            institution_type=detections.get('institution_type'),
            number_institutions=detections.get('number_institutions') if 'number_institutions' in detections else detections.get('number_institutions'),
            # institution_names=detections.get('institution_names'),
            institution_name_mentioned=detections.get('institution_name_mentioned'),
            institution_names=detections.get('institution_names', []),
            institution_names_intent=detections.get('institution_names_intent', "none"))
        
        # Set orchestrator attributes for downstream use
        self.specialty = self.data_processor.specialty
        logger.debug(f"PipelineOrchestrator.specialty set to: {self.specialty!r}")
        self.city = self.data_processor.city
        logger.debug(f"PipelineOrchestrator.city set to: {self.city!r}")
        self.city_detected = self.data_processor.city_detected
        logger.debug(f"PipelineOrchestrator.city_detected set to: {self.city_detected!r}")
        self.institution_type = self.data_processor.institution_type
        logger.debug(f"PipelineOrchestrator.institution_type set to: {self.institution_type!r}")
        self.institution_names = self.data_processor.institution_names
        self.institution_name_mentioned = self.data_processor.institution_name_mentioned
        # self.institution_names_with_types = self.data_processor.institution_names_with_types
        self.institution_names_intent = self.data_processor.institution_names_intent
        logger.debug(f"PipelineOrchestrator.institution_names set to: {self.institution_names!r}")
        self.institution_name_mentioned = self.data_processor.institution_name_mentioned
        logger.debug(f"PipelineOrchestrator.institution_name_mentioned set to: {self.institution_name_mentioned!r}")
        self.number_institutions = self.data_processor.number_institutions
        logger.debug(f"PipelineOrchestrator.number_institutions set to: {self.number_institutions!r}")
        logger.debug(f"PipelineOrchestrator infos - specialty: {self.specialty}, city: {self.city}, institution_type: {self.institution_type}, institution: {self.institution_names}, institution_name_mentioned: {self.institution_name_mentioned}")
        return detections


    def _normalize_str(self, s: str) -> str:
        """
        Normalize a string for comparison: lowercase, strip, remove accents.
        """
        if not isinstance(s, str):
            return s
        s = s.strip().lower()
        s = unicodedata.normalize('NFD', s)
        s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
        return s

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
        logger.info(f"Detected variables: specialty={self.specialty}, city={self.city}, institution_type={self.institution_type}, institution_names={self.institution_names}, number_institutions={self.number_institutions}")
        # Generate main DataFrame
        self.df_gen = self.data_processor.generate_data_response()
        # Add normalized specialty column for robust filtering
        if self.df_gen is not None and 'Spécialité' in self.df_gen.columns:
            self.df_gen['__norm_specialty__'] = self.df_gen['Spécialité'].apply(self._normalize_str)
            norm_specialty = self._normalize_str(self.specialty)
            logger.debug(f"[DEBUG] All normalized specialties: {self.df_gen['__norm_specialty__'].unique()}")
            logger.debug(f"[DEBUG] Normalized search specialty: {norm_specialty}")
            specialty_matches = self.df_gen[self.df_gen['__norm_specialty__'] == norm_specialty]
            logger.debug(f"[DEBUG] Specialty match count: {specialty_matches.shape[0]}")
            if specialty_matches is not None:
                logger.debug(f"[DEBUG] Specialty match rows: {specialty_matches}")
            # If we have matches, filter df_gen to only those rows
            if specialty_matches.shape[0] > 0:
                self.df_gen = specialty_matches.drop(columns=['__norm_specialty__'])
            else:
                self.df_gen = self.df_gen.drop(columns=['__norm_specialty__'])
        # Debug: Log unique specialties and institution types in the loaded DataFrame
        if self.df_gen is not None and 'Spécialité' in self.df_gen.columns:
            logger.debug(f"[DEBUG] Unique specialties in DataFrame: {self.df_gen['Spécialité'].unique()}")
            logger.debug(f"[DEBUG] Unique institution types in DataFrame: {self.df_gen['Catégorie'].unique() if 'Catégorie' in self.df_gen.columns else 'N/A'}")
            logger.debug(f"[DEBUG] DataFrame columns: {self.df_gen.columns}")
            logger.debug(f"[DEBUG] DataFrame head: {self.df_gen.head(10)}")
            logger.debug(f"[DEBUG] Filtering for specialty: '{self.specialty}' and city: '{self.city}'")
            # Normalize specialties for robust matching
            norm_specialty = self._normalize_str(self.specialty)
            self.df_gen['__norm_specialty__'] = self.df_gen['Spécialité'].apply(self._normalize_str)
            specialty_matches = self.df_gen[self.df_gen['__norm_specialty__'] == norm_specialty]
            logger.debug(f"[DEBUG] Specialty match count: {specialty_matches.shape[0]}")
            if specialty_matches is not None:
                logger.debug(f"[DEBUG] Specialty match rows: {specialty_matches}")
            if self.city and 'Ville' in self.df_gen.columns:
                city_matches = self.df_gen[self.df_gen['Ville'] == self.city]
                logger.debug(f"[DEBUG] City match count: {city_matches.shape[0]}")
                if city_matches is not None:
                    logger.debug(f"[DEBUG] City match rows: {city_matches}")
            # If we have matches, filter df_gen to only those rows
            if specialty_matches.shape[0] > 0:
                self.df_gen = specialty_matches.drop(columns=['__norm_specialty__'])
            else:
                self.df_gen = self.df_gen.drop(columns=['__norm_specialty__'])
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
        logger.info(f"Institution mentioned in query: {self.institution_names}")
        # Extract the institution name string for matching
        if isinstance(self.institution_names, list) and self.institution_names:
            inst_name = getattr(self.institution_names[0], 'name', str(self.institution_names[0]))
        else:
            inst_name = str(self.institution_names)
        # Check if institution is present in DataFrame (literal match)
        if not df['Etablissement'].str.contains(inst_name, case=False, na=False, regex=False).any():
            logger.warning(f"Institution {inst_name} not found in DataFrame")
            display_specialty, is_no_match = self._normalize_specialty_for_display(self.specialty)
            if is_no_match:
                return f"Cet établissement ne fait pas partie des {number_institutions} meilleurs établissements du palmarès global"
            else:
                return f"Cet établissement n'est pas présent pour la pathologie {display_specialty}, vous pouvez cependant consulter le classement suivant:"
        # Find institution's position in sorted DataFrame (literal match)
        df_sorted = df.sort_values(by='Note / 20', ascending=False).reset_index(drop=True)
        match_idx = df_sorted["Etablissement"].str.contains(inst_name, case=False, na=False, regex=False)
        position = df_sorted.index[match_idx][0] + 1
        note = df_sorted.loc[match_idx, 'Note / 20'].values[0] if 'Note / 20' in df_sorted.columns else None
        display_specialty, is_no_match = self._normalize_specialty_for_display(self.specialty)
        response = f"{inst_name} est classé n°{position}"
        if note is not None:
            response += f" avec une note de {note:.2f}/20"
        response += " "
        if is_no_match:
            response += "du palmarès général"
        else:
            response += f"du palmarès {display_specialty}."
        if self.institution_type not in ['aucune correspondance', 'no match'] and self.institution_type:
            response += f" {self.institution_type}."
        self.link = extract_links_from_text(response)
        return response, self.link


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
        if self.institution_name_mentioned:
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
            logger.debug(f"[DEBUG] Filtering for specialty: '{self.specialty}' and city: '{self.city}' in filtered_df")
            if 'Spécialité' in filtered_df.columns:
                specialty_matches = filtered_df[filtered_df['Spécialité'] == self.specialty]
                logger.debug(f"[DEBUG] Specialty match count after radius filter: {specialty_matches.shape[0]}")
                logger.debug(f"[DEBUG] Specialty match rows after radius filter: {specialty_matches}")
            if self.city and 'Ville' in filtered_df.columns:
                city_matches = filtered_df[filtered_df['Ville'].str.lower().str.strip() == str(self.city).lower().strip()]
                logger.debug(f"[DEBUG] City match count after radius filter: {city_matches.shape[0]}")
                logger.debug(f"[DEBUG] City match rows after radius filter: {city_matches}")
        else:
            # If no city, skip distance filtering
            logger.info("No city specified or Distance column missing, skipping distance filtering.")
            filtered_df = df
            logger.debug(f"[DEBUG] Filtering for specialty: '{self.specialty}' and city: '{self.city}' in unfiltered_df")
            if 'Spécialité' in filtered_df.columns:
                specialty_matches = filtered_df[filtered_df['Spécialité'].str.lower().str.strip() == str(self.specialty).lower().strip()]
                logger.debug(f"[DEBUG] Specialty match count in unfiltered_df: {specialty_matches.shape[0]}")
                logger.debug(f"[DEBUG] Specialty match rows in unfiltered_df: {specialty_matches}")
            if self.city and 'Ville' in filtered_df.columns:
                city_matches = filtered_df[filtered_df['Ville'].str.lower().str.strip() == str(self.city).lower().strip()]
                logger.debug(f"[DEBUG] City match count in unfiltered_df: {city_matches.shape[0]}")
                logger.debug(f"[DEBUG] City match rows in unfiltered_df: {city_matches}")
        # Only filter and format the DataFrame(s) for the institution type(s) requested by the user
        institution_type = self.institution_type
        public_df = None
        private_df = None
        # Enhanced debug logging for specialty/city filtering in public/private DataFrames
        logger.debug(f"[FILTER] Institution type requested: {institution_type}")
        logger.debug(f"[FILTER] Specialty: '{self.specialty}', City: '{self.city}'")
        if 'Spécialité' in filtered_df.columns and 'Ville' in filtered_df.columns:
            # Public filtering (accent-insensitive)
            public_raw = filtered_df[filtered_df["Catégorie"] == "Public"]
            public_specialty = public_raw[
                public_raw['Spécialité'] == self.specialty
            ]
            public_city = public_specialty[
                public_specialty['Ville'] == self.city
            ]
            logger.debug(f"[FILTER] Public: raw count={public_raw.shape[0]}, specialty count={public_specialty.shape[0]}, city+specialty count={public_city.shape[0]}")
            logger.debug(f"[FILTER] Public: specialty match rows: {public_specialty}")
            logger.debug(f"[FILTER] Public: city+specialty match rows: {public_city}")
            # Log the actual rows and their distance for public_city
            if not public_city.empty:
               logger.debug(f"[RESULT] Public city+specialty match rows (head): {public_city.head(10)}")
               logger.debug(f"[RESULT] Public city+specialty match distances: {public_city['Distance'].tolist() if 'Distance' in public_city.columns else 'N/A'}")
            else:
               logger.debug("[RESULT] No public city+specialty match rows found.")
            # Private filtering (accent-insensitive)
            private_raw = filtered_df[filtered_df["Catégorie"] == "Privé"]
            private_specialty = private_raw[
                private_raw['Spécialité'] == self.specialty
            ]
            private_city = private_specialty[
                private_specialty['Ville'] == self.city
            ]
            logger.debug(f"[FILTER] Private: raw count={private_raw.shape[0]}, specialty count={private_specialty.shape[0]}, city+specialty count={private_city.shape[0]}")
            logger.debug(f"[FILTER] Private: specialty match rows: {private_specialty}")
            logger.debug(f"[FILTER] Private: city+specialty match rows: {private_city}")
            # Log the actual rows and their distance for private_city
            if not private_city.empty:
               logger.debug(f"[RESULT] Private city+specialty match rows (head): {private_city.head(10)}")
               logger.debug(f"[RESULT] Private city+specialty match distances: {private_city['Distance'].tolist() if 'Distance' in private_city.columns else 'N/A'}")
            else:
               logger.debug("[RESULT] No private city+specialty match rows found.")
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
        return self._create_response_and_log(message, res_str, prompt, METHODOLOGY_WEB_LINK)

    def sum_keys_with_substring(self, d, substr):
        if not isinstance(d, dict):
            return 0.0
        return sum(
            v if isinstance(v, (int, float)) else 0
            for k, v in d.items() if substr in k
        )
    
    def compare_institutions(self, institution_names: list, prompt: str, mode: str = "implicit") -> str:
        """
        Build a comparison response for multiple institutions using only canonical (full) names, ranking them by score and noting the best.
        Args:
            institution_names (List[HospitalInfo or str]): The canonical names or HospitalInfo objects of the institutions to compare.
            prompt (str): The original user query.
            mode (str): 'explicit' if the user explicitly asked for comparison.
        Returns:
            str: Formatted comparison result string.
        """
        logger.info(f"Building comparison for canonical institution names: {institution_names}, mode={mode}")

        # Always extract .name if present (for HospitalInfo), else use as string
        canonical_names = [getattr(i, 'name', i) for i in institution_names]

        try:
            df = self.build_ranking_dataframe_with_distances(prompt, self.ranking_file_path, self.specialty)
            logger.info(f"[compare_institutions] DataFrame columns at start: {df.columns.tolist() if hasattr(df, 'columns') else 'N/A'}")
            # Only filter using canonical (full/original) names
            df_filtered = df[df["Etablissement"].isin(canonical_names)]
            logger.info(f"[compare_institutions] DataFrame columns after filtering: {df_filtered.columns.tolist()}")
            found_names = set(df_filtered["Etablissement"]) if not df_filtered.empty else set()
            not_found = [name for name in canonical_names if name not in found_names]
            logger.debug(f"compare_institutions: df_filtered shape: {df_filtered.shape}, columns: {df_filtered.columns.tolist()}, head: {df_filtered.head()}")
            message_extra = ""
            if not_found:
                message_extra = ("<br><b>Note :</b> Les établissements suivants ne figurent pas dans le classement pour la pathologie ou le contexte demandé, "
                                 "mais peuvent être présents dans d'autres classements/pathologies :<br>- " + "<br>- ".join(not_found) +
                                 "<br>Leur classement ne peut donc pas être comparé ici.")
            if df_filtered.empty:
                logger.info(f"[compare_institutions] df_filtered is empty. Columns: {df_filtered.columns.tolist()}")
                return f"Aucun classement trouvé pour les établissements mentionnés: {', '.join(canonical_names)}" + message_extra

            # Sort by score descending
            if "Note / 20" in df_filtered.columns:
                df_sorted = df_filtered.sort_values(by="Note / 20", ascending=False)
            else:
                df_sorted = df_filtered
            logger.info(f"[compare_institutions] DataFrame columns after sorting: {df_sorted.columns.tolist()}")

            # Ensure 'Spécialité' column exists for link generation if possible
            if "Spécialité" not in df_sorted.columns and self.specialty:
                df_sorted["Spécialité"] = self.specialty
            # Build comparison string (reuse format_response if possible, else custom)
            res_str = format_response(
                df_sorted[df_sorted["Catégorie"] == "Public"],
                df_sorted[df_sorted["Catégorie"] == "Privé"],
                len(canonical_names),
                not self.city_detected
            )

            # Add note about the best institution
            best_row = df_sorted.iloc[0] if not df_sorted.empty else None
            best_note = ""
            if best_row is not None:
                best_note = (f"<br><b>L'établissement le mieux classé est :</b> {best_row['Etablissement']}.")

            # Generate and append ranking links for both public and private
            links = self.data_processor.generate_response_links(df_sorted)
            from app.utility.formatting_helpers import format_links
            res_str = format_links(res_str, links)

            comparison_msg = "Comparaison explicite" if mode == "explicit" else "Comparaison des établissements mentionnés"
            return self._create_response_and_log(comparison_msg, res_str + best_note + message_extra, prompt, METHODOLOGY_WEB_LINK)
        except Exception as e:
            logger.exception(f"Exception in compare_institutions: {e}")
            return "Erreur lors de la comparaison des établissements."

    def get_costs_and_tokens(self, sanity_checks_results, query_analyst_results, conversation_analyst_results=None):
        """
        Aggregate total costs and token usage from sanity checks, query analyst, and conversation analyst.
        Returns only total variables for each step and overall.
        """
        logger.debug(f"Sanity check results for costs/tokens aggregation: {sanity_checks_results}")
        logger.debug(f"Query analyst results for costs/tokens aggregation: {query_analyst_results}")
        logger.debug(f"Conversation analyst results for costs/tokens aggregation: {conversation_analyst_results}")
        
        total_cost_sanity_checks_analyst = self.sum_keys_with_substring(sanity_checks_results, 'cost') if sanity_checks_results is not None else 0.0
        total_token_usage_sanity_checks_analyst = self.sum_keys_with_substring(sanity_checks_results, 'tokens') if sanity_checks_results is not None else 0

        total_cost_query_analyst = self.sum_keys_with_substring(query_analyst_results, 'cost') if query_analyst_results is not None else 0.0
        total_token_usage_query_analyst = self.sum_keys_with_substring(query_analyst_results, 'tokens') if query_analyst_results is not None else 0

        total_cost_conversation_analyst = self.sum_keys_with_substring(conversation_analyst_results, 'cost') if conversation_analyst_results is not None else 0.0
        total_token_usage_conversation_analyst = self.sum_keys_with_substring(conversation_analyst_results, 'tokens') if conversation_analyst_results is not None else 0

        total_cost = total_cost_sanity_checks_analyst + total_cost_query_analyst + total_cost_conversation_analyst
        total_token_usage = total_token_usage_sanity_checks_analyst + total_token_usage_query_analyst + total_token_usage_conversation_analyst
        costs_token_usage_dict = {
            'total_cost_sanity_checks_analyst': total_cost_sanity_checks_analyst,
            'total_cost_query_analyst': total_cost_query_analyst,
            'total_cost_conversation_analyst': total_cost_conversation_analyst,
            'total_cost': total_cost,
            'total_token_usage_sanity_checks_analyst': total_token_usage_sanity_checks_analyst,
            'total_token_usage_query_analyst': total_token_usage_query_analyst,
            'total_token_usage_conversation_analyst': total_token_usage_conversation_analyst,
            'total_token_usage': total_token_usage
        }
        logger.info(f"Aggregated costs and token usage: {costs_token_usage_dict}")

        return costs_token_usage_dict

    def generate_response(self, prompt: str, max_radius_km: int = 5, conversation=None, conv_history=None, selected_specialty=None) -> str:
        """
        Main entry point: processes the user question and returns a formatted answer with ranking and links.
        Args:       
            prompt (str): The user query prompt.    
            max_radius_km (int, optional): The maximum radius in kilometers to filter results.
            selected_specialty (str, optional): The specialty selected by the user after multiple matches.
        Returns:
            str: The formatted response string with the hospital rankings and links.    
        """
        logger.info(f"Starting pipeline processing - prompt: {prompt}")
        # Reset attributes for new query
        self.reset_attributes()
        relevant_file = self.ranking_file_path
        # Run sanity checks before any further processing
        if conversation is None:
            conversation = []
        if conv_history is None:
            conv_history = ""
        try:
            logger.info(f"Running sanity checks for prompt: {prompt}, conversation: {conversation}, conv_history: {conv_history}")
            sanity_result = self.sanity_checks_analyst_results.run_checks(prompt, conversation, conv_history)
            logger.info(f"Sanity checks result: {sanity_result}")
            self.sanity_checks_analyst_result = sanity_result
        except Exception as exc:
            if isinstance(exc, (MessagePertinenceCheckException, MessageLengthCheckException, ConversationLimitCheckException)):
                error_msg = str(exc)
            else:
                error_msg = getattr(exc, 'message', str(exc))
            aggregation = self.get_costs_and_tokens(getattr(self, 'sanity_checks_analyst_result', None), None, None) if 'sanity_result' in locals() and isinstance(sanity_result, dict) else {}
            logger.info(f"Final cost/token usage aggregation: {aggregation}")
            logger.info(f"Detected variables: specialty={self.specialty}, city={self.city}, institution_type={self.institution_type}, institution_names={self.institution_names}, number_institutions={self.number_institutions}")

            csv_data = {
                'uuid': str(uuid4()),
                'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'question': prompt,
                'response': error_msg,
                'conversation_list': conversation if conversation else [],
                'city': self.data_processor.city,
                'institution_type': self.data_processor.institution_type,
                'institution_names': self.data_processor.institution_names,
                'specialty': self.data_processor.specialty,
                'number_institutions': self.data_processor.number_institutions,
                'total_cost_sanity_checks': aggregation.get('total_cost_sanity_checks_analyst'),
                'total_cost_query_analyst': aggregation.get('total_cost_query_analyst'),
                'total_cost_conversation_analyst': aggregation.get('total_cost_conversation_analyst'),
                'total_cost': aggregation.get('total_cost'),
                'total_tokens_sanity_checks': aggregation.get('total_token_usage_sanity_checks_analyst'),
                'total_tokens_query_analyst': aggregation.get('total_token_usage_query_analyst'),
                'total_tokens_conversation_analyst': aggregation.get('total_token_usage_conversation_analyst'),
                'total_tokens': aggregation.get('total_token_usage')
            }
            self.data_processor.create_csv(result_data=csv_data)
            logger.info("Sanity check failed, returning error message and halting pipeline.")
            return error_msg, []
        if isinstance(sanity_result, dict) and not sanity_result.get("passed", True):
            error_msg = sanity_result.get("error", ERROR_MESSAGES['general_error'])
            aggregation = self.get_costs_and_tokens(getattr(self, 'sanity_checks_analyst_result', None), None, None)
            logger.info(f"Final cost/token usage aggregation: {aggregation}")
            logger.info(f"Detected variables: specialty={self.specialty}, city={self.city}, institution_type={self.institution_type}, institution_names={self.institution_names}, number_institutions={self.number_institutions}")

            csv_data = {
                'uuid': str(uuid4()),
                'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'question': prompt,
                'response': error_msg,
                'conversation_list': conversation if conversation else [],
                'city': self.data_processor.city,
                'institution_type': self.data_processor.institution_type,
                'institution_names': self.data_processor.institution_names,
                'specialty': self.data_processor.specialty,
                'number_institutions': self.data_processor.number_institutions,
                'total_cost_sanity_checks': aggregation.get('total_cost_sanity_checks_analyst'),
                'total_cost_query_analyst': aggregation.get('total_cost_query_analyst'),
                'total_cost_conversation_analyst': aggregation.get('total_cost_conversation_analyst'),
                'total_cost': aggregation.get('total_cost'),
                'total_tokens_sanity_checks': aggregation.get('total_token_usage_sanity_checks_analyst'),
                'total_tokens_query_analyst': aggregation.get('total_token_usage_query_analyst'),
                'total_tokens_conversation_analyst': aggregation.get('total_token_usage_conversation_analyst'),
                'total_tokens': aggregation.get('total_token_usage')
            }
            self.data_processor.create_csv(result_data=csv_data)
            logger.info("Sanity check failed, returning error message and halting pipeline.")

            return error_msg, []
        

        # Specialty selection logic
        if selected_specialty:
            # User selected a specialty from a provided list, use it directly and skip detection
            logger.info(f"User selected specialty: {selected_specialty}, using for ranking.")
            self.specialty = selected_specialty
            self.data_processor.specialty = selected_specialty
            # Run detection for other parameters only
            detections = self.extract_query_parameters(prompt, selected_specialty, conv_history)
        else:
            # Always detect specialty via query analysis module
            detections = self.extract_query_parameters(prompt, None, conv_history)
        logger.info(f"Detected variables: specialty={self.specialty}, city={self.city}, institution_type={self.institution_type}, institution_names={self.institution_names}, number_institutions={self.number_institutions}")
        logger.debug(f"[CITY DETECTION] Detected city: '{self.city}', city_detected: {self.city_detected}, DataProcessor.city: '{self.data_processor.city}', DataProcessor.city_detected: {self.data_processor.city_detected}")

        specialty_list = []
        # Check for multiple specialties in detections (only if not selected_specialty)
        if not selected_specialty and detections:
            # If specialty is a list with more than one item, treat as multiple specialties
            if "specialty" in detections and isinstance(detections["specialty"], list) and len(detections["specialty"]) > 1:
                specialty_list = detections["specialty"]
            # If specialty is a string, treat as a single specialty
            elif "specialty" in detections and isinstance(detections["specialty"], str):
                specialty_list = [detections["specialty"]]

            # Always block if specialty_list has more than one item
            if specialty_list and len(specialty_list) > 1:
                logger.info("Multiple specialty matches detected, returning for UI selection")
                formatted_response = (NON_ERROR_MESSAGES['multiple_specialties'] + "\n- " + "\n- ".join(specialty_list))
                logger.debug(f"Returning multiple matches response: {formatted_response}")
                return {"message": formatted_response, "multiple_specialties": specialty_list}, None
            
        # Handle explicit institution mentions with intent before ranking logic
        # if self.institution_names and self.institution_names_intent in ["single", "multi", "compare"]:
        if self.institution_name_mentioned and self.institution_names_intent in ["single", "multi", "compare"]: 
            logger.info(
                f"Institution(s) detected with intent={self.institution_names_intent}: "
                f"{self.institution_names}"
            )
            # Add specialty to all HospitalInfo instances if detected
            if self.specialty:
                for hospital in self.institution_names:
                    hospital.specialty = self.specialty

            if self.institution_names_intent == "single":
                # Only one institution explicitly mentioned → fetch its ranking directly
                inst_name = self.institution_names[0].name
                logger.debug(f"Fetching ranking for single institution: {inst_name}")
                df_single_institution = self.build_ranking_dataframe_with_distances(prompt, relevant_file, self.specialty)
                res = self.get_filtered_and_sorted_df(df=df_single_institution, max_radius_km=max_radius_km, number_institutions=1, prompt=prompt)
                return res, self.link or []

            elif self.institution_names_intent == "multi":
                # Multiple institutions explicitly mentioned → return comparison view
                inst_names = [i.name for i in self.institution_names]
                logger.debug(f"Fetching ranking for multiple institutions: {inst_names}")
                res = self.compare_institutions(inst_names, prompt)
                return res, self.link or []

            elif self.institution_names_intent == "compare":
                # Explicit request to compare institutions → always trigger comparison UI
                inst_names = [i.name for i in self.institution_names]
                logger.debug(f"Comparing institutions (explicit compare intent): {inst_names}")
                res = self.compare_institutions(inst_names, prompt, mode="explicit")
                return res, self.link or []
        # Build DataFrame with ranking and distances
        logger.debug("Calling build_ranking_dataframe_with_distances")
        try:
            df = self.build_ranking_dataframe_with_distances(prompt, relevant_file, self.specialty)
            logger.debug(f"build_ranking_dataframe_with_distances returned DataFrame: {type(df)}")
        except Exception as e:
            logger.exception(f"Exception in build_ranking_dataframe_with_distances: {e}")
            return ERROR_MESSAGES['general_ranking_error'], []

        # Check if DataFrame is None and return error message if so
        logger.debug("Checking if DataFrame is None")
        if df is None:
            logger.error("build_ranking_dataframe_with_distances returned None. Aborting response generation.")
            return ERROR_MESSAGES['general_ranking_error'], []
        logger.debug(f"Retrieved DataFrame shape: {df.shape if hasattr(df, 'shape') else 'N/A'}")

        # Handle geolocation API errors
        logger.debug("Checking for geolocation API errors")
        if self.data_processor.geolocation_api_error:
            logger.error("Geopy API error encountered, cannot calculate distances")
            return ERROR_MESSAGES['geopy_error'], []

        # Get ranking link for UI
        logger.debug("Getting ranking link for UI")
        self.link = self.data_processor.web_ranking_link

        # Handle cases where no results are found for requested specialty/type
        logger.debug("Checking for specialty_ranking_unavailable")
        if self.data_processor.specialty_ranking_unavailable:
            logger.warning("Ranking not found for requested specialty/type, suggesting alternative")
            fallback_type = None
            if self.data_processor.institution_type == 'Privé':
                logger.debug("No private institution for this specialty, trying public institutions as fallback")
                fallback_type = 'Public'
            elif self.data_processor.institution_type == 'Public':
                logger.debug("No public institution for this specialty, trying private institutions as fallback")
                fallback_type = 'Privé'
            if fallback_type:
                # Only change institution type, preserve specialty and city
                self.data_processor.institution_type = fallback_type
                self.institution_type = fallback_type
                self.data_processor.specialty_ranking_unavailable = False
                self.data_processor.df_gen = None
                try:
                    # Build DataFrame for fallback type (no parameter re-extraction)
                    fallback_df = self.data_processor.generate_data_response()
                    # Defensive: check DataFrame validity
                    if fallback_df is not None and hasattr(fallback_df, 'columns') and "Catégorie" in fallback_df.columns:
                        filtered_fallback = fallback_df[fallback_df["Catégorie"] == fallback_type]
                        if filtered_fallback is not None and not filtered_fallback.empty and "Note / 20" in filtered_fallback.columns:
                            top_fallback = filtered_fallback.nlargest(self.number_institutions, "Note / 20")
                            if fallback_type == 'Public':
                                res_str = format_response(top_fallback, None, self.number_institutions, not self.data_processor.city_detected)
                                message = self._format_response_with_specialty(NON_ERROR_MESSAGES['no_private_institutions'] + "\nCependant, voici les établissements publics disponibles :", self.number_institutions, max_radius_km, self.city)
                            else:
                                res_str = format_response(None, top_fallback, self.number_institutions, not self.data_processor.city_detected)
                                message = self._format_response_with_specialty(NON_ERROR_MESSAGES['no_public_institutions'] + "\nCependant, voici les établissements privés disponibles :", self.number_institutions, max_radius_km, self.city)
                            return self._create_response_and_log(message, res_str, prompt, METHODOLOGY_WEB_LINK), self.link or []
                        else:
                            public_exists = not fallback_df[fallback_df["Catégorie"] == "Public"].empty if "Catégorie" in fallback_df.columns else False
                            private_exists = not fallback_df[fallback_df["Catégorie"] == "Privé"].empty if "Catégorie" in fallback_df.columns else False
                            if not public_exists and not private_exists:
                                return "Aucun établissement (ni public ni privé) est disponible pour votre query.", []
                            elif fallback_type == 'Privé' and not private_exists:
                                return NON_ERROR_MESSAGES['no_private_institutions'], []
                            elif fallback_type == 'Public' and not public_exists:
                                return NON_ERROR_MESSAGES['no_public_institutions'], []
                    else:
                        logger.warning("Fallback DataFrame missing 'Catégorie' column or is malformed. Returning fallback error message.")
                        return "Aucun établissement (ni public ni privé) est disponible pour votre query.", []
                except Exception as e:
                    logger.exception(f"Exception in fallback to {fallback_type} institutions: {e}")
                    return "Aucun établissement (ni public ni privé) est disponible pour votre query.", []
            if self.data_processor.institution_type == 'Public':
                return NON_ERROR_MESSAGES['no_public_institutions'], []
            elif self.data_processor.institution_type == 'Privé':
                return NON_ERROR_MESSAGES['no_private_institutions'], []
        # If institution is mentioned, return its ranking and link
        logger.debug("Checking if institution is mentioned")
        if self.institution_name_mentioned:
            logger.info("Returning result for mentioned institution")
            try:
                res = self.get_filtered_and_sorted_df(df, max_radius_km, self.number_institutions, prompt)
                logger.debug(f"Result from get_filtered_and_sorted_df: {res}, Links: {self.link}")
            except Exception as e:
                logger.exception(f"Exception in get_filtered_and_sorted_df: {e}")
                return ERROR_MESSAGES['general_error'], []
            return res, self.link or []
        # If city found and Distance column exists, use multi-radius search utility to get enough results
        logger.debug("Checking if city is detected")
        logger.debug(f"[DF COLUMNS] DataFrame columns before city/distance selection: {df.columns.tolist()}")
        # Use original city column 'Ville' for all city-based selection
        if self.data_processor.city_detected and "Ville" in df.columns:
            logger.debug(f"Unique cities in DataFrame before select_hospitals: {df['Ville'].unique() if 'Ville' in df.columns else 'N/A'}")
            logger.info("City detected, preparing to call select_hospitals.")
            logger.debug(f"About to call select_hospitals with df columns: {df.columns.tolist()}, city: {self.data_processor.city}, number_institutions: {self.number_institutions}")
            query_city = self.data_processor.city
            query_coords = None
            # Try to get coordinates for the city if available (assume DataProcessor or utility provides this)
            if hasattr(self.data_processor, 'get_city_coordinates'):
                query_coords = self.data_processor.get_city_coordinates(query_city)
            elif hasattr(self.data_processor, 'city_coordinates'):
                query_coords = self.data_processor.city_coordinates.get(query_city)
            radii = SEARCH_RADIUS_KM
            selected_df, used_radius = self.data_processor.select_hospitals(df, query_city, self.number_institutions, query_coords, radii)
            if selected_df is None or selected_df.empty:
                logger.warning("No results found for city or by distance.")
                return NON_ERROR_MESSAGES['no_results_found_in_location'], []
            institution_type = getattr(self, 'institution_type', None)
            public_df = selected_df[selected_df["Catégorie"] == "Public"] if "Catégorie" in selected_df.columns else None
            private_df = selected_df[selected_df["Catégorie"] == "Privé"] if "Catégorie" in selected_df.columns else None
            if institution_type == 'Public':
                res_str = format_response(public_df, None, self.number_institutions, not self.data_processor.city_detected)
            elif institution_type == 'Privé':
                res_str = format_response(None, private_df, self.number_institutions, not self.data_processor.city_detected)
            else:
                res_str = format_response(public_df, private_df, self.number_institutions, not self.data_processor.city_detected)
            message = self._format_response_with_specialty(
                f"Voici les meilleurs établissements (rayon utilisé : {used_radius} km)",
                self.number_institutions, used_radius, self.city
            )
            return self._create_response_and_log(message, res_str, prompt, METHODOLOGY_WEB_LINK), self.link or []
        # General ranking response if no city found
        logger.info("No city detected, returning general ranking")
        try:
            if 'Distance' in self.df_gen.columns:
                logger.debug("Dropping Distance column from df_gen")
                self.df_gen = self.df_gen.drop(columns=['Distance'])
            logger.debug(f"[GENERAL RANKING] DataFrame columns: {self.df_gen.columns.tolist()}")
            public_df = self.df_gen[self.df_gen["Catégorie"] == "Public"].nlargest(self.number_institutions, "Note / 20")
            private_df = self.df_gen[self.df_gen["Catégorie"] == "Privé"].nlargest(self.number_institutions, "Note / 20")
            res_str = format_response(public_df, private_df, self.number_institutions, not self.data_processor.city_detected)
            logger.debug(f"Formatted response string: {res_str}")
            base_message = "Voici le meilleur établissement" if self.number_institutions == 1 else f"Voici les {self.number_institutions} meilleurs établissements"
            display_specialty, is_no_match = self._normalize_specialty_for_display(self.specialty)
            logger.debug(f"Display specialty: {display_specialty}, is_no_match: {is_no_match}")
            if is_no_match:
                message = f"{base_message}:<br> \n"
            else:
                message = f"{base_message} pour la pathologie {display_specialty}<br> \n"
            logger.debug(f"Result: {message}, Links: {self.link}")
            response = self._create_response_and_log(message, res_str, prompt, METHODOLOGY_WEB_LINK)
            logger.info(f"General ranking response created successfully")
            logger.info(f"Detected variables: specialty={self.specialty}, city={self.city}, institution_type={self.institution_type}, institution_names={self.institution_names}, number_institutions={self.number_institutions}")
            self.link = extract_links_from_text(response)
            return response, self.link
        except Exception as e:
            logger.exception(f"Exception in general ranking response: {e}")
            logger.info(f"Detected variables: specialty={self.specialty}, city={self.city}, institution_type={self.institution_type}, institution_names={self.institution_names}, number_institutions={self.number_institutions}")
            return ERROR_MESSAGES['general_ranking_error'], []
