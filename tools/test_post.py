import requests
import json

url = "http://127.0.0.1:8000/api/chat"
headers = {"Content-Type": "application/json"}
body = {
    "question": "Tôi muốn biết thức ăn cho đàn ASSET_HEO_001",
    "email": "worker1@farmA.com",
    "facilityID": "farm-a"
}

try:
    r = requests.post(url, headers=headers, json=body, timeout=10)
    print("STATUS:", r.status_code)
    try:
        print(json.dumps(r.json(), ensure_ascii=False, indent=2))
    except Exception:
        print(r.text)
except Exception as e:
    print('Request error:', e)

