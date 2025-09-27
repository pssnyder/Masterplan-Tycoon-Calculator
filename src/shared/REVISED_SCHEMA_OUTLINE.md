# Masterplan Tycoon Database Schema - REVISED
## Based on Cleaned Source of Truth (SoT) Data

## 🎯 **KEY INSIGHTS FROM NEW DATA:**
- **Recipes are unlocked at tiers** (not categories) - recipes represent production chains
- **Building + Map combination is unique** - same building type can exist on different maps
- **Resources are map-specific** - same resource can be produced/consumed on different maps  
- **Plans are missions within maps** - multiple plans per map

## 📊 **REVISED SCHEMA:**

### **1. Maps Table**
Base regional areas where gameplay takes place.
```sql
maps (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE NOT NULL  -- Master, Islands, Mountains
)
```

### **2. Plans Table** 
Specific missions/scenarios within each map.
```sql  
plans (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,        -- Master, Brick Mission, Death Island, etc.
    map_id INTEGER,            -- Links to maps.id
    FOREIGN KEY (map_id) REFERENCES maps(id)
)
```

### **3. Recipes Table**
Production chains unlocked at specific tiers. Each recipe represents a complete production setup.
```sql
recipes (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,        -- Poncho, Bread, Steel Beams, etc.
    tier INTEGER NOT NULL,     -- 0-12 (tier when recipe unlocks)
    description TEXT
)
```

### **4. Buildings Table**
Individual building types that can be constructed. Building + Map = unique combination.
```sql
buildings (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,        -- Bakery, Coal Mine, etc.  
    map_id INTEGER,            -- Which map this building exists on
    building_id TEXT UNIQUE,   -- Generated: MAP#-TIER#-RECIPE_ABBR-BUILDING_ABBR
    FOREIGN KEY (map_id) REFERENCES maps(id),
    UNIQUE(name, map_id)       -- Same building can exist on multiple maps
)
```

### **5. Resources Table** 
Resources that can be produced/consumed. Resource + Map = unique combination.
```sql
resources (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,        -- Coal, Water, Steel Beams, etc.
    map_id INTEGER,            -- Which map this resource exists on  
    is_consumable BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (map_id) REFERENCES maps(id),
    UNIQUE(name, map_id)       -- Same resource can exist on multiple maps
)
```

### **6. Recipe_Buildings Table**
Links recipes to the buildings that are part of that recipe.
```sql
recipe_buildings (
    recipe_id INTEGER,
    building_id INTEGER,
    FOREIGN KEY (recipe_id) REFERENCES recipes(id),
    FOREIGN KEY (building_id) REFERENCES buildings(id),
    PRIMARY KEY (recipe_id, building_id)
)
```

### **7. Building Inputs/Outputs/Construction/Maintenance**
Resource requirements and production for each building+map combination.

```sql
building_inputs (
    building_id INTEGER,
    resource_id INTEGER, 
    quantity INTEGER,
    FOREIGN KEY (building_id) REFERENCES buildings(id),
    FOREIGN KEY (resource_id) REFERENCES resources(id),
    PRIMARY KEY (building_id, resource_id)
)

building_outputs (
    building_id INTEGER,
    resource_id INTEGER,
    quantity INTEGER,
    production_time_seconds INTEGER,
    output_per_minute REAL,
    FOREIGN KEY (building_id) REFERENCES buildings(id),
    FOREIGN KEY (resource_id) REFERENCES resources(id),
    PRIMARY KEY (building_id, resource_id)
)

building_construction (
    building_id INTEGER,
    resource_id INTEGER,
    quantity INTEGER,
    FOREIGN KEY (building_id) REFERENCES buildings(id), 
    FOREIGN KEY (resource_id) REFERENCES resources(id),
    PRIMARY KEY (building_id, resource_id)
)

building_maintenance (
    building_id INTEGER,
    resource_id INTEGER,
    quantity INTEGER,
    FOREIGN KEY (building_id) REFERENCES buildings(id),
    FOREIGN KEY (resource_id) REFERENCES resources(id), 
    PRIMARY KEY (building_id, resource_id)
)
```

## 🔄 **KEY RELATIONSHIPS:**
- Maps 1→N Plans (multiple missions per map)
- Recipes M→N Buildings (recipes contain multiple buildings)
- Buildings 1→N Inputs/Outputs/Construction/Maintenance
- Resources are map-specific (Water on Master ≠ Water on Islands)
- Buildings are map-specific (Bakery on Master ≠ Bakery on Mountains)

## ⚡ **UNIQUE IDENTIFIERS:**
- Building ID Format: `MAP#-TIER#-RECIPE_ABBR-BUILDING_ABBR`
- Example: `1-01-B-BM` = Master(1) - Tier01 - Bread(B) - Bakery+Master(BM)

## 🎯 **BUSINESS LOGIC:**
- Recipes unlock at specific tiers, making all associated buildings available
- Same recipe can have different buildings on different maps  
- Resource production/consumption is map-specific
- Complete supply chains traced through recipe → building → resource relationships

Does this schema capture your cleaned data structure correctly? Should we proceed with building the database using this approach?