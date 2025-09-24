#!/usr/bin/env python3
"""
Resource Chain Explorer
Test the complete database with resource chain queries and basic visualizations
    inputs = pd.read_sql_query(inputs_query, conn, params=(int(building_id),))
    
    print(f"📥 INPUTS ({len(inputs)}):")
    if inputs.empty:
        print("   • No inputs required")
    else:
        for _, inp in inputs.iterrows():
            print(f"   • {inp.resource_name}: {inp.quantity} ({inp.resource_map})")
    
    # Get outputs
    outputs_query = """
    SELECT r.name as resource_name, bo.quantity, bo.production_time_seconds, 
           bo.output_per_minute, m.name as resource_map
    FROM building_outputs bo
    JOIN resources r ON bo.resource_id = r.id
    JOIN maps m ON r.map_id = m.id
    WHERE bo.building_id = ?
    """
    outputs = pd.read_sql_query(outputs_query, conn, params=(int(building_id),))e3
import pandas as pd
import matplotlib.pyplot as plt
import networkx as nx
from collections import defaultdict

def get_resource_chain(resource_name, map_name="Master", depth=3):
    """Get the complete resource chain for a given resource"""
    conn = sqlite3.connect('masterplan_tycoon_clean.db')
    
    # Find the target resource
    resource_query = """
    SELECT r.id, r.name, m.name as map_name
    FROM resources r
    JOIN maps m ON r.map_id = m.id
    WHERE r.name = ? AND m.name = ?
    """
    
    target_resource = pd.read_sql_query(resource_query, conn, params=(resource_name, map_name))
    if target_resource.empty:
        print(f"❌ Resource '{resource_name}' not found in map '{map_name}'")
        return None
    
    resource_id = target_resource.iloc[0]['id']
    print(f"🎯 Tracing resource chain for: {resource_name} (ID: {resource_id}) in {map_name}")
    
    # Get producers of this resource
    producers_query = """
    SELECT 
        b.name as building_name,
        m.name as map_name,
        bo.quantity as output_qty,
        bo.production_time_seconds,
        bo.output_per_minute
    FROM building_outputs bo
    JOIN buildings b ON bo.building_id = b.id
    JOIN maps m ON b.map_id = m.id
    WHERE bo.resource_id = ?
    """
    
    producers = pd.read_sql_query(producers_query, conn, params=(int(resource_id),))
    print(f"\n🏭 PRODUCERS ({len(producers)}):")
    for _, producer in producers.iterrows():
        print(f"   • {producer.building_name} ({producer.map_name})")
        print(f"     Output: {producer.output_qty} every {producer.production_time_seconds}s")
        print(f"     Rate: {producer.output_per_minute:.1f}/min")
    
    # Get consumers of this resource
    consumers_query = """
    SELECT 
        b.name as building_name,
        m.name as map_name,
        bi.quantity as input_qty
    FROM building_inputs bi
    JOIN buildings b ON bi.building_id = b.id
    JOIN maps m ON b.map_id = m.id
    WHERE bi.resource_id = ?
    """
    
    consumers = pd.read_sql_query(consumers_query, conn, params=(int(resource_id),))
    print(f"\n🔧 CONSUMERS ({len(consumers)}):")
    for _, consumer in consumers.iterrows():
        print(f"   • {consumer.building_name} ({consumer.map_name})")
        print(f"     Input: {consumer.input_qty} required")
    
    # Get what the producers need as inputs
    if not producers.empty:
        print(f"\n⚙️ UPSTREAM DEPENDENCIES:")
        for _, producer in producers.iterrows():
            building_query = """
            SELECT b.id FROM buildings b 
            JOIN maps m ON b.map_id = m.id
            WHERE b.name = ? AND m.name = ?
            """
            building_id = pd.read_sql_query(building_query, conn, 
                                          params=(producer.building_name, producer.map_name))
            
            if not building_id.empty:
                inputs_query = """
                SELECT 
                    r.name as resource_name,
                    bi.quantity
                FROM building_inputs bi
                JOIN resources r ON bi.resource_id = r.id
                WHERE bi.building_id = ?
                """
                inputs = pd.read_sql_query(inputs_query, conn, params=(int(building_id.iloc[0]['id']),))
                
                if not inputs.empty:
                    print(f"   {producer.building_name} needs:")
                    for _, inp in inputs.iterrows():
                        print(f"     - {inp.resource_name}: {inp.quantity}")
    
    conn.close()
    return {
        'target': target_resource.iloc[0],
        'producers': producers,
        'consumers': consumers
    }

def get_building_analysis(building_name, map_name="Master"):
    """Analyze a specific building's inputs, outputs, construction, and maintenance"""
    conn = sqlite3.connect('masterplan_tycoon_clean.db')
    
    # Find the building
    building_query = """
    SELECT b.id, b.name, m.name as map_name, b.building_id
    FROM buildings b
    JOIN maps m ON b.map_id = m.id
    WHERE b.name = ? AND m.name = ?
    """
    
    building = pd.read_sql_query(building_query, conn, params=(building_name, map_name))
    if building.empty:
        print(f"❌ Building '{building_name}' not found in map '{map_name}'")
        return None
    
    building_id = building.iloc[0]['id']
    print(f"🏗️ BUILDING ANALYSIS: {building_name} (ID: {building.iloc[0]['building_id']}) in {map_name}")
    print("=" * 80)
    
    # Get inputs
    inputs_query = """
    SELECT r.name as resource_name, bi.quantity, m.name as resource_map
    FROM building_inputs bi
    JOIN resources r ON bi.resource_id = r.id
    JOIN maps m ON r.map_id = m.id
    WHERE bi.building_id = ?
    """
    inputs = pd.read_sql_query(inputs_query, conn, params=(building_id,))
    
    print(f"📥 INPUTS ({len(inputs)}):")
    if inputs.empty:
        print("   • No inputs required")
    else:
        for _, inp in inputs.iterrows():
            print(f"   • {inp.resource_name}: {inp.quantity} ({inp.resource_map})")
    
    # Get outputs
    outputs_query = """
    SELECT r.name as resource_name, bo.quantity, bo.production_time_seconds, 
           bo.output_per_minute, m.name as resource_map
    FROM building_outputs bo
    JOIN resources r ON bo.resource_id = r.id
    JOIN maps m ON r.map_id = m.id
    WHERE bo.building_id = ?
    """
    outputs = pd.read_sql_query(outputs_query, conn, params=(int(building_id),))
    
    print(f"\n📤 OUTPUTS ({len(outputs)}):")
    if outputs.empty:
        print("   • No outputs produced")
    else:
        for _, out in outputs.iterrows():
            print(f"   • {out.resource_name}: {out.quantity} every {out.production_time_seconds}s")
            print(f"     Rate: {out.output_per_minute:.1f}/min ({out.resource_map})")
    
    # Get construction requirements
    construction_query = """
    SELECT r.name as resource_name, bc.quantity, m.name as resource_map
    FROM building_construction bc
    JOIN resources r ON bc.resource_id = r.id
    JOIN maps m ON r.map_id = m.id
    WHERE bc.building_id = ?
    """
    construction = pd.read_sql_query(construction_query, conn, params=(int(building_id),))
    
    print(f"\n🔨 CONSTRUCTION REQUIREMENTS ({len(construction)}):")
    if construction.empty:
        print("   • No construction data")
    else:
        for _, const in construction.iterrows():
            print(f"   • {const.resource_name}: {const.quantity} ({const.resource_map})")
    
    # Get maintenance requirements
    maintenance_query = """
    SELECT r.name as resource_name, bm.quantity, m.name as resource_map
    FROM building_maintenance bm
    JOIN resources r ON bm.resource_id = r.id
    JOIN maps m ON r.map_id = m.id
    WHERE bm.building_id = ?
    """
    maintenance = pd.read_sql_query(maintenance_query, conn, params=(int(building_id),))
    
    print(f"\n🔧 MAINTENANCE REQUIREMENTS ({len(maintenance)}):")
    if maintenance.empty:
        print("   • No maintenance required")
    else:
        for _, maint in maintenance.iterrows():
            print(f"   • {maint.resource_name}: {maint.quantity} ({maint.resource_map})")
    
    conn.close()
    return {
        'building': building.iloc[0],
        'inputs': inputs,
        'outputs': outputs,
        'construction': construction,
        'maintenance': maintenance
    }

