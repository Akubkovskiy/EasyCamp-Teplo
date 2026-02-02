
import asyncio
import requests
import sys

# Set output encoding to utf-8
sys.stdout.reconfigure(encoding='utf-8')

from app.services.avito_api_service import avito_api_service

async def liast_items():
    print("Listing Avito items (Attempt 3)...")
    token = avito_api_service.get_access_token()
    url = "https://api.avito.ru/core/v1/items"
    
    try:
        resp = requests.get(
            url,
            headers={"Authorization": f"Bearer {token}"},
            params={"per_page": 100, "status": "active"} 
        )
        if resp.status_code != 200:
            print(f"Error: {resp.status_code} {resp.text}")
        else:
            data = resp.json()
            items = data.get('resources', [])
            print(f"Found {len(items)} active items:")
            for item in items:
                print(f"ID: {item.get('id')} - Title: {item.get('title')}")
                
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    asyncio.run(liast_items())
