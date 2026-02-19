#!/usr/bin/env python3
"""
Process OpenElections Pennsylvania data to create election results JSON.
Aggregates county-level election results from 2000-2024.

AVAILABLE RACES:
- President (2000, 2004, 2008, 2012, 2016, 2020, 2024)
- U.S. Senate (2000, 2004, 2006, 2010, 2012, 2016, 2018, 2022, 2024)
- Governor (2002, 2006, 2010, 2014, 2018, 2022)
- Attorney General (2000, 2004, 2008, 2012, 2016, 2020, 2024)
- Auditor General (2000, 2004, 2008, 2012, 2016, 2020, 2024)
- State Treasurer (2000, 2004, 2008, 2012, 2016, 2020, 2024)
- State House (2000-2024, varies by year)
- State Senate (2000-2024, varies by year)
- U.S. House (2000-2024, varies by year)

NOTE: Pennsylvania judicial elections ARE partisan but are NOT included in OpenElections data.

Requires: pandas
Install: pip install pandas

Usage:
    python process_openelections.py
"""

import pandas as pd
import json
import os
from pathlib import Path
from collections import defaultdict
import re

def aggreg_precinct_to_county(filepath):
    """Aggregate precinct-level election data to county level."""
    df = pd.read_csv(filepath)
    
    # Normalize office names to title case
    df['office'] = df['office'].str.title()
    
    # Convert votes to numeric, handling any string values
    df['votes'] = pd.to_numeric(df['votes'], errors='coerce')
    df = df.dropna(subset=['votes'])
    df['votes'] = df['votes'].astype(int)
    
    # Group by county, office, district, party, candidate and sum votes
    group_cols = ['county']
    # Only include these columns if they exist
    for col in ['office', 'district', 'party', 'candidate']:
        if col in df.columns:
            group_cols.append(col)
    
    # Aggregate votes
    agg_data = df.groupby(group_cols, as_index=False)['votes'].sum()
    
    return agg_data

def get_competitiveness(margin_pct):
    """Determine competitiveness category based on margin percentage."""
    abs_margin = abs(margin_pct)
    
    # Tossup
    if abs_margin < 0.50:
        return {
            "category": "Tossup",
            "party": "Competitive",
            "code": "TOSSUP",
            "color": "#f7f7f7"
        }
    
    # Democratic categories
    elif margin_pct > 0:
        if abs_margin < 1.00:
            return {
                "category": "Tilt Democratic",
                "party": "Democratic",
                "code": "D_TILT",
                "color": "#e1f5fe"
            }
        elif abs_margin < 5.50:
            return {
                "category": "Lean Democratic",
                "party": "Democratic",
                "code": "D_LEAN",
                "color": "#c6dbef"
            }
        elif abs_margin < 10.00:
            return {
                "category": "Likely Democratic",
                "party": "Democratic",
                "code": "D_LIKELY",
                "color": "#9ecae1"
            }
        elif abs_margin < 20.00:
            return {
                "category": "Safe Democratic",
                "party": "Democratic",
                "code": "D_SAFE",
                "color": "#6baed6"
            }
        elif abs_margin < 30.00:
            return {
                "category": "Stronghold Democratic",
                "party": "Democratic",
                "code": "D_STRONGHOLD",
                "color": "#3182bd"
            }
        elif abs_margin < 40.00:
            return {
                "category": "Dominant Democratic",
                "party": "Democratic",
                "code": "D_DOMINANT",
                "color": "#08519c"
            }
        else:
            return {
                "category": "Annihilation Democratic",
                "party": "Democratic",
                "code": "D_ANNIHILATION",
                "color": "#08306b"
            }
    
    # Republican categories
    else:
        if abs_margin < 1.00:
            return {
                "category": "Tilt Republican",
                "party": "Republican",
                "code": "R_TILT",
                "color": "#fee8c8"
            }
        elif abs_margin < 5.50:
            return {
                "category": "Lean Republican",
                "party": "Republican",
                "code": "R_LEAN",
                "color": "#fcae91"
            }
        elif abs_margin < 10.00:
            return {
                "category": "Likely Republican",
                "party": "Republican",
                "code": "R_LIKELY",
                "color": "#fb6a4a"
            }
        elif abs_margin < 20.00:
            return {
                "category": "Safe Republican",
                "party": "Republican",
                "code": "R_SAFE",
                "color": "#ef3b2c"
            }
        elif abs_margin < 30.00:
            return {
                "category": "Stronghold Republican",
                "party": "Republican",
                "code": "R_STRONGHOLD",
                "color": "#cb181d"
            }
        elif abs_margin < 40.00:
            return {
                "category": "Dominant Republican",
                "party": "Republican",
                "code": "R_DOMINANT",
                "color": "#a50f15"
            }
        else:
            return {
                "category": "Annihilation Republican",
                "party": "Republican",
                "code": "R_ANNIHILATION",
                "color": "#67000d"
            }

