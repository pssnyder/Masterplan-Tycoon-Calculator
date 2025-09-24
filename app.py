#!/usr/bin/env python3
"""
Masterplan Tycoon Web Interface

A Flask web application for validating and analyzing Masterplan Tycoon data.
Provides a user-friendly interface for comparing database content with 
in-game building specifications and performing logistics calculations.
"""

from flask import Flask, render_template, jsonify, request, redirect, url_for
import sqlite3
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

app = Flask(__name__)

class MasterplanDatabase:
    def __init__(self, db_path: str = "masterplan_tycoon.db"):
        self.db_path = db_path
        
    def get_connection(self) -> sqlite3.Connection:
        """Get database connection with row factory for easier access"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def get_all_plans(self) -> List[Dict[str, Any]]:
        """Get all plans/regions"""
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM plans ORDER BY name")
            return [dict(row) for row in cursor.fetchall()]
    
    def get_buildings_by_plan(self, plan_name: str) -> List[Dict[str, Any]]:
        """Get all buildings for a specific plan"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT b.*, p.name as plan_name, bc.name as category_name
                FROM buildings b
                JOIN plans p ON b.plan_id = p.id
                LEFT JOIN building_categories bc ON b.category_id = bc.id
                WHERE p.name = ?
                ORDER BY b.tier, b.name
            """, (plan_name,))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_building_details(self, building_id: int) -> Optional[Dict[str, Any]]:
        """Get complete details for a specific building"""
        with self.get_connection() as conn:
            # Get building info
            cursor = conn.execute("""
                SELECT b.*, p.name as plan_name, bc.name as category_name
                FROM buildings b
                JOIN plans p ON b.plan_id = p.id
                LEFT JOIN building_categories bc ON b.category_id = bc.id
                WHERE b.id = ?
            """, (building_id,))
            
            building = cursor.fetchone()
            if not building:
                return None
                
            building_dict = dict(building)
            
            # Get inputs
            cursor = conn.execute("""
                SELECT r.name as resource_name, bi.quantity, 
                       dep.name as dependency_building
                FROM building_inputs bi
                JOIN resources r ON bi.resource_id = r.id
                LEFT JOIN buildings dep ON bi.dependency_building_id = dep.id
                WHERE bi.building_id = ?
                ORDER BY r.name
            """, (building_id,))
            building_dict['inputs'] = [dict(row) for row in cursor.fetchall()]
            
            # Get outputs
            cursor = conn.execute("""
                SELECT r.name as resource_name, bo.quantity, bo.production_time
                FROM building_outputs bo
                JOIN resources r ON bo.resource_id = r.id
                WHERE bo.building_id = ?
                ORDER BY r.name
            """, (building_id,))
            building_dict['outputs'] = [dict(row) for row in cursor.fetchall()]
            
            # Get construction requirements
            cursor = conn.execute("""
                SELECT r.name as resource_name, bc.quantity,
                       dep.name as dependency_building
                FROM building_construction bc
                JOIN resources r ON bc.resource_id = r.id
                LEFT JOIN buildings dep ON bc.dependency_building_id = dep.id
                WHERE bc.building_id = ?
                ORDER BY r.name
            """, (building_id,))
            building_dict['construction'] = [dict(row) for row in cursor.fetchall()]
            
            # Get maintenance requirements
            cursor = conn.execute("""
                SELECT r.name as resource_name, bm.quantity,
                       dep.name as dependency_building
                FROM building_maintenance bm
                JOIN resources r ON bm.resource_id = r.id
                LEFT JOIN buildings dep ON bm.dependency_building_id = dep.id
                WHERE bm.building_id = ?
                ORDER BY r.name
            """, (building_id,))
            building_dict['maintenance'] = [dict(row) for row in cursor.fetchall()]
            
            return building_dict
    
    def search_buildings(self, search_term: str) -> List[Dict[str, Any]]:
        """Search buildings by name"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT b.*, p.name as plan_name, bc.name as category_name
                FROM buildings b
                JOIN plans p ON b.plan_id = p.id
                LEFT JOIN building_categories bc ON b.category_id = bc.id
                WHERE b.name LIKE ? OR bc.name LIKE ?
                ORDER BY b.name
                LIMIT 50
            """, (f"%{search_term}%", f"%{search_term}%"))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_resource_flow(self, resource_name: str) -> Dict[str, Any]:
        """Get complete resource flow (producers and consumers)"""
        with self.get_connection() as conn:
            # Get producers
            cursor = conn.execute("""
                SELECT b.name as building_name, p.name as plan_name,
                       bo.quantity, bo.production_time,
                       CASE 
                           WHEN bo.production_time > 0 
                           THEN (bo.quantity * 60.0 / bo.production_time)
                           ELSE 0 
                       END as rate_per_minute
                FROM building_outputs bo
                JOIN buildings b ON bo.building_id = b.id
                JOIN plans p ON b.plan_id = p.id
                JOIN resources r ON bo.resource_id = r.id
                WHERE r.name = ?
                ORDER BY rate_per_minute DESC
            """, (resource_name,))
            producers = [dict(row) for row in cursor.fetchall()]
            
            # Get consumers (inputs)
            cursor = conn.execute("""
                SELECT b.name as building_name, p.name as plan_name,
                       bi.quantity, 'input' as usage_type
                FROM building_inputs bi
                JOIN buildings b ON bi.building_id = b.id
                JOIN plans p ON b.plan_id = p.id
                JOIN resources r ON bi.resource_id = r.id
                WHERE r.name = ?
                ORDER BY b.name
            """, (resource_name,))
            input_consumers = [dict(row) for row in cursor.fetchall()]
            
            # Get consumers (construction)
            cursor = conn.execute("""
                SELECT b.name as building_name, p.name as plan_name,
                       bc.quantity, 'construction' as usage_type
                FROM building_construction bc
                JOIN buildings b ON bc.building_id = b.id
                JOIN plans p ON b.plan_id = p.id
                JOIN resources r ON bc.resource_id = r.id
                WHERE r.name = ?
                ORDER BY b.name
            """, (resource_name,))
            construction_consumers = [dict(row) for row in cursor.fetchall()]
            
            # Get consumers (maintenance)
            cursor = conn.execute("""
                SELECT b.name as building_name, p.name as plan_name,
                       bm.quantity, 'maintenance' as usage_type
                FROM building_maintenance bm
                JOIN buildings b ON bm.building_id = b.id
                JOIN plans p ON b.plan_id = p.id
                JOIN resources r ON bm.resource_id = r.id
                WHERE r.name = ?
                ORDER BY b.name
            """, (resource_name,))
            maintenance_consumers = [dict(row) for row in cursor.fetchall()]
            
            return {
                'resource_name': resource_name,
                'producers': producers,
                'consumers': input_consumers + construction_consumers + maintenance_consumers
            }

# Initialize database connection
db = MasterplanDatabase()

@app.route('/')
def index():
    """Home page with overview"""
    plans = db.get_all_plans()
    return render_template('index.html', plans=plans)

@app.route('/plan/<plan_name>')
def plan_buildings(plan_name):
    """Show all buildings for a specific plan"""
    buildings = db.get_buildings_by_plan(plan_name)
    return render_template('plan_buildings.html', 
                         plan_name=plan_name, 
                         buildings=buildings)

@app.route('/building/<int:building_id>')
def building_detail(building_id):
    """Show detailed information for a specific building"""
    building = db.get_building_details(building_id)
    if not building:
        return "Building not found", 404
    return render_template('building_detail.html', building=building)

@app.route('/search')
def search():
    """Search buildings"""
    query = request.args.get('q', '')
    if query:
        buildings = db.search_buildings(query)
        return render_template('search_results.html', 
                             query=query, 
                             buildings=buildings)
    return render_template('search.html')

@app.route('/resource/<resource_name>')
def resource_flow(resource_name):
    """Show resource production and consumption"""
    flow = db.get_resource_flow(resource_name)
    return render_template('resource_flow.html', flow=flow)

@app.route('/api/buildings')
def api_buildings():
    """API endpoint for buildings data"""
    plan = request.args.get('plan')
    if plan:
        buildings = db.get_buildings_by_plan(plan)
    else:
        # Get all buildings if no plan specified
        with db.get_connection() as conn:
            cursor = conn.execute("""
                SELECT b.*, p.name as plan_name, bc.name as category_name
                FROM buildings b
                JOIN plans p ON b.plan_id = p.id
                LEFT JOIN building_categories bc ON b.category_id = bc.id
                ORDER BY p.name, b.tier, b.name
            """)
            buildings = [dict(row) for row in cursor.fetchall()]
    
    return jsonify(buildings)

@app.route('/api/building/<int:building_id>')
def api_building_detail(building_id):
    """API endpoint for building details"""
    building = db.get_building_details(building_id)
    if not building:
        return jsonify({'error': 'Building not found'}), 404
    return jsonify(building)

@app.route('/calculator')
def calculator():
    """Production chain calculator"""
    return render_template('calculator.html')

if __name__ == '__main__':
    # Check if database exists
    if not Path("masterplan_tycoon.db").exists():
        print("Database not found! Please run build_database.py first.")
        exit(1)
    
    print("Starting Masterplan Tycoon Web Interface...")
    print("Visit http://localhost:5000 to access the application")
    app.run(debug=True, host='0.0.0.0', port=5000)