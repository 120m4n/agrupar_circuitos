#!/usr/bin/env python3
"""
DFS con NetworkX para agrupar segmentos de ~1km en red eléctrica
Autor: Roman Sarmiento, Asistente DeepSeek
Fecha: 2025-12-12
Versión: 1.0
"""

import pandas as pd
import networkx as nx
from collections import defaultdict, deque
import numpy as np
from typing import List, Dict, Tuple, Set
import argparse
import os

# ============================================================================
# CONFIGURACIÓN DE PARÁMETROS
# ============================================================================
def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Agrupar segmentos de red eléctrica en tramos de ~1km usando DFS'
    )
    parser.add_argument(
        '--input-dir',
        type=str,
        default='./data',
        help='Directorio de entrada para archivos CSV (default: ./data)'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='./data',
        help='Directorio de salida para archivos generados (default: ./data)'
    )
    return parser.parse_args()

def cargar_datos_csv(input_dir):
    """
    Cargar datos desde archivos CSV o generar datos de ejemplo
    
    Args:
        input_dir: Directorio de entrada para archivos CSV
        
    Returns:
        tuple: (df_segmentos, df_nodos)
    """
    print("\n📥 PASO 1: CARGANDO DATOS DESDE ARCHIVOS CSV...")
    
    # Leer segmentos (aristas)
    try:
        segmentos_path = os.path.join(input_dir, 'segmentos_circuito.csv')
        df_segmentos = pd.read_csv(segmentos_path)
        print(f"✅ Segmentos cargados: {len(df_segmentos)} registros")
    except FileNotFoundError:
        print("⚠️  Creando datos de ejemplo...")
        # Datos de ejemplo si no existe el archivo
        df_segmentos = pd.DataFrame({
            'id_segmento': range(11),
            'id_circuito': ['MT-001'] * 11,
            'nodo_inicio': [1001, 1002, 1003, 1004, 1005, 1002, 2001, 2002, 2003, 1004, 3001],
            'nodo_fin': [1002, 1003, 1004, 1005, 1006, 2001, 2002, 2003, 2004, 3001, 3002],
            'longitud_m': [523.5, 478.2, 612.8, 389.4, 734.1, 845.3, 567.9, 423.6, 321.8, 932.7, 587.4],
            'tipo_conductor': ['AAC_150']*5 + ['AAC_95']*4 + ['AAC_150']*2,
            'capacidad_amp': [250, 250, 250, 250, 250, 180, 180, 180, 180, 250, 250]
        })
    
    # Leer nodos (vértices)
    try:
        nodos_path = os.path.join(input_dir, 'nodos_circuito.csv')
        df_nodos = pd.read_csv(nodos_path)
        print(f"✅ Nodos cargados: {len(df_nodos)} registros")
    except FileNotFoundError:
        print("⚠️  Creando datos de nodos de ejemplo...")
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
    
    print("\n📊 RESUMEN INICIAL:")
    print(f"• Longitud total de circuitos: {df_segmentos['longitud_m'].sum()/1000:.2f} km")
    print(f"• Segmento más largo: {df_segmentos['longitud_m'].max():.1f} m")
    print(f"• Segmento más corto: {df_segmentos['longitud_m'].min():.1f} m")
    
    return df_segmentos, df_nodos

# ============================================================================
# 2. CONSTRUIR GRAFO CON NETWORKX
# ============================================================================

