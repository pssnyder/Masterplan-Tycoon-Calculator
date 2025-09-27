#!/usr/bin/env python3
"""
Port and Cross-Map Analysis Tool

Analyzes port buildings, cross-map resource flows, and transportation logic
that could complicate optimization calculations.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.config import get_db_connection
import pandas as pd
import networkx as nx
from collections import defaultdict
import json

class PortAnalyzer:
    def __init__(self):
        self.conn = get_db_connection()
        self.ports = []
        self.transport_buildings = []
        self.cross_map_flows = []
        
    def identify_ports(self):
        """Identify potential port buildings and transportation infrastructure"""
        print("🚢 Identifying ports and transportation buildings...")
        
        # Keywords that might indicate transportation/port buildings
        transport_keywords = [
            'port', 'dock', 'pier', 'harbor', 'ferry', 'ship', 'boat',
            'transport', 'cargo', 'depot', 'terminal', 'wharf'
        ]
        
        # Get all buildings and check for transport keywords
        buildings = pd.read_sql("""
            SELECT b.*, m.name as map_name 
            FROM buildings b 
            LEFT JOIN maps m ON b.map_id = m.id
        """, self.conn)
        
        potential_ports = []
        for _, building in buildings.iterrows():
            building_name_lower = building['name'].lower()
            if any(keyword in building_name_lower for keyword in transport_keywords):
                
                # Get input/output info for this building
                inputs = pd.read_sql(f"""
                    SELECT r.name as resource, bi.quantity
                    FROM building_inputs bi
                    JOIN resources r ON bi.resource_id = r.id
                    WHERE bi.building_id = {building['id']}
                """, self.conn)
                
                outputs = pd.read_sql(f"""
                    SELECT r.name as resource, bo.quantity, bo.output_per_minute
                    FROM building_outputs bo
                    JOIN resources r ON bo.resource_id = r.id
                    WHERE bo.building_id = {building['id']}
                """, self.conn)
                
                construction = pd.read_sql(f"""
                    SELECT r.name as resource, bc.quantity
                    FROM building_construction bc
                    JOIN resources r ON bc.resource_id = r.id
                    WHERE bc.building_id = {building['id']}
                """, self.conn)
                
                maintenance = pd.read_sql(f"""
                    SELECT r.name as resource, bm.quantity
                    FROM building_maintenance bm
                    JOIN resources r ON bm.resource_id = r.id
                    WHERE bm.building_id = {building['id']}
                """, self.conn)
                
                port_info = {
                    'id': building['id'],
                    'name': building['name'],
                    'map': building['map_name'],
                    'inputs': inputs.to_dict('records'),
                    'outputs': outputs.to_dict('records'),
                    'construction': construction.to_dict('records'),
                    'maintenance': maintenance.to_dict('records'),
                    'has_inputs': len(inputs) > 0,
                    'has_outputs': len(outputs) > 0,
                    'has_construction': len(construction) > 0,
                    'has_maintenance': len(maintenance) > 0
                }
                
                potential_ports.append(port_info)
        
        self.ports = potential_ports
        print(f"  🚢 Found {len(potential_ports)} potential port/transport buildings")
        
        # Categorize ports by their characteristics
        categories = {
            'input_only': [],      # Only receives resources (import ports)
            'output_only': [],     # Only sends resources (export ports)  
            'bidirectional': [],   # Both inputs and outputs (transfer hubs)
            'no_flows': [],        # Neither inputs nor outputs (broken/incomplete)
            'zero_cost': []        # No construction/maintenance (special buildings)
        }
        
        for port in potential_ports:
            if port['has_inputs'] and not port['has_outputs']:
                categories['input_only'].append(port)
            elif port['has_outputs'] and not port['has_inputs']:
                categories['output_only'].append(port)
            elif port['has_inputs'] and port['has_outputs']:
                categories['bidirectional'].append(port)
            else:
                categories['no_flows'].append(port)
                
            if not port['has_construction'] and not port['has_maintenance']:
                categories['zero_cost'].append(port)
        
        print(f"  📊 Port Categories:")
        for category, ports in categories.items():
            if ports:
                print(f"    • {category}: {len(ports)} buildings")
                for port in ports[:3]:  # Show first 3 examples
                    print(f"      - {port['name']} ({port['map'] or 'Unknown Map'})")
        
        return potential_ports, categories
    
    def analyze_cross_map_dependencies(self):
        """Analyze resource dependencies that cross map boundaries"""
        print("\n🗺️ Analyzing cross-map resource dependencies...")
        
        # Get all maps
        maps = pd.read_sql("SELECT * FROM maps", self.conn).set_index('id')['name'].to_dict()
        
        # Find resources that exist on multiple maps
        resource_maps = pd.read_sql("""
            SELECT r.name as resource_name, m.name as map_name
            FROM resources r
            LEFT JOIN maps m ON r.map_id = m.id
            ORDER BY r.name, m.name
        """, self.conn)
        
        # Group by resource to see which are cross-map
        cross_map_resources = {}
        for _, row in resource_maps.iterrows():
            resource = row['resource_name']
            map_name = row['map_name']
            
            if resource not in cross_map_resources:
                cross_map_resources[resource] = []
            cross_map_resources[resource].append(map_name)
        
        # Filter to only truly cross-map resources
        cross_map_resources = {k: v for k, v in cross_map_resources.items() if len(v) > 1}
        
        print(f"  🔗 Resources available on multiple maps: {len(cross_map_resources)}")
        
        # Analyze dependencies that require cross-map transport
        cross_map_dependencies = []
        
        # Get all building input requirements
        dependencies_query = """
        SELECT 
            b.name as building_name,
            m1.name as building_map,
            r.name as required_resource,
            m2.name as resource_map,
            bi.quantity as required_quantity
        FROM buildings b
        LEFT JOIN maps m1 ON b.map_id = m1.id
        JOIN building_inputs bi ON b.id = bi.building_id
        JOIN resources r ON bi.resource_id = r.id
        LEFT JOIN maps m2 ON r.map_id = m2.id
        WHERE m1.name != m2.name OR (m1.name IS NULL OR m2.name IS NULL)
        """
        
        cross_dependencies = pd.read_sql(dependencies_query, self.conn)
        
        if not cross_dependencies.empty:
            print(f"  ⚠️  Cross-map dependencies found: {len(cross_dependencies)}")
            
            # Group by maps involved
            map_pairs = cross_dependencies.groupby(['building_map', 'resource_map']).size().reset_index(name='dependency_count')
            
            print(f"    Map dependency pairs:")
            for _, pair in map_pairs.iterrows():
                print(f"      {pair['resource_map']} → {pair['building_map']}: {pair['dependency_count']} dependencies")
        else:
            print(f"  ✅ No cross-map dependencies found (good for calculations)")
        
        return cross_map_resources, cross_dependencies
    
    def detect_transport_chains(self):
        """Detect potential transportation chains and bottlenecks"""
        print("\n🚛 Detecting transportation chains...")
        
        transport_chains = []
        
        # Look for buildings that might be part of transport chains
        # These would be buildings that take a resource as input and output the same resource
        # (essentially moving it from one place to another)
        
        transport_query = """
        SELECT 
            b.name as building_name,
            m.name as building_map,
            r_in.name as input_resource,
            r_out.name as output_resource,
            bi.quantity as input_qty,
            bo.quantity as output_qty,
            bo.output_per_minute
        FROM buildings b
        LEFT JOIN maps m ON b.map_id = m.id
        JOIN building_inputs bi ON b.id = bi.building_id
        JOIN building_outputs bo ON b.id = bo.building_id
        JOIN resources r_in ON bi.resource_id = r_in.id
        JOIN resources r_out ON bo.resource_id = r_out.id
        WHERE r_in.name = r_out.name  -- Same resource in and out
        """
        
        potential_transport = pd.read_sql(transport_query, self.conn)
        
        if not potential_transport.empty:
            print(f"  🔄 Buildings that input/output same resource: {len(potential_transport)}")
            
            for _, row in potential_transport.iterrows():
                transport_info = {
                    'building': row['building_name'],
                    'map': row['building_map'] or 'Unknown',
                    'resource': row['input_resource'],
                    'input_qty': row['input_qty'],
                    'output_qty': row['output_qty'],
                    'efficiency': row['output_qty'] / row['input_qty'] if row['input_qty'] > 0 else 0,
                    'rate': row['output_per_minute']
                }
                transport_chains.append(transport_info)
                
                efficiency_pct = transport_info['efficiency'] * 100
                print(f"    • {row['building_name']}: {row['input_resource']} ({efficiency_pct:.1f}% efficiency)")
        else:
            print(f"  ✅ No obvious transport chains found")
        
        return transport_chains
    
    def identify_calculation_risks(self):
        """Identify specific risks that could break calculations"""
        print("\n⚠️  Identifying calculation risks...")
        
        risks = {
            'missing_port_logic': [],
            'circular_transport': [],
            'infinite_loops': [],
            'missing_connections': [],
            'unrealistic_rates': []
        }
        
        # Risk 1: Ports with no clear transport logic
        for port in self.ports:
            if not port['has_inputs'] and not port['has_outputs']:
                risks['missing_port_logic'].append({
                    'building': port['name'],
                    'map': port['map'] or 'Unknown',
                    'issue': 'No inputs or outputs defined'
                })
            elif port['has_construction'] and len(port['construction']) == 0:
                risks['missing_port_logic'].append({
                    'building': port['name'],
                    'map': port['map'] or 'Unknown',
                    'issue': 'Empty construction requirements'
                })
        
        # Risk 2: Circular transport chains that could cause infinite loops
        for chain in getattr(self, 'transport_chains', []):
            if chain['efficiency'] > 1.0:  # More output than input = potential energy creation
                risks['circular_transport'].append({
                    'building': chain['building'],
                    'resource': chain['resource'],
                    'efficiency': chain['efficiency'],
                    'issue': 'Efficiency > 100% could cause infinite growth'
                })
        
        # Risk 3: Buildings with extremely high or zero production rates
        rate_query = """
        SELECT b.name, r.name as resource, bo.output_per_minute
        FROM buildings b
        JOIN building_outputs bo ON b.id = bo.building_id
        JOIN resources r ON bo.resource_id = r.id
        WHERE bo.output_per_minute > 100 OR bo.output_per_minute = 0
        """
        
        extreme_rates = pd.read_sql(rate_query, self.conn)
        for _, row in extreme_rates.iterrows():
            risks['unrealistic_rates'].append({
                'building': row['name'],
                'resource': row['resource'],
                'rate': row['output_per_minute'],
                'issue': 'Zero rate' if row['output_per_minute'] == 0 else 'Very high rate'
            })
        
        # Summary
        total_risks = sum(len(risk_list) for risk_list in risks.values())
        print(f"  🚨 Total calculation risks identified: {total_risks}")
        
        for risk_type, risk_list in risks.items():
            if risk_list:
                print(f"    • {risk_type}: {len(risk_list)} issues")
        
        return risks
    
    def generate_port_analysis_report(self):
        """Generate a comprehensive port analysis report"""
        print("\n📋 Generating port analysis report...")
        
        # Run all analyses
        ports, port_categories = self.identify_ports()
        cross_map_resources, cross_dependencies = self.analyze_cross_map_dependencies()
        transport_chains = self.detect_transport_chains()
        self.transport_chains = transport_chains  # Store for risk analysis
        risks = self.identify_calculation_risks()
        
        report = {
            'timestamp': pd.Timestamp.now().isoformat(),
            'summary': {
                'total_ports': len(ports),
                'cross_map_resources': len(cross_map_resources),
                'cross_map_dependencies': len(cross_dependencies),
                'transport_chains': len(transport_chains),
                'total_risks': sum(len(risk_list) for risk_list in risks.values())
            },
            'ports': {
                'all_ports': ports,
                'categories': {k: len(v) for k, v in port_categories.items()},
                'category_details': port_categories
            },
            'cross_map_analysis': {
                'resources_on_multiple_maps': cross_map_resources,
                'cross_dependencies': cross_dependencies.to_dict('records') if not cross_dependencies.empty else []
            },
            'transport_chains': transport_chains,
            'calculation_risks': risks
        }
        
        # Save report
        with open('port_analysis_report.json', 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"  ✅ Report saved to: port_analysis_report.json")
        
        # Print actionable recommendations
        print(f"\n🎯 RECOMMENDATIONS:")
        
        if report['summary']['total_ports'] > 0:
            print(f"  🚢 Port Buildings: {report['summary']['total_ports']} found")
            print(f"     → Review port logic before running optimization calculations")
            print(f"     → Consider treating ports as special cases with custom logic")
        
        if report['summary']['cross_map_dependencies'] > 0:
            print(f"  🗺️  Cross-Map Dependencies: {report['summary']['cross_map_dependencies']} found")
            print(f"     → May require transportation cost modeling in calculations")
            print(f"     → Could complicate optimization if not handled properly")
        
        if report['summary']['total_risks'] > 0:  
            print(f"  ⚠️  Calculation Risks: {report['summary']['total_risks']} identified")
            print(f"     → Address these issues before running optimization algorithms")
            print(f"     → Use calculation safety checker to prevent infinite loops")
        else:
            print(f"  ✅ No major calculation risks identified - ready for optimization!")
        
        return report

def main():
    """Run the port analysis"""
    print("🚢 MASTERPLAN TYCOON PORT & TRANSPORT ANALYSIS")
    print("=" * 50)
    
    analyzer = PortAnalyzer()
    report = analyzer.generate_port_analysis_report()
    
    print(f"\n📊 ANALYSIS COMPLETE")
    print(f"  📝 Detailed report: port_analysis_report.json")
    print(f"  🎯 Ready to integrate findings into optimization calculations")

if __name__ == "__main__":
    main()