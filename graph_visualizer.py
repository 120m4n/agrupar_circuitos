#!/usr/bin/env python3
"""
Graph Visualizer - Interactive HTML Network Visualization
==========================================================

This independent module generates interactive HTML visualizations of electrical
network graphs from CSV data (nodes and segments).

Features:
- Reads CSV data (nodos_circuito.csv, segmentos_circuito.csv)
- Creates NetworkX graph
- Generates interactive HTML visualization using Cytoscape.js
- Saves output to independent graph_output/ directory
- Does not interfere with existing agrupar_circuitos.py functionality

Author: Roman Sarmiento
Date: 2025-12-16
Version: 2.0
"""

import pandas as pd
import networkx as nx
import os
import sys
import argparse
import json
from typing import Tuple, Dict, Optional
from datetime import datetime

# Constants for visualization
EDGE_WIDTH_SCALE_FACTOR = 1000  # Scale factor for calculating edge width based on length
MIN_EDGE_WIDTH = 1
MAX_EDGE_WIDTH = 5


def create_example_data() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Create example data for nodes and segments.
    This uses the same example data as defined in agrupar_circuitos.py
    
    Returns:
        tuple: (df_nodos, df_segmentos) with example data
    """
    # Example segments data (from agrupar_circuitos.py)
    df_segmentos = pd.DataFrame({
        'id_segmento': range(11),
        'id_circuito': ['MT-001'] * 11,
        'nodo_inicio': [1001, 1002, 1003, 1004, 1005, 1002, 2001, 2002, 2003, 1004, 3001],
        'nodo_fin': [1002, 1003, 1004, 1005, 1006, 2001, 2002, 2003, 2004, 3001, 3002],
        'longitud_m': [523.5, 478.2, 612.8, 389.4, 734.1, 845.3, 567.9, 423.6, 321.8, 932.7, 587.4],
        'tipo_conductor': ['AAC_150']*5 + ['AAC_95']*4 + ['AAC_150']*2,
        'capacidad_amp': [250, 250, 250, 250, 250, 180, 180, 180, 180, 250, 250]
    })
    
    # Example nodes data (from agrupar_circuitos.py)
    df_nodos = pd.DataFrame({
        'id_nodo': [1001, 1002, 1003, 1004, 1005, 1006, 2001, 2002, 2003, 2004, 3001, 3002],
        'nombre': ['Subestacion_Principal', 'Apoyo_MT_001', 'Apoyo_MT_002', 
                  'Derivacion_001', 'Apoyo_MT_003', 'Transformador_001',
                  'Apoyo_Rama_A_001', 'Apoyo_Rama_A_002', 'Apoyo_Rama_A_003',
                  'Transformador_002', 'Apoyo_Rama_B_001', 'Transformador_003'],
        'tipo': ['Subestacion', 'Apoyo', 'Apoyo', 'Derivacion', 'Apoyo', 'Transformador',
                'Apoyo', 'Apoyo', 'Apoyo', 'Transformador', 'Apoyo', 'Transformador'],
        'voltaje_kv': [34.5, 34.5, 34.5, 34.5, 34.5, 13.8, 34.5, 34.5, 34.5, 13.8, 34.5, 13.8],
        'x': [-70.65, -70.651, -70.652, -70.653, -70.654, -70.655,
              -70.6515, -70.652, -70.6525, -70.653, -70.6535, -70.654],
        'y': [-33.45, -33.451, -33.452, -33.453, -33.454, -33.455,
              -33.4515, -33.452, -33.4525, -33.453, -33.4535, -33.454]
    })
    
    return df_nodos, df_segmentos


def load_csv_data(input_dir: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load node and segment data from CSV files.
    If files don't exist, create example data.
    
    Args:
        input_dir: Directory containing CSV files
        
    Returns:
        tuple: (df_nodos, df_segmentos)
    """
    print(f"\n📥 Loading data from CSV files...")
    
    nodes_path = os.path.join(input_dir, 'nodos_circuito.csv')
    segments_path = os.path.join(input_dir, 'segmentos_circuito.csv')
    
    # Check if both files exist
    files_exist = os.path.exists(nodes_path) and os.path.exists(segments_path)
    
    if not files_exist:
        missing_files = []
        if not os.path.exists(nodes_path):
            missing_files.append(nodes_path)
        if not os.path.exists(segments_path):
            missing_files.append(segments_path)
        
        print(f"⚠️  File(s) not found: {', '.join(missing_files)}")
        print("   Creating example data...")
        return create_example_data()
    
    # Load CSV files
    try:
        df_nodos = pd.read_csv(nodes_path)
        print(f"✅ Loaded {len(df_nodos)} nodes from {nodes_path}")
        
        df_segmentos = pd.read_csv(segments_path)
        print(f"✅ Loaded {len(df_segmentos)} segments from {segments_path}")
        
        return df_nodos, df_segmentos
    except Exception as e:
        print(f"⚠️  Error loading CSV files: {e}")
        print("   Creating example data...")
        return create_example_data()


