#!/usr/bin/env python3
"""
Database Inspector - Check the current state of the clean database
"""

import sqlite3
import pandas as pd

def inspect_database():
    """Inspect the current database structure and contents"""
    conn = sqlite3.connect('masterplan_tycoon_clean.db')
    
    print("🔍 MASTERPLAN TYCOON CLEAN DATABASE INSPECTION")
    print("=" * 60)
    
    # Get all tables
    tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    print(f"\n📋 TABLES: {len(tables)} total")
    for table in tables:
        print(f"  • {table[0]}")
    
    print("\n" + "=" * 60)
    
    # Inspect each table
    for (table_name,) in tables:
        print(f"\n📊 TABLE: {table_name.upper()}")
        print("-" * 40)
        
        # Get row count
        count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
        print(f"Records: {count}")
        
        # Get column info
        columns = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
        print("Columns:")
        for col in columns:
            col_name, col_type, not_null, default, pk = col[1], col[2], col[3], col[4], col[5]
            pk_marker = " (PK)" if pk else ""
            not_null_marker = " NOT NULL" if not_null else ""
            default_marker = f" DEFAULT {default}" if default else ""
            print(f"  • {col_name}: {col_type}{pk_marker}{not_null_marker}{default_marker}")
        
        # Show sample data
        if count > 0:
            print("Sample data (first 3 rows):")
            df = pd.read_sql_query(f"SELECT * FROM {table_name} LIMIT 3", conn)
            for _, row in df.iterrows():
                row_str = " | ".join([f"{col}: {val}" for col, val in row.items() if val is not None])
                print(f"  {row_str}")
    
    print("\n" + "=" * 60)
    print("� KEY STATISTICS")
    print("-" * 40)
    
    # Recipe tiers
    recipe_tiers = conn.execute("SELECT tier, COUNT(*) as count FROM recipes GROUP BY tier ORDER BY tier").fetchall()
    print("Recipes by tier:")
    for tier, count in recipe_tiers:
        print(f"  • Tier {tier:2d}: {count:2d} recipes")
    
    # Buildings per map
    buildings_per_map = conn.execute("""
    SELECT m.name, COUNT(b.id) as building_count 
    FROM maps m 
    LEFT JOIN buildings b ON m.id = b.map_id 
    GROUP BY m.name
    """).fetchall()
    print("\nBuildings per map:")
    for map_name, count in buildings_per_map:
        print(f"  • {map_name}: {count} buildings")
    
    # Resources per map
    resources_per_map = conn.execute("""
    SELECT m.name, COUNT(r.id) as resource_count 
    FROM maps m 
    LEFT JOIN resources r ON m.id = r.map_id 
    GROUP BY m.name
    """).fetchall()
    print("\nResources per map:")
    for map_name, count in resources_per_map:
        print(f"  • {map_name}: {count} resources")
    
    print("\n" + "=" * 60)
    print("🔗 FOREIGN KEY RELATIONSHIPS")
    print("-" * 40)
    
    relationships = [
        "plans.map_id → maps.id",
        "buildings.map_id → maps.id", 
        "resources.map_id → maps.id",
        "recipe_buildings.recipe_id → recipes.id",
        "recipe_buildings.building_id → buildings.id"
    ]
    
    for rel in relationships:
        print(f"  • {rel}")
    
    print("\n" + "=" * 60)
    print("🎯 NEXT STEPS - Add input/output/construction/maintenance tables:")
    
    remaining_csvs = [
        "building_inputs (from inputs.csv)",
        "building_outputs (from outputs.csv)", 
        "building_construction (from construction.csv)",
        "building_maintenance (from maintenance.csv)"
    ]
    
    for table in remaining_csvs:
        print(f"  • {table}")
    
    print(f"\n✅ Core schema complete! Ready for relationship data.")
    
    conn.close()

if __name__ == "__main__":
    inspect_database()