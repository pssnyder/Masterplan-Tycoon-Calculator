#!/usr/bin/env python3
"""
Quick Database Browser - Check available resources and buildings
"""

import sqlite3
import pandas as pd

def check_database_contents():
    """Check what's actually in our database"""
    conn = sqlite3.connect('masterplan_tycoon_clean.db')
    
    print("🔍 DATABASE CONTENTS BROWSER")
    print("=" * 60)
    
    # Check resources by map
    print("📦 RESOURCES BY MAP:")
    resources_query = """
    SELECT m.name as map_name, COUNT(*) as count, 
           GROUP_CONCAT(r.name, ', ') as sample_resources
    FROM resources r
    JOIN maps m ON r.map_id = m.id
    GROUP BY m.id, m.name
    ORDER BY m.name
    """
    resources_summary = pd.read_sql_query(resources_query, conn)
    
    for _, row in resources_summary.iterrows():
        print(f"   {row.map_name}: {row['count']} resources")
        # Show first few resources
        sample_list = row.sample_resources.split(', ')[:5]
        print(f"      Examples: {', '.join(sample_list)}")
        if len(sample_list) == 5:
            print(f"      ... and {row['count'] - 5} more")
        print()
    
    # Check buildings by map
    print("🏗️ BUILDINGS BY MAP:")
    buildings_query = """
    SELECT m.name as map_name, COUNT(*) as count,
           GROUP_CONCAT(b.name, ', ') as sample_buildings
    FROM buildings b
    JOIN maps m ON b.map_id = m.id
    GROUP BY m.id, m.name
    ORDER BY m.name
    """
    buildings_summary = pd.read_sql_query(buildings_query, conn)
    
    for _, row in buildings_summary.iterrows():
        print(f"   {row.map_name}: {row['count']} buildings")
        # Show first few buildings
        sample_list = row.sample_buildings.split(', ')[:5]
        print(f"      Examples: {', '.join(sample_list)}")
        if len(sample_list) == 5:
            print(f"      ... and {row['count'] - 5} more")
        print()
    
    # Check some specific resource chains that should exist
    print("🔍 LOOKING FOR COMMON RESOURCES:")
    common_resources = ['Steel', 'Wood', 'Iron', 'Coal', 'Stone', 'Food', 'Water']
    
    for resource_name in common_resources:
        resource_query = """
        SELECT r.name, m.name as map_name
        FROM resources r
        JOIN maps m ON r.map_id = m.id
        WHERE r.name LIKE ?
        LIMIT 3
        """
        matches = pd.read_sql_query(resource_query, conn, params=(f'%{resource_name}%',))
        
        if not matches.empty:
            print(f"   ✅ Found '{resource_name}'-like resources:")
            for _, match in matches.iterrows():
                print(f"      • {match['name']} ({match.map_name})")
        else:
            print(f"   ❌ No '{resource_name}'-like resources found")
    
    print("\n🏭 LOOKING FOR COMMON BUILDINGS:")
    common_buildings = ['Mill', 'Factory', 'Mine', 'Farm', 'Workshop', 'Refinery']
    
    for building_name in common_buildings:
        building_query = """
        SELECT b.name, m.name as map_name
        FROM buildings b
        JOIN maps m ON b.map_id = m.id
        WHERE b.name LIKE ?
        LIMIT 3
        """
        matches = pd.read_sql_query(building_query, conn, params=(f'%{building_name}%',))
        
        if not matches.empty:
            print(f"   ✅ Found '{building_name}'-like buildings:")
            for _, match in matches.iterrows():
                print(f"      • {match['name']} ({match.map_name})")
        else:
            print(f"   ❌ No '{building_name}'-like buildings found")
    
    conn.close()

if __name__ == "__main__":
    check_database_contents()