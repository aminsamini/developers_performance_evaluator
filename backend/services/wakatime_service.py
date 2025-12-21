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

                        for proj in projects:
                            # Loose matching: check if project name is in our allowed list
                            # WakaTime often uses just directory name. 
                            # allowed_projects should likely contain both "owner/repo" and "repo".
                            if proj["name"] in allowed_projects:
                                total_filtered_seconds += proj["total_seconds"]
                        
                        return int(total_filtered_seconds)
                    
                    # Default: Grand Total
                    return int(day_data["grand_total"]["total_seconds"])
                return 0
            
            except httpx.HTTPError as e:
                print(f"WakaTime API Error: {e}")
                raise e # Propagate error for atomic sync rollback
