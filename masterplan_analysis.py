"""
Masterplan Tycoon Game Stats Dashboard

Author: Patrick Snyder
Creation Date: 11/6/2024

Description:
This script creates a dashboard for displaying game statistics from the game 
"Masterplan Tycoon". The dashboard provides insights into various aspects of the 
game, such as player statistics, building data, and resource storage information.

The dashboard is built using Tkinter for the GUI and Matplotlib for visualizations. It dynamically 
loads game data from a save file (`sav_0.sav`) located in the current user's local directory 
(`C:\\Users\\<username>\\AppData\\LocalLow\\Bureau Bravin\\Masterplan Tycoon`). The data is then processed 
and displayed across three tabs:
    1. Player Stats: Displays key player metrics such as resources extracted, links created, and session time. 
        The developer shares these once you beat the game but I wanted to know them all the time.
    2. Buildings: Lists all constructed buildings and their counts so you have an idea of how large your infrastructure is.
    3. Resources by Location: Shows resources stored at different locations along with their percentage of storage capacity, 
        sorted least to most per location so you can tell where you are low on resources.

Features:
- Dynamically loads game data from save file 0 (save slot 1) based on the current user's directory.
- Displays player stats in a clean format.
- Provides a scrollable table of buildings and their counts.
- Shows a scrollable list of resources by location with percentages indicating how full each storage is.

Usage:
- Run masterplan_analysis.py in python
- Wait for the calculation to perform
- If you receive an error save file not found. Then you can go into the script and update the file location and save file name
    to match your installation. I made the assumption the game always writes to the same location. Also I only pull in
    Save Slot 1. If you want to access data from another save slot you can adjust the save file name below.

Future Ideas:
- Add a Save Slot selector so you can dynamically choose more than just slot 1
- Add an auto refresh so you don't need to re-run the script to update it
- Add warnings for low resource counts that trigger suggestions for additional required infrastructure trees
- Display a building hierarchy tree to show dependency support infrastructure for buildings and its current capacity
- Add a production calculator to calculate building needs depending on scenario. i.e. I want 1 Kerosene Lamp, what infrastructure do I need in order to produce it and how long will it take?

"""

import os
import getpass
import tkinter as tk
from tkinter import ttk
import json
from collections import Counter
from datetime import datetime

# Find the save file in the current user's directory
def find_save_file():
    
    # Try to automatically set the username and save file path
    # DON'T UPDATE THESE
    username = getpass.getuser()  # Get current Windows username
    save_dir = os.path.join('C:', 'Users', username, 'AppData', 'LocalLow', 'Bureau Bravin', 'Masterplan Tycoon')
    save_file = os.path.join(save_dir, 'save_0.sav')
    
    
    # CUSTOM username AND filepath
    # If the script isn't running, you can hard code in your username, file path, and filename below
    # Override username by uncommenting next line
    #username = "myusername"
    
    # Override directory by uncommenting next line (be sure to use the "\\" escape character)
    #save_dir = os.path("C:\\This\\is\\the\\custom\\file\\path")

    # Override the target save file by uncommenting the next line (Slot 1 = save_0, Slot 2 = save_1, etc)
    #save_file = os.path.join(save_dir, 'save_1.sav')
    
    # END User Configuration
    
    if os.path.exists(save_file):
        return save_file
    else:
        print(f"Save file not found at {save_file}")
        return None

# Load the JSON data from the save file
def load_save_data():
    save_file = find_save_file()
    
    if save_file:
        with open(save_file, 'r') as file:
            data = json.load(file)
        return data
    else:
        print("No save file found.")
        return None

def format_location_name(location_string):
    # Remove 'location.' prefix if it exists
    if location_string.startswith("location."):
        location_string = location_string.replace("location.", "", 1)
    
    # Step 2: Split the remaining string by '.'
    parts = location_string.split('.')
    
    # Step 3: Capitalize each part using title()
    capitalized_parts = [part.title() for part in parts]
    
    # Step 4: Join the parts back together with spaces (or another separator)
    formatted_name = ' '.join(capitalized_parts).capitalize()
    
    return formatted_name

# Extract player statistics
def get_player_statistics(data):
    stats = data.get('PlayerStatistic', {})
    
    # Store raw values for calculations
    resources_extracted_raw = stats.get('ResourcesExtracted', 0)
    
    # Format the session start date and time
    session_start = datetime.fromisoformat(stats.get('SessionFirstLaunch', 'Unknown')).strftime("%m/%d/%Y %I:%M %p")
    
    # Calculate hours, minutes, and seconds
    total_seconds = stats.get('SessionSpendTime', 0)
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    # Format the time as HH:MM:SS with zero-padding for minutes and seconds
    session_time = f"{hours}:{minutes:02}:{seconds:02}"
    
    # Return both raw and formatted values
    return {
        "Resources Extracted": f"{resources_extracted_raw:,}",  # Formatted with commas
        "Links Created": f"{stats.get('LinksCreated', 0):,}",
        "Buildings Constructed": f"{stats.get('NodesBuilt', 0):,}",
        "Buildings Deleted": f"{stats.get('NodesDestroyed', 0):,}",
        "Session Started": session_start,
        "Session Time": session_time
    }

