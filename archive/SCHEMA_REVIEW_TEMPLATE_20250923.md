# Masterplan Tycoon Database Schema Review & Modification Guide

## 📋 Current Schema Overview

### **Maps/Regions Table**
The overarching maps where missions take place. Can contain multiple plans and have map specific buildings.
```
maps
├── id (Primary Key)
├── name (Master, Islands, Mountains)
└── description
```
### **Plans/Missions Table**
The specific missions within each map. Each plan belongs to one map.
```
plans
├── id (Primary Key)
├── name (Brick Mission, Steel Mission, Death Island, Gold Mission)
├── map_id → maps.id
└── description
```
### **Building Categories Table**
The individual output categories for factory setups. Determines the groups of buildings required to produce certain resource types within a micro-supply chain. 
```
building_categories
├── id (Primary Key)
├── name (Steel Beams, Port, Overalls, etc.)
├── description
├── map_id → maps.id
├── plan_id → plans.id
└── tier (0-12+)
```

### **Buildings Table (MAIN)**
The individual buildings that can be constructed within each map. 
```
buildings
├── id (Primary Key)
├── building_id (Quick Reference ID: 1-05-C-CFAM, MAP#-TIER#-CATEGORY_ABBR-ABBR(MAP_ABBR))
├── name (Building Name)
├── map_id → maps.id
├── tier (0-12+)
├── maintenance_required (TRUE/FALSE)
├── root_building (True/False: root buildings have no inputs, e.g. Mine, Farm)
├── node_building (True/False: node buildings have inputs and outputs, e.g. Smelter, Sawmill)
└── terminal_building (True/False: terminal buildings have no outputs, e.g. World Exhibition Center, Bank)
```

### **Resources System**
```
resource_categories
├── id (Primary Key) 
├── name (Raw Materials, Agricultural, etc.)
└── description

resources
├── id (Primary Key)
├── name (Coal, Steel, Bread, etc.)
├── category_id → resource_categories.id
├── map_id → maps.id
├── plan_id → plans.id
└── is_consumable (TRUE/FALSE)
```

### **Building Relationships**
Associations for factory setups and production chains.
```
building_groups
├── id (Primary Key)
├── building_id → buildings.id
└── category_id → building_categories.id
```

Resource input/output, construction, and maintenance requirements.
```
building_inputs
├── building_id → buildings.id
├── resource_id → resources.id
└── quantity

building_outputs  
├── building_id → buildings.id
├── resource_id → resources.id
├── quantity
└── production_time

building_construction
├── building_id → buildings.id
├── resource_id → resources.id
└── quantity

building_maintenance
├── building_id → buildings.id
├── resource_id → resources.id
└── quantity
```
