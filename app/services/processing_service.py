"""
Service for processing and transforming hospital ranking data.

This file defines the Processing class, which loads, merges, and filters ranking and
    location data, and prepares results for the chatbot pipeline.
"""

import os
import re
import pandas as pd
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import time
import unicodedata
import csv
from datetime import datetime

from app.config import PATHS
from app.services.llm_service import Appels_LLM
from app.utils.formatting import enlever_accents
from app.utils.distance import exget_coordinates, get_coordinates, distance_to_query


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
        
        self.palmares_df = None
        self.appel_LLM = Appels_LLM()
        self.specialty_df = None
        self.etablissement_name = None
        self.classement_non_trouve = False
        self.lien_classement_web = None
        self.geopy_problem = False
        
        self.weblinks={
                "public":"https://www.lepoint.fr/hopitaux/classements/tableau-d-honneur-public.php",
                "privé":"https://www.lepoint.fr/hopitaux/classements/tableau-d-honneur-prive.php"
        }
        
        self.specialty= None
        self.ispublic= None
        self.city = None
        self.df_with_cities = None
        self.établissement_mentionné = None
        
        self.paths= PATHS
           
    def get_infos(self, prompt: str) -> None:
        """
        Extracts key aspects from the user's question: city, institution type (public/private), and medical specialty. 
        
        Updates instance variables accordingly.

        Args:
            prompt (str): The user's question.
        """
        if self.specialty is None:
            self.appel_LLM.get_speciality(prompt)
            self.palmares_df=pd.read_excel(self.paths["palmares_path"] , sheet_name="Palmarès")
            self.specialty=self.appel_LLM.specialty
        self.palmares_df=pd.read_excel(self.paths["palmares_path"] , sheet_name="Palmarès")
        self.appel_LLM.get_city(prompt)
        self.city=self.appel_LLM.city
        self.appel_LLM.is_public_or_private(prompt)
        self.établissement_mentionné = self.appel_LLM.établissement_mentionné
        self.etablissement_name=self.appel_LLM.etablissement_name
        self.ispublic=self.appel_LLM.ispublic
        return None

    def _generate_lien_classement(self, matching_rows: str = None) -> str:
        """
        Generates web links to the relevant ranking pages based on specialty and institution type.

        Args: CHECK IF STR OR DATAFRAME!!!!
            matching_rows (str, optional): Rows from the ranking sheet that match the query.

        Returns:
            list or None: List of generated URLs or None if not applicable.
        """

        self.lien_classement_web=[]

        if self.specialty== 'aucune correspondance':
            # Suggest general ranking links if no specialty is found
            if self.ispublic == 'Public':
                self.lien_classement_web=[self.weblinks["public"]]
            elif self.ispublic == 'Privé':
                self.lien_classement_web=[self.weblinks["privé"]]
            else:
                self.lien_classement_web=[self.weblinks["public"],self.weblinks["privé"]]
            return None
        etat = self.ispublic
        if self.classement_non_trouve==True:
            # Suggest the opposite type if no ranking is found for the requested type
            if self.ispublic == 'Public':
                etat='prive'
            if self.ispublic == 'Privé':
                etat='public'
            lien_classement_web = self.specialty.replace(' ', '-')
            lien_classement_web='https://www.lepoint.fr/hopitaux/classements/'+ lien_classement_web + '-'+etat+'.php'
            lien_classement_web=lien_classement_web.lower()
            lien_classement_web=enlever_accents(lien_classement_web)
            self.lien_classement_web.append(lien_classement_web)
            return self.lien_classement_web

        for _, row in matching_rows.iterrows():
            lien_classement_web = row["Spécialité"].replace(' ', '-')
            lien_classement_web='https://www.lepoint.fr/hopitaux/classements/'+ lien_classement_web + '-'+row["Catégorie"] +'.php'
            lien_classement_web=lien_classement_web.lower()
            lien_classement_web=enlever_accents(lien_classement_web)
            self.lien_classement_web.append(lien_classement_web)
        return self.lien_classement_web

    def _load_and_transform_for_no_specialty(self, category: str) -> pd.DataFrame:
        """
        Loads and merges the general tables (tableau d'honneur) (public and/or private) for queries
            that do not mention a specific specialty.

        Args:
            category (str): The institution category (public/private) requested.

        Returns:
            pd.DataFrame: The combined DataFrame of relevant institutions.
        """
        
        if category== 'aucune correspondance':
            dfs=[]

            df_private=pd.read_csv(self.paths["palmares_general_private_path"] )
            df_private['Catégorie']='Privé'
            dfs.append(df_private)
            
            df_public=pd.read_csv(self.paths["palmares_general_public_path"] )
            df_public['Catégorie']='Public'
            dfs.append(df_public)

            df= pd.concat(dfs, join="inner", ignore_index=True)
        
        if category == 'Public':
            csv_path=self.paths["palmares_general_public_path"]
            df = pd.read_csv(csv_path)
            df['Catégorie'] = category
        elif category == 'Privé':
            csv_path=self.paths["palmares_general_private_path"]
            df = pd.read_csv(csv_path)
            df['Catégorie'] = category
        
        df = df.rename(columns={'Score final': 'Note / 20', 'Nom Print': 'Etablissement'})
    
        return df
    
    def load_excel_sheets(self, matching_rows: pd.DataFrame) -> pd.DataFrame:
        """
        Loads the Excel sheets corresponding to the matched specialties and categories.

        Args:
            matching_rows (pd.DataFrame): Rows from the ranking sheet that match the query.

        Returns:
            pd.DataFrame or list: Concatenated DataFrame of results, or a message if not found.
        """
        
        excel_path = self.paths["palmares_path"] 
        dfs = []
        for _, row in matching_rows.iterrows():
            sheet_name = row.iloc[2]
            category = row["Catégorie"]
            df_sheet = pd.read_excel(self.paths["palmares_path"] , sheet_name=sheet_name)
            df_sheet["Catégorie"] = category
            dfs.append(df_sheet)

        if dfs:
            return pd.concat(dfs, join="inner", ignore_index=True)
        else:
            if self.specialty!= 'aucune correspondance' and self.ispublic!='aucune correspondance':
                res=[]
                res.append("Nous n'avons pas d'établissement de ce type pour cette pathologie")
                self.classement_non_trouve=True
                return res

    def find_excel_sheet_with_speciality(self, prompt: str) -> pd.DataFrame:
        """
        Finds and loads ranking data based only on the specialty if no public/private criterion is provided.

        Args:
            prompt (str): The user's question.

        Returns:
            pd.DataFrame: DataFrame with the relevant specialty data.
        """
        
        matching_rows = self.palmares_df[self.palmares_df["Spécialité"].str.contains(self.specialty, case=False, na=False)]
        self.lien_classement_web=[]
        self._generate_lien_classement(matching_rows)
        self.specialty_df = self.load_excel_sheets(matching_rows)
        return self.specialty_df

    def find_excel_sheet_with_privacy(self,prompt: str) -> pd.DataFrame:
        """
        Finds and loads ranking data based on both specialty and institution type.

        Args:
            prompt (str): The user's question.

        Returns:
            pd.DataFrame: DataFrame with the relevant filtered data.
        """
        
        self.get_infos(prompt)
        specialty=self.specialty
        
        if specialty== 'aucune correspondance':
            self._generate_lien_classement()
            self.specialty_df=self._load_and_transform_for_no_specialty(category=self.ispublic)
            return self.specialty_df
        if self.ispublic == 'aucune correspondance':
            return self.find_excel_sheet_with_speciality(prompt)

        matching_rows = self.palmares_df[self.palmares_df["Spécialité"].str.contains(specialty, case=False, na=False)]
        matching_rows = matching_rows[matching_rows["Catégorie"].str.contains(self.ispublic, case=False, na=False)]
        self._generate_lien_classement(matching_rows)
        self.specialty_df = self.load_excel_sheets(matching_rows)
        return self.specialty_df

    def extract_loca_hospitals(self, df: pd.DataFrame = None) -> pd.DataFrame:
        """
        Merges ranking data with hospital location data to associate each institution with its city and coordinates.

        Args:
            df (pd.DataFrame, optional): DataFrame containing the hospital ranking data.

        Returns:
            pd.DataFrame: DataFrame with city and coordinate information merged.
        """
        
        coordonnees_df = pd.read_excel(self.paths["coordonnees_path"]).dropna()
        notes_df = self.specialty_df
        coordonnees_df = coordonnees_df[["Etablissement", "Ville", "Latitude", "Longitude"]]
        notes_df = notes_df[["Etablissement", "Catégorie","Note / 20"]]
        self.df_with_cities = pd.merge(coordonnees_df, notes_df, on="Etablissement", how="inner")
        self.df_with_cities.rename(columns={"Ville": "City"}, inplace=True)
        return self.df_with_cities
    
    def get_df_with_distances(self) -> pd.DataFrame:
        """
        Calculates the distances between hospitals and the city specified in the user's query.

        Returns:
            pd.DataFrame or None: DataFrame with distance information, or None if geolocation fails.
        """

        query_coords = exget_coordinates(self.city, self.geopy_problem)
        if self.geopy_problem:
            return None
           
        self.df_with_cities = self.df_with_cities.dropna(subset=['City'])

        def _distance(city):
            city_coords = get_coordinates(self.df_with_cities, city)
            return distance_to_query(query_coords, city_coords, city, self.df_with_cities, self.geopy_problem)
                
        self.df_with_cities['Distance'] = self.df_with_cities['City'].apply(
            lambda city: distance_to_query(
                query_coords,
                city,
                self.df_with_cities,
                self.geopy_problem
            )
        )
        self.df_with_distances = self.df_with_cities
        return self.df_with_distances

    def create_csv(self, question:str, reponse: str):
        """
        Saves the user's query and the system's response to a CSV file for history tracking.

        Args:
            question (str): The user's question.
            reponse (str): The system's response.
        """

        file_name=self.paths["history_path"]
        data = {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "question": question,
            "ville": self.city,
            "type": self.ispublic,
            "spécialité": self.specialty,
            "résultat": reponse,
        }

        file_exists = os.path.exists(file_name)

        with open(file_name, mode="a", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=data.keys())
            if not file_exists: 
                writer.writeheader()
            writer.writerow(data)
        return None
