#!/usr/bin/env python3
"""
Data Validation and Quality Analysis Tool

Identifies data quality issues, missing connections, logical inconsistencies,
and potential calculation breakers in the Masterplan Tycoon database.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.config import get_db_connection
import pandas as pd
import networkx as nx
from collections import defaultdict, Counter
import json

class DataValidator:
    def __init__(self):
        self.conn = get_db_connection()
        self.issues = defaultdict(list)
        self.warnings = defaultdict(list)
        self.stats = {}
        
    def load_data(self):
        """Load all relevant data for validation"""
        print("🔍 Loading data for validation...")
        
        # Core tables with proper joins
        self.buildings = pd.read_sql("""
            SELECT b.*, m.name as map_name 
            FROM buildings b 
            LEFT JOIN maps m ON b.map_id = m.id
        """, self.conn)
        
        self.resources = pd.read_sql("""
            SELECT r.*, m.name as map_name 
            FROM resources r 
            LEFT JOIN maps m ON r.map_id = m.id
        """, self.conn)
        
        self.maps = pd.read_sql("SELECT * FROM maps", self.conn)
        
        # Relationship tables
        self.building_inputs = pd.read_sql("SELECT * FROM building_inputs", self.conn)
        self.building_outputs = pd.read_sql("SELECT * FROM building_outputs", self.conn)
        self.building_construction = pd.read_sql("SELECT * FROM building_construction", self.conn)
        self.building_maintenance = pd.read_sql("SELECT * FROM building_maintenance", self.conn)
        
        print(f"  📊 Loaded: {len(self.buildings)} buildings, {len(self.resources)} resources")
        
    def validate_building_connections(self):
        """Check for buildings with missing or problematic input/output connections"""
        print("\n🔗 Validating building connections...")
        
        # Buildings with no inputs or outputs
        building_ids = set(self.buildings['id'])
        input_building_ids = set(self.building_inputs['building_id'])
        output_building_ids = set(self.building_outputs['building_id'])
        
        no_inputs = building_ids - input_building_ids
        no_outputs = building_ids - output_building_ids
        
        # Get building names for these IDs
        no_input_buildings = self.buildings[self.buildings['id'].isin(no_inputs)]['name'].tolist()
        no_output_buildings = self.buildings[self.buildings['id'].isin(no_outputs)]['name'].tolist()
        
        self.warnings['no_inputs'] = no_input_buildings
        self.warnings['no_outputs'] = no_output_buildings
        
        print(f"  ⚠️  Buildings with no inputs: {len(no_input_buildings)}")
        print(f"  ⚠️  Buildings with no outputs: {len(no_output_buildings)}")
        
        # Check for potential ports (buildings with specific patterns)
        port_keywords = ['port', 'dock', 'pier', 'harbor', 'ferry']
        potential_ports = []
        
        for _, building in self.buildings.iterrows():
            if any(keyword in building['name'].lower() for keyword in port_keywords):
                potential_ports.append({
                    'name': building['name'],
                    'map': building['map_name'],
                    'has_inputs': building['id'] in input_building_ids,
                    'has_outputs': building['id'] in output_building_ids
                })
        
        self.stats['potential_ports'] = potential_ports
        print(f"  🚢 Potential port buildings identified: {len(potential_ports)}")
        
        return no_input_buildings, no_output_buildings, potential_ports
    
    def validate_resource_chains(self):
        """Check for broken resource chains and circular dependencies"""
        print("\n🔄 Validating resource chains...")
        
        # Build production graph
        G = nx.DiGraph()
        
        # Add all resources as nodes
        for _, resource in self.resources.iterrows():
            G.add_node(resource['name'], type='resource', map=resource['map_name'])
        
        # Add production relationships as edges
        production_query = """
        SELECT 
            r_in.name as input_resource,
            r_out.name as output_resource,
            b.name as building_name,
            bo.output_per_minute,
            bi.quantity as input_qty,
            bo.quantity as output_qty
        FROM buildings b
        JOIN building_inputs bi ON b.id = bi.building_id
        JOIN building_outputs bo ON b.id = bo.building_id
        JOIN resources r_in ON bi.resource_id = r_in.id
        JOIN resources r_out ON bo.resource_id = r_out.id
        """
        
        production_data = pd.read_sql(production_query, self.conn)
        
        for _, row in production_data.iterrows():
            G.add_edge(
                row['input_resource'], 
                row['output_resource'],
                building=row['building_name'],
                rate=row['output_per_minute'],
                input_qty=row['input_qty'],
                output_qty=row['output_qty']
            )
        
        # Check for circular dependencies
        try:
            cycles = list(nx.simple_cycles(G))
            self.issues['circular_dependencies'] = cycles
            print(f"  🔄 Circular dependencies found: {len(cycles)}")
            
            if cycles:
                print("     Sample cycles:")
                for i, cycle in enumerate(cycles[:3]):  # Show first 3
                    print(f"       {i+1}. {' → '.join(cycle)} → {cycle[0]}")
                    
        except Exception as e:
            print(f"  ❌ Error checking cycles: {e}")
        
        # Check for isolated resources (no producers or consumers)
        isolated_resources = []
        for resource in self.resources['name']:
            if resource not in G.nodes():
                isolated_resources.append(resource)
            else:
                in_deg = len(list(G.predecessors(resource)))
                out_deg = len(list(G.successors(resource)))
                if in_deg == 0 and out_deg == 0:
                    isolated_resources.append(resource)
        
        self.warnings['isolated_resources'] = isolated_resources
        print(f"  ⚠️  Isolated resources: {len(isolated_resources)}")
        
        # Check for resources with no producers (should be raw materials)
        no_producers = []
        for resource in G.nodes():
            in_degree = len(list(G.predecessors(resource)))
            out_degree = len(list(G.successors(resource)))
            if in_degree == 0 and out_degree > 0:
                no_producers.append(resource)
        
        self.stats['raw_materials'] = no_producers
        print(f"  🏭 Raw materials (no producers): {len(no_producers)}")
        
        return G, cycles, isolated_resources, no_producers
    
    def validate_construction_maintenance(self):
        """Check for buildings missing construction or maintenance data"""
        print("\n🏗️ Validating construction and maintenance data...")
        
        building_ids = set(self.buildings['id'])
        construction_building_ids = set(self.building_construction['building_id'])
        maintenance_building_ids = set(self.building_maintenance['building_id'])
        
        no_construction = building_ids - construction_building_ids
        no_maintenance = building_ids - maintenance_building_ids
        
        # Get building names
        no_construction_names = self.buildings[self.buildings['id'].isin(no_construction)]['name'].tolist()
        no_maintenance_names = self.buildings[self.buildings['id'].isin(no_maintenance)]['name'].tolist()
        
        self.warnings['no_construction_data'] = no_construction_names
        self.warnings['no_maintenance_data'] = no_maintenance_names
        
        print(f"  ⚠️  Buildings missing construction data: {len(no_construction_names)}")
        print(f"  ⚠️  Buildings missing maintenance data: {len(no_maintenance_names)}")
        
        # Check for zero-cost construction or maintenance (might be valid for ports)
        zero_construction = []
        zero_maintenance = []
        
        # Buildings with zero construction costs
        construction_costs = pd.read_sql("""
            SELECT b.name, COUNT(bc.resource_id) as cost_items
            FROM buildings b
            LEFT JOIN building_construction bc ON b.id = bc.building_id
            GROUP BY b.id, b.name
            HAVING cost_items = 0
        """, self.conn)
        
        zero_construction = construction_costs['name'].tolist()
        
        # Buildings with zero maintenance costs
        maintenance_costs = pd.read_sql("""
            SELECT b.name, COUNT(bm.resource_id) as maintenance_items
            FROM buildings b
            LEFT JOIN building_maintenance bm ON b.id = bm.building_id
            GROUP BY b.id, b.name
            HAVING maintenance_items = 0
        """, self.conn)
        
        zero_maintenance = maintenance_costs['name'].tolist()
        
        self.stats['zero_construction_cost'] = zero_construction
        self.stats['zero_maintenance_cost'] = zero_maintenance
        
        print(f"  💰 Buildings with zero construction cost: {len(zero_construction)}")
        print(f"  💰 Buildings with zero maintenance cost: {len(zero_maintenance)}")
        
        return no_construction_names, no_maintenance_names
    
    def detect_calculation_breakers(self):
        """Identify patterns that could break optimization calculations"""
        print("\n💥 Detecting potential calculation breakers...")
        
        breakers = {
            'extremely_high_ratios': [],
            'zero_production_rates': [],
            'missing_rate_data': [],
            'potential_infinite_loops': []
        }
        
        # Check for extremely high input/output ratios
        ratio_query = """
        SELECT 
            b.name as building,
            r_in.name as input_resource,
            r_out.name as output_resource,
            bi.quantity as input_qty,
            bo.quantity as output_qty,
            bo.output_per_minute,
            (bi.quantity * 1.0 / bo.quantity) as input_output_ratio
        FROM buildings b
        JOIN building_inputs bi ON b.id = bi.building_id
        JOIN building_outputs bo ON b.id = bo.building_id
        JOIN resources r_in ON bi.resource_id = r_in.id
        JOIN resources r_out ON bo.resource_id = r_out.id
        WHERE (bi.quantity * 1.0 / bo.quantity) > 10  -- Ratios higher than 10:1
        """
        
        high_ratios = pd.read_sql(ratio_query, self.conn)
        breakers['extremely_high_ratios'] = high_ratios.to_dict('records')
        
        # Check for zero or missing production rates
        zero_rates = pd.read_sql("""
            SELECT b.name, r.name as resource, bo.output_per_minute
            FROM buildings b
            JOIN building_outputs bo ON b.id = bo.building_id
            JOIN resources r ON bo.resource_id = r.id
            WHERE bo.output_per_minute = 0 OR bo.output_per_minute IS NULL
        """, self.conn)
        
        breakers['zero_production_rates'] = zero_rates.to_dict('records')
        
        # Check for buildings that might create infinite demand
        # (buildings that consume their own outputs)
        self_consumers = pd.read_sql("""
            SELECT DISTINCT b.name as building,
                   r.name as resource
            FROM buildings b
            JOIN building_inputs bi ON b.id = bi.building_id
            JOIN building_outputs bo ON b.id = bo.building_id
            JOIN resources r ON bi.resource_id = r.id
            WHERE bi.resource_id = bo.resource_id
        """, self.conn)
        
        breakers['self_consumers'] = self_consumers.to_dict('records')
        
        print(f"  ⚠️  High input/output ratios (>10:1): {len(breakers['extremely_high_ratios'])}")
        print(f"  ⚠️  Zero production rates: {len(breakers['zero_production_rates'])}")
        print(f"  ⚠️  Self-consuming buildings: {len(breakers['self_consumers'])}")
        
        return breakers
    
    def analyze_map_connectivity(self):
        """Analyze connections between maps and potential port logic"""
        print("\n🗺️ Analyzing map connectivity...")
        
        # Get buildings by map
        map_buildings = {}
        for _, building in self.buildings.iterrows():
            map_name = building['map_name'] or 'Unknown'
            if map_name not in map_buildings:
                map_buildings[map_name] = []
            map_buildings[map_name].append(building['name'])
        
        # Get resources by map
        map_resources = {}
        for _, resource in self.resources.iterrows():
            map_name = resource['map_name'] or 'Unknown'
            if map_name not in map_resources:
                map_resources[map_name] = []
            map_resources[map_name].append(resource['name'])
        
        self.stats['map_buildings'] = {k: len(v) for k, v in map_buildings.items()}
        self.stats['map_resources'] = {k: len(v) for k, v in map_resources.items()}
        
        print(f"  📍 Maps analyzed: {len(map_buildings)}")
        for map_name, building_count in self.stats['map_buildings'].items():
            resource_count = self.stats['map_resources'].get(map_name, 0)
            print(f"     {map_name}: {building_count} buildings, {resource_count} resources")
        
        # Check for cross-map resource dependencies
        cross_map_dependencies = []
        
        for map1 in map_buildings:
            for map2 in map_buildings:
                if map1 != map2:
                    # Check if buildings in map1 need resources only available in map2
                    map1_buildings_df = self.buildings[self.buildings['map_name'] == map1]
                    map2_resources_df = self.resources[self.resources['map_name'] == map2]
                    
                    if not map1_buildings_df.empty and not map2_resources_df.empty:
                        map1_building_ids = map1_buildings_df['id'].tolist()
                        map2_resource_ids = map2_resources_df['id'].tolist()
                        
                        if map1_building_ids and map2_resource_ids:
                            dependencies = pd.read_sql(f"""
                                SELECT b.name as building, r.name as resource
                                FROM buildings b
                                JOIN building_inputs bi ON b.id = bi.building_id
                                JOIN resources r ON bi.resource_id = r.id
                                WHERE b.id IN ({','.join(map(str, map1_building_ids))})
                                  AND r.id IN ({','.join(map(str, map2_resource_ids))})
                            """, self.conn)
                            
                            if not dependencies.empty:
                                cross_map_dependencies.append({
                                    'from_map': map1,
                                    'to_map': map2,
                                    'dependencies': dependencies.to_dict('records')
                                })
        
        self.stats['cross_map_dependencies'] = cross_map_dependencies
        print(f"  🔗 Cross-map dependencies found: {len(cross_map_dependencies)}")
        
        return map_buildings, cross_map_dependencies
    
    def generate_report(self):
        """Generate a comprehensive validation report"""
        print("\n📋 Generating validation report...")
        
        report = {
            'timestamp': pd.Timestamp.now().isoformat(),
            'summary': {
                'total_issues': sum(len(v) for v in self.issues.values()),
                'total_warnings': sum(len(v) for v in self.warnings.values()),
                'categories_with_issues': len([k for k, v in self.issues.items() if v]),
                'categories_with_warnings': len([k for k, v in self.warnings.items() if v])
            },
            'critical_issues': self.issues,
            'warnings': self.warnings,
            'statistics': self.stats
        }
        
        # Save report
        with open('data_validation_report.json', 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"  ✅ Report saved to: data_validation_report.json")
        
        # Print summary
        print(f"\n📊 VALIDATION SUMMARY")
        print(f"  🚨 Critical Issues: {report['summary']['total_issues']}")
        print(f"  ⚠️  Warnings: {report['summary']['total_warnings']}")
        
        if self.issues:
            print(f"\n🚨 CRITICAL ISSUES TO FIX:")
            for category, items in self.issues.items():
                if items:
                    print(f"  • {category}: {len(items)} items")
        
        if self.warnings:
            print(f"\n⚠️  WARNINGS TO REVIEW:")
            for category, items in self.warnings.items():
                if items:
                    print(f"  • {category}: {len(items)} items")
        
        return report
        
    def run_full_validation(self):
        """Run all validation checks"""
        print("🔍 MASTERPLAN TYCOON DATA VALIDATION")
        print("=" * 50)
        
        self.load_data()
        self.validate_building_connections()
        self.validate_resource_chains()
        self.validate_construction_maintenance()
        self.detect_calculation_breakers()
        self.analyze_map_connectivity()
        
        return self.generate_report()

def main():
    validator = DataValidator()
    report = validator.run_full_validation()
    
    print(f"\n🎯 NEXT STEPS:")
    print(f"  1. Review data_validation_report.json for detailed findings")
    print(f"  2. Address critical issues before running optimization calculations")
    print(f"  3. Investigate port logic and cross-map dependencies")
    print(f"  4. Add missing building connections or mark as special cases")

if __name__ == "__main__":
    main()