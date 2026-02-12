"""
Merge official 2022 PA election data from CSV into pa_election_results.json
Updates 2022 data with official county-level results.
"""

import json
from collections import defaultdict
from pathlib import Path

import pandas as pd


def get_competitiveness(margin_pct):
    """Categorize race competitiveness based on Democratic margin percentage."""
    # Democratic categories (positive margin)
    if margin_pct >= 40:
        return {"category": "Annihilation Democratic", "party": "Democratic", "code": "D_ANNIHILATION", "color": "#08306b"}
    elif margin_pct >= 30:
        return {"category": "Dominant Democratic", "party": "Democratic", "code": "D_DOMINANT", "color": "#08519c"}
    elif margin_pct >= 20:
        return {"category": "Stronghold Democratic", "party": "Democratic", "code": "D_STRONGHOLD", "color": "#3182bd"}
    elif margin_pct >= 10:
        return {"category": "Safe Democratic", "party": "Democratic", "code": "D_SAFE", "color": "#6baed6"}
    elif margin_pct >= 5.5:
        return {"category": "Likely Democratic", "party": "Democratic", "code": "D_LIKELY", "color": "#9ecae1"}
    elif margin_pct >= 1:
        return {"category": "Lean Democratic", "party": "Democratic", "code": "D_LEAN", "color": "#c6dbef"}
    elif margin_pct >= 0.5:
        return {"category": "Tilt Democratic", "party": "Democratic", "code": "D_TILT", "color": "#e1f5fe"}
    # Tossup
    elif margin_pct > -0.5:
        return {"category": "Tossup", "party": "Tossup", "code": "TOSSUP", "color": "#f7f7f7"}
    # Republican categories (negative margin)
    elif margin_pct > -1:
        return {"category": "Tilt Republican", "party": "Republican", "code": "R_TILT", "color": "#fee8c8"}
    elif margin_pct > -5.5:
        return {"category": "Lean Republican", "party": "Republican", "code": "R_LEAN", "color": "#fcae91"}
    elif margin_pct > -10:
        return {"category": "Likely Republican", "party": "Republican", "code": "R_LIKELY", "color": "#fb6a4a"}
    elif margin_pct > -20:
        return {"category": "Safe Republican", "party": "Republican", "code": "R_SAFE", "color": "#ef3b2c"}
    elif margin_pct > -30:
        return {"category": "Stronghold Republican", "party": "Republican", "code": "R_STRONGHOLD", "color": "#cb181d"}
    elif margin_pct > -40:
        return {"category": "Dominant Republican", "party": "Republican", "code": "R_DOMINANT", "color": "#a50f15"}
    else:
        return {"category": "Annihilation Republican", "party": "Republican", "code": "R_ANNIHILATION", "color": "#67000d"}


def normalize_office_name(office):
    """Normalize office names to match existing JSON structure."""
    office_map = {
        "President of the United States": "president",
        "United States Senator": "us_senate",
        "Attorney General": "attorney_general",
        "Auditor General": "auditor_general",
        "State Treasurer": "state_treasurer",
        "Governor": "governor",
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
        "governor": "Governor",
    }
    return office_map.get(office, office.title())


def load_official_csv(csv_path):
    """Load and parse the official PA election CSV."""
    return pd.read_csv(csv_path)


def aggregate_csv_data(df):
    """Aggregate CSV data by office and county, summing across parties."""
    df["Votes"] = pd.to_numeric(df["Votes"].astype(str).str.replace(",", ""), errors="coerce").fillna(0).astype(int)

    aggregated = defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))

    for _, row in df.iterrows():
        county = row["County Name"].title()
        office = normalize_office_name(row["Office Name"])
        party = row["Party Name"]
        candidate = row["Candidate Name"].title()
        votes = row["Votes"]

        if county not in aggregated[2022][office]:
            aggregated[2022][office][county] = {
                "dem_votes": 0,
                "rep_votes": 0,
                "other_votes": 0,
                "dem_candidate": None,
                "rep_candidate": None,
            }

        if "Democratic" in party:
            aggregated[2022][office][county]["dem_votes"] += votes
            aggregated[2022][office][county]["dem_candidate"] = candidate
        elif "Republican" in party:
            aggregated[2022][office][county]["rep_votes"] += votes
            aggregated[2022][office][county]["rep_candidate"] = candidate
        else:
            aggregated[2022][office][county]["other_votes"] += votes

    return aggregated


def format_result_entry(county_name, office, data, year=2022):
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
        },
    }


def merge_data():
    """Main merge function."""
    json_file = Path(__file__).parent.parent / "data" / "pa_election_results.json"
    csv_file = Path(__file__).parent.parent / "data" / "Official_2112026100831PM.CSV"

    print(f"[INFO] Loading official CSV from {csv_file}...")
    csv_df = load_official_csv(csv_file)
    print(f"[INFO] CSV has {len(csv_df)} rows across {csv_df['County Name'].nunique()} counties")

    print("[INFO] Aggregating CSV data by office and county...")
    csv_aggregated = aggregate_csv_data(csv_df)

    print(f"[INFO] Loading existing JSON from {json_file}...")
    with open(json_file, "r") as f:
        data = json.load(f)

    # Ensure 2022 is in metadata
    if 2022 not in data.get("metadata", {}).get("years", []):
        data.setdefault("metadata", {}).setdefault("years", []).append(2022)
        data["metadata"]["years"].sort()

    # Clear existing 2022 data
    data.setdefault("results_by_year", {})
    if "2022" in data["results_by_year"]:
        print("[INFO] Clearing existing 2022 data...")
        data["results_by_year"]["2022"] = {}
    else:
        data["results_by_year"]["2022"] = {}

    new_entries = 0
    counties_updated = set()

    for office, counties in csv_aggregated[2022].items():
        data["results_by_year"]["2022"].setdefault(office, {})
        contest_key = f"{office}_2022"
        data["results_by_year"]["2022"][office][contest_key] = {
            "contest_name": get_full_office_name(office),
            "results": {},
        }

        for county, county_data in counties.items():
            formatted = format_result_entry(county, office, county_data)
            if formatted:
                data["results_by_year"]["2022"][office][contest_key]["results"][county] = formatted
                new_entries += 1
                counties_updated.add(county)

    print(f"[INFO] Saving merged data to {json_file}...")
    with open(json_file, "w") as f:
        json.dump(data, f, indent=2)

    counties_2022 = set()
    for office in data["results_by_year"].get("2022", {}).values():
        for contest in office.values():
            counties_2022.update(contest.get("results", {}).keys())

    print("\n[SUCCESS] Merge complete!")
    print(f"  - Entries created: {new_entries}")
    print(f"  - Unique counties with 2022 data: {len(counties_2022)}/67")
    print(f"  - Contests included: {list(data['results_by_year']['2022'].keys())}")


if __name__ == "__main__":
    merge_data()
