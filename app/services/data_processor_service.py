""" 
data_processor_service.py
--------------------------
This module contains the DataProcessor class which is responsible for processing and analyzing data.
"""

import csv
import os
import pandas as pd
from app.config.features_config import ERROR_MESSAGES, CSV_FIELDNAMES 
from app.config.file_paths_config import PATHS 
from app.features.query_analysis.institution_names.institution_names_model import HospitalInfo
from app.services.llm_handler_service import LLMHandlerService
from app.snowflake_db.snowflake_query import convert_snowflake_to_pandas_df
from app.utility.functions.data_processor_service_helpers import *
from app.utility.functions.formatting_helpers import normalize_text
from app.utility.functions.logging import get_logger


logger = get_logger(__name__)


class DataProcessorService:
    """
    REDO
    """

    def __init__(self):
        logger.info("Initializing DataProcessor.")
        self.paths = PATHS
        self.snowflake_ranking_df = None
        self.llm_handler_service = LLMHandlerService()
        self.specialty_ranking_unavailable = False

        self.institution_names = []
        self.institution_name_mentioned = None
        self.institution_names_intent = None
        self.institution_type = None
        self.location = {}
        self.location_final = None
        self.location_level_final = None
        self.location_detected = None
        self.number_institutions = 3
        self.specialty = None
        self.multiple_specialty = None

    def load_snowflake_dataframe(self) -> pd.DataFrame:
        """
        Loads the main dataframe from Snowflake.
        """
        try:
            query = f"""
            SELECT *
            FROM DATATABLES_PROD.PATRIMOINE_CLASSE1.DT_PALMARES_HOPITAUX
            """
            df = convert_snowflake_to_pandas_df(query)
            df['CLASSEMENT_TYPE_NORM'] = df['CLASSEMENT_TYPE'].apply(normalize_text)
            df['ETABLISSEMENT_NOM_NORM'] = df['ETABLISSEMENT_NOM'].apply(normalize_text)    
            logger.info(f"Loaded snowflake dataframe with {len(df)} rows")
            return df
        except Exception as e:
            logger.error(f"Error loading snowflake dataframe: {e}")
            raise Exception(ERROR_MESSAGES["general_ranking_error"])


    def set_detection_results(self, specialty, location, location_detected, institution_type, number_institutions=None, institution_names=[], institution_name_mentioned=None, institution_names_with_types=None, institution_names_intent="none"):
        """
        Sets detection results from orchestrator.
        """
        logger.debug(f"set_detection_results: incoming args: "
                     f"specialty={specialty!r} (type: {type(specialty)}), "
                     f"location={location!r} (type: {type(location)}), "
                     f"location_detected={location_detected!r} (type: {type(location_detected)}), "
                     f"institution_type={institution_type!r} (type: {type(institution_type)}), "
                     f"number_institutions={number_institutions!r} (type: {type(number_institutions)}), "
                     f"institution_names={institution_names!r} (type: {type(institution_names)}), "
                     f"institution_name_mentioned={institution_name_mentioned!r} (type: {type(institution_name_mentioned)}), "
                     f"institution_names_with_types={institution_names_with_types!r} (type: {type(institution_names_with_types)}), "
                     f"institution_names_intent={institution_names_intent!r} (type: {type(institution_names_intent)})")
        # Robust specialty extraction
        specialty_value = None
        multiple_specialty_value = None
        if isinstance(specialty, list) and specialty:
            # Remove empty/invalid
            filtered = [s for s in specialty if s and isinstance(s, str) and s.strip()]
            if len(filtered) == 1:
                specialty_value = filtered[0].strip()
                multiple_specialty_value = None
            elif len(filtered) > 1:
                specialty_value = None
                multiple_specialty_value = filtered
            else:
                specialty_value = None
                multiple_specialty_value = None
        elif isinstance(specialty, str):
            specialty_value = specialty.strip() if specialty.strip() else None
            multiple_specialty_value = None
        elif isinstance(specialty, dict) and 'specialty' in specialty:
            specialty_value = str(specialty['specialty']).strip() if specialty['specialty'] else None
            multiple_specialty_value = None
        else:
            specialty_value = None
            multiple_specialty_value = None
        logger.debug(f"set_detection_results: resolved specialty_value={specialty_value!r}, multiple_specialty_value={multiple_specialty_value!r}")
        values = {
            "specialty": specialty_value,
            "multiple_specialty": multiple_specialty_value,
            "location": location or {},
            "location_detected": location_detected,
            "institution_type": institution_type if isinstance(institution_type, str) else None,
            "number_institutions": number_institutions,
            "institution_names": institution_names if isinstance(institution_names, list) else [],
            "institution_names_intent": institution_names_intent,
            "institution_name_mentioned": institution_name_mentioned
        }
        # Assign and log
        for attr, value in values.items():
            setattr(self, attr, value)
            logger.debug(f"DataProcessor.{attr} set to: {value!r}")
        

    def process_institution_names_query(self):
        """
        Process the query related to institution names.
        """
        ranking_df = self.snowflake_ranking_df

        # Filter by specialty
        ranking_df = ranking_df[ranking_df["CLASSEMENT_TYPE_NORM"] == self.specialty]

        # Normalize institution names to strings for filtering
        institution_names_norm = [  # TODO check if this is a list of strings or objects
            h.name if isinstance(h, HospitalInfo) else h
            for h in self.institution_names
        ]
        
        # Filter by institution names
        ranking_df = ranking_df[ranking_df["ETABLISSEMENT_NOM_NORM"].isin(institution_names_norm)] # TODO check it is a list of strings
        if ranking_df.empty:
            logger.warning("No matching institutions found in the rankings.")
            return None, None  # Stop pipeline, handle in orchestrator

        if self.institution_names_intent in ["single", "multi"]:
            return ranking_df, self.institution_names_intent

        if len(self.institution_names)>1 and self.institution_names_intent == "compare":
            # Check types for HospitalInfo objects or fallback to DataFrame
            types = set()
            for h in self.institution_names:
                if isinstance(h, HospitalInfo):
                    types.add(h.type)
                else:
                    match = ranking_df[ranking_df["ETABLISSEMENT_NOM_NORM"] == h]
                    if not match.empty and "ETABLISSEMENT_TYPE" in match.columns:
                        types.update(match["ETABLISSEMENT_TYPE"].unique())
            consistent_types = len(types) == 1

            if consistent_types:
                ranking_df = ranking_df.sort_values(by="CLASSEMENT_NOTE", ascending=False)
                self.institution_names_intent = "compare_consistent"
                return ranking_df, self.institution_names_intent 
            else:
                ranking_df = ranking_df.sort_values(by="ETABLISSEMENT_NOM", ascending=True) # Sort by the formal name; not normalized name
                self.institution_names_intent = "compare_inconsistent"
                return ranking_df, self.institution_names_intent

    def process_other_query(self):
        """  
        Process queries that are not related to institution names.
        """
        ranking_df = self.snowflake_ranking_df
        logger.debug(f"Initial ranking_df shape: {ranking_df.shape}")

        # Filter by location (priority: postal_code, city_commune, department, region)
        location_keys = ["postal_code", "city_commune", "department", "region"]
        location_value = None
        for key in location_keys:
            if self.location and key in self.location and self.location[key]:
                location_value = self.location[key]
                self.location_final = location_value
                self.location_level_final = key
                # Choose column for filtering
                col_map = {
                    "postal_code": "ETABLISSEMENT_CODE_POSTAL",
                    "city_commune": "ETABLISSEMENT_VILLE",
                    "department": "ETABLISSEMENT_DEPARTEMENT",
                    "region": "ETABLISSEMENT_REGION" # TODO make sure SarahLina adds it in 
                }
                # Robust handling: always use scalar for single-element lists
                if isinstance(location_value, list):
                    if len(location_value) == 1:
                        location_value = location_value[0]
                        ranking_df = ranking_df[ranking_df[col_map[key]] == location_value]
                    elif len(location_value) > 1:
                        ranking_df = ranking_df[ranking_df[col_map[key]].isin(location_value)]
                    # If empty list, do not filter
                    break
                else:
                    ranking_df = ranking_df[ranking_df[col_map[key]] == location_value]
                    break

        # Filter by specialty
        logger.debug(f"Filtering by specialty: {self.specialty!r} (type: {type(self.specialty)})")
        if self.specialty and isinstance(self.specialty, str):
            ranking_df = ranking_df[ranking_df["CLASSEMENT_TYPE_NORM"] == self.specialty]
        else:
            logger.warning("No valid specialty set; skipping specialty filter.")

        # Filter by Institution type 
        logger.debug(f"Filtering by institution type: {self.institution_type!r} (type: {type(self.institution_type)})")
        if self.institution_type in ["Public", "Privé"]:
            ranking_df = ranking_df[ranking_df["ETABLISSEMENT_TYPE"] == self.institution_type]
            ranking_df_public = ranking_df if self.institution_type == "Public" else None
            ranking_df_private = ranking_df if self.institution_type == "Privé" else None
        else:
            ranking_df_public = ranking_df[ranking_df["ETABLISSEMENT_TYPE"] == "Public"]
            ranking_df_private = ranking_df[ranking_df["ETABLISSEMENT_TYPE"] == "Privé"]

        # Sort by score
        logger.debug("Sorting by CLASSEMENT_NOTE")
        ranking_df_public_sorted = ranking_df_public.sort_values(by="CLASSEMENT_NOTE", ascending=False) if ranking_df_public is not None and not ranking_df_public.empty else pd.DataFrame()
        ranking_df_private_sorted = ranking_df_private.sort_values(by="CLASSEMENT_NOTE", ascending=False) if ranking_df_private is not None and not ranking_df_private.empty else pd.DataFrame()

        # Select the top N institutions 
        logger.debug(f"Selecting number of institutions requested: {self.number_institutions}")
        if len(ranking_df_public_sorted) >= self.number_institutions and len(ranking_df_private_sorted) >= self.number_institutions:
            ranking_df_public_final = ranking_df_public_sorted.head(self.number_institutions)
            ranking_df_private_final = ranking_df_private_sorted.head(self.number_institutions)
        else:
            ranking_df_public_final, ranking_df_private_final = process_other_query_with_coordinates_fallback(self.snowflake_ranking_df, self.specialty, self.location_final, self.location_level_final, self.institution_type, self.number_institutions)
        logger.debug(f"Final public ranking_df shape: {ranking_df_public_final.shape if ranking_df_public_final is not None else 'None'}")
        logger.debug(f"Final private ranking_df shape: {ranking_df_private_final.shape if ranking_df_private_final is not None else 'None'}")
        return ranking_df_public_final, ranking_df_private_final

    def create_csv(self, result_data: dict): # TODO eventually send to Snowflake
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