def create_networkx_graph(df_nodos: pd.DataFrame, df_segmentos: pd.DataFrame) -> nx.Graph:
    """
    Create a NetworkX graph from nodes and segments data.
    
    Args:
        df_nodos: DataFrame with node information
        df_segmentos: DataFrame with segment information
        
    Returns:
        NetworkX Graph object
    """
    print("\n🔗 Creating NetworkX graph...")
    
    G = nx.Graph()
    
    # Add nodes with attributes
    for _, nodo in df_nodos.iterrows():
        G.add_node(
            nodo['id_nodo'],
            nombre=nodo['nombre'],
            tipo=nodo['tipo'],
            voltaje_kv=nodo['voltaje_kv'],
            x=nodo['x'],
            y=nodo['y']
        )
    
    # Add edges (segments) with attributes
    for _, segmento in df_segmentos.iterrows():
        G.add_edge(
            segmento['nodo_inicio'],
            segmento['nodo_fin'],
            id_segmento=segmento['id_segmento'],
            longitud_m=segmento['longitud_m'],
            tipo_conductor=segmento['tipo_conductor'],
            capacidad_amp=segmento['capacidad_amp'],
            id_circuito=segmento['id_circuito']
        )
    
    print(f"✅ Graph created: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    
    return G


def get_node_color(node_type: str) -> str:
    """
    Get color for node based on its type.
    
    Args:
        node_type: Type of the node (Subestacion, Apoyo, Derivacion, Transformador)
        
    Returns:
        Color code in hex format
    """
    color_map = {
        'Subestacion': '#FF0000',      # Red
        'Apoyo': '#4169E1',             # Royal Blue
        'AEREO': '#4169E1',             # Royal Blue
        'POSTE EN H': "#748DDA",      # Royal Blue
        'CAJA DE INSPECCION': "#604603", # Royal Blue
        'INTERRUPTORDIS': "#53128F",     # Royal Blue
        'Derivacion': '#FFD700',        # Gold
        'Transformador': '#32CD32',     # Lime Green
    }
    return color_map.get(node_type, '#808080')  # Default: Gray


def get_node_size(node_type: str) -> int:
    """
    Get size for node based on its type.
    
    Args:
        node_type: Type of the node
        
    Returns:
        Size value for the node
    """
    size_map = {
        'Subestacion': 35,
        'Derivacion': 25,
        'Transformador': 25,
        'Apoyo': 15,
    }
    return size_map.get(node_type, 15)


def export_minimal_graph_data(G: nx.Graph, output_dir: str) -> dict:
    """
    Export minimal node and edge data needed for diagramming.

    Nodes: id_nodo, es_subestacion (bool), nombre (only for substation)
    Edges: id_segmento, nodo_inicio, nodo_fin
    """
    nodes_out = []
    for node_id in G.nodes():
        node = G.nodes[node_id]
        is_sub = node.get('tipo') == 'Subestacion'
        name = node.get('nombre') if is_sub else ''
        nodes_out.append({'id_nodo': node_id, 'es_subestacion': is_sub, 'nombre': name})

    edges_out = []
    for u, v, data in G.edges(data=True):
        edges_out.append({'id_segmento': data.get('id_segmento'), 'nodo_inicio': u, 'nodo_fin': v})

    # Ensure output dir exists
    os.makedirs(output_dir, exist_ok=True)

    nodes_path = os.path.join(output_dir, 'graph_nodes_minimal.csv')
    edges_path = os.path.join(output_dir, 'graph_edges_minimal.csv')

    try:
        pd.DataFrame(nodes_out).to_csv(nodes_path, index=False)
        pd.DataFrame(edges_out).to_csv(edges_path, index=False)
        print(f"✅ Minimal node data saved to: {nodes_path}")
        print(f"✅ Minimal edge data saved to: {edges_path}")
    except Exception as e:
        print(f"⚠️ Error exporting minimal data: {e}")
        return {'nodes': None, 'edges': None, 'error': str(e)}

    return {'nodes': nodes_path, 'edges': edges_path, 'error': None}


def export_cytoscape_json(G: nx.Graph, output_dir: str) -> str:
        """
        Export graph to a Cytoscape.js-compatible JSON file.

        Nodes include: id, nombre, tipo, voltaje_kv, x, y, color
        Edges include: id, source, target, longitud_m, width, color
        """
        os.makedirs(output_dir, exist_ok=True)

        elements = []
        # Nodes
        for node_id, data in G.nodes(data=True):
                node_data = {
                        'id': str(node_id),
                        'nombre': data.get('nombre', ''),
                        'tipo': data.get('tipo', ''),
                        'voltaje_kv': data.get('voltaje_kv'),
                        'x': data.get('x'),
                        'y': data.get('y'),
                        'color': get_node_color(data.get('tipo'))
                }
                elements.append({'data': node_data})

        # Edges
        for u, v, ed in G.edges(data=True):
                seg_id = ed.get('id_segmento', f"{u}_{v}")
                longitud = ed.get('longitud_m', 0) or 0
                width = max(MIN_EDGE_WIDTH, min(MAX_EDGE_WIDTH, longitud / EDGE_WIDTH_SCALE_FACTOR))
                edge_data = {
                        'id': str(seg_id),
                        'source': str(u),
                        'target': str(v),
                        'longitud_m': longitud,
                        'width': width,
                        'color': '#888888'
                }
                elements.append({'data': edge_data})

        out = {'elements': elements}
        out_path = os.path.join(output_dir, 'graph_cytoscape.json')
        try:
                with open(out_path, 'w', encoding='utf-8') as f:
                        json.dump(out, f, ensure_ascii=False, indent=2)
                print(f"✅ Cytoscape JSON saved to: {out_path}")
        except Exception as e:
                print(f"⚠️ Error saving Cytoscape JSON: {e}")
                out_path = ''

        return out_path


def create_cytoscape_html(output_dir: str, json_filename: str, stats: Dict, title: str = "Red Eléctrica - Cytoscape") -> str:
        """
        Create a standalone HTML file that loads the cytoscape JSON via fetch
        and renders the graph using Cytoscape.js. Also displays the graph statistics
        in a side panel to preserve presentation.
        
        UI/UX Improvements:
        -------------------
        - Modern, clean design with improved color scheme
        - Toggle button to show/hide all node labels conditionally
        - Interactive zoom controls (Zoom In, Zoom Out, Reset, Fit)
        - Better visual hierarchy and spacing
        - Responsive layout with enhanced styling
        - Improved node and edge styling
        - Smooth animations and transitions
        
        Layout Algorithm: cose-bilkent
        -------------------------------
        Uses the cose-bilkent layout algorithm which is specifically designed for:
        - Hierarchical network structures (like electrical distribution systems)
        - Force-directed positioning with high quality results
        - Automatic minimization of edge crossings
        - Clear visualization of tree-like structures with branches
        - Superior to circle layout for showing network flow and topology
        
        This layout is ideal for electrical networks as it naturally shows the 
        hierarchical flow from the substation through the distribution network,
        making it easy to understand the network topology and identify branches.
        """
        os.makedirs(output_dir, exist_ok=True)
        html_path = os.path.join(output_dir, 'red_electrica_cytoscape.html')

        # Build an HTML snippet for stats (simple layout preserving values)
        stats_html_lines = []
        stats_html_lines.append(f"<h2>📊 Estadísticas del Grafo</h2>")
        stats_html_lines.append('<div class="stat-block">')
        stats_html_lines.append('<div class="stat-section">')
        stats_html_lines.append('<h3>🔢 Propiedades</h3>')
        stats_html_lines.append(f"<p><span class='stat-label'>Nodos:</span> <span class='stat-value'>{stats.get('num_nodes', 0)}</span></p>")
        stats_html_lines.append(f"<p><span class='stat-label'>Aristas:</span> <span class='stat-value'>{stats.get('num_edges', 0)}</span></p>")
        stats_html_lines.append(f"<p><span class='stat-label'>Conectado:</span> <span class='stat-value'>{'Sí' if stats.get('is_connected') else 'No'}</span></p>")
        stats_html_lines.append(f"<p><span class='stat-label'>Componentes:</span> <span class='stat-value'>{stats.get('num_components')}</span></p>")
        stats_html_lines.append(f"<p><span class='stat-label'>Densidad:</span> <span class='stat-value'>{stats.get('density', 0):.4f}</span></p>")
        if stats.get('diameter') is not None:
                stats_html_lines.append(f"<p><span class='stat-label'>Diámetro:</span> <span class='stat-value'>{stats.get('diameter')}</span></p>")
        stats_html_lines.append('</div>')
        stats_html_lines.append('<div class="stat-section">')
        stats_html_lines.append('<h3>🏗️ Tipos de Nodos</h3>')
        for t, c in stats.get('node_types', {}).items():
                stats_html_lines.append(f"<p><span class='stat-label'>{t}:</span> <span class='stat-value'>{c}</span></p>")
        stats_html_lines.append('</div>')
        stats_html_lines.append('<div class="stat-section">')
        stats_html_lines.append('<h3>📏 Longitudes</h3>')
        stats_html_lines.append(f"<p><span class='stat-label'>Total:</span> <span class='stat-value'>{stats.get('total_length_km', 0):.2f} km</span></p>")
        stats_html_lines.append(f"<p><span class='stat-label'>Promedio:</span> <span class='stat-value'>{stats.get('avg_edge_length_m', 0):.1f} m</span></p>")
        stats_html_lines.append(f"<p><span class='stat-label'>Mínimo:</span> <span class='stat-value'>{stats.get('min_edge_length_m', 0):.1f} m</span></p>")
        stats_html_lines.append(f"<p><span class='stat-label'>Máximo:</span> <span class='stat-value'>{stats.get('max_edge_length_m', 0):.1f} m</span></p>")
        stats_html_lines.append('</div>')
        stats_html_lines.append('</div>')
        stats_html = '\n'.join(stats_html_lines)

        # Build dynamic legend based on actual node types in the data
        legend_html_lines = []
        legend_html_lines.append('<div class="legend">')
        legend_html_lines.append('<h2>🎨 Leyenda</h2>')
        
        # Get node types from stats and generate legend items dynamically
        node_types = stats.get('node_types', {})
        for node_type in sorted(node_types):
            color = get_node_color(node_type)
            legend_html_lines.append('<div class="legend-item">')
            legend_html_lines.append(f'<div class="legend-color" style="background: {color};"></div>')
            legend_html_lines.append(f'<span>{node_type}</span>')
            legend_html_lines.append('</div>')
        
        legend_html_lines.append('</div>')
        legend_html = '\n'.join(legend_html_lines)

        # Enhanced Cytoscape HTML template with improved UI/UX
        json_basename = os.path.basename(json_filename)
        # Use a placeholder template (not an f-string) to avoid brace-escaping issues
        html_template = """
    <!doctype html>
    <html lang="es">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title><<<TITLE>>></title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            
            body { 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
                background: #f5f7fa;
                color: #2c3e50;
            }
            
            #container { 
                display: flex; 
                height: 100vh;
                overflow: hidden;
            }
            
            #sidebar { 
                width: 340px; 
                background: linear-gradient(to bottom, #ffffff 0%, #f8f9fa 100%);
                box-shadow: 2px 0 10px rgba(0,0,0,0.08);
                overflow-y: auto;
                z-index: 10;
            }
            
            #sidebar-content {
                padding: 24px;
            }
            
            h1 { 
                font-size: 22px;
                font-weight: 700;
                color: #1a202c;
                margin-bottom: 8px;
                padding-bottom: 12px;
                border-bottom: 3px solid #4299e1;
            }
            
            h2 { 
                font-size: 18px;
                font-weight: 600;
                color: #2d3748;
                margin: 24px 0 16px 0;
            }
            
            h3 {
                font-size: 14px;
                font-weight: 600;
                color: #4a5568;
                margin: 16px 0 8px 0;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
            
            .stat-block {
                background: white;
                border-radius: 8px;
                padding: 16px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            }
            
            .stat-section {
                margin-bottom: 16px;
                padding-bottom: 16px;
                border-bottom: 1px solid #e2e8f0;
            }
            
            .stat-section:last-child {
                border-bottom: none;
                padding-bottom: 0;
                margin-bottom: 0;
            }
            
            .stat-block p { 
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin: 8px 0;
                padding: 6px 0;
                font-size: 14px;
            }
            
            .stat-label {
                color: #718096;
                font-weight: 500;
            }
            
            .stat-value {
                color: #2d3748;
                font-weight: 600;
            }
            
            #controls-panel {
                background: white;
                border-radius: 8px;
                padding: 16px;
                margin-top: 20px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            }
            
            #controls-panel h2 {
                margin-top: 0;
            }
            
            .control-group {
                margin: 12px 0;
            }
            
            .control-group label {
                display: block;
                font-size: 13px;
                font-weight: 600;
                color: #4a5568;
                margin-bottom: 8px;
            }
            
            .btn {
                padding: 10px 16px;
                border: none;
                border-radius: 6px;
                font-size: 14px;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.2s ease;
                width: 100%;
                margin: 4px 0;
                display: inline-block;
                text-align: center;
            }
            
            .btn-primary {
                background: #4299e1;
                color: white;
            }
            
            .btn-primary:hover {
                background: #3182ce;
                transform: translateY(-1px);
                box-shadow: 0 4px 8px rgba(66, 153, 225, 0.3);
            }
            
            .btn-secondary {
                background: #e2e8f0;
                color: #2d3748;
            }
            
            .btn-secondary:hover {
                background: #cbd5e0;
                transform: translateY(-1px);
            }
            
            .btn-group {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 8px;
                margin-top: 8px;
            }
            
            .legend {
                background: white;
                border-radius: 8px;
                padding: 16px;
                margin-top: 20px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            }
            
            .legend h2 {
                margin-top: 0;
            }
            
            .legend-item {
                display: flex;
                align-items: center;
                margin: 10px 0;
                font-size: 13px;
            }
            
            .legend-color {
                width: 20px;
                height: 20px;
                border-radius: 50%;
                margin-right: 10px;
                border: 2px solid #e2e8f0;
            }
            
            .timestamp {
                margin-top: 20px;
                padding-top: 16px;
                border-top: 1px solid #e2e8f0;
                font-size: 12px;
                color: #a0aec0;
                text-align: center;
            }
            
            #graph-container {
                flex: 1;
                position: relative;
                background: #ffffff;
            }
            
            #cy { 
                width: 100%;
                height: 100%;
                background: linear-gradient(135deg, #f5f7fa 0%, #ffffff 100%);
            }
            
            /* Scrollbar styling for sidebar */
            #sidebar::-webkit-scrollbar {
                width: 8px;
            }
            
            #sidebar::-webkit-scrollbar-track {
                background: #f1f1f1;
            }
            
            #sidebar::-webkit-scrollbar-thumb {
                background: #cbd5e0;
                border-radius: 4px;
            }
            
            #sidebar::-webkit-scrollbar-thumb:hover {
                background: #a0aec0;
            }
            
            /* Responsive design */
            @media (max-width: 768px) {
                #container {
                    flex-direction: column;
                }
                
                #sidebar {
                    width: 100%;
                    max-height: 40vh;
                }
                
                #graph-container {
                    height: 60vh;
                }
            }
        </style>
        <script src="https://unpkg.com/cytoscape@3.24.0/dist/cytoscape.min.js"></script>
        <script src="https://unpkg.com/cytoscape-cose-bilkent@4.0.0/cytoscape-cose-bilkent.js"></script>
    </head>
    <body>
        <div id="container">
            <div id="sidebar">
                <div id="sidebar-content">
                    <h1>⚡ <<<TITLE>>></h1>
                    
                    <div id="controls-panel">
                        <h2>🎛️ Controles</h2>
                        <div class="control-group">
                            <button id="toggleLabels" class="btn btn-primary">
                                🏷️ Mostrar Etiquetas
                            </button>
                        </div>
                        <div class="control-group">
                            <label>🔍 Zoom</label>
                            <div class="btn-group">
                                <button id="zoomIn" class="btn btn-secondary">Acercar +</button>
                                <button id="zoomOut" class="btn btn-secondary">Alejar -</button>
                            </div>
                            <div class="btn-group">
                                <button id="resetZoom" class="btn btn-secondary">Resetear</button>
                                <button id="fitGraph" class="btn btn-secondary">Ajustar</button>
                            </div>
                        </div>
                    </div>
                    
                    <<<STATS_HTML>>>
                    
                    <<<LEGEND_HTML>>>
                    
                    <div class="timestamp">
                        🕐 Generado: <<<GEN_TIME>>>
                    </div>
                </div>
            </div>
            <div id="graph-container">
                <div id="cy"></div>
            </div>
        </div>

        <script>
            let cy;
            let labelsVisible = false;
            
            fetch('<<<JSON>>>')
                .then(r => r.json())
                .then(data => {
                    cy = cytoscape({
                        container: document.getElementById('cy'),
                        elements: data.elements,
                        style: [
                            { 
                                selector: 'node', 
                                style: { 
                                    'label': '',
                                    'background-color': 'data(color)', 
                                    'width': 'mapData(voltaje_kv, 0, 35, 20, 50)', 
                                    'height': 'mapData(voltaje_kv, 0, 35, 20, 50)', 
                                    'text-valign': 'center', 
                                    'text-halign': 'center',
                                    'color': '#2d3748', 
                                    'text-outline-width': 3, 
                                    'text-outline-color': '#ffffff',
                                    'font-size': '11px',
                                    'font-weight': 'bold',
                                    'border-width': 2,
                                    'border-color': '#ffffff',
                                    'border-opacity': 0.8,
                                    'transition-property': 'background-color, border-color',
                                    'transition-duration': '0.3s'
                                } 
                            },
                            { 
                                selector: 'node:selected', 
                                style: { 
                                    'border-width': 4,
                                    'border-color': '#4299e1',
                                    'border-opacity': 1
                                } 
                            },
                            { 
                                selector: 'node[tipo = "Subestacion"]', 
                                style: { 
                                    'label': 'data(nombre)',
                                    'font-size': '13px',
                                    'border-width': 3
                                } 
                            },
                            { 
                                selector: 'edge', 
                                style: { 
                                    'width': 'data(width)', 
                                    'line-color': '#a0aec0', 
                                    'curve-style': 'bezier',
                                    'opacity': 0.7,
                                    'transition-property': 'line-color, width, opacity',
                                    'transition-duration': '0.3s'
                                } 
                            },
                            { 
                                selector: 'edge:selected', 
                                style: { 
                                    'line-color': '#4299e1',
                                    'width': 'mapData(width, 1, 5, 3, 8)',
                                    'opacity': 1
                                } 
                            },
                            { 
                                selector: 'node.highlighted', 
                                style: { 
                                    'border-width': 4,
                                    'border-color': '#4299e1',
                                    'border-opacity': 1,
                                    'background-color': 'data(color)',
                                    'z-index': 999
                                } 
                            },
                            { 
                                selector: 'edge.highlighted', 
                                style: { 
                                    'line-color': '#4299e1',
                                    'width': 'mapData(width, 1, 5, 3, 8)',
                                    'opacity': 1,
                                    'z-index': 999
                                } 
                            }
                        ],
                        layout: { 
                            name: 'cose-bilkent'
                        }
                    });
                    
                    // Toggle labels button
                    const toggleButton = document.getElementById('toggleLabels');
                    document.getElementById('toggleLabels').addEventListener('click', function() {
                        labelsVisible = !labelsVisible;
                        
                        if (labelsVisible) {
                            cy.style()
                                .selector('node')
                                .style('label', 'data(nombre)')
                                .update();
                            toggleButton.textContent = '🏷️ Ocultar Etiquetas';
                        } else {
                            cy.style()
                                .selector('node[tipo != "Subestacion"]')
                                .style('label', '')
                                .update();
                            cy.style()
                                .selector('node[tipo = "Subestacion"]')
                                .style('label', 'data(nombre)')
                                .update();
                            toggleButton.textContent = '🏷️ Mostrar Etiquetas';
                        }
                    });
                    
                    // Zoom controls
                    document.getElementById('zoomIn').addEventListener('click', function() {
                        cy.zoom({
                            level: cy.zoom() * 1.2,
                            renderedPosition: { x: cy.width() / 2, y: cy.height() / 2 }
                        });
                    });
                    
                    document.getElementById('zoomOut').addEventListener('click', function() {
                        cy.zoom({
                            level: cy.zoom() * 0.8,
                            renderedPosition: { x: cy.width() / 2, y: cy.height() / 2 }
                        });
                    });
                    
                    document.getElementById('resetZoom').addEventListener('click', function() {
                        cy.zoom(1);
                        cy.center();
                    });
                    
                    document.getElementById('fitGraph').addEventListener('click', function() {
                        cy.fit(null, 50);
                    });
                    
                    // Add interactivity - highlight connected edges on node tap
                    cy.on('tap', 'node', function(evt) {
                        const node = evt.target;
                        cy.elements().removeClass('highlighted');
                        node.addClass('highlighted');
                        node.connectedEdges().addClass('highlighted');
                    });
                    
                    cy.on('tap', function(evt) {
                        if (evt.target === cy) {
                            cy.elements().removeClass('highlighted');
                        }
                    });
                })
                .catch(err => {
                    document.getElementById('cy').innerHTML = '<div style="padding:40px;text-align:center;color:#e53e3e;font-size:16px;">❌ Error cargando el grafo: ' + err + '</div>';
                });
        </script>
    </body>
    </html>
    """

        gen_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        html_content = html_template.replace('<<<TITLE>>>', title).replace('<<<STATS_HTML>>>', stats_html).replace('<<<LEGEND_HTML>>>', legend_html).replace('<<<JSON>>>', json_basename).replace('<<<GEN_TIME>>>', gen_time)

        # write files: ensure JSON is copied/moved in same output_dir so fetch path works
        # (json already written by export_cytoscape_json into output_dir)
        try:
                with open(html_path, 'w', encoding='utf-8') as f:
                        f.write(html_content)
                print(f"✅ Cytoscape HTML viewer saved to: {html_path}")
        except Exception as e:
                print(f"⚠️ Error writing Cytoscape HTML: {e}")
                html_path = ''

        return html_path


def generate_graph_statistics(G: nx.Graph) -> Dict:
    """
    Generate statistics about the graph.
    
    Args:
        G: NetworkX graph
        
    Returns:
        Dictionary with graph statistics
    """
    stats = {
        'num_nodes': G.number_of_nodes(),
        'num_edges': G.number_of_edges(),
        'is_connected': nx.is_connected(G),
        'num_components': nx.number_connected_components(G),
        'density': nx.density(G)
    }
    
    # Calculate diameter only if connected
    if stats['is_connected']:
        stats['diameter'] = nx.diameter(G)
    else:
        stats['diameter'] = None
    
    # Node type distribution
    node_types = {}
    for node_id in G.nodes():
        node_type = G.nodes[node_id]['tipo']
        node_types[node_type] = node_types.get(node_type, 0) + 1
    stats['node_types'] = node_types
    
    # Edge length statistics
    edge_lengths = [data['longitud_m'] for _, _, data in G.edges(data=True)]
    stats['total_length_m'] = sum(edge_lengths)
    stats['total_length_km'] = sum(edge_lengths) / 1000
    stats['avg_edge_length_m'] = sum(edge_lengths) / len(edge_lengths) if edge_lengths else 0
    stats['min_edge_length_m'] = min(edge_lengths) if edge_lengths else 0
    stats['max_edge_length_m'] = max(edge_lengths) if edge_lengths else 0
    
    return stats


def print_graph_statistics(stats: Dict):
    """
    Print graph statistics in a formatted way.
    
    Args:
        stats: Dictionary with graph statistics
    """
    print("\n" + "=" * 70)
    print("📊 GRAPH STATISTICS")
    print("=" * 70)
    
    print(f"\n🔢 Graph Properties:")
    print(f"   • Nodes: {stats['num_nodes']}")
    print(f"   • Edges: {stats['num_edges']}")
    print(f"   • Connected: {'Yes' if stats['is_connected'] else 'No'}")
    print(f"   • Components: {stats['num_components']}")
    print(f"   • Density: {stats['density']:.4f}")
    if stats['diameter'] is not None:
        print(f"   • Diameter: {stats['diameter']}")
    
    print(f"\n🏗️ Node Type Distribution:")
    for node_type, count in stats['node_types'].items():
        print(f"   • {node_type}: {count}")
    
    print(f"\n📏 Edge Length Statistics:")
    print(f"   • Total length: {stats['total_length_km']:.2f} km ({stats['total_length_m']:.1f} m)")
    print(f"   • Average length: {stats['avg_edge_length_m']:.1f} m")
    print(f"   • Min length: {stats['min_edge_length_m']:.1f} m")
    print(f"   • Max length: {stats['max_edge_length_m']:.1f} m")
    
    print("=" * 70)


def main(
    input_dir: str = './data',
    output_dir: str = './graph_output',
    use_example_data: bool = False
) -> Dict:
    """
    Main function to generate graph visualization using Cytoscape.js.
    
    Args:
        input_dir: Directory containing CSV files
        output_dir: Directory to save output files
        use_example_data: If True, use example data instead of CSV files
        
    Returns:
        Dictionary with execution results including:
        - success: Boolean indicating if visualization was created
        - output_file: Path to generated HTML file
        - cytoscape_json: Path to JSON data file
        - minimal_export: Dict with paths to minimal CSV files
        - stats: Graph statistics dictionary
        - error: Error message if success is False
    """
    result = {
        'success': False,
        'error': None,
        'output_file': None,
        'stats': {}
    }
    
    try:
        print("=" * 70)
        print("GRAPH VISUALIZER - Interactive HTML Network Visualization (Cytoscape.js)")
        print("=" * 70)
        print(f"Input directory: {input_dir}")
        print(f"Output directory: {output_dir}")
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        print(f"\n✅ Output directory created/verified: {output_dir}")
        
        # Load data
        if use_example_data:
            print("\n⚠️  Using example data (--example flag)")
            df_nodos, df_segmentos = create_example_data()
            print(f"✅ Example data created: {len(df_nodos)} nodes, {len(df_segmentos)} segments")
        else:
            df_nodos, df_segmentos = load_csv_data(input_dir)
        
        # Create NetworkX graph
        G = create_networkx_graph(df_nodos, df_segmentos)
        
        # Generate and print statistics
        stats = generate_graph_statistics(G)
        print_graph_statistics(stats)
        result['stats'] = stats
        
        # Export minimal graph data (nodes and edges) for diagramming
        minimal_export = export_minimal_graph_data(G, output_dir)
        result['minimal_export'] = minimal_export
        
        # Export Cytoscape JSON and create HTML viewer
        try:
            cyto_json = export_cytoscape_json(G, output_dir)
            result['cytoscape_json'] = cyto_json
            if cyto_json:
                cyto_html = create_cytoscape_html(output_dir, cyto_json, stats, title="Red Eléctrica")
                result['cytoscape_html'] = cyto_html
                result['output_file'] = cyto_html
            else:
                error_msg = "Failed to export Cytoscape JSON file"
                result['cytoscape_html'] = None
                result['error'] = error_msg
                print(f"⚠️ Error: {error_msg}")
                return result
        except Exception as e:
            error_msg = f"Failed to create Cytoscape visualization: {e}"
            result['error'] = error_msg
            print(f"⚠️ {error_msg}")
            return result
            
        result['success'] = True
        
        # Final summary
        print("\n" + "=" * 70)
        print("✅ VISUALIZATION COMPLETED SUCCESSFULLY")
        print("=" * 70)
        print(f"\n📁 Output file: {result['output_file']}")
        print(f"📊 Graph: {stats['num_nodes']} nodes, {stats['num_edges']} edges")
        print(f"📏 Total network length: {stats['total_length_km']:.2f} km")
        print(f"\n💡 Open the HTML file in your web browser to view the interactive visualization!")
        print("=" * 70)
        
    except Exception as e:
        result['error'] = str(e)
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
    
    return result


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Generate interactive HTML visualization of electrical network graph using Cytoscape.js',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use CSV files from data directory (default)
  python graph_visualizer.py
  
  # Specify custom input directory
  python graph_visualizer.py --input-dir /path/to/csv/files
  
  # Specify custom output directory
  python graph_visualizer.py --output-dir ./my_graphs
  
  # Use example data (ignore CSV files)
  python graph_visualizer.py --example
  
  # Full custom example
  python graph_visualizer.py --input-dir ./data --output-dir ./graphs

Notes:
  - This tool is independent and does not modify existing agrupar_circuitos.py functionality
  - CSV files expected: nodos_circuito.csv, segmentos_circuito.csv
  - Output is saved in the graph_output/ directory by default
  - Uses Cytoscape.js for interactive visualization with cose-bilkent layout
  - Output filename is always: red_electrica_cytoscape.html
        """
    )
    
    parser.add_argument(
        '--input-dir',
        type=str,
        default='./data',
        help='Directory containing CSV files (default: ./data)'
    )
    
    parser.add_argument(
        '--output-dir',
        type=str,
        default='./graph_output',
        help='Directory to save output files (default: ./graph_output)'
    )
    
    parser.add_argument(
        '--example',
        action='store_true',
        help='Use example data instead of CSV files'
    )
    
    return parser.parse_args()


if __name__ == "__main__":
    # Parse arguments
    args = parse_arguments()
    
    # Run main function
    result = main(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        use_example_data=args.example
    )
    
    # Exit with appropriate code
    sys.exit(0 if result['success'] else 1)
