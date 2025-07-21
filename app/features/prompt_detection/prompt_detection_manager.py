from .city_detection import CityDetector
from .institution_name_detection import InstitutionNameDetector
from .institution_type_detection import InstitutionTypeDetector
from .specialty_detection import SpecialtyDetector

class PromptDetectionManager:
    def __init__(self, model=None):
        self.model = model
        self.city_detector = CityDetector(model)
        self.institution_name_detector = InstitutionNameDetector(model)
        self.institution_type_detector = InstitutionTypeDetector(model)
        self.specialty_detector = SpecialtyDetector(model)
        from .topk_detection import TopKDetector
        self.topk_detector = TopKDetector(model)

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
        if institution_list:
            self.institution_name_detector.set_institution_list(institution_list)
            self.institution_type_detector.set_institution_list(institution_list)

        specialty_result = self.specialty_detector.detect_specialty(text, conv_history)
        specialty = specialty_result.get_primary_specialty() if hasattr(specialty_result, 'get_primary_specialty') else specialty_result
        top_k = self.topk_detector.detect_topk(text, conv_history)

        return {
            "city": self.city_detector.detect_city(text, conv_history),
            "institution_name": self.institution_name_detector.detect_institution_name(text, conv_history),
            "institution_type": self.institution_type_detector.detect_institution_type(text, conv_history),
            "specialty": specialty,
            "top_k": top_k
        }
