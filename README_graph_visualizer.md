# Graph Visualizer - Interactive HTML Network Visualization

## 📖 Overview

`graph_visualizer.py` is an **independent standalone application** that generates interactive HTML visualizations of electrical network graphs from CSV data using **Cytoscape.js**. This tool is completely separate from the main `agrupar_circuitos.py` functionality and does not interfere with the existing processing pipeline.

## ✨ Features

- 🎨 **Interactive HTML Visualization**: Creates beautiful, interactive network graphs using Cytoscape.js library
- 🏷️ **Conditional Label Toggle**: Show/hide all node labels with a single button click
- 📊 **Graph Statistics**: Provides detailed statistics about the network (nodes, edges, connectivity, lengths)
- 🎯 **Color-coded Nodes**: Different colors and sizes for different node types (Substation, Support, Derivation, Transformer)
- 📏 **Smart Edge Display**: Edge thickness based on segment length
- 🔍 **Interactive Controls**: 
  - Toggle labels on/off conditionally
  - Zoom In/Out buttons
  - Reset zoom and fit to screen
  - Pan and explore the network
- 🎨 **Modern UI/UX**: Clean, professional design with smooth animations
- 📱 **Responsive Design**: Optimized for desktop and mobile devices
- 🖱️ **Interactive Highlighting**: Click nodes to highlight connections
- 📁 **Independent Output**: Saves all files to a separate `graph_output/` directory
- 🆓 **Open Source**: Uses free and open-source libraries (NetworkX, Cytoscape.js)
- 🎯 **Optimal Layout**: Uses cose-bilkent layout algorithm, ideal for electrical network visualization

## 🎨 UI/UX Improvements (v2.1)

The latest version includes major UI/UX enhancements:

### Modern Design
- **Clean Interface**: Professional look with modern color scheme
- **Gradient Backgrounds**: Subtle gradients for visual appeal
- **Better Spacing**: Improved padding and margins throughout
- **Card-Based Layout**: Statistics and controls in clean card containers
- **Custom Scrollbar**: Styled scrollbar for the sidebar

### Interactive Controls Panel
- **🏷️ Label Toggle**: Single button to show/hide all node labels conditionally
  - By default, only Subestación labels are shown
  - Click to toggle all labels on/off
- **🔍 Zoom Controls**: Four dedicated zoom buttons
  - Acercar + (Zoom In)
  - Alejar - (Zoom Out)
  - Resetear (Reset to default zoom)
  - Ajustar (Fit graph to screen)

### Enhanced Statistics Display
- **Organized Sections**: Statistics grouped into logical sections
  - 🔢 Propiedades (Properties)
  - 🏗️ Tipos de Nodos (Node Types)
  - 📏 Longitudes (Lengths)
- **Visual Hierarchy**: Clear labels and values with distinct styling
- **Icons**: Emoji icons for better visual recognition

### Color Legend
- **Visual Guide**: Shows node type colors
- **Circle Indicators**: Visual color swatches for each type
- **Clear Labels**: Subestación, Derivación, Transformador, Apoyo

### Graph Enhancements
- **Smooth Animations**: Transitions on node/edge interactions
- **Better Node Styling**: Enhanced borders and sizing
- **Interactive Highlighting**: Click a node to highlight its connections
- **Improved Edges**: Semi-transparent edges that highlight on selection
- **Optimized Layout**: Better cose-bilkent parameters for clearer visualization

## 🚀 Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- Modern web browser (Chrome, Firefox, Edge, Safari)

### Required Libraries

Install the required libraries using pip:

```bash
pip install pandas networkx
```

Or if you have a requirements file:

```bash
pip install -r requirements_graph.txt
```

### Verify Installation

```bash
python graph_visualizer.py --help
```

If you see the help message, the installation was successful!

## 📋 Usage

### Basic Usage

The simplest way to use the graph visualizer:

```bash
python graph_visualizer.py
```

This will:
1. Look for CSV files in the `./data` directory
2. Create a NetworkX graph from the data
3. Generate an interactive HTML visualization using Cytoscape.js
4. Save the output to `./graph_output/red_electrica_cytoscape.html`

### Using Example Data

If you don't have CSV files yet, you can use the built-in example data:

```bash
python graph_visualizer.py --example
```

This uses the same example data as defined in `agrupar_circuitos.py`.

### Custom Input Directory

Specify a custom directory containing your CSV files:

```bash
python graph_visualizer.py --input-dir /path/to/your/csv/files
```

### Custom Output Directory

Save the visualization to a specific location:

```bash
python graph_visualizer.py --output-dir ./my_visualizations
```

### Full Custom Example

```bash
python graph_visualizer.py \
  --input-dir ./data \
  --output-dir ./graphs/2024
```

## 📁 Input Files

The visualizer expects two CSV files in the input directory:

### 1. `nodos_circuito.csv` (Nodes)

Contains information about network nodes:

| Column | Type | Description |
|--------|------|-------------|
| `id_nodo` | int | Unique node identifier |
| `nombre` | str | Node name |
| `tipo` | str | Node type (Subestacion, Apoyo, Derivacion, Transformador) |
| `voltaje_kv` | float | Voltage in kV |
| `x` | float | X coordinate (longitude) |
| `y` | float | Y coordinate (latitude) |

**Example:**
```csv
id_nodo,nombre,tipo,voltaje_kv,x,y
1001,Subestacion_Principal,Subestacion,34.5,-70.65,-33.45
1002,Apoyo_MT_001,Apoyo,34.5,-70.651,-33.451
```

### 2. `segmentos_circuito.csv` (Segments)

Contains information about network segments (edges):

| Column | Type | Description |
|--------|------|-------------|
| `id_segmento` | int | Unique segment identifier |
| `id_circuito` | str | Circuit identifier |
| `nodo_inicio` | int | Starting node ID |
| `nodo_fin` | int | Ending node ID |
| `longitud_m` | float | Length in meters |
| `tipo_conductor` | str | Conductor type |
| `capacidad_amp` | int | Capacity in amperes |

**Example:**
```csv
id_segmento,id_circuito,nodo_inicio,nodo_fin,longitud_m,tipo_conductor,capacidad_amp
0,MT-001,1001,1002,523.5,AAC_150,250
1,MT-001,1002,1003,478.2,AAC_150,250
```

## 📤 Output

### Generated Files

The visualizer creates the following output in the `graph_output/` directory:

1. **`red_electrica_cytoscape.html`**
   - Interactive HTML visualization using Cytoscape.js
   - Can be opened in any modern web browser
   - No internet connection required after generation (uses CDN)
   
2. **`graph_cytoscape.json`**
   - JSON file with graph data in Cytoscape format
   
3. **`graph_nodes_minimal.csv` and `graph_edges_minimal.csv`**
   - Minimal CSV files for external use

### Output Directory Structure

```
graph_output/
├── red_electrica_cytoscape.html    # Interactive Cytoscape visualization
├── graph_cytoscape.json            # Graph data in Cytoscape format
├── graph_nodes_minimal.csv         # Minimal node data
└── graph_edges_minimal.csv         # Minimal edge data
```

### HTML Visualization Features

The generated HTML file includes:

- **Interactive Network Graph**: Pan and zoom to explore
- **Toggle Labels Button**: 🏷️ Show/hide all node labels conditionally with a single click
- **Zoom Controls**: 
  - 🔍 Mouse wheel to zoom in/out
  - ➕ Zoom In button
  - ➖ Zoom Out button
  - 🔄 Reset Zoom button
  - 📐 Fit to Screen button
- **Pan**: Click and drag background to move around
- **Force-Directed Layout**: Uses cose-bilkent algorithm optimized for hierarchical electrical networks
- **Color-Coded Nodes**: Different colors for different node types with visual legend
- **Statistics Panel**: Modern sidebar with detailed graph statistics
- **Interactive Highlighting**: Click nodes to highlight connections
- **Responsive Design**: Works on desktop and mobile browsers
- **Modern UI/UX**: Clean, professional interface with smooth animations

## 🎨 Visualization Details

### Node Representation

- **Colors**:
  - 🔴 Red: Substation (Subestación)
  - 🟡 Gold: Derivation (Derivación)
  - 🟢 Green: Transformer (Transformador)
  - 🔵 Blue: Support/Pole (Apoyo)

- **Sizes**:
  - Sized based on voltage level (higher voltage = larger node)

- **Labels**:
  - Substation: Name always displayed
  - Other nodes: Labels hidden by default (cleaner visualization)
  - Toggle Button: Show/hide all labels with the "🏷️ Mostrar/Ocultar Etiquetas" button

### Edge Representation

- **Width**: Based on segment length (dynamically calculated)
- **Color**: Neutral gray with transparency
- **Style**: Bezier curves for smooth connections
- **Interactive**: Highlighted when connected nodes are selected

### Layout Algorithm

The visualization uses the **cose-bilkent** layout algorithm, which is specifically designed for:
- Hierarchical structures (like electrical distribution networks)
- Force-directed positioning with quality results
- Automatic node placement that minimizes edge crossings
- Clear visualization of tree-like structures with branches

This layout is ideal for electrical networks as it naturally shows the hierarchical flow from substation through the distribution network.

## 📊 Statistics Output

The tool displays comprehensive statistics in the console:

```
📊 GRAPH STATISTICS
====================

🔢 Graph Properties:
   • Nodes: 12
   • Edges: 11
   • Connected: Yes
   • Components: 1
   • Density: 0.1667
   • Diameter: 5

🏗️ Node Type Distribution:
   • Subestacion: 1
   • Apoyo: 6
   • Derivacion: 1
   • Transformador: 3

📏 Edge Length Statistics:
   • Total length: 6.42 km (6416.7 m)
   • Average length: 583.3 m
   • Min length: 321.8 m
   • Max length: 932.7 m
```