# Analyze building (construction) data
def analyze_buildings(data):
    building_counter = Counter()
    nodes = data.get('Nodes', [])
    
    for node in nodes:
        config_id = node.get('ConfigID', '')
        if config_id.startswith('construction.'):
            building_name = config_id.split('.')[1]  # Extract building name after 'construction.'
            if building_name in ["master", "islands", "mountains"]:
                continue
            else:
                building_counter[building_name] += 1
    
    return dict(building_counter.most_common())  # Sort by most common

# Analyze resource (stuff) data and calculate percentage full for each item in each location
def analyze_storage(data):
    global_storage = data.get('GlobalStuffStorage', {})
    
    storage_analysis = {}
    
    for location, items in global_storage.items():
        max_capacity = max(items.values())  # Get the maximum value in this location
        
        # avoid division by zero
        if max_capacity == 0:
            continue
        
        # Calculate percentage full for each item in this location and sort by percentage
        sorted_items = sorted(
            {item.split('.')[1]: (amount / max_capacity) * 100 for item, amount in items.items()}.items(),
            key=lambda x: x[1]
        )
        
        storage_analysis[location] = sorted_items
    
    return storage_analysis

# Create the GUI window
class GameStatusGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Masterplan Tycoon Game Status Dashboard")

        # Create tabs for different sections: Player Stats, Buildings, Resources by Location
        self.tab_control = ttk.Notebook(root)
        
        self.player_stats_tab = ttk.Frame(self.tab_control)
        self.buildings_tab = ttk.Frame(self.tab_control)
        self.resources_tab = ttk.Frame(self.tab_control)

        self.tab_control.add(self.player_stats_tab, text='Player Stats')
        self.tab_control.add(self.buildings_tab, text='Buildings')
        self.tab_control.add(self.resources_tab, text='Resources by Location')
        
        self.tab_control.pack(expand=1, fill="both")

        # Load game data from sav_0.sav file dynamically based on user directory
        self.data = load_save_data()

        if self.data:
            # Display Player Statistics
            self.display_player_stats()
            
            # Display Buildings Table
            self.display_buildings_table()
            
            # Display Resources List by Location (showing percentage full)
            self.display_resources_table()
    
    def display_player_stats(self):
        player_stats = get_player_statistics(self.data)

        row = 0
        for key, value in player_stats.items():
            label_key = tk.Label(self.player_stats_tab, text=f"{key}:")
            label_key.grid(row=row, column=0, padx=10, pady=5, sticky=tk.W)
            
            label_value = tk.Label(self.player_stats_tab, text=str(value))
            label_value.grid(row=row, column=1, padx=10, pady=5)
            
            row += 1

    def display_buildings_table(self):
        buildings = analyze_buildings(self.data)

        tree = ttk.Treeview(self.buildings_tab, columns=("Building", "Count"), show="headings", height=40)
        
        tree.heading("Building", text="Building")
        tree.heading("Count", text="Count")
        
        tree.column("Building", width=400)

        for building_name, count in buildings.items():
            tree.insert("", tk.END, values=(building_name.capitalize(), count))
            
        tree.pack(padx=10, pady=10)

    def display_resources_table(self):
        storage_data = analyze_storage(self.data)

        tree = ttk.Treeview(self.resources_tab, columns=("Location", "Resource", "Percentage Full"), show="headings", height=40)
        
        tree.heading("Location", text="Location")
        tree.heading("Resource", text="Resource")
        tree.heading("Percentage Full", text="Percentage Full")

        tree.column("Location", width=200)
        tree.column("Resource", width=200)
        
        # Insert resource data into the table with formatted location names and percentages sorted from lowest to highest
        for location_name, items in storage_data.items():
            formatted_location_name = format_location_name(location_name)
            
            for item_name, percentage_full in items:
                tree.insert("", tk.END, values=(formatted_location_name.capitalize(), item_name.capitalize(), f"{percentage_full:.2f}%"))
            
        tree.pack(padx=10, pady=10)

# Run the GUI application
if __name__ == "__main__":
    root = tk.Tk()
    app = GameStatusGUI(root)
    root.mainloop()