def normalize_candidate_name(candidate, office_name):
    """Normalize candidate names to regular case and strip running mates for president."""
    if not candidate or pd.isna(candidate):
        return ""
    name = str(candidate).strip()
    if not name:
        return ""

    if office_name in ("President", "Governor"):
        match = re.split(r"\s*(?:/|and|&)\s*", name, flags=re.IGNORECASE, maxsplit=1)
        if match:
            name = match[0]

    name = " ".join(name.split())
    name = name.title()

    # Add period to any standalone middle initial (e.g., "Donald J Trump" -> "Donald J. Trump")
    name = re.sub(r"\b([A-Z])\b(?!\.)", r"\1.", name)

    # Fix common surname casing (e.g., McCormick, DePasquale)
    name = re.sub(r"\bMc([a-z])", lambda m: "Mc" + m.group(1).upper(), name)
    name = re.sub(r"\bDe([a-z])", lambda m: "De" + m.group(1).upper(), name)

    suffix_map = {
        "Jr": "Jr.",
        "Sr": "Sr.",
        "Ii": "II",
        "Iii": "III",
        "Iv": "IV",
        "V": "V",
    }
    parts = name.split()
    if parts and parts[-1] in suffix_map:
        parts[-1] = suffix_map[parts[-1]]
        name = " ".join(parts)

    return name

def normalize_county_name(county):
    """Normalize county names to title case with Mc* correction."""
    if not county:
        return ""
    name = str(county).replace(" County", "").strip()
    if not name:
        return ""
    name = " ".join(name.split())
    name = name.title()
    name = re.sub(r"\bMc([a-z])", lambda m: "Mc" + m.group(1).upper(), name)
    return name

def normalize_party_code(party):
    """Normalize party codes to common abbreviations."""
    if not party or pd.isna(party):
        return ""
    p = str(party).strip()
    if not p:
        return ""
    mapping = {
        "Dem": "DEM",
        "Democratic": "DEM",
        "Rep": "REP",
        "Republican": "REP",
        "Grn": "GRN",
        "Green": "GRN",
        "Green Party": "GRN",
        "Lib": "LIB",
        "Libertarian": "LIB",
        "Const": "CNST",
        "Constitution": "CNST",
        "Constitution Party": "CNST",
        "Ref": "REF",
        "Reform": "REF",
        "Forward": "FWD",
        "Forward Party": "FWD",
        "Keystone": "KEY",
    }
    return mapping.get(p, p.upper())

def get_president_name(year, party_code):
    """Return full presidential nominee name for a given year and party."""
    president_map = {
        2000: {"DEM": "Al Gore", "REP": "George W. Bush"},
        2004: {"DEM": "John F. Kerry", "REP": "George W. Bush"},
        2008: {"DEM": "Barack Obama", "REP": "John McCain"},
        2012: {"DEM": "Barack Obama", "REP": "Mitt Romney"},
        2016: {"DEM": "Hillary Clinton", "REP": "Donald J. Trump"},
        2020: {"DEM": "Joe Biden", "REP": "Donald J. Trump"},
        2024: {"DEM": "Kamala Harris", "REP": "Donald J. Trump"},
    }
    return president_map.get(year, {}).get(party_code, "")

def aggregate_precinct_to_county(df):
    """Aggregate precinct-level data to county level."""
    # Normalize office names to title case for consistency
    df = df.copy()
    df['office'] = df['office'].str.title()

    # Preserve rows with missing party/candidate by filling blanks before grouping
    if 'party' in df.columns:
        df['party'] = df['party'].fillna('')
    if 'candidate' in df.columns:
        df['candidate'] = df['candidate'].fillna('')
    
    # Ensure votes is numeric before aggregating
    df['votes'] = pd.to_numeric(df['votes'], errors='coerce').fillna(0).astype(int)
    
    # Group by county, office, party and sum votes
    aggregated = df.groupby(['county', 'office', 'party', 'candidate']).agg({
        'votes': 'sum'
    }).reset_index()
    
    return aggregated

def build_county_name_map(election_data):
    """Build a map of uppercased county name -> canonical county name."""
    county_map = {}
    for year_races in election_data.values():
        for county_results in year_races.values():
            for county in county_results.keys():
                county_map[county.upper()] = county
            if county_map:
                return county_map
    return county_map

