# Masterplan Tycoon Calculator - AI-Driven Supply Chain Optimization# Masterplan Tycoon Resource Chain Database & AI Optimization Challenge



**Author**: Patrick Snyder  **Author**: Patrick Snyder  

**Creation Date**: 11/6/2024**Creation Date**: 11/6/2024

**Last Updated**: September 26, 2025**Last Updated**: September 24, 2025



## Project Overview## Project Evolution



A comprehensive data science and mathematical optimization project that analyzes Masterplan Tycoon gameplay patterns and develops AI-driven strategies for optimal resource chain management.This project has evolved from a simple game stats dashboard into a comprehensive resource chain analysis system with an ambitious AI optimization challenge.



## 🚀 Quick Start### Phase 1: Game Stats Dashboard ✅ COMPLETE

Original Tkinter-based dashboard for displaying game statistics from save files.

```bash

# Navigate to the src directory### Phase 2: Database-Driven Resource Chain Analysis ✅ COMPLETE  

cd src/Complete transformation into a relational database system with normalized schema and full resource chain visualization.



# Explore the modular structure### Phase 3: AI Save File Optimization Challenge 🚧 IN PROGRESS

python module_demo.py**THE GRAND CHALLENGE**: Can AI reverse-engineer and optimize a complex tycoon game without ever playing it?



# Run analysis on your current gameplay## Current Project Structure

cd analysis/

python brute_force_analyzer.py```

python mission_analyzer.pysrc/

├── masterplan_tycoon_clean.db          # Normalized SQLite database

# Launch interactive dashboard├── resource_chain_explorer_fixed.py     # Resource chain analysis tool

cd ../visualization/├── streamlit_dashboard.py               # Database-driven web interface

streamlit run streamlit_dashboard.py├── save_file_parser.py                  # Save file JSON analysis

├── build_clean_database.py              # Database builder from cleaned CSVs

# Run dependency calculations└── inspect_database.py                  # Database inspection tool

cd ../game_calculation/

python dependency_analyzer.pyarchive/                                 # Archived development files

```references/                              # Cleaned CSV data & save file

```

## 📁 Modular Architecture

## Database Schema ✅ COMPLETE

The project is organized into specialized modules for maximum flexibility and maintainability:

**Core Tables:**

```- `maps` - Game locations (Master, Islands, Mountains)  

src/- `buildings` - All building types with generated unique IDs

├── data_processing/         # Data ingestion and database operations- `resources` - All resources by map

├── data_exploration/        # Interactive data discovery tools  - `recipes` - Production recipes by tier

├── analysis/               # Strategy analysis and pattern evaluation- `plans` - Mission plans

├── visualization/          # Dashboards and interactive charts

├── game_calculation/       # Core optimization algorithms**Relationship Tables:**

└── shared/                 # Common utilities and configuration- `building_inputs` - What each building consumes

```- `building_outputs` - What each building produces (with rates)

- `building_construction` - Construction requirements

See `src/README.md` for detailed module documentation.- `building_maintenance` - Maintenance costs

- `recipe_buildings` - Recipe-building associations

## 🎯 The AI Optimization Challenge

**Key Innovation**: Used building+map combinations as unique identifiers to solve data normalization challenges.

**Core Question**: Can AI optimize complex supply chain strategies without experiential knowledge?

## Resource Chain Capabilities ✅ COMPLETE

### Challenge Scope

- **Input**: Game save file (1,826 buildings, 48.2 hours of play)  The system can now:

- **Database**: Normalized schema with 130 resources, 219 production relationships- **Trace complete resource chains**: Find all producers and consumers of any resource

- **Goal**: Generate optimized strategies achieving same victory with ~60% fewer buildings- **Analyze building dependencies**: See inputs/outputs/construction/maintenance for any building

- **Calculate production rates**: Output per minute, production times

### Current Analysis Results- **Map resource flows**: Upstream and downstream dependencies

- **Overproduction Identified**: 480 water/min vs. 5 needed (960% waste)- **Cross-map analysis**: Resource chains spanning multiple game locations

- **Strategic Flaws**: Construction vs. production confusion, 1:1 ratio fallacy

- **Dependency Depth**: 5-level chains with 47 unique production elements**Example Working Chains:**

- **Mathematical Scope**: Requires Mixed Integer Programming, Network Flow Optimization- Coal: 4 producers (Coal Mine, Charcoal Kiln, Steam Coal Mine, Steel Mission) → 3 consumers

- Steel: 2 producers (Furnace needs Coal+Iron, Steel Mission) → 3 consumers

## 🧮 Mathematical Approaches- Furnace Analysis: Inputs Coal+Iron → Outputs 2 Steel every 30s (4.0/min)



The optimization challenge requires advanced mathematical modeling:## The AI Optimization Challenge 🎯



1. **Multi-level BOM Explosion** - Full dependency tree traversal### Challenge Parameters

2. **Mixed Integer Programming** - Optimal building count calculation  **Given**: 

3. **Critical Path Method** - Construction sequencing optimization- A completed game save file (JSON, 1,826 nodes, 3,394 links, 48.2 hours of play)

4. **Network Flow Analysis** - Resource routing optimization- Complete normalized database of all buildings, resources, and relationships

5. **Constraint Satisfaction** - Complex dependency resolution- Knowledge that storage buildings act as universal load balancers



## 📊 Key Findings**Goal**: 

