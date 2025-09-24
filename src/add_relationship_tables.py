#!/usr/bin/env python3
"""
Add Relationship Tables to Clean Database
Build building_inputs, building_outputs, building_construction, building_maintenance
using building+map combinations as the unique identifier
"""

import sqlite3
import pandas as pd

def load_relationship_data():
    """Load the relationship CSV files"""
    try:
        data = {}
        files = ['inputs', 'outputs', 'construction', 'maintenance']
        
        for file in files:
            file_path = f'../references/Masterplan Tycoon Data SoT - {file}.csv'
            data[file] = pd.read_csv(file_path)
            print(f"📁 Loaded {file}.csv: {len(data[file])} records")
        
        return data
    except Exception as e:
        print(f"❌ Error loading relationship files: {e}")
        return None

def get_database_lookups():
    """Create lookup dictionaries from existing database"""
    conn = sqlite3.connect('masterplan_tycoon_clean.db')
    
    # Get buildings lookup: (building_name, map_name) -> building_id
    buildings_query = """
    SELECT b.id, b.name as building_name, m.name as map_name 
    FROM buildings b 
    JOIN maps m ON b.map_id = m.id
    """
    buildings_df = pd.read_sql_query(buildings_query, conn)
    building_lookup = {}
    for _, row in buildings_df.iterrows():
        key = (row.building_name, row.map_name)
        building_lookup[key] = row.id
    
    # Get resources lookup: (resource_name, map_name) -> resource_id
    resources_query = """
    SELECT r.id, r.name as resource_name, m.name as map_name
    FROM resources r
    JOIN maps m ON r.map_id = m.id
    """
    resources_df = pd.read_sql_query(resources_query, conn)
    resource_lookup = {}
    for _, row in resources_df.iterrows():
        key = (row.resource_name, row.map_name)
        resource_lookup[key] = row.id
    
    conn.close()
    
    print(f"📋 Building lookup: {len(building_lookup)} entries")
    print(f"📦 Resource lookup: {len(resource_lookup)} entries")
    
    return building_lookup, resource_lookup

def create_building_inputs_table(conn, inputs_df, building_lookup, resource_lookup):
    """Create and populate building_inputs table"""
    print("🔄 Creating building_inputs table...")
    
    conn.execute('''
    CREATE TABLE building_inputs (
        building_id INTEGER,
        resource_id INTEGER,
        quantity INTEGER,
        FOREIGN KEY (building_id) REFERENCES buildings(id),
        FOREIGN KEY (resource_id) REFERENCES resources(id),
        PRIMARY KEY (building_id, resource_id)
    )
    ''')
    
    inputs_data = []
    missing_buildings = set()
    missing_resources = set()
    
    for _, row in inputs_df.iterrows():
        building_name = row.building_name
        map_name = row.map_name
        resource_name = row.input_resource
        quantity = row.input_resource_qty
        
        # Get building_id
        building_key = (building_name, map_name)
        building_id = building_lookup.get(building_key)
        
        if not building_id:
            missing_buildings.add(building_key)
            continue
        
        # Get resource_id
        resource_key = (resource_name, map_name)
        resource_id = resource_lookup.get(resource_key)
        
        if not resource_id:
            missing_resources.add(resource_key)
            continue
        
        inputs_data.append((building_id, resource_id, quantity))
    
    # Remove duplicates (in case of data issues)
    inputs_data = list(set(inputs_data))
    
    conn.executemany('''
    INSERT INTO building_inputs (building_id, resource_id, quantity) VALUES (?, ?, ?)
    ''', inputs_data)
    
    conn.commit()
    
    print(f"✅ Inserted {len(inputs_data)} building input relationships")
    if missing_buildings:
        print(f"⚠️ Missing buildings: {len(missing_buildings)} (first 5: {list(missing_buildings)[:5]})")
    if missing_resources:
        print(f"⚠️ Missing resources: {len(missing_resources)} (first 5: {list(missing_resources)[:5]})")
    
    return inputs_data

def create_building_outputs_table(conn, outputs_df, building_lookup, resource_lookup):
    """Create and populate building_outputs table"""
    print("🏭 Creating building_outputs table...")
    
    conn.execute('''
    CREATE TABLE building_outputs (
        building_id INTEGER,
        resource_id INTEGER,
        quantity INTEGER,
        production_time_seconds INTEGER,
        output_per_minute REAL,
        FOREIGN KEY (building_id) REFERENCES buildings(id),
        FOREIGN KEY (resource_id) REFERENCES resources(id),
        PRIMARY KEY (building_id, resource_id)
    )
    ''')
    
    outputs_data = []
    missing_buildings = set()
    missing_resources = set()
    
    for _, row in outputs_df.iterrows():
        building_name = row.building  # Note: column name is 'building' not 'building_name'
        map_name = row.map_name
        resource_name = row.output
        quantity = row.output_qty
        production_time = row.iloc[4]  # output_time(s) column
        output_per_min = row.output_per_minute
        
        # Get building_id
        building_key = (building_name, map_name)
        building_id = building_lookup.get(building_key)
        
        if not building_id:
            missing_buildings.add(building_key)
            continue
        
        # Get resource_id
        resource_key = (resource_name, map_name)
        resource_id = resource_lookup.get(resource_key)
        
        if not resource_id:
            missing_resources.add(resource_key)
            continue
        
        outputs_data.append((building_id, resource_id, quantity, production_time, output_per_min))
    
    # Remove duplicates
    outputs_data = list(set(outputs_data))
    
    conn.executemany('''
    INSERT INTO building_outputs (building_id, resource_id, quantity, production_time_seconds, output_per_minute) 
    VALUES (?, ?, ?, ?, ?)
    ''', outputs_data)
    
    conn.commit()
    
    print(f"✅ Inserted {len(outputs_data)} building output relationships")
    if missing_buildings:
        print(f"⚠️ Missing buildings: {len(missing_buildings)} (first 5: {list(missing_buildings)[:5]})")
    if missing_resources:
        print(f"⚠️ Missing resources: {len(missing_resources)} (first 5: {list(missing_resources)[:5]})")
    
    return outputs_data