def load_official_row_offices(official_base_path, county_name_map):
    """Load Auditor General and State Treasurer from official county-level CSVs."""
    official_files = {
        2000: "Official_2182026094443PM.CSV",
        2004: "Official_2182026094602PM.CSV",
        2008: "Official_2182026094634PM.CSV",
        2012: "Official_2182026094715PM.CSV",
    }

    party_code_map = {
        "Democratic": "DEM",
        "Republican": "REP",
        "Green": "GRN",
        "Libertarian": "LIB",
        "Constitution": "CNST",
        "Reform": "REF",
    }

    candidate_names = {
        2000: {
            "Auditor General": {
                "Democratic": "Bob Casey Jr.",
                "Republican": "Katie True",
                "Green": "Anne E. Goeke",
                "Libertarian": "Jessica A. Morris",
                "Constitution": "John H. Rhine",
                "Reform": "James R. Blair",
            },
            "State Treasurer": {
                "Democratic": "Catherine Baker Knoll",
                "Republican": "Barbara Hafer",
                "Green": "Barbara S. Knox",
                "Libertarian": "John D. Famularo",
                "Constitution": "John P. McDermott",
                "Reform": "Joseph F. Patterson",
            },
        },
        2004: {
            "Auditor General": {
                "Democratic": "Jack Wagner",
                "Republican": "Joe Peters",
                "Green": "Ben Price",
                "Libertarian": "Berlie Etzel",
                "Constitution": "Leonard Ritchie",
            },
            "State Treasurer": {
                "Democratic": "Bob Casey Jr.",
                "Republican": "Jean Craige Pepper",
                "Libertarian": "Darryl Perry",
                "Green": "Paul Teese",
                "Constitution": "Max Lampenfield",
            },
        },
        2008: {
            "Auditor General": {
                "Democratic": "Jack Wagner",
                "Republican": "Chet Beiler",
                "Libertarian": "Betsy Summers",
            },
            "State Treasurer": {
                "Democratic": "Rob McCord",
                "Republican": "Tom Ellis",
                "Libertarian": "Berlie Etzel",
            },
        },
        2012: {
            "Auditor General": {
                "Democratic": "Eugene DePasquale",
                "Republican": "John Maher",
                "Libertarian": "Betsy Summers",
            },
            "State Treasurer": {
                "Democratic": "Rob McCord",
                "Republican": "Diana Irey Vaughan",
                "Libertarian": "Patricia M. Fryman",
            },
        },
    }

    results = {}

    for year, filename in official_files.items():
        full_path = os.path.join(official_base_path, filename)
        if not os.path.exists(full_path):
            print(f"[!] Warning: Official data not found at {filename}")
            continue

        df = pd.read_csv(full_path, dtype=str)
        df = df[df["Office Name"].isin(["Auditor General", "State Treasurer"])]
        if df.empty:
            continue

        year_results = {}
        for office_name in ["Auditor General", "State Treasurer"]:
            office_df = df[df["Office Name"] == office_name]
            if office_df.empty:
                continue

            county_results = defaultdict(lambda: {
                "DEM": 0, "REP": 0, "other": 0, "total": 0,
                "dem_candidate": "", "rep_candidate": "",
                "all_parties": {}
            })

            for _, row in office_df.iterrows():
                county_raw = str(row.get("County Name", "")).strip()
                if not county_raw:
                    continue

                county = county_name_map.get(county_raw.upper(), normalize_county_name(county_raw))
                party_name = str(row.get("Party Name", "")).strip()
                votes_raw = str(row.get("Votes", "")).replace(",", "").strip()
                if not votes_raw:
                    continue
                try:
                    votes = int(votes_raw)
                except ValueError:
                    continue

                party_code = party_code_map.get(party_name, party_name.upper())
                candidate = candidate_names.get(year, {}).get(office_name, {}).get(party_name, "")
                if not candidate:
                    candidate = str(row.get("Candidate Name", "")).strip()

                county_results[county]["all_parties"][party_code] = votes

                if party_code == "DEM":
                    county_results[county]["DEM"] += votes
                    if candidate:
                        county_results[county]["dem_candidate"] = normalize_candidate_name(candidate, office_name)
                elif party_code == "REP":
                    county_results[county]["REP"] += votes
                    if candidate:
                        county_results[county]["rep_candidate"] = normalize_candidate_name(candidate, office_name)
                else:
                    county_results[county]["other"] += votes

                county_results[county]["total"] += votes

            for county, data in county_results.items():
                dem = data["DEM"]
                rep = data["REP"]
                total = data["total"]
                other = data["other"]
                two_party_total = dem + rep

                if two_party_total > 0:
                    dem_pct = (dem / total) * 100
                    rep_pct = (rep / total) * 100
                    margin = dem - rep
                    margin_pct = (margin / two_party_total) * 100

                    data["dem_pct"] = round(dem_pct, 2)
                    data["rep_pct"] = round(rep_pct, 2)
                    data["other_votes"] = other
                    data["two_party_total"] = two_party_total
                    data["margin"] = margin
                    data["margin_pct"] = round(margin_pct, 2)
                    data["winner"] = "DEM" if margin > 0 else "REP"
                    data["competitiveness"] = get_competitiveness(margin_pct)

            year_results[office_name] = dict(county_results)

        if year_results:
            results[year] = year_results

    return results

