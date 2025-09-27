#!/usr/bin/env python3
"""
Masterplan Tycoon Database Builder - Clean SoT Data Version
Build database from cleaned Source of Truth CSV files
"""

import sqlite3
import pandas as pd
import json
from pathlib import Path

def create_clean_database():
    """Create the database with clean SoT schema"""
    conn = sqlite3.connect('masterplan_tycoon_clean.db')
    
    # Drop existing tables if they exist
    drop_tables = [
        'building_maintenance', 'building_construction', 'building_outputs', 
        'building_inputs', 'recipe_buildings', 'resources', 'buildings', 
        'recipes', 'plans', 'maps'
    ]
    
    for table in drop_tables:
        conn.execute(f'DROP TABLE IF EXISTS {table}')
    
    conn.commit()
    return conn

def load_sot_data():
    """Load all Source of Truth CSV files"""
    try:
        data = {}
        sot_files = [
            'maps', 'plans', 'recipes', 'buildings', 'resources', 
            'inputs', 'outputs', 'construction', 'maintenance'
        ]
        
        for file in sot_files:
            file_path = f'../references/Masterplan Tycoon Data SoT - {file}.csv'
            data[file] = pd.read_csv(file_path)
            print(f"📁 Loaded {file}.csv: {len(data[file])} records")
        
        return data
    except Exception as e:
        print(f"❌ Error loading SoT files: {e}")
        return None

def create_maps_table(conn, maps_df):
    """Create and populate maps table"""
    print("🗺️ Creating Maps table...")
    
    conn.execute('''
    CREATE TABLE maps (
        id INTEGER PRIMARY KEY,
        name TEXT UNIQUE NOT NULL
    )
    ''')
    
    maps_data = []
    for i, row in enumerate(maps_df.itertuples(), 1):
        maps_data.append((i, row.map_name))
    
    conn.executemany('INSERT INTO maps (id, name) VALUES (?, ?)', maps_data)
    conn.commit()
    
    print(f"✅ Inserted {len(maps_data)} maps")
    return maps_data

def create_plans_table(conn, plans_df, maps_df):
    """Create and populate plans table"""
    print("📋 Creating Plans table...")
    
    conn.execute('''
    CREATE TABLE plans (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        map_id INTEGER,
        FOREIGN KEY (map_id) REFERENCES maps(id)
    )
    ''')
    
    # Create map name to ID lookup
    map_name_to_id = {row.map_name: i+1 for i, row in enumerate(maps_df.itertuples())}
    
    plans_data = []
    for i, row in enumerate(plans_df.itertuples(), 1):
        map_id = map_name_to_id.get(row.map_name)
        plans_data.append((i, row.plan_name, map_id))
    
    conn.executemany('INSERT INTO plans (id, name, map_id) VALUES (?, ?, ?)', plans_data)
    conn.commit()
    
    print(f"✅ Inserted {len(plans_data)} plans")
    return plans_data

def create_recipes_table(conn, recipes_df):
    """Create and populate recipes table"""
    print("🍳 Creating Recipes table...")
    
    conn.execute('''
    CREATE TABLE recipes (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        tier INTEGER NOT NULL,
        description TEXT
    )
    ''')
    
    # Get unique recipes with their tiers
    unique_recipes = recipes_df.groupby('recipe_name')['tier'].first().reset_index()
    
    recipes_data = []
    for i, row in enumerate(unique_recipes.itertuples(), 1):
        recipe_name = row.recipe_name
        tier = row.tier
        description = f"Recipe for {recipe_name} production (Tier {tier})"
        recipes_data.append((i, recipe_name, tier, description))
    
    conn.executemany('INSERT INTO recipes (id, name, tier, description) VALUES (?, ?, ?, ?)', recipes_data)
    conn.commit()
    
    print(f"✅ Inserted {len(recipes_data)} recipes")
    return recipes_data

