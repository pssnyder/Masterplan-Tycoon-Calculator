#!/usr/bin/env python3
"""
Resource Chain Dependency Analyzer
Build complete dependency trees from mission requirements to raw resources
"""

import sqlite3
import pandas as pd
from collections import defaultdict, deque
import networkx as nx
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared.config import get_db_connection

def load_database():
    """Load our resource chain database"""
    return get_db_connection()

def build_production_graph():
    """Build a directed graph of all production relationships"""
    conn = load_database()
    
    # Get all building input/output relationships
    query = """
    SELECT 
        b.name as building_name,
        r_in.name as input_resource,
        bi.quantity as input_qty,
        r_out.name as output_resource,
        bo.quantity as output_qty,
        bo.output_per_minute,
        bo.production_time_seconds
    FROM buildings b
    LEFT JOIN building_inputs bi ON b.id = bi.building_id
    LEFT JOIN resources r_in ON bi.resource_id = r_in.id
    LEFT JOIN building_outputs bo ON b.id = bo.building_id  
    LEFT JOIN resources r_out ON bo.resource_id = r_out.id
    WHERE r_in.name IS NOT NULL AND r_out.name IS NOT NULL
    ORDER BY b.name
    """
    
    production_data = pd.read_sql_query(query, conn)
    
    # Build networkx directed graph
    G = nx.DiGraph()
    
    # Add nodes for resources
    all_resources = set(production_data['input_resource'].unique()) | set(production_data['output_resource'].unique())
    for resource in all_resources:
        if pd.notna(resource):
            G.add_node(resource, type='resource')
    
    # Add production relationships as edges
    building_info = {}
    
    for _, row in production_data.iterrows():
        building = row['building_name']
        input_res = row['input_resource'] 
        output_res = row['output_resource']
        
        if pd.notna(input_res) and pd.notna(output_res):
            # Create edge from input to output resource
            G.add_edge(input_res, output_res, 
                      building=building,
                      input_qty=row['input_qty'],
                      output_qty=row['output_qty'],
                      production_rate=row['output_per_minute'],
                      production_time=row['production_time_seconds'])
            
            # Store building info
            if building not in building_info:
                building_info[building] = {
                    'inputs': {},
                    'outputs': {},
                    'production_rate': row['output_per_minute'],
                    'production_time': row['production_time_seconds']
                }
            
            building_info[building]['inputs'][input_res] = row['input_qty']
            building_info[building]['outputs'][output_res] = row['output_qty']
    
    conn.close()
    return G, building_info

def trace_resource_dependencies(graph, target_resource, max_depth=10):
    """Trace all dependencies needed to produce a target resource"""
    print(f"=== DEPENDENCY TREE FOR {target_resource.upper()} ===")
    
    dependencies = defaultdict(set)
    visited = set()
    
    def dfs_dependencies(resource, depth=0, path=None):
        if path is None:
            path = []
        
        if resource in visited or depth > max_depth:
            return
        
        visited.add(resource)
        indent = "  " * depth
        
        # Find all ways to produce this resource
        producers = list(graph.predecessors(resource))
        
        if not producers:
            print(f"{indent}{resource} (RAW MATERIAL)")
            dependencies[depth].add((resource, "raw"))
        else:
            print(f"{indent}{resource}")
            for producer_resource in producers:
                edge_data = graph.get_edge_data(producer_resource, resource)
                building = edge_data['building']
                input_qty = edge_data['input_qty']
                output_qty = edge_data['output_qty']
                rate = edge_data['production_rate']
                
                print(f"{indent}  <- {building} (needs {input_qty} {producer_resource} -> {output_qty} {resource} @ {rate}/min)")
                dependencies[depth].add((resource, building))
                
                # Recursively find dependencies of the input resource
                dfs_dependencies(producer_resource, depth + 1, path + [resource])
    
    dfs_dependencies(target_resource)
    return dependencies