def load_official_us_senate(official_base_path, county_name_map):
    """Load U.S. Senate results from official county-level CSVs."""
    official_files = {
        2018: "Official_2112026093800PM.CSV",
        2022: "Official_2112026100831PM.CSV",
        2024: "Official_2182026102327PM.CSV",
    }

    party_code_map = {
        "Democratic": "DEM",
        "Republican": "REP",
        "Green": "GRN",
        "Green Party": "GRN",
        "Libertarian": "LIB",
        "Constitution": "CNST",
        "Constitution Party": "CNST",
        "Reform": "REF",
    }

    results = {}
    for year, filename in official_files.items():
        full_path = os.path.join(official_base_path, filename)
        if not os.path.exists(full_path):
            print(f"[!] Warning: Official data not found at {filename}")
            continue

        df = pd.read_csv(full_path, dtype=str)
        df = df[df["Office Name"] == "United States Senator"]
        if df.empty:
            print(f"[!] Warning: No U.S. Senate data found in {filename}")
            continue

        county_results = defaultdict(lambda: {
            "DEM": 0, "REP": 0, "other": 0, "total": 0,
            "dem_candidate": "", "rep_candidate": "",
            "all_parties": {}
        })

        for _, row in df.iterrows():
            county_raw = str(row.get("County Name", "")).strip()
            if not county_raw:
                continue
            county = county_name_map.get(county_raw.upper(), normalize_county_name(county_raw))

            party_name = str(row.get("Party Name", "")).strip()
            votes_raw = str(row.get("Votes", "")).replace(",", "").strip()
            if not votes_raw:
                continue
            try:
                votes = int(votes_raw)
            except ValueError:
                continue

            candidate = str(row.get("Candidate Name", "")).strip()
            party_code = party_code_map.get(party_name, party_name.upper())

            county_results[county]["all_parties"][party_code] = votes

            if party_code == "DEM":
                county_results[county]["DEM"] += votes
                if candidate:
                    county_results[county]["dem_candidate"] = normalize_candidate_name(candidate, "U.S. Senate")
            elif party_code == "REP":
                county_results[county]["REP"] += votes
                if candidate:
                    county_results[county]["rep_candidate"] = normalize_candidate_name(candidate, "U.S. Senate")
            else:
                county_results[county]["other"] += votes

            county_results[county]["total"] += votes

        for county, data in county_results.items():
            dem = data["DEM"]
            rep = data["REP"]
            total = data["total"]
            other = data["other"]
            two_party_total = dem + rep

            if two_party_total > 0:
                dem_pct = (dem / total) * 100
                rep_pct = (rep / total) * 100
                margin = dem - rep
                margin_pct = (margin / two_party_total) * 100

                data["dem_pct"] = round(dem_pct, 2)
                data["rep_pct"] = round(rep_pct, 2)
                data["other_votes"] = other
                data["two_party_total"] = two_party_total
                data["margin"] = margin
                data["margin_pct"] = round(margin_pct, 2)
                data["winner"] = "DEM" if margin > 0 else "REP"
                data["competitiveness"] = get_competitiveness(margin_pct)

        results[year] = {"U.S. Senate": dict(county_results)}

    return results

def load_official_governor(official_base_path, county_name_map):
    """Load Governor results from official county-level CSVs."""
    official_files = {
        2018: "Official_2112026093800PM.CSV",
        2022: "Official_2112026100831PM.CSV",
    }

    party_code_map = {
        "Democratic": "DEM",
        "Republican": "REP",
        "Green": "GRN",
        "Green Party": "GRN",
        "Libertarian": "LIB",
        "Constitution": "CNST",
        "Constitution Party": "CNST",
        "Reform": "REF",
        "Keystone": "KEY",
    }

    results = {}
    for year, filename in official_files.items():
        full_path = os.path.join(official_base_path, filename)
        if not os.path.exists(full_path):
            print(f"[!] Warning: Official data not found at {filename}")
            continue

        df = pd.read_csv(full_path, dtype=str)
        df = df[df["Office Name"] == "Governor"]
        if df.empty:
            print(f"[!] Warning: No Governor data found in {filename}")
            continue

        county_results = defaultdict(lambda: {
            "DEM": 0, "REP": 0, "other": 0, "total": 0,
            "dem_candidate": "", "rep_candidate": "",
            "all_parties": {}
        })

        for _, row in df.iterrows():
            county_raw = str(row.get("County Name", "")).strip()
            if not county_raw:
                continue
            county = county_name_map.get(county_raw.upper(), normalize_county_name(county_raw))

            party_name = str(row.get("Party Name", "")).strip()
            votes_raw = str(row.get("Votes", "")).replace(",", "").strip()
            if not votes_raw:
                continue
            try:
                votes = int(votes_raw)
            except ValueError:
                continue

            candidate = str(row.get("Candidate Name", "")).strip()
            party_code = party_code_map.get(party_name, party_name.upper())

            county_results[county]["all_parties"][party_code] = votes

            if party_code == "DEM":
                county_results[county]["DEM"] += votes
                if candidate:
                    county_results[county]["dem_candidate"] = normalize_candidate_name(candidate, "Governor")
            elif party_code == "REP":
                county_results[county]["REP"] += votes
                if candidate:
                    county_results[county]["rep_candidate"] = normalize_candidate_name(candidate, "Governor")
            else:
                county_results[county]["other"] += votes

            county_results[county]["total"] += votes

        for county, data in county_results.items():
            dem = data["DEM"]
            rep = data["REP"]
            total = data["total"]
            other = data["other"]
            two_party_total = dem + rep

            if two_party_total > 0:
                dem_pct = (dem / total) * 100
                rep_pct = (rep / total) * 100
                margin = dem - rep
                margin_pct = (margin / two_party_total) * 100

                data["dem_pct"] = round(dem_pct, 2)
                data["rep_pct"] = round(rep_pct, 2)
                data["other_votes"] = other
                data["two_party_total"] = two_party_total
                data["margin"] = margin
                data["margin_pct"] = round(margin_pct, 2)
                data["winner"] = "DEM" if margin > 0 else "REP"
                data["competitiveness"] = get_competitiveness(margin_pct)

        results[year] = {"Governor": dict(county_results)}

    return results

