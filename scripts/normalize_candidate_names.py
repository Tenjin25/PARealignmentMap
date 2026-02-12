"""
Normalize candidate names throughout the JSON file to proper title case.
Handles initials with periods and common name patterns.
"""

import json
from pathlib import Path


def normalize_name(name):
    """Normalize a candidate name to proper title case with periods on initials."""
    if not name or name.lower() in ['unknown', 'tie', 'vacant']:
        return name
    
    # Roman numerals to preserve as uppercase
    roman_numerals = {'i', 'ii', 'iii', 'iv', 'v', 'vi', 'vii', 'viii', 'ix', 'x'}
    # Suffixes to preserve
    suffixes = {'jr', 'sr', 'ph.d', 'phd', 'md', 'dds', 'esq'}
    
    # Split the name into parts
    parts = name.strip().split()
    normalized_parts = []
    
    for i, part in enumerate(parts):
        # Remove trailing/leading punctuation for checking, keep original with it
        clean_part = part.rstrip('.,')
        
        # If it's a single letter (likely an initial), add a period
        if len(clean_part) == 1 and clean_part.isalpha():
            normalized_parts.append(clean_part.upper() + '.')
        # Check for Roman numerals
        elif clean_part.lower() in roman_numerals:
            normalized_parts.append(clean_part.upper())
        # Check for suffixes
        elif clean_part.lower() in suffixes:
            suffix = clean_part.lower()
            if suffix in ['jr', 'sr', 'esq']:
                normalized_parts.append(suffix.title() + '.')
            elif suffix in ['ph.d', 'md', 'dds']:
                normalized_parts.append(suffix.upper())
            else:
                normalized_parts.append(suffix)
        else:
            # Title case the part (handles hyphenated names too)
            if '-' in clean_part:
                # Handle hyphenated names like "Mc-Something"
                normalized_parts.append('-'.join([p.capitalize() for p in clean_part.split('-')]))
            else:
                # Title case, handling special cases
                if clean_part.lower().startswith('mc') and len(clean_part) > 2:
                    # Mc format (McCormick, McClelland)
                    normalized_parts.append('Mc' + clean_part[2:].capitalize())
                elif clean_part.lower().startswith('o\'') and len(clean_part) > 2:
                    # O'Xxx format
                    normalized_parts.append('O\'' + clean_part[2:].capitalize())
                else:
                    normalized_parts.append(clean_part.capitalize())
    
    result = ' '.join(normalized_parts)
    # Clean up any double spaces or extra periods
    result = ' '.join(result.split())
    return result


def fix_middle_initials(name):
    """Fix spacing around middle initials like 'D HARRIS' -> 'D. Harris'"""
    parts = name.split()
    fixed_parts = []
    
    for i, part in enumerate(parts):
        # If this is a single letter followed by another part, it's likely an initial
        if len(part) == 1 and part.isalpha() and i < len(parts) - 1:
            # Check next part to see if we should combine them
            fixed_parts.append(part + '.')
        else:
            fixed_parts.append(part)
    
    return ' '.join(fixed_parts)


def normalize_json_candidates():
    """Normalize all candidate names in the JSON file."""
    json_file = Path(__file__).parent.parent / "data" / "pa_election_results.json"
    
    print(f"[INFO] Loading JSON from {json_file}...")
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    # Track changes
    names_updated = {}
    count = 0
    
    # Iterate through all results
    for year_data in data.get("results_by_year", {}).values():
        for office_data in year_data.values():
            for contest_data in office_data.values():
                for county_data in contest_data.get("results", {}).values():
                    # Normalize dem_candidate
                    if "dem_candidate" in county_data:
                        old_name = county_data["dem_candidate"]
                        new_name = normalize_name(old_name)
                        if old_name != new_name:
                            if old_name not in names_updated:
                                names_updated[old_name] = new_name
                            county_data["dem_candidate"] = new_name
                            count += 1
                    
                    # Normalize rep_candidate
                    if "rep_candidate" in county_data:
                        old_name = county_data["rep_candidate"]
                        new_name = normalize_name(old_name)
                        if old_name != new_name:
                            if old_name not in names_updated:
                                names_updated[old_name] = new_name
                            county_data["rep_candidate"] = new_name
                            count += 1
    
    # Save updated JSON
    print(f"[INFO] Saving normalized JSON to {json_file}...")
    with open(json_file, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"\n[SUCCESS] Normalization complete!")
    print(f"  - Total name fields updated: {count}")
    print(f"  - Unique names normalized: {len(names_updated)}")
    
    if names_updated:
        print(f"\n  Sample normalizations:")
        for old, new in sorted(names_updated.items())[:10]:
            print(f"    '{old}' -> '{new}'")
        if len(names_updated) > 10:
            print(f"    ... and {len(names_updated) - 10} more")


if __name__ == "__main__":
    normalize_json_candidates()
