import pandas as pd
import math
import numpy as np
from collections import defaultdict

# Load the CSV data
df = pd.read_csv('game_data.csv')

def get_specific_resource_type(building_name, resource_type, quantity):
    # Input: Building you want to view specific resource requirements for, the resource type requested (Build Resource, Maintenance Resource, Input Resource, Output Resource)
    # Output: All resources required by this building for production
    resources_df = df[(df['Building'] == building_name) & (df['Resource Type'] == resource_type)]
    resource_requirements = {}
    for _, row in resources_df.iterrows():
        resource_name = row['Resource']
        resource_quantity = row['Resource Quantity'] #* quantity
        if resource_name in resource_requirements:
            resource_requirements[resource_name] += resource_quantity
        else:
            resource_requirements[resource_name] = resource_quantity
    return resource_requirements

def get_production_resources(building_name,  quantity):
    # Input: Building you want to view all resource requirements of
    # Output: All resources required by this building for production
    resources_df = df[(df['Building'] == building_name) & (df['Resource Type'].isin(["Input Resource", "Maintenance Resource"]))]
    resource_requirements = {}
    for _, row in resources_df.iterrows():
        resource_name = row['Resource']
        resource_quantity = row['Resource Quantity'] #* quantity
        if resource_name in resource_requirements:
            resource_requirements[resource_name] += resource_quantity
        else:
            resource_requirements[resource_name] = resource_quantity
    return resource_requirements

def get_production_buildings(resource_name, quantity):
    # Input: Name of Resource you want to produce and how many
    # Output: List of Buildings that produce that resource and quantity required
    buildings_df = df[(df['Resource'] == resource_name) & (df['Resource Type'] == "Output Resource")]
    building_requirements = {}
    for _, row in buildings_df.iterrows():
        if row['Tier'] != 0:
            building_name = row['Building']
            building_quantity = row['Resource Quantity'] / quantity
            if building_name in building_requirements:
                building_requirements[building_name] += building_quantity
            else:
                building_requirements[building_name] = building_quantity
    return building_requirements

def get_building_tier(building_name):
    # Input: Name of building you want to know the tier of
    # Output: The numeric tier of the building
    buildings_df = df[(df['Building'] == building_name) & (df['Resource Type'] == "Output Resource")]
    building_tier = buildings_df.iat[0,df.columns.get_loc('Tier')]
    return building_tier

def get_resource_dependencies(building_name):
    # Input: Name of building you want to find all resource dependencies for
    # Output: Name of buildings that are required for target building
    if building_name == "None":
        return
    # resources_df = df[(df['Building'] == building_name) & (df['Resource Type'].isin(["Build Resource","Input Resource", "Maintenance Resource"]))] # All
    resources_df = df[(df['Building'] == building_name) & (df['Resource Type'].isin(["Input Resource", "Maintenance Resource"]))] # Only Maintenance and Inputs
    #resources_df = df[(df['Building'] == building_name) & (df['Resource Type'].isin(["Input Resource"]))] # Only Inputs
    resource_dependencies = {}
    for _, row in resources_df.iterrows():
        building = row['Resource Dependency']
        resource_quantity = row['Resource Quantity'] #* quantity
        if building in resource_dependencies:
            resource_dependencies[building] += resource_quantity
        else:
            resource_dependencies[building] = resource_quantity
    return resource_dependencies

def get_dependency_counts():
    # Output: the count of all building dependencies needed.
    dependencies_df = df[(df['Resource Type'].isin(["Build Resource","Input Resource", "Maintenance Resource"]))]
    building_dependencies = {}
    for _, row in dependencies_df.iterrows():
        building = row['Resource Dependency']
        building_quantity = row['Resource Quantity']
        if building in building_dependencies:
            building_dependencies[building] += building_quantity
        else:
            building_dependencies[building] = building_quantity
        
        # Keep the counts from getting out of control
        while building_dependencies[building] >= 50:
                building_dependencies[building] = round(building_dependencies[building] / 2)
    return building_dependencies

# Helper Functions
def is_nan(value):
    """Helper function to check if a value is NaN."""
    try:
        return math.isnan(value) or np.isnan(value)
    except TypeError:
        return False  # If value is not a number, it's not NaN

# Primary Recursive Search for Dependencies
def recursive_search(building_name, counter=0, max_depth=20, building_counts=None):
    
    if building_counts is None:
        building_counts = defaultdict(int)
    
    # Prevent runaway recursion
    if counter >= max_depth:
       return building_counts

    # Accumulate all buildings needed
    all_dependencies = get_resource_dependencies(building_name)

    # For each required resource, find out which buildings produce it
    for building in all_dependencies.keys():
        if building and building != "None" and not (is_nan(building)):
            counter += 1
            # Print the results of this buildings requirements
            #print(f"'{building_name}' requires a '{building}'")
            #if get_building_tier(dependency_building) == 0:
            #    return
            if building_counts[building] >= 50:
                return building_counts
            building_counts[building] += 1
            recursive_search(building, counter, max_depth, building_counts)
            
    return building_counts

# Run the program on a target resource
#building_counts = recursive_search("World Exhibition")
building_counts = get_dependency_counts()

# Print the final counts of each building found in the recursive search
print("Building counts:")
for building, count in building_counts.items():
    print(f"{building}: {count}")