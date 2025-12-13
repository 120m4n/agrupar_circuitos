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

print("=" * 70)
print("DFS + NETWORKX - AGRUPACIÓN DE SEGMENTOS DE ~1KM EN RED ELÉCTRICA")
print("=" * 70)

# ============================================================================
# 1. CARGAR DATOS DESDE CSV
# ============================================================================
print("\n📥 PASO 1: CARGANDO DATOS DESDE ARCHIVOS CSV...")

# Leer segmentos (aristas)
try:
    df_segmentos = pd.read_csv('segmentos_circuito.csv')
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
    df_nodos = pd.read_csv('nodos_circuito.csv')
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
print(f"• Número de derivaciones: {len(df_nodos[df_nodos['tipo'] == 'Derivacion'])}")

# ============================================================================
# 2. CONSTRUIR GRAFO CON NETWORKX
# ============================================================================
print("\n\n🔗 PASO 2: CONSTRUYENDO GRAFO CON NETWORKX...")

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
    
    def dfs_por_ramas(self, longitud_objetivo_m: float = 1000.0) -> Dict:
        """
        DFS que procesa cada rama por separado (para redes ramificadas)
        """
        nodo_inicio = self.encontrar_subestacion_principal()
        
        # Encontrar todas las ramas (caminos desde la subestación a transformadores)
        transformadores = [n for n, attr in self.G.nodes(data=True) 
                          if attr['tipo'] == 'Transformador']
        
        grupos_por_rama = {}
        
        for tf in transformadores:
            try:
                # Encontrar camino desde subestación a transformador
                camino = nx.shortest_path(self.G, nodo_inicio, tf, weight='longitud_m')
                
                # Obtener segmentos en este camino
                segmentos_camino = []
                for i in range(len(camino)-1):
                    segmento_data = self.G.get_edge_data(camino[i], camino[i+1])
                    segmentos_camino.append({
                        'segmento_id': segmento_data['id_segmento'],
                        'longitud_m': segmento_data['longitud_m'],
                        'nodo_inicio': camino[i],
                        'nodo_fin': camino[i+1]
                    })
                
                # Agrupar segmentos del camino en tramos de ~1km
                grupos_rama = self._agrupar_camino(segmentos_camino, longitud_objetivo_m)
                grupos_por_rama[tf] = grupos_rama
                
                print(f"\n   Rama hacia transformador {tf}:")
                print(f"   Camino: {len(camino)} nodos, "
                      f"{sum(s['longitud_m'] for s in segmentos_camino)/1000:.2f}km")
                print(f"   Grupos formados: {len(grupos_rama)}")
                
            except nx.NetworkXNoPath:
                print(f"   ⚠️  No hay camino al transformador {tf}")
        
        return grupos_por_rama
    
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
    
    def analizar_resultados(self):
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
        self.exportar_resultados_csv()
    
    def exportar_resultados_csv(self):
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
        df_grupos.to_csv('grupos_1km.csv', index=False)
        
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
        df_segmentos_grupo.to_csv('segmentos_con_grupo.csv', index=False)
        
        print(f"\n💾 RESULTADOS EXPORTADOS:")
        print(f"   • grupos_1km.csv: {len(df_grupos)} grupos")
        print(f"   • segmentos_con_grupo.csv: {len(df_segmentos_grupo)} segmentos")

