"""
Merge official 2024 PA election data from CSV into pa_election_results.json
Fills in missing county-level data for the 10 counties not in OpenElections precinct files.
"""

import pandas as pd
import json
from pathlib import Path
from collections import defaultdict

def get_competitiveness(margin_pct):
    """Categorize race competitiveness based on Democratic margin percentage."""
    if margin_pct > 40:
        return {"category": "Annihilation", "party": "Democratic"}
    elif margin_pct > 20:
        return {"category": "Dominant", "party": "Democratic"}
    elif margin_pct > 10:
        return {"category": "Safe", "party": "Democratic"}
    elif margin_pct > 5:
        return {"category": "Likely", "party": "Democratic"}
    elif margin_pct > 2:
        return {"category": "Lean", "party": "Democratic"}
    elif margin_pct > -2:
        return {"category": "Tossup", "party": "Tossup"}
    elif margin_pct > -5:
        return {"category": "Lean", "party": "Republican"}
    elif margin_pct > -10:
        return {"category": "Likely", "party": "Republican"}
    elif margin_pct > -20:
        return {"category": "Safe", "party": "Republican"}
    elif margin_pct > -40:
        return {"category": "Dominant", "party": "Republican"}
    else:
        return {"category": "Annihilation", "party": "Republican"}


def normalize_office_name(office):
    """Normalize office names to match existing JSON structure."""
    office_map = {
        "President of the United States": "president",
        "United States Senator": "us_senate",
        "Attorney General": "attorney_general",
        "Auditor General": "auditor_general",
        "State Treasurer": "state_treasurer",
    }
    return office_map.get(office, office.lower().replace(" ", "_"))


def load_official_csv(csv_path):
    """Load and parse the official PA election CSV."""
    df = pd.read_csv(csv_path)
    return df


def aggregate_csv_data(df):
    """Aggregate CSV data by office and county, summing across parties."""
    # Convert votes to numeric, handling commas
    df['Votes'] = pd.to_numeric(df['Votes'].astype(str).str.replace(',', ''), errors='coerce').fillna(0).astype(int)
    
    aggregated = defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))
    
    for _, row in df.iterrows():
        county = row['County Name'].title()
        office = normalize_office_name(row['Office Name'])
        party = row['Party Name']
        candidate = row['Candidate Name'].title()
        votes = row['Votes']
        
        key = f"{office}_2024"
        
        if county not in aggregated[2024][office]:
            aggregated[2024][office][county] = {
                "dem_votes": 0,
                "rep_votes": 0,
                "other_votes": 0,
                "dem_candidate": None,
                "rep_candidate": None,
            }
        
        # Categorize by party
        if 'Democratic' in party or 'HARRIS' in candidate or 'CASEY' in candidate or 'DEPASQUALE' in candidate or 'KENYATTA' in candidate or 'MCCLELLAND' in candidate:
            aggregated[2024][office][county]["dem_votes"] += votes
            aggregated[2024][office][county]["dem_candidate"] = candidate
        elif 'Republican' in party or 'TRUMP' in candidate or 'MCCORMICK' in candidate or 'SUNDAY' in candidate or 'DEFOOR' in candidate or 'GARRITY' in candidate:
            aggregated[2024][office][county]["rep_votes"] += votes
            aggregated[2024][office][county]["rep_candidate"] = candidate
        else:
            aggregated[2024][office][county]["other_votes"] += votes
    
    return aggregated


def format_result_entry(county_name, contest, office, data, year=2024):
    """Format a single result entry matching JSON structure."""
    dem_votes = data.get("dem_votes", 0)
    rep_votes = data.get("rep_votes", 0)
    total_votes = dem_votes + rep_votes
    
    if total_votes == 0:
        return None
    
    margin = dem_votes - rep_votes
    margin_pct = (margin / total_votes * 100) if total_votes > 0 else 0
    
    return {
        "county": county_name,
        "contest": office,
        "dem_candidate": data.get("dem_candidate", "Unknown"),
        "rep_candidate": data.get("rep_candidate", "Unknown"),
        "dem_votes": dem_votes,
        "rep_votes": rep_votes,
        "margin": margin,
        "margin_pct": round(margin_pct, 2),
        "competitiveness": get_competitiveness(margin_pct),
    }


def merge_data():
    """Main merge function."""
    # Load paths
    json_file = Path(__file__).parent.parent / "data" / "pa_election_results.json"
    csv_file = Path(__file__).parent.parent / "data" / "Official_2112026091549PM.CSV"
    
    print(f"[INFO] Loading official CSV from {csv_file}...")
    csv_df = load_official_csv(csv_file)
    print(f"[INFO] CSV has {len(csv_df)} rows across {csv_df['County Name'].nunique()} counties")
    
    # Aggregate CSV data
    print("[INFO] Aggregating CSV data by office and county...")
    csv_aggregated = aggregate_csv_data(csv_df)
    
    # Load existing JSON
    print(f"[INFO] Loading existing JSON from {json_file}...")
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    # Track updates
    update_count = 0
    new_entries = 0
    counties_updated = set()
    
    # Merge 2024 data
    for office, counties in csv_aggregated[2024].items():
        if 2024 not in data["results_by_year"]:
            data["results_by_year"][2024] = {}
        
        if office not in data["results_by_year"][2024]:
            data["results_by_year"][2024][office] = {}
        
        contest_key = f"{office}_2024"
        
        if contest_key not in data["results_by_year"][2024][office]:
            data["results_by_year"][2024][office][contest_key] = {"results": {}}
        
        for county, county_data in counties.items():
            if county not in data["results_by_year"][2024][office][contest_key]["results"]:
                # New entry
                formatted = format_result_entry(county, contest_key, office, county_data)
                if formatted:
                    data["results_by_year"][2024][office][contest_key]["results"][county] = formatted
                    new_entries += 1
                    counties_updated.add(county)
            else:
                # Update existing (in case data is more complete)
                data["results_by_year"][2024][office][contest_key]["results"][county].update({
                    "dem_votes": county_data.get("dem_votes", 0),
                    "rep_votes": county_data.get("rep_votes", 0),
                    "dem_candidate": county_data.get("dem_candidate"),
                    "rep_candidate": county_data.get("rep_candidate"),
                })
                update_count += 1
                counties_updated.add(county)
    
    # Save updated JSON
    print(f"[INFO] Saving merged data to {json_file}...")
    with open(json_file, 'w') as f:
        json.dump(data, f, indent=2)
    
    # Count final coverage
    counties_2024 = set()
    for office in data["results_by_year"].get(2024, {}).values():
        for contest in office.values():
            counties_2024.update(contest.get("results", {}).keys())
    
    print(f"\n[SUCCESS] Merge complete!")
    print(f"  - New entries added: {new_entries}")
    print(f"  - Entries updated: {update_count}")
    print(f"  - Unique counties updated: {len(counties_updated)}")
    print(f"  - Total PA counties with 2024 data: {len(counties_2024)}/67")
    print(f"  - Counties updated: {sorted(counties_updated)}")


if __name__ == "__main__":
    merge_data()
