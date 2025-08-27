import os
import pandas as pd
import csv
from datetime import datetime
import unicodedata

from app.config.file_paths_config import PATHS
from app.config.features_config import (PUBLIC_RANKING_URL, PRIVATE_RANKING_URL, INSTITUTION_TYPE_URL_MAPPING, CSV_FIELDNAMES)
from app.services.llm_handler_service import LLMHandler
from app.utility.formatting_helpers import remove_accents
from app.utility.distance_calc_helpers import exget_coordinates, distance_to_query
from app.utility.logging import get_logger


logger = get_logger(__name__)

class DataProcessor:
    """
    Processes hospital ranking data based on user queries. Extracts query information using LLM services, 
    loads and filters ranking data by specialty and institution type, and calculates distances to provide relevant results.

    Attributes:
        paths (dict): Paths to various data files and resources.
        ranking_df (pd.DataFrame): DataFrame containing hospital rankings.
        llm_handler_service (LLMHandler): Service for handling LLM interactions.
        specialty_df (pd.DataFrame): DataFrame for the specific specialty rankings.
        institution_name (str): Name of the institution mentioned in the query.
        specialty_ranking_unavailable (bool): Flag indicating if the specialty ranking is unavailable.      
        web_ranking_link (list): List of generated web links for rankings.
        geolocation_api_error (bool): Flag indicating if there was an error with geolocation API
        specialty (str): Medical specialty extracted from the query.
        institution_type (str): Type of institution (public/private) extracted from the query.
        city (str): City extracted from the query.      
        city_detected (bool): Flag indicating if a city was detected in the query.
        df_with_cities (pd.DataFrame): DataFrame containing hospitals with city information.
        institution_mentioned (str): Institution mentioned in the query.
        number_institutions (int): Number of institutions mentioned in the query.
        weblinks (dict): Predefined links for public and private rankings.
        institution_coordinates_df (pd.DataFrame): DataFrame containing hospital coordinates.
    Methods:
        __init__: Initializes the DataProcessor class, sets up file paths, loads the LLM service, and prepares variables for query processing.
        _load_ranking_dataframe: Loads and prepares a ranking DataFrame with category.
        _generate_web_link: Generates a single web ranking link based on    specialty and institution type.     
        _normalize_str: Normalizes strings for matching.
        _is_no_specialty: Checks if the specialty is empty or no match.
        _parse_specialty_list: Parses multiple specialties from a string.
        _get_institution_list: Returns a formatted, deduplicated list of institutions present in the rankings.
        _filter_ranking_by_criteria: Filters ranking DataFrame by specialty and optionally by institution type.
        get_institution_type_for_url: Converts institution type to format expected by web URLs.
        set_detection_results: Sets detection results from orchestrator.
        generate_response_links: Generates web links to the relevant ranking pages based on specialty and institution type.
        _concat_dataframes: Concatenates a list of DataFrames.
        load_and_transform_for_no_specialty: Loads and merges the general tables (tableau d'honneur) for queries that do not mention a specific specialty.
        load_excel_sheets: Loads the Excel sheets corresponding to the matched specialties and categories.
        find_excel_sheet_with_specialty: Finds and loads ranking data based only on the specialty if no public/private criterion is provided.
        generate_data_response: Main entry point for generating the data response (DataFrame) for a user query.
        extract_local_hospitals: Merges ranking data with hospital location data to associate each institution with its city and coordinates.
        get_df_with_distances: Calculates the distances between hospitals and the city specified in the user's query.
        create_csv: Saves the user's query and the system's response to a CSV file for history tracking.
    """
    
    def __init__(self):
        logger.info("Initializing DataProcessor")
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
        self.city_detected = False
        self.df_with_cities = None
        self.institution_mentioned = None
        self.number_institutions = None
        # Predefined links for public/private rankings
        self.weblinks={
            "public": PUBLIC_RANKING_URL,
            "privé": PRIVATE_RANKING_URL
        }
        try:
            self.institution_coordinates_df = pd.read_excel(self.paths["hospital_coordinates_path"])
        except Exception as e:
            logger.error(f"Failed to load hospital coordinates Excel: {e}")
            raise
    
    
    def _load_ranking_dataframe(self, file_path: str, category: str) -> pd.DataFrame:
        """
        Helper method to load a ranking DataFrame from a CSV file and add the category.
        Args:
            file_path (str): Path to the CSV file containing the ranking data.
            category (str): The category of the ranking (e.g., 'Public', 'Privé').
        Returns:
            pd.DataFrame: DataFrame with the loaded ranking data and category added.
        """
        logger.debug(f"Loading ranking dataframe from {file_path} for category {category}")
        df = pd.read_csv(file_path)
        df['Catégorie'] = category
        df = df.rename(columns={'Score final': 'Note / 20', 'Nom Print': 'Etablissement'})
        logger.debug(f"Loaded {category} rankings: {len(df)} rows")
        return df


    def _generate_web_link(self, specialty: str, institution_type: str) -> str:
        
        """
        Helper method to generate a single web ranking link.
        
        Args:
            specialty: Medical specialty name
            institution_type: Institution type (public/private)
            
        Returns:
            str: Generated web link URL
        """
        logger.debug(f"Generating web link for specialty '{specialty}' and institution_type '{institution_type}'")
        web_link = specialty.replace(' ', '-')
        web_link = f'https://www.lepoint.fr/hopitaux/classements/{web_link}-{institution_type}.php'
        web_link = web_link.lower()
        return remove_accents(web_link)


    def _normalize_str(self, s: str) -> str:
        """
        Utility to normalize strings for matching.
        Args:
            s (str): The string to normalize.
        Returns:
            str: Normalized string, stripped of whitespace and lowercased.  
        """
        logger.debug(f"Normalizing string: {s}")
        if not isinstance(s, str):
            return ""
        s = s.strip().lower()
        s = unicodedata.normalize('NFKD', s)
        s = ''.join(c for c in s if not unicodedata.combining(c))
        return s


    def _is_no_specialty(self, specialty: str) -> bool:
        """
        Utility to check if specialty is empty or no match.
        Args:
            specialty (str): The specialty string to check.
        Returns:
            bool: True if specialty is empty or indicates no match, False otherwise.    
        """
        logger.debug(f"Checking if specialty is 'no match': {specialty}")
        return not specialty or specialty in ["no match", "no specialty match", "aucune correspondance"] or specialty.strip() == ""


    def _parse_specialty_list(self, specialty: str) -> list:
        
        """
        Utility to parse multiple specialties from a string.
        Args:
            specialty (str): The specialty string to parse.
        Returns:
            list: List of individual specialties extracted from the string. 
        """
        logger.debug(f"Parsing specialty list from: {specialty}")
        if specialty.startswith('plusieurs correspondances:'):
            specialty_list = specialty.replace('plusieurs correspondances:', '').strip()
        elif specialty.startswith('multiple matches:'):
            specialty_list = specialty.replace('multiple matches:', '').strip()
        else:
            specialty_list = specialty
        return [s.strip() for s in specialty_list.split(',') if s.strip()]
    

    def _get_institution_list(self):
        """
        Returns a formatted, deduplicated list of institutions present in the rankings.
        Cleans names to avoid duplicates or matching errors.
        Returns:
            str: Comma-separated list of unique institution names.
        """
        logger.info("Getting institution list from coordinates DataFrame")
        column_1 = self.institution_coordinates_df.iloc[:, 0]
        institution_list = [element.split(",")[0] for element in column_1]
        institution_list = list(set(institution_list))
        institution_list = [element for element in institution_list if element not in ("CHU", "CH")]
        institution_list = ", ".join(map(str, institution_list))
        logger.debug(f"Institution list: {institution_list}")
        return institution_list


    def _filter_ranking_by_criteria(self, specialty: str, institution_type: str = None) -> pd.DataFrame:
        
        """
        Helper method to filter ranking DataFrame by specialty and optionally by institution type.
        Normalizes both specialty and data for robust matching.

        Args:       
            specialty (str): The specialty to filter by.
            institution_type (str, optional): The institution type to filter by (e.g., 'Public', 'Privé'). Defaults to None.    

        Returns:
            pd.DataFrame: DataFrame containing rows that match the specified specialty and institution type.    
        """
        logger.info(f"Filtering ranking by criteria: specialty='{specialty}', institution_type='{institution_type}'")
        logger.debug(f"Filtering ranking data - specialty: '{specialty}', institution_type: '{institution_type}'")
        logger.debug(f"Specialty type: {type(specialty)}, length: {len(specialty) if specialty else 'None'}")
        logger.debug(f"Available specialties in ranking data: {self.ranking_df['Spécialité'].unique()}")

        if self._is_no_specialty(specialty):
            logger.debug("No specialty provided or specialty is 'no match', returning empty DataFrame")
            return pd.DataFrame()
        # Normalize the Spécialité column once if not already present
        if 'Spécialité_norm' not in self.ranking_df.columns:
            self.ranking_df['Spécialité_norm'] = self.ranking_df['Spécialité'].apply(self._normalize_str)
        # Debug: Show all normalized specialties in the DataFrame
        logger.debug(f"Normalized specialties in DataFrame: {[repr(s) for s in self.ranking_df['Spécialité_norm'].unique()]}")
        matching_rows = pd.DataFrame()
        # Handle multiple specialties
        if ',' in specialty or specialty.startswith(('plusieurs correspondances:', 'multiple matches:')):
            individual_specialties = self._parse_specialty_list(specialty)
            logger.debug(f"Processing multiple specialties: {individual_specialties}")
            for individual_specialty in individual_specialties:
                if not self._is_no_specialty(individual_specialty):
                    try:
                        norm_spec = self._normalize_str(individual_specialty)
                        logger.debug(f"Normalized specialty from query (multiple): '{repr(norm_spec)}'")
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
                logger.debug(f"Normalized specialty from query: '{repr(specialty_norm)}'")
                matching_rows = self.ranking_df[self.ranking_df['Spécialité_norm'] == specialty_norm]
                logger.debug(f"Found {len(matching_rows)} rows matching single specialty '{specialty}' (normalized: '{specialty_norm}')")
                logger.debug(f"Specialties found after specialty filtering: {matching_rows['Spécialité'].unique()}")
            except Exception as e:
                logger.warning(f"Error filtering by specialty '{specialty}': {e}")
                return pd.DataFrame()
        # Filter by institution type if provided
        if institution_type and institution_type not in ['no match', 'aucune correspondance']:
            # Assume institution_type is already normalized by QueryAnalyst
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
        """
        Convert institution type to format expected by web URLs. Assumes input is already normalized.
        Args:
            institution_type (str): The institution type to convert.
        Returns:
            str: Converted institution type for URL, or the original if not found in mapping.   
        """
        logger.debug(f"Mapping institution type for URL: {institution_type}")
        return INSTITUTION_TYPE_URL_MAPPING.get(institution_type, institution_type.lower())
    
    
    def set_detection_results(self, specialty, city, city_detected, institution_type, number_institutions=None, institution_name=None, institution_mentioned=None):
        """
        Sets detection results from orchestrator.
        Args:
            specialty (str): The medical specialty detected in the query.
            city (str): The city detected in the query.
            city_detected (bool): Flag indicating if a city was detected.
            institution_type (str): The type of institution (public/private) detected.
            number_institutions (int, optional): Number of institutions mentioned in the query.
            institution_name (str, optional): Name of the institution mentioned in the query.
            institution_mentioned (str, optional): Institution mentioned in the query.
        Returns:
            None
        """
        logger.debug(f"set_detection_results: specialty={specialty!r}, city={city!r}, city_detected={city_detected!r}, institution_type={institution_type!r}, number_institutions={number_institutions!r}, institution_name={institution_name!r}, institution_mentioned={institution_mentioned!r}")
        invalid_specialties = ["no match", "no specialty match", "aucune correspondance", ""]
        if specialty not in invalid_specialties and specialty is not None:
            self.specialty = specialty
            logger.debug(f"DataProcessor.specialty set to: {self.specialty!r}")
        else:
            logger.debug(f"Specialty value '{specialty}' is invalid, not overwriting existing specialty: {getattr(self, 'specialty', None)!r}")
        self.city = city
        logger.debug(f"DataProcessor.city set to: {self.city!r}")
        self.city_detected = city_detected
        logger.debug(f"DataProcessor.city_detected set to: {self.city_detected!r}")
        self.institution_type = institution_type
        logger.debug(f"DataProcessor.institution_type set to: {self.institution_type!r}")
        self.number_institutions = number_institutions
        logger.debug(f"DataProcessor.number_institutions set to: {self.number_institutions!r}")
        self.institution_name = institution_name
        logger.debug(f"DataProcessor.institution_name set to: {self.institution_name!r}")
        self.institution_mentioned = institution_mentioned
        logger.debug(f"DataProcessor.institution_mentioned set to: {self.institution_mentioned!r}")
        try:
            self.institution_coordinates_df = pd.read_excel(self.paths["hospital_coordinates_path"])
        except Exception as e:
            logger.error(f"Failed to load hospital coordinates Excel: {e}")
            raise
        self.institution_list = self._get_institution_list()
        # Load ranking data
        try:
            ranking_file_path = self.paths["ranking_file_path"]
            logger.debug(f"Loading ranking data from: {ranking_file_path}")
            if not os.path.exists(ranking_file_path):
                logger.error(f"Ranking file not found: {ranking_file_path}")
                raise FileNotFoundError(f"Ranking file not found: {ranking_file_path}")
            self.ranking_df = pd.read_excel(ranking_file_path, sheet_name="Palmarès")
            logger.debug(f"Loaded ranking DataFrame with {len(self.ranking_df)} rows")
            logger.debug(f"Ranking DataFrame columns: {list(self.ranking_df.columns)}")
        except Exception as e:
            logger.error(f"Failed to load ranking file: {e}")
            raise
        return


    def generate_response_links(self, matching_rows: pd.DataFrame = None) -> list:
        logger.info(f"generate_response_links called with matching_rows: {type(matching_rows)}")
        """
        Generates web links to the relevant ranking pages based on specialty and institution type.

        Args:
            matching_rows (pd.DataFrame, optional): Rows from the ranking sheet that match the query.

        Returns:    
            list: List of generated web links for rankings. 
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
        """
        Utility to concatenate DataFrames.
        Args:   
            dfs (list): List of DataFrames to concatenate.
        Returns:    
            pd.DataFrame: Concatenated DataFrame with inner join and reset index.
        """
        logger.debug(f"Concatenating {len(dfs)} dataframes")
        if not dfs:
            return pd.DataFrame()
        return pd.concat(dfs, join="inner", ignore_index=True)

    def load_and_transform_for_no_specialty(self, category: str) -> pd.DataFrame:
        """
        Loads and merges the general tables (tableau d'honneur) (public and/or private) for queries
            that do not mention a specific specialty.

        Args:
            category (str): The institution category (public/private) requested. 
                        Accepted values: 'aucune correspondance', 'Public', 'Privé'

        Returns:
            pd.DataFrame: The combined DataFrame of relevant institutions.
        """
        logger.info(f"load_and_transform_for_no_specialty called with category: {category}")
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
        """
        Loads the Excel sheets corresponding to the matched specialties and categories.

        Args:
            matching_rows (pd.DataFrame): Rows from the ranking sheet that match the query.

        Returns:
            pd.DataFrame: Concatenated DataFrame of results, or an empty DataFrame if not found.
        """
        logger.info(f"load_excel_sheets called with matching_rows of length: {len(matching_rows) if matching_rows is not None else 'None'}")

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


    def generate_data_response(self) -> pd.DataFrame:
        """
        Main entry point for generating the data response (DataFrame) for a user query. Assumes detection results have already been set.
        Returns:
            pd.DataFrame: DataFrame with the relevant filtered data.
        """
        logger.info("generate_data_response called")
        specialty = self.specialty
        institution_type = self.institution_type
        logger.debug(f"Extracted values - specialty: '{specialty}', institution_type: '{institution_type}', city: '{self.city}'")

        # Defensive: ensure specialty is never empty or None
        if not specialty or (isinstance(specialty, str) and specialty.strip() == ""):
            specialty = "no specialty match"

        # If no specialty, load general table
        if specialty in ['aucune correspondance', 'no specialty match']:
            logger.debug("No specialty match found, loading general rankings")
            self.generate_response_links()
            institution_type_french = institution_type  # Already normalized
            if institution_type_french == "aucune correspondance":
                category_for_loading = "aucune correspondance"
            else:
                category_for_loading = institution_type_french
            self.specialty_df = self.load_and_transform_for_no_specialty(category=category_for_loading)
            return self.specialty_df

        # If no public/private criterion, load by specialty only
        if institution_type in ['no match', 'aucune correspondance']:
            logger.debug("No institution type match found, loading by specialty only")
            matching_rows = self._filter_ranking_by_criteria(specialty)
            self.web_ranking_link = []
            self.generate_response_links(matching_rows)
            self.specialty_df = self.load_excel_sheets(matching_rows)
            logger.info("Loaded specialty DataFrame")
            return self.specialty_df

        # Filter rows by specialty and category using helper method
        logger.debug(f"Filtering by both specialty '{specialty}' and institution type '{institution_type}'")
        matching_rows = self._filter_ranking_by_criteria(specialty, institution_type)
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
        # Skip geolocation if no city is detected
        if not self.city_detected or not self.city:
            logger.info("No city detected, skipping geolocation and returning DataFrame without distances.")
            # Defensive: always add a Distance column filled with None if missing
            if self.df_with_cities is not None and 'Distance' not in self.df_with_cities.columns:
                self.df_with_cities['Distance'] = None
            return self.df_with_cities

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

        # Log cities/hospitals with None in Distance
        none_distance_rows = self.df_with_cities[self.df_with_cities['Distance'].isnull()]
        if not none_distance_rows.empty:
            logger.warning(f"Rows with None in Distance after calculation: {none_distance_rows[['Etablissement', 'City']]}")

        # Strictly filter out all rows with None in Distance
        self.df_with_distances = self.df_with_cities[self.df_with_cities['Distance'].notnull()]

        logger.debug(f"DataFrame with distances shape after filtering: {self.df_with_distances.shape}")
        logger.debug(f"Distance column values after filtering: {self.df_with_distances['Distance'].tolist()}")
        return self.df_with_distances


    

    def create_csv(self, result_data: dict):
        """
        Saves the user's query and the system's response (and metadata) to a CSV file for history tracking.

        Args:
            data (dict): Dictionary where keys are column names and values are cell values.
        Returns:
            None
        """
        logger.info(f"Saving Q&A to CSV: {result_data.get('question','')}")
        file_name = self.paths["history_path"]
        file_exists = os.path.exists(file_name)
        # Fill missing columns with empty string
        for col in CSV_FIELDNAMES:
            if col not in result_data:
                result_data[col] = ""
        try:
            with open(file_name, mode="a", newline="", encoding="utf-8") as file:
                writer = csv.DictWriter(file, fieldnames=CSV_FIELDNAMES)
                if not file_exists:
                    writer.writeheader()
                writer.writerow(result_data)
            logger.debug(f"CSV written to {file_name}")
        except Exception as e:
            logger.error(f"Failed to write CSV: {e}")
        return None

