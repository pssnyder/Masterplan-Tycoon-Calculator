#!/usr/bin/env python3
"""
Fun Game Detective - Analyze your Masterplan Tycoon gameplay patterns!
"""

import json
import pandas as pd
from collections import defaultdict, Counter
import sqlite3

def load_save_file():
    """Load the game save file"""
    with open('../references/game_data_save0.json', 'r') as f:
        return json.load(f)

def game_stats_summary(save_data):
    """Fun summary of your gaming achievement"""
    print("=== MASTERPLAN TYCOON GAME DETECTIVE ===")
    print()
    
    stats = save_data['PlayerStatistic']
    print(f"YOUR GAMING MARATHON:")
    print(f"  Time Played: {stats['SessionSpendTime']/3600:.1f} hours")
    print(f"  Buildings Built: {stats['NodesBuilt']:,}")
    print(f"  Buildings per Hour: {stats['NodesBuilt']/(stats['SessionSpendTime']/3600):.1f}")
    print(f"  Resources Mined: {stats['ResourcesExtracted']:,}")
    print(f"  Links Created: {stats['LinksCreated']:,}")
    print()

def analyze_your_building_obsessions(save_data):
    """Find your favorite buildings and weird patterns"""
    print("YOUR BUILDING OBSESSIONS:")
    print("-" * 40)
    
    nodes = save_data['Nodes']
    building_counts = Counter()
    
    for node in nodes:
        config_id = node['ConfigID']
        # Clean up the name
        clean_name = config_id.replace('construction.', '').replace('mountains.', '').replace('islands.', '')
        building_counts[clean_name] += 1
    
    print("Top 10 Buildings You Love Most:")
    for i, (building, count) in enumerate(building_counts.most_common(10), 1):
        print(f"  {i:2d}. {building}: {count} buildings")
    
    print()
    print("INTERESTING PATTERNS:")
    
    # Storage addiction analysis
    storage_total = building_counts.get('storage', 0) + building_counts.get('mountains.storage', 0) + building_counts.get('islands.storage', 0)
    total_buildings = sum(building_counts.values())
    storage_percent = (storage_total / total_buildings) * 100
    
    print(f"  Storage Addiction Level: {storage_percent:.1f}% of your buildings are storage!")
    if storage_percent > 20:
        print("    ^ You REALLY love your storage buildings!")
    
    # Well obsession
    well_count = building_counts.get('well', 0) + building_counts.get('mountains.well', 0)
    print(f"  Water Security: {well_count} wells (you'll never be thirsty!)")
    
    return building_counts

def analyze_resource_flows(save_data):
    """Analyze what resources you're hoarding"""
    print()
    print("RESOURCE HOARDING ANALYSIS:")
    print("-" * 40)
    
    nodes = save_data['Nodes']
    resource_storage = Counter()
    
    for node in nodes:
        if 'Construction' in node:
            construction = node['Construction']
            
            # Count stored resources
            for storage_type in ['IncomeStorage', 'OutcomeStorage']:
                if storage_type in construction:
                    for resource, quantity in construction[storage_type].items():
                        clean_resource = resource.replace('stuff.', '')
                        resource_storage[clean_resource] += quantity
    
    print("Your Top 10 Stockpiled Resources:")
    for i, (resource, amount) in enumerate(resource_storage.most_common(10), 1):
        print(f"  {i:2d}. {resource}: {amount:,} units")
    
    return resource_storage

def find_interesting_buildings(save_data):
    """Find your most interesting building placements"""
    print()
    print("INTERESTING BUILDING DISCOVERIES:")
    print("-" * 40)
    
    nodes = save_data['Nodes']
    
    # Find buildings with interesting properties
    massive_producers = []
    isolated_buildings = []
    
    for node in nodes:
        if 'Construction' in node:
            construction = node['Construction']
            pos = node.get('Position', {'X': 0, 'Y': 0})
            
            # Find massive producers
            if 'ProductionUptime' in construction:
                uptime_hours = construction['ProductionUptime'] / 3600
                if uptime_hours > 100:  # Buildings running for 100+ hours
                    clean_name = node['ConfigID'].replace('construction.', '')
                    massive_producers.append((clean_name, uptime_hours, pos))
    
    if massive_producers:
        print("Your Hardest Working Buildings (100+ hours of production):")
        for name, hours, pos in sorted(massive_producers, key=lambda x: x[1], reverse=True)[:5]:
            print(f"  {name}: {hours:.1f} hours at ({pos['X']:.0f}, {pos['Y']:.0f})")
    
    return massive_producers

def compare_to_database(save_data):
    """Compare your actual game to our database"""
    print()
    print("HOW YOU PLAYED VS. GAME DATA:")
    print("-" * 40)
    
    # Quick database comparison
    conn = sqlite3.connect('masterplan_tycoon_clean.db')
    
    # Get total possible buildings
    total_buildings_query = "SELECT COUNT(*) as count FROM buildings"
    total_possible = pd.read_sql_query(total_buildings_query, conn).iloc[0]['count']
    
    # Get your actual building count
    nodes = save_data['Nodes']
    your_building_count = len([n for n in nodes if 'construction.' in n.get('ConfigID', '')])
    
    print(f"Buildings in game database: {total_possible}")
    print(f"Buildings you actually used: {your_building_count}")
    print(f"You used {(your_building_count/total_possible)*100:.1f}% of available building types!")
    
    conn.close()

def main():
    """Main fun analysis"""
    try:
        save_data = load_save_file()
        
        game_stats_summary(save_data)
        building_counts = analyze_your_building_obsessions(save_data)
        resource_storage = analyze_resource_flows(save_data)
        interesting_buildings = find_interesting_buildings(save_data)
        compare_to_database(save_data)
        
        print()
        print("=== READY FOR MORE FUN ANALYSIS? ===")
        print("Try these:")
        print("  1. Spatial analysis - Where did you build everything?")
        print("  2. Efficiency analysis - How good were your ratios?")
        print("  3. AI optimization - Can AI beat your strategy?")
        
    except UnicodeEncodeError:
        print("Note: Some fancy characters might not display properly on Windows")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()