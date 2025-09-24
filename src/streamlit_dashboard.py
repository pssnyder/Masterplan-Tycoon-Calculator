#!/usr/bin/env python3
"""
Simple Streamlit Dashboard for Masterplan Tycoon Resource Chain Analysis
"""

import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
import os

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def load_database():
    """Load the clean database"""
    return sqlite3.connect('masterplan_tycoon_clean.db')

def get_resource_chain_data(resource_name, map_name):
    """Get complete resource chain data for visualization"""
    conn = load_database()
    
    # Get resource ID
    resource_query = """
    SELECT r.id, r.name, m.name as map_name
    FROM resources r
    JOIN maps m ON r.map_id = m.id
    WHERE r.name = ? AND m.name = ?
    """
    resource_df = pd.read_sql_query(resource_query, conn, params=(resource_name, map_name))
    
    if resource_df.empty:
        return None
    
    resource_id = resource_df.iloc[0]['id']
    
    # Get producers
    producers_query = """
    SELECT 
        b.name as building_name,
        m.name as map_name,
        bo.quantity as output_qty,
        bo.production_time_seconds,
        bo.output_per_minute
    FROM building_outputs bo
    JOIN buildings b ON bo.building_id = b.id
    JOIN maps m ON b.map_id = m.id
    WHERE bo.resource_id = ?
    """
    producers = pd.read_sql_query(producers_query, conn, params=(int(resource_id),))
    
    # Get consumers
    consumers_query = """
    SELECT 
        b.name as building_name,
        m.name as map_name,
        bi.quantity as input_qty
    FROM building_inputs bi
    JOIN buildings b ON bi.building_id = b.id
    JOIN maps m ON b.map_id = m.id
    WHERE bi.resource_id = ?
    """
    consumers = pd.read_sql_query(consumers_query, conn, params=(int(resource_id),))
    
    conn.close()
    return {
        'resource': resource_df.iloc[0],
        'producers': producers,
        'consumers': consumers
    }

def get_building_data(building_name, map_name):
    """Get complete building analysis data"""
    conn = load_database()
    
    # Get building
    building_query = """
    SELECT b.id, b.name, m.name as map_name, b.building_id
    FROM buildings b
    JOIN maps m ON b.map_id = m.id
    WHERE b.name = ? AND m.name = ?
    """
    building_df = pd.read_sql_query(building_query, conn, params=(building_name, map_name))
    
    if building_df.empty:
        return None
    
    building_id = building_df.iloc[0]['id']
    
    # Get all relationship data
    tables = {
        'inputs': 'building_inputs',
        'outputs': 'building_outputs', 
        'construction': 'building_construction',
        'maintenance': 'building_maintenance'
    }
    
    data = {'building': building_df.iloc[0]}
    
    for key, table in tables.items():
        if key == 'outputs':
            query = f"""
            SELECT r.name as resource_name, bo.quantity, bo.production_time_seconds, 
                   bo.output_per_minute, m.name as resource_map
            FROM {table} bo
            JOIN resources r ON bo.resource_id = r.id
            JOIN maps m ON r.map_id = m.id
            WHERE bo.building_id = ?
            """
        else:
            query = f"""
            SELECT r.name as resource_name, t.quantity, m.name as resource_map
            FROM {table} t
            JOIN resources r ON t.resource_id = r.id
            JOIN maps m ON r.map_id = m.id
            WHERE t.building_id = ?
            """
        
        data[key] = pd.read_sql_query(query, conn, params=(int(building_id),))
    
    conn.close()
    return data

