# Cytoscape Layout Documentation for Electrical Networks

## Overview

This document explains the choice of the **cose-bilkent** layout algorithm for visualizing electrical distribution networks in the `graph_visualizer.py` module.

## Layout Selection Criteria

When visualizing electrical distribution networks, the layout algorithm must:

1. ✅ Show hierarchical structure (substation → branches → transformers)
2. ✅ Minimize edge crossings for clarity
3. ✅ Handle tree-like topologies with multiple branches
4. ✅ Provide consistent, readable layouts
5. ❌ Avoid circle layouts (as per requirements)

## Why cose-bilkent?

### Description

**CoSE-Bilkent** (Compound Spring Embedder) is a force-directed layout algorithm specifically designed for:
- Hierarchical graph structures
- Compound graphs with nested nodes
- Complex networks with multiple branches

### Advantages for Electrical Networks

1. **Hierarchical Awareness**
   - Naturally positions the substation at the top/center
   - Shows branching structure clearly
   - Maintains parent-child relationships

2. **Edge Crossing Minimization**
   - Uses sophisticated algorithms to reduce visual clutter
   - Makes it easier to trace power flow paths
   - Improves overall readability

3. **Force-Directed Positioning**
   - Nodes are positioned based on their connections
   - Related components stay close together
   - Empty space is distributed naturally

4. **Branch Visualization**
   - Multiple branches from derivation points are clearly separated
   - Easy to identify different distribution paths
   - Transformers at branch endpoints are visually distinct

## Layout Comparison

### cose-bilkent (SELECTED)
```
                    [Subestación]
                          |
                    [Apoyo 1]
                          |
                    [Apoyo 2]
                       /     \
                      /       \
              [Rama A]         [Rama B]
                 |                |
           [Derivación]      [Derivación]
              /    \              |
             /      \        [Transformador]
    [Transformador] [Apoyo]
```

**Pros:**
- ✅ Clear hierarchical flow
- ✅ Minimal edge crossings
- ✅ Branches are well separated
- ✅ Easy to trace power paths

### circle (NOT USED)
```
        [Apoyo]---[Apoyo]
         /              \
    [Trans]            [Trans]
       |                  |
    [Apoyo]           [Apoyo]
       |                  |
  [Subestación]-------[Deriv]
```

**Cons:**
- ❌ No hierarchical structure shown
- ❌ Substation position not emphasized
- ❌ Difficult to identify flow direction
- ❌ Branches not visually separated
- ❌ Power flow path unclear

### Other Layout Options (Not Suitable)

- **random**: No structure, poor readability
- **grid**: Too rigid, doesn't respect connections
- **concentric**: Requires manual level assignment
- **breadthfirst**: Good alternative, but less sophisticated than cose-bilkent
- **dagre**: Good for directed graphs, but electrical networks are undirected

## Implementation Details

### Layout Configuration

```javascript
layout: { 
    name: 'cose-bilkent'
}
```

The algorithm uses default parameters which work well for electrical networks:
- Automatic spacing
- Optimal edge length calculation
- Quality-focused positioning (may take slightly longer but produces better results)

### Node Styling

Nodes are styled to enhance the hierarchical view:
- **Substation**: Labeled with name (starting point)
- **Other nodes**: No label (reduces clutter)
- **Size**: Based on voltage level (higher voltage = larger)
- **Color**: Type-based (Substation=Red, Transformer=Green, etc.)

### Edge Styling

- **Width**: Based on segment length
- **Color**: Uniform gray
- **Curve**: Bezier curves for smooth connections

## Performance Considerations

**cose-bilkent** characteristics:
- **Speed**: Moderate (quality over speed)
- **Scalability**: Good for networks up to ~1000 nodes
- **Quality**: Excellent for complex hierarchical structures

For very large networks (>1000 nodes), consider:
- Filtering to show only main branches
- Using zoom levels for detail
- Implementing pagination

## References

- [Cytoscape.js Documentation](https://js.cytoscape.org/)
- [CoSE-Bilkent Algorithm](https://github.com/cytoscape/cytoscape.js-cose-bilkent)
- [Layout Options Comparison](https://js.cytoscape.org/#layouts)

## Conclusion

The **cose-bilkent** layout is the optimal choice for electrical distribution network visualization because:

1. ✅ Respects the hierarchical nature of electrical networks
2. ✅ Produces clear, readable visualizations
3. ✅ Handles branching structures elegantly
4. ✅ Minimizes visual complexity
5. ✅ Does NOT use circle layout (as required)

This layout makes it easy for engineers and operators to:
- Understand network topology
- Trace power flow paths
- Identify branches and derivations
- Locate transformers and critical nodes