def get_map_overview():
    """Get a quick overview of all maps and their production capacity"""
    conn = sqlite3.connect('masterplan_tycoon_clean.db')
    
    query = """
    SELECT 
        m.name as map_name,
        COUNT(DISTINCT b.id) as buildings,
        COUNT(DISTINCT r.id) as resources,
        COUNT(DISTINCT bo.building_id) as producers,
        SUM(bo.output_per_minute) as total_output_per_minute
    FROM maps m
    LEFT JOIN buildings b ON m.id = b.map_id
    LEFT JOIN resources r ON m.id = r.map_id
    LEFT JOIN building_outputs bo ON b.id = bo.building_id
    GROUP BY m.id, m.name
    ORDER BY m.name
    """
    
    overview = pd.read_sql_query(query, conn)
    
    print("🌍 MAP OVERVIEW")
    print("=" * 60)
    for _, row in overview.iterrows():
        print(f"📍 {row.map_name}:")
        print(f"   Buildings: {row.buildings}")
        print(f"   Resources: {row.resources}")
        print(f"   Active Producers: {row.producers}")
        if row.total_output_per_minute:
            print(f"   Total Output/Min: {row.total_output_per_minute:.1f}")
        print()
    
    conn.close()
    return overview

def main():
    """Interactive resource chain explorer"""
    print("🔗 MASTERPLAN TYCOON RESOURCE CHAIN EXPLORER")
    print("=" * 60)
    
    # Quick overview
    print("\n📊 Database Overview:")
    get_map_overview()
    
    # Example resource chain analysis
    print("\n" + "="*80)
    print("🔍 EXAMPLE: Steel Beams Resource Chain")
    get_resource_chain("Steel Beams", "Master")
    
    print("\n" + "="*80)
    print("🏭 EXAMPLE: Steel Mill Building Analysis")
    get_building_analysis("Steel Mill", "Master")
    
    print("\n" + "="*80)
    print("💡 INTERACTIVE MODE")
    print("Try these commands:")
    print("  • get_resource_chain('Resource Name', 'Map Name')")
    print("  • get_building_analysis('Building Name', 'Map Name')")
    print("  • get_map_overview()")

if __name__ == "__main__":
    main()