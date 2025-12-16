#!/usr/bin/env python3
"""
Graph Visualizer - Interactive HTML Network Visualization
==========================================================

This independent module generates interactive HTML visualizations of electrical
network graphs from CSV data (nodes and segments).

Features:
- Reads CSV data (nodos_circuito.csv, segmentos_circuito.csv)
- Creates NetworkX graph
- Generates interactive HTML visualization using pyvis
- Saves output to independent graph_output/ directory
- Does not interfere with existing agrupar_circuitos.py functionality

Author: Roman Sarmiento
Date: 2025-12-16
Version: 1.0
"""

import pandas as pd
import networkx as nx
import os
import sys
import argparse
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


def create_html_visualization(
    G: nx.Graph,
    output_path: str,
    title: str = "Red Eléctrica - Visualización Interactiva",
    height: str = "750px",
    width: str = "100%",
    notebook: bool = False
) -> str:
    """
    Create an interactive HTML visualization using pyvis.
    
    Args:
        G: NetworkX graph
        output_path: Path to save the HTML file
        title: Title for the visualization
        height: Height of the visualization
        width: Width of the visualization
        notebook: Whether to use notebook mode
        
    Returns:
        Path to the generated HTML file
    """
    try:
        from pyvis.network import Network
    except ImportError:
        print("❌ ERROR: pyvis library is not installed.")
        print("   Install it with: pip install pyvis")
        raise
    
    print(f"\n🎨 Creating interactive HTML visualization...")
    
    # Create pyvis network
    net = Network(
        height=height,
        width=width,
        bgcolor='#FFFFFF',
        font_color='#000000',
        notebook=notebook,
        directed=False
    )
    
    # Set physics options for better layout
    net.set_options("""
    {
        "nodes": {
            "font": {
                "size": 12
            },
            "borderWidth": 2,
            "borderWidthSelected": 4
        },
        "edges": {
            "color": {
                "inherit": true
            },
            "smooth": {
                "enabled": true,
                "type": "continuous"
            }
        },
        "physics": {
            "enabled": true,
            "barnesHut": {
                "gravitationalConstant": -8000,
                "centralGravity": 0.3,
                "springLength": 150,
                "springConstant": 0.04,
                "damping": 0.09
            },
            "stabilization": {
                "enabled": true,
                "iterations": 1000,
                "updateInterval": 25
            }
        },
        "interaction": {
            "hover": true,
            "tooltipDelay": 100,
            "navigationButtons": true,
            "keyboard": true
        }
    }
    """)
    
    # Add nodes with attributes
    for node_id in G.nodes():
        node_data = G.nodes[node_id]
        
        color = get_node_color(node_data['tipo'])
        size = get_node_size(node_data['tipo'])
        
        # Create detailed hover tooltip
        tooltip = (
            f"<b>{node_data['nombre']}</b><br>"
            f"ID: {node_id}<br>"
            f"Tipo: {node_data['tipo']}<br>"
            f"Voltaje: {node_data['voltaje_kv']} kV<br>"
            f"Coordenadas: ({node_data['x']:.4f}, {node_data['y']:.4f})"
        )
        
        # Add node label based on type
        if node_data['tipo'] == 'Subestacion':
            label = f"🏭 {node_data['nombre']}"
        elif node_data['tipo'] == 'Transformador':
            label = f"⚡ {node_id}"
        elif node_data['tipo'] == 'Derivacion':
            label = f"⚪ {node_id}"
        else:
            label = f"{node_id}"
        
        net.add_node(
            node_id,
            label=label,
            title=tooltip,
            color=color,
            size=size,
            borderWidth=2,
            borderWidthSelected=4
        )
    
    # Add edges with attributes
    for edge in G.edges(data=True):
        u, v, data = edge
        
        # Create edge tooltip with segment information
        tooltip = (
            f"<b>Segmento {data['id_segmento']}</b><br>"
            f"De: {u} → A: {v}<br>"
            f"Longitud: {data['longitud_m']:.1f} m<br>"
            f"Conductor: {data['tipo_conductor']}<br>"
            f"Capacidad: {data['capacidad_amp']} A<br>"
            f"Circuito: {data['id_circuito']}"
        )
        
        # Edge width based on length (shorter = thicker)
        # Uses scale factor to normalize width between min and max
        width = max(MIN_EDGE_WIDTH, min(MAX_EDGE_WIDTH, EDGE_WIDTH_SCALE_FACTOR / data['longitud_m']))
        
        # Edge color based on conductor type
        if data['tipo_conductor'].startswith('AAC_150'):
            edge_color = '#1E90FF'  # Dodger Blue
        elif data['tipo_conductor'].startswith('AAC_95'):
            edge_color = '#FFA500'  # Orange
        else:
            edge_color = '#808080'  # Gray
        
        net.add_edge(
            u, v,
            title=tooltip,
            width=width,
            color=edge_color
        )
    
    # Add title to the visualization
    html_title = f"""
    <div style="text-align: center; padding: 20px; background-color: #f0f0f0; border-bottom: 2px solid #ccc;">
        <h1 style="margin: 0; color: #333;">{title}</h1>
        <p style="margin: 5px 0; color: #666;">
            Nodos: {G.number_of_nodes()} | Segmentos: {G.number_of_edges()} | 
            Generado: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        </p>
        <div style="margin-top: 10px; font-size: 14px;">
            <span style="color: #FF0000;">■</span> Subestación &nbsp;
            <span style="color: #FFD700;">■</span> Derivación &nbsp;
            <span style="color: #32CD32;">■</span> Transformador &nbsp;
            <span style="color: #4169E1;">■</span> Apoyo
        </div>
    </div>
    """
    
    # Save the network
    net.save_graph(output_path)
    
    # Add custom title by modifying the HTML file
    with open(output_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # Insert title after body tag
    html_content = html_content.replace('<body>', f'<body>\n{html_title}')
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ HTML visualization saved to: {output_path}")
    
    return output_path


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
    output_filename: str = 'red_electrica_graph.html',
    use_example_data: bool = False
) -> Dict:
    """
    Main function to generate graph visualization.
    
    Args:
        input_dir: Directory containing CSV files
        output_dir: Directory to save output files
        output_filename: Name of the output HTML file
        use_example_data: If True, use example data instead of CSV files
        
    Returns:
        Dictionary with execution results
    """
    result = {
        'success': False,
        'error': None,
        'output_file': None,
        'stats': {}
    }
    
    try:
        print("=" * 70)
        print("GRAPH VISUALIZER - Interactive HTML Network Visualization")
        print("=" * 70)
        print(f"Input directory: {input_dir}")
        print(f"Output directory: {output_dir}")
        print(f"Output filename: {output_filename}")
        
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
        
        # Create HTML visualization
        output_path = os.path.join(output_dir, output_filename)
        create_html_visualization(
            G,
            output_path,
            title="Red Eléctrica - Visualización Interactiva"
        )
        
        result['output_file'] = output_path
        result['success'] = True
        
        # Final summary
        print("\n" + "=" * 70)
        print("✅ VISUALIZATION COMPLETED SUCCESSFULLY")
        print("=" * 70)
        print(f"\n📁 Output file: {output_path}")
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
        description='Generate interactive HTML visualization of electrical network graph',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use CSV files from data directory (default)
  python graph_visualizer.py
  
  # Specify custom input directory
  python graph_visualizer.py --input-dir /path/to/csv/files
  
  # Specify custom output directory and filename
  python graph_visualizer.py --output-dir ./my_graphs --output-file my_graph.html
  
  # Use example data (ignore CSV files)
  python graph_visualizer.py --example
  
  # Full custom example
  python graph_visualizer.py --input-dir ./data --output-dir ./graphs --output-file network_2024.html

Notes:
  - This tool is independent and does not modify existing agrupar_circuitos.py functionality
  - CSV files expected: nodos_circuito.csv, segmentos_circuito.csv
  - Output is saved in the graph_output/ directory by default
  - Requires pyvis library: pip install pyvis
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
        '--output-file',
        type=str,
        default='red_electrica_graph.html',
        help='Name of output HTML file (default: red_electrica_graph.html)'
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
        output_filename=args.output_file,
        use_example_data=args.example
    )
    
    # Exit with appropriate code
    sys.exit(0 if result['success'] else 1)