def load_official_statewide_2024(official_base_path, county_name_map):
    """Load 2024 statewide offices from official county-level CSV."""
    filename = "Official_2182026102327PM.CSV"
    full_path = os.path.join(official_base_path, filename)
    if not os.path.exists(full_path):
        print(f"[!] Warning: Official data not found at {filename}")
        return {}

    office_map = {
        "President of the United States": "President",
        "United States Senator": "U.S. Senate",
        "Attorney General": "Attorney General",
        "Auditor General": "Auditor General",
        "State Treasurer": "State Treasurer",
    }

    df = pd.read_csv(full_path, dtype=str)
    df = df[df["Office Name"].isin(office_map.keys())]
    if df.empty:
        print(f"[!] Warning: No 2024 statewide data found in {filename}")
        return {}

    results = {}
    year = 2024

    for office_name, mapped_office in office_map.items():
        office_df = df[df["Office Name"] == office_name]
        if office_df.empty:
            continue

        county_results = defaultdict(lambda: {
            "DEM": 0, "REP": 0, "other": 0, "total": 0,
            "dem_candidate": "", "rep_candidate": "",
            "all_parties": {}
        })

        for _, row in office_df.iterrows():
            county_raw = str(row.get("County Name", "")).strip()
            if not county_raw:
                continue
            county = county_name_map.get(county_raw.upper(), normalize_county_name(county_raw))

            party_code = normalize_party_code(row.get("Party Name", ""))
            votes_raw = str(row.get("Votes", "")).replace(",", "").strip()
            if not votes_raw:
                continue
            try:
                votes = int(votes_raw)
            except ValueError:
                continue

            candidate = str(row.get("Candidate Name", "")).strip()
            normalized_candidate = normalize_candidate_name(candidate, mapped_office)

            county_results[county]["all_parties"][party_code] = votes

            if party_code == "DEM":
                county_results[county]["DEM"] += votes
                if mapped_office == "President":
                    mapped_name = get_president_name(year, "DEM")
                    county_results[county]["dem_candidate"] = mapped_name or normalized_candidate
                else:
                    county_results[county]["dem_candidate"] = normalized_candidate
            elif party_code == "REP":
                county_results[county]["REP"] += votes
                if mapped_office == "President":
                    mapped_name = get_president_name(year, "REP")
                    county_results[county]["rep_candidate"] = mapped_name or normalized_candidate
                else:
                    county_results[county]["rep_candidate"] = normalized_candidate
            else:
                county_results[county]["other"] += votes

            county_results[county]["total"] += votes

        for county, data in county_results.items():
            dem = data["DEM"]
            rep = data["REP"]
            total = data["total"]
            other = data["other"]
            two_party_total = dem + rep

            if two_party_total > 0:
                dem_pct = (dem / total) * 100
                rep_pct = (rep / total) * 100
                margin = dem - rep
                margin_pct = (margin / two_party_total) * 100

                data["dem_pct"] = round(dem_pct, 2)
                data["rep_pct"] = round(rep_pct, 2)
                data["other_votes"] = other
                data["two_party_total"] = two_party_total
                data["margin"] = margin
                data["margin_pct"] = round(margin_pct, 2)
                data["winner"] = "DEM" if margin > 0 else "REP"
                data["competitiveness"] = get_competitiveness(margin_pct)

        results.setdefault(year, {})[mapped_office] = dict(county_results)

    return results

