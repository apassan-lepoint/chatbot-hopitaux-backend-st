README

# Description
The hospital ranking assistant allows interaction with Le Point's hospital rankings and exploration of its content. It enables users to ask questions to query one of the rankings and continue the conversation based on the results of the initial question. It is currently accessible through a simple Streamlit application, serving as a user interface for testing and in production mode via FastAPI (in development).

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
│   │   ├── dependencies.py 
│   │   └── routes.py
│   ├── db/
│   │   ├── query.py
│   │   └── snowflake_connector.py
│   ├── models/
│   │   ├── query_model.py
│   │   └── response_model.py
│   ├── services/
│   │   ├── query_extraction_service.py
│   │   ├── conversation_service.py
│   │   ├── llm_handler_service.py
│   │   ├── pipeline_service.py
│   │   └── data_processing_service.py
│   └── ui/
│       ├── streamlit_app.py
│   └── utils/
│       ├── query_detection/
│       │   ├── institutions.py
│       │   ├── prompt_formatting.py
│       │   ├── PROMPT_INSTRUCTIONS.py
│       │   └── specialties.py
│       ├── sanity_checks/
│       │   ├── core_logic_sanity_checks.py
│       │   ├── fast_api_sanity_checks.py
│       │   └── streamlit_sanity_checks.py
│       ├── config.py
│       ├── distance.py
│       ├── formatting.py
│       └── logging.py
├── data/
├── history/
├── tests/



# Installation
If you want to launch the Streamlit app, you should create a python environnement named 'chop_venv' with the package from the "requirement.txt" file. 
You should as well get an API Key from Open AI and paste it in the '.env' file  to use our model: "gpt-4o-mini".

# Usage - EDIT 
Here are the commands to launch the Streamlit app from the terminal anaconda for example: 
- input "conda activate chop_venv"
Copy the path of the Front folder
- input "cd app/ui/streamlit_app.py"
- input "streamlit run app/ui/streamlit_app.py"
- ask your question

# Code organization
UPDATE!!!! - give high level overview of how code works

# Contact
Anuradha (Annie) Passan - apassan@ext.lepoint.fr, apassan@eulidia.com
Maxime Kermagoet - mkermagoret@ext.lepoint.fr, mkermagoret@eulidia.com
Benjamin L'Hyver - blhyver@eulidia.com


## Files to maybe add
**app/api/dependencies.py**
Defines reusable dependencies for FastAPI routes.
This file contains functions and classes that provide shared logic or resources
to be injected into API endpoints, such as authentication, database sessions, or configuration.



Modularisation du code basé sur les retours de Benjamin 


backend_chatbot_hopitaux
├── README.md
├── Dockerfile.yaml
├── requirements.txt
├── .env
├── .gitignore
├── main.py
├── config
│   ├── features_config.py
│   └── file_paths_config.py
├── app
│   ├── api
│   │   └── routes.py
│   ├── snowflake_db
│   │   ├── snowflake_connect.py
│   │   └── snowflake_query.py
│   ├── pydantic_models
│   │   ├── query_model.py
│   │   └── response_model.py
│   ├── services
│   │   ├── llm_handler_service.py
│   │   ├── data_processing_service.py
│   │   └── pipeline_orchestrator_service.py
│   ├── utility
│   │   ├── fast_api_utility.py
│   │   ├── geo_utility.py
│   │   ├── formatting_utility.py
│   │   ├── logging_utility.py
│   │   └── prompt_utility.py
│   └── features
│       ├── conversation
│       │   ├── conversation_manager.py
│       │   └── multi_turn.py
│       ├── checks
│       │   ├── sanity_checks_manager.py
│       │   ├── message_length_check.py
│       │   ├── conversation_limit_check.py
│       │   └── relevance_check.py
│       └── prompt_detection
│           ├── prompt_detection_manager.py
│           ├── specialty_detection.py
│           ├── city_detection.py
│           ├── kpop_detection.py
│           ├── institution_type_detection.py
│           └── institution_type_detection.py
├── streamlit
│   ├── streamlit_ui.py
│   └── streamlit_utility.py
├── tests
├── data
└── history