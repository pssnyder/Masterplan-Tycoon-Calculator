#!/usr/bin/env python3
"""
Masterplan Tycoon Database Builder - Revised Schema
Build database following the updated schema template, table by table
"""

import sqlite3
import pandas as pd
import json
from pathlib import Path

def create_database():
    """Create the database with revised schema"""
    conn = sqlite3.connect('masterplan_tycoon_revised.db')
    
    # Drop existing tables if they exist
    drop_tables = [
        'building_maintenance', 'building_construction', 'building_outputs', 
        'building_inputs', 'building_groups', 'resources', 'resource_categories',
        'buildings', 'building_categories', 'plans', 'maps'
    ]
    
    for table in drop_tables:
        conn.execute(f'DROP TABLE IF EXISTS {table}')
    
    conn.commit()
    return conn

def create_maps_table(conn):
    """Create and populate the maps table"""
    print("🗺️ Creating Maps table...")
    
    conn.execute('''
    CREATE TABLE maps (
        id INTEGER PRIMARY KEY,
        name TEXT UNIQUE NOT NULL,
        description TEXT
    )
    ''')
    
    # Based on the data, we have these main maps
    maps_data = [
        (1, 'Master', 'The main master region with basic production facilities'),
        (2, 'Islands', 'Tropical islands region with specialized production'),
        (3, 'Mountains', 'Mountain region with mining and advanced production'),
        (4, 'Other', 'Special or universal buildings not tied to specific regions')
    ]
    
    conn.executemany('''
    INSERT INTO maps (id, name, description) VALUES (?, ?, ?)
    ''', maps_data)
    
    conn.commit()
    print(f"✅ Inserted {len(maps_data)} maps")
    return maps_data

def create_plans_table(conn, buildings_df):
    """Create and populate the plans table based on CSV data"""
    print("📋 Creating Plans table...")
    
    conn.execute('''
    CREATE TABLE plans (
        id INTEGER PRIMARY KEY,
        name TEXT UNIQUE NOT NULL,
        map_id INTEGER,
        description TEXT,
        FOREIGN KEY (map_id) REFERENCES maps (id)
    )
    ''')
    
    # Get unique plan names from buildings data
    unique_plans = buildings_df['plan'].unique()
    
    # Map plan names to map IDs
    plan_to_map = {
        'Master': 1,
        'Islands': 2, 
        'Mountains': 3,
        'Other': 4
    }
    
    plans_data = []
    for i, plan_name in enumerate(unique_plans, 1):
        map_id = plan_to_map.get(plan_name, 4)  # Default to 'Other'
        description = f"Production plan for {plan_name} region"
        plans_data.append((i, plan_name, map_id, description))
    
    conn.executemany('''
    INSERT INTO plans (id, name, map_id, description) VALUES (?, ?, ?, ?)
    ''', plans_data)
    
    conn.commit()
    print(f"✅ Inserted {len(plans_data)} plans")
    return plans_data

def create_building_categories_table(conn, buildings_df):
    """Create and populate building categories table"""
    print("🏗️ Creating Building Categories table...")
    
    conn.execute('''
    CREATE TABLE building_categories (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        description TEXT,
        map_id INTEGER,
        plan_id INTEGER,
        tier INTEGER,
        UNIQUE(name, plan_id),
        FOREIGN KEY (map_id) REFERENCES maps (id),
        FOREIGN KEY (plan_id) REFERENCES plans (id)
    )
    ''')
    
    # Get unique categories with their associated plans and tiers
    category_info = buildings_df.groupby(['category', 'plan']).agg({
        'tier': 'max'  # Use max tier for the category
    }).reset_index()
    
    # Map plan names to IDs
    plan_name_to_id = {'Master': 1, 'Islands': 2, 'Mountains': 3, 'Other': 4}
    map_name_to_id = {'Master': 1, 'Islands': 2, 'Mountains': 3, 'Other': 4}
    
    categories_data = []
    for i, row in enumerate(category_info.itertuples(), 1):
        category_name = row.category
        plan_name = row.plan
        tier = row.tier
        
        plan_id = plan_name_to_id.get(plan_name, 4)
        map_id = map_name_to_id.get(plan_name, 4)
        
        description = f"Production category for {category_name} in {plan_name} (Tier {tier})"
        categories_data.append((i, category_name, description, map_id, plan_id, tier))
    
    conn.executemany('''
    INSERT INTO building_categories (id, name, description, map_id, plan_id, tier) 
    VALUES (?, ?, ?, ?, ?, ?)
    ''', categories_data)
    
    conn.commit()
    print(f"✅ Inserted {len(categories_data)} building categories")
    return categories_data

