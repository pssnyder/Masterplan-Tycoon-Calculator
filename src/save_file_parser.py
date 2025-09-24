#!/usr/bin/env python3
"""
Save File Parser - Analyze the Masterplan Tycoon save file structure
"""

import json
import pandas as pd
from collections import defaultdict, Counter
import sqlite3

def load_save_file():
    """Load the game save file"""
    with open('../references/game_data_save0.json', 'r') as f:
        return json.load(f)

def analyze_save_structure(save_data):
    """Analyze the basic structure of the save file"""
    print("📊 SAVE FILE STRUCTURE ANALYSIS")
    print("=" * 60)
    
    print(f"🎮 Game Info:")
    print(f"   Version: {save_data['System']['Version']}")
    print(f"   Map Seed: {save_data['System']['MapSeed']}")
    
    stats = save_data['PlayerStatistic']
    print(f"\n📈 Player Stats:")
    print(f"   Nodes Built: {stats['NodesBuilt']:,}")
    print(f"   Links Created: {stats['LinksCreated']:,}")
    print(f"   Resources Extracted: {stats['ResourcesExtracted']:,}")
    print(f"   Session Time: {stats['SessionSpendTime']:,} seconds ({stats['SessionSpendTime']/3600:.1f} hours)")
    
    print(f"\n🗺️ Locations:")
    for location, camera in save_data['Missions']['CameraLocationData'].items():
        print(f"   {location}: Position({camera['Position']['X']:.1f}, {camera['Position']['Y']:.1f}) Size: {camera['Size']:.1f}")

def analyze_nodes(save_data):
    """Analyze all nodes in the save file"""
    print("\n🏗️ NODE ANALYSIS")
    print("=" * 60)
    
    nodes = save_data['Nodes']
    print(f"Total Nodes: {len(nodes)}")
    
    # Count node types by ConfigID
    config_counts = Counter()
    position_data = []
    construction_data = []
    
    for node in nodes:
        config_id = node['ConfigID']
        config_counts[config_id] += 1
        
        # Collect position data
        pos = node.get('Position', {})
        position_data.append({
            'ID': node['ID'],
            'ConfigID': config_id,
            'X': pos.get('X', 0.0),
            'Y': pos.get('Y', 0.0)
        })
        
        # Analyze construction data if available
        if 'Construction' in node:
            construction = node['Construction']
            construction_entry = {
                'ID': node['ID'],
                'ConfigID': config_id,
                'X': pos.get('X', 0.0),
                'Y': pos.get('Y', 0.0),
                'has_income_storage': 'IncomeStorage' in construction,
                'has_outcome_storage': 'OutcomeStorage' in construction,
                'has_active_recipe': 'ActiveRecipe' in construction,
                'maintenance_time': construction.get('MaintenanceTimeLeft', 0),
                'production_uptime': construction.get('ProductionUptime', 0)
            }
            
            # Count input/output resources
            if 'IncomeStorage' in construction:
                construction_entry['income_resources'] = list(construction['IncomeStorage'].keys())
                construction_entry['income_count'] = len(construction['IncomeStorage'])
            else:
                construction_entry['income_resources'] = []
                construction_entry['income_count'] = 0
            
            if 'OutcomeStorage' in construction:
                construction_entry['outcome_resources'] = list(construction['OutcomeStorage'].keys())
                construction_entry['outcome_count'] = len(construction['OutcomeStorage'])
            else:
                construction_entry['outcome_resources'] = []
                construction_entry['outcome_count'] = 0
            
            construction_data.append(construction_entry)
    
    print(f"\n🏭 Top 20 Building Types:")
    for config_id, count in config_counts.most_common(20):
        print(f"   {config_id}: {count}")
    
    # Create dataframes for analysis
    positions_df = pd.DataFrame(position_data)
    construction_df = pd.DataFrame(construction_data)
    
    return {
        'config_counts': config_counts,
        'positions_df': positions_df,
        'construction_df': construction_df,
        'total_nodes': len(nodes)
    }

def analyze_building_types(node_analysis):
    """Analyze building types and categorize them"""
    print(f"\n🔍 BUILDING TYPE ANALYSIS")
    print("=" * 60)
    
    config_counts = node_analysis['config_counts']
    
    # Categorize building types
    categories = {
        'missions': [],
        'storage': [],
        'ports': [], 
        'production': [],
        'special': []
    }
    
    for config_id, count in config_counts.items():
        if 'mission' in config_id:
            categories['missions'].append((config_id, count))
        elif 'storage' in config_id:
            categories['storage'].append((config_id, count))
        elif 'port' in config_id:
            categories['ports'].append((config_id, count))
        elif config_id.startswith('construction.') and not any(x in config_id for x in ['mission', 'storage', 'port']):
            categories['production'].append((config_id, count))
        else:
            categories['special'].append((config_id, count))
    
    for category, buildings in categories.items():
        if buildings:
            print(f"\n📂 {category.upper()} ({len(buildings)}):")
            for config_id, count in sorted(buildings, key=lambda x: x[1], reverse=True)[:10]:
                # Clean up the config_id for display
                clean_name = config_id.replace('construction.', '').replace('.', ' ').title()
                print(f"   {clean_name}: {count}")
    
    return categories