def load_official_statewide_2020(official_base_path, county_name_map):
    """Load 2020 statewide offices from official county-level CSV."""
    filename = "Official_2112026093510PM.CSV"
    full_path = os.path.join(official_base_path, filename)
    if not os.path.exists(full_path):
        print(f"[!] Warning: Official data not found at {filename}")
        return {}

    office_map = {
        "President of the United States": "President",
        "Attorney General": "Attorney General",
        "Auditor General": "Auditor General",
        "State Treasurer": "State Treasurer",
    }

    df = pd.read_csv(full_path, dtype=str)
    df = df[df["Office Name"].isin(office_map.keys())]
    if df.empty:
        print(f"[!] Warning: No 2020 statewide data found in {filename}")
        return {}

    results = {}
    year = 2020

    for office_name, mapped_office in office_map.items():
        office_df = df[df["Office Name"] == office_name]
        if office_df.empty:
            continue

        county_results = defaultdict(lambda: {
            "DEM": 0, "REP": 0, "other": 0, "total": 0,
            "dem_candidate": "", "rep_candidate": "",
            "all_parties": {}
        })

        for _, row in office_df.iterrows():
            county_raw = str(row.get("County Name", "")).strip()
            if not county_raw:
                continue
            county = county_name_map.get(county_raw.upper(), normalize_county_name(county_raw))

            party_code = normalize_party_code(row.get("Party Name", ""))
            votes_raw = str(row.get("Votes", "")).replace(",", "").strip()
            if not votes_raw:
                continue
            try:
                votes = int(votes_raw)
            except ValueError:
                continue

            candidate = str(row.get("Candidate Name", "")).strip()
            normalized_candidate = normalize_candidate_name(candidate, mapped_office)

            county_results[county]["all_parties"][party_code] = votes

            if party_code == "DEM":
                county_results[county]["DEM"] += votes
                if mapped_office == "President":
                    mapped_name = get_president_name(year, "DEM")
                    county_results[county]["dem_candidate"] = mapped_name or normalized_candidate
                else:
                    county_results[county]["dem_candidate"] = normalized_candidate
            elif party_code == "REP":
                county_results[county]["REP"] += votes
                if mapped_office == "President":
                    mapped_name = get_president_name(year, "REP")
                    county_results[county]["rep_candidate"] = mapped_name or normalized_candidate
                else:
                    county_results[county]["rep_candidate"] = normalized_candidate
            else:
                county_results[county]["other"] += votes

            county_results[county]["total"] += votes

        for county, data in county_results.items():
            dem = data["DEM"]
            rep = data["REP"]
            total = data["total"]
            other = data["other"]
            two_party_total = dem + rep

            if two_party_total > 0:
                dem_pct = (dem / total) * 100
                rep_pct = (rep / total) * 100
                margin = dem - rep
                margin_pct = (margin / two_party_total) * 100

                data["dem_pct"] = round(dem_pct, 2)
                data["rep_pct"] = round(rep_pct, 2)
                data["other_votes"] = other
                data["two_party_total"] = two_party_total
                data["margin"] = margin
                data["margin_pct"] = round(margin_pct, 2)
                data["winner"] = "DEM" if margin > 0 else "REP"
                data["competitiveness"] = get_competitiveness(margin_pct)

        results.setdefault(year, {})[mapped_office] = dict(county_results)

    return results

