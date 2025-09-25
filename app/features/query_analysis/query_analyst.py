from .location.location_analyst import LocationAnalyst
from .location.location_validation import LocationCheckException
from .institution_names.institution_names_analyst import InstitutionNamesAnalyst
from .institution_type.institution_type_analyst import InstitutionTypeAnalyst
from .number_institutions.number_institutions_analyst import NumberInstitutionsAnalyst
from .specialty.specialty_analyst import SpecialtyAnalyst
from app.utility.functions.logging import get_logger

logger = get_logger(__name__)

class QueryAnalyst:
    """
    QueryAnalyst consolidates various detection services to analyze queries for location, institution name,
    institution type, specialty, and number of institutions.
    It provides a unified interface to run all detections and returns the results in a structured format.

    Attributes:
        model: The model used for processing queries.
        institution_list: Optional list of institutions for validation.
        llm_handler_service: Optional service for handling large language model interactions.
    Methods:
        run_all_detections(text, conv_history="", institution_list=None):
            Analyzes the provided text and conversation history to detect location, institution name,
            institution type, specialty, and number of institutions.    
    """
    def __init__(self, model=None, llm_handler_service=None):
        logger.info("Initializing QueryAnalyst")
        self.model = model
        self.location_service = LocationAnalyst(llm_handler_service, model)
        self.institution_names_service = InstitutionNamesAnalyst(model)
        self.institution_type_service = InstitutionTypeAnalyst(model)
        self.specialty_analyst = SpecialtyAnalyst(model)
        self.number_institutions_service = NumberInstitutionsAnalyst(model)


    def run_all_detections(self, text, conv_history="", institution_list=None):
        """
        Consolidate results from all prompt detection classes into a dictionary.
        """
        logger.info(f"QueryAnalyst running all detections for text: {text}, conv_history: {conv_history}")

        specialty_result = self.specialty_analyst.detect_and_validate_specialty(text, conv_history)

        try:
            location_result = self.location_service.detect_and_validate_location(text, conv_history)
            if not isinstance(location_result, dict) or "location" not in location_result or "location_detected" not in location_result:
                logger.error(f"QueryAnalyst.run_all_detections: location_result malformed, using fallback: {location_result}")
                location_result = {"location": None, "location_detected": False, "detection_method": None, "cost": 0.0}
        except LocationCheckException as e:
            logger.error(f"QueryAnalyst.run_all_detections: LocationCheckException: {e}")
            location_result = {"location": None, "location_detected": False, "detection_method": None, "cost": 0.0}
        except Exception as e:
            logger.error(f"QueryAnalyst.run_all_detections: Unexpected exception: {e}")
            location_result = {"location": None, "location_detected": False, "detection_method": None, "cost": 0.0}

        institution_names_result = self.institution_names_service.detect_and_validate_institution_names(text, conv_history)
        institution_type_result = self.institution_type_service.detect_and_validate_institution_type(text, conv_history)

        number_institutions_result = self.number_institutions_service.process_number_institutions(text, conv_history)
        if institution_names_result.get("institutions"): # If institution names are detected, override number_institutions_result
            number_institutions = len(institution_names_result["institutions"])
        else:
            number_institutions = number_institutions_result.get("number_institutions")

        total_cost = (
            location_result.get("cost", 0.0)
            + institution_names_result.get("cost", 0.0)
            + institution_type_result.get("cost", 0.0)
            + specialty_result.get("cost", 0.0)
            + number_institutions_result.get("cost", 0.0)
        )
        total_token_usage = (
            location_result.get("token_usage", 0)
            + institution_names_result.get("token_usage", 0)
            + institution_type_result.get("token_usage", 0)
            + specialty_result.get("token_usage", 0)
            + number_institutions_result.get("token_usage", 0)
        )
        results =  {
            "location": location_result["location"],
            "location_detected": location_result["location_detected"],
            "location_detection_method": location_result.get("detection_method"),
            "location_cost": location_result.get("cost", 0.0),
            "location_token_usage": location_result.get("token_usage", 0),
            "institution_name_mentioned": institution_names_result.get("institution_name_mentioned"),
            "institution_names": institution_names_result.get("institutions"),  # list of {name,type}
            "institution_names_detection_method": institution_names_result.get("detection_method"),
            "institution_names_cost": institution_names_result.get("cost", 0.0),
            "institution_names_token_usage": institution_names_result.get("token_usage", 0),
            "institution_names_intent": institution_names_result.get("intent"),
            "institution_type": institution_type_result.get("institution_type"),
            "institution_type_detection_method": institution_type_result.get("detection_method"),
            "institution_type_cost": institution_type_result.get("cost", 0.0),
            "institution_type_token_usage": institution_type_result.get("token_usage", 0),
            "specialty": specialty_result.get("specialty"),
            "specialty_detection_method": specialty_result.get("detection_method"),
            "specialty_cost": specialty_result.get("cost", 0.0),
            "specialty_token_usage": specialty_result.get("token_usage", 0),
            "number_institutions": number_institutions,
            "number_institutions_detection_method": number_institutions_result.get("detection_method"),
            "number_institutions_cost": number_institutions_result.get("cost", 0.0),
            "number_institutions_token_usage": number_institutions_result.get("token_usage", 0),
            "total_cost": total_cost,
            "total_token_usage": total_token_usage
        }

        logger.info(f"QueryAnalyst detected: specialty={specialty_result.get('specialty')}, location={location_result.get('location')}, institution_names={institution_names_result.get('institution_names')}, institution_type={institution_type_result.get('institution_type')}, number_institutions={number_institutions_result.get('number_institutions')}")
        logger.info(f"QueryAnalyst costs/tokens: specialty_cost={specialty_result.get('cost')}, location_cost={location_result.get('cost')}, institution_names_cost={institution_names_result.get('cost')}, institution_type_cost={institution_type_result.get('cost')}, number_institutions_cost={number_institutions_result.get('cost')}")
        logger.info(f"QueryAnalyst tokens: specialty_tokens={specialty_result.get('token_usage')}, location_tokens={location_result.get('token_usage')}, institution_names_tokens={institution_names_result.get('token_usage')}, institution_type_tokens={institution_type_result.get('token_usage')}, number_institutions_tokens={number_institutions_result.get('token_usage')}")

        return results
    

    #  # Logging for debugging and analysis
    # logger.info(
    #     f"Institution names detected: {results['institution_names_with_types']}, "
    #     f"intent={results['institution_names_intent']}, "
    #     f"detection method={results['institution_names_detection_method']}"
    # )
    # logger.info(
    #     f"Costs/tokens: cost={results['institution_names_cost']}, "
    #     f"tokens={results['institution_names_token_usage']}"
    # )
