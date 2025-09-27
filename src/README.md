# Masterplan Tycoon Calculator - Module Structure

This document outlines the reorganized module structure for the Masterplan Tycoon Calculator project.

## 📁 Project Structure

```
src/
├── data_processing/         # Raw data ingestion and database operations
│   ├── __init__.py
│   ├── build_clean_database.py      # Build normalized SQLite database from CSVs
│   ├── add_relationship_tables.py   # Add relational tables to database
│   └── save_file_parser.py          # Parse game save files
│
├── data_exploration/        # Interactive data discovery and exploration
│   ├── __init__.py
│   ├── database_browser.py          # Browse database schema and contents
│   ├── inspect_database.py          # Detailed database inspection utilities
│   └── resource_chain_explorer_fixed.py  # Interactive resource chain exploration
│
├── analysis/               # Strategy analysis and gameplay evaluation
│   ├── __init__.py
│   ├── brute_force_analyzer.py      # Analyze brute force vs strategic patterns
│   ├── mission_analyzer.py          # Parse and analyze mission requirements
│   └── game_detective.py            # General gameplay pattern detection
│
├── visualization/          # Dashboards and interactive visualizations
│   ├── __init__.py
│   └── streamlit_dashboard.py       # Main Streamlit dashboard
│
├── game_calculation/       # Core optimization algorithms and mathematical models
│   ├── __init__.py
│   └── dependency_analyzer.py       # Resource dependency tree analysis
│
└── shared/                 # Common utilities and configuration
    ├── __init__.py
    ├── config.py                    # Database connections and project configuration
    ├── masterplan_tycoon_clean.db   # Main SQLite database
    ├── REVISED_SCHEMA_OUTLINE.md    # Database schema documentation
    └── STRATEGY_ANALYSIS.md         # Strategic analysis documentation
```

## 🎯 Module Purposes

### `data_processing/`
**Purpose**: Raw data ingestion, cleaning, and database operations
- Processes CSV files from the game into normalized database
- Handles save file parsing and data extraction
- Manages database schema and relationships

**Key Files**:
- `build_clean_database.py`: Main database builder from CSV files
- `save_file_parser.py`: Extracts data from game save files
- `add_relationship_tables.py`: Adds relational integrity to database

### `data_exploration/`
**Purpose**: Interactive data discovery and understanding
- Provides tools for exploring the cleaned game data
- Enables interactive browsing of resource relationships
- Supports data discovery and pattern identification

**Key Files**:
- `resource_chain_explorer_fixed.py`: Interactive resource chain explorer
- `database_browser.py`: Browse database contents
- `inspect_database.py`: Detailed database inspection

### `analysis/`
**Purpose**: Strategic analysis and gameplay pattern evaluation
- Analyzes actual gameplay patterns and strategies
- Compares brute force vs. strategic approaches
- Evaluates efficiency and identifies optimization opportunities

**Key Files**:
- `brute_force_analyzer.py`: Quantifies overproduction and brute force patterns
- `mission_analyzer.py`: Analyzes mission requirements and completion strategies
- `game_detective.py`: General gameplay pattern detection

### `visualization/`
**Purpose**: Dashboards and interactive data presentation
- Provides web-based dashboards for data visualization
- Creates interactive charts and exploration interfaces
- Presents analysis results in user-friendly formats

**Key Files**:
- `streamlit_dashboard.py`: Main interactive dashboard

### `game_calculation/`
**Purpose**: Core optimization algorithms and mathematical models
- Implements supply chain optimization algorithms
- Provides dependency analysis and calculation engines
- Contains the mathematical core for strategy optimization

**Key Files**:
- `dependency_analyzer.py`: Resource dependency tree analysis and optimization

### `shared/`
**Purpose**: Common utilities, configuration, and shared resources
- Provides database connections and configuration
- Contains shared documentation and data
- Offers common utilities used across modules

**Key Files**:
- `config.py`: Database connections and project configuration
- `masterplan_tycoon_clean.db`: Main SQLite database
- Documentation and analysis files

## 🔗 Module Dependencies

```
data_processing/     → shared/ (database config)
data_exploration/    → shared/ (database config)
analysis/           → shared/ (database config)
                    → data_processing/ (save file parsing)
visualization/      → shared/ (database config)
                    → data_exploration/ (resource chains)
game_calculation/   → shared/ (database config)
                    → analysis/ (mission requirements)
```

## 🚀 Getting Started

### Running Individual Modules

```bash
# Data Processing
cd src/data_processing
python build_clean_database.py

# Data Exploration
cd src/data_exploration
python resource_chain_explorer_fixed.py

# Analysis
cd src/analysis
python brute_force_analyzer.py
python mission_analyzer.py

# Visualization
cd src/visualization
streamlit run streamlit_dashboard.py

# Game Calculation
cd src/game_calculation
python dependency_analyzer.py
```

### Module Imports

```python
# Import shared configuration
from shared.config import get_db_connection, get_project_info

# Cross-module imports
from analysis.mission_analyzer import parse_mission_requirements
from game_calculation.dependency_analyzer import build_dependency_graph
```

## 📊 Data Flow

1. **Raw Data** → `data_processing/` → **Cleaned Database**
2. **Cleaned Database** → `data_exploration/` → **Resource Understanding**
3. **Game Save + Database** → `analysis/` → **Strategy Analysis**
4. **Analysis Results** → `visualization/` → **Interactive Dashboards**
5. **All Data** → `game_calculation/` → **Optimized Strategies**

## 🎯 Next Development Steps

1. **Enhanced Game Calculation**: Add Mixed Integer Programming optimization
2. **Spatial Analysis**: Add building placement and layout optimization
3. **Temporal Planning**: Add construction sequencing optimization
4. **Advanced Visualization**: Add network diagrams and flow visualizations
5. **API Development**: Create REST API for external tool integration

## 🔧 Configuration

All modules use the shared configuration in `shared/config.py` for:
- Database connections
- Project paths
- Cross-module imports
- Common utilities

This ensures consistent behavior across all modules while maintaining clear separation of concerns.