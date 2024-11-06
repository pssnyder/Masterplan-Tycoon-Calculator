# Masterplan Tycoon Game Stats Dashboard

**Author**: Patrick Snyder  
**Creation Date**: 11/6/2024

## Description
This script creates a dashboard for displaying game statistics from the game "Masterplan Tycoon". The dashboard provides insights into various aspects of the game, such as player statistics, building data, and resource storage information.

The dashboard is built using **Tkinter** for the GUI and **Matplotlib** for visualizations. It dynamically loads game data from a save file (`sav_0.sav`) located in the current user's local directory (`C:\Users\<username>\AppData\LocalLow\Bureau Bravin\Masterplan Tycoon`). The data is then processed and displayed across three tabs:

1. **Player Stats**: Displays key player metrics such as resources extracted, links created, and session time. The developer shares these once you beat the game, but I wanted to know them all the time.
2. **Buildings**: Lists all constructed buildings and their counts so you have an idea of how large your infrastructure is.
3. **Resources by Location**: Shows resources stored at different locations along with their percentage of storage capacity, sorted least to most per location so you can tell where you are low on resources.

## Features
- Dynamically loads game data from save file 0 (save slot 1) based on the current user's directory.
- Displays player stats in a clean format.
- Provides a scrollable table of buildings and their counts.
- Shows a scrollable list of resources by location with percentages indicating how full each storage is.

## Usage
1. Run `masterplan_analysis.py` in Python.
2. Wait for the calculation to complete.
3. If you receive an error like "save file not found", go into the script and update the file location and save file name to match your installation. I made the assumption that the game always writes to the same location. Also, I only pull in Save Slot 1. If you want to access data from another save slot, you can adjust the save file name accordingly.

## Future Ideas
- Add a Save Slot selector so you can dynamically choose more than just slot 1.
- Add an auto-refresh feature so you don't need to re-run the script to update it.
- Add warnings for low resource counts that trigger suggestions for additional required infrastructure trees.
- Display a building hierarchy tree to show dependency support infrastructure for buildings and its current capacity.
- Add a production calculator to calculate building needs depending on scenarios (e.g., "I want 1 Kerosene Lamp, what infrastructure do I need in order to produce it and how long will it take?").
