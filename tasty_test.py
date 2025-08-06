from dotenv import load_dotenv
import os
import requests

load_dotenv()
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')

url = "https://naveropenapi.apigw.ntruss.com/map-geocode/v2/geocode"
headers = {
    'X-NCP-APIGW-API-KEY-ID': CLIENT_ID,
    'X-NCP-APIGW-API-KEY': CLIENT_SECRET
}
params = {'query': '전북특별자치도 전주시 완산구 홍산중앙로 37'}
response = requests.get(url, headers=headers, params=params)
print(response.status_code)
print(response.json())