def map_config_to_buildings(node_analysis):
    """Try to map save file ConfigIDs to our database building names"""
    print(f"\n🗺️ MAPPING CONFIG IDS TO DATABASE")
    print("=" * 60)
    
    # Load our database to get building names
    conn = sqlite3.connect('masterplan_tycoon_clean.db')
    
    # Get all building names from database
    buildings_query = """
    SELECT DISTINCT b.name as building_name, m.name as map_name
    FROM buildings b
    JOIN maps m ON b.map_id = m.id
    ORDER BY b.name
    """
    db_buildings = pd.read_sql_query(buildings_query, conn)
    conn.close()
    
    print(f"Database has {len(db_buildings)} unique buildings")
    
    # Try to match ConfigIDs to building names
    config_counts = node_analysis['config_counts']
    
    matches = []
    unmatched_configs = []
    
    for config_id, count in config_counts.items():
        # Clean up config_id
        clean_config = config_id.replace('construction.', '').replace('.', ' ')
        
        # Try various matching strategies
        matched = False
        
        # Strategy 1: Direct name matching (case insensitive)
        for _, row in db_buildings.iterrows():
            building_name = row['building_name'].lower()
            if clean_config.lower() in building_name or building_name in clean_config.lower():
                matches.append({
                    'config_id': config_id,
                    'count': count,
                    'building_name': row['building_name'],
                    'map_name': row['map_name'],
                    'match_type': 'direct_name'
                })
                matched = True
                break
        
        # Strategy 2: Partial keyword matching
        if not matched:
            keywords = clean_config.lower().split()
            for _, row in db_buildings.iterrows():
                building_name = row['building_name'].lower()
                if any(keyword in building_name for keyword in keywords if len(keyword) > 2):
                    matches.append({
                        'config_id': config_id,
                        'count': count,
                        'building_name': row['building_name'],
                        'map_name': row['map_name'],
                        'match_type': 'keyword'
                    })
                    matched = True
                    break
        
        if not matched:
            unmatched_configs.append((config_id, count))
    
    matches_df = pd.DataFrame(matches)
    
    print(f"\n✅ MATCHED CONFIGS ({len(matches)}):")
    if not matches_df.empty:
        for _, row in matches_df.head(15).iterrows():
            print(f"   {row['config_id']} → {row['building_name']} ({row['map_name']}) [{row['count']}]")
    
    print(f"\n❌ UNMATCHED CONFIGS ({len(unmatched_configs)}):")
    for config_id, count in sorted(unmatched_configs, key=lambda x: x[1], reverse=True)[:15]:
        clean_name = config_id.replace('construction.', '')
        print(f"   {clean_name}: {count}")
    
    return matches_df, unmatched_configs

def analyze_resource_flows(save_data, node_analysis):
    """Analyze resource flows in the save file"""
    print(f"\n💧 RESOURCE FLOW ANALYSIS")
    print("=" * 60)
    
    nodes = save_data['Nodes']
    
    # Count all resources mentioned
    resource_counts = Counter()
    production_data = []
    
    for node in nodes:
        if 'Construction' in node:
            construction = node['Construction']
            
            # Count input resources
            if 'IncomeStorage' in construction:
                for resource, quantity in construction['IncomeStorage'].items():
                    resource_counts[resource] += quantity
                    production_data.append({
                        'node_id': node['ID'],
                        'config_id': node['ConfigID'],
                        'resource': resource,
                        'quantity': quantity,
                        'flow_type': 'input'
                    })
            
            # Count output resources
            if 'OutcomeStorage' in construction:
                for resource, quantity in construction['OutcomeStorage'].items():
                    resource_counts[resource] += quantity
                    production_data.append({
                        'node_id': node['ID'],
                        'config_id': node['ConfigID'],
                        'resource': resource,
                        'quantity': quantity,
                        'flow_type': 'output'
                    })
    
    print(f"📦 Top 20 Resources by Volume:")
    for resource, count in resource_counts.most_common(20):
        clean_resource = resource.replace('stuff.', '')
        print(f"   {clean_resource}: {count}")
    
    production_df = pd.DataFrame(production_data)
    
    return {
        'resource_counts': resource_counts,
        'production_df': production_df
    }

def main():
    """Main analysis function"""
    print("🔍 MASTERPLAN TYCOON SAVE FILE ANALYSIS")
    print("=" * 80)
    
    # Load save file
    save_data = load_save_file()
    
    # Basic structure analysis
    analyze_save_structure(save_data)
    
    # Node analysis
    node_analysis = analyze_nodes(save_data)
    
    # Building type analysis
    building_categories = analyze_building_types(node_analysis)
    
    # Try to map to our database
    matches_df, unmatched = map_config_to_buildings(node_analysis)
    
    # Resource flow analysis
    resource_analysis = analyze_resource_flows(save_data, node_analysis)
    
    print(f"\n🎯 ANALYSIS SUMMARY")
    print("=" * 40)
    print(f"Total Nodes: {node_analysis['total_nodes']}")
    print(f"Unique Building Types: {len(node_analysis['config_counts'])}")
    print(f"Matched to Database: {len(matches_df) if not matches_df.empty else 0}")
    print(f"Unmatched Configs: {len(unmatched)}")
    print(f"Unique Resources: {len(resource_analysis['resource_counts'])}")
    
    return {
        'save_data': save_data,
        'node_analysis': node_analysis,
        'building_categories': building_categories,
        'matches_df': matches_df,
        'unmatched': unmatched,
        'resource_analysis': resource_analysis
    }

if __name__ == "__main__":
    analysis_results = main()