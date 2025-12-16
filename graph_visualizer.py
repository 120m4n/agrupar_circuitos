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
        """
        os.makedirs(output_dir, exist_ok=True)
        html_path = os.path.join(output_dir, 'red_electrica_cytoscape.html')

        # Build an HTML snippet for stats (simple layout preserving values)
        stats_html_lines = []
        stats_html_lines.append(f"<h2>GRAPH STATISTICS</h2>")
        stats_html_lines.append('<div class="stat-block">')
        stats_html_lines.append(f"<p><strong>Nodes:</strong> {stats.get('num_nodes', 0)}</p>")
        stats_html_lines.append(f"<p><strong>Edges:</strong> {stats.get('num_edges', 0)}</p>")
        stats_html_lines.append(f"<p><strong>Connected:</strong> {'Yes' if stats.get('is_connected') else 'No'}</p>")
        stats_html_lines.append(f"<p><strong>Components:</strong> {stats.get('num_components')}</p>")
        stats_html_lines.append(f"<p><strong>Density:</strong> {stats.get('density', 0):.4f}</p>")
        if stats.get('diameter') is not None:
                stats_html_lines.append(f"<p><strong>Diameter:</strong> {stats.get('diameter')}</p>")
        stats_html_lines.append('<h3>Node Types</h3>')
        for t, c in stats.get('node_types', {}).items():
                stats_html_lines.append(f"<p><strong>{t}:</strong> {c}</p>")
        stats_html_lines.append('<h3>Edge Lengths</h3>')
        stats_html_lines.append(f"<p><strong>Total:</strong> {stats.get('total_length_km', 0):.2f} km ({stats.get('total_length_m', 0):.1f} m)</p>")
        stats_html_lines.append(f"<p><strong>Average:</strong> {stats.get('avg_edge_length_m', 0):.1f} m</p>")
        stats_html_lines.append(f"<p><strong>Min:</strong> {stats.get('min_edge_length_m', 0):.1f} m</p>")
        stats_html_lines.append(f"<p><strong>Max:</strong> {stats.get('max_edge_length_m', 0):.1f} m</p>")
        stats_html_lines.append('</div>')
        stats_html = '\n'.join(stats_html_lines)

        # Simple Cytoscape HTML template using CDN
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
            body { margin:0; font-family: Arial, Helvetica, sans-serif; }
            #container { display:flex; height:100vh; }
            #cy { flex:1; border-left:1px solid #ddd; }
            #sidebar { width:320px; padding:16px; box-sizing:border-box; background:#f7f7f7; overflow:auto; }
            h1,h2 { margin:8px 0; }
            .stat-block p { margin:6px 0; }
        </style>
        <script src="https://unpkg.com/cytoscape@3.24.0/dist/cytoscape.min.js"></script>
        <script src="https://unpkg.com/cytoscape-cose-bilkent@4.0.0/cytoscape-cose-bilkent.js"></script>
    </head>
    <body>
        <div id="container">
            <div id="sidebar">
                <h1><<<TITLE>>></h1>
                <<<STATS_HTML>>>
                <p style="margin-top:12px; font-size:0.9em; color:#666;">Generado: <<<GEN_TIME>>></p>
            </div>
            <div id="cy"></div>
        </div>

        <script>
            fetch('<<<JSON>>>')
                .then(r => r.json())
                .then(data => {
                    const cy = cytoscape({
                        container: document.getElementById('cy'),
                        elements: data.elements,
                        style: [
                            { selector: 'node', style: { 'label': 'data(nombre)', 'background-color': 'data(color)', 'width': 'mapData(voltaje_kv, 0, 35, 20,40)', 'height': 'mapData(voltaje_kv, 0, 35, 20,40)', 'text-valign': 'center', 'color': '#fff', 'text-outline-width': 2, 'text-outline-color': '#333' } },
                            { selector: "node[tipo != 'Subestacion']", style: { 'label': '' } },
                            { selector: 'edge', style: { 'width': 'data(width)', 'line-color': 'data(color)', 'curve-style': 'bezier' } }
                        ],
                        layout: { name: 'cose-bilkent' }
                    });
                })
                .catch(err => {
                    document.getElementById('cy').innerText = 'Error cargando el grafo: ' + err;
                });
        </script>
    </body>
    </html>
    """

        gen_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        html_content = html_template.replace('<<<TITLE>>>', title).replace('<<<STATS_HTML>>>', stats_html).replace('<<<JSON>>>', json_basename).replace('<<<GEN_TIME>>>', gen_time)

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
    output_filename: str = 'red_electrica_cytoscape.html',
    use_example_data: bool = False
) -> Dict:
    """
    Main function to generate graph visualization using Cytoscape.js.
    
    Args:
        input_dir: Directory containing CSV files
        output_dir: Directory to save output files
        output_filename: Name of the output HTML file (ignored, uses cytoscape naming)
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
        cyto_json = export_cytoscape_json(G, output_dir)
        result['cytoscape_json'] = cyto_json
        if cyto_json:
            cyto_html = create_cytoscape_html(output_dir, cyto_json, stats, title="Red Eléctrica - Cytoscape")
            result['cytoscape_html'] = cyto_html
            result['output_file'] = cyto_html
        else:
            result['cytoscape_html'] = None
            print(f"⚠️ Error exporting Cytoscape files")
            
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
        default='red_electrica_cytoscape.html',
        help='Name of output HTML file (default: red_electrica_cytoscape.html)'
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