def generate_building_id(building_name, map_name, recipe_name, tier):
    """Generate unique building ID: MAP#-TIER#-RECIPE_ABBR-BUILDING_ABBR"""
    
    # Map names to numbers
    map_numbers = {'Master': '1', 'Islands': '2', 'Mountains': '3', 'Other': '4'}
    map_abbr = {'Master': 'M', 'Islands': 'I', 'Mountains': 'M', 'Other': 'O'}
    
    # Recipe abbreviation (first letter of each word, max 3 chars)
    recipe_words = recipe_name.replace('-', ' ').replace('&', '').split()
    recipe_abbr = ''.join(word[0].upper() for word in recipe_words if word)[:3]
    
    # Building abbreviation (first letter of each word, max 4 chars) 
    building_words = building_name.replace('-', ' ').replace('&', '').split()
    building_abbr = ''.join(word[0].upper() for word in building_words if word)[:4]
    
    # Format: MAP#-TIER#-RECIPE_ABBR-BUILDING_ABBR+MAP_ABBR
    map_num = map_numbers.get(map_name, '4')
    map_suffix = map_abbr.get(map_name, 'O')
    
    building_id = f"{map_num}-{tier:02d}-{recipe_abbr}-{building_abbr}{map_suffix}"
    
    return building_id

def create_buildings_table(conn, buildings_df, recipes_df, maps_df):
    """Create and populate buildings table"""
    print("🏢 Creating Buildings table...")
    
    conn.execute('''
    CREATE TABLE buildings (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        map_id INTEGER,
        building_id TEXT UNIQUE NOT NULL,
        FOREIGN KEY (map_id) REFERENCES maps(id),
        UNIQUE(name, map_id)
    )
    ''')
    
    # Create lookup dictionaries
    map_name_to_id = {row.map_name: i+1 for i, row in enumerate(maps_df.itertuples())}
    
    # Create building to recipe mapping from recipes_df
    building_recipe_map = {}
    for _, row in recipes_df.iterrows():
        key = (row.building_name, row.map_name)
        building_recipe_map[key] = (row.recipe_name, row.tier)
    
    buildings_data = []
    used_building_ids = set()
    
    for i, row in enumerate(buildings_df.itertuples(), 1):
        building_name = row.building_name
        map_name = row.map_name
        map_id = map_name_to_id.get(map_name)
        
        # Get recipe info for this building
        recipe_info = building_recipe_map.get((building_name, map_name))
        if recipe_info:
            recipe_name, tier = recipe_info
            
            # Generate building ID
            base_building_id = generate_building_id(building_name, map_name, recipe_name, tier)
            building_id = base_building_id
            
            # Handle duplicates
            counter = 1
            while building_id in used_building_ids:
                building_id = f"{base_building_id}-{counter}"
                counter += 1
            
            used_building_ids.add(building_id)
            
            buildings_data.append((i, building_name, map_id, building_id))
    
    conn.executemany('INSERT INTO buildings (id, name, map_id, building_id) VALUES (?, ?, ?, ?)', buildings_data)
    conn.commit()
    
    print(f"✅ Inserted {len(buildings_data)} buildings")
    print("📋 Sample building IDs:")
    for data in buildings_data[:5]:
        print(f"   • {data[3]} - {data[1]}")
    
    return buildings_data

def create_resources_table(conn, resources_df, maps_df):
    """Create and populate resources table"""
    print("📦 Creating Resources table...")
    
    conn.execute('''
    CREATE TABLE resources (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        map_id INTEGER,
        is_consumable BOOLEAN DEFAULT TRUE,
        FOREIGN KEY (map_id) REFERENCES maps(id),
        UNIQUE(name, map_id)
    )
    ''')
    
    # Create map name to ID lookup
    map_name_to_id = {row.map_name: i+1 for i, row in enumerate(maps_df.itertuples())}
    
    # Filter out null/empty resource names
    clean_resources_df = resources_df.dropna(subset=['resource_name'])
    clean_resources_df = clean_resources_df[clean_resources_df['resource_name'].str.strip() != '']
    
    print(f"⚠️ Filtered out {len(resources_df) - len(clean_resources_df)} null/empty resource names")
    
    resources_data = []
    for i, row in enumerate(clean_resources_df.itertuples(), 1):
        resource_name = row.resource_name
        map_name = row.map_name
        map_id = map_name_to_id.get(map_name)
        
        resources_data.append((i, resource_name, map_id, True))
    
    conn.executemany('INSERT INTO resources (id, name, map_id, is_consumable) VALUES (?, ?, ?, ?)', resources_data)
    conn.commit()
    
    print(f"✅ Inserted {len(resources_data)} resources")
    return resources_data

