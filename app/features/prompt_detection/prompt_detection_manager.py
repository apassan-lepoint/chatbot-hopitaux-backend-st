from .city.city_service import CityService
from .city.city_validation import CityCheckException
from .institution_name.institution_name_service import InstitutionNameService
from .institution_type.institution_type_service import InstitutionTypeService
from .topk.topk_service import TopKService
from .specialty_detection import SpecialtyDetector

class PromptDetectionManager:
    def __init__(self, model=None, institution_list=None, llm_handler_service=None):
        self.model = model
        self.city_service = CityService(llm_handler_service, model)
        self.institution_name_service = InstitutionNameService(model, institution_list or "")
        self.institution_type_service = InstitutionTypeService(model, institution_list or "")
        self.specialty_detector = SpecialtyDetector(model)
        self.topk_service = TopKService(model)

    def run_all_detections(self, text, conv_history="", institution_list=None):
        """
        Consolidate results from all prompt detection classes into a dictionary.
        Returns:
            dict: {
                'city': ...,
                'institution_name': ...,
                'institution_type': ...,
                'specialty': ...,
                'top_k': ...
            }
        """
        specialty_result = self.specialty_detector.detect_specialty(text, conv_history)
        specialty = specialty_result.get_primary_specialty() if hasattr(specialty_result, 'get_primary_specialty') else specialty_result
        top_k = self.topk_service.process_topk(text, conv_history)

        try:
            city = self.city_service.process_city(text, conv_history)
        except CityCheckException as e:
            city = str(e)

        institution_name_result = self.institution_name_service.detect_and_validate(text, conv_history)
        institution_type_result = self.institution_type_service.detect_and_validate_type(text, conv_history)
        return {
            "city": city,
            "institution_name": institution_name_result.get("institution_name"),
            "institution_type": institution_type_result.get("institution_type"),
            "specialty": specialty,
            "top_k": top_k
        }
