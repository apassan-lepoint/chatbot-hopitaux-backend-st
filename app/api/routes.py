from fastapi import APIRouter, Body 
from app.services.pipeline_service import Pipeline
from app.models.query_model import UserQuery
from app.models.response_model import AskResponse

# Initialize the API router instance to define and group related endpoints
router = APIRouter() 
# Initialize the pipeline service to use its methods to process incoming requests
pipeline = Pipeline() 

# Defines a POST endpoint at /ask using the router. This endpoint handles incoming POST requests.
@router.post("/ask", response_model=AskResponse)
def ask_question(query: UserQuery):
    """
    Inputs: 
    - prompt: question/prompt to be answered by the chatbot
        - Extracted from the request body
        - It expectes a JSON object with a "prompt" key
    - specialty_st: An optional specialty string to guide the chatbot's response
   
    Output: JSON object with final answer and links
    """
    
    # Call pipeline.final_answer and pass the prompt and specialty_st, unpack results
    res, link = pipeline.final_answer(prompt=query.prompt, specialty_st=query.specialty_st)
    return {"result": res, "links": link} 