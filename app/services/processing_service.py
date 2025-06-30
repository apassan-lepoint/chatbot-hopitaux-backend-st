"""
Service for processing and transforming hospital ranking data.

This file defines the Processing class, which loads, merges, and filters ranking and
    location data, and prepares results for the chatbot pipeline.
"""

import os
import pandas as pd
import csv
from datetime import datetime

from app.utils.query_detection.institutions import coordinates_df
from app.utils.config import PATHS
from app.services.llm_service import LLMService
from app.utils.formatting import enlever_accents
from app.utils.distance import exget_coordinates, get_coordinates, distance_to_query
from app.utils.logging import get_logger
logger = get_logger(__name__)

class Processing:
    """
    Handles the processing of user queries related to hospital and clinic rankings.
    
    This includes extracting relevant information using the LLM, loading and transforming ranking data, 
        merging with location data, and saving query history.
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
        self.ranking_not_found = False
        self.web_ranking_link = None
        self.geopy_problem = False
        self.coordinates_df = coordinates_df
        
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
           
    def get_infos(self, prompt: str) -> None:
        """
        Extracts key aspects from the user's question: city, institution type (public/private), and medical specialty. 
        
        Updates instance variables accordingly.

        Args:
            prompt (str): The user's question.
        """
        logger.info(f"Extracting infos from prompt: {prompt}")
        
        self.specialty = self.llm_service.detect_specialty(prompt)
        self.city = self.llm_service.detect_city(prompt)
        self.institution_type = self.llm_service.detect_institution_type(prompt)
        self.institution_mentioned = self.llm_service.institution_mentioned 
        self.institution_name = self.llm_service.institution_name  
        self.ranking_df = pd.read_excel(self.paths["ranking_file_path"], sheet_name="Palmarès")
        logger.debug(f"Extracted specialty: {self.specialty}, city: {self.city}, type: {self.institution_type}")
        
    
        return None

    def generate_response_links(self, matching_rows: str = None) -> str:
        """
        Generates web links to the relevant ranking pages based on specialty and institution type.

        Args: CHECK IF STR OR DATAFRAME!!!!
            matching_rows (str, optional): Rows from the ranking sheet that match the query.

        Returns:
            list or None: List of generated URLs or None if not applicable.
        """

        logger.info("Generating ranking links")
        
        self.web_ranking_link=[]

        # If no specialty, suggest general ranking links
        if self.specialty== 'aucune correspondance':
            if self.institution_type == 'Public':
                self.web_ranking_link=[self.weblinks["public"]]
            elif self.institution_type == 'Privé':
                self.web_ranking_link=[self.weblinks["privé"]]
            else:
                self.web_ranking_link=[self.weblinks["public"],self.weblinks["privé"]]
            return None
        etat = self.institution_type
        
        # If ranking not found, suggest the opposite type
        if self.ranking_not_found==True:
            if self.institution_type == 'Public':
                etat='prive'
            if self.institution_type == 'Privé':
                etat='public'
            web_ranking_link = self.specialty.replace(' ', '-')
            web_ranking_link='https://www.lepoint.fr/hopitaux/classements/'+ web_ranking_link + '-'+etat+'.php'
            web_ranking_link=web_ranking_link.lower()
            web_ranking_link=enlever_accents(web_ranking_link)
            self.web_ranking_link.append(web_ranking_link)
            return self.web_ranking_link

        # Generate links for each matching specialty/category row
        for _, row in matching_rows.iterrows():
            web_ranking_link = row["Spécialité"].replace(' ', '-')
            web_ranking_link='https://www.lepoint.fr/hopitaux/classements/'+ web_ranking_link + '-'+row["Catégorie"] +'.php'
            web_ranking_link=web_ranking_link.lower()
            web_ranking_link=enlever_accents(web_ranking_link)
            self.web_ranking_link.append(web_ranking_link)
        
        logger.info(f"Generated ranking links: {self.web_ranking_link}")
        return self.web_ranking_link

    def load_and_transform_for_no_specialty(self, category: str) -> pd.DataFrame:
        """
        Loads and merges the general tables (tableau d'honneur) (public and/or private) for queries
            that do not mention a specific specialty.

        Args:
            category (str): The institution category (public/private) requested.

        Returns:
            pd.DataFrame: The combined DataFrame of relevant institutions.
        """
        
        logger.info(f"Loading and transforming data for category: {category}")
        
        dfs=[]
        
        # Load both public and private rankings if no specific category is requested
        if category== 'aucune correspondance':
            df_private=pd.read_csv(self.paths["ranking_overall_private_path"] )
            df_private['Catégorie']='Privé'
            dfs.append(df_private)
            
            df_public=pd.read_csv(self.paths["ranking_overall_public_path"] )
            df_public['Catégorie']='Public'
            dfs.append(df_public)

            df= pd.concat(dfs, join="inner", ignore_index=True)
        
        elif category == 'Public':
            df = pd.read_csv(self.paths["ranking_overall_public_path"])
            df['Catégorie'] = 'Public'
        elif category == 'Privé':
            df = pd.read_csv(self.paths["ranking_overall_private_path"])
            df['Catégorie'] = 'Privé'
        else:
            raise ValueError(f"Unknown category: {category}")
        
        # Rename columns for consistency
        df = df.rename(columns={'Score final': 'Note / 20', 'Nom Print': 'Etablissement'})

        logger.debug(f"Loaded DataFrame shape (no specialty): {df.shape}")
        return df
    
    def load_excel_sheets(self, matching_rows: pd.DataFrame) -> pd.DataFrame:
        """
        Loads the Excel sheets corresponding to the matched specialties and categories.

        Args:
            matching_rows (pd.DataFrame): Rows from the ranking sheet that match the query.

        Returns:
            pd.DataFrame or list: Concatenated DataFrame of results, or a message if not found.
        """
        
        logger.info("Loading Excel sheets for matched specialties/categories")
        
        dfs = []
        
        # Load each sheet for the matched specialty/category
        for _, row in matching_rows.iterrows():
            logger.debug(f"Loading sheet: {row.iloc[2]} for category: {row['Catégorie']}")
            sheet_name = row.iloc[2]
            category = row["Catégorie"]
            df_sheet = pd.read_excel(self.paths["ranking_file_path"] , sheet_name=sheet_name)
            df_sheet["Catégorie"] = category
            dfs.append(df_sheet)

        if dfs:
            logger.info(f"Loaded {len(dfs)} sheets, concatenating results")
            logger.debug(f"Concatenated DataFrame shape: {pd.concat(dfs, join='inner', ignore_index=True).shape}")
            return pd.concat(dfs, join="inner", ignore_index=True)
        else:
            logger.warning("No matching sheets found for specialties/categories")
            if self.specialty!= 'aucune correspondance' and self.institution_type!='aucune correspondance':
                res=[]
                res.append("Nous n'avons pas d'établissement de ce type pour cette pathologie")
                self.ranking_not_found=True
                return res

    def find_excel_sheet_with_speciality(self, prompt: str) -> pd.DataFrame:
        """
        Finds and loads ranking data based only on the specialty if no public/private criterion is provided.

        Args:
            prompt (str): The user's question.

        Returns:
            pd.DataFrame: DataFrame with the relevant specialty data.
        """
        logger.info(f"Finding Excel sheet with specialty for prompt: {prompt}")
        
        matching_rows = self.ranking_df[self.ranking_df["Spécialité"].str.contains(self.specialty, case=False, na=False)]
        self.web_ranking_link=[]
        self.generate_response_links(matching_rows)
        self.specialty_df = self.load_excel_sheets(matching_rows)
        
        logger.info("Loaded specialty DataFrame")
        return self.specialty_df

    def find_excel_sheet_with_privacy(self,prompt: str) -> pd.DataFrame:
        """
        Finds and loads ranking data based on both specialty and institution type.

        Args:
            prompt (str): The user's question.

        Returns:
            pd.DataFrame: DataFrame with the relevant filtered data.
        """
        
        logger.info(f"Finding Excel sheet with privacy for prompt: {prompt}")
        
        self.get_infos(prompt)
        specialty=self.specialty
        
        # Defensive insertion: ensure specialty is never empty or None
        if not specialty or (isinstance(specialty, str) and specialty.strip() == ""):
            specialty = "aucune correspondance"
        
        # If no specialty, load general table
        if specialty== 'aucune correspondance':
            self.generate_response_links()
            self.specialty_df=self.load_and_transform_for_no_specialty(category=self.institution_type)
            return self.specialty_df
        
        # If no public/private criterion, load by specialty only
        if self.institution_type == 'aucune correspondance':
            return self.find_excel_sheet_with_speciality(prompt)

         # Filter rows by specialty and category
        matching_rows = self.ranking_df[self.ranking_df["Spécialité"].str.contains(specialty, case=False, na=False)]
        matching_rows = matching_rows[matching_rows["Catégorie"].str.contains(self.institution_type, case=False, na=False)]
        self.generate_response_links(matching_rows)
        self.specialty_df = self.load_excel_sheets(matching_rows)
        
        logger.debug(f"Loaded specialty DataFrame: {self.specialty_df}")
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
        coordinates_df = self.coordinates_df[["Etablissement", "Ville", "Latitude", "Longitude"]]
        scores_df = self.specialty_df[["Etablissement", "Catégorie","Note / 20"]]
        self.df_with_cities = pd.merge(coordinates_df, scores_df, on="Etablissement", how="inner")
        self.df_with_cities.rename(columns={"Ville": "City"}, inplace=True)
        logger.debug(f"Merged DataFrame shape (with cities): {self.df_with_cities.shape}")
        return self.df_with_cities
    
    def get_df_with_distances(self) -> pd.DataFrame:
        """
        Calculates the distances between hospitals and the city specified in the user's query.

        Returns:
            pd.DataFrame or None: DataFrame with distance information, or None if geolocation fails.
        """

        logger.info("Calculating distances to query city")
        
        # Get coordinates for the query city
        query_coords, self.geopy_problem = exget_coordinates(self.city)
        if self.geopy_problem:
            return None
        
        # Drop rows with missing city info
        self.df_with_cities = self.df_with_cities.dropna(subset=['City'])

        # Helper function for distance calculation (not used in lambda, but kept for clarity)
        def _distance(city):
            city_coords = get_coordinates(self.df_with_cities, city)
            return distance_to_query(query_coords, city_coords, city, self.df_with_cities, self.geopy_problem)
        
        # Calculate distance for each hospital/city        
        self.df_with_cities['Distance'] = self.df_with_cities['City'].apply(
            lambda city: distance_to_query(
                query_coords,
                city,
                self.df_with_cities,
                self.geopy_problem
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
