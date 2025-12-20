import httpx
from datetime import date

class WakaTimeService:
    def __init__(self):
        self.base_url = "https://wakatime.com/api/v1"

    async def fetch_coding_time(self, api_key: str, day: date) -> int:
        """
        Fetches the total coding seconds for a specific day using the user's API Key.
        """
        if not api_key:
            return 0
            
        headers = {"Authorization": f"Basic {api_key}"} # Converting key to b64 if needed, but WakaTime usually accepts header or param.
        # Actually WakaTime API usually takes 'api_key' as query param or Bearer.
        # API Key method: Base64 encode the API key.
        # Easier method: query param ?api_key=...
        
        async with httpx.AsyncClient() as client:
            try:
                # Get summaries for the specific date
                response = await client.get(
                    f"{self.base_url}/users/current/summaries",
                    params={
                        "start": day.isoformat(),
                        "end": day.isoformat(),
                        "api_key": api_key
                    }
                )
                response.raise_for_status()
                data = response.json()
                
                # Parse total seconds from the first day in data
                if data.get("data"):
                    return int(data["data"][0]["grand_total"]["total_seconds"])
                return 0
            
            except httpx.HTTPError as e:
                print(f"WakaTime API Error: {e}")
                return 0