Use AI reasoning to generate an optimized save file JSON that achieves the same victory conditions with better efficiency, without ever opening or playing the game.

### Strategic Pattern Analysis

- **Brute Force Indicators**: Massive overproduction (400-960% waste)### Current Analysis Status ✅ PHASE 1 COMPLETE

- **Resource Chain Complexity**: Up to 5 levels of dependencies  

- **Mission Requirements**: 12 final products, 146+ buildings minimum**Save File Parsing Results:**

- **Optimization Potential**: 500-700 buildings vs. current 1,826- **Total Nodes**: 1,826 buildings placed

- **Unique Building Types**: 207 discovered

### Database Insights- **Database Mapping**: 167/207 building types matched (80% success rate)

- **Production Graph**: NetworkX graph with 130 resources, 219 relationships- **Resource Flows**: 129 unique resources identified

- **Building Mapping**: 80% success rate matching save file to database- **Storage Buildings**: 318 total (heavy reliance on storage as load balancers)

- **Chain Analysis**: Complete upstream/downstream traceability- **Top Resources**: Coal (702), Water (690), Steel (651)



## 🔧 Technical Stack**Building Categories Identified:**

- **Production Buildings**: 177 types (lumbercamp, ironmine, furnace, etc.)

- **Database**: SQLite with normalized relational schema- **Storage Buildings**: 3 types, 318 total instances

- **Analysis**: Python, Pandas, NetworkX for graph analysis- **Mission Buildings**: 23 (completion objectives)

- **Optimization**: Scipy, NetworkX, custom algorithms  - **Transport**: 4 port buildings for inter-map shipping

- **Visualization**: Streamlit, Plotly for interactive dashboards

- **Modeling**: Mathematical optimization libraries## Current Status & Next Steps



## 📈 Development Phases### ✅ COMPLETED

1. **Database Architecture**: Fully normalized schema with all relationships

### ✅ Phase 1 Complete - Data Foundation2. **Resource Chain Analysis**: Complete traceability of production dependencies

- Normalized database schema from cleaned CSV data3. **Save File Parsing**: Successfully analyzed game structure and building placements

- Resource chain explorer and analysis tools  4. **Building Mapping**: 80% of save file buildings mapped to database entities

- Save file parser and pattern recognition

### 🚧 IN PROGRESS (CHECKPOINT)

### ✅ Phase 2 Complete - Strategic Analysis  **Phase 3A - Save File Integration**

- Brute force vs. strategic pattern quantification1. **Fix naming mismatches**: Map remaining 40 unmatched building types

- Mission requirement analysis and dependency mapping2. **Spatial analysis**: Understand current layout patterns and inefficiencies

- Strategic flaw identification and optimization framework3. **Resource flow modeling**: Build mathematical model of current production



### 🚧 Phase 3 Current - Mathematical Optimization### 📋 UPCOMING PHASES

- **Multi-level BOM explosion** for complete requirement calculation**Phase 3B - Optimization Algorithm**

- **Mixed Integer Programming** for optimal building counts1. **Constraint modeling**: Victory conditions, resource requirements, map limitations

- **Construction sequencing** and spatial optimization algorithms2. **Efficiency metrics**: Define what "better" means (fewer buildings? faster completion? better ratios?)

3. **AI optimization**: Genetic algorithm, simulated annealing, or other optimization approach

### 📋 Phase 4 Planned - Strategy Generation

- Generate optimized building templates and spatial layouts**Phase 3C - Save File Generation**

- Create construction roadmaps with phase-based building1. **Layout optimization**: Determine optimal building placements

- Export optimized strategies as actionable game plans2. **JSON generation**: Create new save file in proper format

3. **Validation**: Ensure generated save file is technically valid

## 🎮 Game Impact

## Tools & Technologies

This project addresses universal resource management challenges:

- **Supply Chain Optimization**: Applicable to logistics, manufacturing, economics- **Database**: SQLite with normalized relational schema

- **Constraint Satisfaction**: Project management, resource allocation- **Analysis**: Python, Pandas, NetworkX for graph analysis

- **Dependency Analysis**: Software architecture, infrastructure planning  - **Visualization**: Streamlit, Plotly for interactive dashboards

- **Strategic Planning**: Business optimization, operational research- **Optimization**: TBD (likely scikit-learn, scipy.optimize, or custom algorithms)

- **Data Sources**: Cleaned CSV exports + JSON save file

## 🏆 Success Criteria

## The Ultimate Test

**Victory Condition**: Generate a mathematically optimized strategy that achieves the same game objectives with significantly improved efficiency metrics.

This represents a unique AI challenge: **Can artificial intelligence become a master game optimizer based purely on data analysis, without experiential knowledge?** 

**Measurable Outcomes**:

- Reduce total building count from 1,826 to ~600-700It's like asking an AI to redesign a city's infrastructure having never lived in a city, using only:

- Eliminate 400-960% resource overproduction waste  - Economic data about buildings and resources

- Optimize construction sequencing for faster completion- A map of someone else's working (but inefficient) city

- Provide reusable templates for different game scenarios- Knowledge of optimization principles



---**Success Criteria**: Generate a theoretically superior save file that could achieve victory more efficiently than the original 48.2-hour human playthrough.



**The Ultimate AI Challenge**: Master complex supply chain optimization through pure mathematical reasoning and data analysis, without experiential gameplay knowledge.---

*This project demonstrates the power of data normalization, resource chain analysis, and AI optimization applied to complex simulation games.*
