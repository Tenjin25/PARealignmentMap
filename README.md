# Pennsylvania Political Realignment Map (2000-2024)

An interactive web-based visualization exploring Pennsylvania's transformation from a reliably Democratic state to America's most critical swing state. This project analyzes 24 years of election data across all 67 Pennsylvania counties, tracking how voting patterns have shifted and what these changes mean for presidential politics.

## 🗺️ Overview

Pennsylvania has undergone a dramatic political realignment over the past two decades. This visualization provides an interactive framework to explore that transformation at the county level, revealing:

- **Working-class realignment**: Counties like Lackawanna (Biden's hometown) and Luzerne flipped from Democratic strongholds to Republican leans
- **Suburban shifts**: Philadelphia collar counties (Montgomery, Delaware, Chester, Bucks) transformed from Republican to Democratic
- **Urban Democratic firewall**: Philadelphia and Allegheny (Pittsburgh) counties generate 500,000+ Democratic votes, but face overwhelming Republican margins in rural PA
- **The 2024 result**: Trump won Pennsylvania 50.5% to 48.7%, reestablishing Republican presidential dominance

## 📊 Features

- **Interactive Mapbox visualization** showing county-level election results with color-coded competitiveness categories
- **Contest selector** to compare results across presidential, Senate, gubernatorial, and other statewide races
- **Statewide temperature bar** displaying aggregate margins and vote production
- **County profiles** providing historical context and demographic analysis
- **Completeness**: 2000-2024 data across all 67 Pennsylvania counties

### Political Categories

Results are categorized by margin of victory:

- **Annihilation** (40%+): Overwhelming one-party dominance
- **Dominant** (30-39.99%): Strong one-party state
- **Stronghold** (20-29.99%): Likely one-party
- **Safe** (10-19.99%): Probable one-party
- **Likely** (5.50-9.99%): Lean toward one party
- **Lean** (1-5.49%): Slight preference for one party
- **Tilt** (0.50-0.99%): Minimal margin
- **Tossup** (<0.50%): Essentially tied

## 📈 Key Findings

### Lackawanna County: Biden's Hometown Story
Joe Biden's childhood home in Scranton (Lackawanna County) exemplifies the working-class realignment:
- 2008: D+8.3% (Obama 54%, McCain 46%)
- 2016: R+9.5% (Trump 54%, Clinton 45%) — an 18-point swing
- 2020: R+8.2% (Trump 54%, Biden 46%) — Biden couldn't win his hometown
- 2024: D+2-3% (Harris barely recovers) — but too narrow to save Rep. Matt Cartwright in PA-8

### Philadelphia: Democratic Firewall
Philadelphia County (1.6M residents) is Democrats' most valuable asset:
- Delivers 400,000+ Democratic vote margins
- Voting 75-85% Democratic across expanding urban professional base
- Growing Democratic margins each cycle (D+33% in 2016 → D+40% in 2024)

### Philadelphia Suburbs: The Realignment
Once Republican strongholds, Montgomery, Delaware, Chester, and Bucks counties have become Democratic-leaning:
- 2000: Competitive/lean Republican
- 2016: Clinton flipped multiple suburban House seats
- 2020-2024: Maintain Democratic margins, offsetting rural Republican gains

### Allegheny County (Pittsburgh): Western PA Anchor
Pittsburgh's transition from Republican steel city to Democratic metro:
- Delivers 100,000-150,000 Democratic margins
- Combined with Philadelphia, provides ~500,000 Democratic firewall
- Tech/healthcare economy attracting college-educated Democratic voters

### Southwest PA Rural Counties: Republican Surge
Counties like Beaver, Greene, Fayette, Washington, and Cambria show massive Republican gains:
- Former union/coal strongholds now voting 60%+ Republican
- Environmental concerns over fracking/'green' energy policies
- Manufacturing decline eroding Democratic base

### Why Pennsylvania Remains the Swing State
Unlike Ohio (now Safe Republican), Pennsylvania stays competitive because:
- Growing/stable metropolitan areas (Philly suburbs, Pittsburgh tech corridor)
- Multiple mid-sized cities (Philadelphia, Pittsburgh, Harrisburg, Allentown)
- Increasing college-educated population in suburbs
- More diverse newcomer migration than Rust Belt decline states

## 🛠️ Technology Stack

- **Frontend**: Mapbox GL JS for interactive mapping
- **Data Processing**: Python (pandas) for election data aggregation
- **Data Sources**: 
  - [OpenElections PA dataset](https://github.com/openelections/openelections-data-pa) (2000-2024)
  - TIGER/Line county shapefiles (U.S. Census Bureau)
- **Visualization Framework**: HTML5, CSS3, vanilla JavaScript
- **Data Format**: GeoJSON for county boundaries, JSON for election results

## 📁 Project Structure

```
PARealignment/
├── index.html                          # Main interactive visualization
├── README.md                           # This file
├── data/
│   ├── pa_election_results.json       # Processed election data (2000-2024)
│   ├── pa_counties.geojson            # PA county boundaries (GeoJSON)
│   ├── tl_2020_42_county20.*          # TIGER/Line county shapefiles
│   └── openelections-data-pa/         # Source OpenElections data
│       ├── 2000-2024/                 # Annual election files
│       ├── parsers/                   # Data parsing utilities
│       └── utils.py                   # Shared utilities
└── scripts/
    ├── process_openelections.py       # Main data aggregation script
    ├── convert_shapefile_to_geojson.py # Shapefile converter
    └── convert_simple.py              # GeoJSON converter
```

## 🚀 Getting Started

### Prerequisites

- Modern web browser with JavaScript enabled (Chrome, Firefox, Safari, Edge)
- Mapbox API token (free at [mapbox.com](https://www.mapbox.com))
- Python 3.8+ (for data processing only, not required to view visualization)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/Tenjin25/PARealignmentMap.git
   cd PARealignmentMap
   ```

2. Set up Mapbox token:
   - Get a free token at [mapbox.com/account/tokens](https://mapbox.com/account/tokens)
   - Open `index.html` and update line ~1320:
     ```javascript
     mapboxToken: 'YOUR_MAPBOX_TOKEN_HERE'
     ```
   - Or set environment variable: `export MAPBOX_TOKEN=pk.eyJ...`

3. Start a local web server:
   ```bash
   # Python 3
   python -m http.server 8000
   
   # Or Node.js (http-server)
   npx http-server
   ```

4. Open browser and navigate to `http://localhost:8000`

### Data Processing (Optional)

To regenerate election data from OpenElections:

```bash
cd scripts
python process_openelections.py
```

This will:
- Process 2000-2024 OpenElections PA data
- Aggregate precinct-level data to county totals
- Generate `data/pa_election_results.json`
- Calculate competitiveness metrics

**Data Strategy:**
- 2000-2014: Uses county-level files directly (complete 67-county coverage)
- 2016-2024: Uses precinct files aggregated to county (ensures geographic completeness)

## 📊 Contests Included

- **Presidential**: 2000, 2004, 2008, 2012, 2016, 2020, 2024
- **U.S. Senate**: 2006, 2012, 2016, 2018, 2022, 2024
- **Governor**: 2010, 2014, 2018, 2022
- **Attorney General, Auditor General, State Treasurer**: Available years

All contests display:
- County-level vote totals by candidate
- Vote margins and vote share percentages
- Competitiveness categorization
- Statewide aggregates

## 🔍 How to Use the Visualization

1. **Select a Contest**: Use the dropdown menu to pick a race
2. **View County Results**: Click any county to see detailed results
3. **Color Interpretation**: County colors indicate political category (see categories above)
4. **Temperature Bar**: Shows statewide margin and vote concentration
5. **Accessibility**: Toggle color-blind mode or county labels using buttons

## 📚 Data Sources

### OpenElections Pennsylvania
- GitHub: [openelections/openelections-data-pa](https://github.com/openelections/openelections-data-pa)
- Format: CSV (county and precinct level)
- Years: Comprehensive coverage 2000-2024
- Standardized across election types and years

### Census Geography
- TIGER/Line county boundaries (2020 vintage)
- Source: U.S. Census Bureau
- Format: Shapefile (converted to GeoJSON)

### Election Administration
- County-level results from OpenElections aggregation
- Precinct results from local election boards

## 🎓 Educational Context

This project was developed as part of CPT-236 course work to explore:
- Geographic political polarization in swing states
- Data-driven analysis of electoral trends
- Interactive web visualization best practices
- Working with election data and geographic information systems

## 🔄 Data Processing Pipeline

1. **Extract**: Download raw OpenElections PA CSVs
2. **Transform**: 
   - Normalize office/candidate names
   - Aggregate precinct-level data to county where necessary
   - Convert votes to numeric values
   - Calculate vote margins and percentages
3. **Categorize**: Apply competitiveness classification
4. **Load**: Generate structured JSON for web visualization

## 🚀 Future Enhancements

- [ ] Add time-series animation showing 2000-2024 realignment
- [ ] Include precinct-level drilling for county deep dives
- [ ] Demographic overlay (education, income, population density)
- [ ] Congressional district mapping and results
- [ ] State legislature results (Senate and House)
- [ ] Judicial election results (partisan races)
- [ ] Export county profiles as PDF reports
- [ ] Comparison mode (side-by-side election analysis)

## 🤝 Contributing

This project welcomes contributions! Areas for improvement:

1. **Data**: Additional election cycles, judicial races, local results
2. **Visualization**: Mobile optimization, accessibility enhancements
3. **Analysis**: County profile narratives, demographic context
4. **Documentation**: Tutorials, methodology explanations

## 📄 License

This project uses publicly available election data from OpenElections and U.S. Census geographic data. See respective sources for licensing terms.

## 🙋 Questions & Contact

For questions about the project methodology, data sources, or visualization:
- Review the embedded documentation in `index.html`
- Check OpenElections project documentation
- Submit issues or discussions via GitHub

## 📖 Reading the Results

### What does a county's color mean?
- **Red counties**: Republican advantage (Safe to Annihilation)
- **Blue counties**: Democratic advantage (Safe to Annihilation)
- **Gray counties**: Tossup or minimal margin (<0.50%)

### What indicates a county has "flipped"?
- Compare colors across two elections
- Look for dramatic margin changes (e.g., blue → red)
- Check vote share percentages for shifts

### Key Interpretations

**Pennsylvania Paradox**: Democrats consistently win Senate and gubernatorial races by substantial margins, yet presidential races remain razor-close. This reflects:
- Strength of Democratic urban coalition in local/state races
- Vulnerability to Republican gains in presidential turnout
- Importance of candidate-specific factors (e.g., Shapiro 56%, Harris 48%)

**The Math**: Democrats need:
- Philadelphia 400,000+ Democratic margin
- Allegheny 100,000-150,000 Democratic margin
- Philadelphia suburbs 100,000+ Democratic margin
- **Plus:** wins in swing counties (Dauphin, Centre, Lehigh, Northampton, Erie)

Republicans need:
- Win or come close in swing counties
- Run up 60%+ margins in rural/exurban Pennsylvania (84 counties)
- Limit Democratic margins in urban areas

## 🎯 Key Takeaway

Pennsylvania's 2024 result (Trump 50.5%, Harris 48.7%, R+1.8%) proves the state remains America's most crucial swing state—19 electoral votes decided by narrow margins. The interactive map reveals how this competitiveness emerges from a deeply divided geography: Democratic urban strongholds facing overwhelming Republican rural dominance, with suburban counties determining every election.

---

**Created by Shamar Davis**  
**Last Updated: February 2026**

For the most current version and updates, visit the [GitHub repository](https://github.com/Tenjin25/PARealignmentMap).