def load_election_data(base_path):
    """Load all election data from OpenElections PA data."""
    
    # Define election years, file patterns, and statewide races
    # Pennsylvania statewide offices:
    # - President (every 4 years: 2000, 2004, 2008, 2012, 2016, 2020)
    # - U.S. Senate (varies by cycle, generally: 2000, 2004, 2006, 2010, 2012, 2016, 2018)
    # - Governor (every 4 years in midterms: 2002, 2006, 2010, 2014, 2018)
    # - Attorney General (varies: 2000, 2004, 2008, 2012, 2016, 2020)
    # - Auditor General and State Treasurer (2000-2012 from official county returns; 2016+ from OpenElections)
    
    elections = {
        2000: {"file": "2000/20001107__pa__general__county.csv", "races": ["President", "U.S. Senate", "Attorney General", "Auditor General", "State Treasurer"]},
        2002: {"file": "2002/20021105__pa__general__county.csv", "races": ["Governor"]},
        2004: {"file": "2004/20041102__pa__general__county.csv", "races": ["President", "U.S. Senate", "Attorney General", "Auditor General", "State Treasurer"]},
        2006: {"file": "2006/20061107__pa__general__county.csv", "races": ["U.S. Senate", "Governor"]},
        2008: {"file": "2008/20081104__pa__general__county.csv", "races": ["President", "Attorney General", "Auditor General", "State Treasurer"]},
        2010: {"file": "2010/20101102__pa__general__county.csv", "races": ["U.S. Senate", "Governor"]},
        2012: {"file": "2012/20121102__pa__general__county.csv", "races": ["President", "U.S. Senate", "Attorney General", "Auditor General", "State Treasurer"]},
        2014: {"file": "2014/20141104__pa__general__county.csv", "races": ["Governor"]},
        2016: {"file": "2016/20161108__pa__general__precinct.csv", "races": ["President", "U.S. Senate", "Attorney General", "Auditor General", "State Treasurer"], "aggregate": True},
        2018: {"file": "2018/20181106__pa__general__precinct.csv", "races": ["U.S. Senate", "Governor"], "aggregate": True},
        2020: {"file": "2020/20201103__pa__general__precinct.csv", "races": ["President", "Attorney General", "Auditor General", "State Treasurer"], "aggregate": True},
        2024: {"file": "2024/20241105__pa__general__precinct.csv", "races": ["President", "U.S. Senate", "Attorney General", "Auditor General", "State Treasurer"], "aggregate": True},
    }
    
    all_data = {}
    
    for year, config in elections.items():
        filepath = config["file"]
        races = config["races"]
        should_aggregate = config.get("aggregate", False)
        full_path = os.path.join(base_path, filepath)
        
        if not os.path.exists(full_path):
            print(f"[!] Warning: {year} data not found at {filepath}")
            continue
        
        print(f"Loading {year} data...")
        
        try:
            df = pd.read_csv(full_path)
            
            # If this is precinct-level data, aggregate to county
            if should_aggregate:
                df = aggregate_precinct_to_county(df)
            
            year_results = {}
            
            # Process each race type for this year
            for race_type in races:
                office_df = df[df['office'] == race_type].copy()
                
                if len(office_df) == 0:
                    print(f"  [!] No {race_type} data found for {year}")
                    continue

                # Build candidate -> party map for rows missing party labels
                candidate_party_map = {}
                for _, row in office_df.iterrows():
                    party = normalize_party_code(row.get('party', ''))
                    candidate = row.get('candidate', '')
                    if pd.notna(party) and party:
                        key = normalize_candidate_name(candidate, race_type).lower()
                        if key and key not in candidate_party_map:
                            candidate_party_map[key] = party
                
                # Group by county and party to get total votes and candidates
                county_results = defaultdict(lambda: {
                    'DEM': 0, 'REP': 0, 'other': 0, 'total': 0,
                    'dem_candidate': '', 'rep_candidate': '',
                    'all_parties': {}
                })
                
                for _, row in office_df.iterrows():
                    county = row['county']
                    party = normalize_party_code(row['party'])
                    votes = row['votes']
                    candidate = row.get('candidate', '')
                    if (pd.isna(party) or not party) and candidate:
                        key = normalize_candidate_name(candidate, race_type).lower()
                        party = candidate_party_map.get(key, party)
                    
                    if pd.isna(votes) or pd.isna(county):
                        continue
                    
                    # Ensure votes is converted to int, handling both int and str types
                    try:
                        votes = int(float(votes))
                    except (ValueError, TypeError):
                        continue
                    
                    # Store all party votes
                    if pd.notna(party) and party:
                        county_results[county]['all_parties'][party] = votes
                    
                    # Aggregate major party votes and track candidates
                    if party == 'DEM':
                        county_results[county]['DEM'] += votes
                        if pd.notna(candidate) and candidate:
                            if race_type == "President":
                                mapped_name = get_president_name(year, "DEM")
                                county_results[county]['dem_candidate'] = mapped_name or normalize_candidate_name(candidate, race_type)
                            else:
                                county_results[county]['dem_candidate'] = normalize_candidate_name(candidate, race_type)
                    elif party == 'REP':
                        county_results[county]['REP'] += votes
                        if pd.notna(candidate) and candidate:
                            if race_type == "President":
                                mapped_name = get_president_name(year, "REP")
                                county_results[county]['rep_candidate'] = mapped_name or normalize_candidate_name(candidate, race_type)
                            else:
                                county_results[county]['rep_candidate'] = normalize_candidate_name(candidate, race_type)
                    else:
                        county_results[county]['other'] += votes
                    
                    county_results[county]['total'] += votes
                
                # Calculate margins and competitiveness
                for county, data in county_results.items():
                    dem = data['DEM']
                    rep = data['REP']
                    total = data['total']
                    other = data['other']
                    two_party_total = dem + rep
                    
                    if two_party_total > 0:
                        dem_pct = (dem / total) * 100
                        rep_pct = (rep / total) * 100
                        margin = dem - rep
                        margin_pct = (margin / two_party_total) * 100
                        
                        data['dem_pct'] = round(dem_pct, 2)
                        data['rep_pct'] = round(rep_pct, 2)
                        data['other_votes'] = other
                        data['two_party_total'] = two_party_total
                        data['margin'] = margin
                        data['margin_pct'] = round(margin_pct,  2)
                        data['winner'] = 'DEM' if margin > 0 else 'REP'
                        data['competitiveness'] = get_competitiveness(margin_pct)
                
                year_results[race_type] = dict(county_results)
                print(f"  [OK] {race_type}: {len(county_results)} counties")
            
            all_data[year] = year_results
            
        except Exception as e:
            print(f"  [ERROR] Error loading {year}: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    return all_data

def create_output_json(election_data, output_path):
    """Create the final JSON structure for the map."""
    
    # Map office types to contest categories and names
    office_mapping = {
        "President": {
            "category": "president",
            "name": "President of the United States"
        },
        "Governor": {
            "category": "governor",
            "name": "Governor of Pennsylvania"
        },
        "U.S. Senate": {
            "category": "us_senate",
            "name": "United States Senator"
        },
        "Attorney General": {
            "category": "attorney_general",
            "name": "Attorney General of Pennsylvania"
        },
        "Auditor General": {
            "category": "auditor_general",
            "name": "Auditor General of Pennsylvania"
        },
        "State Treasurer": {
            "category": "state_treasurer",
            "name": "State Treasurer of Pennsylvania"
        }
    }
    
    # Restructure data by year, then by contest, then by county
    results_by_year = {}
    all_contests = set()
    
    for year in sorted(election_data.keys()):
        year_races = election_data[year]
        year_str = str(year)
        
        # Initialize year structure
        if year_str not in results_by_year:
            results_by_year[year_str] = {}
        
        # Process each race type for this year
        for race_type, county_results in year_races.items():
            # Get contest info from mapping
            contest_info = office_mapping.get(race_type, {
                "category": race_type.lower().replace(" ", "_").replace(".", ""),
                "name": race_type
            })
            
            contest_category = contest_info["category"]
            contest_name = contest_info["name"]
            all_contests.add(contest_category)
            
            # Initialize contest category
            if contest_category not in results_by_year[year_str]:
                results_by_year[year_str][contest_category] = {}
            
            # Create contest key
            contest_key = f"{contest_category}_{year}"
            results_by_year[year_str][contest_category][contest_key] = {
                "contest_name": contest_name,
                "results": {}
            }
            
            for county, data in county_results.items():
                # Normalize county name (remove " County" suffix if present)
                county_clean = normalize_county_name(county)
                
                results_by_year[year_str][contest_category][contest_key]["results"][county_clean] = {
                    "county": county_clean,
                    "contest": contest_name,
                    "year": year_str,
                    "dem_candidate": data.get('dem_candidate', ''),
                    "rep_candidate": data.get('rep_candidate', ''),
                    "dem_votes": data['DEM'],
                    "rep_votes": data['REP'],
                    "other_votes": data.get('other_votes', 0),
                    "total_votes": data['total'],
                    "two_party_total": data.get('two_party_total', data['DEM'] + data['REP']),
                    "margin": data.get('margin', 0),
                    "margin_pct": data.get('margin_pct', 0),
                    "winner": data.get('winner', 'TIE'),
                    "competitiveness": data.get('competitiveness', {}),
                    "all_parties": data.get('all_parties', {})
                }
    
    # Count total counties (get from first available race in first year)
    counties_count = 0
    if election_data:
        first_year = list(election_data.values())[0]
        if first_year:
            first_race = list(first_year.values())[0]
            counties_count = len(first_race)
    
    # Convert to regular dict for JSON serialization
    output = {
        "metadata": {
            "title": "Pennsylvania Election Results",
            "years": sorted(election_data.keys()),
            "contests": sorted(list(all_contests)),
            "counties_count": counties_count
        },
        "results_by_year": results_by_year
    }
    
    # Write to JSON
    print(f"\nWriting output to: {output_path}")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2)
    
    print(f"[OK] Created election results JSON")
    print(f"[OK] {counties_count} counties")
    print(f"[OK] {len(election_data)} election years")
    print(f"[OK] Contests: {', '.join(sorted(all_contests))}")
    
    # Print sample for first few years
    if election_data:
        print(f"\nSample results:")
        for year in sorted(election_data.keys())[:5]:
            year_str = str(year)
            if year_str in results_by_year:
                races_in_year = []
                for contest in results_by_year[year_str]:
                    races_in_year.append(contest)
                print(f"  {year}: {', '.join(races_in_year)}")

