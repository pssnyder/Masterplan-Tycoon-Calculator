#!/usr/bin/env python3
"""
Calculation Safety Checker

Monitors calculation processes for infinite loops, unrealistic numbers,
and provides safety bounds based on actual gameplay data.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.config import get_db_connection
import pandas as pd
import json
from pathlib import Path
import time

class CalculationSafetyChecker:
    def __init__(self, save_file_path=None):
        self.conn = get_db_connection()
        self.safety_bounds = {}
        self.load_safety_bounds(save_file_path)
        
    def load_safety_bounds(self, save_file_path=None):
        """Load safety bounds from actual gameplay data"""
        print("🛡️ Loading safety bounds from gameplay data...")
        
        # Try to load from save file if provided
        if save_file_path and Path(save_file_path).exists():
            try:
                with open(save_file_path, 'r') as f:
                    save_data = json.load(f)
                
                # Extract building counts from save file
                building_counts = {}
                if 'nodes' in save_data:
                    for node in save_data['nodes']:
                        building_type = node.get('name', 'unknown')
                        building_counts[building_type] = building_counts.get(building_type, 0) + 1
                
                self.safety_bounds['max_buildings_per_type'] = building_counts
                self.safety_bounds['total_buildings'] = len(save_data.get('nodes', []))
                
                print(f"  ✅ Loaded bounds from save file: {self.safety_bounds['total_buildings']} total buildings")
                
            except Exception as e:
                print(f"  ⚠️ Could not load save file: {e}")
        
        # Set default safety bounds
        if not self.safety_bounds:
            self.safety_bounds = {
                'max_buildings_per_type': {},
                'total_buildings': 2000,  # Conservative upper bound
                'max_production_rate': 1000,  # Resources per minute
                'max_calculation_depth': 10,  # Dependency levels
                'max_calculation_time': 30,  # Seconds
                'max_iterations': 1000
            }
            print(f"  ⚠️ Using default safety bounds")
        
        # Set additional computed bounds
        self.safety_bounds.update({
            'warning_threshold': 0.8,  # Warn at 80% of max
            'error_threshold': 1.0,    # Error at 100% of max
            'building_type_multiplier': 3.0  # Allow 3x actual count as upper bound
        })
        
    def get_building_safety_limit(self, building_type):
        """Get safety limit for a specific building type"""
        actual_count = self.safety_bounds['max_buildings_per_type'].get(building_type, 0)
        
        if actual_count > 0:
            # Use actual count * multiplier as upper bound
            return int(actual_count * self.safety_bounds['building_type_multiplier'])
        else:
            # For unknown buildings, use a conservative default
            return 50
    
    def check_building_count(self, building_type, calculated_count):
        """Check if calculated building count is within safe bounds"""
        limit = self.get_building_safety_limit(building_type)
        warning_level = int(limit * self.safety_bounds['warning_threshold'])
        
        if calculated_count > limit:
            return {
                'status': 'ERROR',
                'message': f'{building_type}: {calculated_count} exceeds safety limit of {limit}',
                'limit': limit,
                'calculated': calculated_count,
                'severity': 'high'
            }
        elif calculated_count > warning_level:
            return {
                'status': 'WARNING',
                'message': f'{building_type}: {calculated_count} approaching limit (>{warning_level})',
                'limit': limit,
                'calculated': calculated_count,
                'severity': 'medium'
            }
        else:
            return {
                'status': 'OK',
                'calculated': calculated_count,
                'limit': limit,
                'severity': 'low'
            }
    
    def check_total_buildings(self, total_calculated):
        """Check if total building count is reasonable"""
        limit = self.safety_bounds['total_buildings']
        warning_level = int(limit * self.safety_bounds['warning_threshold'])
        
        if total_calculated > limit:
            return {
                'status': 'ERROR',
                'message': f'Total buildings {total_calculated} exceeds limit of {limit}',
                'severity': 'critical'
            }
        elif total_calculated > warning_level:
            return {
                'status': 'WARNING', 
                'message': f'Total buildings {total_calculated} approaching limit',
                'severity': 'medium'
            }
        else:
            return {'status': 'OK', 'severity': 'low'}
    
    def check_production_rate(self, resource_name, rate_per_minute):
        """Check if production rate is realistic"""
        max_rate = self.safety_bounds['max_production_rate']
        
        if rate_per_minute > max_rate:
            return {
                'status': 'ERROR',
                'message': f'{resource_name}: {rate_per_minute}/min exceeds max rate {max_rate}',
                'severity': 'high'
            }
        elif rate_per_minute > max_rate * 0.5:
            return {
                'status': 'WARNING',
                'message': f'{resource_name}: High production rate {rate_per_minute}/min',
                'severity': 'medium'
            }
        else:
            return {'status': 'OK', 'severity': 'low'}

def create_safety_checker_from_save_file():
    """Create a safety checker using the actual save file data"""
    # Look for save file in the project
    project_root = Path(__file__).parent.parent.parent
    save_file_candidates = [
        project_root / "game_data_save0.json",
        project_root / "references" / "game_data_save0.json",
        project_root / "archive" / "game_data_save0.json"
    ]
    
    save_file_path = None
    for candidate in save_file_candidates:
        if candidate.exists():
            save_file_path = candidate
            break
    
    if save_file_path:
        print(f"📁 Found save file: {save_file_path}")
        return CalculationSafetyChecker(str(save_file_path))
    else:
        print("⚠️ No save file found, using default safety bounds")
        return CalculationSafetyChecker()

def main():
    """Demo the safety checker"""
    print("🛡️ CALCULATION SAFETY CHECKER DEMO")
    print("=" * 40)
    
    checker = create_safety_checker_from_save_file()
    
    # Demo some safety checks
    print("\n🧪 Testing safety checks...")
    
    # Test building count checks
    test_buildings = [
        ('Well', 120),      # From our analysis - should be WARNING
        ('Fishery', 90),    # Should be WARNING  
        ('Bakery', 500),    # Should be ERROR
        ('Unknown Building', 5)  # Should be OK
    ]
    
    for building, count in test_buildings:
        result = checker.check_building_count(building, count)
        status_emoji = "🚨" if result['status'] == 'ERROR' else "⚠️" if result['status'] == 'WARNING' else "✅"
        print(f"  {status_emoji} {building}: {count} buildings - {result['status']}")
        if result.get('message'):
            print(f"      {result['message']}")
    
    # Test total building check
    total_check = checker.check_total_buildings(1800)
    status_emoji = "🚨" if total_check['status'] == 'ERROR' else "⚠️" if total_check['status'] == 'WARNING' else "✅"  
    print(f"\n  {status_emoji} Total buildings: 1800 - {total_check['status']}")
    
    print(f"\n🎯 Safety checker ready for calculations!")
    print(f"   Use the safety checker methods to validate calculation results")

if __name__ == "__main__":
    main()