def create_building_construction_table(conn, construction_df, building_lookup, resource_lookup):
    """Create and populate building_construction table"""
    print("🏗️ Creating building_construction table...")
    
    conn.execute('''
    CREATE TABLE building_construction (
        building_id INTEGER,
        resource_id INTEGER,
        quantity INTEGER,
        FOREIGN KEY (building_id) REFERENCES buildings(id),
        FOREIGN KEY (resource_id) REFERENCES resources(id),
        PRIMARY KEY (building_id, resource_id)
    )
    ''')
    
    construction_data = []
    missing_buildings = set()
    missing_resources = set()
    
    for _, row in construction_df.iterrows():
        building_name = row.building_name
        map_name = row.map_name
        resource_name = row.construction_resource
        quantity = row.construction_resource_qty
        
        # Get building_id
        building_key = (building_name, map_name)
        building_id = building_lookup.get(building_key)
        
        if not building_id:
            missing_buildings.add(building_key)
            continue
        
        # Get resource_id
        resource_key = (resource_name, map_name)
        resource_id = resource_lookup.get(resource_key)
        
        if not resource_id:
            missing_resources.add(resource_key)
            continue
        
        construction_data.append((building_id, resource_id, quantity))
    
    # Remove duplicates
    construction_data = list(set(construction_data))
    
    conn.executemany('''
    INSERT INTO building_construction (building_id, resource_id, quantity) VALUES (?, ?, ?)
    ''', construction_data)
    
    conn.commit()
    
    print(f"✅ Inserted {len(construction_data)} building construction relationships")
    if missing_buildings:
        print(f"⚠️ Missing buildings: {len(missing_buildings)} (first 5: {list(missing_buildings)[:5]})")
    if missing_resources:
        print(f"⚠️ Missing resources: {len(missing_resources)} (first 5: {list(missing_resources)[:5]})")
    
    return construction_data

def create_building_maintenance_table(conn, maintenance_df, building_lookup, resource_lookup):
    """Create and populate building_maintenance table"""
    print("🔧 Creating building_maintenance table...")
    
    conn.execute('''
    CREATE TABLE building_maintenance (
        building_id INTEGER,
        resource_id INTEGER,
        quantity INTEGER,
        FOREIGN KEY (building_id) REFERENCES buildings(id),
        FOREIGN KEY (resource_id) REFERENCES resources(id),
        PRIMARY KEY (building_id, resource_id)
    )
    ''')
    
    maintenance_data = []
    missing_buildings = set()
    missing_resources = set()
    
    for _, row in maintenance_df.iterrows():
        building_name = row.building_name
        map_name = row.map_name
        resource_name = row.maintenance_resource
        quantity = row.maintenance_resource_qty
        
        # Get building_id
        building_key = (building_name, map_name)
        building_id = building_lookup.get(building_key)
        
        if not building_id:
            missing_buildings.add(building_key)
            continue
        
        # Get resource_id
        resource_key = (resource_name, map_name)
        resource_id = resource_lookup.get(resource_key)
        
        if not resource_id:
            missing_resources.add(resource_key)
            continue
        
        maintenance_data.append((building_id, resource_id, quantity))
    
    # Remove duplicates
    maintenance_data = list(set(maintenance_data))
    
    conn.executemany('''
    INSERT INTO building_maintenance (building_id, resource_id, quantity) VALUES (?, ?, ?)
    ''', maintenance_data)
    
    conn.commit()
    
    print(f"✅ Inserted {len(maintenance_data)} building maintenance relationships")
    if missing_buildings:
        print(f"⚠️ Missing buildings: {len(missing_buildings)} (first 5: {list(missing_buildings)[:5]})")
    if missing_resources:
        print(f"⚠️ Missing resources: {len(missing_resources)} (first 5: {list(missing_resources)[:5]})")
    
    return maintenance_data

def main():
    """Main function to add relationship tables"""
    print("🔗 Adding Relationship Tables to Clean Database")
    print("=" * 60)
    
    # Load relationship data
    data = load_relationship_data()
    if not data:
        return
    
    # Get database lookups
    building_lookup, resource_lookup = get_database_lookups()
    
    # Connect to database
    conn = sqlite3.connect('masterplan_tycoon_clean.db')
    
    try:
        # Create relationship tables
        inputs_data = create_building_inputs_table(conn, data['inputs'], building_lookup, resource_lookup)
        outputs_data = create_building_outputs_table(conn, data['outputs'], building_lookup, resource_lookup)
        construction_data = create_building_construction_table(conn, data['construction'], building_lookup, resource_lookup)
        maintenance_data = create_building_maintenance_table(conn, data['maintenance'], building_lookup, resource_lookup)
        
        print("\n" + "=" * 60)
        print("🎉 Relationship tables added successfully!")
        print(f"📊 Summary:")
        print(f"   • Building Inputs: {len(inputs_data)}")
        print(f"   • Building Outputs: {len(outputs_data)}")
        print(f"   • Building Construction: {len(construction_data)}")
        print(f"   • Building Maintenance: {len(maintenance_data)}")
        print(f"\n💾 Database updated: masterplan_tycoon_clean.db")
        print(f"\n🎯 Ready for resource chain visualization!")
        
    except Exception as e:
        print(f"❌ Error during relationship table creation: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == "__main__":
    main()