#!/usr/bin/env python3
"""
Quick Save Game Insights Generator
"""

import json
import pandas as pd
from collections import Counter

def analyze_save_game():
    print('🔬 SAVE GAME DATA SCIENCE INSIGHTS')
    print('=' * 50)

    with open('game_data_save0.json', 'r') as f:
        data = json.load(f)

    # Player Performance Analysis
    if 'PlayerStatistic' in data:
        stats = data['PlayerStatistic']
        print('📊 PLAYER PERFORMANCE METRICS')
        playtime_hours = stats["SessionSpendTime"]//3600
        playtime_mins = (stats["SessionSpendTime"]%3600)//60
        print(f'Total Playtime: {playtime_hours}h {playtime_mins}m')
        print(f'Resources Extracted: {stats["ResourcesExtracted"]:,}')
        print(f'Buildings Built: {stats["NodesBuilt"]:,}')
        print(f'Resource Efficiency: {stats["ResourcesExtracted"]//stats["NodesBuilt"]:,} resources/building')
        build_success = (1 - stats["NodesDestroyed"]/stats["NodesBuilt"])
        print(f'Build Success Rate: {build_success:.1%}')

    # Building Analysis
    if 'Nodes' in data:
        buildings = data['Nodes']
        print(f'\n🏗️ BUILDING ANALYSIS ({len(buildings)} total)')
        
        # Extract ConfigID instead of BuildingType
        building_types = Counter(node.get('ConfigID', 'Unknown') for node in buildings)
        print('Top Building Types (ConfigID):')
        for building, count in building_types.most_common(10):
            print(f'  • {building}: {count}')

    # Resource Flow Analysis  
    if 'Links' in data:
        links = data['Links']
        print(f'\n🔗 RESOURCE FLOW ANALYSIS ({len(links)} links)')
        
        # Extract StuffTypeID instead of Resource
        resource_flows = Counter(link.get('StuffTypeID', 'Unknown') for link in links)
        print('Most Transported Resources (StuffTypeID):')
        for resource, count in resource_flows.most_common(10):
            print(f'  • {resource}: {count} links')

    # End Game Resource State - handle nested structure
    if 'GlobalStuffStorage' in data and data['GlobalStuffStorage']:
        storage = data['GlobalStuffStorage']
        print(f'\n💰 END-GAME RESOURCE STOCKPILE')
        
        # Storage is organized by location
        for location, resources in storage.items():
            print(f'\n{location} Resources:')
            if isinstance(resources, dict):
                sorted_resources = sorted(resources.items(), key=lambda x: x[1], reverse=True)
                for resource, amount in sorted_resources[:10]:  # Top 10 per location
                    print(f'  • {resource}: {amount:,}')
            else:
                print(f'  • Total: {resources}')

    print('\n✅ Analysis complete! View full dashboard at http://localhost:8502')

if __name__ == "__main__":
    analyze_save_game()