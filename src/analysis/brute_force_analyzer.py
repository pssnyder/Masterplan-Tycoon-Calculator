#!/usr/bin/env python3
"""
Brute Force vs Strategy Analyzer
Find where Patrick went "just build more buildings" instead of optimizing ratios
"""

import json
import pandas as pd
from collections import defaultdict, Counter
import sqlite3

def load_save_file():
    """Load the game save file"""
    with open('../references/game_data_save0.json', 'r') as f:
        return json.load(f)

def analyze_production_chains(save_data):
    """Analyze actual production rates vs needs"""
    print("=== BRUTE FORCE vs STRATEGY ANALYSIS ===")
    print()
    
    # Load database to get production rates
    conn = sqlite3.connect('masterplan_tycoon_clean.db')
    
    # Get building output rates from database
    output_rates_query = """
    SELECT 
        b.name as building_name,
        r.name as resource_name,
        bo.output_per_minute,
        bo.quantity as output_qty,
        bo.production_time_seconds
    FROM building_outputs bo
    JOIN buildings b ON bo.building_id = b.id
    JOIN resources r ON bo.resource_id = r.id
    ORDER BY b.name, r.name
    """
    db_output_rates = pd.read_sql_query(output_rates_query, conn)
    
    # Get building input requirements
    input_rates_query = """
    SELECT 
        b.name as building_name,
        r.name as resource_name,
        bi.quantity as input_qty
    FROM building_inputs bi
    JOIN buildings b ON bi.building_id = b.id
    JOIN resources r ON bi.resource_id = r.id
    ORDER BY b.name, r.name
    """
    db_input_rates = pd.read_sql_query(input_rates_query, conn)
    conn.close()
    
    # Count buildings in save file
    nodes = save_data['Nodes']
    building_counts = Counter()
    
    for node in nodes:
        config_id = node['ConfigID']
        if config_id.startswith('construction.'):
            # Clean up building name for matching
            clean_name = config_id.replace('construction.', '')
            clean_name = clean_name.replace('mountains.', '').replace('islands.', '')
            building_counts[clean_name] += 1
    
    print("YOUR ACTUAL PRODUCTION ANALYSIS:")
    print("-" * 50)
    
    # Calculate total production for key resources
    resource_production = defaultdict(float)
    resource_consumption = defaultdict(float)
    building_analysis = []
    
    # Map save file building names to database names (simple mapping for common ones)
    building_name_map = {
        'well': 'Well',
        'farm': 'Farm', 
        'sawmill': 'Sawmill',
        'lumbercamp': 'Lumbercamp',
        'fishery': 'Fishery',
        'quarry': 'Quarry',
        'coalmine': 'Coal Mine',
        'ironmine': 'Iron Mine',
        'furnace': 'Furnace',
        'barleyfarm': 'Barley Farm'
    }
    
    print("POTENTIAL OVERPRODUCTION ANALYSIS:")
    print()
    
    for save_building, count in building_counts.most_common(15):
        if save_building in building_name_map:
            db_building = building_name_map[save_building]
            
            # Get outputs for this building type
            building_outputs = db_output_rates[db_output_rates['building_name'] == db_building]
            
            if not building_outputs.empty:
                print(f"{save_building.upper()} ANALYSIS:")
                print(f"  You have: {count} buildings")
                
                for _, output_row in building_outputs.iterrows():
                    resource = output_row['resource_name']
                    rate_per_building = output_row['output_per_minute']
                    total_production = count * rate_per_building
                    
                    resource_production[resource] += total_production
                    
                    print(f"  Produces: {resource}")
                    print(f"    Per building: {rate_per_building:.1f}/min")
                    print(f"    Total production: {total_production:,.1f}/min")
                    
                    # Flag potential overproduction
                    if total_production > 1000:  # Arbitrary high threshold
                        print(f"    ⚠️  POTENTIAL OVERPRODUCTION! That's A LOT of {resource}")
                    
                    building_analysis.append({
                        'building_type': save_building,
                        'count': count,
                        'resource': resource,
                        'rate_per_building': rate_per_building,
                        'total_production': total_production
                    })
                print()
    
    return resource_production, building_analysis