def main():
    st.set_page_config(
        page_title="Masterplan Tycoon Resource Chain Explorer",
        page_icon="🏭",
        layout="wide"
    )
    
    st.title("🔗 Masterplan Tycoon Resource Chain Explorer")
    st.markdown("*Explore resource chains and building relationships from the cleaned database*")
    
    # Sidebar for navigation
    st.sidebar.title("🎯 Navigation")
    analysis_type = st.sidebar.selectbox(
        "Choose Analysis Type:",
        ["📊 Database Overview", "🔍 Resource Chain Analysis", "🏗️ Building Analysis", "💾 Save File Explorer"]
    )
    
    if analysis_type == "📊 Database Overview":
        st.header("Database Overview")
        
        conn = load_database()
        
        # Get map overview
        overview_query = """
        SELECT 
            m.name as map_name,
            COUNT(DISTINCT b.id) as buildings,
            COUNT(DISTINCT r.id) as resources,
            COUNT(DISTINCT bo.building_id) as producers
        FROM maps m
        LEFT JOIN buildings b ON m.id = b.map_id
        LEFT JOIN resources r ON m.id = r.map_id
        LEFT JOIN building_outputs bo ON b.id = bo.building_id
        GROUP BY m.id, m.name
        ORDER BY m.name
        """
        overview_df = pd.read_sql_query(overview_query, conn)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📍 Map Statistics")
            st.dataframe(overview_df, use_container_width=True)
        
        with col2:
            # Create bar chart
            fig = px.bar(overview_df, x='map_name', y=['buildings', 'resources', 'producers'], 
                        title="Resources & Buildings by Map",
                        barmode='group')
            st.plotly_chart(fig, use_container_width=True)
        
        # Get production summary
        st.subheader("🏭 Production Summary")
        production_query = """
        SELECT 
            m.name as map_name,
            COUNT(*) as total_outputs,
            SUM(bo.output_per_minute) as total_output_per_minute,
            AVG(bo.output_per_minute) as avg_output_per_minute
        FROM building_outputs bo
        JOIN buildings b ON bo.building_id = b.id
        JOIN maps m ON b.map_id = m.id
        GROUP BY m.id, m.name
        ORDER BY total_output_per_minute DESC
        """
        production_df = pd.read_sql_query(production_query, conn)
        st.dataframe(production_df, use_container_width=True)
        
        conn.close()
    
    elif analysis_type == "🔍 Resource Chain Analysis":
        st.header("Resource Chain Analysis")
        
        conn = load_database()
        
        # Get available resources for dropdown
        resources_query = """
        SELECT DISTINCT r.name as resource_name, m.name as map_name
        FROM resources r
        JOIN maps m ON r.map_id = m.id
        ORDER BY m.name, r.name
        """
        resources_df = pd.read_sql_query(resources_query, conn)
        conn.close()
        
        col1, col2 = st.columns(2)
        
        with col1:
            selected_map = st.selectbox("Select Map:", resources_df['map_name'].unique())
        
        with col2:
            map_resources = resources_df[resources_df['map_name'] == selected_map]['resource_name'].tolist()
            selected_resource = st.selectbox("Select Resource:", map_resources)
        
        if st.button("🔍 Analyze Resource Chain"):
            chain_data = get_resource_chain_data(selected_resource, selected_map)
            
            if chain_data:
                st.success(f"Resource Chain for **{selected_resource}** in **{selected_map}**")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("🏭 Producers")
                    if not chain_data['producers'].empty:
                        st.dataframe(chain_data['producers'], use_container_width=True)
                        
                        # Production chart
                        fig = px.bar(chain_data['producers'], 
                                   x='building_name', y='output_per_minute',
                                   title=f"{selected_resource} Production Rates",
                                   color='map_name')
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("No producers found")
                
                with col2:
                    st.subheader("🔧 Consumers") 
                    if not chain_data['consumers'].empty:
                        st.dataframe(chain_data['consumers'], use_container_width=True)
                        
                        # Consumption chart
                        fig = px.bar(chain_data['consumers'],
                                   x='building_name', y='input_qty',
                                   title=f"{selected_resource} Consumption",
                                   color='map_name')
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("No consumers found")
            else:
                st.error("Resource not found!")
    
    elif analysis_type == "🏗️ Building Analysis":
        st.header("Building Analysis")
        
        conn = load_database()
        
        # Get available buildings
        buildings_query = """
        SELECT DISTINCT b.name as building_name, m.name as map_name
        FROM buildings b
        JOIN maps m ON b.map_id = m.id
        ORDER BY m.name, b.name
        """
        buildings_df = pd.read_sql_query(buildings_query, conn)
        conn.close()
        
        col1, col2 = st.columns(2)
        
        with col1:
            selected_map = st.selectbox("Select Map:", buildings_df['map_name'].unique())
        
        with col2:
            map_buildings = buildings_df[buildings_df['map_name'] == selected_map]['building_name'].tolist()
            selected_building = st.selectbox("Select Building:", map_buildings)
        
        if st.button("🏗️ Analyze Building"):
            building_data = get_building_data(selected_building, selected_map)
            
            if building_data:
                st.success(f"Building Analysis: **{selected_building}** in **{selected_map}**")
                
                # Create tabs for different aspects
                tab1, tab2, tab3, tab4 = st.tabs(["📥 Inputs", "📤 Outputs", "🔨 Construction", "🔧 Maintenance"])
                
                with tab1:
                    if not building_data['inputs'].empty:
                        st.dataframe(building_data['inputs'], use_container_width=True)
                    else:
                        st.info("No input requirements")
                
                with tab2:
                    if not building_data['outputs'].empty:
                        st.dataframe(building_data['outputs'], use_container_width=True)
                        
                        # Output rate chart
                        if 'output_per_minute' in building_data['outputs'].columns:
                            fig = px.bar(building_data['outputs'],
                                       x='resource_name', y='output_per_minute',
                                       title="Production Rates per Minute")
                            st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("No outputs produced")
                
                with tab3:
                    if not building_data['construction'].empty:
                        st.dataframe(building_data['construction'], use_container_width=True)
                    else:
                        st.info("No construction data")
                
                with tab4:
                    if not building_data['maintenance'].empty:
                        st.dataframe(building_data['maintenance'], use_container_width=True)
                    else:
                        st.info("No maintenance requirements")
            else:
                st.error("Building not found!")
    
    elif analysis_type == "💾 Save File Explorer":
        st.header("Save File Explorer")
        st.markdown("*Coming soon: Load and analyze the actual game save file*")
        
        st.info("🚧 **Phase 2 Development**")
        st.markdown("""
        This section will:
        - Load and parse the game_data_save0.json file
        - Map save file ConfigIDs to our database building types  
        - Visualize the current game layout on a map
        - **Challenge**: Generate optimized building placements
        - Export optimized save file for testing
        """)
        
        # Show save file stats as preview
        st.subheader("📊 Save File Preview")
        st.code("""
        Save File Stats:
        • Total Nodes: 1,888
        • Links Created: 3,394  
        • Resources Extracted: 3,419,840
        • Session Time: 173,673 seconds (~48 hours)
        
        Building Types Found:
        • construction.lumbercamp
        • construction.sawmill
        • construction.quarry
        • construction.fishery
        • construction.well
        • ... and many more
        """)

if __name__ == "__main__":
    main()