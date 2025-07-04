"""
Service for processing and transforming hospital ranking data.

This file defines the Processing class, which loads, merges, and filters ranking and
    location data, and prepares results for the chatbot pipeline.
"""

import os
import pandas as pd
import csv
from datetime import datetime

from app.utils.query_detection.institutions import institution_coordinates_df
from app.utils.config import PATHS
from app.services.llm_service import LLMService
from app.utils.formatting import remove_accents
from app.utils.distance import exget_coordinates, get_coordinates, distance_to_query
from app.utils.logging import get_logger
logger = get_logger(__name__)

class Processing:
    """
    Processes hospital ranking data based on user queries. Extracts query information using LLM services, 
    loads and filters ranking data by specialty and institution type, and calculates distances to provide relevant results.
    
    Attributes:
        ranking_df (pd.DataFrame | None): Main DataFrame containing hospital rankings from Excel.
        llm_service (LLMService): Service instance for extracting information from user queries.
        specialty_df (pd.DataFrame | None): Filtered DataFrame for specific medical specialties.
        institution_name (str | None): Name of specific institution mentioned in query.
        specialty_ranking_unavailable (bool): Flag indicating if requested ranking data was not found.
        web_ranking_link (list | None): Generated URLs to relevant online ranking pages.
        geolocation_api_error (bool): Flag indicating geolocation service issues.
        institution_coordinates_df (pd.DataFrame): Reference DataFrame with institution coordinates.
        weblinks (dict): Predefined URLs for public and private general rankings.
        specialty (str | None): Medical specialty extracted from user query.
        institution_type (str | None): Institution category ('Public'/'Privé') from query.
        city (str | None): City or department name extracted from user query.
        df_with_cities (pd.DataFrame | None): Rankings merged with location data.
        institution_mentioned (str | None): Institution name mentioned in query.
        paths (dict): Configuration dictionary containing file paths.
    """
    
    def __init__(self):
        """
        Initializes the Processing class, sets up file paths, loads the LLM service, and prepares variables 
        for query processing.
        """
        self.ranking_df = None
        self.llm_service = LLMService()
        self.specialty_df = None
        self.institution_name = None
        self.specialty_ranking_unavailable = False
        self.web_ranking_link = None
        self.geolocation_api_error = False
        self.institution_coordinates_df = institution_coordinates_df
        
        # Predefined links for public/private rankings
        self.weblinks={
                "public":"https://www.lepoint.fr/hopitaux/classements/tableau-d-honneur-public.php",
                "privé":"https://www.lepoint.fr/hopitaux/classements/tableau-d-honneur-prive.php"
        }
        
        self.specialty= None
        self.institution_type= None
        self.city = None
        self.df_with_cities = None
        self.institution_mentioned = None
        
        self.paths= PATHS
    
    
    def _load_ranking_dataframe(self, file_path: str, category: str) -> pd.DataFrame:
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

    def _filter_ranking_by_criteria(self, specialty: str, institution_type: str = None) -> pd.DataFrame:
        """
        Helper method to filter ranking DataFrame by specialty and optionally by institution type.
        
        Args:
            specialty: Medical specialty to filter by (can be a single specialty or comma-separated list)
            institution_type: Institution type to filter by (optional)
            
        Returns:
            pd.DataFrame: Filtered DataFrame
        """
        logger.debug(f"Filtering ranking data - specialty: '{specialty}', institution_type: '{institution_type}'")
        logger.debug(f"Available specialties in ranking data: {self.ranking_df['Spécialité'].unique()}")
        
        # Handle cases where specialty is not provided or is "no match"
        if not specialty or specialty == "no match" or specialty.strip() == "":
            logger.debug("No specialty provided or specialty is 'no match', returning empty DataFrame")
            return pd.DataFrame()
        
        # Handle multiple specialties (comma-separated or special format)
        if specialty and (',' in specialty or specialty.startswith(('plusieurs correspondances:', 'multiple matches:'))):
            # Extract individual specialties
            if specialty.startswith('plusieurs correspondances:'):
                # Remove the prefix and get the specialty list
                specialty_list = specialty.replace('plusieurs correspondances:', '').strip()
            elif specialty.startswith('multiple matches:'):
                # Remove the prefix and get the specialty list
                specialty_list = specialty.replace('multiple matches:', '').strip()
            else:
                specialty_list = specialty
            
            # Split by comma and clean each specialty
            individual_specialties = [s.strip() for s in specialty_list.split(',') if s.strip()]
            logger.debug(f"Processing multiple specialties: {individual_specialties}")
            
            # Find matching rows for any of the specialties
            matching_rows = pd.DataFrame()
            for individual_specialty in individual_specialties:
                if individual_specialty and individual_specialty != "no match":  # Skip empty strings and "no match"
                    try:
                        specialty_matches = self.ranking_df[
                            self.ranking_df["Spécialité"].str.contains(individual_specialty, case=False, na=False)
                        ]
                        if len(specialty_matches) > 0:
                            matching_rows = pd.concat([matching_rows, specialty_matches], ignore_index=True)
                    except Exception as e:
                        logger.warning(f"Error filtering by specialty '{individual_specialty}': {e}")
                        continue
            
            # Remove duplicates
            matching_rows = matching_rows.drop_duplicates()
            logger.debug(f"Found {len(matching_rows)} rows matching multiple specialties")
        else:
            # Single specialty matching
            try:
                matching_rows = self.ranking_df[self.ranking_df["Spécialité"].str.contains(specialty, case=False, na=False)]
                logger.debug(f"Found {len(matching_rows)} rows matching single specialty '{specialty}'")
            except Exception as e:
                logger.warning(f"Error filtering by specialty '{specialty}': {e}")
                return pd.DataFrame()
        
        if institution_type:
            institution_type_french = self.normalize_institution_type(institution_type)
            logger.debug(f"Filtering by institution type: '{institution_type}' -> '{institution_type_french}'")
            logger.debug(f"Available categories in ranking data: {self.ranking_df['Catégorie'].unique()}")
            
            if institution_type_french != "no match":
                try:
                    matching_rows = matching_rows[matching_rows["Catégorie"].str.contains(institution_type_french, case=False, na=False)]
                    logger.debug(f"Found {len(matching_rows)} rows after filtering by institution type")
                except Exception as e:
                    logger.warning(f"Error filtering by institution type '{institution_type_french}': {e}")
        
        return matching_rows

    def normalize_institution_type(self, institution_type: str) -> str:
        """
        Automatically normalize institution type to French format used in data.
        Handles both English and French input, returns standardized French format.
        """
        if not institution_type or institution_type == "no match":
            return "no match"
            
        # Convert to lowercase for comparison
        type_lower = institution_type.lower().strip()
        logger.debug(f"Normalizing institution type: '{institution_type}' -> '{type_lower}'")
        
        # Mapping of all possible variations to standardized French
        type_mapping = {
            # English variations
            "public": "Public",
            "private": "Privé",
            
            # French variations (ensure consistency)
            "privé": "Privé",    # lowercase French with accent
            "prive": "Privé",    # lowercase French without accent
            
            # Handle common variations
            "publique": "Public",
            "privée": "Privé"
        }
        
        normalized = type_mapping.get(type_lower, institution_type)
        logger.debug(f"Normalized institution type: '{institution_type}' -> '{normalized}'")
        return normalized
    
    def get_institution_type_for_url(self, institution_type: str) -> str:
        """Convert institution type to format expected by web URLs."""
        normalized = self.normalize_institution_type(institution_type)
        
        url_mapping = {
            "Public": "public",
            "Privé": "prive",
            "no match": "no match"
        }
        
        return url_mapping.get(normalized, normalized.lower())
    
    
    def get_infos(self, prompt: str, detected_specialty: str = None) -> None:
        """
        Extracts key aspects from the user's question: city, institution type (public/private), and medical specialty. 
        
        Updates instance variables accordingly.

        Args:
            prompt (str): The user's question.
            detected_specialty (str, optional): Pre-detected specialty from conversation context.
        """
        logger.info(f"Extracting infos from prompt: {prompt}")
        
        # Use provided specialty or detect it
        if detected_specialty:
            logger.info(f"Using provided specialty from context: {detected_specialty}")
            self.specialty = detected_specialty
        else:
            self.specialty = self.llm_service.detect_specialty(prompt)
        
        self.city = self.llm_service.detect_city(prompt)
        self.institution_type = self.llm_service.detect_institution_type(prompt)
        self.topk = self.llm_service.detect_topk(prompt)
        
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
            logger.error(f"Failed to load ranking data: {e}")
            raise
        
        self.institution_mentioned = self.llm_service.institution_mentioned 
        self.institution_name = self.llm_service.institution_name  
        logger.debug(f"Extracted specialty: '{self.specialty}', city: '{self.city}', type: '{self.institution_type}'")
    
        return None


    def generate_response_links(self, matching_rows: pd.DataFrame = None) -> list:
        """
        Generates web links to the relevant ranking pages based on specialty and institution type.

        Args:
            matching_rows (pd.DataFrame, optional): Rows from the ranking sheet that match the query.

        Returns:
            list or None: List of generated URLs or None if not applicable.
        """
        logger.info("Generating ranking links")
        self.web_ranking_link = []

        # If no specialty, suggest general ranking links
        if self.specialty == 'no match' or not self.specialty:
            logger.debug("No specialty detected, generating general ranking links")
            institution_type_french = self.normalize_institution_type(self.institution_type)
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
            institution_type_french = self.normalize_institution_type(self.institution_type)
            opposite_type = 'prive' if institution_type_french == 'Public' else 'public'
            
            # Handle multiple specialties for opposite type links
            if self.specialty and (',' in self.specialty or self.specialty.startswith(('plusieurs correspondances:', 'multiple matches:'))):
                # Extract first specialty for the opposite type link
                if self.specialty.startswith('plusieurs correspondances:'):
                    specialty_list = self.specialty.replace('plusieurs correspondances:', '').strip()
                elif self.specialty.startswith('multiple matches:'):
                    specialty_list = self.specialty.replace('multiple matches:', '').strip()
                else:
                    specialty_list = self.specialty
                
                first_specialty = specialty_list.split(',')[0].strip()
                web_link = self._generate_web_link(first_specialty, opposite_type)
                self.web_ranking_link.append(web_link)
            else:
                web_link = self._generate_web_link(self.specialty, opposite_type)
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


    def load_and_transform_for_no_specialty(self, category: str) -> pd.DataFrame:
        """
        Loads and merges the general tables (tableau d'honneur) (public and/or private) for queries
            that do not mention a specific specialty.

        Args:
            category (str): The institution category (public/private) requested. 
                          Accepted values: 'no specialty match', 'Public', 'Privé'

        Returns:
            pd.DataFrame: The combined DataFrame of relevant institutions.
        """
        logger.info(f"Loading general rankings for category: {category}")
        
        try:
            if category == 'no specialty match':
                logger.debug("Loading both public and private rankings")
                df_private = self._load_ranking_dataframe(self.paths["ranking_overall_private_path"], 'Privé')
                df_public = self._load_ranking_dataframe(self.paths["ranking_overall_public_path"], 'Public')
                df = pd.concat([df_private, df_public], join="inner", ignore_index=True)
            elif category == 'Public':
                logger.debug("Loading public rankings only")
                df = self._load_ranking_dataframe(self.paths["ranking_overall_public_path"], 'Public')
            elif category == 'Privé':
                logger.debug("Loading private rankings only")
                df = self._load_ranking_dataframe(self.paths["ranking_overall_private_path"], 'Privé')
            else:
                raise ValueError(f"Unknown category: {category}")
            
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
            pd.DataFrame or list: Concatenated DataFrame of results, or a message if not found.
        """
        
        logger.info(f"Loading Excel sheets for {len(matching_rows)} matched specialties/categories")
        
        if len(matching_rows) == 0:
            logger.warning("No matching rows provided to load_excel_sheets")
            if self.specialty != 'no match' and self.institution_type != 'no match':
                res = []
                res.append("Nous n'avons pas d'établissement de ce type pour cette pathologie")
                self.specialty_ranking_unavailable = True
                return res
        
        dfs = []
        
        # Load each sheet for the matched specialty/category
        for index, row in matching_rows.iterrows():
            sheet_name = row.iloc[2]  # Assuming sheet name is in the 3rd column
            category = row["Catégorie"]
            logger.debug(f"Loading sheet: '{sheet_name}' for category: '{category}'")
            
            try:
                df_sheet = pd.read_excel(self.paths["ranking_file_path"], sheet_name=sheet_name)
                df_sheet["Catégorie"] = category
                dfs.append(df_sheet)
                logger.debug(f"Sheet '{sheet_name}' loaded successfully with {len(df_sheet)} rows")
            except Exception as e:
                logger.warning(f"Failed to load sheet '{sheet_name}': {e}")
                continue

        if dfs:
            concatenated_df = pd.concat(dfs, join="inner", ignore_index=True)
            logger.info(f"Successfully loaded {len(dfs)} sheets, total rows: {len(concatenated_df)}")
            return concatenated_df
        else:
            logger.warning("No matching sheets found for specialties/categories")
            if self.specialty != 'no match' and self.institution_type != 'no match':
                res = []
                res.append("Nous n'avons pas d'établissement de ce type pour cette pathologie")
                self.specialty_ranking_unavailable = True
                return res


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

    def find_excel_sheet_with_privacy(self, prompt: str, detected_specialty: str = None) -> pd.DataFrame:
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
        if specialty == 'no specialty match':
            logger.debug("No specialty match found, loading general rankings")
            self.generate_response_links()
            institution_type_french = self.normalize_institution_type(self.institution_type)
            self.specialty_df = self.load_and_transform_for_no_specialty(category=institution_type_french)
            return self.specialty_df
        
        # If no public/private criterion, load by specialty only
        if self.institution_type == 'no match':
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
        """
        Saves the user's query and the system's response to a CSV file for history tracking.

        Args:
            question (str): The user's question.
            reponse (str): The system's response.
        """

        logger.info(f"Saving Q&A to CSV: question={question}")
        file_name=self.paths["history_path"]
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
        with open(file_name, mode="a", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=data.keys())
            if not file_exists: 
                writer.writeheader()
            writer.writerow(data)
        
        logger.debug(f"CSV written to {file_name}")
        
        return None

    def _normalize_specialty_format(self, specialty: str) -> str:
        """
        Normalize specialty format to handle both French and English formats consistently.
        
        Args:
            specialty (str): The specialty string to normalize
            
        Returns:
            str: Normalized specialty string
        """
        if not specialty:
            return ""
            
        # Convert French format to English format for consistency
        if specialty.startswith("plusieurs correspondances:"):
            return specialty.replace("plusieurs correspondances:", "multiple matches:")
        
        # Handle common no-match cases
        if specialty in ["aucune correspondance", "no match"]:
            return "no specialty match"
            
        return specialty

    def _extract_specialty_list(self, specialty: str) -> list:
        """
        Extract list of individual specialties from formatted specialty string.
        
        Args:
            specialty (str): The specialty string (single or multiple)
            
        Returns:
            list: List of individual specialty strings
        """
        if not specialty:
            return []
            
        # Normalize format first
        normalized_specialty = self._normalize_specialty_format(specialty)
        
        # Handle multiple specialties
        if ',' in normalized_specialty or normalized_specialty.startswith('multiple matches:'):
            if normalized_specialty.startswith('multiple matches:'):
                specialty_list = normalized_specialty.replace('multiple matches:', '').strip()
            else:
                specialty_list = normalized_specialty
            
            # Split by comma and clean each specialty
            return [s.strip() for s in specialty_list.split(',') if s.strip()]
        else:
            # Single specialty
            return [normalized_specialty] if normalized_specialty else []
