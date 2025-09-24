#!/usr/bin/env python3
"""
Debug Relationship Tables - Check why relationships aren't showing up
"""

import sqlite3
import pandas as pd

def debug_relationships():
    """Debug relationship table connections"""
    conn = sqlite3.connect('masterplan_tycoon_clean.db')
    
    print("🔍 DEBUGGING RELATIONSHIP TABLE CONNECTIONS")
    print("=" * 60)
    
    # Check building_outputs data
    print("📤 Building Outputs Sample:")
    outputs = pd.read_sql_query("SELECT * FROM building_outputs LIMIT 5", conn)
    print(outputs)
    
    print("\n📥 Building Inputs Sample:")
    inputs = pd.read_sql_query("SELECT * FROM building_inputs LIMIT 5", conn)
    print(inputs)
    
    print("\n🏗️ Buildings ID Range:")
    building_ids = pd.read_sql_query("SELECT MIN(id) as min_id, MAX(id) as max_id, COUNT(*) as total FROM buildings", conn)
    print(building_ids)
    
    print("\n📦 Resources ID Range:")
    resource_ids = pd.read_sql_query("SELECT MIN(id) as min_id, MAX(id) as max_id, COUNT(*) as total FROM resources", conn)
    print(resource_ids)
    
    # Check for data type issues
    print("\n🔍 Checking data types in building_outputs:")
    type_check = pd.read_sql_query("""
    SELECT 
        typeof(building_id) as building_id_type,
        typeof(resource_id) as resource_id_type,
        building_id, 
        resource_id 
    FROM building_outputs 
    LIMIT 5
    """, conn)
    print(type_check)
    
    # Test a specific building lookup
    print("\n🧪 Testing specific building lookup:")
    test_building = pd.read_sql_query("""
    SELECT b.id, b.name, m.name as map_name
    FROM buildings b
    JOIN maps m ON b.map_id = m.id
    WHERE b.name = 'Coal Mine' AND m.name = 'Master'
    """, conn)
    print("Coal Mine lookup:", test_building)
    
    if not test_building.empty:
        building_id = test_building.iloc[0]['id']
        print(f"Building ID: {building_id} (type: {type(building_id)})")
        
        # Check if this building has outputs
        outputs_check = pd.read_sql_query("""
        SELECT * FROM building_outputs WHERE building_id = ?
        """, conn, params=(building_id,))
        print(f"Outputs for Coal Mine: {len(outputs_check)} records")
        print(outputs_check)
        
        # Check inputs too
        inputs_check = pd.read_sql_query("""
        SELECT * FROM building_inputs WHERE building_id = ?
        """, conn, params=(building_id,))
        print(f"Inputs for Coal Mine: {len(inputs_check)} records")
        print(inputs_check)
    
    # Check if we have any valid relationships at all
    print("\n📊 Relationship Table Stats:")
    for table in ['building_outputs', 'building_inputs', 'building_construction', 'building_maintenance']:
        count = pd.read_sql_query(f"SELECT COUNT(*) as count FROM {table}", conn)
        print(f"   {table}: {count.iloc[0]['count']} records")
    
    conn.close()

if __name__ == "__main__":
    debug_relationships()