-- Masterplan Tycoon Database Schema
-- This schema is designed to normalize and organize all game data for efficient analysis

-- ========================================
-- Core Entity Tables
-- ========================================

-- Plans/Regions - Different geographic areas in the game
CREATE TABLE plans (
    id INTEGER PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    description TEXT
);

-- Resource Categories - Groups of similar resources
CREATE TABLE resource_categories (
    id INTEGER PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    description TEXT
);

-- Resources - All materials, goods, and items in the game
CREATE TABLE resources (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    category_id INTEGER,
    is_consumable BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (category_id) REFERENCES resource_categories(id)
);

-- Building Categories - Groups of similar buildings by function
CREATE TABLE building_categories (
    id INTEGER PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    description TEXT
);

-- Buildings - All structures that can be built
CREATE TABLE buildings (
    id INTEGER PRIMARY KEY,
    building_id VARCHAR(20) NOT NULL UNIQUE, -- Game's internal ID (e.g., "2-06-P-AFI")
    name VARCHAR(100) NOT NULL,
    plan_id INTEGER NOT NULL,
    tier INTEGER NOT NULL,
    category_id INTEGER,
    production_time INTEGER, -- In game time units, NULL if no production
    FOREIGN KEY (plan_id) REFERENCES plans(id),
    FOREIGN KEY (category_id) REFERENCES building_categories(id)
);

-- ========================================
-- Resource Flow Tables
-- ========================================

-- Building Inputs - Resources consumed by buildings
CREATE TABLE building_inputs (
    id INTEGER PRIMARY KEY,
    building_id INTEGER NOT NULL,
    resource_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    dependency_building_id INTEGER, -- Which building produces this resource
    FOREIGN KEY (building_id) REFERENCES buildings(id),
    FOREIGN KEY (resource_id) REFERENCES resources(id),
    FOREIGN KEY (dependency_building_id) REFERENCES buildings(id)
);

-- Building Outputs - Resources produced by buildings
CREATE TABLE building_outputs (
    id INTEGER PRIMARY KEY,
    building_id INTEGER NOT NULL,
    resource_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    production_time INTEGER, -- Override building's default production time
    FOREIGN KEY (building_id) REFERENCES buildings(id),
    FOREIGN KEY (resource_id) REFERENCES resources(id)
);

-- Building Construction Requirements - Resources needed to build a building
CREATE TABLE building_construction (
    id INTEGER PRIMARY KEY,
    building_id INTEGER NOT NULL,
    resource_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    dependency_building_id INTEGER, -- Which building produces this resource
    FOREIGN KEY (building_id) REFERENCES buildings(id),
    FOREIGN KEY (resource_id) REFERENCES resources(id),
    FOREIGN KEY (dependency_building_id) REFERENCES buildings(id)
);

-- Building Maintenance Requirements - Ongoing resources needed to operate
CREATE TABLE building_maintenance (
    id INTEGER PRIMARY KEY,
    building_id INTEGER NOT NULL,
    resource_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    dependency_building_id INTEGER, -- Which building produces this resource
    FOREIGN KEY (building_id) REFERENCES buildings(id),
    FOREIGN KEY (resource_id) REFERENCES resources(id),
    FOREIGN KEY (dependency_building_id) REFERENCES buildings(id)
);

-- ========================================
-- Game State Tables (from JSON save data)
-- ========================================

-- Player Statistics - Overall game progression
CREATE TABLE player_stats (
    id INTEGER PRIMARY KEY,
    save_name VARCHAR(100),
    save_date DATETIME,
    total_population INTEGER,
    total_money DECIMAL(15,2),
    prestige_points INTEGER,
    current_mission VARCHAR(100)
);

-- Missions - Game objectives and progress
CREATE TABLE missions (
    id INTEGER PRIMARY KEY,
    mission_id VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(200),
    description TEXT,
    is_completed BOOLEAN DEFAULT FALSE,
    completion_date DATETIME,
    reward_money DECIMAL(10,2),
    reward_prestige INTEGER
);

-- Storage Facilities - Resource storage locations
CREATE TABLE storage_facilities (
    id INTEGER PRIMARY KEY,
    facility_id VARCHAR(50) NOT NULL,
    name VARCHAR(100),
    plan_id INTEGER,
    capacity_limit INTEGER,
    FOREIGN KEY (plan_id) REFERENCES plans(id)
);

-- Current Storage - What resources are stored where
CREATE TABLE current_storage (
    id INTEGER PRIMARY KEY,
    facility_id INTEGER NOT NULL,
    resource_id INTEGER NOT NULL,
    quantity DECIMAL(10,2),
    last_updated DATETIME,
    FOREIGN KEY (facility_id) REFERENCES storage_facilities(id),
    FOREIGN KEY (resource_id) REFERENCES resources(id)
);

-- Placed Buildings - Actual buildings in the game world
CREATE TABLE placed_buildings (
    id INTEGER PRIMARY KEY,
    building_template_id INTEGER NOT NULL,
    instance_id VARCHAR(50), -- Unique instance identifier from save
    plan_id INTEGER NOT NULL,
    x_coordinate INTEGER,
    y_coordinate INTEGER,
    is_active BOOLEAN DEFAULT TRUE,
    construction_date DATETIME,
    FOREIGN KEY (building_template_id) REFERENCES buildings(id),
    FOREIGN KEY (plan_id) REFERENCES plans(id)
);

-- ========================================
-- Analysis and Calculation Tables
-- ========================================

