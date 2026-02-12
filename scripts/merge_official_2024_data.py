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
    categories = [
        (40, "Annihilation", "Democratic", "D_ANNIHILATION", "#08519c"),
        (20, "Dominant", "Democratic", "D_DOMINANT", "#3182bd"),
        (10, "Safe", "Democratic", "D_SAFE", "#6baed6"),
        (5, "Likely", "Democratic", "D_LIKELY", "#9ecae1"),
        (2, "Lean", "Democratic", "D_LEAN", "#c6dbef"),
        (-2, "Tossup", "Tossup", "TOSSUP", "#f7f7f7"),
        (-5, "Lean", "Republican", "R_LEAN", "#fee5d9"),
        (-10, "Likely", "Republican", "R_LIKELY", "#fcae91"),
        (-20, "Safe", "Republican", "R_SAFE", "#fb6a4a"),
        (-40, "Dominant", "Republican", "R_DOMINANT", "#cb181d"),
        (float('-inf'), "Annihilation", "Republican", "R_ANNIHILATION", "#67000d"),
    ]
    
    for threshold, category, party, code, color in categories:
        if margin_pct > threshold:
            return {
                "category": category,
                "party": party,
                "code": code,
                "color": color
            }
    
    return {
        "category": "Annihilation",
        "party": "Republican",
        "code": "R_ANNIHILATION",
        "color": "#67000d"
    }


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


def get_full_office_name(office):
    """Get full office name for display."""
    office_map = {
        "president": "President of the United States",
        "us_senate": "United States Senator",
        "attorney_general": "Attorney General",
        "auditor_general": "Auditor General",
        "state_treasurer": "State Treasurer",
    }
    return office_map.get(office, office.title())


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
        
        if county not in aggregated[2024][office]:
            aggregated[2024][office][county] = {
                "dem_votes": 0,
                "rep_votes": 0,
                "other_votes": 0,
                "dem_candidate": None,
                "rep_candidate": None,
            }
        
        # Categorize by party
        if 'Democratic' in party:
            aggregated[2024][office][county]["dem_votes"] += votes
            aggregated[2024][office][county]["dem_candidate"] = candidate
        elif 'Republican' in party:
            aggregated[2024][office][county]["rep_votes"] += votes
            aggregated[2024][office][county]["rep_candidate"] = candidate
        else:
            # All other parties (Libertarian, Green, Constitution, etc.)
            aggregated[2024][office][county]["other_votes"] += votes
    
    return aggregated


def format_result_entry(county_name, contest, office, data, year=2024):
    """Format a single result entry matching JSON structure."""
    dem_votes = data.get("dem_votes", 0)
    rep_votes = data.get("rep_votes", 0)
    other_votes = data.get("other_votes", 0)
    total_votes = dem_votes + rep_votes + other_votes
    two_party_total = dem_votes + rep_votes
    
    if two_party_total == 0:
        return None
    
    margin = dem_votes - rep_votes
    margin_pct = (margin / two_party_total * 100) if two_party_total > 0 else 0
    
    # Determine winner
    winner = "DEM" if dem_votes > rep_votes else ("REP" if rep_votes > dem_votes else "TIE")
    
    return {
        "county": county_name,
        "contest": get_full_office_name(office),
        "year": str(year),
        "dem_candidate": data.get("dem_candidate", "Unknown"),
        "rep_candidate": data.get("rep_candidate", "Unknown"),
        "dem_votes": dem_votes,
        "rep_votes": rep_votes,
        "other_votes": other_votes,
        "total_votes": total_votes,
        "two_party_total": two_party_total,
        "margin": margin,
        "margin_pct": round(margin_pct, 2),
        "winner": winner,
        "competitiveness": get_competitiveness(margin_pct),
        "all_parties": {
            "DEM": dem_votes,
            "REP": rep_votes,
            "OTHER": other_votes,
        }
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
    
    # Ensure 2024 is in metadata
    if 2024 not in data.get("metadata", {}).get("years", []):
        if "metadata" not in data:
            data["metadata"] = {}
        if "years" not in data["metadata"]:
            data["metadata"]["years"] = []
        if 2024 not in data["metadata"]["years"]:
            data["metadata"]["years"].append(2024)
            data["metadata"]["years"].sort()
    
    # Clear existing 2024 data
    if 2024 in data["results_by_year"]:
        print("[INFO] Clearing existing 2024 data...")
        data["results_by_year"][2024] = {}
    else:
        data["results_by_year"][2024] = {}
        if "results_by_year" not in data:
            data["results_by_year"] = {}
        data["results_by_year"][2024] = {}
    
    # Track updates
    new_entries = 0
    counties_updated = set()
    
    # Build 2024 data from scratch with proper structure
    for office, counties in csv_aggregated[2024].items():
        # Initialize office structure
        if office not in data["results_by_year"][2024]:
            data["results_by_year"][2024][office] = {}
        
        contest_key = f"{office}_2024"
        
        # Create contest entry
        data["results_by_year"][2024][office][contest_key] = {
            "contest_name": get_full_office_name(office),
            "results": {}
        }
        
        for county, county_data in counties.items():
            formatted = format_result_entry(county, contest_key, office, county_data)
            if formatted:
                data["results_by_year"][2024][office][contest_key]["results"][county] = formatted
                new_entries += 1
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
    print(f"  - Entries created: {new_entries}")
    print(f"  - Unique counties with 2024 data: {len(counties_2024)}/67")
    print(f"  - Sample counties: {sorted(list(counties_2024))[:5]}")


if __name__ == "__main__":
    merge_data()