def generate_building_id(building_name, plan, tier, category):
    """Generate unique building ID using constructor format: MAP#-TIER#-CATEGORY_ABBR-BUILDING_ABBR(MAP_ABBR)"""
    
    # Map plan names to numbers
    map_numbers = {'Master': '1', 'Islands': '2', 'Mountains': '3', 'Other': '4'}
    map_abbr = {'Master': 'M', 'Islands': 'I', 'Mountains': 'M', 'Other': 'O'}
    
    # Generate category abbreviation (first letter of each word, max 3 chars)
    category_words = category.replace('-', ' ').split()
    category_abbr = ''.join(word[0].upper() for word in category_words)[:3]
    
    # Generate building abbreviation (first letter of each word, max 4 chars)
    # Remove plan name from building name first
    clean_building_name = building_name.replace(f'({plan})', '').strip()
    building_words = clean_building_name.replace('-', ' ').split()
    building_abbr = ''.join(word[0].upper() for word in building_words if word)[:4]
    
    # Format: MAP#-TIER#-CATEGORY_ABBR-BUILDING_ABBR+MAP_ABBR
    building_id = f"{map_numbers[plan]}-{tier:02d}-{category_abbr}-{building_abbr}{map_abbr[plan]}"
    
    return building_id

def create_buildings_table(conn, buildings_df, inputs_df, outputs_df):
    """Create and populate the main buildings table"""
    print("🏢 Creating Buildings table...")
    
    conn.execute('''
    CREATE TABLE buildings (
        id INTEGER PRIMARY KEY,
        building_id TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        map_id INTEGER,
        tier INTEGER,
        maintenance_required BOOLEAN DEFAULT FALSE,
        root_building BOOLEAN DEFAULT FALSE,
        node_building BOOLEAN DEFAULT FALSE,
        terminal_building BOOLEAN DEFAULT FALSE,
        FOREIGN KEY (map_id) REFERENCES maps (id)
    )
    ''')
    
    # Map plan names to map IDs
    plan_to_map_id = {'Master': 1, 'Islands': 2, 'Mountains': 3, 'Other': 4}
    
    buildings_data = []
    used_building_ids = set()  # Track used IDs to ensure uniqueness
    
    for i, row in enumerate(buildings_df.itertuples(), 1):
        original_buid = row.buid
        name = row.buildings
        plan = row.plan
        tier = row.tier
        category = row.category
        
        map_id = plan_to_map_id.get(plan, 4)
        
        # Generate new unique building ID
        base_building_id = generate_building_id(name, plan, tier, category)
        building_id = base_building_id
        
        # Handle duplicates by adding suffix
        counter = 1
        while building_id in used_building_ids:
            building_id = f"{base_building_id}-{counter}"
            counter += 1
        
        used_building_ids.add(building_id)
        
        # Determine building type based on inputs/outputs using original buid
        has_inputs = len(inputs_df[inputs_df['buid'] == original_buid]) > 0
        has_outputs = len(outputs_df[outputs_df['buid'] == original_buid]) > 0
        
        # Classification logic
        root_building = not has_inputs and has_outputs  # No inputs, has outputs
        terminal_building = has_inputs and not has_outputs  # Has inputs, no outputs  
        node_building = has_inputs and has_outputs  # Has both
        
        # For now, assume all buildings require maintenance
        maintenance_required = True
        
        buildings_data.append((
            i, building_id, name, map_id, tier, 
            maintenance_required, root_building, node_building, terminal_building
        ))
    
    conn.executemany('''
    INSERT INTO buildings (id, building_id, name, map_id, tier, maintenance_required, 
                          root_building, node_building, terminal_building) 
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', buildings_data)
    
    conn.commit()
    print(f"✅ Inserted {len(buildings_data)} buildings")
    print("📋 Sample building IDs generated:")
    for i in range(min(5, len(buildings_data))):
        data = buildings_data[i]
        print(f"   • {data[1]} - {data[2]}")
    
    return buildings_data

def create_resource_tables(conn, inputs_df, outputs_df):
    """Create and populate resource-related tables"""
    print("📦 Creating Resource tables...")
    
    # Create resource categories table
    conn.execute('''
    CREATE TABLE resource_categories (
        id INTEGER PRIMARY KEY,
        name TEXT UNIQUE NOT NULL,
        description TEXT
    )
    ''')
    
    # Create resources table
    conn.execute('''
    CREATE TABLE resources (
        id INTEGER PRIMARY KEY,
        name TEXT UNIQUE NOT NULL,
        category_id INTEGER,
        is_consumable BOOLEAN DEFAULT TRUE,
        FOREIGN KEY (category_id) REFERENCES resource_categories (id)
    )
    ''')
    
    # Get all unique resources from inputs and outputs
    input_resources = set(inputs_df['input'].unique())
    output_resources = set(outputs_df['output'].unique())
    all_resources = input_resources.union(output_resources)
    
    # Categorize resources (basic categorization)
    resource_categories = {
        'Raw Materials': ['Coal', 'Iron Ore', 'Copper Ore', 'Gold Ore', 'Stone', 'Clay', 'Sand', 'Water', 'Tree', 'Oak'],
        'Agricultural': ['Grain', 'Barley', 'Bean', 'Fish', 'Milk', 'Cotton', 'Bamboo', 'Banana', 'Citrus', 'Coffee Beans', 'Corn'],
        'Processed Materials': ['Steel', 'Copper', 'Gold', 'Brick', 'Glass', 'Plank', 'Rope', 'Leather'],
        'Food & Beverages': ['Bread', 'Beer', 'Steak', 'Rum', 'Coffee', 'Lemonade'],
        'Manufactured Goods': ['Clothes', 'Boots', 'Glasses', 'Watch', 'Revolver', 'Steam Engine'],
        'Advanced Products': ['Coin', 'Light Bulb', 'Poncho', 'Cigars']
    }
    
    # Insert categories
    category_data = []
    for i, (cat_name, _) in enumerate(resource_categories.items(), 1):
        description = f"Category for {cat_name.lower()}"
        category_data.append((i, cat_name, description))
    
    conn.executemany('''
    INSERT INTO resource_categories (id, name, description) VALUES (?, ?, ?)
    ''', category_data)
    
    # Insert resources
    resources_data = []
    resource_id = 1
    
    for cat_id, (cat_name, resource_list) in enumerate(resource_categories.items(), 1):
        for resource_name in all_resources:
            if any(cat_resource.lower() in resource_name.lower() for cat_resource in resource_list):
                resources_data.append((resource_id, resource_name, cat_id, True))
                resource_id += 1
                break
    
    # Add any remaining resources to a default category
    assigned_resources = {r[1] for r in resources_data}
    remaining_resources = all_resources - assigned_resources
    
    if remaining_resources:
        # Add "Other" category
        cursor = conn.execute("INSERT INTO resource_categories (name, description) VALUES (?, ?)",
                    ("Other", "Miscellaneous resources"))
        other_cat_id = cursor.lastrowid
        
        for resource_name in remaining_resources:
            resources_data.append((resource_id, resource_name, other_cat_id, True))
            resource_id += 1
    
    conn.executemany('''
    INSERT INTO resources (id, name, category_id, is_consumable) VALUES (?, ?, ?, ?)
    ''', resources_data)
    
    conn.commit()
    print(f"✅ Inserted {len(category_data)} resource categories")
    print(f"✅ Inserted {len(resources_data)} resources")
    return category_data, resources_data

def main():
    """Main function to build the revised database"""
    print("🏗️ Building Masterplan Tycoon Revised Database")
    print("=" * 50)
    
    # Load CSV data
    try:
        buildings_df = pd.read_csv('../references/Masterplan Tycoon Building Calculations - buildings.csv')
        inputs_df = pd.read_csv('../references/Masterplan Tycoon Building Calculations - inputs.csv')
        outputs_df = pd.read_csv('../references/Masterplan Tycoon Building Calculations - outputs.csv')
        print("📁 Loaded CSV data files")
    except Exception as e:
        print(f"❌ Error loading CSV files: {e}")
        return
    
    # Create database
    conn = create_database()
    
    try:
        # Build tables in dependency order
        maps_data = create_maps_table(conn)
        plans_data = create_plans_table(conn, buildings_df)
        categories_data = create_building_categories_table(conn, buildings_df)
        buildings_data = create_buildings_table(conn, buildings_df, inputs_df, outputs_df)
        resource_categories_data, resources_data = create_resource_tables(conn, inputs_df, outputs_df)
        
        print("\n" + "=" * 50)
        print("🎉 Database creation completed successfully!")
        print(f"📊 Summary:")
        print(f"   • Maps: {len(maps_data)}")
        print(f"   • Plans: {len(plans_data)}")  
        print(f"   • Building Categories: {len(categories_data)}")
        print(f"   • Buildings: {len(buildings_data)}")
        print(f"   • Resource Categories: {len(resource_categories_data)}")
        print(f"   • Resources: {len(resources_data)}")
        print(f"\n💾 Database saved as: masterplan_tycoon_revised.db")
        
    except Exception as e:
        print(f"❌ Error during database creation: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
