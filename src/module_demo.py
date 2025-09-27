#!/usr/bin/env python3
"""
Masterplan Tycoon Calculator - Module Demo
Demonstrates the organized module structure and cross-module integration
"""

import os
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from shared.config import get_project_info, get_db_connection

def main():
    """Demonstrate the modular organization"""
    
    print("🏗️  MASTERPLAN TYCOON CALCULATOR - MODULE STRUCTURE")
    print("=" * 60)
    
    # Show project information
    project_info = get_project_info()
    print(f"\n📁 Project Root: {project_info['project_root']}")
    print(f"🗄️  Database: {project_info['database_path']}")
    
    print(f"\n📦 Available Modules:")
    for module_name, module_path in project_info['modules'].items():
        status = "✅ Ready" if module_path.exists() else "❌ Missing"
        print(f"  • {module_name:20} - {status}")
        
        # List files in each module
        if module_path.exists():
            python_files = list(module_path.glob("*.py"))
            if python_files:
                for file in python_files:
                    if file.name != "__init__.py":
                        print(f"    └── {file.name}")
    
    # Test database connection
    print(f"\n🔗 Database Connection Test:")
    try:
        with get_db_connection() as conn:
            cursor = conn.execute("SELECT COUNT(*) as table_count FROM sqlite_master WHERE type='table'")
            table_count = cursor.fetchone()[0]
            print(f"  ✅ Connected successfully - {table_count} tables found")
    except Exception as e:
        print(f"  ❌ Connection failed: {e}")
    
    print(f"\n🎯 Usage Examples:")
    print(f"  # Run data exploration")
    print(f"  cd data_exploration && python resource_chain_explorer_fixed.py")
    
    print(f"\n  # Run analysis")
    print(f"  cd analysis && python brute_force_analyzer.py")
    
    print(f"\n  # Run calculations")
    print(f"  cd game_calculation && python dependency_analyzer.py")
    
    print(f"\n  # Launch dashboard")
    print(f"  cd visualization && streamlit run streamlit_dashboard.py")
    
    print(f"\n🚀 Ready for optimization algorithms!")

if __name__ == "__main__":
    main()