def create_recipe_buildings_table(conn, recipes_df, recipes_data, buildings_data):
    """Create and populate recipe_buildings relationship table"""
    print("🔗 Creating Recipe-Buildings relationships...")
    
    conn.execute('''
    CREATE TABLE recipe_buildings (
        recipe_id INTEGER,
        building_id INTEGER,
        FOREIGN KEY (recipe_id) REFERENCES recipes(id),
        FOREIGN KEY (building_id) REFERENCES buildings(id),
        PRIMARY KEY (recipe_id, building_id)
    )
    ''')
    
    # Create lookup dictionaries
    recipe_name_to_id = {recipe[1]: recipe[0] for recipe in recipes_data}  # name: id
    building_key_to_id = {(building[1], building[2]): building[0] for building in buildings_data}  # (name, map_id): id
    
    # Create map name to ID lookup (needed for building lookup)
    maps_df = pd.read_csv('../references/Masterplan Tycoon Data SoT - maps.csv')
    map_name_to_id = {row.map_name: i+1 for i, row in enumerate(maps_df.itertuples())}
    
    relationship_data = []
    for _, row in recipes_df.iterrows():
        recipe_id = recipe_name_to_id.get(row.recipe_name)
        map_id = map_name_to_id.get(row.map_name)
        building_id = building_key_to_id.get((row.building_name, map_id))
        
        if recipe_id and building_id:
            relationship_data.append((recipe_id, building_id))
    
    # Remove duplicates
    relationship_data = list(set(relationship_data))
    
    conn.executemany('INSERT INTO recipe_buildings (recipe_id, building_id) VALUES (?, ?)', relationship_data)
    conn.commit()
    
    print(f"✅ Inserted {len(relationship_data)} recipe-building relationships")
    return relationship_data

def main():
    """Main function to build the clean database"""
    print("🏗️ Building Masterplan Tycoon Clean Database")
    print("=" * 60)
    
    # Load all SoT data
    data = load_sot_data()
    if not data:
        return
    
    # Create database
    conn = create_clean_database()
    
    try:
        # Build tables in dependency order
        maps_data = create_maps_table(conn, data['maps'])
        plans_data = create_plans_table(conn, data['plans'], data['maps'])
        recipes_data = create_recipes_table(conn, data['recipes'])
        buildings_data = create_buildings_table(conn, data['buildings'], data['recipes'], data['maps'])
        resources_data = create_resources_table(conn, data['resources'], data['maps'])
        relationships_data = create_recipe_buildings_table(conn, data['recipes'], recipes_data, buildings_data)
        
        print("\n" + "=" * 60)
        print("🎉 Clean Database creation completed successfully!")
        print(f"📊 Summary:")
        print(f"   • Maps: {len(maps_data)}")
        print(f"   • Plans: {len(plans_data)}")  
        print(f"   • Recipes: {len(recipes_data)}")
        print(f"   • Buildings: {len(buildings_data)}")
        print(f"   • Resources: {len(resources_data)}")
        print(f"   • Recipe-Building Links: {len(relationships_data)}")
        print(f"\n💾 Database saved as: masterplan_tycoon_clean.db")
        
    except Exception as e:
        print(f"❌ Error during database creation: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == "__main__":
    main()