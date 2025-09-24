# Masterplan Tycoon Resource Chain Database & AI Optimization Challenge

**Author**: Patrick Snyder  
**Creation Date**: 11/6/2024
**Last Updated**: September 24, 2025

## Project Evolution

This project has evolved from a simple game stats dashboard into a comprehensive resource chain analysis system with an ambitious AI optimization challenge.

### Phase 1: Game Stats Dashboard ✅ COMPLETE
Original Tkinter-based dashboard for displaying game statistics from save files.

### Phase 2: Database-Driven Resource Chain Analysis ✅ COMPLETE  
Complete transformation into a relational database system with normalized schema and full resource chain visualization.

### Phase 3: AI Save File Optimization Challenge 🚧 IN PROGRESS
**THE GRAND CHALLENGE**: Can AI reverse-engineer and optimize a complex tycoon game without ever playing it?

## Current Project Structure

```
src/
├── masterplan_tycoon_clean.db          # Normalized SQLite database
├── resource_chain_explorer_fixed.py     # Resource chain analysis tool
├── streamlit_dashboard.py               # Database-driven web interface
├── save_file_parser.py                  # Save file JSON analysis
├── build_clean_database.py              # Database builder from cleaned CSVs
└── inspect_database.py                  # Database inspection tool

archive/                                 # Archived development files
references/                              # Cleaned CSV data & save file
```

## Database Schema ✅ COMPLETE

**Core Tables:**
- `maps` - Game locations (Master, Islands, Mountains)  
- `buildings` - All building types with generated unique IDs
- `resources` - All resources by map
- `recipes` - Production recipes by tier
- `plans` - Mission plans

**Relationship Tables:**
- `building_inputs` - What each building consumes
- `building_outputs` - What each building produces (with rates)
- `building_construction` - Construction requirements
- `building_maintenance` - Maintenance costs
- `recipe_buildings` - Recipe-building associations

**Key Innovation**: Used building+map combinations as unique identifiers to solve data normalization challenges.

## Resource Chain Capabilities ✅ COMPLETE

The system can now:
- **Trace complete resource chains**: Find all producers and consumers of any resource
- **Analyze building dependencies**: See inputs/outputs/construction/maintenance for any building
- **Calculate production rates**: Output per minute, production times
- **Map resource flows**: Upstream and downstream dependencies
- **Cross-map analysis**: Resource chains spanning multiple game locations

**Example Working Chains:**
- Coal: 4 producers (Coal Mine, Charcoal Kiln, Steam Coal Mine, Steel Mission) → 3 consumers
- Steel: 2 producers (Furnace needs Coal+Iron, Steel Mission) → 3 consumers
- Furnace Analysis: Inputs Coal+Iron → Outputs 2 Steel every 30s (4.0/min)

## The AI Optimization Challenge 🎯

### Challenge Parameters
**Given**: 
- A completed game save file (JSON, 1,826 nodes, 3,394 links, 48.2 hours of play)
- Complete normalized database of all buildings, resources, and relationships
- Knowledge that storage buildings act as universal load balancers

**Goal**: 
Use AI reasoning to generate an optimized save file JSON that achieves the same victory conditions with better efficiency, without ever opening or playing the game.

### Current Analysis Status ✅ PHASE 1 COMPLETE

**Save File Parsing Results:**
- **Total Nodes**: 1,826 buildings placed
- **Unique Building Types**: 207 discovered
- **Database Mapping**: 167/207 building types matched (80% success rate)
- **Resource Flows**: 129 unique resources identified
- **Storage Buildings**: 318 total (heavy reliance on storage as load balancers)
- **Top Resources**: Coal (702), Water (690), Steel (651)

**Building Categories Identified:**
- **Production Buildings**: 177 types (lumbercamp, ironmine, furnace, etc.)
- **Storage Buildings**: 3 types, 318 total instances
- **Mission Buildings**: 23 (completion objectives)
- **Transport**: 4 port buildings for inter-map shipping

## Current Status & Next Steps

### ✅ COMPLETED
1. **Database Architecture**: Fully normalized schema with all relationships
2. **Resource Chain Analysis**: Complete traceability of production dependencies
3. **Save File Parsing**: Successfully analyzed game structure and building placements
4. **Building Mapping**: 80% of save file buildings mapped to database entities

### 🚧 IN PROGRESS (CHECKPOINT)
**Phase 3A - Save File Integration**
1. **Fix naming mismatches**: Map remaining 40 unmatched building types
2. **Spatial analysis**: Understand current layout patterns and inefficiencies
3. **Resource flow modeling**: Build mathematical model of current production

### 📋 UPCOMING PHASES
**Phase 3B - Optimization Algorithm**
1. **Constraint modeling**: Victory conditions, resource requirements, map limitations
2. **Efficiency metrics**: Define what "better" means (fewer buildings? faster completion? better ratios?)
3. **AI optimization**: Genetic algorithm, simulated annealing, or other optimization approach

**Phase 3C - Save File Generation**
1. **Layout optimization**: Determine optimal building placements
2. **JSON generation**: Create new save file in proper format
3. **Validation**: Ensure generated save file is technically valid

## Tools & Technologies

- **Database**: SQLite with normalized relational schema
- **Analysis**: Python, Pandas, NetworkX for graph analysis
- **Visualization**: Streamlit, Plotly for interactive dashboards
- **Optimization**: TBD (likely scikit-learn, scipy.optimize, or custom algorithms)
- **Data Sources**: Cleaned CSV exports + JSON save file

## The Ultimate Test

This represents a unique AI challenge: **Can artificial intelligence become a master game optimizer based purely on data analysis, without experiential knowledge?** 

It's like asking an AI to redesign a city's infrastructure having never lived in a city, using only:
- Economic data about buildings and resources
- A map of someone else's working (but inefficient) city
- Knowledge of optimization principles

**Success Criteria**: Generate a theoretically superior save file that could achieve victory more efficiently than the original 48.2-hour human playthrough.

---

*This project demonstrates the power of data normalization, resource chain analysis, and AI optimization applied to complex simulation games.*
