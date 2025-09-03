import pandas as pd
from datetime import datetime
from uuid import uuid4
## Accent-insensitive matching removed
from app.services.data_processing_service import DataProcessor
from app.features.query_analysis.query_analyst import QueryAnalyst
from app.config.file_paths_config import PATHS
from app.config.features_config import (SEARCH_RADIUS_KM, NON_ERROR_MESSAGES, ERROR_MESSAGES, METHODOLOGY_WEB_LINK)
from app.utility.logging import get_logger
from app.utility.formatting_helpers import format_response
from app.features.sanity_checks.message_pertinence_check import MessagePertinenceCheckException
from app.features.sanity_checks.message_length_check import MessageLengthCheckException
from app.features.sanity_checks.conversation_limit_check import ConversationLimitCheckException
from app.features.sanity_checks.sanity_checks_analyst import SanityChecksAnalyst

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
        generate_response(prompt: str, max_radius_km: int = 5, conversation=None, conv_history=None) -> str:
            Main entry point: processes the user question and returns a formatted answer with ranking and links.    
    """
    def __init__(self):
        logger.info("Initializing PipelineOrchestrator")
        self.ranking_file_path= PATHS["ranking_file_path"]
        self.specialty= None
        self.institution_type= None
        self.city = None
        self.city_detected = False  # Flag to indicate if a city was detected
        self.df_gen = None # DF for results 
        self.institution_mentioned=None
        self.institution_name=None
        self.data_processor=DataProcessor() # Instance of DataProcessor for data extraction and transformation
        self.sanity_checks_analyst_results = SanityChecksAnalyst(self.data_processor.llm_handler_service)
        self.query_analyst_results = None

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


    def _create_response_and_log(self, message: str, table_str: str, prompt: str, ranking_link: str = None, sanity_result=None, detections=None, conversation_analyst_results=None) -> str:
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
        logger.info(f"Detected variables: specialty={self.specialty}, city={self.city}, institution_type={self.institution_type}, institution_name={self.institution_name}, number_institutions={self.number_institutions}")

        csv_data = {
            'uuid': str(uuid4()),
            'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'question': prompt,
            'response': response,
            'conversation_list': conversation_analyst_results.get('conversation', []) if conversation_analyst_results else [],
            'city': self.data_processor.city,
            'institution_type': self.data_processor.institution_type,
            'institution_name': self.data_processor.institution_name,
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
            institution_name=detections.get('institution_name'),
            institution_mentioned=detections.get('institution_mentioned')
        )
        # Set orchestrator attributes for downstream use
        self.specialty = self.data_processor.specialty
        logger.debug(f"PipelineOrchestrator.specialty set to: {self.specialty!r}")
        self.city = self.data_processor.city
        logger.debug(f"PipelineOrchestrator.city set to: {self.city!r}")
        self.city_detected = self.data_processor.city_detected
        logger.debug(f"PipelineOrchestrator.city_detected set to: {self.city_detected!r}")
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
        logger.info(f"Detected variables: specialty={self.specialty}, city={self.city}, institution_type={self.institution_type}, institution_name={self.institution_name}, number_institutions={self.number_institutions}")
        
        # Generate main DataFrame
        self.df_gen = self.data_processor.generate_data_response()
        # Debug: Log unique specialties and institution types in the loaded DataFrame
        if self.df_gen is not None:
            logger.debug(f"[DEBUG] Unique specialties in DataFrame: {self.df_gen['Spécialité'].unique() if 'Spécialité' in self.df_gen.columns else 'N/A'}")
            logger.debug(f"[DEBUG] Unique institution types in DataFrame: {self.df_gen['Catégorie'].unique() if 'Catégorie' in self.df_gen.columns else 'N/A'}")
            logger.debug(f"[DEBUG] DataFrame columns: {self.df_gen.columns}")
            logger.debug(f"[DEBUG] DataFrame head: {self.df_gen.head(10)}")
            logger.debug(f"[DEBUG] Filtering for specialty: '{self.specialty}' and city: '{self.city}'")
            specialty_matches = self.df_gen[self.df_gen['Spécialité'] == self.specialty] if 'Spécialité' in self.df_gen.columns else None
            logger.debug(f"[DEBUG] Specialty match count: {specialty_matches.shape[0] if specialty_matches is not None else 'N/A'}")
            if specialty_matches is not None:
                logger.debug(f"[DEBUG] Specialty match rows: {specialty_matches}")
            if self.city:
                city_matches = self.df_gen[self.df_gen['Ville'] == self.city] if 'Ville' in self.df_gen.columns else None
                logger.debug(f"[DEBUG] City match count: {city_matches.shape[0] if city_matches is not None else 'N/A'}")
                if city_matches is not None:
                    logger.debug(f"[DEBUG] City match rows: {city_matches}")
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
            logger.info(f"Detected variables: specialty={self.specialty}, city={self.city}, institution_type={self.institution_type}, institution_name={self.institution_name}, number_institutions={self.number_institutions}")

            csv_data = {
                'uuid': str(uuid4()),
                'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'question': prompt,
                'response': error_msg,
                'conversation_list': conversation if conversation else [],
                'city': self.data_processor.city,
                'institution_type': self.data_processor.institution_type,
                'institution_name': self.data_processor.institution_name,
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
            return error_msg, None
        if isinstance(sanity_result, dict) and not sanity_result.get("passed", True):
            error_msg = sanity_result.get("error", ERROR_MESSAGES['general_error'])
            aggregation = self.get_costs_and_tokens(getattr(self, 'sanity_checks_analyst_result', None), None, None)
            logger.info(f"Final cost/token usage aggregation: {aggregation}")
            logger.info(f"Detected variables: specialty={self.specialty}, city={self.city}, institution_type={self.institution_type}, institution_name={self.institution_name}, number_institutions={self.number_institutions}")

            csv_data = {
                'uuid': str(uuid4()),
                'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'question': prompt,
                'response': error_msg,
                'conversation_list': conversation if conversation else [],
                'city': self.data_processor.city,
                'institution_type': self.data_processor.institution_type,
                'institution_name': self.data_processor.institution_name,
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

            return error_msg, None
        

        # Specialty selection logic
        if selected_specialty:
            # User selected a specialty, use it directly and skip detection
            logger.info(f"User selected specialty: {selected_specialty}, using for ranking.")
            self.specialty = selected_specialty
            self.data_processor.specialty = selected_specialty
            # Run detection for other parameters only
            detections = self.extract_query_parameters(prompt, selected_specialty, conv_history)
        else:
            # Always detect specialty via query analysis module
            detections = self.extract_query_parameters(prompt, None, conv_history)
        logger.info(f"Detected variables: specialty={self.specialty}, city={self.city}, institution_type={self.institution_type}, institution_name={self.institution_name}, number_institutions={self.number_institutions}")
        logger.debug(f"[CITY DETECTION] Detected city: '{self.city}', city_detected: {self.city_detected}, DataProcessor.city: '{self.data_processor.city}', DataProcessor.city_detected: {self.data_processor.city_detected}")

        specialty_list = []
        # Check for multiple specialties in detections (only if not selected_specialty)
        if not selected_specialty and detections:
            # Case 1: explicit multiple_specialties list
            if "multiple_specialties" in detections and detections["multiple_specialties"]:
                specialty_list = detections["multiple_specialties"]
            # Case 2: specialty is a list
            elif "specialty" in detections and isinstance(detections["specialty"], list) and len(detections["specialty"]) > 1:
                specialty_list = detections["specialty"]
            # Case 3: specialty is a string starting with 'multiple matches:' (robust to spaces)
            elif "specialty" in detections and isinstance(detections["specialty"], str):
                specialty_str = detections["specialty"].lower().replace(" ","")
                if specialty_str.startswith("multiplematches:"):
                    matches_str = detections["specialty"][detections["specialty"].find(":")+1:].strip()
                    if "," in matches_str:
                        specialty_list = [s.strip() for s in matches_str.split(",") if s.strip()]
                    else:
                        specialty_list = [matches_str] if matches_str else []

        # Always block if specialty_list has more than one item
        if specialty_list and len(specialty_list) > 1:
            logger.info("Multiple specialty matches detected (robust), returning for UI selection")
            formatted_response = (
                NON_ERROR_MESSAGES['multiple_specialties'] + "\n- " + "\n- ".join(specialty_list)
            )
            logger.debug(f"Returning multiple matches response: {formatted_response}")
            return {
                "message": formatted_response,
                "multiple_specialties": specialty_list
            }, None

        # Build DataFrame with ranking and distances
        logger.debug("Calling build_ranking_dataframe_with_distances")
        try:
            df = self.build_ranking_dataframe_with_distances(prompt, relevant_file, self.specialty)
            logger.debug(f"build_ranking_dataframe_with_distances returned DataFrame: {type(df)}")
        except Exception as e:
            logger.exception(f"Exception in build_ranking_dataframe_with_distances: {e}")
            return ERROR_MESSAGES['general_ranking_error'], None

        # Check if DataFrame is None and return error message if so
        logger.debug("Checking if DataFrame is None")
        if df is None:
            logger.error("build_ranking_dataframe_with_distances returned None. Aborting response generation.")
            return ERROR_MESSAGES['general_ranking_error'], None
        logger.debug(f"Retrieved DataFrame shape: {df.shape if hasattr(df, 'shape') else 'N/A'}")

        # Handle geolocation API errors
        logger.debug("Checking for geolocation API errors")
        if self.data_processor.geolocation_api_error:
            logger.error("Geopy API error encountered, cannot calculate distances")
            return ERROR_MESSAGES['geopy_error'], None

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
                            return self._create_response_and_log(message, res_str, prompt, METHODOLOGY_WEB_LINK), self.link
                        else:
                            public_exists = not fallback_df[fallback_df["Catégorie"] == "Public"].empty if "Catégorie" in fallback_df.columns else False
                            private_exists = not fallback_df[fallback_df["Catégorie"] == "Privé"].empty if "Catégorie" in fallback_df.columns else False
                            if not public_exists and not private_exists:
                                return "Aucun établissement (ni public ni privé) est disponible pour votre query.", self.link
                            elif fallback_type == 'Privé' and not private_exists:
                                return NON_ERROR_MESSAGES['no_private_institutions'], self.link
                            elif fallback_type == 'Public' and not public_exists:
                                return NON_ERROR_MESSAGES['no_public_institutions'], self.link
                    else:
                        logger.warning("Fallback DataFrame missing 'Catégorie' column or is malformed. Returning fallback error message.")
                        return "Aucun établissement (ni public ni privé) est disponible pour votre query.", self.link
                except Exception as e:
                    logger.exception(f"Exception in fallback to {fallback_type} institutions: {e}")
                    return "Aucun établissement (ni public ni privé) est disponible pour votre query.", self.link
            if self.data_processor.institution_type == 'Public':
                return NON_ERROR_MESSAGES['no_public_institutions'], self.link
            elif self.data_processor.institution_type == 'Privé':
                return NON_ERROR_MESSAGES['no_private_institutions'], self.link

        # If institution is mentioned, return its ranking and link
        logger.debug("Checking if institution is mentioned")
        if self.institution_mentioned:
            logger.info("Returning result for mentioned institution")
            try:
                res = self.get_filtered_and_sorted_df(df, max_radius_km, self.number_institutions, prompt)
                logger.debug(f"Result from get_filtered_and_sorted_df: {res}, Links: {self.link}")
            except Exception as e:
                logger.exception(f"Exception in get_filtered_and_sorted_df: {e}")
                return ERROR_MESSAGES['general_error'], self.link
            return res, self.link

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
                return NON_ERROR_MESSAGES['no_results_found_in_location'], self.link
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
            return self._create_response_and_log(message, res_str, prompt, METHODOLOGY_WEB_LINK), self.link

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
                message = f"{base_message}:<br> \n"
            else:
                message = f"{base_message} pour la pathologie {display_specialty}<br> \n"
            logger.debug(f"Result: {message}, Links: {self.link}")
            response = self._create_response_and_log(message, res_str, prompt, METHODOLOGY_WEB_LINK)
            logger.info(f"General ranking response created successfully")
            logger.info(f"Detected variables: specialty={self.specialty}, city={self.city}, institution_type={self.institution_type}, institution_name={self.institution_name}, number_institutions={self.number_institutions}")
            return response, self.link
        except Exception as e:
            logger.exception(f"Exception in general ranking response: {e}")
            logger.info(f"Detected variables: specialty={self.specialty}, city={self.city}, institution_type={self.institution_type}, institution_name={self.institution_name}, number_institutions={self.number_institutions}")
            return ERROR_MESSAGES['general_ranking_error'], self.link