# ============================================================================
# 3. EJECUCIÓN PRINCIPAL
# ============================================================================
def main():
    """Función principal de ejecución"""
    
    # Crear instancia de la red eléctrica
    red = RedElectrica()
    
    # 1. Cargar datos
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
        tolerancia_km=0.2  # ±200m
    )
    
    # Opción 2: DFS por ramas (descomentar para usar)
    # print("\n" + "=" * 70)
    # print("🌳 AGRUPANDO POR RAMAS (DFS POR CAMINOS)")
    # print("=" * 70)
    # grupos_por_rama = red.dfs_por_ramas(longitud_objetivo_m=1000.0)
    
    # 3. Analizar resultados
    red.analizar_resultados()
    
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
    gdf.to_file('segmentos_con_grupos.geojson', driver='GeoJSON')
    gdf.to_file('segmentos_con_grupos.gpkg', driver='GPKG')
    
    print(f"✅ GeoJSON exportado: 'segmentos_con_grupos.geojson'")
    print(f"✅ GeoPackage exportado: 'segmentos_con_grupos.gpkg'")
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
    4. 💾 Archivos generados:
       • grupos_1km.csv
       • segmentos_con_grupo.csv  
       • segmentos_con_grupos.geojson
       • segmentos_con_grupos.gpkg
    
    Siguientes pasos sugeridos:
    • Importa el GeoJSON o GeoPackage a QGIS/ArcGIS
    • Usa el campo 'grupo_id' para simbología
    • Calcula estadísticas por grupo en tu GIS
    """)

# ============================================================================
# 4. FUNCIONES ADICIONALES PARA ANÁLISIS AVANZADO
# ============================================================================
def analisis_avanzado(red: RedElectrica):
    """Funciones adicionales para análisis avanzado"""
    
    print("\n" + "=" * 70)
    print("🧠 ANÁLISIS AVANZADO CON NETWORKX")
    print("=" * 70)
    
    # 1. Encontrar todos los caminos desde subestación a transformadores
    subestacion = red.encontrar_subestacion_principal()
    transformadores = [n for n, attr in red.G.nodes(data=True) 
                      if attr['tipo'] == 'Transformador']
    
    print(f"\n🔍 CAMINOS DESDE SUBESTACIÓN {subestacion}:")
    for tf in transformadores:
        try:
            caminos = list(nx.all_simple_paths(red.G, subestacion, tf, cutoff=10))
            print(f"   → Transformador {tf}: {len(caminos)} caminos posibles")
            
            # Camino más corto
            camino_corto = nx.shortest_path(red.G, subestacion, tf, weight='longitud_m')
            longitud = sum(
                red.G[u][v]['longitud_m'] 
                for u, v in zip(camino_corto[:-1], camino_corto[1:])
            )
            print(f"     Camino más corto: {len(camino_corto)} nodos, {longitud/1000:.2f}km")
            
        except nx.NetworkXNoPath:
            print(f"   → Transformador {tf}: Sin camino")
    
    # 2. Calcular centralidad de intermediación (betweenness)
    print(f"\n📊 CENTRALIDAD DE INTERMEDIACIÓN:")
    betweenness = nx.betweenness_centrality(red.G, weight='longitud_m')
    
    # Top 5 nodos más críticos
    top_criticos = sorted(betweenness.items(), key=lambda x: x[1], reverse=True)[:5]
    for nodo, valor in top_criticos:
        nombre = red.G.nodes[nodo]['nombre']
        tipo = red.G.nodes[nodo]['tipo']
        print(f"   Nodo {nodo} ({nombre}, {tipo}): {valor:.4f}")
    
    # 3. Detectar ciclos en la red
    ciclos = list(nx.cycle_basis(red.G))
    print(f"\n🔄 CICLOS EN LA RED: {len(ciclos)} ciclos detectados")
    if ciclos:
        for i, ciclo in enumerate(ciclos[:3]):  # Mostrar solo primeros 3
            print(f"   Ciclo {i+1}: {ciclo} ({len(ciclo)} nodos)")
    
    # 4. Análisis de robustez
    print(f"\n💪 ANÁLISIS DE ROBUSTEZ:")
    
    # Nodos críticos (de corte)
    nodos_corte = list(nx.articulation_points(red.G))
    print(f"   Nodos de corte (articulación): {len(nodos_corte)}")
    if nodos_corte:
        for nodo in list(nodos_corte)[:5]:
            nombre = red.G.nodes[nodo]['nombre']
            print(f"     • Nodo {nodo}: {nombre}")
    
    # Puentes (aristas críticas)
    puentes = list(nx.bridges(red.G))
    print(f"   Puentes (segmentos críticos): {len(puentes)}")
    if puentes:
        for u, v in list(puentes)[:5]:
            longitud = red.G[u][v]['longitud_m']
            print(f"     • Segmento {u}-{v}: {longitud}m")

# ============================================================================
# EJECUCIÓN
# ============================================================================
if __name__ == "__main__":
    main()
    
    # Para análisis avanzado, descomentar:
    # red = RedElectrica()
    # red.cargar_datos(df_segmentos, df_nodos)
    # analisis_avanzado(red)