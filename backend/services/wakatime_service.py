import httpx
from datetime import date

class WakaTimeService:
    def __init__(self):
        self.base_url = "https://wakatime.com/api/v1"

    async def fetch_coding_time(self, api_key: str, day: date, allowed_projects: list[str] = None) -> int:
        """
        Fetches coding seconds. If allowed_projects is provided, only counts time for those projects.
        """
        if not api_key:
            return 0
            
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
                if data.get("data") and len(data["data"]) > 0:
                    day_data = data["data"][0]
                    
                    # If Filtering Enabled
                    if allowed_projects:
                        total_filtered_seconds = 0
                        projects = day_data.get("projects", [])
                        
                        # Debug: Print what WakaTime returned vs what we are looking for
                        # (Optional, maybe verbose logging)
                        # print(f"WakaTime Projects: {[p['name'] for p in projects]}")
                        # print(f"Allowed Projects: {allowed_projects}")

                        # Normalize function for matching
                        def normalize(name):
                            return name.lower().replace("_", "").replace("-", "").replace(" ", "")

                        normalized_allowed = [normalize(p) for p in allowed_projects]

                        for proj in projects:
                            p_name = proj["name"]
                            # Check exact, normalized, or loose containment
                            norm_name = normalize(p_name)
                            
                            is_match = (
                                p_name in allowed_projects or 
                                norm_name in normalized_allowed
                            )
                            
                            if is_match:
                                total_filtered_seconds += proj["total_seconds"]
                        
                        return int(total_filtered_seconds)
                    
                    # Default: Grand Total
                    return int(day_data["grand_total"]["total_seconds"])
                return 0
            
            except httpx.HTTPError as e:
                print(f"WakaTime API Summaries Error: {e}")
                raise e

    async def fetch_durations(self, api_key: str, day: date) -> list:
        """
        Fetches granular 'durations' (time ticks) for deep work analysis.
        Return: List of duration dicts.
        """
        if not api_key: return []
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/users/current/durations",
                    params={
                        "date": day.isoformat(),
                        "api_key": api_key
                    }
                )
                if response.status_code == 402:
                    print("WakaTime Durations API requires Premium (402). Skipping deep work analysis.")
                    return [] 
                
                response.raise_for_status()
                data = response.json()
                return data.get("data", [])
            except Exception as e:
                print(f"WaKaTime Durations Error: {e}")
                return [] # Non-critical failure

    async def fetch_detailed_summary(self, api_key: str, day: date) -> dict:
        """
        Fetches the full summary object (languages, editors, etc) for storage.
        """
        if not api_key: return {}
        async with httpx.AsyncClient() as client:
            try:
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
                if data.get("data"):
                    return data["data"][0]
                return {}
            except Exception as e:
                print(f"WakaTime Detailed Summary Error: {e}")
                return {}