-- Production Chains - Calculated optimal production sequences
CREATE TABLE production_chains (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    target_resource_id INTEGER NOT NULL,
    target_quantity INTEGER NOT NULL,
    efficiency_score DECIMAL(5,2),
    created_date DATETIME,
    FOREIGN KEY (target_resource_id) REFERENCES resources(id)
);

-- Production Chain Steps - Individual steps in a production chain
CREATE TABLE production_chain_steps (
    id INTEGER PRIMARY KEY,
    chain_id INTEGER NOT NULL,
    building_id INTEGER NOT NULL,
    step_order INTEGER NOT NULL,
    required_quantity INTEGER NOT NULL,
    notes TEXT,
    FOREIGN KEY (chain_id) REFERENCES production_chains(id),
    FOREIGN KEY (building_id) REFERENCES buildings(id)
);

-- Resource Calculations - Cached calculation results
CREATE TABLE resource_calculations (
    id INTEGER PRIMARY KEY,
    resource_id INTEGER NOT NULL,
    calculation_type VARCHAR(50) NOT NULL, -- 'optimal_production', 'supply_chain', etc.
    input_parameters JSON,
    result_data JSON,
    calculated_date DATETIME,
    FOREIGN KEY (resource_id) REFERENCES resources(id)
);

-- ========================================
-- Indexes for Performance
-- ========================================

-- Primary lookup indexes
CREATE INDEX idx_buildings_plan_tier ON buildings(plan_id, tier);
CREATE INDEX idx_buildings_category ON buildings(category_id);
CREATE INDEX idx_building_inputs_building ON building_inputs(building_id);
CREATE INDEX idx_building_outputs_building ON building_outputs(building_id);
CREATE INDEX idx_building_construction_building ON building_construction(building_id);
CREATE INDEX idx_building_maintenance_building ON building_maintenance(building_id);

-- Resource flow indexes
CREATE INDEX idx_building_inputs_resource ON building_inputs(resource_id);
CREATE INDEX idx_building_outputs_resource ON building_outputs(resource_id);
CREATE INDEX idx_building_construction_resource ON building_construction(resource_id);
CREATE INDEX idx_building_maintenance_resource ON building_maintenance(resource_id);

-- Dependency tracking indexes
CREATE INDEX idx_building_inputs_dependency ON building_inputs(dependency_building_id);
CREATE INDEX idx_building_construction_dependency ON building_construction(dependency_building_id);
CREATE INDEX idx_building_maintenance_dependency ON building_maintenance(dependency_building_id);

-- Game state indexes
CREATE INDEX idx_current_storage_facility ON current_storage(facility_id);
CREATE INDEX idx_current_storage_resource ON current_storage(resource_id);
CREATE INDEX idx_placed_buildings_template ON placed_buildings(building_template_id);
CREATE INDEX idx_placed_buildings_plan ON placed_buildings(plan_id);

-- Analysis indexes
CREATE INDEX idx_production_chain_steps_chain ON production_chain_steps(chain_id);
CREATE INDEX idx_resource_calculations_resource ON resource_calculations(resource_id);
CREATE INDEX idx_resource_calculations_type ON resource_calculations(calculation_type);

-- ========================================
-- Views for Common Queries
-- ========================================

-- Complete building information with category names
CREATE VIEW building_details AS
SELECT 
    b.id,
    b.building_id,
    b.name,
    p.name as plan_name,
    b.tier,
    bc.name as category_name,
    b.production_time
FROM buildings b
LEFT JOIN plans p ON b.plan_id = p.id
LEFT JOIN building_categories bc ON b.category_id = bc.id;

-- Resource production overview
CREATE VIEW resource_production AS
SELECT 
    r.name as resource_name,
    b.name as building_name,
    p.name as plan_name,
    bo.quantity,
    bo.production_time,
    CASE 
        WHEN bo.production_time > 0 THEN (bo.quantity * 60.0 / bo.production_time)
        ELSE 0
    END as production_rate_per_minute
FROM building_outputs bo
JOIN resources r ON bo.resource_id = r.id
JOIN buildings b ON bo.building_id = b.id
JOIN plans p ON b.plan_id = p.id;

-- Complete supply chain view
CREATE VIEW supply_chain AS
SELECT 
    consumer.name as consumer_building,
    consumer_plan.name as consumer_plan,
    resource.name as resource_name,
    bi.quantity as required_quantity,
    producer.name as producer_building,
    producer_plan.name as producer_plan
FROM building_inputs bi
JOIN buildings consumer ON bi.building_id = consumer.id
JOIN plans consumer_plan ON consumer.plan_id = consumer_plan.id
JOIN resources resource ON bi.resource_id = resource.id
LEFT JOIN buildings producer ON bi.dependency_building_id = producer.id
LEFT JOIN plans producer_plan ON producer.plan_id = producer_plan.id;

-- ========================================
-- Sample Data Inserts (will be populated from CSV files)
-- ========================================

-- Plans
INSERT INTO plans (name, description) VALUES 
('Master', 'Main continental region with advanced industrial buildings'),
('Islands', 'Tropical islands with specialized agricultural and luxury goods'),
('Mountains', 'Mountain region with mining and heavy industry');

-- Common Resource Categories
INSERT INTO resource_categories (name, description) VALUES
('Raw Materials', 'Basic resources extracted from the environment'),
('Agricultural Products', 'Food and organic materials from farms'),
('Manufactured Goods', 'Processed items created in factories'),
('Luxury Items', 'High-tier consumer goods'),
('Construction Materials', 'Resources used for building structures'),
('Tools & Equipment', 'Mechanical devices and instruments'),
('Consumables', 'Items that are consumed during use');