class RedElectrica:
    """Clase para gestionar la red eléctrica usando NetworkX"""
    
    def __init__(self):
        self.G = nx.Graph()
        self.segmentos_por_grupo = defaultdict(list)
        self.grupos = {}
        
    def cargar_datos(self, df_segmentos: pd.DataFrame, df_nodos: pd.DataFrame):
        """Cargar datos de segmentos y nodos al grafo"""
        
        # Agregar nodos con atributos
        for _, nodo in df_nodos.iterrows():
            self.G.add_node(
                nodo['id_nodo'],
                nombre=nodo['nombre'],
                tipo=nodo['tipo'],
                voltaje_kv=nodo['voltaje_kv'],
                pos=(nodo['x'], nodo['y'])
            )
        
        # Agregar aristas (segmentos) con atributos
        for _, segmento in df_segmentos.iterrows():
            self.G.add_edge(
                segmento['nodo_inicio'],
                segmento['nodo_fin'],
                id_segmento=segmento['id_segmento'],
                longitud_m=segmento['longitud_m'],
                tipo_conductor=segmento['tipo_conductor'],
                capacidad_amp=segmento['capacidad_amp'],
                id_circuito=segmento['id_circuito']
            )
        
        print(f"   Nodos agregados: {self.G.number_of_nodes()}")
        print(f"   Segmentos agregados: {self.G.number_of_edges()}")
    
    def encontrar_subestacion_principal(self) -> int:
        """Encontrar la subestación principal (nodo con tipo 'Subestacion')"""
        for nodo in self.G.nodes(data=True):
            if nodo[1]['tipo'] == 'Subestacion':
                print(f"   Subestación principal encontrada: Nodo {nodo[0]} - {nodo[1]['nombre']}")
                return nodo[0]
        
        # Si no hay subestación, usar el nodo con mayor grado
        grados = dict(self.G.degree())
        nodo_principal = max(grados, key=grados.get)
        print(f"   Usando nodo con mayor grado: Nodo {nodo_principal}")
        return nodo_principal
    
    def dfs_agrupar_segmentos(self, longitud_objetivo_m: float = 1000.0, 
                              tolerancia_km: float = 0.2) -> Dict:
        """
        DFS para agrupar segmentos contiguos en grupos de ~1km
        
        Args:
            longitud_objetivo_m: Longitud objetivo en metros (default: 1000m = 1km)
            tolerancia_km: Tolerancia en kilómetros (default: ±200m)
        """
        
        nodo_inicio = self.encontrar_subestacion_principal()
        visitados = set()
        grupos = []
        grupo_actual = []
        longitud_actual = 0.0
        grupo_id = 1
        
        # Usar pila para DFS iterativo: (nodo_actual, nodo_anterior, segmento_id, longitud)
        pila = [(nodo_inicio, None, None, 0.0)]
        
        print(f"\n🎯 AGRUPANDO SEGMENTOS EN GRUPOS DE ~{longitud_objetivo_m/1000}km")
        print(f"   Tolerancia: ±{tolerancia_km*1000}m")
        print("-" * 60)
        
        while pila:
            nodo_actual, nodo_anterior, segmento_id, longitud_segmento = pila.pop()
            
            if nodo_actual in visitados:
                continue
            
            # Si hay un segmento que agregar (no es el inicio)
            if segmento_id is not None:
                # Verificar si agregar este segmento al grupo actual
                if (longitud_actual + longitud_segmento <= 
                    longitud_objetivo_m * (1 + tolerancia_km)):
                    
                    # Agregar al grupo actual
                    grupo_actual.append({
                        'segmento_id': segmento_id,
                        'longitud_m': longitud_segmento,
                        'nodo_inicio': nodo_anterior,
                        'nodo_fin': nodo_actual
                    })
                    longitud_actual += longitud_segmento
                    
                    print(f"   Grupo {grupo_id}: +Segmento {segmento_id} "
                          f"({longitud_segmento}m) "
                          f"[Acumulado: {longitud_actual:.1f}m]")
                    
                    # Si alcanzamos el objetivo, cerrar grupo
                    if longitud_actual >= longitud_objetivo_m * (1 - tolerancia_km):
                        self._cerrar_grupo(grupo_actual, longitud_actual, grupo_id)
                        grupo_actual = []
                        longitud_actual = 0.0
                        grupo_id += 1
                
                else:
                    # Este segmento excede la tolerancia, crear nuevo grupo con él
                    if grupo_actual:  # Si hay grupo actual, cerrarlo primero
                        self._cerrar_grupo(grupo_actual, longitud_actual, grupo_id)
                        grupo_id += 1
                    
                    # Crear nuevo grupo con este segmento
                    grupo_actual = [{
                        'segmento_id': segmento_id,
                        'longitud_m': longitud_segmento,
                        'nodo_inicio': nodo_anterior,
                        'nodo_fin': nodo_actual
                    }]
                    longitud_actual = longitud_segmento
                    print(f"   🔄 Nuevo grupo {grupo_id} con segmento {segmento_id}")
            
            visitados.add(nodo_actual)
            
            # Explorar vecinos en orden inverso para mantener orden natural
            vecinos = list(self.G.neighbors(nodo_actual))
            vecinos.reverse()  # Para procesar en el orden correcto con pila LIFO
            
            for vecino in vecinos:
                if vecino not in visitados:
                    # Obtener información del segmento
                    segmento_data = self.G.get_edge_data(nodo_actual, vecino)
                    pila.append((
                        vecino,
                        nodo_actual,
                        segmento_data['id_segmento'],
                        segmento_data['longitud_m']
                    ))
        
        # Cerrar el último grupo si queda algo
        if grupo_actual:
            self._cerrar_grupo(grupo_actual, longitud_actual, grupo_id)
        
        return self.grupos
    
    def _cerrar_grupo(self, segmentos: List, longitud_total: float, grupo_id: int):
        """Cerrar un grupo y almacenar la información"""
        self.grupos[grupo_id] = {
            'segmentos': segmentos.copy(),
            'longitud_total_m': longitud_total,
            'num_segmentos': len(segmentos),
            'longitud_km': longitud_total / 1000
        }
        
        # Almacenar relación inversa (segmento -> grupo)
        for segmento in segmentos:
            self.segmentos_por_grupo[segmento['segmento_id']] = grupo_id
        
        print(f"   ✅ Grupo {grupo_id} CERRADO: "
              f"{len(segmentos)} segmentos, "
              f"{longitud_total:.1f}m ({longitud_total/1000:.2f}km)")
    

    def _agrupar_camino(self, segmentos: List, longitud_objetivo: float) -> List:
        """Agrupar segmentos de un camino en tramos de longitud objetivo"""
        grupos = []
        grupo_actual = []
        longitud_actual = 0.0
        
        for segmento in segmentos:
            # Si agregar este segmento excede el objetivo (con tolerancia)
            if longitud_actual + segmento['longitud_m'] > longitud_objetivo * 1.2:
                # Si el grupo actual tiene algo, cerrarlo
                if grupo_actual:
                    grupos.append({
                        'segmentos': grupo_actual.copy(),
                        'longitud_total': longitud_actual
                    })
                    grupo_actual = []
                    longitud_actual = 0.0
                
                # Si el segmento individual es muy largo (>1.2km)
                if segmento['longitud_m'] > longitud_objetivo * 1.2:
                    # Dividir segmento virtualmente (solo para agrupación)
                    grupos.append({
                        'segmentos': [segmento],
                        'longitud_total': segmento['longitud_m'],
                        'nota': 'Segmento largo individual'
                    })
                else:
                    grupo_actual = [segmento]
                    longitud_actual = segmento['longitud_m']
            else:
                grupo_actual.append(segmento)
                longitud_actual += segmento['longitud_m']
                
                # Si alcanzamos el objetivo, cerrar grupo
                if longitud_actual >= longitud_objetivo * 0.8:  # 80% del objetivo
                    grupos.append({
                        'segmentos': grupo_actual.copy(),
                        'longitud_total': longitud_actual
                    })
                    grupo_actual = []
                    longitud_actual = 0.0
        
        # Agregar último grupo si queda algo
        if grupo_actual:
            grupos.append({
                'segmentos': grupo_actual.copy(),
                'longitud_total': longitud_actual
            })
        
        return grupos
    
    def analizar_resultados(self, output_dir):
        """Analizar y mostrar resultados de la agrupación"""
        if not self.grupos:
            print("⚠️  No hay grupos para analizar. Ejecuta dfs_agrupar_segmentos() primero.")
            return
        
        print("\n" + "=" * 70)
        print("📊 ANÁLISIS DE RESULTADOS")
        print("=" * 70)
        
        longitudes = [g['longitud_total_m'] for g in self.grupos.values()]
        
        print(f"\n📈 ESTADÍSTICAS DE GRUPOS:")
        print(f"   • Total grupos formados: {len(self.grupos)}")
        print(f"   • Longitud promedio: {np.mean(longitudes)/1000:.2f} km")
        print(f"   • Longitud mínima: {np.min(longitudes)/1000:.2f} km")
        print(f"   • Longitud máxima: {np.max(longitudes)/1000:.2f} km")
        print(f"   • Desviación estándar: {np.std(longitudes)/1000:.2f} km")
        
        print("\n📋 DETALLE DE GRUPOS:")
        print("-" * 70)
        print(f"{'Grupo':<6} {'Segs':<6} {'Longitud (m)':<12} {'Longitud (km)':<12}")
        print("-" * 70)
        
        for grupo_id, info in sorted(self.grupos.items()):
            print(f"{grupo_id:<6} {info['num_segmentos']:<6} "
                  f"{info['longitud_total_m']:<12.1f} "
                  f"{info['longitud_total_m']/1000:<12.2f}")
        
        # Exportar resultados a CSV
        self.exportar_resultados_csv(output_dir)
    
    def exportar_resultados_csv(self, output_dir):
        """Exportar resultados a archivos CSV"""
        # 1. Grupos a CSV
        datos_grupos = []
        for grupo_id, info in self.grupos.items():
            datos_grupos.append({
                'grupo_id': grupo_id,
                'num_segmentos': info['num_segmentos'],
                'longitud_total_m': info['longitud_total_m'],
                'longitud_km': info['longitud_total_m'] / 1000
            })
        
        df_grupos = pd.DataFrame(datos_grupos)
        grupos_path = os.path.join(output_dir, 'grupos_1km.csv')
        df_grupos.to_csv(grupos_path, index=False)
        
        # 2. Segmentos con su grupo asignado
        datos_segmentos = []
        for segmento_id, grupo_id in self.segmentos_por_grupo.items():
            # Buscar información del segmento
            for u, v, data in self.G.edges(data=True):
                if data['id_segmento'] == segmento_id:
                    datos_segmentos.append({
                        'segmento_id': segmento_id,
                        'grupo_id': grupo_id,
                        'nodo_inicio': u,
                        'nodo_fin': v,
                        'longitud_m': data['longitud_m'],
                        'tipo_conductor': data['tipo_conductor'],
                        'circuito': data['id_circuito']
                    })
                    break
        
        df_segmentos_grupo = pd.DataFrame(datos_segmentos)
        segmentos_path = os.path.join(output_dir, 'segmentos_con_grupo.csv')
        df_segmentos_grupo.to_csv(segmentos_path, index=False)
        
        print(f"\n💾 RESULTADOS EXPORTADOS:")
        print(f"   • {grupos_path}: {len(df_grupos)} grupos")
        print(f"   • {segmentos_path}: {len(df_segmentos_grupo)} segmentos")

