#!/usr/bin/env python3
"""
Game Resource Management Analysis Dashboard
A generalized tool for analyzing building/resource chain dependencies in management games

This focuses on end-game state analysis to understand:
- Resource flow patterns
- Production chain dependencies  
- Optimization opportunities
- Building efficiency metrics
"""

import streamlit as st
import pandas as pd
import json
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import networkx as nx
import numpy as np
from pathlib import Path
import sqlite3

# Page config
st.set_page_config(
    page_title="Game Resource Analysis Dashboard",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

@st.cache_data
def load_game_save_data(file_path: str = "../references/game_data_save0.json") -> dict:
    """Load and cache the game save data"""
    with open(file_path, 'r') as f:
        return json.load(f)

@st.cache_data
def load_csv_data():
    """Load all CSV reference data"""
    data = {}
    csv_files = {
        'buildings': '../references/Masterplan Tycoon Building Calculations - buildings.csv',
        'inputs': '../references/Masterplan Tycoon Building Calculations - inputs.csv',
        'outputs': '../references/Masterplan Tycoon Building Calculations - outputs.csv',
        'construction': '../references/Masterplan Tycoon Building Calculations - construction.csv',
        'maintenance': '../references/Masterplan Tycoon Building Calculations - maintenance.csv'
    }
    
    for key, path in csv_files.items():
        try:
            data[key] = pd.read_csv(path)
        except FileNotFoundError:
            st.warning(f"Could not find {path}")
            data[key] = pd.DataFrame()
    
    return data

@st.cache_data
def analyze_resource_flows(inputs_df, outputs_df):
    """Analyze resource production and consumption patterns"""
    
    # Resource producers
    producers = outputs_df.groupby('output').agg({
        'building': 'nunique',
        'output_qty': 'sum',
        'outputs_per_minute': 'sum'
    }).round(2)
    producers.columns = ['producer_buildings', 'total_output_qty', 'total_per_minute']
    
    # Resource consumers  
    consumers = inputs_df.groupby('input').agg({
        'building': 'nunique',
        'input_qty': 'sum'
    }).round(2)
    consumers.columns = ['consumer_buildings', 'total_consumption']
    
    # Combine for flow analysis
    flow_analysis = producers.join(consumers, how='outer').fillna(0)
    flow_analysis['net_production'] = flow_analysis['total_per_minute'] - flow_analysis['total_consumption']
    flow_analysis['supply_demand_ratio'] = np.where(
        flow_analysis['total_consumption'] > 0,
        flow_analysis['total_per_minute'] / flow_analysis['total_consumption'],
        np.inf
    )
    
    return flow_analysis.sort_values('net_production', ascending=False)

@st.cache_data  
def create_supply_chain_network(inputs_df, outputs_df):
    """Create network graph of supply chain dependencies"""
    G = nx.DiGraph()
    
    # Add nodes for all resources
    all_resources = set(inputs_df['input'].unique()) | set(outputs_df['output'].unique())
    for resource in all_resources:
        G.add_node(resource, type='resource')
    
    # Add building nodes and connections
    for _, building_data in outputs_df.iterrows():
        building = building_data['building']
        output_resource = building_data['output']
        
        # Add building node
        if not G.has_node(building):
            G.add_node(building, type='building')
        
        # Building produces resource
        G.add_edge(building, output_resource, 
                  weight=building_data['outputs_per_minute'],
                  type='production')
    
    for _, building_data in inputs_df.iterrows():
        building = building_data['building']
        input_resource = building_data['input']
        
        # Add building node
        if not G.has_node(building):
            G.add_node(building, type='building')
            
        # Resource consumed by building
        G.add_edge(input_resource, building,
                  weight=building_data['input_qty'], 
                  type='consumption')
    
    return G

def main():
    st.title("🏗️ Game Resource Management Analysis Dashboard")
    st.markdown("**Generalized tool for analyzing building/resource dependencies in management games**")
    
    # Sidebar controls
    st.sidebar.header("📊 Analysis Controls")
    
    analysis_mode = st.sidebar.selectbox(
        "Analysis Focus",
        ["End-Game State Analysis", "Resource Flow Patterns", "Production Chain Optimization", "Building Efficiency"]
    )
    
    # Load data
    with st.spinner("Loading game data..."):
        try:
            save_data = load_game_save_data()
            csv_data = load_csv_data()
            st.sidebar.success("✅ Data loaded successfully")
        except Exception as e:
            st.error(f"Error loading data: {e}")
            return
    
    # Main analysis based on mode
    if analysis_mode == "End-Game State Analysis":
        end_game_analysis(save_data, csv_data)
    elif analysis_mode == "Resource Flow Patterns":
        resource_flow_analysis(csv_data)
    elif analysis_mode == "Production Chain Optimization":
        production_chain_analysis(csv_data)
    elif analysis_mode == "Building Efficiency":
        building_efficiency_analysis(csv_data)

def end_game_analysis(save_data, csv_data):
    """Analyze the end-game state from save file"""
    st.header("🎯 End-Game State Analysis")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Save File Structure")
        
        # Explore save file structure
        if st.checkbox("Show raw save file keys"):
            st.json(list(save_data.keys())[:20])  # Show first 20 keys
        
        # Extract key metrics from save data
        st.subheader("Game State Metrics")
        
        # Try to extract meaningful data
        metrics_found = {}
        
        # Look for common game state indicators
        for key, value in save_data.items():
            if isinstance(value, (int, float)) and key.lower() in ['population', 'money', 'cash', 'gold', 'score', 'level']:
                metrics_found[key] = value
            elif isinstance(value, list) and len(value) < 100:  # Reasonable list size
                metrics_found[f"{key}_count"] = len(value)
        
        if metrics_found:
            metrics_df = pd.DataFrame(list(metrics_found.items()), columns=['Metric', 'Value'])
            st.dataframe(metrics_df, use_container_width=True)
        else:
            st.info("Analyzing save file structure to identify key metrics...")
            
            # Show sample of data structure
            sample_keys = list(save_data.keys())[:10]
            for key in sample_keys:
                value = save_data[key]
                st.write(f"**{key}**: {type(value).__name__}")
                if isinstance(value, dict) and len(value) < 10:
                    st.json(value)
                elif isinstance(value, list) and len(value) < 20:
                    st.write(f"List with {len(value)} items")
                    if value and not isinstance(value[0], dict):
                        st.write(value[:5])
    
    with col2:
        st.subheader("Data Summary")
        
        # CSV data summary
        if not csv_data['buildings'].empty:
            st.metric("Total Buildings", len(csv_data['buildings']))
            
            # Building distribution by plan
            if 'plan' in csv_data['buildings'].columns:
                plan_counts = csv_data['buildings']['plan'].value_counts()
                fig = px.pie(values=plan_counts.values, names=plan_counts.index, 
                           title="Buildings by Region")
                st.plotly_chart(fig, use_container_width=True)
        
        if not csv_data['inputs'].empty and not csv_data['outputs'].empty:
            unique_resources = set(csv_data['inputs']['input'].unique()) | set(csv_data['outputs']['output'].unique())
            st.metric("Total Resources", len(unique_resources))

def resource_flow_analysis(csv_data):
    """Analyze resource production and consumption flows"""
    st.header("🔄 Resource Flow Analysis")
    
    if csv_data['inputs'].empty or csv_data['outputs'].empty:
        st.error("Missing input/output data for flow analysis")
        return
    
    # Calculate flow analysis
    flow_df = analyze_resource_flows(csv_data['inputs'], csv_data['outputs'])
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Resource Supply vs Demand")
        
        # Filter options
        flow_filter = st.selectbox(
            "Show resources:",
            ["All", "Surplus (Overproduced)", "Deficit (Underproduced)", "Balanced"]
        )
        
        if flow_filter == "Surplus":
            filtered_df = flow_df[flow_df['net_production'] > 0]
        elif flow_filter == "Deficit":
            filtered_df = flow_df[flow_df['net_production'] < 0]
        elif flow_filter == "Balanced":
            filtered_df = flow_df[abs(flow_df['net_production']) < 0.1]
        else:
            filtered_df = flow_df
        
        # Supply/Demand chart
        fig = px.scatter(
            filtered_df.reset_index(),
            x='total_per_minute',
            y='total_consumption', 
            size='producer_buildings',
            color='net_production',
            hover_name='index',
            title="Resource Production vs Consumption",
            labels={
                'total_per_minute': 'Production Rate (per minute)',
                'total_consumption': 'Consumption Rate',
                'net_production': 'Net Production'
            },
            color_continuous_scale='RdYlGn'
        )
        
        # Add diagonal line for balance
        max_val = max(filtered_df['total_per_minute'].max(), filtered_df['total_consumption'].max())
        fig.add_shape(
            type="line",
            x0=0, y0=0, x1=max_val, y1=max_val,
            line=dict(dash="dash", color="gray")
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Top Resource Insights")
        
        # Most overproduced
        surplus = flow_df[flow_df['net_production'] > 0].head(5)
        if not surplus.empty:
            st.write("**Most Overproduced:**")
            for resource, data in surplus.iterrows():
                st.write(f"• {resource}: +{data['net_production']:.1f}/min")
        
        # Most underproduced  
        deficit = flow_df[flow_df['net_production'] < 0].tail(5)
        if not deficit.empty:
            st.write("**Most Underproduced:**")
            for resource, data in deficit.iterrows():
                st.write(f"• {resource}: {data['net_production']:.1f}/min")
    
    # Detailed table
    st.subheader("Detailed Resource Flow Table")
    st.dataframe(
        flow_df.round(2),
        use_container_width=True,
        column_config={
            "supply_demand_ratio": st.column_config.NumberColumn(
                "Supply/Demand Ratio",
                help="Values > 1 indicate surplus, < 1 indicate deficit",
                format="%.2f"
            )
        }
    )

def production_chain_analysis(csv_data):
    """Analyze production chain dependencies"""
    st.header("⛓️ Production Chain Analysis")
    
    if csv_data['inputs'].empty or csv_data['outputs'].empty:
        st.error("Missing data for chain analysis")
        return
    
    # Create supply chain network
    with st.spinner("Building supply chain network..."):
        G = create_supply_chain_network(csv_data['inputs'], csv_data['outputs'])
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.subheader("Supply Chain Complexity")
        
        # Network statistics
        st.write(f"**Network Overview:**")
        st.write(f"• Total nodes: {G.number_of_nodes()}")
        st.write(f"• Total connections: {G.number_of_edges()}")
        
        building_nodes = [n for n, d in G.nodes(data=True) if d.get('type') == 'building']
        resource_nodes = [n for n, d in G.nodes(data=True) if d.get('type') == 'resource']
        
        st.write(f"• Buildings: {len(building_nodes)}")
        st.write(f"• Resources: {len(resource_nodes)}")
        
        # Most connected resources
        resource_connections = {}
        for resource in resource_nodes:
            in_degree = G.in_degree(resource)  # How many buildings produce this
            out_degree = G.out_degree(resource)  # How many buildings consume this
            resource_connections[resource] = {'producers': in_degree, 'consumers': out_degree, 'total': in_degree + out_degree}
        
        connections_df = pd.DataFrame.from_dict(resource_connections, orient='index')
        connections_df = connections_df.sort_values('total', ascending=False)
        
        st.subheader("Most Connected Resources")
        
        # Bar chart of top connected resources
        top_connected = connections_df.head(15)
        fig = go.Figure()
        fig.add_trace(go.Bar(name='Producers', x=top_connected.index, y=top_connected['producers']))
        fig.add_trace(go.Bar(name='Consumers', x=top_connected.index, y=top_connected['consumers']))
        fig.update_layout(
            title="Resource Network Connectivity",
            xaxis_title="Resource",
            yaxis_title="Number of Connections",
            barmode='stack'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Chain Insights")
        
        # Critical resources (high connectivity)
        critical_resources = connections_df[connections_df['total'] >= 5].head(10)
        if not critical_resources.empty:
            st.write("**Critical Resources:**")
            for resource, data in critical_resources.iterrows():
                st.write(f"• {resource}: {data['total']} connections")
        
        # Bottleneck detection (resources with many consumers but few producers)
        bottlenecks = connections_df[
            (connections_df['consumers'] >= 3) & 
            (connections_df['producers'] <= 1)
        ].head(5)
        
        if not bottlenecks.empty:
            st.write("**Potential Bottlenecks:**")
            for resource, data in bottlenecks.iterrows():
                st.write(f"• {resource}: {data['consumers']}C/{data['producers']}P")

def building_efficiency_analysis(csv_data):
    """Analyze building efficiency and optimization opportunities"""
    st.header("⚡ Building Efficiency Analysis")
    
    if csv_data['buildings'].empty or csv_data['outputs'].empty:
        st.error("Missing building data for efficiency analysis")
        return
    
    # Merge building data with outputs
    efficiency_df = csv_data['buildings'].merge(
        csv_data['outputs'], 
        left_on='buildings', 
        right_on='building',
        how='left'
    )
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Production Efficiency by Tier")
        
        if 'tier' in efficiency_df.columns and 'outputs_per_minute' in efficiency_df.columns:
            # Group by tier and calculate average efficiency
            tier_efficiency = efficiency_df.groupby('tier').agg({
                'outputs_per_minute': ['mean', 'max', 'count'],
                'buildings': 'nunique'
            }).round(2)
            
            tier_efficiency.columns = ['avg_output_rate', 'max_output_rate', 'total_outputs', 'unique_buildings']
            tier_efficiency = tier_efficiency.reset_index()
            
            # Efficiency by tier chart
            fig = make_subplots(specs=[[{"secondary_y": True}]])
            
            fig.add_trace(
                go.Bar(x=tier_efficiency['tier'], y=tier_efficiency['avg_output_rate'], 
                      name="Avg Output Rate", opacity=0.7),
                secondary_y=False,
            )
            
            fig.add_trace(
                go.Scatter(x=tier_efficiency['tier'], y=tier_efficiency['unique_buildings'],
                          mode='lines+markers', name="Building Count", line=dict(color='red')),
                secondary_y=True,
            )
            
            fig.update_xaxes(title_text="Tier")
            fig.update_yaxes(title_text="Average Output Rate (per minute)", secondary_y=False)
            fig.update_yaxes(title_text="Number of Buildings", secondary_y=True)
            fig.update_layout(title_text="Production Efficiency vs Building Count by Tier")
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Show tier efficiency table
            st.dataframe(tier_efficiency, use_container_width=True)
    
    with col2:
        st.subheader("Efficiency Insights")
        
        # Top performers
        if 'outputs_per_minute' in efficiency_df.columns:
            top_producers = efficiency_df.nlargest(10, 'outputs_per_minute')[['buildings', 'outputs_per_minute', 'tier']]
            
            st.write("**Top Producers:**")
            for _, building in top_producers.iterrows():
                st.write(f"• {building['buildings'][:30]}...")
                st.write(f"  {building['outputs_per_minute']:.1f}/min (T{building['tier']})")
        
        # Category analysis
        if 'category' in efficiency_df.columns:
            category_efficiency = efficiency_df.groupby('category')['outputs_per_minute'].mean().sort_values(ascending=False).head(8)
            
            st.write("**Most Efficient Categories:**")
            for category, avg_rate in category_efficiency.items():
                st.write(f"• {category}: {avg_rate:.1f}/min avg")

if __name__ == "__main__":
    main()