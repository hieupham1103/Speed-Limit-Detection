from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session
import requests

import os
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
THING_ID = os.getenv("THING_ID")
PROPERTY_ID = os.getenv("PROPERTY_ID")

oauth_client = BackendApplicationClient(client_id=CLIENT_ID)
token_url = "https://api2.arduino.cc/iot/v1/clients/token"

oauth = OAuth2Session(client=oauth_client)
token = oauth.fetch_token(
    token_url=token_url,
    client_id= CLIENT_ID,
    client_secret=CLIENT_SECRET,
    include_client_id=True,
    audience="https://api2.arduino.cc/iot",
)

# store access token in access_token variable
access_token = token.get("access_token")

url = f"https://api2.arduino.cc/iot/v2/things/{THING_ID}/properties/{PROPERTY_ID}"

headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json"
}

response = requests.get(url, headers=headers)
if response.status_code == 200:
    data = response.json()
    # In ra giá trị của thuộc tính (ví dụ: gia tốc)
    print("Property Data:", data)
else:
    print("Error:", response.status_code, response.text)