# ============================================================================
# 3. EJECUCIÓN PRINCIPAL
# ============================================================================
def main(input_dir='./data', output_dir='./data'):
    """
    Función principal de ejecución
    
    Args:
        input_dir: Directorio de entrada para archivos CSV (default: './data')
        output_dir: Directorio de salida para archivos generados (default: './data')
        
    Returns:
        Dict con resultados del proceso:
        {
            'success': bool,
            'grupos': dict,
            'red': RedElectrica instance,
            'stats': {
                'num_grupos': int,
                'num_segmentos': int,
                'num_nodos': int
            },
            'error': str (optional, only if success=False)
        }
    """
    try:
        # Cargar datos
        df_segmentos, df_nodos = cargar_datos_csv(input_dir)
        
        # Crear instancia de la red eléctrica
        print("\n\n🔗 PASO 2: CONSTRUYENDO GRAFO CON NETWORKX...")
        red = RedElectrica()
        
        # 1. Cargar datos al grafo
        red.cargar_datos(df_segmentos, df_nodos)
        
        print("\n" + "=" * 70)
        print("🔍 ANÁLISIS TOPOLÓGICO INICIAL")
        print("=" * 70)
        
        # Análisis básico del grafo
        print(f"\n📐 PROPIEDADES DEL GRAFO:")
        print(f"   • Es conexo: {nx.is_connected(red.G)}")
        print(f"   • Número de componentes conexos: {nx.number_connected_components(red.G)}")
        print(f"   • Diámetro: {nx.diameter(red.G) if nx.is_connected(red.G) else 'N/A'}")
        print(f"   • Densidad: {nx.density(red.G):.4f}")
        
        # 2. Agrupar segmentos usando DFS
        print("\n" + "=" * 70)
        print("🔄 EJECUTANDO DFS PARA AGRUPAR SEGMENTOS")
        print("=" * 70)
        
        # Opción 1: DFS simple (agrupa a lo largo del recorrido)
        grupos = red.dfs_agrupar_segmentos(
            longitud_objetivo_m=1000.0,  # 1km
            tolerancia_km=0.1  # ±100m
        )
        
        
        # 3. Analizar resultados
        red.analizar_resultados(output_dir)
        
        # 4. Exportar para GIS
        print("\n" + "=" * 70)
        print("🗺️  PREPARANDO DATOS PARA GIS")
        print("=" * 70)
        
        # Crear GeoDataFrame para exportar a Shapefile/GeoJSON
        import geopandas as gpd
        from shapely.geometry import LineString
        
        # Datos de ejemplo de coordenadas (en realidad usarías tus coordenadas reales)
        # Aquí asumimos que los nodos tienen coordenadas x,y
        geometrias = []
        atributos = []
        
        for u, v, data in red.G.edges(data=True):
            # Obtener coordenadas de los nodos
            u_pos = red.G.nodes[u]['pos']
            v_pos = red.G.nodes[v]['pos']
            
            # Crear LineString
            linea = LineString([u_pos, v_pos])
            geometrias.append(linea)
            
            # Atributos
            atributos.append({
                'id_segmento': data['id_segmento'],
                'grupo_id': red.segmentos_por_grupo.get(data['id_segmento'], -1),
                'longitud_m': data['longitud_m'],
                'tipo_conductor': data['tipo_conductor'],
                'circuito': data['id_circuito'],
                'nodo_inicio': u,
                'nodo_fin': v
            })
        
        gdf = gpd.GeoDataFrame(atributos, geometry=geometrias, crs="EPSG:4326")
        geojson_path = os.path.join(output_dir, 'segmentos_con_grupos.geojson')
        gpkg_path = os.path.join(output_dir, 'segmentos_con_grupos.gpkg')
        gdf.to_file(geojson_path, driver='GeoJSON')
        gdf.to_file(gpkg_path, driver='GPKG')
        
        print(f"✅ GeoJSON exportado: '{geojson_path}'")
        print(f"✅ GeoPackage exportado: '{gpkg_path}'")
        print(f"   {len(gdf)} segmentos con información de grupo")
        
        # Resumen final
        print("\n" + "=" * 70)
        print("✅ PROCESO COMPLETADO EXITOSAMENTE")
        print("=" * 70)
        print(f"""
    Resumen del proceso:
    1. 📊 Datos cargados: {len(df_segmentos)} segmentos, {len(df_nodos)} nodos
    2. 🔗 Grafo construido: {red.G.number_of_nodes()} nodos, {red.G.number_of_edges()} aristas
    3. 🎯 Segmentos agrupados: {len(red.grupos)} grupos de ~1km
    4. 💾 Archivos generados en {output_dir}:
       • grupos_1km.csv
       • segmentos_con_grupo.csv  
       • segmentos_con_grupos.geojson
       • segmentos_con_grupos.gpkg
    
    Siguientes pasos sugeridos:
    • Importa el GeoJSON o GeoPackage a QGIS/ArcGIS
    • Usa el campo 'grupo_id' para simbología
    • Calcula estadísticas por grupo en tu GIS
        """)
    
        # Return results for library usage
        return {
            'success': True,
            'grupos': red.grupos,
            'red': red,
            'stats': {
                'num_grupos': len(red.grupos),
                'num_segmentos': len(df_segmentos),
                'num_nodos': len(df_nodos)
            },
            'files': {
                'grupos': os.path.join(output_dir, 'grupos_1km.csv'),
                'segmentos': os.path.join(output_dir, 'segmentos_con_grupo.csv'),
                'geojson': geojson_path,
                'gpkg': gpkg_path
            }
        }
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'error': str(e)
        }

# ============================================================================
# EJECUCIÓN
# ============================================================================
if __name__ == "__main__":
    print("=" * 70)
    print("DFS + NETWORKX - AGRUPACIÓN DE SEGMENTOS DE ~1KM EN RED ELÉCTRICA")
    print("=" * 70)
    
    # Parsear argumentos
    args = parse_arguments()
    input_dir = args.input_dir
    output_dir = args.output_dir
    
    # Validar y crear directorios
    if not os.path.exists(input_dir):
        print(f"⚠️  El directorio de entrada '{input_dir}' no existe. Será creado.")
        os.makedirs(input_dir, exist_ok=True)
    
    if not os.access(input_dir, os.R_OK):
        print(f"❌ Error: El directorio de entrada '{input_dir}' no es legible.")
        exit(1)
    
    # Crear directorio de salida si no existe
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"\n⚙️  CONFIGURACIÓN:")
    print(f"   • Directorio de entrada: {input_dir}")
    print(f"   • Directorio de salida: {output_dir}")
    
    # Ejecutar proceso principal
    result = main(input_dir, output_dir)
    
    # Exit with appropriate code
    if result and result.get('success'):
        exit(0)
    else:
        exit(1)