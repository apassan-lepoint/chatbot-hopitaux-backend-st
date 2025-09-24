""" 
pipeline_orchestrator_service.py
---------------------------------
This file contains the PipelineOrchestratorService class which orchestrates the processing of user queries related to hospital rankings.
"""

from datetime import datetime
import pandas as pd
from uuid import uuid4
from app.config.features_config import ERROR_MESSAGES, NON_ERROR_MESSAGES, METHODOLOGY_WEB_LINK
from app.features.query_analysis.query_analyst import QueryAnalyst
from app.features.sanity_checks.conversation_limit_check import ConversationLimitCheckException
from app.features.sanity_checks.message_length_check import MessageLengthCheckException
from app.features.sanity_checks.message_pertinence_check import MessagePertinenceCheckException
from app.features.sanity_checks.sanity_checks_analyst import SanityChecksAnalyst
from app.services.data_processor_service import DataProcessorService
from app.utility.functions.logging import get_logger
from app.utility.functions.pipeline_orchestrator_helpers import * 

logger = get_logger(__name__)

class PipelineOrchestratorService:
    """
    """

    def __init__(self):
        self.data_processor=DataProcessorService()
        self.response = ""
        self.web_ranking_links = []

        
        self.institution_names = []
        self.institution_name_mentioned = None
        self.institution_names_intent = None
        self.institution_type = None
        self.location = {}
        self.location_detected = None
        self.number_institutions = 3
        self.specialty = None
        self.specialty_ranking_unavailable = False

    
    def reset_attributes(self): #TODO check that the proper attributes are being reset
        """
        Resets pipeline attributes for a new user query.
        """
        logger.info("Resetting PipelineOrchestratorServiceattributes for new query")
        # Reset all relevant attributes to None for a fresh query
        for attr in [
            "specialty", "institution_type", "location", "df_with_cities", "specialty_df",
            "location_not_specified", "institution_name_mentioned", "institution_names", "df_gen"
        ]:
            setattr(self, attr, None)


    def _handle_response_generation_failure(self, prompt, conversation, error_msg, aggregation, mode=None):
        logger.info(f"Final cost/token usage aggregation: {aggregation}")
        logger.info(
            f"Detected variables: specialty={self.specialty}, "
            f"location={self.location}, institution_type={self.institution_type}, "
            f"institution_names={self.institution_names}, number_institutions={self.number_institutions}"
        )

        if mode =='snowflake_data_load_failure':
            csv_data = {
                'uuid': str(uuid4()),
                'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'question': prompt,
                'response': error_msg,      
                'error': True,  
                'conversation_list': conversation or [],
                'sanity_check_pass': "",
                'location': "",
                'location_level': "",
                'institution_type': "",
                'institution_names': "",
                'institution_names_intent': "",
                'specialty': "",
                'number_institutions': "",
                'total_cost_sanity_checks': 0,        
                'total_cost_query_analyst': 0,
                'total_cost_conversation_analyst': 0,
                'total_cost': 0,
                'total_tokens_sanity_checks': 0,
                'total_tokens_query_analyst': 0,
                'total_tokens_conversation_analyst': 0,
                'total_tokens': 0
            }

        error_value = True
        sanity_check_pass = False if mode == 'sanity_check' else True

        csv_data = {
            'uuid': str(uuid4()),
            'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'question': prompt,
            'response': error_msg,
            'error': error_value,
            'conversation_list': conversation or [],
            'sanity_check_pass': sanity_check_pass,
            'location': self.data_processor.location_final if self.data_processor.location_final else self.data_processor.location,
            'location_level': self.data_processor.location_level_final,
            'institution_type': self.data_processor.institution_type,
            'institution_names': self.data_processor.institution_names,
            'institution_names_intent': self.data_processor.institution_names_intent,
            'specialty': self.data_processor.specialty,
            'multiple_specialty': self.data_processor.multiple_specialty,
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

        self.response = error_msg
        self.web_ranking_links = []

        return self.response, self.web_ranking_links


    def _run_sanity_checks(self, prompt: str, conversation, conv_history):
        """ 
        """
        logger.info(f"Running sanity checks for prompt: {prompt}, conversation: {conversation}, conv_history: {conv_history}")
        try:
            self.sanity_checks_analyst_results = SanityChecksAnalyst(self.data_processor.llm_handler_service)
            sanity_result = self.sanity_checks_analyst_results.run_checks(prompt, conversation, conv_history)
            logger.info(f"Sanity checks result: {sanity_result}")
            self.sanity_checks_analyst_result = sanity_result
        except Exception as exc:
            error = True
            error_message = str(exc)
            aggregation = get_costs_and_tokens(getattr(self, 'sanity_checks_analyst_result', None), None, None)
            return self._handle_response_generation_failure(prompt, conversation, error_message, aggregation, mode='sanity_check')

        if isinstance(sanity_result, dict) and not sanity_result.get("passed", True):
            error_message = sanity_result.get("error", ERROR_MESSAGES['general_error'])
            aggregation = get_costs_and_tokens(getattr(self, 'sanity_checks_analyst_result', None), None, None)
            return self._handle_response_generation_failure(prompt, conversation, error_message, aggregation, mode='sanity_check')


    def extract_query_parameters(self, prompt: str, detected_specialty: str = None, conversation: list = None, conv_history: list = None) -> dict:
        """
        Centralized detection: runs QueryAnalyst and sets results in DataProcessor.
        Returns detections dict.
        Returns a dictionary containing the results of all query parameter detections.    
        """
        logger.info(f"Extracting query parameters: prompt='{prompt}', detected_specialty='{detected_specialty}', conv_history='{conv_history}'")
        
        try:
            # Setup QueryAnalyst
            llm_handler_service = self.data_processor.llm_handler_service
            prompt_manager = QueryAnalyst(model=getattr(llm_handler_service, 'model', None), llm_handler_service=llm_handler_service)

            # Format conversation history as string
            conv_history_str = "".join(conv_history) if conv_history else ""

            # Run all detections
            detections = prompt_manager.run_all_detections(prompt, conv_history=conv_history_str)
            self.query_analyst_results = detections
            logger.debug("Full detections dict: %s", detections)

            # Only use a valid specialty for assignment
            invalid_specialties = {"no match", "no specialty match", "aucune correspondance", ""}
            specialty_candidate = detected_specialty if detected_specialty else detections.get("specialty")
            specialty_to_set = None
            if isinstance(specialty_candidate, list):
                # Remove any invalid specialties from the list
                filtered = [s for s in specialty_candidate if s and s not in invalid_specialties]
                if filtered:
                    specialty_to_set = filtered
                else:
                    specialty_to_set = None
            elif isinstance(specialty_candidate, str):
                if specialty_candidate and specialty_candidate not in invalid_specialties:
                    specialty_to_set = specialty_candidate
                else:
                    specialty_to_set = None
            else:
                specialty_to_set = None

            # Push results into DataProcessor
            self.data_processor.set_detection_results(
                specialty=specialty_to_set,
                location=detections.get('location'),
                location_detected=detections.get('location_detected', False),
                institution_type=detections.get('institution_type'),
                number_institutions=detections.get('number_institutions') if 'number_institutions' in detections else detections.get('number_institutions'),
                institution_name_mentioned=detections.get('institution_name_mentioned'),
                institution_names=detections.get('institution_names', []),
                institution_names_intent=detections.get('institution_names_intent', "none"))
            
            # Mirror attributes locally and log
            attrs_to_log = ["specialty", "location", "location_detected", "institution_type", "institution_names", "institution_name_mentioned", "number_institutions"]
            for attr in attrs_to_log:
                setattr(self, attr, getattr(self.data_processor, attr))
                logger.debug("PipelineOrchestrator.%s set to: %r", attr, getattr(self, attr))

            logger.debug("PipelineOrchestratorServiceinfos - specialty=%s, location=%s, institution_type=%s, institution=%s, institution_name_mentioned=%s",
                        self.specialty, self.location, self.institution_type, self.institution_names, self.institution_name_mentioned)

            return detections
        
        except Exception as e:
            logger.error(f"Error in extract_query_parameters: {str(e)}", exc_info=True)
            error_message = str(e)
            aggregation = get_costs_and_tokens(getattr(self, 'query_analyst_result', None), None, None)
            return self._handle_response_generation_failure(prompt, conversation, error_message, aggregation)


    def format_response(self, public_df=None, private_df=None, number_institutions=5, location_not_specified=True, institution_df=None, intent=None):
        """
        Format DataFrames into a chatbot response. Handles public/private or institution name queries.
        If intent indicates a comparison and institution_df is provided, adds a sentence indicating the best institution.
        """
        response = ""
        if institution_df is not None:
            response += format_rows(institution_df, "", number_institutions, location_not_specified)
            logger.debug(f"format_response intent={intent}, institution_df columns={institution_df.columns}")
            if intent in ("compare", "compare_consistent", "compare_inconsistent") and not institution_df.empty:
                best_institution = institution_df.iloc[0]["ETABLISSEMENT_NOM"]
                logger.debug(f"Best institution determined: {best_institution}")
                response += f"<br><b>Parmi les établissements comparés, le mieux classé est : {best_institution}.</b>"
        else:
            response += format_rows(private_df, "privé", number_institutions, location_not_specified)
            response += format_rows(public_df, "public", number_institutions, location_not_specified)
        return response.rstrip('<br>')


    def generate_response_links(self, matching_rows: pd.DataFrame = None) -> list:
        """
        Generates web links to the relevant ranking pages based on specialty and institution type.
        """
        logger.info("Generating ranking links")
        self.web_ranking_links.clear()
        
        # If no specialty, suggest general ranking links
        if self.specialty == 'tableau d\'honneur':
            logger.debug("No specialty detected, generating general ranking links")
            institution_type_french = self.institution_type  # Already normalized
            if institution_type_french == 'Public':
                self.web_ranking_links = [self.weblinks["public"]]
            elif institution_type_french == 'Privé':
                self.web_ranking_links = [self.weblinks["privé"]]
            else:
                self.web_ranking_links = [self.weblinks["public"], self.weblinks["privé"]]
            self.web_ranking_links.append(METHODOLOGY_WEB_LINK)
            return self.web_ranking_links
        
        # If ranking not found, suggest the opposite type
        if self.specialty_ranking_unavailable:
            logger.debug("Specialty ranking unavailable, generating opposite type links")
            institution_type_french = self.institution_type
            opposite_type = 'prive' if institution_type_french == 'Public' else 'public'
            first_specialty = self._parse_specialty_list(self.specialty)[0] if (',' in self.specialty or self.specialty.startswith(('plusieurs correspondances:', 'multiple matches:'))) else self.specialty
            specialty_for_url = row.get("CLASSEMENT_TYPE", first_specialty)
            web_link = generate_web_link(specialty_for_url, opposite_type)
            self.web_ranking_links.append(web_link)
            self.web_ranking_links.append(METHODOLOGY_WEB_LINK)
            return self.web_ranking_links
        
        # Generate links for each matching row
        if matching_rows is not None and len(matching_rows) > 0:
            logger.debug(f"Generating links for {len(matching_rows)} matching rows")
            for _, row in matching_rows.iterrows():
                # Try both possible column names for category and specialty
                category_for_url = row.get("ETABLISSEMENT_TYPE", None)
                specialty_for_url = row.get("CLASSEMENT_TYPE", self.specialty)
                web_link = generate_web_link(specialty_for_url, category_for_url)
                self.web_ranking_links.append(web_link)
        else:
            logger.debug("No matching rows provided, no links generated")
        logger.info(f"Generated ranking links: {self.web_ranking_links}")
        return self.web_ranking_links            

    def generate_response(self, prompt: str, conversation=None, conv_history=None, user_selected_specialty=None) -> tuple:
        """
        Main entry point for generating a response. Catches all exceptions and ensures error messages are sent to frontend and CSV.
        """
        logger.info(f"Starting response generation for prompt: {prompt}")

        # Step 1: reset attributes for new query 
        self.reset_attributes()

        if conversation is None: 
            conversation = []
        if conv_history is None: 
            conv_history = []
        
        # Step 2: Check that snowflake connection is working and ranking data is accessible
        try:
            self.data_processor.snowflake_ranking_df = self.data_processor.load_snowflake_dataframe()
        except Exception as e:
            logger.error(f"Error loading snowflake dataframe: {e}")
            error_message = str(e)
            aggregation = get_costs_and_tokens(None, None, None)

            return self._handle_response_generation_failure(prompt, conversation, error_message, aggregation, mode='snowflake_data_load_failure')

        # Step 3: run sanity checks on prompt
        sanity_check_output = self._run_sanity_checks(prompt, conversation, conv_history)

        if sanity_check_output:  # means sanity checks failed
            error_msg, web_links = sanity_check_output # Note that web_links will be empty list here
            return error_msg, web_links  # stop pipeline early

        logger.info("Sanity checks passed. Proceeding with pipeline.")

        # Step 4: detect variables from prompt
        detect_specialty = None  # Only set this to a string if you have a user-selected specialty
        detection_results = self.extract_query_parameters(prompt, detect_specialty, conversation, conv_history)

        # Step 4a: resolve specialty if user selected one; can eventually add on for other variables
        success, result = handle_variable_selection(
            variable_name="specialty",
            user_selected_value=user_selected_specialty,
            detections=detection_results
        )

        # If ambiguous, return options for UI selection
        if not success:
            # If multiple specialties, return as dict for API
            if self.data_processor.multiple_specialty:
                return {
                    "message": result if isinstance(result, str) else "Plusieurs spécialités détectées.",
                    "multiple_specialty": self.data_processor.multiple_specialty
                }, []
            return result  # fallback

        self.specialty = result
        self.data_processor.specialty = result

        logger.info(
            f"Detected variables: specialty={self.specialty}, location={self.location}, "
            f"institution_type={self.institution_type}, institution_names={self.institution_names}, "
            f"number_institutions={self.number_institutions}"
        )


        # Execute the appropriate query based on institution name mention
        if self.institution_name_mentioned:
            query_result_data, intent = self.data_processor.process_institution_names_query()
            self.institution_names_intent = intent  # Ensure intent is set for format_response
            if query_result_data is None:
                self.specialty_ranking_unavailable = True
                error_msg = ERROR_MESSAGES["institution_not_found_df"]
                aggregation = get_costs_and_tokens(getattr(self, 'detection_results', None), getattr(self, 'query_analyst_results', None), None)
                csv_data = {
                    'uuid': str(uuid4()),
                    'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'question': prompt,
                    'response': error_msg,
                    'error': True,
                    'conversation_list': conversation or [],
                    'sanity_check_pass': True,
                    'location': self.data_processor.location_final if self.data_processor.location_final else self.data_processor.location,
                    'location_level': self.data_processor.location_level_final,
                    'institution_type': self.data_processor.institution_type,
                    'institution_names': self.data_processor.institution_names,
                    'institution_names_intent': self.data_processor.institution_names_intent,
                    'specialty': self.data_processor.specialty,
                    'multiple_specialty': self.data_processor.multiple_specialty,
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

                self.response = error_msg
                self.web_ranking_links = []
                return self.response, self.web_ranking_links

        else:
            ranking_df_public_final, ranking_df_private_final = self.data_processor.process_other_query()
            if ranking_df_public_final is None and ranking_df_private_final is None:
                self.specialty_ranking_unavailable = True
                error_msg = ERROR_MESSAGES["general_ranking_error"]
                aggregation = get_costs_and_tokens(getattr(self, 'detection_results', None), getattr(self, 'query_analyst_results', None), None)
                csv_data = {
                    'uuid': str(uuid4()),
                    'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'question': prompt,
                    'response': error_msg,
                    'error': True,
                    'conversation_list': conversation or [],
                    'sanity_check_pass': True,
                    'location': self.data_processor.location_final if self.data_processor.location_final else self.data_processor.location,
                    'location_level': self.data_processor.location_level_final,
                    'institution_type': self.data_processor.institution_type,
                    'institution_names': self.data_processor.institution_names,
                    'institution_names_intent': self.data_processor.institution_names_intent,
                    'specialty': self.data_processor.specialty,
                    'multiple_specialty': self.data_processor.multiple_specialty,
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

                self.response = error_msg
                self.web_ranking_links = []
                return self.response, self.web_ranking_links

        # Create the text response from the dataframes
        if self.institution_name_mentioned:
            logger.debug(f"Calling format_response with intent={self.institution_names_intent}, institution_names={self.institution_names}, number_institutions={self.number_institutions}")
            response = self.format_response(institution_df=query_result_data, number_institutions=self.number_institutions, location_not_specified=not self.location_detected, intent=self.institution_names_intent)
        else:
            response = self.format_response(public_df=ranking_df_public_final, private_df=ranking_df_private_final, number_institutions=self.number_institutions, location_not_specified=not self.location_detected)
        self.response = response

        #  Create the web links to the ranking pages
        if self.institution_name_mentioned:
            links = self.generate_response_links(query_result_data)
        else:
            combined_df = pd.concat([ranking_df_public_final, ranking_df_private_final], ignore_index=True)
            links = self.generate_response_links(combined_df)
        self.web_ranking_links = links
        
        # Export to csv
        aggregation = get_costs_and_tokens(getattr(self, 'detection_results', None), getattr(self, 'query_analyst_results', None), None)
        csv_data = {
            'uuid': str(uuid4()),
            'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'question': prompt,
            'response': response,
            'error': False,
            'conversation_list': conversation or [],
            'sanity_check_pass': True,
            'location': self.data_processor.location_final if self.data_processor.location_final else self.data_processor.location,
            'location_level': self.data_processor.location_level_final,
            'institution_type': self.data_processor.institution_type,
            'institution_names': self.data_processor.institution_names,
            'institution_names_intent': self.data_processor.institution_names_intent,
            'specialty': self.data_processor.specialty,
            'multiple_specialty': self.data_processor.multiple_specialty,
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

        return self.response, self.web_ranking_links
