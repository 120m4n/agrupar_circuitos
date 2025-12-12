# Agrupación de Circuitos Eléctricos

Este proyecto implementa un algoritmo basado en **DFS (Depth-First Search)** y **NetworkX** para agrupar segmentos de una red eléctrica en tramos de aproximadamente **1 km**. 

Es útil para la gestión de activos, planificación de mantenimiento y análisis de redes de distribución de media tensión.

## 📋 Características

- **Carga de Datos**: Ingesta de datos desde archivos CSV (`segmentos_circuito.csv`, `nodos_circuito.csv`). Genera datos de prueba si no existen.
- **Modelado de Red**: Construcción de un grafo no dirigido ponderado utilizando `NetworkX`.
- **Agrupación Inteligente**: 
  - Utiliza un recorrido DFS para recorrer la red desde la subestación.
  - Agrupa segmentos contiguos hasta completar ~1 km (configurable).
  - Maneja tolerancias y ramificaciones.
- **Análisis y Estadísticas**: Calcula métricas de los grupos formados (min, max, promedio, desviación estándar).
- **Visualización**: Genera mapas de la red coloreados por grupos (`red_electrica_grupos.png`).
- **Exportación GIS**: Genera archivos GeoJSON para integración con sistemas GIS (QGIS, ArcGIS).

## 🚀 Requisitos

- Python 3.8+
- Librerías:
  - `pandas`
  - `networkx`
  - `matplotlib`
  - `numpy`
  - `geopandas` (para exportación GIS)
  - `shapely` (para geometrías GIS)

```bash
pip install pandas networkx matplotlib numpy geopandas shapely
```

## 🛠️ Uso

Ejecuta el script principal:

```bash
python agrupar_circuitos.py
```

El script verificará si existen los archivos de entrada. Si no, creará datos de ejemplo automáticamente.

### Salidas Generadas

1.  `grupos_1km.csv`: Tabla resumen de los grupos formados.
2.  `segmentos_con_grupo.csv`: Detalle de cada segmento con su ID de grupo asignado.
3.  `red_electrica_grupos.png`: Visualización gráfica de la red.
4.  `segmentos_con_grupos.geojson`: Archivo geoespacial para GIS.

## 🧩 Diagrama Funcional

El siguiente diagrama describe el flujo de lógica del algoritmo de agrupación:

```mermaid
flowchart TD
    A[Inicio] --> B{¿Existen CSVs?}
    B -- No --> C[Generar Datos Dummy]
    B -- Sí --> D[Cargar DataFrames]
    C --> D
    
    D --> E[Construir Grafo NetworkX]
    E --> F[Identificar Subestación]
    
    F --> G[Iniciar DFS desde Subestación]
    
    G --> H{¿Pila Vacía?}
    H -- Sí --> Z[Fin Agrupación]
    H -- No --> I[Pop Nodo Actual]
    
    I --> J{¿Visitado?}
    J -- Sí --> H
    J -- No --> K[Procesar Segmento Entrante]
    
    K --> L{¿Acumulado + Seg <= Objetivo + Tol?}
    
    L -- Sí --> M[Agregar a Grupo Actual]
    M --> N{¿Grupo >= Objetivo - Tol?}
    N -- Sí --> O[Cerrar Grupo]
    N -- No --> P[Continuar]
    
    L -- No --> Q[Cerrar Grupo Actual]
    Q --> R[Crear Nuevo Grupo con Segmento]
    
    O --> P
    R --> P
    
    P --> S[Marcar Visitado]
    S --> T[Push Vecinos a Pila]
    T --> H

    Z --> AA[Analizar Estadísticas]
    AA --> AB[Exportar CSV/GeoJSON]
    AB --> AC[Visualizar Grafico]
    AC --> AD[Fin]
    
    style A fill:#f9f,stroke:#333
    style Z fill:#f9f,stroke:#333
    style AD fill:#f9f,stroke:#333
    style O fill:#bfb,stroke:#333
    style Q fill:#fbb,stroke:#333
```
