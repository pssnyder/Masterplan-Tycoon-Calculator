#!/usr/bin/env python3
"""
Save Game Data Science Analysis Dashboard
Deep dive into game save file patterns and end-game state analysis
"""

import streamlit as st
import pandas as pd
import json
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta
from collections import Counter, defaultdict

# Page config
st.set_page_config(
    page_title="Save Game Data Analysis",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

@st.cache_data
def load_save_data():
    """Load and parse the complete save game data"""
    try:
        with open("../references/game_data_save0.json", 'r') as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Error loading save data: {e}")
        return {}

@st.cache_data
def analyze_nodes_data(nodes_data):
    """Analyze the Nodes array for building patterns"""
    if not nodes_data:
        return pd.DataFrame()
    
    # Convert nodes to DataFrame
    building_analysis = []
    
    for node in nodes_data:
        analysis_row = {
            'node_id': node.get('ID', 'unknown'),
            'building_type': node.get('ConfigID', 'unknown'),  # Use ConfigID instead of BuildingType
            'position_x': node.get('Position', {}).get('X', 0),
            'position_y': node.get('Position', {}).get('Y', 0),
            'is_completed': node.get('Construction', {}).get('IsCompleted', False),  # Check Construction.IsCompleted
            'mission_location': node.get('ConfigID', 'unknown').split('.')[1] if '.' in node.get('ConfigID', '') else 'unknown',  # Extract location from ConfigID
            'efficiency': node.get('Efficiency', 1.0),
            'level': node.get('Level', 1),
        }
        
        # Extract resource data if available
        resources = node.get('Resources', {})
        if resources and isinstance(resources, dict):
            total_resources = sum(resources.values())
            analysis_row['resource_storage'] = len(resources)
            analysis_row['total_stored_resources'] = total_resources
        else:
            analysis_row['resource_storage'] = 0
            analysis_row['total_stored_resources'] = 0
            
        building_analysis.append(analysis_row)
    
    return pd.DataFrame(building_analysis)

@st.cache_data
def analyze_links_data(links_data):
    """Analyze the Links array for resource flow patterns"""
    if not links_data:
        return pd.DataFrame()
    
    links_analysis = []
    
    for link in links_data:
        # Extract location from the behavior type or use StuffTypeID
        stuff_type = link.get('StuffTypeID', 'unknown')
        location = stuff_type.split('.')[1] if '.' in stuff_type else 'unknown'
        
        link_row = {
            'link_id': link.get('ID', 'unknown'),
            'from_node': link.get('InNodeID', 'unknown'),  # Use InNodeID instead of From.NodeID
            'to_node': link.get('OutNodeID', 'unknown'),   # Use OutNodeID instead of To.NodeID
            'from_slot': 0,  # Not available in this data structure
            'to_slot': 0,    # Not available in this data structure
            'resource_type': stuff_type,  # Use StuffTypeID instead of Resource
            'mission_location': location,
            'is_active': True,  # Assume active since no field available
            'behaviour_type': link.get('BehaviourType', 'unknown'),
            'follower_progress': link.get('FollowerProgress', 0)
        }
        links_analysis.append(link_row)
    
    return pd.DataFrame(links_analysis)

@st.cache_data
def analyze_research_progress(research_data):
    """Analyze research/technology progression"""
    if not research_data:
        return pd.DataFrame()
    
    research_analysis = []
    
    # Get viewed and completed research lists
    viewed_researches = set(research_data.get('ViewedResearches', []))
    completed_researches = set(research_data.get('CompleteResearches', []))
    
    # Combine all unique research IDs
    all_researches = viewed_researches.union(completed_researches)
    
    for research_id in all_researches:
        research_row = {
            'research_id': research_id,
            'is_unlocked': research_id in completed_researches,
            'is_viewed': research_id in viewed_researches,
            'research_category': research_id.split('.')[1] if '.' in research_id else 'unknown'
        }
        research_analysis.append(research_row)
    
    return pd.DataFrame(research_analysis)

@st.cache_data
def load_supply_chain_data():
    """Load and process the CSV data for supply chain analysis"""
    try:
        buildings_df = pd.read_csv("../references/Masterplan Tycoon Building Calculations - buildings.csv")
        inputs_df = pd.read_csv("../references/Masterplan Tycoon Building Calculations - inputs.csv")
        outputs_df = pd.read_csv("../references/Masterplan Tycoon Building Calculations - outputs.csv")
        
        return buildings_df, inputs_df, outputs_df
    except Exception as e:
        st.error(f"Error loading supply chain data: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

def build_supply_chain_tree(target_category, buildings_df, inputs_df, outputs_df, max_depth=10, current_depth=0):
    """
    Recursively build supply chain dependency tree for a target category
    Returns a dictionary representing the dependency tree
    """
    if current_depth >= max_depth:
        return {"category": target_category, "depth": current_depth, "inputs": [], "buildings": [], "note": "Max depth reached"}
    
    # Find buildings that produce this category
    category_buildings = buildings_df[buildings_df['category'] == target_category]
    
    if category_buildings.empty:
        # This might be a raw resource
        return {"category": target_category, "depth": current_depth, "inputs": [], "buildings": [], "is_raw": True}
    
    # Get all the inputs needed for buildings in this category
    category_inputs = set()
    building_details = []
    
    for _, building in category_buildings.iterrows():
        buid = building['buid']
        building_inputs = inputs_df[inputs_df['buid'] == buid]
        
        building_detail = {
            "name": building['buildings'],
            "buid": buid,
            "plan": building['plan'],
            "tier": building['tier'],
            "inputs": []
        }
        
        for _, input_row in building_inputs.iterrows():
            input_resource = input_row['input']
            input_qty = input_row['input_qty']
            category_inputs.add(input_resource)
            building_detail["inputs"].append({"resource": input_resource, "quantity": input_qty})
        
        building_details.append(building_detail)
    
    # For each input resource, find what category produces it
    input_dependencies = []
    
    for input_resource in category_inputs:
        # Find which buildings produce this input
        producing_buildings = outputs_df[outputs_df['output'] == input_resource]
        
        if not producing_buildings.empty:
            # Get the categories that produce this resource
            producer_categories = set()
            for _, producer in producing_buildings.iterrows():
                producer_buid = producer['buid']
                producer_building = buildings_df[buildings_df['buid'] == producer_buid]
                if not producer_building.empty:
                    producer_categories.add(producer_building.iloc[0]['category'])
            
            # Recursively analyze each producer category
            for producer_category in producer_categories:
                if producer_category != target_category:  # Avoid infinite loops
                    dependency = build_supply_chain_tree(
                        producer_category, buildings_df, inputs_df, outputs_df, 
                        max_depth, current_depth + 1
                    )
                    dependency["produces_resource"] = input_resource
                    input_dependencies.append(dependency)
        else:
            # This is likely a raw resource
            input_dependencies.append({
                "category": input_resource,
                "depth": current_depth + 1,
                "inputs": [],
                "buildings": [],
                "is_raw": True,
                "produces_resource": input_resource
            })
    
    return {
        "category": target_category,
        "depth": current_depth,
        "buildings": building_details,
        "inputs": input_dependencies,
        "is_raw": False
    }

def create_supply_chain_network_graph(chain_tree, pos_x=0, pos_y=0, layout_width=1000, level_height=150):
    """Create network graph visualization of supply chain"""
    import networkx as nx
    
    G = nx.DiGraph()
    pos = {}
    node_colors = {}
    node_sizes = {}
    
    def add_nodes_recursive(tree, x, y, level):
        category = tree["category"]
        depth = tree.get("depth", 0)
        is_raw = tree.get("is_raw", False)
        
        # Add the main category node
        G.add_node(category)
        pos[category] = (x, y)
        
        # Color coding by type
        if is_raw:
            node_colors[category] = 'lightgreen'
            node_sizes[category] = 300
        elif depth == 0:
            node_colors[category] = 'red'  # Target category
            node_sizes[category] = 800
        else:
            node_colors[category] = 'lightblue'
            node_sizes[category] = 500
        
        # Process inputs
        inputs = tree.get("inputs", [])
        if inputs:
            input_width = layout_width / max(len(inputs), 1)
            for i, input_tree in enumerate(inputs):
                input_x = x - layout_width/2 + (i + 0.5) * input_width
                input_y = y + level_height
                
                input_category = input_tree["category"]
                produces_resource = input_tree.get("produces_resource", "")
                
                # Add edge with resource label
                G.add_edge(input_category, category, resource=produces_resource)
                
                # Recursively add input nodes
                add_nodes_recursive(input_tree, input_x, input_y, level + 1)
    
    add_nodes_recursive(chain_tree, pos_x, pos_y, 0)
    
    return G, pos, node_colors, node_sizes

def supply_chain_analysis(save_data):
    """Analyze supply chain dependencies from high-tier buildings down to raw resources"""
    st.header("🏭 Supply Chain Dependencies Analysis")
    st.markdown("**Trace production chains from high-tier buildings down to raw resources**")
    
    # Load supply chain data
    buildings_df, inputs_df, outputs_df = load_supply_chain_data()
    
    if buildings_df.empty:
        st.error("Could not load supply chain data from CSV files")
        return
    
    # Get unique categories sorted by max tier
    category_tiers = buildings_df.groupby('category')['tier'].max().sort_values(ascending=False)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("🎯 Select Target Category")
        
        # Show top tier categories
        st.write("**Highest Tier Categories:**")
        top_categories = category_tiers.head(10)
        for category, tier in top_categories.items():
            st.write(f"• **{category}** (Tier {tier})")
        
        # Category selector
        selected_category = st.selectbox(
            "Choose category to analyze:",
            options=list(category_tiers.index),
            index=0  # Default to highest tier
        )
        
        # Analysis depth selector
        max_depth = st.slider("Maximum analysis depth:", min_value=3, max_value=15, value=8)
        
    with col2:
        st.subheader("📊 Category Overview")
        
        if selected_category:
            selected_tier = category_tiers.loc[selected_category]
            st.metric("Selected Category Tier", int(selected_tier))
            
            # Buildings in this category
            category_buildings = buildings_df[buildings_df['category'] == selected_category]
            st.metric("Buildings in Category", len(category_buildings))
            
            # Plans that have this category
            plans = category_buildings['plan'].unique()
            st.write(f"**Available in Plans:** {', '.join(plans)}")
    
    if st.button("🔍 Analyze Supply Chain", type="primary"):
        with st.spinner(f"Building supply chain tree for {selected_category}..."):
            # Build the supply chain tree
            supply_tree = build_supply_chain_tree(
                selected_category, buildings_df, inputs_df, outputs_df, max_depth
            )
            
            # Display the tree structure
            st.subheader(f"🌳 Supply Chain Tree: {selected_category}")
            
            # Create network visualization
            try:
                G, pos, node_colors, node_sizes = create_supply_chain_network_graph(supply_tree)
                
                # Create plotly network graph
                edge_x = []
                edge_y = []
                edge_info = []
                
                for edge in G.edges(data=True):
                    x0, y0 = pos[edge[0]]
                    x1, y1 = pos[edge[1]]
                    edge_x.extend([x0, x1, None])
                    edge_y.extend([y0, y1, None])
                    edge_info.append(f"{edge[0]} → {edge[1]}<br>Resource: {edge[2].get('resource', 'Unknown')}")
                
                # Create node traces
                node_x = []
                node_y = []
                node_text = []
                node_color = []
                node_size = []
                
                for node in G.nodes():
                    x, y = pos[node]
                    node_x.append(x)
                    node_y.append(y)
                    node_text.append(node)
                    node_color.append(node_colors.get(node, 'lightblue'))
                    node_size.append(node_sizes.get(node, 500))
                
                # Create the plot
                fig = go.Figure()
                
                # Add edges
                fig.add_trace(go.Scatter(
                    x=edge_x, y=edge_y,
                    line=dict(width=2, color='gray'),
                    hoverinfo='none',
                    mode='lines'
                ))
                
                # Add nodes
                fig.add_trace(go.Scatter(
                    x=node_x, y=node_y,
                    mode='markers+text',
                    hoverinfo='text',
                    text=node_text,
                    textposition="middle center",
                    marker=dict(
                        size=[s/10 for s in node_size],
                        color=node_color,
                        line=dict(width=2, color='black')
                    )
                ))
                
                fig.update_layout(
                    title=f"Supply Chain Network: {selected_category}",
                    showlegend=False,
                    hovermode='closest',
                    margin=dict(b=20,l=5,r=5,t=40),
                    annotations=[ dict(
                        text="Red = Target Category, Green = Raw Resources, Blue = Intermediate Categories",
                        showarrow=False,
                        xref="paper", yref="paper",
                        x=0.005, y=-0.002,
                        xanchor='left', yanchor='bottom',
                        font=dict(size=12)
                    )],
                    xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
            except Exception as e:
                st.error(f"Could not create network visualization: {e}")
            
            # Display detailed tree structure
            st.subheader("📋 Detailed Supply Chain Breakdown")
            
            def display_tree_level(tree, level=0):
                indent = "  " * level
                category = tree["category"]
                is_raw = tree.get("is_raw", False)
                depth = tree.get("depth", 0)
                
                if is_raw:
                    st.write(f"{indent}🟢 **{category}** *(Raw Resource)*")
                else:
                    buildings = tree.get("buildings", [])
                    st.write(f"{indent}🏭 **{category}** *(Tier {buildings[0]['tier'] if buildings else '?'})*")
                    
                    if buildings:
                        for building in buildings:
                            st.write(f"{indent}  • {building['name']} ({building['plan']})")
                            for input_item in building['inputs']:
                                st.write(f"{indent}    - Needs: {input_item['quantity']}x {input_item['resource']}")
                
                # Recursively display inputs
                inputs = tree.get("inputs", [])
                for input_tree in inputs:
                    display_tree_level(input_tree, level + 1)
            
            display_tree_level(supply_tree)
            
            # Supply chain completeness check
            st.subheader("✅ Supply Chain Completeness Check")
            
            def check_completeness(tree, player_buildings):
                """Check if player has all required buildings for this supply chain"""
                completeness_report = {
                    "total_categories": 0,
                    "player_has": 0,
                    "missing": [],
                    "raw_resources": []
                }
                
                def check_recursive(subtree):
                    category = subtree["category"]
                    is_raw = subtree.get("is_raw", False)
                    
                    if is_raw:
                        completeness_report["raw_resources"].append(category)
                    else:
                        completeness_report["total_categories"] += 1
                        
                        # Check if player has buildings in this category
                        buildings = subtree.get("buildings", [])
                        has_building = False
                        
                        for building in buildings:
                            # Check against player's buildings (from save data)
                            config_pattern = building.get("name", "").lower().replace(" ", "").replace("(", "").replace(")", "")
                            if any(config_pattern in pb.lower() for pb in player_buildings):
                                has_building = True
                                break
                        
                        if has_building:
                            completeness_report["player_has"] += 1
                        else:
                            completeness_report["missing"].append({
                                "category": category,
                                "buildings": [b["name"] for b in buildings]
                            })
                    
                    # Check inputs recursively
                    for input_tree in subtree.get("inputs", []):
                        check_recursive(input_tree)
                
                check_recursive(tree)
                return completeness_report
            
            # Get player's buildings from save data
            if 'Nodes' in save_data:
                player_buildings = [node.get('ConfigID', '') for node in save_data['Nodes']]
                report = check_completeness(supply_tree, player_buildings)
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    completion_rate = report["player_has"] / max(report["total_categories"], 1)
                    st.metric("Supply Chain Completion", f"{completion_rate:.1%}")
                
                with col2:
                    st.metric("Categories Complete", f"{report['player_has']}/{report['total_categories']}")
                
                with col3:
                    st.metric("Raw Resources Needed", len(report["raw_resources"]))
                
                # Show missing buildings
                if report["missing"]:
                    st.write("**🚨 Missing Building Categories:**")
                    for missing in report["missing"]:
                        st.write(f"• **{missing['category']}**: {', '.join(missing['buildings'])}")
                
                # Show raw resources
                if report["raw_resources"]:
                    st.write("**🌿 Raw Resources Required:**")
                    for resource in sorted(set(report["raw_resources"])):
                        st.write(f"• {resource}")
            else:
                st.info("No player building data available for completeness check")

def main():
    st.title("🔬 Save Game Data Science Analysis")
    st.markdown("**Deep dive into your completed game state and patterns**")
    
    # Load save data
    save_data = load_save_data()
    if not save_data:
        st.error("Could not load save data")
        return
    
    # Sidebar for analysis selection
    st.sidebar.header("🎯 Analysis Focus")
    analysis_type = st.sidebar.selectbox(
        "Select Analysis Type",
        [
            "Game Overview & Statistics", 
            "Building Placement Patterns",
            "🏭 Supply Chain Dependencies",
            "Resource Flow Networks",
            "Technology Progression", 
            "End-Game State Analysis",
            "Efficiency & Performance"
        ]
    )
    
    # Main analysis
    if analysis_type == "Game Overview & Statistics":
        game_overview_analysis(save_data)
    elif analysis_type == "Building Placement Patterns":
        building_patterns_analysis(save_data)
    elif analysis_type == "🏭 Supply Chain Dependencies":
        supply_chain_analysis(save_data)
    elif analysis_type == "Resource Flow Networks":
        resource_flow_analysis(save_data)
    elif analysis_type == "Technology Progression":
        technology_analysis(save_data)
    elif analysis_type == "End-Game State Analysis":
        end_game_analysis(save_data)
    elif analysis_type == "Efficiency & Performance":
        efficiency_analysis(save_data)

def game_overview_analysis(save_data):
    """High-level game statistics and overview"""
    st.header("📊 Game Overview & Statistics")
    
    col1, col2, col3 = st.columns(3)
    
    # Player Statistics
    if 'PlayerStatistic' in save_data:
        stats = save_data['PlayerStatistic']
        
        with col1:
            st.subheader("🏗️ Construction Stats")
            st.metric("Resources Extracted", f"{stats.get('ResourcesExtracted', 0):,}")
            st.metric("Buildings Built", stats.get('NodesBuilt', 0))
            st.metric("Buildings Destroyed", stats.get('NodesDestroyed', 0))
            
            # Calculate efficiency
            if stats.get('NodesBuilt', 0) > 0:
                build_efficiency = 1 - (stats.get('NodesDestroyed', 0) / stats.get('NodesBuilt', 1))
                st.metric("Build Efficiency", f"{build_efficiency:.1%}")
        
        with col2:
            st.subheader("🔗 Logistics Stats")  
            st.metric("Links Created", f"{stats.get('LinksCreated', 0):,}")
            
            # Links per building ratio
            if stats.get('NodesBuilt', 0) > 0:
                links_per_building = stats.get('LinksCreated', 0) / stats.get('NodesBuilt', 1)
                st.metric("Links per Building", f"{links_per_building:.1f}")
        
        with col3:
            st.subheader("⏱️ Session Stats")
            session_time = stats.get('SessionSpendTime', 0)
            
            # Convert seconds to hours/minutes
            hours = session_time // 3600
            minutes = (session_time % 3600) // 60
            st.metric("Total Play Time", f"{hours}h {minutes}m")
            
            # Launch date
            launch_date = stats.get('SessionFirstLaunch', '')
            if launch_date:
                st.write(f"**Started:** {launch_date[:10]}")
    
    # System Information
    st.subheader("🎮 Game System Info")
    if 'System' in save_data:
        system = save_data['System']
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Version:** {system.get('Version', 'Unknown')}")
        with col2:
            st.write(f"**Map Seed:** {system.get('MapSeed', 'Unknown')}")
    
    # Data Structure Overview
    st.subheader("📁 Save Data Structure")
    
    data_summary = []
    for key, value in save_data.items():
        data_type = type(value).__name__
        if isinstance(value, (list, dict)):
            size = len(value)
            data_summary.append({
                'Section': key,
                'Type': data_type,
                'Size': size,
                'Description': get_section_description(key)
            })
        else:
            data_summary.append({
                'Section': key,
                'Type': data_type, 
                'Size': 1,
                'Description': get_section_description(key)
            })
    
    summary_df = pd.DataFrame(data_summary)
    st.dataframe(summary_df, use_container_width=True)

def building_patterns_analysis(save_data):
    """Analyze building placement and usage patterns"""
    st.header("🏗️ Building Placement Patterns")
    
    if 'Nodes' not in save_data:
        st.error("No building data found in save file")
        return
    
    # Analyze nodes data
    nodes_df = analyze_nodes_data(save_data['Nodes'])
    
    if nodes_df.empty:
        st.error("Could not parse building data")
        return
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Building type distribution
        st.subheader("Building Type Distribution")
        
        building_counts = nodes_df['building_type'].value_counts()
        
        fig = px.bar(
            x=building_counts.index[:20],  # Top 20 building types
            y=building_counts.values[:20],
            title="Most Built Building Types",
            labels={'x': 'Building Type', 'y': 'Count'}
        )
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)
        
        # Spatial distribution
        st.subheader("Building Spatial Distribution")
        
        fig = px.scatter(
            nodes_df,
            x='position_x',
            y='position_y', 
            color='mission_location',
            size='resource_storage',
            hover_data=['building_type', 'efficiency', 'level'],
            title="Building Positions by Region"
        )
        fig.update_yaxes(autorange="reversed")  # Flip Y axis for map-like view
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Key insights
        st.subheader("Building Insights")
        
        st.metric("Total Buildings", len(nodes_df))
        st.metric("Building Types", nodes_df['building_type'].nunique())
        st.metric("Regions", nodes_df['mission_location'].nunique())
        
        # Completion rate
        completion_rate = nodes_df['is_completed'].mean()
        st.metric("Completion Rate", f"{completion_rate:.1%}")
        
        # Average efficiency
        avg_efficiency = nodes_df['efficiency'].mean()
        st.metric("Average Efficiency", f"{avg_efficiency:.2f}")
        
        # Top building types
        st.write("**Most Built:**")
        for building, count in building_counts.head(8).items():
            st.write(f"• {building}: {count}")
    
    # Detailed building analysis
    st.subheader("Detailed Building Analysis")
    
    # Group by location and building type
    location_analysis = nodes_df.groupby(['mission_location', 'building_type']).size().reset_index(name='count')
    
    # Pivot for heatmap
    pivot_df = location_analysis.pivot(index='mission_location', columns='building_type', values='count').fillna(0)
    
    fig = px.imshow(
        pivot_df.values,
        x=pivot_df.columns,
        y=pivot_df.index,
        title="Building Distribution Heatmap (Location vs Type)",
        aspect='auto'
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Show the detailed table
    st.dataframe(nodes_df.head(20), use_container_width=True)

def resource_flow_analysis(save_data):
    """Analyze resource flow networks from Links data"""
    st.header("🔗 Resource Flow Networks")
    
    if 'Links' not in save_data:
        st.error("No links data found in save file")
        return
    
    links_df = analyze_links_data(save_data['Links'])
    
    if links_df.empty:
        st.error("Could not parse links data")
        return
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Resource flow patterns
        st.subheader("Resource Flow Patterns")
        
        resource_counts = links_df['resource_type'].value_counts()
        
        fig = px.bar(
            x=resource_counts.values[:15],
            y=resource_counts.index[:15],
            orientation='h',
            title="Most Transported Resources",
            labels={'x': 'Number of Links', 'y': 'Resource Type'}
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Network connectivity by location
        st.subheader("Network Connectivity by Region")
        
        location_connections = links_df['mission_location'].value_counts()
        
        fig = px.pie(
            values=location_connections.values,
            names=location_connections.index,
            title="Resource Links by Region"
        )
        st.plotly_chart(fig, use_container_width=True)
        
    with col2:
        st.subheader("Network Insights")
        
        st.metric("Total Links", len(links_df))
        st.metric("Resource Types", links_df['resource_type'].nunique())
        st.metric("Connected Regions", links_df['mission_location'].nunique())
        
        # Active links percentage
        active_rate = links_df['is_active'].mean() if 'is_active' in links_df else 1.0
        st.metric("Active Links", f"{active_rate:.1%}")
        
        st.write("**Top Resources:**")
        for resource, count in resource_counts.head(8).items():
            st.write(f"• {resource}: {count} links")
    
    # Network analysis
    st.subheader("Network Analysis")
    
    # Create network graph data
    if not links_df.empty:
        # Node connectivity analysis
        from_nodes = links_df['from_node'].value_counts()
        to_nodes = links_df['to_node'].value_counts()
        
        # Most connected nodes (buildings)
        st.write("**Most Connected Buildings (Output):**")
        for node, count in from_nodes.head(10).items():
            st.write(f"• Node {node}: {count} outgoing links")

def end_game_analysis(save_data):
    """Analyze the end-game state and victory patterns"""
    st.header("🎯 End-Game State Analysis")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Resource accumulation analysis
        st.subheader("Resource Accumulation Patterns")
        
        if 'GlobalStuffStorage' in save_data:
            global_storage = save_data['GlobalStuffStorage']
            
            if global_storage:
                storage_df = pd.DataFrame([
                    {'Resource': k, 'Amount': v} 
                    for k, v in global_storage.items()
                ])
                storage_df = storage_df.sort_values('Amount', ascending=False)
                
                fig = px.bar(
                    storage_df.head(20),
                    x='Amount',
                    y='Resource',
                    orientation='h',
                    title="Global Resource Storage at Game End"
                )
                st.plotly_chart(fig, use_container_width=True)
        
        # Research completion analysis
        st.subheader("Technology Progression")
        
        if 'Researches' in save_data:
            research_df = analyze_research_progress(save_data['Researches'])
            
            if not research_df.empty:
                completion_rate = research_df['is_unlocked'].mean()
                st.metric("Research Completion", f"{completion_rate:.1%}")
                
                # Research timeline if unlock times available
                unlocked_research = research_df[research_df['is_unlocked'] == True]
                st.write(f"**Unlocked Technologies:** {len(unlocked_research)}")
    
    with col2:
        st.subheader("Victory Analysis")
        
        # Game completion metrics
        if 'Quests' in save_data:
            quests = save_data['Quests']
            st.metric("Total Quests", len(quests))
            
            # Analyze quest completion if data available
            completed_quests = 0
            for quest_data in quests.values():
                if isinstance(quest_data, dict) and quest_data.get('IsCompleted', False):
                    completed_quests += 1
            
            if len(quests) > 0:
                quest_completion = completed_quests / len(quests)
                st.metric("Quest Completion", f"{quest_completion:.1%}")
        
        # Resource extraction efficiency
        if 'PlayerStatistic' in save_data:
            stats = save_data['PlayerStatistic']
            resources_per_building = stats.get('ResourcesExtracted', 0) / max(stats.get('NodesBuilt', 1), 1)
            st.metric("Resources per Building", f"{resources_per_building:,.0f}")

def get_section_description(section_key):
    """Get description for save file sections"""
    descriptions = {
        'ID': 'Game save identifier',
        'System': 'Game version and system info',
        'PlayerStatistic': 'Player performance metrics',
        'Missions': 'Mission and location data',
        'Researches': 'Technology/research progress',
        'Quests': 'Quest completion status',
        'GlobalStuffStorage': 'Global resource storage',
        'Nodes': 'Building placement and data',
        'Links': 'Resource connection networks',
        'Weather': 'Weather system state',
        'RenovationResourceZones': 'Resource zone data'
    }
    return descriptions.get(section_key, 'Unknown section')

def technology_analysis(save_data):
    """Analyze technology and research progression"""
    st.header("🔬 Technology Progression Analysis")
    
    if 'Researches' not in save_data:
        st.error("No research data found")
        return
    
    research_df = analyze_research_progress(save_data['Researches'])
    
    if research_df.empty:
        st.error("Could not parse research data")
        return
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Research completion overview
        completion_counts = research_df['is_unlocked'].value_counts()
        
        fig = px.pie(
            values=completion_counts.values,
            names=['Unlocked' if x else 'Locked' for x in completion_counts.index],
            title="Research Completion Status"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Research by category
        if 'research_category' in research_df.columns:
            category_counts = research_df['research_category'].value_counts()
            
            fig = px.bar(
                x=category_counts.index,
                y=category_counts.values,
                title="Research Distribution by Category",
                labels={'x': 'Category', 'y': 'Count'}
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Completion rate by category
            category_completion = research_df.groupby('research_category')['is_unlocked'].agg(['count', 'sum'])
            category_completion['completion_rate'] = category_completion['sum'] / category_completion['count']
            category_completion = category_completion.sort_values('completion_rate', ascending=False)
            
            fig = px.bar(
                x=category_completion.index,
                y=category_completion['completion_rate'],
                title="Completion Rate by Research Category",
                labels={'x': 'Category', 'y': 'Completion Rate'}
            )
            fig.update_layout(yaxis_tickformat='.0%')
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Research Insights")
        
        total_research = len(research_df)
        unlocked_research = research_df['is_unlocked'].sum()
        viewed_research = research_df['is_viewed'].sum()
        
        st.metric("Total Research", total_research)
        st.metric("Unlocked", unlocked_research)
        st.metric("Viewed", viewed_research)
        st.metric("Completion Rate", f"{unlocked_research/total_research:.1%}")
        
        # Show research categories breakdown
        if 'research_category' in research_df.columns:
            st.write("**Categories:**")
            category_counts = research_df['research_category'].value_counts()
            for category, count in category_counts.items():
                st.write(f"• {category}: {count}")
    
    # Detailed research table
    st.subheader("📋 Research Details")
    display_df = research_df.copy()
    display_df['Status'] = display_df['is_unlocked'].map({True: '✅ Unlocked', False: '🔒 Locked'})
    display_df['Viewed'] = display_df['is_viewed'].map({True: '👀 Viewed', False: '🔍 Not Viewed'})
    
    st.dataframe(
        display_df[['research_id', 'research_category', 'Status', 'Viewed']], 
        use_container_width=True
    )

def efficiency_analysis(save_data):
    """Analyze efficiency and performance patterns"""
    st.header("⚡ Efficiency & Performance Analysis")
    
    # Combine multiple data sources for efficiency analysis
    efficiency_metrics = {}
    
    if 'PlayerStatistic' in save_data:
        stats = save_data['PlayerStatistic']
        
        # Calculate various efficiency ratios
        nodes_built = stats.get('NodesBuilt', 1)
        resources_extracted = stats.get('ResourcesExtracted', 0)
        links_created = stats.get('LinksCreated', 0)
        session_time = stats.get('SessionSpendTime', 1)
        
        efficiency_metrics = {
            'Resources per Building': resources_extracted / nodes_built,
            'Links per Building': links_created / nodes_built,
            'Buildings per Hour': (nodes_built * 3600) / session_time,
            'Resources per Hour': (resources_extracted * 3600) / session_time,
            'Build Efficiency': 1 - (stats.get('NodesDestroyed', 0) / nodes_built)
        }
    
    # Display efficiency metrics
    col1, col2, col3 = st.columns(3)
    
    metrics_list = list(efficiency_metrics.items())
    for i, (metric, value) in enumerate(metrics_list):
        col = [col1, col2, col3][i % 3]
        with col:
            if 'per Hour' in metric:
                st.metric(metric, f"{value:,.0f}")
            elif 'Efficiency' in metric:
                st.metric(metric, f"{value:.1%}")
            else:
                st.metric(metric, f"{value:.1f}")
    
    # Building efficiency analysis from Nodes data
    if 'Nodes' in save_data:
        nodes_df = analyze_nodes_data(save_data['Nodes'])
        
        if not nodes_df.empty:
            st.subheader("Building Performance Distribution")
            
            if 'efficiency' in nodes_df.columns:
                fig = px.histogram(
                    nodes_df,
                    x='efficiency',
                    title="Building Efficiency Distribution",
                    nbins=20
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Efficiency by building type
                efficiency_by_type = nodes_df.groupby('building_type')['efficiency'].mean().sort_values(ascending=False)
                
                fig = px.bar(
                    x=efficiency_by_type.values[:15],
                    y=efficiency_by_type.index[:15],
                    orientation='h',
                    title="Average Efficiency by Building Type"
                )
                st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    main()