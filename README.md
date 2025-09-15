README

# Description
The hospital ranking assistant allows interaction with Le Point's hospital rankings and exploration of its content. It enables users to ask questions to query the rankings. It is currently accessible through a Streamlit application, serving as a user interface for testing and in production mode via FastAPI (in development).

# Project Structure

BackendChatbotHopitaux/
├── .env
├── .gitignore
├── Dockerfile
├── README.md
├── requirements.txt
├── main.py
├── app/
│   ├── api/
│   │   └── routes.py
│   ├── config/
│   │   ├── features_config.py
│   │   └── file_paths_config.py
│   ├── features/==
│   │   ├── conversation/
│   │   │  ├── conversation_analyst.py
│   │   │  ├── llm_responder.py
│   │   │  └── multi_turn.py
│   │   ├── query_analysis/
│   │   │  ├── city/
│   │   │  │   ├── city_analyst.py
│   │   │  │   ├── city_detection.py
│   │   │  │   └── city_validation.py
│   │   │  ├── institution_names/
│   │   │  │   ├── institution_names_analyst.py
│   │   │  │   ├── institution_names_detection.py
│   │   │  │   └── institution_names_validation.py
│   │   │  ├── institution_type/
│   │   │  │   ├── institution_type_analyst.py
│   │   │  │   ├── institution_type_detection.py
│   │   │  │   └── institution_type_validation.py
│   │   │  ├── number_institutions/
│   │   │  │   ├── number_institutions_analyst.py
│   │   │  │   ├── number_institutions_detection.py
│   │   │  │   └── number_institutions_validation.py
│   │   │  └── specialty/
│   │   │  │   ├── specialty_analyst.py - IN DEV
│   │   │  │   ├── specialty_detection.py - IN DEV
│   │   │  │   └── specialty_validation.py - IN DEV
│   │   │  └── query_analyst.py
│   │   └── sanity_checks/
│   │      ├── conversation_limit_check.py
│   │      ├── message_length_check.py
│   │      ├── message_pertinence_check.py
│   │      └── sanity_checks_analyst.py
│   ├── pydantic_models/
│   │   ├── query_model.py
│   │   └── response_model.py
│   ├── services/
│   │   ├── data_processing_service.py
│   │   ├── llm_handler_service.py
│   │   ├── pipeline_orchestrator_service.py
│   │   └── conversation_service.py
│   ├── snowflake_db/
│   │   ├── query.py
│   │   └── snowflake_connector.py
│   └── utils/
│       ├── distance_calc_helpers.py
│       │── formatting_helpers.py
│       │── llm_helpers.py
│       │── logging.py
│       │── prompt_formatting_helpers.py
│       │── prompt_instructions.py
│       │── specialty_dicts_lists.py
│       └── wrappers.py
├── Streamlit/
│   ├── st_app.py
│   ├── st_config.py
│   ├── st_ui_components.py
│   └── st_utility.py
├── data/
├── history/
└── tests/



# Installation (in dev)
If you want to launch the Streamlit app, you should create a python environnement with the packages from the "requirement.txt" file and then run the main.py file. 
Additionally, you will need an API Key from Open AI and paste it in the '.env' file  to use our model: "gpt-4o-mini".


# Running the app locally in your python terminal. 
1. Go to the project folder where you created your virtual environment and activate it: source chatbot_hop/bin/activate
   1. If you haven't set up your local environment, follow the below steps: 
      1. Navigate to your local project directory
      2. Create a new virtual environment named chatbot_hop : python3 -m venv chatbot_hop
      3. Activate the virtual environment: source chatbot_hop/bin/activate
      4. Install all required packages from requirements.txt: 
         1. pip install --upgrade pip
         2. pip install -r requirements.txt
2. To get FastAPI up and running : uvicorn main:app --reload
   1. Note: to get out of the FastAPI in the terminal, press CTRL+C
3. Navigate to another terminal (keep FastAPI running in original terminal) once the application is started up and activate your virtual environment again: source chatbot_hop/bin/activate
4. In the new terminal run the following: python3 test_api.py

**Note:** if you get an error about not having SSL certificates, run the following command in the terminal where you activated your python virtual environment: python -m pip install --upgrade certifi


# Code organization
This code base serves as the backend for the hospital ranking chatbot assistant for Le Point (chatbot hôpitaux). It includes the code to run the chat bot via a Streamlit application and FastAPI application. The Streamlit application is solely for functional testing purposes. The FastAPI application will be used in production. 

The Streamlit application entry point is in Streamlit/st_app.py.

The FastAPI application entry point is in main.py.

At a high level, here is how the chatbot works:
1. User asks a question 
2. The backend runs a variety of sanity checks.
   1. If any of the sanity checks fail, the user gets an automated response that their query is invalid. 
3. Then the backend will use the "gpt-4o-mini" LLM model to help detect potential mentions of location, medical specialty, type of institution (public/private), institution name, and the number of institutions the user would like to see in the response. 
4. Then the backend will get correct tables from the excel files and apply the proper filters and transformations to the tables to generate the list of institutions for the response and the relevant links in the hospital class ranking webpages. 
5. The backend puts together the final response to the user. 

The above process is managed by the PipelineOrchestrator class in app/services/pipeline_orchestrator.py which is called when creating both the Streamlit and FastAPI applications.

# Swagger Documentation 
To open Swagger UI on your browser: http://127.0.0.1:8000/docs
It will show the request/response schemas from your pydantic_models.

To open the ReDoc UI (spec-style documentation) in your browser: http://127.0.0.1:8000/redoc

# Docker
To build the docker image run: docker build -t my-chatbot:latest .
To run the Docker image locally: docker run -p 8000:8000 my-chatbot:latest
Health check: curl http://localhost:8000/health


# Contact
Anuradha (Annie) Passan - apassan@ext.lepoint.fr, apassan@eulidia.com
Benjamin L'Hyver - blhyver@eulidia.com
