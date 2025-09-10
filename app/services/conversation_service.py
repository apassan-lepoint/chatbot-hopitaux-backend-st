from fastapi import HTTPException
from app.services.pipeline_orchestrator_service import PipelineOrchestrator
from app.services.llm_handler_service import LLMHandler
from app.features.conversation.conversation_analyst import ConversationAnalyst
from app.pydantic_models.query_model import ChatRequest
from app.pydantic_models.response_model import ChatResponse
from app.utility.logging import get_logger
from app.config.features_config import ERROR_MESSAGES
from app.utility.formatting_helpers import format_links


class ConversationService:
    """
    Handles all multi-turn conversation logic extracted from routes.py.
    """

    def __init__(self):
        self.pipeline = PipelineOrchestrator()
        self.llm_handler = LLMHandler()
        self.conv_manager = ConversationAnalyst(self.llm_handler.model)
        self.logger = get_logger(__name__)
    

    def _build_response(self, prompt: str, answer: str, history: list) -> ChatResponse:
        updated_history = history + [[prompt, answer]]
        return ChatResponse(response=answer, conversation=updated_history, ambiguous=False)


    @staticmethod
    def _history_to_str(history):
        return "\n".join([f"Utilisateur: {q}\nAssistant: {r}" for q, r in history])


    def handle_chat(self, request: ChatRequest) -> ChatResponse:
        """
        Handle multi-turn chat requests, replicating the original /chat endpoint logic.
        """
        # TODO : make case names more descriptive
        try:
            conv_history = request.conversation if request.conversation else []
            conv_results = self.conv_manager.run_all_conversation_checks(request.prompt, conv_history)
            multi_turn_result = conv_results.get("multi_turn_result", {})
            case = multi_turn_result.get("case")

            # Fall back to LLM case detection if needed
            if not case:
                conv_history_str = self._history_to_str(conv_history)
                analysis = self.llm_handler.analyze_subsequent_message(request.prompt, conv_history_str)
                case = self.llm_handler.determine_case(analysis)

            self.logger.info(f"Determined case: {case}, Analysis: {multi_turn_result}")

            if case == "case1":
                result = ERROR_MESSAGES["message_pertinence"]
                return self._build_response(request.prompt, result, conv_history)

            elif case == "case2":
                rewritten_query = self.llm_handler.rewrite_query_merge(request.prompt, self._history_to_str(conv_history))
                result, links = self.pipeline.generate_response(prompt=rewritten_query)
                return self._build_response(request.prompt, format_links(result, links), conv_history)

            elif case == "case3":
                rewritten_query = self.llm_handler.rewrite_query_add(request.prompt, self._history_to_str(conv_history))
                result, links = self.pipeline.generate_response(prompt=rewritten_query)
                return self._build_response(request.prompt, format_links(result, links), conv_history)

            elif case == "case4":
                result = conv_results["continued_response"]
                return self._build_response(request.prompt, result, conv_history)

            elif case == "case5":
                result, links = self.pipeline.generate_response(prompt=request.prompt)
                if isinstance(result, dict) and "multiple_specialties" in result:
                    return ChatResponse(response=result["message"], conversation=conv_history + [[request.prompt, result["message"]]], ambiguous=True, multiple_specialties=result["multiple_specialties"])
                return self._build_response(request.prompt, format_links(result, links), conv_history)

            else:  # case6
                result = conv_results["continued_response"]
                return self._build_response(request.prompt, result, conv_history)

        except Exception as e:
            self.logger.error(f"Error processing /chat request: {str(e)}")
            if not isinstance(e, HTTPException):
                raise HTTPException(status_code=500, detail=ERROR_MESSAGES['internal_server_error'])
            raise

    