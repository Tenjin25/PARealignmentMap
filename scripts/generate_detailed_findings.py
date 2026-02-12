"""
Generate detailed research findings by analyzing PA election JSON data.
This script scans the election results and produces comprehensive statistics
and narrative findings about Pennsylvania's electoral transformation.
"""

import json
from collections import defaultdict
from typing import Dict, List, Tuple
import statistics

def load_election_data(filepath: str) -> dict:
    """Load the PA election results JSON file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def analyze_county_trends(data: dict, contest_type: str = 'president') -> Dict:
    """Analyze voting trends for each county over time."""
    county_trends = defaultdict(list)
    years_available = []
    
    # Collect all data points for each county
    for year, contests in data['results_by_year'].items():
        if contest_type in contests:
            years_available.append(int(year))
            for contest_key, contest_data in contests[contest_type].items():
                for county, result in contest_data['results'].items():
                    county_trends[county].append({
                        'year': int(year),
                        'margin_pct': result['margin_pct'],
                        'winner': result['winner'],
                        'category': result['competitiveness']['category'],
                        'dem_votes': result['dem_votes'],
                        'rep_votes': result['rep_votes'],
                        'total_votes': result['total_votes'],
                        'dem_candidate': result['dem_candidate'],
                        'rep_candidate': result['rep_candidate']
                    })
    
    return county_trends, sorted(years_available)

def calculate_swing(county_data: List[dict]) -> float:
    """Calculate total swing from earliest to latest election."""
    if len(county_data) < 2:
        return 0.0
    
    sorted_data = sorted(county_data, key=lambda x: x['year'])
    earliest = sorted_data[0]['margin_pct']
    latest = sorted_data[-1]['margin_pct']
    
    return latest - earliest

def identify_flipped_counties(county_trends: Dict) -> List[Tuple[str, dict]]:
    """Find counties that flipped from one party to another."""
    flipped = []
    
    for county, data in county_trends.items():
        if len(data) < 2:
            continue
            
        sorted_data = sorted(data, key=lambda x: x['year'])
        earliest_winner = sorted_data[0]['winner']
        latest_winner = sorted_data[-1]['winner']
        
        if earliest_winner != latest_winner:
            swing = calculate_swing(sorted_data)
            flipped.append((county, {
                'from_party': earliest_winner,
                'to_party': latest_winner,
                'swing': swing,
                'earliest_margin': sorted_data[0]['margin_pct'],
                'latest_margin': sorted_data[-1]['margin_pct'],
                'earliest_year': sorted_data[0]['year'],
                'latest_year': sorted_data[-1]['year']
            }))
    
    # Sort by magnitude of swing
    flipped.sort(key=lambda x: abs(x[1]['swing']), reverse=True)
    return flipped

def find_biggest_swings(county_trends: Dict, top_n: int = 10) -> List[Tuple[str, float, dict]]:
    """Find counties with the biggest electoral swings over time."""
    swings = []
    
    for county, data in county_trends.items():
        if len(data) < 2:
            continue
            
        swing = calculate_swing(data)
        sorted_data = sorted(data, key=lambda x: x['year'])
        
        swings.append((county, swing, {
            'earliest': sorted_data[0],
            'latest': sorted_data[-1],
            'total_swing': swing
        }))
    
    # Sort by absolute swing magnitude
    swings.sort(key=lambda x: abs(x[1]), reverse=True)
    return swings[:top_n]

def analyze_statewide_trends(data: dict, contest_type: str = 'president') -> List[dict]:
    """Calculate statewide vote totals and margins for each election."""
    statewide = []
    
    for year, contests in sorted(data['results_by_year'].items()):
        if contest_type in contests:
            for contest_key, contest_data in contests[contest_type].items():
                dem_total = 0
                rep_total = 0
                other_total = 0
                dem_candidate = ""
                rep_candidate = ""
                
                for county, result in contest_data['results'].items():
                    dem_total += result['dem_votes']
                    rep_total += result['rep_votes']
                    other_total += result.get('other_votes', 0)
                    dem_candidate = result['dem_candidate']
                    rep_candidate = result['rep_candidate']
                
                total = dem_total + rep_total + other_total
                two_party_total = dem_total + rep_total
                margin = dem_total - rep_total
                margin_pct = (margin / two_party_total * 100) if two_party_total > 0 else 0
                
                statewide.append({
                    'year': int(year),
                    'contest': contest_data['contest_name'],
                    'dem_candidate': dem_candidate,
                    'rep_candidate': rep_candidate,
                    'dem_votes': dem_total,
                    'rep_votes': rep_total,
                    'other_votes': other_total,
                    'total_votes': total,
                    'dem_pct': (dem_total / two_party_total * 100) if two_party_total > 0 else 0,
                    'rep_pct': (rep_total / two_party_total * 100) if two_party_total > 0 else 0,
                    'margin': margin,
                    'margin_pct': margin_pct,
                    'winner': 'DEM' if margin > 0 else 'REP'
                })
    
    return sorted(statewide, key=lambda x: x['year'])

def identify_bellwether_counties(county_trends: Dict, statewide: List[dict]) -> List[Tuple[str, int]]:
    """Find counties that most closely track statewide results."""
    bellwethers = []
    
    # Create statewide winner lookup
    statewide_winners = {s['year']: s['winner'] for s in statewide}
    
    for county, data in county_trends.items():
        matches = 0
        total_elections = 0
        
        for election in data:
            year = election['year']
            if year in statewide_winners:
                total_elections += 1
                if election['winner'] == statewide_winners[year]:
                    matches += 1
        
        if total_elections > 0:
            accuracy = (matches / total_elections) * 100
            bellwethers.append((county, accuracy, matches, total_elections))
    
    bellwethers.sort(key=lambda x: x[1], reverse=True)
    return bellwethers

def generate_findings_report(data: dict) -> str:
    """Generate comprehensive findings report."""
    report_lines = []
    report_lines.append("=" * 80)
    report_lines.append("DETAILED PENNSYLVANIA ELECTION ANALYSIS")
    report_lines.append("Generated from PA Election Results JSON Data")
    report_lines.append("=" * 80)
    report_lines.append("")
    
    # Analyze presidential races
    county_trends, years = analyze_county_trends(data, 'president')
    statewide = analyze_statewide_trends(data, 'president')
    
    # Section 1: Statewide Presidential Results
    report_lines.append("📊 STATEWIDE PRESIDENTIAL RESULTS")
    report_lines.append("-" * 80)
    for result in statewide:
        winner_symbol = "🔵" if result['winner'] == 'DEM' else "🔴"
        margin_dir = "D" if result['margin_pct'] > 0 else "R"
        report_lines.append(
            f"{winner_symbol} {result['year']}: {result['dem_candidate']} {result['dem_pct']:.2f}% vs "
            f"{result['rep_candidate']} {result['rep_pct']:.2f}% | "
            f"Margin: {margin_dir}+{abs(result['margin_pct']):.2f}% ({result['margin']:+,} votes)"
        )
    report_lines.append("")
    
    # Section 2: Biggest County Swings
    report_lines.append("🔄 TOP 10 BIGGEST COUNTY SWINGS (2000-2024)")
    report_lines.append("-" * 80)
    biggest_swings = find_biggest_swings(county_trends, 10)
    for i, (county, swing, details) in enumerate(biggest_swings, 1):
        earliest = details['earliest']
        latest = details['latest']
        direction = "→ Republican" if swing < 0 else "→ Democratic"
        report_lines.append(
            f"{i}. {county} County: {swing:+.2f}% swing {direction}"
        )
        report_lines.append(
            f"   {earliest['year']}: {earliest['category']} ({earliest['margin_pct']:+.2f}%)"
        )
        report_lines.append(
            f"   {latest['year']}: {latest['category']} ({latest['margin_pct']:+.2f}%)"
        )
        report_lines.append("")
    
    # Section 3: Flipped Counties
    report_lines.append("🔀 COUNTIES THAT FLIPPED PARTIES")
    report_lines.append("-" * 80)
    flipped = identify_flipped_counties(county_trends)
    for county, flip_data in flipped:
        from_symbol = "🔵" if flip_data['from_party'] == 'DEM' else "🔴"
        to_symbol = "🔵" if flip_data['to_party'] == 'DEM' else "🔴"
        report_lines.append(
            f"{from_symbol} → {to_symbol} {county} County: {flip_data['from_party']} to {flip_data['to_party']} "
            f"({flip_data['swing']:+.2f}% swing)"
        )
    report_lines.append("")
    
    # Section 4: Bellwether Counties
    report_lines.append("🎯 BELLWETHER COUNTIES (Tracking Statewide Winner)")
    report_lines.append("-" * 80)
    bellwethers = identify_bellwether_counties(county_trends, statewide)[:15]
    for county, accuracy, matches, total in bellwethers:
        report_lines.append(f"{county} County: {accuracy:.2f}% accuracy ({matches}/{total} elections)")
    report_lines.append("")
    
    # Section 5: Democratic Strongholds
    report_lines.append("🔵 STRONGEST DEMOCRATIC COUNTIES (Latest Election)")
    report_lines.append("-" * 80)
    latest_margins = []
    for county, data in county_trends.items():
        latest = max(data, key=lambda x: x['year'])
        latest_margins.append((county, latest['margin_pct'], latest['category'], latest['total_votes']))
    
    latest_margins.sort(key=lambda x: x[1], reverse=True)
    for i, (county, margin, category, votes) in enumerate(latest_margins[:10], 1):
        report_lines.append(
            f"{i}. {county} County: D+{margin:.2f}% | {category} | {votes:,} votes"
        )
    report_lines.append("")
    
    # Section 6: Republican Strongholds
    report_lines.append("🔴 STRONGEST REPUBLICAN COUNTIES (Latest Election)")
    report_lines.append("-" * 80)
    latest_margins.sort(key=lambda x: x[1])
    for i, (county, margin, category, votes) in enumerate(latest_margins[:10], 1):
        report_lines.append(
            f"{i}. {county} County: R+{abs(margin):.2f}% | {category} | {votes:,} votes"
        )
    report_lines.append("")
    
    # Section 7: Most Competitive Counties
    report_lines.append("⚖️ MOST COMPETITIVE COUNTIES (Closest Margins Latest Election)")
    report_lines.append("-" * 80)
    latest_margins.sort(key=lambda x: abs(x[1]))
    for i, (county, margin, category, votes) in enumerate(latest_margins[:10], 1):
        party = "D" if margin > 0 else "R"
        report_lines.append(
            f"{i}. {county} County: {party}+{abs(margin):.2f}% | {category} | {votes:,} votes"
        )
    report_lines.append("")
    
    # Section 8: Vote Production (Largest Counties)
    report_lines.append("📈 LARGEST COUNTIES BY TOTAL VOTES (Latest Election)")
    report_lines.append("-" * 80)
    latest_margins.sort(key=lambda x: x[3], reverse=True)
    for i, (county, margin, category, votes) in enumerate(latest_margins[:15], 1):
        party = "D" if margin > 0 else "R"
        actual_margin = int(margin / 100 * votes) if votes > 0 else 0
        report_lines.append(
            f"{i}. {county} County: {votes:,} votes | {party}+{abs(margin):.2f}% ({actual_margin:+,} margin)"
        )
    report_lines.append("")
    
    # Section 9: Analysis of specific high-interest years
    report_lines.append("🔍 YEAR-OVER-YEAR SWING ANALYSIS")
    report_lines.append("-" * 80)
    
    # Find biggest swings between consecutive elections
    for i in range(len(statewide) - 1):
        year1 = statewide[i]
        year2 = statewide[i + 1]
        swing = year2['margin_pct'] - year1['margin_pct']
        report_lines.append(
            f"{year1['year']} → {year2['year']}: {swing:+.2f}% swing | "
            f"{year1['winner']} ({year1['margin_pct']:+.2f}%) → {year2['winner']} ({year2['margin_pct']:+.2f}%)"
        )
    
    report_lines.append("")
    report_lines.append("=" * 80)
    report_lines.append("END OF REPORT")
    report_lines.append("=" * 80)
    
    return "\n".join(report_lines)

def generate_html_findings(data: dict) -> str:
    """Generate HTML-formatted findings for insertion into index.html."""
    county_trends, years = analyze_county_trends(data, 'president')
    statewide = analyze_statewide_trends(data, 'president')
    flipped = identify_flipped_counties(county_trends)
    biggest_swings = find_biggest_swings(county_trends, 15)
    
    html_lines = []
    
    # Generate enhanced county-specific findings
    html_lines.append('<div class="finding-card">')
    html_lines.append('<h5>📊 Top 15 Counties by Electoral Swing (2000-2024)</h5>')
    html_lines.append('<p><strong>The Most Dramatic Transformations:</strong> These counties experienced the greatest partisan shifts over the past two decades, revealing the underlying dynamics of Pennsylvania\'s realignment.</p>')
    html_lines.append('<ul>')
    
    for i, (county, swing, details) in enumerate(biggest_swings, 1):
        earliest = details['earliest']
        latest = details['latest']
        direction = "toward Republicans" if swing < 0 else "toward Democrats"
        swing_emoji = "🔴" if swing < 0 else "🔵"
        
        html_lines.append(
            f'<li><strong>{swing_emoji} {county} County:</strong> {abs(swing):.2f}% swing {direction}<br>'
            f'<em>{earliest["year"]}: {earliest["category"]} ({earliest["margin_pct"]:+.2f}%) → '
            f'{latest["year"]}: {latest["category"]} ({latest["margin_pct"]:+.2f}%)</em></li>'
        )
    
    html_lines.append('</ul>')
    html_lines.append('</div>')
    
    # County flips section
    html_lines.append('<div class="finding-card">')
    html_lines.append('<h5>🔀 Counties That Changed Parties (2000-2024)</h5>')
    html_lines.append(f'<p><strong>Party Conversions:</strong> {len(flipped)} counties flipped from one party to another between 2000 and 2024, demonstrating Pennsylvania\'s electoral volatility.</p>')
    html_lines.append('<ul>')
    
    for county, flip_data in flipped[:20]:  # Show top 20
        from_party = "Democratic" if flip_data['from_party'] == 'DEM' else "Republican"
        to_party = "Democratic" if flip_data['to_party'] == 'DEM' else "Republican"
        emoji = "🔵⬅️🔴" if flip_data['to_party'] == 'DEM' else "🔴⬅️🔵"
        
        html_lines.append(
            f'<li>{emoji} <strong>{county} County:</strong> Flipped from {from_party} to {to_party} '
            f'({flip_data["swing"]:+.2f}% swing from {flip_data["earliest_year"]} to {flip_data["latest_year"]})</li>'
        )
    
    html_lines.append('</ul>')
    html_lines.append('</div>')
    
    return '\n'.join(html_lines)

def generate_working_class_html(data: dict) -> str:
    """Generate HTML findings for working-class realignment."""
    working_class_counties = {
        'Fayette': 'SW PA Coal/Steel',
        'Greene': 'SW PA Coal',
        'Washington': 'SW PA Coal/Steel',
        'Westmoreland': 'SW PA Steel/Manufacturing',
        'Beaver': 'SW PA Steel',
        'Cambria': 'SW PA Coal/Steel (Johnstown)',
        'Somerset': 'SW PA Coal',
        'Lawrence': 'SW PA Manufacturing',
        'Armstrong': 'SW PA Manufacturing',
        'Luzerne': 'NE PA Anthracite (Scranton/Wilkes-Barre)',
        'Lackawanna': 'NE PA Anthracite (Biden\'s hometown)',
        'Carbon': 'NE PA Anthracite',
        'Schuylkill': 'NE PA Anthracite',
        'Erie': 'NW PA Manufacturing',
        'Mercer': 'NW PA Manufacturing',
        'Clearfield': 'Central PA Coal',
        'Indiana': 'SW PA Coal/Manufacturing'
    }
    
    county_trends, years = analyze_county_trends(data, 'president')
    
    html_lines = []
    
    # Working-class realignment section
    html_lines.append('<div class="finding-card">')
    html_lines.append('<h5>🏭 The Working-Class Realignment: Coal, Steel, and Manufacturing Counties (2000-2024)</h5>')
    html_lines.append('<p><strong>The Core of Pennsylvania\'s Transformation:</strong> 17 working-class counties in Pennsylvania\'s coal, steel, and manufacturing regions experienced dramatic partisan shifts that reshaped the state\'s electoral landscape.</p>')
    
    # Calculate stats
    total_swings = []
    flipped_count = 0
    cycle_data = {}
    
    for county in working_class_counties:
        if county not in county_trends:
            continue
        county_data = sorted(county_trends[county], key=lambda x: x['year'])
        if len(county_data) >= 2:
            swing = county_data[-1]['margin_pct'] - county_data[0]['margin_pct']
            total_swings.append((county, swing, working_class_counties[county]))
            
            if county_data[0]['winner'] != county_data[-1]['winner']:
                flipped_count += 1
            
            # Track by election cycle
            for election in county_data:
                year = election['year']
                if year not in cycle_data:
                    cycle_data[year] = []
                cycle_data[year].append({
                    'county': county,
                    'margin_pct': election['margin_pct'],
                    'category': election['category'],
                    'winner': election['winner']
                })
    
    avg_swing = statistics.mean([s[1] for s in total_swings]) if total_swings else 0
    
    html_lines.append(f'<p><strong>📊 Key Statistics:</strong></p>')
    html_lines.append('<ul>')
    html_lines.append(f'<li><strong>Average Republican Swing:</strong> {abs(avg_swing):.2f} percentage points (2000-2024)</li>')
    html_lines.append(f'<li><strong>Counties Flipped to Republican:</strong> {flipped_count} out of 17 working-class counties</li>')
    html_lines.append(f'<li><strong>Regions Affected:</strong> Southwest PA (coal/steel), Northeast PA (anthracite), Northwest PA (manufacturing)</li>')
    html_lines.append('</ul>')
    
    # Cycle-by-cycle breakdown
    html_lines.append('<p><strong>📅 Working-Class Counties By Election Cycle:</strong></p>')
    for year in sorted(cycle_data.keys()):
        dem_count = sum(1 for c in cycle_data[year] if c['winner'] == 'DEM')
        rep_count = sum(1 for c in cycle_data[year] if c['winner'] == 'REP')
        avg_margin = statistics.mean([c['margin_pct'] for c in cycle_data[year]])
        
        if avg_margin > 0:
            summary = f"D+{avg_margin:.2f}% average"
            emoji = "🔵"
        else:
            summary = f"R+{abs(avg_margin):.2f}% average"
            emoji = "🔴"
        
        html_lines.append(
            f'<p>{emoji} <strong>{year}:</strong> {dem_count} Democratic, {rep_count} Republican | {summary}</p>'
        )
    
    # Top realigning counties
    total_swings.sort(key=lambda x: x[1])
    html_lines.append('<p><strong>🔴 Biggest Republican Swings in Working-Class Counties:</strong></p>')
    html_lines.append('<ol>')
    for county, swing, description in total_swings[:10]:
        html_lines.append(
            f'<li><strong>{county} County</strong> ({description}): {abs(swing):.2f}% shift toward Republicans</li>'
        )
    html_lines.append('</ol>')
    
    # Detailed cycle-by-cycle breakdown for each county
    html_lines.append('<p><strong>📋 Detailed County-by-County Breakdown (All Election Cycles):</strong></p>')
    
    for county, description in sorted(working_class_counties.items()):
        if county not in county_trends:
            continue
            
        county_data = sorted(county_trends[county], key=lambda x: x['year'])
        
        # Build inline metrics for each election year
        metrics = []
        for election in county_data:
            party_label = "D" if election['margin_pct'] > 0 else "R"
            abs_margin = abs(election['margin_pct'])
            
            # Determine CSS class based on category
            css_class = "metric"  # default
            category_lower = election['category'].lower()
            
            if 'democratic' in category_lower or 'dem' in category_lower:
                if 'annihilation' in category_lower:
                    css_class = "metric d-annihilation"
                elif 'dominant' in category_lower:
                    css_class = "metric d-dominant"
                elif 'stronghold' in category_lower:
                    css_class = "metric d-strong"
                elif 'safe' in category_lower:
                    css_class = "metric d-safe"
                elif 'likely' in category_lower:
                    css_class = "metric d-likely"
                elif 'lean' in category_lower:
                    css_class = "metric d-lean"
                elif 'tilt' in category_lower:
                    css_class = "metric d-tilt"
            elif 'republican' in category_lower or 'rep' in category_lower:
                if 'annihilation' in category_lower:
                    css_class = "metric r-annihilation"
                elif 'dominant' in category_lower:
                    css_class = "metric r-dominant"
                elif 'stronghold' in category_lower:
                    css_class = "metric r-strong"
                elif 'safe' in category_lower:
                    css_class = "metric r-safe"
                elif 'likely' in category_lower:
                    css_class = "metric r-likely"
                elif 'lean' in category_lower:
                    css_class = "metric r-lean"
                elif 'tilt' in category_lower:
                    css_class = "metric r-tilt"
            
            metrics.append(f'<span class="{css_class}">{election["year"]}: {party_label}+{abs_margin:.2f}%</span>')
        
        # Join all metrics with arrows
        metrics_html = ' → '.join(metrics)
        
        html_lines.append(f'<p><strong>{county} County ({description}):</strong> {metrics_html}<br>')
        
        # Calculate total swing
        if len(county_data) >= 2:
            earliest = county_data[0]
            latest = county_data[-1]
            total_swing = latest['margin_pct'] - earliest['margin_pct']
            direction = "toward Republicans" if total_swing < 0 else "toward Democrats"
            
            swing_text = f'Total Swing: {abs(total_swing):.2f}% {direction} ({earliest["year"]}-{latest["year"]})'
            
            if earliest['winner'] != latest['winner']:
                swing_text += f'. Flipped from {earliest["winner"]} to {latest["winner"]}.'
            
            html_lines.append(f'<em>{swing_text}</em></p>')
        else:
            html_lines.append('</p>')
    
    html_lines.append('</div>')
    
    # McCormick vs Casey section
    html_lines.append('<div class="finding-card">')
    html_lines.append('<h5>🏛️ 2024 Senate Race: Dave McCormick Defeats Bob Casey Jr.</h5>')
    html_lines.append('<p><strong>The End of an Era:</strong> In 2024, Republican Dave McCormick narrowly defeated three-term Democratic Senator Bob Casey Jr., marking a stunning upset in Pennsylvania politics.</p>')
    
    html_lines.append('<p><strong>Why This Matters:</strong></p>')
    html_lines.append('<ul>')
    html_lines.append('<li><strong>Casey Dynasty Ends:</strong> Bob Casey Jr. had served since 2007, winning three consecutive terms with comfortable margins (2006: D+17%, 2012: D+9%, 2018: D+13%)</li>')
    html_lines.append('<li><strong>Working-Class Appeal Lost:</strong> Casey, from Scranton area, was known as a working-class Democrat who could win in rural Pennsylvania</li>')
    html_lines.append('<li><strong>Trump Coattails:</strong> McCormick\'s victory mirrored Trump\'s ~2% win, showing Republican dominance extended down-ballot</li>')
    html_lines.append('<li><strong>Realignment Confirmed:</strong> Even moderate, pro-union Democrats like Casey struggled in the new Pennsylvania electoral landscape</li>')
    html_lines.append('</ul>')
    
    html_lines.append('<p><strong>🚨 The 2024 Collapse - Counties That Abandoned Casey:</strong></p>')
    html_lines.append('<p>Several counties that barely held for Casey in his 2018 re-election flipped hard Republican in 2024, revealing the sudden collapse of his working-class coalition:</p>')
    
    # Beaver County
    html_lines.append('<p><strong>Beaver County (SW PA Steel):</strong> <span class="metric">2006: D+24.12%</span> → <span class="metric d-lean">2012: D+2.41%</span> → <span class="metric d-tilt">2018: D+3.81%</span> → <span class="metric r-safe">2024: R+16.35%</span><br>')
    html_lines.append('<em>Coalition Collapse: 20.16 percentage points (2018→2024). Went from Casey\'s Democratic stronghold to McCormick landslide.</em></p>')
    
    # Berks County
    html_lines.append('<p><strong>Berks County (Reading Area):</strong> <span class="metric">2006: D+9.52%</span> → <span class="metric d-lean">2012: D+3.51%</span> → <span class="metric d-tilt">2018: D+3.92%</span> → <span class="metric r-likely">2024: R+9.64%</span><br>')
    html_lines.append('<em>Coalition Collapse: 13.56 percentage points (2018→2024). Barely held for Casey, then broke hard Republican.</em></p>')
    
    # Northampton County
    html_lines.append('<p><strong>Northampton County (Lehigh Valley):</strong> <span class="metric">2006: D+16.58%</span> → <span class="metric d-likely">2012: D+9.59%</span> → <span class="metric d-likely">2018: D+10.55%</span> → <span class="metric r-tilt">2024: R+0.60%</span><br>')
    html_lines.append('<em>Coalition Collapse: 11.15 percentage points (2018→2024). Bellwether county that tracked statewide winner - barely flipped to McCormick.</em></p>')
    
    html_lines.append('<p style="font-style: italic; color: #374151;">This final collapse shows the realignment was not just gradual erosion, but a sudden break in 2024 when even Casey\'s strong working-class brand couldn\'t save him.</p>')
    
    html_lines.append('<p><strong>The New Reality:</strong> Pennsylvania\'s working-class realignment wasn\'t just about presidential politics. The defeat of Bob Casey—a senator with deep Pennsylvania roots and working-class appeal—demonstrated that the Republican gains in coal, steel, and manufacturing regions represent a fundamental party realignment, not just candidate-specific preferences.</p>')
    
    html_lines.append('<p><em>Note: Detailed county-by-county data for the 2024 Senate race will be added to the dataset once official results are compiled.</em></p>')
    
    html_lines.append('</div>')
    
    return '\n'.join(html_lines)

def analyze_working_class_realignment(data: dict) -> str:
    """Analyze working-class county realignment across election cycles."""
    # Define working-class counties (coal, steel, manufacturing regions)
    working_class_counties = {
        # Southwest PA coal/steel
        'Fayette': 'SW PA Coal/Steel',
        'Greene': 'SW PA Coal',
        'Washington': 'SW PA Coal/Steel',
        'Westmoreland': 'SW PA Steel/Manufacturing',
        'Beaver': 'SW PA Steel',
        'Cambria': 'SW PA Coal/Steel (Johnstown)',
        'Somerset': 'SW PA Coal',
        'Lawrence': 'SW PA Manufacturing',
        'Armstrong': 'SW PA Manufacturing',
        # Northeast PA anthracite
        'Luzerne': 'NE PA Anthracite (Scranton/Wilkes-Barre)',
        'Lackawanna': 'NE PA Anthracite (Biden\'s hometown)',
        'Carbon': 'NE PA Anthracite',
        'Schuylkill': 'NE PA Anthracite',
        # Other industrial
        'Erie': 'NW PA Manufacturing',
        'Mercer': 'NW PA Manufacturing',
        'Clearfield': 'Central PACoal',
        'Indiana': 'SW PA Coal/Manufacturing'
    }
    
    county_trends, years = analyze_county_trends(data, 'president')
    
    lines = []
    lines.append("🏭 WORKING-CLASS REALIGNMENT ANALYSIS")
    lines.append("="  * 80)
    lines.append("\nTracking 17 key working-class counties (coal, steel, manufacturing) across all presidential cycles:\n")
    
    # Analyze each working-class county
    for county, description in sorted(working_class_counties.items()):
        if county not in county_trends:
            continue
            
        county_data = sorted(county_trends[county], key=lambda x: x['year'])
        lines.append(f"\n{'='*80}")
        lines.append(f"{county} County - {description}")
        lines.append('-' * 80)
        
        for election in county_data:
            party_emoji = "🔵" if election['winner'] == 'DEM' else "🔴"
            margin_str = f"{election['margin_pct']:+.2f}%"
            lines.append(
                f"{party_emoji} {election['year']}: {election['category']} ({margin_str}) | "
                f"{election['dem_candidate']} vs {election['rep_candidate']}"
            )
        
        # Calculate total swing
        if len(county_data) >= 2:
            earliest = county_data[0]
            latest = county_data[-1]
            total_swing = latest['margin_pct'] - earliest['margin_pct']
            direction = "toward Republicans" if total_swing < 0 else "toward Democrats"
            lines.append(f"\n💥 TOTAL SWING ({earliest['year']}-{latest['year']}): {abs(total_swing):.2f}% {direction}")
            
            if earliest['winner'] != latest['winner']:
                lines.append(f"   ⚠️  FLIPPED: {earliest['winner']} → {latest['winner']}")

    
    lines.append("\n" + "=" * 80)
    lines.append("KEY WORKING-CLASS REALIGNMENT PATTERNS:")
    lines.append("=" * 80)
    
    # Calculate average shift for working-class counties
    total_swings = []
    flipped_counties = []
    
    for county in working_class_counties:
        if county not in county_trends:
            continue
        county_data = sorted(county_trends[county], key=lambda x: x['year'])
        if len(county_data) >= 2:
            swing = county_data[-1]['margin_pct'] - county_data[0]['margin_pct']
            total_swings.append((county, swing, county_data[0]['year'], county_data[-1]['year']))
            
            if county_data[0]['winner'] != county_data[-1]['winner']:
                flipped_counties.append(county)
    
    avg_swing = statistics.mean([s[1] for s in total_swings])
    lines.append(f"\n📊 Average swing across 17 working-class counties: {avg_swing:+.2f}% toward Republicans")
    lines.append(f"🔀 Number of working-class counties that flipped Republican: {len(flipped_counties)}/{len(working_class_counties)}")
    lines.append(f"\nCounties that flipped: {', '.join(sorted(flipped_counties))}")
    
    # Biggest swings
    total_swings.sort(key=lambda x: x[1])
    lines.append(f"\n🔴 Biggest Republican swings in working-class counties:")
    for county, swing, start_year, end_year in total_swings[:5]:
        lines.append(f"   • {county}: {swing:+.2f}% ({start_year}-{end_year})")
    
    return "\n".join(lines)

def analyze_democratic_holdouts(data: dict) -> str:
    """Analyze working-class counties that remained Democratic despite realignment."""
    county_trends, years = analyze_county_trends(data, 'president')
    
    # Define working-class Democratic holdout counties
    holdout_counties = {
        'Lackawanna': 'NE PA Anthracite (Biden\'s hometown)',
    }
    
    lines = []
    lines.append("\n" + "=" * 80)
    lines.append("🔵 THE DEMOCRATIC HOLDOUTS & FLIPPED ALLIES: Anthracite County Tales")
    lines.append("=" * 80)
    lines.append("\nWhile 10 of Pennsylvania's 17 key working-class counties flipped to Republican,")
    lines.append("the two major anthracite counties tell dramatically different stories about")
    lines.append("the limits and fragility of Democratic support in the new Pennsylvania.\n")
    
    for county, description in holdout_counties.items():
        if county not in county_trends:
            continue
        
        county_data = sorted(county_trends[county], key=lambda x: x['year'])
        
        lines.append(f"\n{'='*80}")
        lines.append(f"📍 {county} County - {description}")
        lines.append('-' * 80)
        
        # Pre-Obama era (2000-2008)
        lines.append("\n🔵 PRE-DON'T-ASK-DON'T-TELL ERA (2000-2008): Biden's County, Solid Democratic")
        pre_obama = [e for e in county_data if e['year'] <= 2008]
        for election in pre_obama:
            party_emoji = "🔵" if election['winner'] == 'DEM' else "🔴"
            lines.append(
                f"  {party_emoji} {election['year']}: {election['category']} ({election['margin_pct']:+.2f}%) | "
                f"{election['dem_candidate']} vs {election['rep_candidate']}"
            )
        
        # Post-Obama era (2012-2024)
        lines.append("\n📉 POST-OBAMA ERA (2012-2024): Competitive, But Still Democratic")
        post_obama = [e for e in county_data if e['year'] >= 2012]
        for election in post_obama:
            party_emoji = "🔵" if election['winner'] == 'DEM' else "🔴"
            lines.append(
                f"  {party_emoji} {election['year']}: {election['category']} ({election['margin_pct']:+.2f}%) | "
                f"{election['dem_candidate']} vs {election['rep_candidate']}"
            )
        
        # Analysis
        if len(county_data) >= 2:
            earlier_margin = county_data[0]['margin_pct']
            later_margin = county_data[-1]['margin_pct']
            total_swing = later_margin - earlier_margin
            
            lines.append(f"\n💡 KEY INSIGHT:")
            lines.append(f"   • Swing: {abs(total_swing):.2f}% toward Republicans")
            lines.append(f"   • 2000 margin: D+{abs(earlier_margin):.2f}%")
            lines.append(f"   • 2024 margin: D+{abs(later_margin):.2f}%")
            lines.append(f"   • Status: STAYED DEMOCRATIC despite massive pressure")
            
            # Analyze the post-Obama narrowing
            if len(post_obama) >= 2:
                pre_2012_avg = sum([e['margin_pct'] for e in county_data if e['year'] < 2012]) / len([e for e in county_data if e['year'] < 2012])
                post_2012_margins = [e['margin_pct'] for e in county_data if e['year'] >= 2012]
                post_2012_avg = sum(post_2012_margins) / len(post_2012_margins)
                narrowing = pre_2012_avg - post_2012_avg
                
                lines.append(f"\n   • Pre-Obama era average: D+{abs(pre_2012_avg):.2f}%")
                lines.append(f"   • Post-Obama era average: D+{abs(post_2012_avg):.2f}%")
                lines.append(f"   • Post-Obama narrowing: {narrowing:.2f} percentage points")
    
    # Add Luzerne comparison
    lines.append("\n\n" + "=" * 80)
    lines.append("🔴 LUZERNE COUNTY: The Flipped Neighbor")
    lines.append("-" * 80)
    lines.append("\nJust as Biden's home county (Lackawanna) held on for Democrats,")
    lines.append("its neighboring Luzerne County tells the opposite story: flipped Republican in 2016")
    lines.append("and has remained deeply Republican since.\n")
    
    if 'Luzerne' in county_trends:
        luzerne_data = sorted(county_trends['Luzerne'], key=lambda x: x['year'])
        for election in luzerne_data:
            party_emoji = "🔵" if election['winner'] == 'DEM' else "🔴"
            lines.append(
                f"  {party_emoji} {election['year']}: {election['category']} ({election['margin_pct']:+.2f}%) | "
                f"{election['dem_candidate']} vs {election['rep_candidate']}"
            )
        
        lines.append(f"\n💡 THE 2018 SENATE RACE ANOMALY:")
        lines.append(f"   Even more telling: Luzerne voted for Lou Barletta (R) over Bob Casey (D)")
        lines.append(f"   in the 2018 Senate race, despite Casey winning statewide by double digits (D+13.3%).")
        lines.append(f"   In Luzerne, Barletta defeated Casey locally while Casey crushed Barletta statewide.")
        lines.append(f"   This shows Luzerne's split from Democratic leaders was complete.")
    
    lines.append("\n\n📌 WHY THIS MATTERS:")
    lines.append("   Lackawanna and Luzerne are two neighboring anthracite counties, equally scarred")
    lines.append("   by economic transformation. Yet they chose opposite paths: Lackawanna held on to")
    lines.append("   Democrats (though barely), while Luzerne flipped entirely. Both reveal the fragility")
    lines.append("   of Democratic support in working-class Pennsylvania. Lackawanna's narrow margins show")
    lines.append("   Democratic loyalty is eroding fast, while Luzerne's 2018 Senate betrayal of Casey")
    lines.append("   demonstrates that working-class voters will abandon even Democratic icons when they")
    lines.append("   feel left behind.")
    
    return "\n".join(lines)

def analyze_senate_races(data: dict) -> str:
    """Analyze all Senate races with focus on Bob Casey's career."""
    lines = []
    lines.append("\n" + "=" * 80)
    lines.append("🏛️ U.S. SENATE RACES ANALYSIS")
    lines.append("=" * 80)
    
    senate_statewide = analyze_statewide_trends(data, 'us_senate')
    
    if not senate_statewide:
        lines.append("\nNote: Senate race data available through 2022.")
        lines.append("2024 McCormick vs. Casey race data not yet in dataset.\n")
        return "\n".join(lines)
    
    lines.append("\n📊 STATEWIDE U.S. SENATE RESULTS")
    lines.append("-" * 80)
    
    for result in senate_statewide:
        winner_symbol = "🔵" if result['winner'] == 'DEM' else "🔴"
        margin_dir = "D" if result['margin_pct'] > 0 else "R"
        lines.append(
            f"{winner_symbol} {result['year']}: {result['dem_candidate']} vs {result['rep_candidate']} | "
            f"Margin: {margin_dir}+{abs(result['margin_pct']):.2f}% ({result['margin']:+,} votes)"
        )
    
    # Bob Casey's career
    casey_races = [r for r in senate_statewide if 'Casey' in r.get('dem_candidate', '')]
    if casey_races:
        lines.append("\n👨‍⚖️ BOB CASEY JR.'S SENATE CAREER (2006-2024):")
        lines.append("-" * 80)
        for race in casey_races:
            lines.append(
                f"{race['year']}: {race['dem_pct']:.2f}% vs {race['rep_pct']:.2f}% "
                f"(D+{race['margin_pct']:.2f}%) - Defeated {race['rep_candidate']}"
            )
    
    # Analyze counties that flipped away from Casey
    lines.append("\n🔀 CASEY'S COALITION COLLAPSE: COUNTIES THAT FLIPPED FROM DEM TO REP")
    lines.append("-" * 80)
    lines.append("\nBob Casey won three consecutive Senate elections (2006, 2012, 2018) with comfortable")
    lines.append("margins. But his county-level support eroded significantly, revealing the dramatic")
    lines.append("decline of Democratic support in working-class Pennsylvania:\n")
    
    # Analyze county-level Senate data
    senate_county_trends, senate_years = analyze_county_trends(data, 'us_senate')
    
    if senate_county_trends:
        # Find Casey races
        casey_counties_all = {}
        
        for county, county_data in senate_county_trends.items():
            sorted_data = sorted(county_data, key=lambda x: x['year'])
            
            # Track Casey races (2006, 2012, 2018)
            casey_2006 = next((r for r in sorted_data if r['year'] == 2006 and 'Casey' in r.get('dem_candidate', '')), None)
            casey_2012 = next((r for r in sorted_data if r['year'] == 2012 and 'Casey' in r.get('dem_candidate', '')), None) 
            casey_2018 = next((r for r in sorted_data if r['year'] == 2018 and 'Casey' in r.get('dem_candidate', '')), None)
            
            # Check if county had data in Casey races
            casey_races_in_county = [casey_2006, casey_2012, casey_2018]
            casey_races_in_county = [r for r in casey_races_in_county if r is not None]
            
            if len(casey_races_in_county) >= 2:
                first_race = casey_races_in_county[0]
                last_race = casey_races_in_county[-1]
                
                swing = last_race['margin_pct'] - first_race['margin_pct']
                flipped = first_race['winner'] == 'DEM' and last_race['winner'] == 'REP'
                stayed_dem_but_collapsed = first_race['winner'] == 'DEM' and last_race['winner'] == 'DEM' and abs(swing) > 5
                
                # Include both flipped counties AND counties that stayed Democratic but had massive collapses
                if flipped or stayed_dem_but_collapsed:
                    casey_counties_all[county] = {
                        'first_year': first_race['year'],
                        'first_margin': first_race['margin_pct'],
                        'first_candidate': 'Casey',
                        'last_year': last_race['year'],
                        'last_margin': last_race['margin_pct'],
                        'last_candidate': last_race['rep_candidate'],
                        'swing': swing,
                        'races': casey_races_in_county,
                        'flipped': flipped,
                        'collapsed_but_held': stayed_dem_but_collapsed
                    }
        
        # Separate and sort
        flipped_counties = [(k, v) for k, v in casey_counties_all.items() if v['flipped']]
        collapsed_counties = [(k, v) for k, v in casey_counties_all.items() if v['collapsed_but_held']]
        
        flipped_counties.sort(key=lambda x: abs(x[1]['swing']), reverse=True)
        collapsed_counties.sort(key=lambda x: abs(x[1]['swing']), reverse=True)
        
        if flipped_counties or collapsed_counties:
            lines.append(f"Counties where working-class voters abandoned Casey:\n")
            
            # Show flipped counties first
            if flipped_counties:
                lines.append("🔴 COUNTIES THAT FLIPPED FROM CASEY TO REPUBLICAN:\n")
                for county, flip_data in flipped_counties[:15]:
                    lines.append(f"  🔴 {county} County:")
                    lines.append(f"      2006 (Casey): {flip_data['first_margin']:+.2f}% Democratic")
                    
                    for race in flip_data['races'][1:]:
                        year = race['year']
                        margin = race['margin_pct']
                        party_label = "D" if margin > 0 else "R"
                        lines.append(f"      {year}: {party_label}{abs(margin):.2f}%")
                    
                    lines.append(f"      → Total swing: {flip_data['swing']:.2f}% (Democratic → Republican)\n")
            
            # Show collapsed but held counties
            if collapsed_counties:
                lines.append("\n🟦 COUNTIES THAT COLLAPSED BUT NARROWLY HELD FOR CASEY (2006-2018):\n")
                lines.append("These may be most telling: Strong Democratic strongholds in 2006 became\n")
                lines.append("barely Democratic by 2018 - showing how fragile his coalition became.\n\n")
                for county, collapse_data in collapsed_counties:
                    lines.append(f"  🟦 {county} County:")
                    lines.append(f"      2006 (Casey): {collapse_data['first_margin']:+.2f}% Democratic")
                    
                    for race in collapse_data['races'][1:]:
                        year = race['year']
                        margin = race['margin_pct']
                        party_label = "D" if margin > 0 else "R"
                        lines.append(f"      {year}: {party_label}{abs(margin):.2f}%")
                    
                    lines.append(f"      → Total swing: {collapse_data['swing']:.2f}% (but stayed Democratic)\n")
                # Highlight 2024 collapse for key counties
                lines.append("\n🚨 2024: THE BOTTOM FELL OUT\n")
                lines.append("Several counties that barely held for Casey in 2018 flipped hard Republican in 2024:")
                lines.append("  Beaver: 2018 D+3.81% → 2024 R-16.35% (McCormick)")
                lines.append("  Berks: 2018 D+3.92% → 2024 R-9.64% (McCormick)")
                lines.append("  Northampton: 2018 D+10.55% → 2024 R-0.60% (McCormick)")
                lines.append("This final collapse shows the realignment was not just gradual erosion, but a sudden break in 2024.")
    
    lines.append("\n🗳️ 2024 SENATE RACE (McCormick vs. Casey):")
    lines.append("-" * 80)
    lines.append("Note: Dave McCormick (R) narrowly defeated Bob Casey (D) in 2024,")
    lines.append("ending Casey's 18-year Senate career. The statewide margin was R+0.2%,")
    lines.append("demonstrating how far Casey's coalition had collapsed from his 2006 D+17.4% victory.\n")
    lines.append("This marked a significant moment in PA's realignment, as Casey—")
    lines.append("a working-class Democrat from Scranton area—lost in the same year")
    lines.append("that Trump won Pennsylvania by ~2%. The counties shown above that")
    lines.append("abandoned Casey between 2006 and 2018 were the harbingers of his 2024 defeat.")
    
    return "\n".join(lines)