## 🔧 Advanced Usage

### As a Python Module

You can also use `graph_visualizer.py` as a module in your own Python scripts:

```python
import graph_visualizer

# Option 1: Use the main function
result = graph_visualizer.main(
    input_dir='./data',
    output_dir='./my_graphs',
    use_example_data=False
)

if result['success']:
    print(f"Visualization created: {result['output_file']}")
    print(f"Statistics: {result['stats']}")
else:
    print(f"Error: {result['error']}")

# Option 2: Use individual functions
df_nodos, df_segmentos = graph_visualizer.load_csv_data('./data')
G = graph_visualizer.create_networkx_graph(df_nodos, df_segmentos)
stats = graph_visualizer.generate_graph_statistics(G)
cyto_json = graph_visualizer.export_cytoscape_json(G, './output')
cyto_html = graph_visualizer.create_cytoscape_html('./output', cyto_json, stats)
```

### Integration with Existing Pipeline

You can run the graph visualizer after the main `agrupar_circuitos.py` process:

```bash
# Step 1: Run main circuit grouping
python agrupar_circuitos.py --input-dir ./data --output-dir ./data

# Step 2: Generate visualization
python graph_visualizer.py --input-dir ./data --output-dir ./graph_output
```

Or create a simple script:

```python
import agrupar_circuitos
import graph_visualizer

# Run circuit grouping
result1 = agrupar_circuitos.main(input_dir='./data', output_dir='./data')

# Generate visualization
result2 = graph_visualizer.main(input_dir='./data', output_dir='./graph_output')

print(f"Groups created: {result1['stats']['num_grupos']}")
print(f"Visualization: {result2['output_file']}")
```

## 🎯 Use Cases

1. **Network Visualization**: Quickly visualize the structure of your electrical network
2. **Topology Analysis**: Understand network connectivity and identify bottlenecks
3. **Documentation**: Generate visual documentation for reports and presentations
4. **Quality Assurance**: Verify that CSV data is correct by visual inspection
5. **Education**: Use as a teaching tool to explain network topology concepts
6. **Debugging**: Identify data issues or network anomalies visually

## 📝 Command Line Options

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--input-dir` | - | `./data` | Directory containing CSV files |
| `--output-dir` | - | `./graph_output` | Directory to save output files |
| `--example` | - | False | Use example data instead of CSV files |
| `--help` | `-h` | - | Show help message |

## ⚠️ Important Notes

### Independence

- **No Interference**: This tool does not modify or interfere with `agrupar_circuitos.py`
- **Separate Output**: All files are saved to a separate `graph_output/` directory
- **Read-Only**: Only reads CSV files, never modifies them
- **Standalone**: Can be used independently without running other scripts

### Data Requirements

- CSV files must follow the expected format (see Input Files section)
- Node IDs in segments must match node IDs in the nodes file
- Missing or malformed data will cause errors

### Browser Compatibility

The generated HTML works best with modern browsers:
- ✅ Google Chrome (recommended)
- ✅ Mozilla Firefox
- ✅ Microsoft Edge
- ✅ Safari
- ⚠️ Internet Explorer (not recommended)

## 🐛 Troubleshooting

### Problem: "ModuleNotFoundError: No module named 'pandas'" or similar

**Solution**: Install required libraries
```bash
pip install pandas networkx
```

### Problem: "File not found" error

**Solution**: Make sure CSV files exist in the input directory, or use `--example` flag
```bash
python graph_visualizer.py --example
```

### Problem: "Graph is empty" or "No nodes/edges"

**Solution**: Check that your CSV files contain valid data and are not empty

### Problem: HTML file doesn't open or shows errors

**Solution**: 
- Make sure you're using a modern browser
- Try opening the file with a different browser
- Check that the file was completely generated (no process interruption)

## 📚 Dependencies

- **pandas**: Data manipulation and CSV reading
- **networkx**: Graph creation and analysis
- **Cytoscape.js**: Interactive network visualization (loaded via CDN in HTML)

## 🔐 Security

- No external network connections required after generation
- No sensitive data is transmitted
- All processing is done locally
- Output HTML is self-contained

## 📄 License

This tool is part of the agrupar_circuitos project. See the main project for license information.

## 👤 Author

- **Roman Sarmiento**
- Date: 2025-12-16
- Version: 2.0 (Cytoscape.js implementation)

## 🤝 Contributing

This is an independent module. If you find bugs or have suggestions for improvements, please contribute to the main project.

## 🔗 Related Tools

- **agrupar_circuitos.py**: Main circuit grouping application
- **oracle_export.py**: Oracle database export utility
- **main.py**: Integrated pipeline script

## 📞 Support

For issues or questions:
1. Check this README for solutions
2. Review the error messages carefully
3. Try using the `--example` flag to test with known-good data
4. Check that all dependencies are installed correctly

---

**Happy Visualizing! 🎉**
