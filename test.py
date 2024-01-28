import requests

URL = 'http://localhost:8080/play'
data = {'bpm': 120}

try:
    response = requests.post(URL, json=data)
    response.raise_for_status()
    print("Response:", response.text)
except Exception as e:
    print("An error occurred:", e)