def calculate_production_requirements(target_resources, building_info):
    """Calculate how many of each building type is needed"""
    print("\n=== PRODUCTION REQUIREMENTS CALCULATION ===")
    
    # This is a simplified version - a full solution would need linear programming
    building_requirements = defaultdict(int)
    
    for resource, quantity_needed in target_resources.items():
        print(f"\nFor {quantity_needed} {resource}:")
        
        # Find buildings that produce this resource
        for building_name, info in building_info.items():
            if resource in info['outputs']:
                output_qty = info['outputs'][resource]
                production_rate = info['production_rate']
                
                if production_rate > 0:
                    # Calculate buildings needed based on production rate
                    # This is simplified - doesn't account for production time properly
                    buildings_needed = max(1, quantity_needed / output_qty)
                    building_requirements[building_name] = max(
                        building_requirements[building_name], 
                        int(buildings_needed)
                    )
                    
                    print(f"  {building_name}: need {int(buildings_needed)} buildings")
                    print(f"    (produces {output_qty} per cycle at {production_rate}/min)")
    
    return building_requirements

def analyze_mission_complexity():
    """Analyze the complexity of the full mission requirements"""
    print("\n=== MISSION COMPLEXITY ANALYSIS ===")
    
    # Mission requirements from previous analysis (capitalized to match database)
    mission_requirements = {
        'Beer': 9, 'Bread': 19, 'Brick': 36, 'Clothes': 10,
        'Coal': 9, 'Fish': 10, 'Moonshine': 9, 'Rum': 20,
        'Sausages': 10, 'Steam Engine': 13, 'Steel': 10, 'Water': 5
    }
    
    graph, building_info = build_production_graph()
    
    print(f"Mission requires {len(mission_requirements)} different final products")
    
    all_dependencies = set()
    max_depth = 0
    
    # Trace dependencies for each mission requirement
    for resource, quantity in mission_requirements.items():
        print(f"\n--- Analyzing {resource} (need {quantity}) ---")
        
        if resource in graph:
            dependencies = trace_resource_dependencies(graph, resource, max_depth=5)
            
            # Count total dependencies
            for depth, deps in dependencies.items():
                all_dependencies.update(deps)
                max_depth = max(max_depth, depth)
        else:
            print(f"  {resource} not found in production graph")
    
    print(f"\n=== COMPLEXITY SUMMARY ===")
    print(f"Max dependency depth: {max_depth}")
    print(f"Total unique dependencies: {len(all_dependencies)}")
    print(f"This explains why you needed {len(all_dependencies)} different production elements!")
    
    # Calculate rough building requirements
    building_requirements = calculate_production_requirements(mission_requirements, building_info)
    
    total_buildings_needed = sum(building_requirements.values())
    print(f"\nRough estimate of buildings needed: {total_buildings_needed}")
    print("(This is a simplified calculation - real optimization would be much more complex)")
    
    return mission_requirements, building_requirements

def main():
    """Main dependency analysis"""
    print("🔍 RESOURCE CHAIN DEPENDENCY ANALYZER")
    print("=" * 60)
    
    graph, building_info = build_production_graph()
    
    print(f"Production graph loaded:")
    print(f"  Resources: {len([n for n in graph.nodes() if graph.nodes[n].get('type') == 'resource'])}")
    print(f"  Production relationships: {len(graph.edges())}")
    
    # Example: Trace dependencies for bread (complex item)
    if 'Bread' in graph:
        trace_resource_dependencies(graph, 'Bread')
    
    # Analyze full mission complexity
    analyze_mission_complexity()
    
    print("\n=== MATHEMATICAL APPROACHES NEEDED ===")
    print("1. Multi-level BOM explosion for dependency trees")
    print("2. Mixed Integer Programming for building optimization") 
    print("3. Critical Path Method for construction sequencing")
    print("4. Network flow for resource routing")
    print("5. Constraint satisfaction for complex dependencies")

if __name__ == "__main__":
    main()