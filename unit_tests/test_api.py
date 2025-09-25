import pytest
import requests
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.api.routes import router
from app.pydantic_models.query_model import UserQuery, ChatRequest
from app.pydantic_models.response_model import AskResponse, ChatResponse

from fastapi import FastAPI

# Setup FastAPI app for testing
app = FastAPI()
app.include_router(router)

class TestAPI:
    def setup_method(self):
        """
        Setup the test client for API endpoint testing.
        """
        self.client = TestClient(app)


    def test_ask_valid_response(self):
        """
        Test /ask endpoint with a valid payload and mocked pipeline response.
        Ensures correct AskResponse structure and status code 200.
        """
        with patch('app.api.routes.pipeline') as mock_pipeline:
            mock_pipeline.generate_response.return_value = ("Best hospital response", ["link1", "link2"])
            payload = {"prompt": "Which is the best hospital in Paris?"}
            response = self.client.post("/ask", json=payload)
            assert response.status_code == 200
            data = response.json()
            assert data["result"] == "Best hospital response"
            assert isinstance(data["links"], list)


    def test_ask_multiple_specialties(self):
        """
        Test /ask endpoint when pipeline returns multiple specialties.
        Ensures multiple_specialty field is present in response.
        """
        with patch('app.api.routes.pipeline') as mock_pipeline:
            mock_pipeline.generate_response.return_value = ({"message": "Ambiguous specialty.", "multiple_specialty": ["cardio", "neuro"]}, [])
            payload = {"prompt": "Find a hospital for cardio or neuro."}
            response = self.client.post("/ask", json=payload)
            assert response.status_code == 200
            data = response.json()
            assert data["multiple_specialty"] == ["cardio", "neuro"]
            assert data["result"] == "Ambiguous specialty."


    def test_ask_invalid_result_type(self):
        """
        Test /ask endpoint when pipeline returns an invalid result type (not str or dict).
        Should return 500 error.
        """
        with patch('app.api.routes.pipeline') as mock_pipeline:
            mock_pipeline.generate_response.return_value = (12345, [])
            payload = {"prompt": "Invalid result type test."}
            response = self.client.post("/ask", json=payload)
            assert response.status_code == 500
            assert "Internal server error" in response.text


    def test_ask_pipeline_exception(self):
        """
        Test /ask endpoint when pipeline raises an exception.
        Should return 500 error.
        """
        with patch('app.api.routes.pipeline') as mock_pipeline:
            mock_pipeline.generate_response.side_effect = Exception("Pipeline error")
            payload = {"prompt": "Trigger error."}
            response = self.client.post("/ask", json=payload)
            assert response.status_code == 500
            assert "Internal server error" in response.text


    def test_chat_multi_turn_enabled(self):
        """
        Test /chat endpoint with multi-turn enabled and mocked conversation service.
        Ensures ChatResponse structure and status code 200.
        """
        with patch('app.api.routes.ENABLE_MULTI_TURN', True), \
             patch('app.api.routes.conversation_service') as mock_conv:
            mock_conv.handle_chat.return_value = ChatResponse(response="Multi-turn reply", conversation=[["Hi", "Multi-turn reply"]], ambiguous=False)
            payload = {"prompt": "Hi", "conversation": []}
            response = self.client.post("/chat", json=payload)
            assert response.status_code == 200
            data = response.json()
            assert data["response"] == "Multi-turn reply"
            assert data["ambiguous"] is False


    def test_chat_fallback_single_turn(self):
        """
        Test /chat endpoint fallback to single-turn when multi-turn is disabled.
        Ensures ChatResponse structure and status code 200.
        """
        with patch('app.api.routes.ENABLE_MULTI_TURN', False), \
             patch('app.api.routes.pipeline') as mock_pipeline:
            mock_pipeline.generate_response.return_value = ("Fallback reply", ["linkA"])
            payload = {"prompt": "Fallback test.", "conversation": []}
            response = self.client.post("/chat", json=payload)
            assert response.status_code == 200
            data = response.json()
            assert data["response"] == "Fallback reply"
            assert data["ambiguous"] is False


    def test_chat_ambiguous_specialties(self):
        """
        Test /chat endpoint when pipeline returns ambiguous specialties.
        Ensures ambiguous flag and multiple_specialty field are set.
        Also prints the response for debugging if the key is missing.
        """
        with patch('app.api.routes.ENABLE_MULTI_TURN', False), \
             patch('app.api.routes.pipeline') as mock_pipeline:
            mock_pipeline.generate_response.return_value = ({"message": "Ambiguous reply", "multiple_specialties": ["cardio", "neuro"]}, [])
            payload = {"prompt": "Ambiguous specialty test.", "conversation": []}
            response = self.client.post("/chat", json=payload)
            assert response.status_code == 200
            data = response.json()
            assert data["ambiguous"] is True
            # Defensive: check for key, print response if missing
            assert "multiple_specialty" in data, f"Response missing 'multiple_specialty': {data}"
            assert data["multiple_specialty"] is None


    def test_chat_pipeline_exception(self):
        """
        Test /chat endpoint when pipeline raises an exception.
        Should return 500 error.
        """
        with patch('app.api.routes.ENABLE_MULTI_TURN', False), \
             patch('app.api.routes.pipeline') as mock_pipeline:
            mock_pipeline.generate_response.side_effect = Exception("Pipeline error")
            payload = {"prompt": "Trigger chat error.", "conversation": []}
            response = self.client.post("/chat", json=payload)
            assert response.status_code == 500
            assert "Internal server error" in response.text

