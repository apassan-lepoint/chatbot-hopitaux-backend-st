"""
Service for processing and transforming hospital ranking data.

This file defines the DataProcessor class, which loads, merges, and filters ranking and
    location data, and prepares results for the chatbot pipeline.
"""

import os
from click import prompt
import pandas as pd
import csv
from datetime import datetime
import unicodedata

from app.config.file_paths_config import PATHS
from app.services.llm_handler_service import LLMHandler
from app.utility.formatting_helpers import remove_accents
from app.utility.distance_calc_helpers import exget_coordinates, distance_to_query
from app.utility.logging import get_logger


logger = get_logger(__name__)

class DataProcessor:
    """
    Processes hospital ranking data based on user queries. Extracts query information using LLM services, 
    loads and filters ranking data by specialty and institution type, and calculates distances to provide relevant results.
        """
    
    def __init__(self):
        logger.info("Initializing DataProcessor")
        """
        Initializes the DataProcessor class, sets up file paths, loads the LLM service, and prepares variables 
        for query processing.
        """
        self.paths = PATHS
        self.ranking_df = None
        self.llm_handler_service = LLMHandler()
        self.specialty_df = None
        self.institution_name = None
        self.specialty_ranking_unavailable = False
        self.web_ranking_link = []
        self.geolocation_api_error = False
        self.specialty= None
        self.institution_type= None
        self.city = None
        self.df_with_cities = None
        self.institution_mentioned = None
        self.topk = None
        # Predefined links for public/private rankings
        self.weblinks={
                "public":"https://www.lepoint.fr/hopitaux/classements/tableau-d-honneur-public.php",
                "privé":"https://www.lepoint.fr/hopitaux/classements/tableau-d-honneur-prive.php"
        }
        try:
            self.institution_coordinates_df = pd.read_excel(self.paths["hospital_coordinates_path"])
        except Exception as e:
            logger.error(f"Failed to load hospital coordinates Excel: {e}")
            raise
    
    
    def _load_ranking_dataframe(self, file_path: str, category: str) -> pd.DataFrame:
        logger.debug(f"Loading ranking dataframe from {file_path} for category {category}")
        """
        Helper method to load and prepare ranking DataFrame with category.
        
        Args:
            file_path: Path to the CSV file
            category: Category to assign to the data
            
        Returns:
            pd.DataFrame: Prepared DataFrame with category and renamed columns
        """
        df = pd.read_csv(file_path)
        df['Catégorie'] = category
        df = df.rename(columns={'Score final': 'Note / 20', 'Nom Print': 'Etablissement'})
        logger.debug(f"Loaded {category} rankings: {len(df)} rows")
        return df

    def _generate_web_link(self, specialty: str, institution_type: str) -> str:
        logger.debug(f"Generating web link for specialty '{specialty}' and institution_type '{institution_type}'")
        """
        Helper method to generate a single web ranking link.
        
        Args:
            specialty: Medical specialty name
            institution_type: Institution type (public/private)
            
        Returns:
            str: Generated web link URL
        """
        web_link = specialty.replace(' ', '-')
        web_link = f'https://www.lepoint.fr/hopitaux/classements/{web_link}-{institution_type}.php'
        web_link = web_link.lower()
        return remove_accents(web_link)

    def _normalize_str(self, s: str) -> str:
        logger.debug(f"Normalizing string: {s}")
        """Utility to normalize strings for matching."""
        if not isinstance(s, str):
            return ""
        s = s.strip().lower()
        s = unicodedata.normalize('NFKD', s)
        s = ''.join(c for c in s if not unicodedata.combining(c))
        return s

    def _is_no_specialty(self, specialty: str) -> bool:
        logger.debug(f"Checking if specialty is 'no match': {specialty}")
        """Utility to check if specialty is empty or no match."""
        return not specialty or specialty in ["no match", "no specialty match", "aucune correspondance"] or specialty.strip() == ""

    def _parse_specialty_list(self, specialty: str) -> list:
        logger.debug(f"Parsing specialty list from: {specialty}")
        """Utility to parse multiple specialties from a string."""
        if specialty.startswith('plusieurs correspondances:'):
            specialty_list = specialty.replace('plusieurs correspondances:', '').strip()
        elif specialty.startswith('multiple matches:'):
            specialty_list = specialty.replace('multiple matches:', '').strip()
        else:
            specialty_list = specialty
        return [s.strip() for s in specialty_list.split(',') if s.strip()]
    
    def _get_institution_list(self):
        logger.info("Getting institution list from coordinates DataFrame")
        """
        Returns a formatted, deduplicated list of institutions present in the rankings.
        Cleans names to avoid duplicates or matching errors.
        """
        column_1 = self.institution_coordinates_df.iloc[:, 0]
        institution_list = [element.split(",")[0] for element in column_1]
        institution_list = list(set(institution_list))
        institution_list = [element for element in institution_list if element not in ("CHU", "CH")]
        institution_list = ", ".join(map(str, institution_list))
        logger.debug(f"Institution list: {institution_list}")
        return institution_list

    def _filter_ranking_by_criteria(self, specialty: str, institution_type: str = None) -> pd.DataFrame:
        logger.info(f"Filtering ranking by criteria: specialty='{specialty}', institution_type='{institution_type}'")
        """
        Helper method to filter ranking DataFrame by specialty and optionally by institution type.
        Normalizes both specialty and data for robust matching.
        """
        logger.debug(f"Filtering ranking data - specialty: '{specialty}', institution_type: '{institution_type}'")
        logger.debug(f"Specialty type: {type(specialty)}, length: {len(specialty) if specialty else 'None'}")
        logger.debug(f"Available specialties in ranking data: {self.ranking_df['Spécialité'].unique()}")

        if self._is_no_specialty(specialty):
            logger.debug("No specialty provided or specialty is 'no match', returning empty DataFrame")
            return pd.DataFrame()
        # Normalize the Spécialité column once if not already present
        if 'Spécialité_norm' not in self.ranking_df.columns:
            self.ranking_df['Spécialité_norm'] = self.ranking_df['Spécialité'].apply(self._normalize_str)
        matching_rows = pd.DataFrame()
        # Handle multiple specialties
        if ',' in specialty or specialty.startswith(('plusieurs correspondances:', 'multiple matches:')):
            individual_specialties = self._parse_specialty_list(specialty)
            logger.debug(f"Processing multiple specialties: {individual_specialties}")
            for individual_specialty in individual_specialties:
                if not self._is_no_specialty(individual_specialty):
                    try:
                        norm_spec = self._normalize_str(individual_specialty)
                        specialty_matches = self.ranking_df[self.ranking_df['Spécialité_norm'] == norm_spec]
                        if len(specialty_matches) > 0:
                            matching_rows = pd.concat([matching_rows, specialty_matches], ignore_index=True)
                    except Exception as e:
                        logger.warning(f"Error filtering by specialty '{individual_specialty}': {e}")
                        continue
            matching_rows = matching_rows.drop_duplicates()
            logger.debug(f"Found {len(matching_rows)} rows matching multiple specialties")
            logger.debug(f"Specialties found after specialty filtering: {matching_rows['Spécialité'].unique()}")
        else:
            # Single specialty matching with normalization
            try:
                specialty_norm = self._normalize_str(specialty)
                matching_rows = self.ranking_df[self.ranking_df['Spécialité_norm'] == specialty_norm]
                logger.debug(f"Found {len(matching_rows)} rows matching single specialty '{specialty}' (normalized: '{specialty_norm}')")
                logger.debug(f"Specialties found after specialty filtering: {matching_rows['Spécialité'].unique()}")
            except Exception as e:
                logger.warning(f"Error filtering by specialty '{specialty}': {e}")
                return pd.DataFrame()
        # Filter by institution type if provided
        if institution_type and institution_type not in ['no match', 'aucune correspondance']:
            # Assume institution_type is already normalized by PromptDetectionManager
            logger.debug(f"Filtering by institution type: '{institution_type}' (already normalized)")
            logger.debug(f"Available categories in ranking data: {self.ranking_df['Catégorie'].unique()}")
            if institution_type not in ["no match", "aucune correspondance"]:
                try:
                    matching_rows = matching_rows[matching_rows["Catégorie"].str.contains(institution_type, case=False, na=False)]
                    logger.debug(f"Found {len(matching_rows)} rows after filtering by institution type")
                except Exception as e:
                    logger.warning(f"Error filtering by institution type '{institution_type}': {e}")
        return matching_rows

    def get_institution_type_for_url(self, institution_type: str) -> str:
        logger.debug(f"Mapping institution type for URL: {institution_type}")
        """Convert institution type to format expected by web URLs. Assumes input is already normalized."""
        url_mapping = {
            "Public": "public",
            "Privé": "prive",
            "aucune correspondance": "aucune correspondance"
        }
        return url_mapping.get(institution_type, institution_type.lower())
    
    
    def get_infos(self, prompt: str, detected_specialty: str = None, conv_history: list = None) -> dict:
        logger.info(f"get_infos called with prompt: {prompt}, detected_specialty: {detected_specialty}, conv_history: {conv_history}")
        """
        Extracts key aspects from the user's question using PromptDetectionManager.
        Args:
            prompt (str): The user's question.
            detected_specialty (str, optional): Pre-detected specialty from conversation context.
            conv_history (list, optional): Conversation history for multi-turn context.
        Returns:
            dict: Dictionary of extracted info (city, specialty, institution type, etc.)
        """
        logger.info(f"Extracting infos from prompt: {prompt}")
        from app.features.prompt_detection.prompt_detection_manager import PromptDetectionManager
        # Use the LLM model from llm_handler_service
        model = getattr(self.llm_handler_service, 'model', None)
        prompt_manager = PromptDetectionManager(model=model)
        institution_list = self._get_institution_list()
        conv_history_str = "".join(conv_history) if conv_history else ""
        detections = prompt_manager.run_all_detections(prompt, conv_history=conv_history_str, institution_list=institution_list)
        # Use provided specialty or detect it
        if detected_specialty:
            logger.info(f"Using provided specialty from context: {detected_specialty}")
            self.specialty = detected_specialty
        else:
            self.specialty = detections.get('specialty')
        self.city = detections.get('city')
        self.institution_type = detections.get('institution_type')
        self.topk = detections.get('top_k')
        self.institution_name = detections.get('institution_name')
        self.institution_mentioned = detections.get('institution_mentioned')
        try:
            self.institution_coordinates_df = pd.read_excel(self.paths["hospital_coordinates_path"])
        except Exception as e:
            logger.error(f"Failed to load hospital coordinates Excel: {e}")
            raise
        self.institution_list = institution_list
        # Load ranking data
        try:
            ranking_file_path = self.paths["ranking_file_path"]
            logger.debug(f"Loading ranking data from: {ranking_file_path}")

            # Check if file exists
            if not os.path.exists(ranking_file_path):
                logger.error(f"Ranking file not found: {ranking_file_path}")
                raise FileNotFoundError(f"Ranking file not found: {ranking_file_path}")

            self.ranking_df = pd.read_excel(ranking_file_path, sheet_name="Palmarès")
            logger.debug(f"Loaded ranking DataFrame with {len(self.ranking_df)} rows")

            # Log column names for debugging
            logger.debug(f"Ranking DataFrame columns: {list(self.ranking_df.columns)}")

        except Exception as e:
            logger.error(f"Failed to load ranking file: {e}")
            raise
        return detections


    def generate_response_links(self, matching_rows: pd.DataFrame = None) -> list:
        logger.info(f"generate_response_links called with matching_rows: {type(matching_rows)}")
        """
        Generates web links to the relevant ranking pages based on specialty and institution type.

        Args:
            matching_rows (pd.DataFrame, optional): Rows from the ranking sheet that match the query.

        Returns:
            list or None: List of generated URLs or None if not applicable.
        """
        logger.info("Generating ranking links")
        self.web_ranking_link.clear()
        # If no specialty, suggest general ranking links
        if self._is_no_specialty(self.specialty):
            logger.debug("No specialty detected, generating general ranking links")
            institution_type_french = self.institution_type  # Already normalized
            if institution_type_french == 'Public':
                self.web_ranking_link = [self.weblinks["public"]]
            elif institution_type_french == 'Privé':
                self.web_ranking_link = [self.weblinks["privé"]]
            else:
                self.web_ranking_link = [self.weblinks["public"], self.weblinks["privé"]]
            return None
        # If ranking not found, suggest the opposite type
        if self.specialty_ranking_unavailable:
            logger.debug("Specialty ranking unavailable, generating opposite type links")
            institution_type_french = self.institution_type  # Already normalized
            opposite_type = 'prive' if institution_type_french == 'Public' else 'public'
            # Handle multiple specialties for opposite type links
            first_specialty = self._parse_specialty_list(self.specialty)[0] if (',' in self.specialty or self.specialty.startswith(('plusieurs correspondances:', 'multiple matches:'))) else self.specialty
            web_link = self._generate_web_link(first_specialty, opposite_type)
            self.web_ranking_link.append(web_link)
            return self.web_ranking_link
        # Generate links for each matching specialty/category row
        if matching_rows is not None and len(matching_rows) > 0:
            logger.debug(f"Generating links for {len(matching_rows)} matching rows")
            for _, row in matching_rows.iterrows():
                category_for_url = self.get_institution_type_for_url(row["Catégorie"])
                web_link = self._generate_web_link(row["Spécialité"], category_for_url)
                self.web_ranking_link.append(web_link)
        else:
            logger.debug("No matching rows provided, no links generated")
        logger.info(f"Generated ranking links: {self.web_ranking_link}")
        return self.web_ranking_link


    def _concat_dataframes(self, dfs: list) -> pd.DataFrame:
        logger.debug(f"Concatenating {len(dfs)} dataframes")
        """Utility to concatenate DataFrames."""
        if not dfs:
            return pd.DataFrame()
        return pd.concat(dfs, join="inner", ignore_index=True)

    def load_and_transform_for_no_specialty(self, category: str) -> pd.DataFrame:
        logger.info(f"load_and_transform_for_no_specialty called with category: {category}")
        """
        Loads and merges the general tables (tableau d'honneur) (public and/or private) for queries
            that do not mention a specific specialty.

        Args:
            category (str): The institution category (public/private) requested. 
                        Accepted values: 'aucune correspondance', 'Public', 'Privé'

        Returns:
            pd.DataFrame: The combined DataFrame of relevant institutions.
        """
        logger.info(f"Loading general rankings for category: {category}")
        
        try:
            dfs = []
            if category == 'aucune correspondance':
                logger.debug("Loading both public and private rankings")
                dfs.append(self._load_ranking_dataframe(self.paths["ranking_overall_private_path"], 'Privé'))
                dfs.append(self._load_ranking_dataframe(self.paths["ranking_overall_public_path"], 'Public'))
            elif category == 'Public':
                logger.debug("Loading public rankings only")
                dfs.append(self._load_ranking_dataframe(self.paths["ranking_overall_public_path"], 'Public'))
            elif category == 'Privé':
                logger.debug("Loading private rankings only")
                dfs.append(self._load_ranking_dataframe(self.paths["ranking_overall_private_path"], 'Privé'))
            else:
                raise ValueError(f"Unknown category: {category}")
            df = self._concat_dataframes(dfs)
            logger.info(f"Successfully loaded general rankings, final shape: {df.shape}")
            return df
        except Exception as e:
            logger.error(f"Failed to load rankings for category {category}: {e}")
            raise


    def load_excel_sheets(self, matching_rows: pd.DataFrame) -> pd.DataFrame:
        logger.info(f"load_excel_sheets called with matching_rows of length: {len(matching_rows) if matching_rows is not None else 'None'}")
        """
        Loads the Excel sheets corresponding to the matched specialties and categories.

        Args:
            matching_rows (pd.DataFrame): Rows from the ranking sheet that match the query.

        Returns:
            pd.DataFrame: Concatenated DataFrame of results, or an empty DataFrame if not found.
        """
        logger.info(f"Loading Excel sheets for {len(matching_rows)} matched specialties/categories")

        if len(matching_rows) == 0:
            logger.warning("No matching rows provided to load_excel_sheets")
            self.specialty_ranking_unavailable = True
            return pd.DataFrame()
        dfs = []
        excel_path = self.paths["ranking_file_path"]
        for _, row in matching_rows.iterrows():
            sheet_name = row["Sheet"]
            category = row["Catégorie"] if "Catégorie" in row else None
            logger.debug(f"Loading sheet: '{sheet_name}' for category: '{category}'")
            try:
                df_sheet = pd.read_excel(excel_path, sheet_name=sheet_name)
                if category is not None:
                    df_sheet["Catégorie"] = category
                dfs.append(df_sheet)
                logger.debug(f"Sheet '{sheet_name}' loaded successfully with {len(df_sheet)} rows")
            except Exception as e:
                logger.warning(f"Failed to load sheet '{sheet_name}': {e}")
                continue
        concatenated_df = self._concat_dataframes(dfs)
        if not concatenated_df.empty:
            logger.info(f"Successfully loaded {len(dfs)} sheets, total rows: {len(concatenated_df)}")
            return concatenated_df
        else:
            logger.warning("No matching sheets found for specialties/categories")
            self.specialty_ranking_unavailable = True
            return pd.DataFrame()


    def find_excel_sheet_with_specialty(self, prompt: str) -> pd.DataFrame:
        logger.info(f"find_excel_sheet_with_specialty called with prompt: {prompt}")
        """
        Finds and loads ranking data based only on the specialty if no public/private criterion is provided.

        Args:
            prompt (str): The user's question.

        Returns:
            pd.DataFrame: DataFrame with the relevant specialty data.
        """
        logger.info(f"Finding Excel sheet with specialty for prompt: {prompt}")
        
        matching_rows = self._filter_ranking_by_criteria(self.specialty)
        self.web_ranking_link = []
        self.generate_response_links(matching_rows)
        self.specialty_df = self.load_excel_sheets(matching_rows)
        
        logger.info("Loaded specialty DataFrame")
        return self.specialty_df

    def find_excel_sheet_with_privacy(self, prompt: str, detected_specialty: str = None) -> pd.DataFrame:
        logger.info(f"find_excel_sheet_with_privacy called with prompt: {prompt}, detected_specialty: {detected_specialty}")
        """
        Finds and loads ranking data based on both specialty and institution type.

        Args:
            prompt (str): The user's question.
            detected_specialty (str, optional): Pre-detected specialty from conversation context.

        Returns:
            pd.DataFrame: DataFrame with the relevant filtered data.
        """
        logger.info(f"Finding Excel sheet with privacy for prompt: {prompt}")
        
        self.get_infos(prompt, detected_specialty)
        specialty = self.specialty
        logger.debug(f"Extracted values - specialty: '{specialty}', institution_type: '{self.institution_type}', city: '{self.city}'")
        # Defensive insertion: ensure specialty is never empty or None
        if not specialty or (isinstance(specialty, str) and specialty.strip() == ""):
            specialty = "no specialty match"
        # If no specialty, load general table
        if specialty in ['aucune correspondance', 'no specialty match']:
            logger.debug("No specialty match found, loading general rankings")
            self.generate_response_links()
            institution_type_french = self.institution_type  # Already normalized
            # When institution type is "aucune correspondance", load both public and private rankings
            if institution_type_french == "aucune correspondance":
                category_for_loading = "aucune correspondance"
            else:
                category_for_loading = institution_type_french
            self.specialty_df = self.load_and_transform_for_no_specialty(category=category_for_loading)
            return self.specialty_df
        
        # If no public/private criterion, load by specialty only
        if self.institution_type in ['no match', 'aucune correspondance']:
            logger.debug("No institution type match found, loading by specialty only")
            return self.find_excel_sheet_with_specialty(prompt)

        # Filter rows by specialty and category using helper method
        logger.debug(f"Filtering by both specialty '{specialty}' and institution type '{self.institution_type}'")
        matching_rows = self._filter_ranking_by_criteria(specialty, self.institution_type)
        logger.debug(f"Found {len(matching_rows)} matching rows")
        
        self.generate_response_links(matching_rows)
        self.specialty_df = self.load_excel_sheets(matching_rows)
        
        logger.debug(f"Loaded specialty DataFrame: {type(self.specialty_df)}")
        return self.specialty_df


    def extract_local_hospitals(self, df: pd.DataFrame = None) -> pd.DataFrame:
        logger.info(f"extract_local_hospitals called with df: {type(df)}")
        """
        Merges ranking data with hospital location data to associate each institution with its city and coordinates.

        Args:
            df (pd.DataFrame, optional): DataFrame containing the hospital ranking data.

        Returns:
            pd.DataFrame: DataFrame with city and coordinate information merged.
        """
        logger.info("Merging ranking data with hospital location data")
        institution_coordinates_df = self.institution_coordinates_df[["Etablissement", "Ville", "Latitude", "Longitude"]]
        scores_df = self.specialty_df[["Etablissement", "Catégorie","Note / 20"]]
        self.df_with_cities = pd.merge(institution_coordinates_df, scores_df, on="Etablissement", how="inner")
        self.df_with_cities.rename(columns={"Ville": "City"}, inplace=True)
        logger.debug(f"Merged DataFrame shape (with cities): {self.df_with_cities.shape}")
        return self.df_with_cities
    
    
    def get_df_with_distances(self) -> pd.DataFrame:
        logger.info("get_df_with_distances called")
        """
        Calculates the distances between hospitals and the city specified in the user's query.

        Returns:
            pd.DataFrame or None: DataFrame with distance information, or None if geolocation fails.
        """
        logger.info(f"Calculating distances from query city: {self.city}")
        
        # Get coordinates for the query city
        try:
            query_coords, self.geolocation_api_error = exget_coordinates(self.city)
            if self.geolocation_api_error:
                logger.warning(f"Geolocation failed for city: {self.city}")
                return None
            logger.debug(f"Query city coordinates: {query_coords}")
        except Exception as e:
            logger.error(f"Failed to get coordinates for city {self.city}: {e}")
            self.geolocation_api_error = True
            return None
        
        # Drop rows with missing city info
        initial_count = len(self.df_with_cities)
        self.df_with_cities = self.df_with_cities.dropna(subset=['City'])
        dropped_count = initial_count - len(self.df_with_cities)
        if dropped_count > 0:
            logger.debug(f"Dropped {dropped_count} rows with missing city information")

        # Calculate distance for each hospital/city        
        self.df_with_cities['Distance'] = self.df_with_cities['City'].apply(
            lambda city: distance_to_query(
                query_coords,
                city,
                self.df_with_cities,
                self.geolocation_api_error
            )
        )
        self.df_with_distances = self.df_with_cities
        
        logger.debug(f"DataFrame with distances shape: {self.df_with_distances.shape}")
        return self.df_with_distances


    def create_csv(self, question:str, reponse: str):
        logger.info(f"create_csv called with question: {question}")
        """
        Saves the user's query and the system's response to a CSV file for history tracking.

        Args:
            question (str): The user's question.
            reponse (str): The system's response.
        """

        logger.info(f"Saving Q&A to CSV: question={question}")
        file_name=self.paths["history_path"]
        # Prepare the data dictionary for CSV row
        data = {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "question": question,
            "ville": self.city,
            "type": self.institution_type,
            "spécialité": self.specialty,
            "résultat": reponse,
        }

        file_exists = os.path.exists(file_name)
        # Write to CSV, add header if file does not exist
        try:
            with open(file_name, mode="a", newline="", encoding="utf-8") as file:
                writer = csv.DictWriter(file, fieldnames=data.keys())
                # Write header only if file does not exist yet
                if not file_exists: 
                    writer.writeheader()
                # Write the data row
                writer.writerow(data)
            logger.debug(f"CSV written to {file_name}")
        except Exception as e:
            logger.error(f"Failed to write CSV: {e}")
        return None

