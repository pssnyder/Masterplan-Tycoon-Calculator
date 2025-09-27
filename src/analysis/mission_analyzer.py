#!/usr/bin/env python3
"""
Mission Requirements Analyzer
Parse the save file to understand actual victory conditions and resource targets
"""

import json
import pandas as pd
from collections import defaultdict

def load_save_file():
    """Load the game save file"""
    with open('../references/game_data_save0.json', 'r') as f:
        return json.load(f)

def analyze_mission_requirements(save_data):
    """Extract mission requirements from save file"""
    print("=== MISSION REQUIREMENTS ANALYSIS ===")
    print()
    
    # Look for mission data in different sections
    sections_to_check = ['Missions', 'Researches', 'Nodes']
    
    missions_found = {}
    
    # Check Missions section
    if 'Missions' in save_data:
        print("MISSIONS SECTION FOUND:")
        missions = save_data['Missions']
        
        for key, value in missions.items():
            print(f"  {key}: {value}")
        print()
    
    # Look for mission nodes specifically
    if 'Nodes' in save_data:
        mission_nodes = []
        for node in save_data['Nodes']:
            if 'mission' in node.get('ConfigID', '').lower():
                mission_nodes.append(node)
        
        print(f"MISSION NODES FOUND: {len(mission_nodes)}")
        print()
        
        # Analyze mission node requirements
        for node in mission_nodes[:10]:  # Show first 10 missions
            config_id = node['ConfigID']
            print(f"Mission: {config_id}")
            
            if 'Construction' in node:
                construction = node['Construction']
                
                # Check input requirements
                if 'IncomeStorage' in construction:
                    print("  Required inputs:")
                    for resource, qty in construction['IncomeStorage'].items():
                        clean_resource = resource.replace('stuff.', '')
                        print(f"    {clean_resource}: {qty}")
                
                # Check outputs/rewards
                if 'OutcomeStorage' in construction:
                    print("  Rewards/Outputs:")
                    for resource, qty in construction['OutcomeStorage'].items():
                        clean_resource = resource.replace('stuff.', '')
                        print(f"    {clean_resource}: {qty}")
                
                # Check production uptime (how long it ran)
                if 'ProductionUptime' in construction:
                    uptime_hours = construction['ProductionUptime'] / 3600
                    print(f"  Ran for: {uptime_hours:.1f} hours")
            
            print()
    
    return mission_nodes

def analyze_research_requirements(save_data):
    """Analyze research/tech tree requirements"""
    print("=== RESEARCH REQUIREMENTS ANALYSIS ===")
    print()
    
    if 'Researches' in save_data:
        researches = save_data['Researches']
        print("Research data found:")
        
        # This might contain unlock requirements
        for key, value in researches.items():
            if isinstance(value, dict):
                print(f"  {key}:")
                for subkey, subvalue in value.items():
                    print(f"    {subkey}: {subvalue}")
            else:
                print(f"  {key}: {value}")
        print()
    
    return researches if 'Researches' in save_data else {}

def calculate_actual_victory_cost(mission_nodes):
    """Calculate what resources were actually needed for victory"""
    print("=== ACTUAL VICTORY COST CALCULATION ===")
    print()
    
    total_requirements = defaultdict(int)
    
    for node in mission_nodes:
        if 'Construction' in node and 'IncomeStorage' in node['Construction']:
            for resource, qty in node['Construction']['IncomeStorage'].items():
                clean_resource = resource.replace('stuff.', '')
                total_requirements[clean_resource] += qty
    
    print("TOTAL RESOURCES REQUIRED FOR ALL MISSIONS:")
    for resource, total_qty in sorted(total_requirements.items()):
        print(f"  {resource}: {total_qty}")
    
    print()
    return total_requirements

def compare_requirements_vs_production(total_requirements, current_production):
    """Compare what was needed vs what was produced"""
    print("=== REQUIREMENT vs PRODUCTION COMPARISON ===")
    print()
    
    # Map some common resource names
    resource_mapping = {
        'water': 'Water',
        'fish': 'Fish', 
        'grain': 'Grain',
        'coal': 'Coal',
        'iron': 'Iron',
        'stone': 'Stone',
        'tree': 'Tree',
        'plank': 'Plank'
    }
    
    print("OVERPRODUCTION ANALYSIS:")
    print(f"{'Resource':<15} {'Required':<10} {'Produced/Min':<12} {'Overproduction':<15}")
    print("-" * 60)
    
    for req_resource, required_qty in total_requirements.items():
        # Try to find matching production
        production_rate = 0
        
        for mapped_name in [req_resource, req_resource.title(), resource_mapping.get(req_resource.lower(), '')]:
            if mapped_name in current_production:
                production_rate = current_production[mapped_name]
                break
        
        if production_rate > 0:
            # Assume missions took 1 hour total to complete (rough estimate)
            # So required rate would be required_qty per hour = required_qty/60 per minute
            required_rate = required_qty / 60  # Convert to per-minute
            
            if required_rate > 0:
                overproduction = (production_rate / required_rate) * 100
                print(f"{req_resource:<15} {required_qty:<10} {production_rate:<12.1f} {overproduction:<15.0f}%")
            else:
                print(f"{req_resource:<15} {required_qty:<10} {production_rate:<12.1f} {'N/A':<15}")
    
    print()

def main():
    """Main analysis function"""
    print("🎯 VICTORY CONDITIONS & REQUIREMENTS ANALYZER")
    print("=" * 60)
    
    save_data = load_save_file()
    
    # Analyze mission requirements
    mission_nodes = analyze_mission_requirements(save_data)
    
    # Analyze research requirements  
    researches = analyze_research_requirements(save_data)
    
    # Calculate total victory cost
    total_requirements = calculate_actual_victory_cost(mission_nodes)
    
    # Compare with current production (from previous analysis)
    # This is a simplified version - in reality we'd want to load the full production analysis
    estimated_current_production = {
        'Water': 480,
        'Fish': 180,
        'Grain': 133,
        'Coal': 44,
        'Iron': 36,
        'Stone': 52
    }
    
    compare_requirements_vs_production(total_requirements, estimated_current_production)
    
    print("=== NEXT STEPS ===")
    print("1. Use this data to calculate optimal building counts")
    print("2. Design phased construction strategy") 
    print("3. Create spatial organization plan")
    print("4. Generate optimized save file")

if __name__ == "__main__":
    main()