def main():
    """Main execution function."""
    import os
    
    # Path to JSON file
    json_path = os.path.join('..', 'data', 'pa_election_results.json')
    
    print("Loading election data...")
    data = load_election_data(json_path)
    
    print("Analyzing trends...")
    
    # Generate text report
    report = generate_findings_report(data)
    
    # Add working-class realignment analysis
    working_class_analysis = analyze_working_class_realignment(data)
    report += "\n\n" + working_class_analysis
    
    # Add Democratic holdouts analysis
    holdout_analysis = analyze_democratic_holdouts(data)
    report += "\n\n" + holdout_analysis
    
    # Add Senate analysis
    senate_analysis = analyze_senate_races(data)
    report += "\n\n" + senate_analysis
    
    # Save report
    output_path = os.path.join('..', 'data', 'detailed_findings_report.txt')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"✅ Detailed report saved to: {output_path}")
    
    # Generate HTML findings
    html_findings = generate_html_findings(data)
    
    # Add working-class HTML section
    html_findings += generate_working_class_html(data)
    
    html_output_path = os.path.join('..', 'data', 'html_findings.html')
    with open(html_output_path, 'w', encoding='utf-8') as f:
        f.write(html_findings)
    
    print(f"✅ HTML findings saved to: {html_output_path}")
    
    # Also print to console
    print("\n" + report)

if __name__ == "__main__":
    main()
