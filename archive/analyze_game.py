import tkinter as tk
from tkinter import ttk
import json
from collections import Counter
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Load the JSON data from the file
with open('game_data_save0.json', 'r') as file:
    data = json.load(file)

# Extract game metadata
def get_game_metadata(data):
    return {
        "Version": data.get('System', {}).get('Version', 'Unknown'),
        "Map Seed": data.get('System', {}).get('MapSeed', 'Unknown'),
        "Last Active Location": data.get('Missions', {}).get('LastActiveMission', 'None')
    }

# Extract player statistics
def get_player_statistics(data):
    stats = data.get('PlayerStatistic', {})
    
    # Store raw values for calculations
    resources_extracted_raw = stats.get('ResourcesExtracted', 0)
    
    # Calculate hours, minutes, and seconds
    total_seconds = stats.get('SessionSpendTime', 0)
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    # Format the time as HH:MM:SS with zero-padding for minutes and seconds
    session_time = f"{hours}:{minutes:02}:{seconds:02}"
    
    # Return both raw and formatted values
    return {
        "ResourcesExtracted": f"{resources_extracted_raw:,}",  # Formatted with commas
        "ResourcesExtractedRaw": resources_extracted_raw,  # Raw value for calculations
        "Links Created": f"{stats.get('LinksCreated', 0):,}",
        "Buildings Built": f"{stats.get('NodesBuilt', 0):,}",
        "Buildings Destroyed": f"{stats.get('NodesDestroyed', 0):,}",
        "Session Started": stats.get('SessionFirstLaunch', 'Unknown'),
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
            building_counter[building_name] += 1
    return dict(building_counter.most_common())  # Sort by most common

# Analyze resource (stuff) data
def analyze_resources(data):
    resource_counter = Counter()
    resources = data.get('GlobalStuffStorage', {})
    for location, resource_data in resources.items():
        for resource, amount in resource_data.items():
            resource = resource.split('.')[1]  # Extract resource name after 'stuff.'
            resource_counter[resource] += amount
    return dict(resource_counter.most_common())  # Sort by most common

# Create the GUI window
class GameStatusGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Game Status Dashboard")
        
        # Create tabs for different sections: Player Stats, Buildings, Resources
        self.tab_control = ttk.Notebook(root)
        
        self.player_stats_tab = ttk.Frame(self.tab_control)
        self.buildings_tab = ttk.Frame(self.tab_control)
        self.resources_tab = ttk.Frame(self.tab_control)
        
        self.tab_control.add(self.player_stats_tab, text='Player Stats')
        self.tab_control.add(self.buildings_tab, text='Buildings')
        self.tab_control.add(self.resources_tab, text='Resources')
        
        self.tab_control.pack(expand=1, fill="both")
        
        # Display Player Statistics
        self.display_player_stats()
        
        # Display Buildings Table
        self.display_buildings_table()
        
        # Display Resources Table
        self.display_resources_table()
    
    def display_player_stats(self):
        player_stats = get_player_statistics(data)
        
        # Create labels to display player statistics in the Player Stats tab
        row = 0
        for key, value in player_stats.items():
            label_key = tk.Label(self.player_stats_tab, text=f"{key}:")
            label_key.grid(row=row, column=0, padx=10, pady=5, sticky=tk.W)
            
            label_value = tk.Label(self.player_stats_tab, text=str(value))
            label_value.grid(row=row, column=1, padx=10, pady=5)
            
            row += 1
        
        # Add a gauge for Resources Extracted using Matplotlib
        fig, ax = plt.subplots(figsize=(2.5, 2.5))
        
        # Use the raw value for calculations in the pie chart
        ax.pie([player_stats['ResourcesExtractedRaw'], 10000000 - player_stats['ResourcesExtractedRaw']],
        labels=['Extracted', 'Remaining'], autopct='%1.1f%%')
        
        ax.set_title("Resources Extracted")
        
        canvas = FigureCanvasTkAgg(fig, master=self.player_stats_tab)
        canvas.draw()
        
        canvas.get_tk_widget().grid(row=row + 1, columnspan=2)

    def display_buildings_table(self):
        buildings = analyze_buildings(data)
        
        # Create a table for Buildings in the Buildings tab using Treeview
        tree = ttk.Treeview(self.buildings_tab, columns=("Building", "Count"), show="headings", height=40)
        
        tree.heading("Building", text="Building")
        tree.heading("Count", text="Count")
        
        tree.column("Building", width=400)
        
        # Insert building data into the table
        for building, count in buildings.items():
            tree.insert("", tk.END, values=(building.capitalize(), count))
            
        tree.pack(padx=10, pady=10)

    def display_resources_table(self):
        resources = analyze_resources(data)
        
        # Create a table for Resources in the Resources tab using Treeview
        tree = ttk.Treeview(self.resources_tab, columns=("Resource", "Amount"), show="headings", height=40)
        
        tree.heading("Resource", text="Resource")
        tree.heading("Amount", text="Amount")
        
        tree.column("Resource", width=400)
        
        # Insert resource data into the table
        for resource, amount in resources.items():
            tree.insert("", tk.END, values=(resource.capitalize(), amount))
            
        tree.pack(padx=10, pady=10)

# Run the GUI application
if __name__ == "__main__":
    root = tk.Tk()
    app = GameStatusGUI(root)
    root.mainloop()