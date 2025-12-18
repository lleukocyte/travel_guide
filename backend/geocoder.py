import asyncio
import os
from typing import Optional, Tuple, Dict
from dotenv import load_dotenv
import httpx

load_dotenv()

YANDEX_GEOCODER_API_KEY = os.getenv("GEOCODER_API_KEY")
GEOCODER_URL = "https://geocode-maps.yandex.ru/1.x/"

class YandexGeocoder:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = GEOCODER_URL
    
    async def geocode_address(self, city: str, address: str) -> Optional[Tuple[float, float]]:
        if not self.api_key:
            print("API ключ Яндекс.Карт не настроен")
            return None
        
        full_address = f"{city}, {address}"
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(self.base_url, params={
                    "apikey": self.api_key,
                    "geocode": full_address,
                    "format": "json",
                    "lang": "ru_RU",
                    "results": 1
                })
                
                if response.status_code == 200:
                    data = response.json()
                    
                    features = data.get("response", {}).get("GeoObjectCollection", {}).get("featureMember", [])
                    
                    if features:
                        geo_object = features[0]["GeoObject"]
                        pos = geo_object["Point"]["pos"]
                        
                        lon, lat = map(float, pos.split())
                        
                        return [lat, lon]
                    else:
                        return None
                else:
                    print(f"Ошибка геокодера: {response.status_code}")
                    return None
                    
        except Exception as e:
            print(f"Ошибка при геокодировании {full_address}: {str(e)}")
            return None
    
geocoder = YandexGeocoder(YANDEX_GEOCODER_API_KEY)