def main():
    # Paths
    base_path = "../data/openelections-data-pa"
    output_path = "../data/pa_election_results.json"
    
    print("=" * 60)
    print("OpenElections Pennsylvania Data Processor")
    print("Statewide Elections: 2000-2024")
    print("=" * 60)
    print()
    
    # Load data
    election_data = load_election_data(base_path)

    if not election_data:
        print("\n[ERROR] No election data loaded!")
        return

    # Merge Auditor General and State Treasurer from official county returns (2000-2012)
    county_name_map = build_county_name_map(election_data)
    official_data = load_official_row_offices("../data", county_name_map)
    for year, year_races in official_data.items():
        if year not in election_data:
            election_data[year] = {}
        for race_type in sorted(year_races.keys()):
            county_results = year_races[race_type]
            election_data[year][race_type] = county_results

    # Merge U.S. Senate from official county returns (2018, 2022, 2024)
    official_senate = load_official_us_senate("../data", county_name_map)
    for year, year_races in official_senate.items():
        if year not in election_data:
            election_data[year] = {}
        for race_type, county_results in year_races.items():
            election_data[year][race_type] = county_results

    # Merge Governor from official county returns (2022)
    official_governor = load_official_governor("../data", county_name_map)
    for year, year_races in official_governor.items():
        if year not in election_data:
            election_data[year] = {}
        for race_type, county_results in year_races.items():
            election_data[year][race_type] = county_results

    # Merge 2024 statewide offices from official county returns
    official_2024 = load_official_statewide_2024("../data", county_name_map)
    for year, year_races in official_2024.items():
        if year not in election_data:
            election_data[year] = {}
        for race_type, county_results in year_races.items():
            election_data[year][race_type] = county_results

    # Merge 2020 statewide offices from official county returns
    official_2020 = load_official_statewide_2020("../data", county_name_map)
    for year, year_races in official_2020.items():
        if year not in election_data:
            election_data[year] = {}
        for race_type, county_results in year_races.items():
            election_data[year][race_type] = county_results
    
    # Create output JSON
    create_output_json(election_data, output_path)
    
    print("\n" + "=" * 60)
    print("[OK] Processing complete!")
    print("=" * 60)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
