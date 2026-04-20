import os
import requests
from dotenv import load_dotenv

# Try current dir, then parent dir
load_dotenv()
if not os.getenv("X_BEARER_TOKEN"):
    load_dotenv("../.env")

BEARER_TOKEN = os.getenv("X_BEARER_TOKEN")

def fetch_user_info(username="alhrkn"):
    if not BEARER_TOKEN:
        print("Error: X_BEARER_TOKEN not found in .env")
        return

    url = f"https://api.twitter.com/2/users/by/username/{username}"
    headers = {
        "Authorization": f"Bearer {BEARER_TOKEN}"
    }
    params = {
        "user.fields": "created_at,description,public_metrics,verified"
    }

    print(f"Fetching info for @{username}...")
    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        data = response.json()
        print("\n--- User Data ---")
        print(f"Name: {data['data']['name']}")
        print(f"ID: {data['data']['id']}")
        print(f"Bio: {data['data']['description']}")
        print(f"Followers: {data['data']['public_metrics']['followers_count']}")
        print(f"Created At: {data['data']['created_at']}")
    else:
        print(f"Error {response.status_code}: {response.text}")

if __name__ == "__main__":
    fetch_user_info()
