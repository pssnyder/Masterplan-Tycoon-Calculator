#!/usr/bin/env python3
"""
Masterplan Tycoon Database Builder

This script creates and populates a SQLite database with all the game data
from CSV files and JSON save data. It implements the relational schema
designed for efficient analysis and web interface validation.
"""

import sqlite3
import pandas as pd
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

class MasterplanDatabaseBuilder:
    def __init__(self, database_path="masterplan_tycoon.db", data_directory="."):
        self.database_path = database_path
        self.data_directory = Path(data_directory)
        self.conn: Optional[sqlite3.Connection] = None
        
    def connect(self):
        """Connect to SQLite database"""
        self.conn = sqlite3.connect(self.database_path)
        self.conn.execute("PRAGMA foreign_keys = ON")  # Enable foreign key constraints
        
    def disconnect(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            
    def execute_schema(self, schema_file="database_schema.sql"):
        """Execute the database schema SQL file"""
        if not self.conn:
            raise RuntimeError("Database connection not established")
            
        schema_path = self.data_directory / schema_file
        with open(schema_path, 'r') as f:
            schema_sql = f.read()
        
        # Split by semicolons and execute each statement
        statements = [stmt.strip() for stmt in schema_sql.split(';') if stmt.strip()]
        for statement in statements:
            try:
                self.conn.execute(statement)
            except sqlite3.Error as e:
                print(f"Warning: Could not execute statement: {e}")
                print(f"Statement: {statement[:100]}...")
        
        self.conn.commit()
        print("Database schema created successfully")
        
    def populate_reference_data(self):
        """Populate lookup tables with reference data"""
        if not self.conn:
            raise RuntimeError("Database connection not established")
            
        cursor = self.conn.cursor()
        
        # Plans (regions)
        plans = [
            ('Master', 'Main continental region with advanced industrial buildings'),
            ('Islands', 'Tropical islands with specialized agricultural and luxury goods'),  
            ('Mountains', 'Mountain region with mining and heavy industry')
        ]
        
        for plan in plans:
            cursor.execute("INSERT OR IGNORE INTO plans (name, description) VALUES (?, ?)", plan)
            
        # Resource categories - we'll discover these from the data
        categories = set()
        
        # Building categories - we'll discover these from the CSV data
        building_categories = set()
        
        self.conn.commit()
        print("Reference data populated")
        
    def load_csv_data(self):
        """Load all CSV data into the database"""
        if not self.conn:
            raise RuntimeError("Database connection not established")
        
        # Load the main game data CSV
        game_data_path = self.data_directory / "Masterplan Tycoon Building Calculations - game_data.csv"
        if not game_data_path.exists():
            print(f"Warning: {game_data_path} not found")
            return
            
        df = pd.read_csv(game_data_path)
        print(f"Loaded {len(df)} rows from game_data.csv")
        
        # Get plan IDs
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, name FROM plans")
        plan_map = {name: id for id, name in cursor.fetchall()}
        
        # Process unique resources first
        resources = set()
        building_categories = set()
        
        for _, row in df.iterrows():
            # Extract resource name (remove asterisks)
            resource_name = str(row['Resource']).replace('*', '').strip()
            if resource_name and resource_name != 'None':
                resources.add(resource_name)
            
            # Extract building category
            if pd.notna(row['Category']):
                building_categories.add(str(row['Category']).strip())
        
        # Insert building categories
        for category in building_categories:
            cursor.execute("INSERT OR IGNORE INTO building_categories (name) VALUES (?)", (category,))
        
        # Insert resources (we'll categorize them later)
        for resource in resources:
            cursor.execute("INSERT OR IGNORE INTO resources (name) VALUES (?)", (resource,))
        
        self.conn.commit()
        
        # Get resource and category mappings
        cursor.execute("SELECT id, name FROM resources")
        resource_map = {name: id for id, name in cursor.fetchall()}
        
        cursor.execute("SELECT id, name FROM building_categories") 
        category_map = {name: id for id, name in cursor.fetchall()}
        
        # Process buildings and their relationships
        buildings_processed = set()
        
        for _, row in df.iterrows():
            building_id = str(row['buid']).strip()
            building_name = str(row['Building']).strip()
            plan_name = str(row['Plan']).strip()
            tier = int(row['Tier']) if pd.notna(row['Tier']) and str(row['Tier']).isdigit() else 0
            category = str(row['Category']).strip() if pd.notna(row['Category']) else None
            production_time = int(row['Production Time']) if pd.notna(row['Production Time']) and str(row['Production Time']).isdigit() else None
            
            # Insert building if not already processed
            building_key = (building_id, building_name, plan_name)
            if building_key not in buildings_processed:
                plan_id = plan_map.get(plan_name)
                category_id = category_map.get(category) if category else None
                
                cursor.execute("""
                    INSERT OR IGNORE INTO buildings 
                    (building_id, name, plan_id, tier, category_id, production_time)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (building_id, building_name, plan_id, tier, category_id, production_time))
                
                buildings_processed.add(building_key)
        
        self.conn.commit()
        
        # Get building mappings
        cursor.execute("SELECT id, building_id, name FROM buildings")
        building_map = {(bid, name): id for id, bid, name in cursor.fetchall()}
        
        # Process resource relationships
        for _, row in df.iterrows():
            building_id = str(row['buid']).strip()
            building_name = str(row['Building']).strip()
            resource_type = str(row['Resource Type']).strip()
            resource_name = str(row['Resource']).replace('*', '').strip()
            quantity = int(row['Resource Quantity']) if pd.notna(row['Resource Quantity']) and str(row['Resource Quantity']).isdigit() else 0
            dependency = str(row['Resource Dependency']).replace('*', '').strip() if pd.notna(row['Resource Dependency']) and str(row['Resource Dependency']) != 'N/A' else None
            
            if resource_name == 'None' or quantity == 0:
                continue
                
            # Get building ID
            building_db_id = building_map.get((building_id, building_name))
            if not building_db_id:
                continue
                
            # Get resource ID
            resource_id = resource_map.get(resource_name)
            if not resource_id:
                continue
                
            # Find dependency building ID if specified
            dependency_building_id = None
            if dependency and dependency != 'None':
                # Try to find the dependency building
                for (bid, bname), db_id in building_map.items():
                    if dependency in bname:
                        dependency_building_id = db_id
                        break
            
            # Insert into appropriate table based on resource type
            try:
                if resource_type == 'Output Resource':
                    prod_time = int(row['Production Time']) if pd.notna(row['Production Time']) and str(row['Production Time']).isdigit() else None
                    cursor.execute("""
                        INSERT OR IGNORE INTO building_outputs 
                        (building_id, resource_id, quantity, production_time)
                        VALUES (?, ?, ?, ?)
                    """, (building_db_id, resource_id, quantity, prod_time))
                    
                elif resource_type == 'Input Resource':
                    cursor.execute("""
                        INSERT OR IGNORE INTO building_inputs 
                        (building_id, resource_id, quantity, dependency_building_id)
                        VALUES (?, ?, ?, ?)
                    """, (building_db_id, resource_id, quantity, dependency_building_id))
                    
                elif resource_type == 'Build Resource':
                    cursor.execute("""
                        INSERT OR IGNORE INTO building_construction 
                        (building_id, resource_id, quantity, dependency_building_id)
                        VALUES (?, ?, ?, ?)
                    """, (building_db_id, resource_id, quantity, dependency_building_id))
                    
                elif resource_type == 'Maintenance Resource':
                    cursor.execute("""
                        INSERT OR IGNORE INTO building_maintenance 
                        (building_id, resource_id, quantity, dependency_building_id)
                        VALUES (?, ?, ?, ?)
                    """, (building_db_id, resource_id, quantity, dependency_building_id))
                    
            except sqlite3.Error as e:
                print(f"Error inserting {resource_type} for {building_name}: {e}")
        
        self.conn.commit()
        print(f"Processed {len(buildings_processed)} unique buildings")
        
    def load_json_save_data(self):
        """Load game save data from JSON file"""
        if not self.conn:
            raise RuntimeError("Database connection not established")
            
        json_path = self.data_directory / "game_data_save0.json"
        if not json_path.exists():
            print(f"Warning: {json_path} not found")
            return
            
        with open(json_path, 'r') as f:
            save_data = json.load(f)
            
        cursor = self.conn.cursor()
        
        # Extract player statistics
        player_data = save_data.get('player', {})
        cursor.execute("""
            INSERT OR REPLACE INTO player_stats 
            (save_name, save_date, total_population, total_money, prestige_points)
            VALUES (?, ?, ?, ?, ?)
        """, (
            save_data.get('saveName', 'Unknown'),
            datetime.now().isoformat(),
            player_data.get('population', 0),
            player_data.get('money', 0),
            player_data.get('prestige', 0)
        ))
        
        # Extract mission data
        missions = save_data.get('missions', {})
        for mission_id, mission_data in missions.items():
            cursor.execute("""
                INSERT OR IGNORE INTO missions 
                (mission_id, name, description, is_completed)
                VALUES (?, ?, ?, ?)
            """, (
                mission_id,
                mission_data.get('name', ''),
                mission_data.get('description', ''),
                mission_data.get('completed', False)
            ))
        
        # Extract storage data
        storage_data = save_data.get('storage', {})
        for facility_name, facility_data in storage_data.items():
            # Insert storage facility
            cursor.execute("""
                INSERT OR IGNORE INTO storage_facilities 
                (facility_id, name, capacity_limit)
                VALUES (?, ?, ?)
            """, (facility_name, facility_name, facility_data.get('capacity', 0)))
            
            # Get facility ID
            cursor.execute("SELECT id FROM storage_facilities WHERE facility_id = ?", (facility_name,))
            facility_id = cursor.fetchone()[0]
            
            # Insert stored resources
            resources = facility_data.get('resources', {})
            for resource_name, quantity in resources.items():
                cursor.execute("SELECT id FROM resources WHERE name = ?", (resource_name,))
                resource_result = cursor.fetchone()
                if resource_result:
                    resource_id = resource_result[0]
                    cursor.execute("""
                        INSERT OR REPLACE INTO current_storage 
                        (facility_id, resource_id, quantity, last_updated)
                        VALUES (?, ?, ?, ?)
                    """, (facility_id, resource_id, quantity, datetime.now().isoformat()))
        
        self.conn.commit()
        print("JSON save data loaded successfully")
        
    def create_database(self):
        """Complete database creation process"""
        try:
            print("Creating Masterplan Tycoon database...")
            
            # Remove existing database if it exists
            if os.path.exists(self.database_path):
                try:
                    os.remove(self.database_path)
                    print(f"Removed existing database: {self.database_path}")
                except PermissionError:
                    print(f"Warning: Could not remove existing database {self.database_path}")
                    print("Will try to create a new one with timestamp...")
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    self.database_path = f"masterplan_tycoon_{timestamp}.db"
            
            self.connect()
            
            # Create schema
            self.execute_schema()
            
            # Populate data
            self.populate_reference_data()
            self.load_csv_data()
            self.load_json_save_data()
            
            # Print summary statistics
            self.print_database_stats()
            
            print(f"\nDatabase created successfully: {self.database_path}")
            print("Ready for web interface and analysis!")
            
        except Exception as e:
            print(f"Error creating database: {e}")
            raise
        finally:
            self.disconnect()
            
    def print_database_stats(self):
        """Print summary statistics about the database"""
        if not self.conn:
            raise RuntimeError("Database connection not established")
            
        cursor = self.conn.cursor()
        
        print("\n" + "="*50)
        print("DATABASE SUMMARY")
        print("="*50)
        
        # Count records in each main table
        tables = [
            ('plans', 'Plans/Regions'),
            ('resources', 'Resources'),
            ('resource_categories', 'Resource Categories'),
            ('buildings', 'Buildings'),
            ('building_categories', 'Building Categories'),
            ('building_inputs', 'Building Inputs'),
            ('building_outputs', 'Building Outputs'),
            ('building_construction', 'Construction Requirements'),
            ('building_maintenance', 'Maintenance Requirements'),
            ('storage_facilities', 'Storage Facilities'),
            ('current_storage', 'Current Storage Records'),
            ('missions', 'Missions')
        ]
        
        for table, description in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"{description:.<30} {count:>6}")
            except sqlite3.Error:
                print(f"{description:.<30} {'ERROR':>6}")
        
        print("="*50)
        
        # Show sample building data
        print("\nSAMPLE BUILDING DATA:")
        cursor.execute("""
            SELECT b.name, p.name as plan, b.tier, bc.name as category
            FROM buildings b
            LEFT JOIN plans p ON b.plan_id = p.id  
            LEFT JOIN building_categories bc ON b.category_id = bc.id
            LIMIT 5
        """)
        
        for row in cursor.fetchall():
            print(f"  - {row[0]} ({row[1]}, Tier {row[2]}, {row[3]})")

def main():
    """Main execution function"""
    builder = MasterplanDatabaseBuilder()
    builder.create_database()

if __name__ == "__main__":
    main()