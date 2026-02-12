import requests
from bs4 import BeautifulSoup
import json
import csv
from collections import defaultdict

# Scrape PA Election Returns for 2024 county-level data
# Target: Auditor General and State Treasurer results

def scrape_county_results(election_id, race_name):
    """
    Scrape PA election results by county
    election_id: ID for the election (105 = 2024 General)
    race_name: Name of the race (auditor_general, state_treasurer, etc)
    """
    base_url = "https://www.electionreturns.pa.gov/General/SummaryResults"
    
    params = {
        'ElectionID': election_id,
        'ElectionType': 'G',
        'IsActive': 0
    }
    
    print(f"\nScraping {race_name.replace('_', ' ').title()}...")
    
    try:
        response = requests.get(base_url, params=params, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Look for county breakdown data
        # The page structure may have tables or data attributes
        # This is a starting point - we'll need to inspect the actual HTML
        
        print(f"✓ Successfully fetched page for {race_name}")
        print("Response length:", len(response.text), "bytes")
        
        # Try to find race section
        race_section = soup.find('h5', string=lambda x: x and race_name.replace('_', ' ').title() in x if x else False)
        
        if race_section:
            print(f"✓ Found {race_name} section")
            # Look for county breakdown link or data
            county_breakdown = race_section.find_next('a', string=lambda x: x and 'County Breakdown' in x if x else False)
            if county_breakdown:
                county_url = county_breakdown.get('href')
                print(f"✓ County breakdown URL: {county_url}")
                return county_url
        else:
            print(f"✗ Could not find {race_name} section")
            # Print available headings for debugging
            headings = soup.find_all('h5')
            print(f"Available sections: {[h.text for h in headings[:10]]}")
        
        return None
        
    except Exception as e:
        print(f"✗ Error scraping {race_name}: {e}")
        return None


def parse_html_table(html_content, race_name):
    """Parse HTML table from county breakdown page"""
    soup = BeautifulSoup(html_content, 'html.parser')
    counties_data = {}
    
    # Look for table with county results
    tables = soup.find_all('table')
    print(f"Found {len(tables)} tables on page")
    
    for table in tables:
        rows = table.find_all('tr')
        if len(rows) > 0:
            # Try to parse county name and results
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    # Likely format: County Name | Candidate Results...
                    first_cell = cells[0].text.strip()
                    if first_cell and 'County' in first_cell:
                        # This is probably the county name
                        county_name = first_cell.replace(' County', '')
                        print(f"  Found: {county_name}")
    
    return counties_data


# Test the scraper
if __name__ == "__main__":
    print("=" * 60)
    print("PA Election Returns Scraper (2024 County Data)")
    print("=" * 60)
    
    # 2024 General Election ID
    election_id = 105
    
    # Try to get Auditor General data
    print("\n[1] Attempting to scrape Auditor General data...")
    auditor_url = scrape_county_results(election_id, "auditor_general")
    
    # Try to get State Treasurer data
    print("\n[2] Attempting to scrape State Treasurer data...")
    treasurer_url = scrape_county_results(election_id, "state_treasurer")
    
    print("\n" + "=" * 60)
    print("NOTES:")
    print("=" * 60)
    print("The PA Election Returns site uses JavaScript to load county data.")
    print("A simple BeautifulSoup scraper may not capture the content.")
    print("\nAlternative approaches:")
    print("1. Use Selenium or Playwright for JavaScript rendering")
    print("2. Check if PA provides CSV exports")
    print("3. Consult the Network tab (inspect element) for API calls")
    print("4. Download from PA Department of State directly")
