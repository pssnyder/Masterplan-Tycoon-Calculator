#!/usr/bin/env python3
"""
Deep dive into the Coal Mine relationship issue
"""

import sqlite3
import pandas as pd

def investigate_coal_mine():
    """Deep investigation of Coal Mine relationships"""
    conn = sqlite3.connect('masterplan_tycoon_clean.db')
    
    print("🔍 COAL MINE DEEP INVESTIGATION")
    print("=" * 50)
    
    # Get Coal Mine details
    coal_mine = pd.read_sql_query("""
    SELECT b.id, b.name, m.name as map_name, b.building_id
    FROM buildings b
    JOIN maps m ON b.map_id = m.id
    WHERE b.name = 'Coal Mine' AND m.name = 'Master'
    """, conn)
    
    print("Coal Mine Building Info:")
    print(coal_mine)
    
    if not coal_mine.empty:
        building_id = coal_mine.iloc[0]['id']
        print(f"\nLooking for building_id: {building_id} (type: {type(building_id)})")
        
        # Check all relationship tables for this building_id
        tables = ['building_outputs', 'building_inputs', 'building_construction', 'building_maintenance']
        
        for table in tables:
            print(f"\n🔍 Checking {table}:")
            
            # First check if this ID exists at all
            exists_query = f"SELECT COUNT(*) as count FROM {table} WHERE building_id = ?"
            exists = pd.read_sql_query(exists_query, conn, params=(building_id,))
            print(f"   Records found: {exists.iloc[0]['count']}")
            
            # If records exist, show them
            if exists.iloc[0]['count'] > 0:
                data_query = f"SELECT * FROM {table} WHERE building_id = ?"
                data = pd.read_sql_query(data_query, conn, params=(building_id,))
                print(f"   Data:")
                print(data.to_string(index=False))
    
    # Also check what outputs building_id 43 has using raw SQL
    print(f"\n🔍 Raw SQL check for building_id 43:")
    raw_check = conn.execute("SELECT * FROM building_outputs WHERE building_id = 43").fetchall()
    print(f"Raw SQL results: {raw_check}")
    
    # Check all building_ids that have outputs
    print(f"\n📊 All building_ids in outputs (sample):")
    all_outputs = pd.read_sql_query("SELECT building_id, COUNT(*) as count FROM building_outputs GROUP BY building_id ORDER BY building_id LIMIT 10", conn)
    print(all_outputs)
    
    conn.close()

if __name__ == "__main__":
    investigate_coal_mine()