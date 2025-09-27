"""
Database Configuration and Connection Utilities

This module provides centralized database connections and common configurations
used across all modules in the Masterplan Tycoon Calculator project.
"""
import sqlite3
import os
from pathlib import Path

# Database configuration
DB_NAME = "masterplan_tycoon_clean.db"
DB_PATH = Path(__file__).parent / DB_NAME

def get_db_connection():
    """
    Get a connection to the main game database.
    
    Returns:
        sqlite3.Connection: Database connection object
    """
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Database not found at {DB_PATH}")
    
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row  # Enable column access by name
    return conn

def get_db_path():
    """
    Get the absolute path to the database file.
    
    Returns:
        Path: Path object pointing to the database
    """
    return DB_PATH

# Project configuration constants
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT.parent
ARCHIVE_DIR = PROJECT_ROOT.parent / "archive"
DOCS_DIR = PROJECT_ROOT.parent / "docs"
REFERENCES_DIR = PROJECT_ROOT.parent / "references"

# Module paths for cross-module imports
DATA_PROCESSING_DIR = PROJECT_ROOT / "data_processing"
DATA_EXPLORATION_DIR = PROJECT_ROOT / "data_exploration"
ANALYSIS_DIR = PROJECT_ROOT / "analysis"
VISUALIZATION_DIR = PROJECT_ROOT / "visualization"
GAME_CALCULATION_DIR = PROJECT_ROOT / "game_calculation"

def get_project_info():
    """
    Get basic project information and structure.
    
    Returns:
        dict: Dictionary containing project paths and configuration
    """
    return {
        "project_root": PROJECT_ROOT,
        "data_dir": DATA_DIR,
        "database_path": DB_PATH,
        "modules": {
            "data_processing": DATA_PROCESSING_DIR,
            "data_exploration": DATA_EXPLORATION_DIR,
            "analysis": ANALYSIS_DIR,
            "visualization": VISUALIZATION_DIR,
            "game_calculation": GAME_CALCULATION_DIR,
        }
    }