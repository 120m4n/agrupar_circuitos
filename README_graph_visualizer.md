# Graph Visualizer - Interactive HTML Network Visualization

## 📖 Overview

`graph_visualizer.py` is an **independent standalone application** that generates interactive HTML visualizations of electrical network graphs from CSV data. This tool is completely separate from the main `agrupar_circuitos.py` functionality and does not interfere with the existing processing pipeline.

## ✨ Features

- 🎨 **Interactive HTML Visualization**: Creates beautiful, interactive network graphs using the Pyvis library
- 📊 **Graph Statistics**: Provides detailed statistics about the network (nodes, edges, connectivity, lengths)
- 🎯 **Color-coded Nodes**: Different colors and sizes for different node types (Substation, Support, Derivation, Transformer)
- 📏 **Smart Edge Display**: Edge thickness and color based on segment properties
- 💡 **Hover Tooltips**: Detailed information on hover for nodes and edges
- 🔍 **Interactive Controls**: Zoom, pan, drag nodes, and navigate through the network
- 📁 **Independent Output**: Saves all files to a separate `graph_output/` directory
- 🆓 **Open Source**: Uses free and open-source libraries (NetworkX, Pyvis)

## 🚀 Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

### Required Libraries

Install the required libraries using pip:

```bash
pip install pandas networkx pyvis
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
3. Generate an interactive HTML visualization
4. Save the output to `./graph_output/red_electrica_graph.html`

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

### Custom Output Directory and Filename

Save the visualization to a specific location with a custom name:

```bash
python graph_visualizer.py --output-dir ./my_visualizations --output-file my_network.html
```

### Full Custom Example

```bash
python graph_visualizer.py \
  --input-dir ./data \
  --output-dir ./graphs/2024 \
  --output-file network_dec_2024.html
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

1. **`red_electrica_graph.html`** (or custom filename)
   - Interactive HTML visualization
   - Can be opened in any modern web browser
   - No internet connection required after generation

### Output Directory Structure

```
graph_output/
└── red_electrica_graph.html    # Interactive visualization
```

### HTML Visualization Features

The generated HTML file includes:

- **Interactive Network Graph**: Click and drag nodes to rearrange
- **Zoom Controls**: Mouse wheel or pinch to zoom in/out
- **Pan**: Click and drag background to move around
- **Node Tooltips**: Hover over nodes to see detailed information
- **Edge Tooltips**: Hover over edges to see segment details
- **Navigation Buttons**: Built-in controls for easy navigation
- **Legend**: Color legend for different node types
- **Statistics Header**: Summary of network statistics

## 🎨 Visualization Details

### Node Representation

- **Colors**:
  - 🔴 Red: Substation (Subestación)
  - 🟡 Gold: Derivation (Derivación)
  - 🟢 Green: Transformer (Transformador)
  - 🔵 Blue: Support/Pole (Apoyo)

- **Sizes**:
  - Substation: Largest (35px)
  - Derivation/Transformer: Medium (25px)
  - Support: Small (15px)

- **Labels**:
  - Substation: 🏭 + Name
  - Transformer: ⚡ + ID
  - Derivation: ⚪ + ID
  - Support: ID only

### Edge Representation

- **Width**: Based on segment length (shorter segments = thicker lines)
- **Color**: Based on conductor type
  - AAC_150: Dodger Blue
  - AAC_95: Orange
  - Other: Gray

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
    output_filename='network.html',
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
graph_visualizer.create_html_visualization(G, './output/graph.html')
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
| `--output-file` | - | `red_electrica_graph.html` | Name of output HTML file |
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

### Problem: "ModuleNotFoundError: No module named 'pyvis'"

**Solution**: Install pyvis library
```bash
pip install pyvis
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
- **pyvis**: Interactive network visualization

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
- Version: 1.0

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