def find_brute_force_indicators(building_analysis):
    """Find signs of brute force building"""
    print("BRUTE FORCE INDICATORS:")
    print("-" * 30)
    
    # Sort by total production to find extreme cases
    sorted_analysis = sorted(building_analysis, key=lambda x: x['total_production'], reverse=True)
    
    print("TOP 10 HIGHEST PRODUCTION RATES:")
    for i, item in enumerate(sorted_analysis[:10], 1):
        print(f"{i:2d}. {item['resource']}: {item['total_production']:,.0f}/min")
        print(f"    ({item['count']} {item['building_type']} buildings)")
        
        # Calculate if this seems excessive
        if item['total_production'] > 5000:
            print(f"    🚨 BRUTE FORCE ALERT: This seems excessive!")
        elif item['total_production'] > 1000:
            print(f"    ⚠️  High production - might be overkill")
        print()

def analyze_resource_ratios(resource_production):
    """Analyze if resource production ratios make sense"""
    print("RESOURCE RATIO ANALYSIS:")
    print("-" * 25)
    
    # Some known resource relationships from the game
    interesting_ratios = [
        ('Water', 'Grain', 'Farms need water'),
        ('Tree', 'Plank', 'Sawmills convert trees to planks'),
        ('Coal', 'Iron', 'Furnaces need both for steel'),
        ('Stone', 'Brick', 'Stone becomes brick')
    ]
    
    for resource1, resource2, relationship in interesting_ratios:
        prod1 = resource_production.get(resource1, 0)
        prod2 = resource_production.get(resource2, 0)
        
        if prod1 > 0 and prod2 > 0:
            ratio = prod1 / prod2
            print(f"{resource1} vs {resource2}: {ratio:.2f}:1 ratio")
            print(f"  {relationship}")
            
            if ratio > 10:
                print(f"  🚨 MASSIVE OVERPRODUCTION of {resource1}!")
            elif ratio > 3:
                print(f"  ⚠️  Overproducing {resource1}")
            elif ratio < 0.3:
                print(f"  ⚠️  Underproducing {resource1}")
            print()

def compare_to_victory_requirements():
    """Estimate what's actually needed to win"""
    print("VICTORY REQUIREMENTS ESTIMATE:")
    print("-" * 30)
    
    # These are rough estimates based on typical tycoon game patterns
    # In reality, we'd need to analyze the mission requirements from the save file
    estimated_needs = {
        'Water': 50,    # per minute, basic need
        'Food': 20,     # per minute, population
        'Wood/Planks': 30,  # per minute, construction
        'Stone': 25,    # per minute, construction
        'Coal': 15,     # per minute, industry
        'Iron': 10,     # per minute, industry
        'Steel': 5      # per minute, advanced items
    }
    
    print("Rough estimates of what you might actually need:")
    for resource, estimated_need in estimated_needs.items():
        print(f"  {resource}: ~{estimated_need}/min estimated need")
    
    print("\nNOTE: These are very rough estimates!")
    print("The real analysis would require parsing mission objectives")

def main():
    """Main analysis function"""
    print("🔍 PATRICK'S BRUTE FORCE vs STRATEGY ANALYZER")
    print("=" * 60)
    
    save_data = load_save_file()
    
    resource_production, building_analysis = analyze_production_chains(save_data)
    find_brute_force_indicators(building_analysis)
    analyze_resource_ratios(resource_production)
    compare_to_victory_requirements()
    
    print("\n=== SUMMARY ===")
    print("This analysis helps identify where you might have")
    print("'brute forced' solutions by building many buildings")
    print("instead of optimizing production ratios!")

if __name__ == "__main__":
    main()