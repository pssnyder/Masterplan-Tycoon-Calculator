import pandas as pd

# Load the CSV data
df = pd.read_csv('game_data.csv')

# Extract unique counts
unique_buildings = df['Building'].unique()
unique_resources = df['Resource'].unique()

# Count the total number of unique items
unique_building_count = len(unique_buildings)
unique_resource_count = len(unique_resources)


def get_resources_by_building(building_name, resource_type, quantity):
    # Load the CSV data
    df = pd.read_csv('game_data.csv')
    
    # Filter for the specified building and type
    resources_df = df[(df['Building'] == building_name) & (df['Resource Type'] == resource_type)]
    
    # Create a dictionary to hold resource requirements
    resource_requirements = {}
    
    # Populate the dictionary with resources and quantities needed
    for _, row in resources_df.iterrows():
        resource_name = row['Resource']
        resource_quantity = row['Resource Quantity'] * quantity  # Multiply by requested quantity
        if resource_name in resource_requirements:
            resource_requirements[resource_name] += resource_quantity
        else:
            resource_requirements[resource_name] = resource_quantity
    
    return resource_requirements

def get_buildings_by_resource(resource_name, quantity):
    # Load the CSV data
    df = pd.read_csv('game_data.csv')
    
    # Filter for the specified building and type
    buildings_df = df[(df['Resource'] == resource_name) & (df['Resource Type'] == "Output Resource")]
    
    # Create a dictionary to hold building requirements
    building_requirements = {}
    
    # Populate the dictionary with resources and quantities needed
    for _, row in buildings_df.iterrows():
        building_name = row['Building']
        building_quantity = row['Resource Quantity'] / quantity  # Multiply by requested quantity
        if building_name in building_requirements:
            building_requirements[building_name] += building_quantity
        else:
            building_requirements[building_name] = building_quantity
    
    return building_requirements


# Output the result
print(f"Total number of unique buildings: {unique_building_count}")
print(f"Total number of unique resources: {unique_resource_count}")

# Call the function for the World Exhibition building
building_name = 'World Exhibition'
resource_type = 'Output Resource'
resource_name = 'Win'
quantity = 1
build_resources = get_resources_by_building(building_name, "Build Resources", quantity)
maintenance_resources = get_resources_by_building(building_name, "Maintenance Resources", quantity)
input_resources = get_resources_by_building(building_name, "Input Resources", quantity)
production_buildings = get_buildings_by_resource(resource_name, quantity)

# Display results if not None
if build_resources:
    print(f"\nBuild Resources for {building_name}:")
    for resource, qty in build_resources.items():
        print(f"{resource}: {qty}")

if maintenance_resources:
    print(f"\nMaintenance Resources for {building_name}:")
    for resource, qty in maintenance_resources.items():
        print(f"{resource}: {qty}")

if input_resources:
    print(f"\nInput Resources for {building_name}:")
    for resource, qty in input_resources.items():
        print(f"{resource}: {qty}")

if production_buildings:
    print(f"\nBuildings producing {resource_name}:")
    for building in production_buildings:
        print(building)

print(f'\nRequired buildings for producing {quantity} units of {resource_name}:')
for building, qty in production_buildings.items():
    if pd.notna(building):  # Ensure building name is not NaN
        print(f'{building}: {qty}')
        
# Example call for a resource that does not exist to demonstrate error handling
#print("\n")
#get_building_resources('Fake Building', 1)
#get_maintenance_resources('Fake Building', 1)
#get_input_resources('Fake Building', 1)
#get_buildings_producing_resource('Unicorn Dust')