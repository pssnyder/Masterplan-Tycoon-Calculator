#!/usr/bin/env python3
"""
Test Resource Chain with Real Data
"""

import sqlite3
import pandas as pd
import sys
import os

# Add the src directory to the path so we can import our explorer
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from resource_chain_explorer import get_resource_chain, get_building_analysis

def test_real_chains():
    """Test with actual data from the database"""
    print("🧪 TESTING RESOURCE CHAINS WITH REAL DATA")
    print("=" * 60)
    
    # Test 1: Steel resource chain
    print("Test 1: Steel Resource Chain (Master)")
    print("-" * 40)
    get_resource_chain("Steel", "Master")
    
    print("\n" + "=" * 60)
    
    # Test 2: Coal Mine building analysis
    print("Test 2: Coal Mine Building Analysis (Master)")
    print("-" * 40)
    get_building_analysis("Coal Mine", "Master")
    
    print("\n" + "=" * 60)
    
    # Test 3: Water resource chain (should be widely used)
    print("Test 3: Water Resource Chain (Master)")
    print("-" * 40)
    get_resource_chain("Water", "Master")
    
    print("\n" + "=" * 60)
    
    # Test 4: Anchor Workshop (should have inputs/outputs)
    print("Test 4: Anchor Workshop Building Analysis (Master)")
    print("-" * 40)
    get_building_analysis("Anchor Workshop", "Master")

if __name__ == "__main__":
    test_real_chains()