"""
Fetch 2024 county-level election data from PA Election Returns
by querying their API directly
"""

import requests
import json
import pandas as pd
from datetime import datetime

def fetch_2024_county_data(race_name, race_id):
    """
    Attempt to fetch county breakdown from PA election returns API
    
    Common race IDs for 2024:
    - President: appears in main data
    - US Senate: appears in main data  
    - Attorney General, Auditor General, State Treasurer: need specific IDs
    """
    
    # The electionreturns.pa.gov site appears to load data via JSON API
    # Try different API endpoints
    
    api_urls = [
        f"https://www.electionreturns.pa.gov/api/electionData?electionID=105&raceID={race_id}",
        f"https://www.electionreturns.pa.gov/General/api/SummaryResults?ElectionID=105&raceID={race_id}",
        f"https://www.electionreturns.pa.gov/General/SummaryResults/Summary?ElectionID=105",
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    print(f"\nFetching 2024 {race_name}...")
    print(f"Race ID: {race_id}")
    
    for url in api_urls:
        try:
            print(f"  Trying: {url}")
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            print(f"  ✓ Status: {response.status_code}")
            print(f"  Content length: {len(response.text)} bytes")
            
            # Try to parse as JSON
            data = response.json()
            print(f"  ✓ Valid JSON received")
            print(f"  Keys: {list(data.keys())[:5]}")
            
            # Save response for inspection
            with open(f'2024_{race_name}_raw.json', 'w') as f:
                json.dump(data, f, indent=2)
            print(f"  Saved to: 2024_{race_name}_raw.json")
            
            return data
            
        except requests.exceptions.RequestException as e:
            print(f"  ✗ Request error: {e}")
            continue
        except json.JSONDecodeError as e:
            print(f"  ✗ JSON error: {e}")
            continue
        except Exception as e:
            print(f"  ✗ Unexpected error: {e}")
            continue
    
    print(f"  ✗ Could not fetch {race_name}")
    return None


def find_missing_counties_in_api(response_data):
    """Parse API response to find county-level data"""
    if not response_data:
        return []
    
    # Look for common patterns where counties might be stored
    patterns = [
        'counties', 'results', 'data', 'races', 'candidates', 
        'county_results', 'county_breakdown', 'by_county'
    ]
    
    def search_for_counties(obj, depth=0):
        """Recursively search for county data"""
        if depth > 5:  # Prevent infinite recursion
            return []
        
        counties = []
        
        if isinstance(obj, dict):
            for key, value in obj.items():
                if 'county' in key.lower() or isinstance(value, dict):
                    if isinstance(value, dict):
                        counties.extend(search_for_counties(value, depth + 1))
        elif isinstance(obj, list) and len(obj) > 0:
            for item in obj[:5]:  # Sample first 5
                if isinstance(item, dict):
                    counties.extend(search_for_counties(item, depth + 1))
        
        return counties
    
    return search_for_counties(response_data)


if __name__ == "__main__":
    print("=" * 70)
    print("PA 2024 Election County-Level Data Fetcher")
    print("=" * 70)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Target: Missing county data for 2024")
    print(f"Missing: Cameron, Clarion, Columbia, Crawford, Erie, Forest,")
    print(f"         Jefferson, Montgomery, Sullivan, Wayne")
    
    # Try to fetch data for the three statewide races
    races = [
        ("Auditor General", "auditor_general"),
        ("State Treasurer", "state_treasurer"),
        ("Attorney General", "attorney_general"),
    ]
    
    for race_name, race_slug in races:
        # Try various race IDs (these are guesses - actual IDs may differ)
        for race_id in range(1, 10):
            result = fetch_2024_county_data(race_name, race_id)
            if result:
                break
    
    print("\n" + "=" * 70)
    print("MANUAL DATA COLLECTION RECOMMENDED")
    print("=" * 70)
    print("""
The PA election returns site loads data dynamically via JavaScript.
To get the missing county data:

1. Visit: https://www.electionreturns.pa.gov/General/SummaryResults?ElectionID=105&ElectionType=G&IsActive=0
2. Open browser DevTools (F12) → Network tab
3. Click "County Breakdown" for Auditor General
4. Look for XHR/Fetch requests - copy county-level JSON
5. Repeat for State Treasurer

OR contact PA Department of State for CSV export of county results.
""")
