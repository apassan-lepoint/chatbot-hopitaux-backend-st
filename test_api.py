import requests

API_URL = "http://localhost:8000"

# Test /ask endpoint
def test_ask():
    payload = {
        "prompt": "Quels sont les meilleurs hôpitaux à Paris pour la cancer de la vessie ?",
        #"prompt": "Quels sont les 10 meilleurs hôpitaux publics à Bordeaux pour les maladies cardiaques?",
        "detected_specialty": ""
    }
    response = requests.post(f"{API_URL}/ask", json=payload)
    print("/ask response:", response.status_code, response.json())

# Test /chat endpoint - only for multi-turn conversations
def test_chat():
    payload = {
        "prompt": "Et à Lyon?",
        "conversation": [["Quels sont les meilleurs hôpitaux à Paris?", "Voici la liste..."]]
    }
    response = requests.post(f"{API_URL}/chat", json=payload)
    print("/chat response:", response.status_code, response.json())

if __name__ == "__main__":
    test_ask()
    #test_chat()