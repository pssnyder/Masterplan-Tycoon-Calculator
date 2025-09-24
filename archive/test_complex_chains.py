#!/usr/bin/env python3
"""
Test Complex Resource Chains
"""

import sys
sys.path.append('.')
from resource_chain_explorer_fixed import get_resource_chain, get_building_analysis

print('🔗 TESTING COMPLEX RESOURCE CHAINS')
print('='*60)

print('\n1️⃣ STEEL CHAIN (should be complex):')
get_resource_chain('Steel', 'Master')

print('\n2️⃣ ANCHOR CHAIN (manufactured item):')
get_resource_chain('Anchor', 'Master')

print('\n3️⃣ FURNACE ANALYSIS (consumer of multiple resources):')
get_building_analysis('Furnace', 'Master')