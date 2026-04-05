import httpx
import asyncio
import json

async def test_geocoding(lat, lon):
    headers = {"User-Agent": "NeuroVitals/1.0 (PuneHack)"}
    async with httpx.AsyncClient() as client:
        url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}"
        print(f"Requesting: {url}")
        geo_resp = await client.get(url, headers=headers, timeout=10.0)
        if geo_resp.status_code == 200:
            geo_data = geo_resp.json()
            print(json.dumps(geo_data, indent=2))
        else:
            print(f"Error: {geo_resp.status_code}")
            print(geo_resp.text)

if __name__ == "__main__":
    lat = 20.5582638
    lon = 78.5852114
    asyncio.run(test_geocoding(lat, lon))
