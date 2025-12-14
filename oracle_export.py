#!/usr/bin/env python3
"""
Módulo de Exportación desde Oracle para Agrupar Circuitos
==========================================================

Este módulo genera archivos CSV desde una base de datos Oracle,
compatibles con el formato esperado por agrupar_circuitos.py.

Para documentación completa, ver: oracle_export_documentation.md

Autor: Roman Sarmiento
Fecha: 2025-12-13
Versión: 1.0
"""

import sys
import os
import time
import logging
import argparse
import configparser
import tempfile
import re
from typing import Dict, Tuple, Any, Union, List, Generator
from contextlib import contextmanager
from logging.handlers import RotatingFileHandler

# Import pandas
import pandas as pd

# Try to import oracledb, but allow module to load without it
try:
    import oracledb as cx_Oracle
    from oracledb import Connection as OracleConnection
    ORACLE_AVAILABLE = True
except ImportError:
    ORACLE_AVAILABLE = False
    cx_Oracle = None
    OracleConnection = Any  # Fallback type for when cx_Oracle is not available


class OracleExportError(Exception):
    """Excepción base para el módulo"""
    pass


class ConfigurationError(OracleExportError):
    """Error en configuración"""
    pass


class OracleConnectionError(OracleExportError):
    """Error de conexión a Oracle"""
    pass


class PackageExecutionError(OracleExportError):
    """Error al ejecutar package"""
    pass


class DataExtractionError(OracleExportError):
    """Error al extraer datos"""
    pass


class DataValidationError(OracleExportError):
    """Error de validación de datos"""
    pass


class CSVWriteError(OracleExportError):
    """Error al escribir CSV"""
    pass


# ============================================================================
# FUNCIONES PÚBLICAS
# ============================================================================

def export_from_oracle(
    config_file: str = "Connect.ini",
    circuito: str = None,
    return_dataframes: bool = False
) -> Union[Dict[str, str], Tuple[pd.DataFrame, pd.DataFrame]]:
    """
    Función pública principal para exportación desde Oracle.
    
    Args:
        config_file: Ruta al archivo de configuración
        circuito: Código del circuito a procesar (requerido)
        return_dataframes: Si True, retorna DataFrames en lugar de rutas
        
    Returns:
        Si return_dataframes=False:
            Dict con rutas de archivos: {'nodes': path, 'lines': path}
        Si return_dataframes=True:
            Tupla (df_nodos, df_segmentos)
            
    Example:
        # Generar archivos CSV
        files = export_from_oracle('Connect.ini', '12 0m4n')
        print(f"Archivos generados: {files}")
        
        # Obtener DataFrames directamente
        df_nodos, df_segmentos = export_from_oracle(
            'Connect.ini', '12 0m4n', 
            return_dataframes=True
        )
    """
    if not circuito:
        raise ValueError("El parámetro 'circuito' es requerido")
    
    result = oracle_to_csv_pipeline(config_file, circuito)
    
    if not result['success']:
        raise OracleExportError(f"Error en pipeline: {result['errors']}")
    
    if return_dataframes:
        # Read the generated CSV files and return DataFrames
        df_nodos = pd.read_csv(result['files']['nodes'])
        df_segmentos = pd.read_csv(result['files']['lines'])
        return df_nodos, df_segmentos
    else:
        return result['files']


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def sanitize_identifier(identifier: str) -> str:
    """
    Sanitiza identificadores SQL (nombres de tablas, esquemas, packages) 
    para prevenir SQL injection.
    
    Args:
        identifier: Nombre de tabla, esquema o package
        
    Returns:
        Identificador sanitizado
        
    Raises:
        ValueError: Si el identificador contiene caracteres no válidos
    """
    if not identifier:
        raise ValueError("El identificador no puede estar vacío")
    
    # Oracle identifiers can contain letters, numbers, underscore, $, #
    # and must start with a letter
    if not re.match(r'^[A-Za-z][A-Za-z0-9_$#]*$', identifier):
        raise ValueError(
            f"Identificador SQL inválido: {identifier}. "
            f"Solo se permiten letras, números, _, $, # y debe iniciar con letra"
        )
    
    # Limit length (Oracle max is 30 chars for most identifiers)
    if len(identifier) > 30:
        raise ValueError(f"Identificador demasiado largo (max 30 caracteres): {identifier}")
    
    return identifier


# ============================================================================
# MÓDULO 1: CONFIGURACIÓN
# ============================================================================

def read_config(config_file: str = "Connect.ini") -> Dict[str, Any]:
    """
    Lee y valida el archivo de configuración.
    
    Args:
        config_file: Ruta al archivo de configuración
        
    Returns:
        Diccionario con configuración validada
        
    Raises:
        FileNotFoundError: Si el archivo no existe
        ConfigurationError: Si faltan parámetros obligatorios
    """
    if not os.path.exists(config_file):
        raise FileNotFoundError(
            f"Archivo de configuración no encontrado: {config_file}\n"
            f"Cree el archivo a partir de Connect.ini.example"
        )
    
    config_parser = configparser.ConfigParser()
    config_parser.read(config_file)
    
    # Convert to nested dictionary
    config = {}
    for section in config_parser.sections():
        config[section] = dict(config_parser[section])
    
    # Convert types for specific fields
    if 'ORACLE' in config:
        if 'port' in config['ORACLE']:
            config['ORACLE']['port'] = int(config['ORACLE']['port'])
        if 'connection_timeout' in config['ORACLE']:
            config['ORACLE']['connection_timeout'] = int(config['ORACLE']['connection_timeout'])
    
    if 'OUTPUT' in config:
        if 'overwrite' in config['OUTPUT']:
            config['OUTPUT']['overwrite'] = config['OUTPUT']['overwrite'].lower() == 'true'
    
    if 'ADVANCED' in config:
        if 'chunk_size' in config['ADVANCED']:
            config['ADVANCED']['chunk_size'] = int(config['ADVANCED']['chunk_size'])
        if 'max_retries' in config['ADVANCED']:
            config['ADVANCED']['max_retries'] = int(config['ADVANCED']['max_retries'])
        if 'retry_delay' in config['ADVANCED']:
            config['ADVANCED']['retry_delay'] = int(config['ADVANCED']['retry_delay'])
        if 'debug_mode' in config['ADVANCED']:
            config['ADVANCED']['debug_mode'] = config['ADVANCED']['debug_mode'].lower() == 'true'
    
    return config


def validate_config(config: Dict[str, Any]) -> bool:
    """
    Valida que todos los parámetros obligatorios estén presentes.
    
    Args:
        config: Diccionario de configuración
        
    Returns:
        True si la configuración es válida
        
    Raises:
        ConfigurationError: Si hay errores en la configuración
    """
    # Required sections
    required_sections = ['ORACLE', 'DATABASE', 'OUTPUT']
    for section in required_sections:
        if section not in config:
            raise ConfigurationError(f"Falta la sección [{section}] en la configuración")
    
    # Required Oracle parameters
    oracle_required = ['host', 'port', 'service_name', 'username']
    for param in oracle_required:
        if param not in config['ORACLE'] or not config['ORACLE'][param]:
            raise ConfigurationError(f"Falta el parámetro obligatorio: ORACLE.{param}")
    
    # Either password or wallet must be provided
    has_password = 'password' in config['ORACLE'] and config['ORACLE']['password']
    has_wallet = 'wallet_location' in config['ORACLE'] and config['ORACLE']['wallet_location']
    
    if not has_password and not has_wallet:
        raise ConfigurationError(
            "Se requiere 'password' o 'wallet_location' en la sección [ORACLE]"
        )
    
    # Required Database parameters
    db_required = ['package_name', 'node_table', 'line_table']
    for param in db_required:
        if param not in config['DATABASE'] or not config['DATABASE'][param]:
            raise ConfigurationError(f"Falta el parámetro obligatorio: DATABASE.{param}")
    
    # Required Output parameters
    output_required = ['output_dir', 'node_csv', 'segment_csv']
    for param in output_required:
        if param not in config['OUTPUT'] or not config['OUTPUT'][param]:
            raise ConfigurationError(f"Falta el parámetro obligatorio: OUTPUT.{param}")
    
    return True


# ============================================================================
# MÓDULO 2: CONEXIÓN ORACLE
# ============================================================================

def create_connection(config: Dict[str, Any]) -> OracleConnection:
    """
    Establece conexión con la base de datos Oracle.
    
    Args:
        config: Diccionario con parámetros de conexión
        
    Returns:
        Objeto de conexión Oracle
        
    Raises:
        OracleConnectionError: Si falla la conexión
    """
    if not ORACLE_AVAILABLE:
        raise OracleConnectionError(
            "oracledb no está instalado. Instalar con: pip install oracledb\n"
            "Para conexiones básicas no requiere Oracle Instant Client."
        )
    
    oracle_config = config['ORACLE']
    
    try:

        cx_Oracle.init_oracle_client(lib_dir=oracle_config.get('instant_client_path'))
        # Build DSN
        
        dsn = cx_Oracle.makedsn(
            oracle_config['host'],
            oracle_config['port'],
            service_name=oracle_config['service_name']
        )
        
        # Connect
        if 'password' in oracle_config and oracle_config['password']:
            # Connect with username/password
            conn = cx_Oracle.connect(
                user=oracle_config['username'],
                password=oracle_config['password'],
                dsn=dsn
            )
        elif 'wallet_location' in oracle_config and oracle_config['wallet_location']:
            # Connect with wallet
            conn = cx_Oracle.connect(
                user=oracle_config['username'],
                dsn=dsn,
                wallet_location=oracle_config['wallet_location']
            )
        else:
            raise ConfigurationError("No se proporcionó password ni wallet_location")
        
        logging.info(f"[OK] Conexión establecida a {oracle_config['host']}:{oracle_config['port']}/{oracle_config['service_name']}")
        return conn
        
    except cx_Oracle.Error as e:
        # Safely extract error message
        if e.args and len(e.args) > 0:
            error_msg = str(e.args[0]) if hasattr(e.args[0], '__str__') else str(e)
        else:
            error_msg = str(e)
        raise OracleConnectionError(f"Error al conectar a Oracle: {error_msg}")


def test_connection(conn: OracleConnection) -> bool:
    """
    Verifica que la conexión esté activa.
    
    Args:
        conn: Conexión a Oracle
        
    Returns:
        True si la conexión es exitosa
    """
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM DUAL")
        cursor.fetchone()
        cursor.close()
        return True
    except cx_Oracle.Error:
        return False


def close_connection(conn: OracleConnection) -> None:
    """
    Cierra la conexión de forma segura.
    
    Args:
        conn: Conexión a cerrar
    """
    try:
        if conn:
            conn.close()
            logging.info("[OK] Conexión cerrada")
    except cx_Oracle.Error as e:
        logging.warning(f"Error al cerrar conexión: {e}")


@contextmanager
def oracle_connection(config: Dict[str, Any]) -> Generator[OracleConnection, None, None]:
    """
    Context manager para gestión automática de conexión.
    
    Uso:
        with oracle_connection(config) as conn:
            # Usar conexión
            pass
    """
    conn = None
    try:
        conn = create_connection(config)
        yield conn
    finally:
        if conn:
            close_connection(conn)


# ============================================================================
# MÓDULO 3: EJECUCIÓN DE PACKAGE
# ============================================================================

def execute_package(
    conn: OracleConnection,
    package_name: str,
    circuito: str,
    schema: str = None
) -> bool:
    """
    Ejecuta el procedimiento Oracle especificado.
    
    Args:
        conn: Conexión activa a Oracle
        package_name: Nombre del package (ej. "AGRUPAR_CIRCUITOS")
        circuito: Código del circuito a procesar
        schema: Esquema donde está el package (opcional)
        
    Returns:
        True si la ejecución fue exitosa
        
    Raises:
        PackageExecutionError: Si falla la ejecución del procedimiento
        
    Notas:
        - El procedimiento debe existir en la base de datos
        - Debe tener los permisos necesarios para ejecutarlo
        - Se ejecuta como CALL schema.package.procedure(circuito)
    """
    try:
        cursor = conn.cursor()
        
        # Sanitize identifiers to prevent SQL injection
        # Note: Procedure names cannot be parameterized in SQL, so we use sanitize_identifier()
        # which validates against strict regex pattern to prevent injection
        safe_package = sanitize_identifier(package_name)
        
        # Build qualified name with procedure
        if schema:
            safe_schema = sanitize_identifier(schema)
            qualified_name = f"{safe_schema}.{safe_package}.PROCESAR"
        else:
            qualified_name = f"{safe_package}.PROCESAR"
        
        # Execute procedure using CALL syntax
        # Using f-string is safe here because qualified_name has been sanitized
        # sql = f"CALL {qualified_name}();"
        
        logging.info(f"Ejecutando procedimiento: {qualified_name}('{circuito}')")
        cursor.callproc(qualified_name, [circuito])
        conn.commit()
        cursor.close()
        
        logging.info(f"[OK] Procedimiento ejecutado exitosamente")
        return True
        
    except cx_Oracle.Error as e:
        # Safely extract error message
        if e.args and len(e.args) > 0:
            error_msg = str(e.args[0]) if hasattr(e.args[0], '__str__') else str(e)
        else:
            error_msg = str(e)
        
        # Check for specific Oracle errors and provide concise messages
        if "ORA-20002" in error_msg:
            raise PackageExecutionError("Código de circuito no válido")
        elif "ORA-06553" in error_msg or "PLS-306" in error_msg:
            raise PackageExecutionError("Número o tipos de argumentos erróneos al llamar al procedimiento")
        else:
            raise PackageExecutionError(f"Error al ejecutar procedimiento {qualified_name}: {error_msg}")


def check_package_exists(
    conn: OracleConnection,
    package_name: str,
    schema: str = None
) -> bool:
    """
    Verifica si el package existe en la base de datos.
    
    Args:
        conn: Conexión activa a Oracle
        package_name: Nombre del package
        schema: Esquema del package
        
    Returns:
        True si el package existe
    """
    try:
        cursor = conn.cursor()
        
        # Use parameterized queries - already safe from SQL injection
        if schema:
            sql = """
                SELECT COUNT(*) 
                FROM all_objects 
                WHERE owner = :schema 
                  AND object_name = :package_name 
                  AND object_type = 'PACKAGE'
            """
            # Fix: use dictionary or tuple, not mixed
            cursor.execute(sql, {'schema': schema.upper(), 'package_name': package_name.upper()})
        else:
            sql = """
                SELECT COUNT(*) 
                FROM user_objects 
                WHERE object_name = :package_name 
                  AND object_type = 'PACKAGE'
            """
            cursor.execute(sql, {'package_name': package_name.upper()})
        
        count = cursor.fetchone()[0]
        cursor.close()
        
        return count > 0
        
    except cx_Oracle.Error:
        return False


# ============================================================================
# MÓDULO 4: EXTRACCIÓN DE DATOS
# ============================================================================

def extract_nodes(
    conn: OracleConnection,
    table_name: str = "HIT_NODE",
    schema: str = None
) -> pd.DataFrame:
    """
    Extrae datos de nodos desde Oracle.
    
    Args:
        conn: Conexión activa a Oracle
        table_name: Nombre de la tabla de nodos
        schema: Esquema de la tabla
        
    Returns:
        DataFrame con columnas: id_nodo, nombre, tipo, voltaje_kv, x, y
        
    Raises:
        DataExtractionError: Si falla la consulta
    """
    try:
        # Sanitize identifiers to prevent SQL injection
        # Note: Table names cannot be parameterized in SQL, so we use sanitize_identifier()
        # which validates against a strict regex pattern to prevent injection
        safe_table = sanitize_identifier(table_name)
        
        if schema:
            safe_schema = sanitize_identifier(schema)
            qualified_name = f"{safe_schema}.{safe_table}"
        else:
            qualified_name = safe_table
        
        # Query - using generic column names as per documentation
        # These mappings should be adjusted based on actual Oracle schema
        # Using f-string is safe here because qualified_name has been sanitized
        sql = f"""
            SELECT
                hn.ABB_INT_ID AS id_nodo,
                hn.NNAME AS nombre,
                hn.tipo AS tipo,
                hn.TENSION voltaje_kv,
                hn.LON x,
                hn.LAT y
            FROM {qualified_name} hn
            ORDER BY hn.ABB_INT_ID
        """
        
        logging.info(f"Extrayendo datos de tabla {qualified_name}...")
        df = pd.read_sql(sql, conn)
        # Ensure column names are lowercase for compatibility with agrupar_circuitos.py
        df.columns = df.columns.str.lower()
        logging.info(f"[OK] {len(df)} nodos extraídos")
        
        return df
        
    except Exception as e:
        raise DataExtractionError(f"Error al extraer nodos: {e}")


def extract_lines(
    conn: OracleConnection,
    table_name: str = "HIT_LINE",
    schema: str = None
) -> pd.DataFrame:
    """
    Extrae datos de líneas/segmentos desde Oracle.
    
    Args:
        conn: Conexión activa a Oracle
        table_name: Nombre de la tabla de líneas
        schema: Esquema de la tabla
        
    Returns:
        DataFrame con columnas: id_segmento, id_circuito, nodo_inicio, 
                               nodo_fin, longitud_m, tipo_conductor, capacidad_amp
        
    Raises:
        DataExtractionError: Si falla la consulta
    """
    try:
        # Sanitize identifiers to prevent SQL injection
        # Note: Table names cannot be parameterized in SQL, so we use sanitize_identifier()
        # which validates against a strict regex pattern to prevent injection
        safe_table = sanitize_identifier(table_name)
        
        if schema:
            safe_schema = sanitize_identifier(schema)
            qualified_name = f"{safe_schema}.{safe_table}"
        else:
            qualified_name = safe_table
        
        # Query - using generic column names as per documentation
        # These mappings should be adjusted based on actual Oracle schema
        # Using f-string is safe here because qualified_name has been sanitized
        sql = f"""
            SELECT
                hl.ABB_INT_ID AS id_segmento,
                '12 0m4n' AS id_circuito,
                hl.NO_KEY_1 AS nodo_inicio,
                hl.NO_KEY_2 AS nodo_fin,
                hl."LENGTH" AS longitud_m,
                hl.TIPO_CONDUCTOR AS tipo_conductor,
                hl.CAPACIDAD_AMP AS capacidad_amp
            FROM {qualified_name} hl
            JOIN HIT_NODE hn ON hn.ABB_INT_ID = hl.NO_KEY_1
            JOIN HIT_NODE hn2 ON hn2.ABB_INT_ID = hl.NO_KEY_2 
            ORDER BY hl.ABB_INT_ID
        """
        
        logging.info(f"Extrayendo datos de tabla {qualified_name}...")
        df = pd.read_sql(sql, conn)
        # Ensure column names are lowercase for compatibility with agrupar_circuitos.py
        df.columns = df.columns.str.lower()
        logging.info(f"[OK] {len(df)} segmentos extraídos")
        
        return df
        
    except Exception as e:
        raise DataExtractionError(f"Error al extraer líneas: {e}")


def extract_data(
    conn: OracleConnection,
    config: Dict[str, Any]
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Extrae ambas tablas (nodos y líneas).
    
    Args:
        conn: Conexión activa a Oracle
        config: Configuración con nombres de tablas
        
    Returns:
        Tupla (df_nodos, df_segmentos)
    """
    db_config = config['DATABASE']
    schema = db_config.get('schema')
    
    df_nodes = extract_nodes(conn, db_config['node_table'], schema)
    df_lines = extract_lines(conn, db_config['line_table'], schema)
    
    return df_nodes, df_lines


# ============================================================================
# MÓDULO 5: TRANSFORMACIÓN DE DATOS
# ============================================================================

def transform_nodes(df_raw: pd.DataFrame) -> pd.DataFrame:
    """
    Transforma DataFrame de nodos al formato esperado.
    
    Transformaciones:
    - Renombrar columnas si es necesario
    - Convertir tipos de datos
    - Validar campos obligatorios
    - Limpiar valores nulos o inválidos
    
    Args:
        df_raw: DataFrame con datos crudos de Oracle
        
    Returns:
        DataFrame transformado con formato correcto
        
    Raises:
        DataValidationError: Si hay datos inválidos
    """
    df = df_raw.copy()
    
    # Validate required columns
    required_columns = ['id_nodo', 'nombre', 'tipo', 'voltaje_kv', 'x', 'y']
    for col in required_columns:
        if col not in df.columns:
            raise DataValidationError(f"Falta la columna requerida: {col}")
    
    # Convert data types
    df['id_nodo'] = df['id_nodo'].astype(str)  # Ensure consistent string type
    df['voltaje_kv'] = pd.to_numeric(df['voltaje_kv'], errors='coerce')
    df['x'] = pd.to_numeric(df['x'], errors='coerce')
    df['y'] = pd.to_numeric(df['y'], errors='coerce')
    
    # Check for nulls in required fields
    if df['id_nodo'].isna().any():
        raise DataValidationError("Hay valores nulos en id_nodo")
    
    # Remove rows with invalid data
    initial_count = len(df)
    df = df.dropna(subset=['nombre', 'tipo', 'voltaje_kv', 'x', 'y'])
    
    if len(df) < initial_count:
        logging.warning(f"Se eliminaron {initial_count - len(df)} nodos con datos inválidos")
    
    # Validate voltaje_kv is positive
    if (df['voltaje_kv'] <= 0).any():
        raise DataValidationError("Hay valores no positivos en voltaje_kv")
    
    logging.info("[OK] Nodos transformados y validados")
    return df


def transform_lines(df_raw: pd.DataFrame) -> pd.DataFrame:
    """
    Transforma DataFrame de líneas al formato esperado.
    
    Transformaciones:
    - Renombrar columnas si es necesario
    - Convertir tipos de datos
    - Validar campos obligatorios
    - Asegurar integridad referencial con nodos
    
    Args:
        df_raw: DataFrame con datos crudos de Oracle
        
    Returns:
        DataFrame transformado con formato correcto
        
    Raises:
        DataValidationError: Si hay datos inválidos
    """
    df = df_raw.copy()
    
    # Validate required columns
    required_columns = ['id_segmento', 'id_circuito', 'nodo_inicio', 'nodo_fin', 
                       'longitud_m', 'tipo_conductor', 'capacidad_amp']
    for col in required_columns:
        if col not in df.columns:
            raise DataValidationError(f"Falta la columna requerida: {col}")
    
    # Convert data types - handle NaN values before int conversion
    # First convert id_segmento safely
    df['id_segmento'] = pd.to_numeric(df['id_segmento'], errors='coerce')
    if df['id_segmento'].isna().any():
        logging.warning("Hay valores NaN en id_segmento, se eliminarán esas filas")
        df = df.dropna(subset=['id_segmento'])
    df['id_segmento'] = df['id_segmento'].astype(int)
    
    df['nodo_inicio'] = df['nodo_inicio'].astype(str)  # Consistent with nodes
    df['nodo_fin'] = df['nodo_fin'].astype(str)
    df['longitud_m'] = pd.to_numeric(df['longitud_m'], errors='coerce')
    
    # Handle NaN values in capacidad_amp before converting to int
    df['capacidad_amp'] = pd.to_numeric(df['capacidad_amp'], errors='coerce')
    if df['capacidad_amp'].isna().any():
        logging.warning("Hay valores NaN en capacidad_amp, se eliminarán esas filas")
        df = df.dropna(subset=['capacidad_amp'])
    df['capacidad_amp'] = df['capacidad_amp'].astype(int)
    
    # Check for nulls in required fields
    if df[['id_segmento', 'id_circuito', 'nodo_inicio', 'nodo_fin']].isna().any().any():
        raise DataValidationError("Hay valores nulos en campos obligatorios de segmentos")
    
    # Remove self-loops
    self_loops = df['nodo_inicio'] == df['nodo_fin']
    if self_loops.any():
        logging.warning(f"Se eliminaron {self_loops.sum()} segmentos con self-loops")
        df = df[~self_loops]
    
    # Validate longitud_m is positive
    if (df['longitud_m'] <= 0).any():
        raise DataValidationError("Hay valores no positivos en longitud_m")
    
    # Check for unrealistic values
    if (df['longitud_m'] > 10000).any():
        logging.warning("Hay segmentos con longitud > 10 km")
    
    logging.info("[OK] Líneas transformadas y validadas")
    return df


def validate_data_integrity(
    df_nodes: pd.DataFrame,
    df_lines: pd.DataFrame
) -> Tuple[bool, List[str]]:
    """
    Valida integridad referencial entre nodos y líneas.
    
    Validaciones:
    - Todos los nodos referenciados en líneas existen
    - No hay duplicados en id_nodo o id_segmento
    - Campos obligatorios no nulos
    - Tipos de datos correctos
    - Valores en rangos válidos (ej. longitud_m > 0)
    
    Args:
        df_nodes: DataFrame de nodos
        df_lines: DataFrame de líneas
        
    Returns:
        Tupla (es_valido, lista_de_errores)
    """
    errors = []
    
    # Check for duplicate IDs in nodes
    if df_nodes['id_nodo'].duplicated().any():
        duplicate_count = df_nodes['id_nodo'].duplicated().sum()
        errors.append(f"Hay {duplicate_count} IDs de nodo duplicados")
    
    # Check for duplicate IDs in lines
    if df_lines['id_segmento'].duplicated().any():
        duplicate_count = df_lines['id_segmento'].duplicated().sum()
        errors.append(f"Hay {duplicate_count} IDs de segmento duplicados")
    
    # Check referential integrity
    node_ids = set(df_nodes['id_nodo'].astype(str))
    inicio_ids = set(df_lines['nodo_inicio'].astype(str))
    fin_ids = set(df_lines['nodo_fin'].astype(str))
    
    missing_inicio = inicio_ids - node_ids
    if missing_inicio:
        errors.append(f"Hay {len(missing_inicio)} nodos de inicio que no existen en la tabla de nodos")
    
    missing_fin = fin_ids - node_ids
    if missing_fin:
        errors.append(f"Hay {len(missing_fin)} nodos de fin que no existen en la tabla de nodos")
    
    # Log validation results
    if errors:
        for error in errors:
            logging.error(f"Error de validación: {error}")
        return False, errors
    else:
        logging.info("[OK] Validación de integridad exitosa")
        return True, []


# ============================================================================
# MÓDULO 6: GENERACIÓN DE CSV
# ============================================================================

def write_csv(
    df: pd.DataFrame,
    filename: str,
    output_dir: str = "./",
    encoding: str = "utf-8"
) -> str:
    """
    Escribe DataFrame a archivo CSV.
    
    Args:
        df: DataFrame a exportar
        filename: Nombre del archivo CSV
        output_dir: Directorio de salida
        encoding: Codificación del archivo
        
    Returns:
        Ruta completa del archivo generado
        
    Raises:
        CSVWriteError: Si falla la escritura
    """
    try:
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Build full path
        filepath = os.path.join(output_dir, filename)
        
        # Write CSV
        df.to_csv(filepath, index=False, encoding=encoding)
        
        logging.info(f"[OK] {filename} generado ({len(df)} registros)")
        return filepath
        
    except Exception as e:
        raise CSVWriteError(f"Error al escribir CSV {filename}: {e}")


def generate_csv_files(
    df_nodes: pd.DataFrame,
    df_lines: pd.DataFrame,
    config: Dict[str, Any]
) -> Dict[str, str]:
    """
    Genera ambos archivos CSV.
    
    Args:
        df_nodes: DataFrame de nodos
        df_lines: DataFrame de líneas
        config: Configuración con rutas de salida
        
    Returns:
        Diccionario con rutas de archivos generados:
        {'nodes': 'ruta/nodos_circuito.csv', 
         'lines': 'ruta/segmentos_circuito.csv'}
    """
    output_config = config['OUTPUT']
    
    output_dir = output_config.get('output_dir', './')
    encoding = output_config.get('encoding', 'utf-8')
    
    # Check if files exist and overwrite flag
    overwrite = output_config.get('overwrite', True)
    
    node_file = os.path.join(output_dir, output_config['node_csv'])
    segment_file = os.path.join(output_dir, output_config['segment_csv'])
    
    if not overwrite:
        if os.path.exists(node_file):
            raise CSVWriteError(f"El archivo {node_file} ya existe y overwrite=false")
        if os.path.exists(segment_file):
            raise CSVWriteError(f"El archivo {segment_file} ya existe y overwrite=false")
    
    # Write files
    nodes_path = write_csv(df_nodes, output_config['node_csv'], output_dir, encoding)
    lines_path = write_csv(df_lines, output_config['segment_csv'], output_dir, encoding)
    
    return {
        'nodes': nodes_path,
        'lines': lines_path
    }


def verify_csv_format(csv_file: str, expected_columns: List[str]) -> bool:
    """
    Verifica que el CSV generado tenga el formato correcto.
    
    Args:
        csv_file: Ruta al archivo CSV
        expected_columns: Lista de columnas esperadas
        
    Returns:
        True si el formato es correcto
    """
    try:
        df = pd.read_csv(csv_file, nrows=1)
        actual_columns = list(df.columns)
        
        # Check if all expected columns are present
        missing = set(expected_columns) - set(actual_columns)
        if missing:
            logging.error(f"Faltan columnas en {csv_file}: {missing}")
            return False
        
        return True
        
    except Exception as e:
        logging.error(f"Error al verificar formato de {csv_file}: {e}")
        return False


# ============================================================================
# LOGGING SETUP
# ============================================================================

def setup_logging(log_level: str = "INFO", log_file: str = "oracle_export.log"):
    """
    Configura el sistema de logging.
    
    - Logs a archivo con rotación (max 10MB, 5 backups)
    - Logs a consola con formato legible
    - Niveles: DEBUG, INFO, WARNING, ERROR, CRITICAL
    """
    # Clear existing handlers
    logger = logging.getLogger()
    logger.handlers = []
    
    # Set level
    logger.setLevel(logging.DEBUG)
    
    # Formato
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_formatter = logging.Formatter(
        '[%(levelname)s] %(message)s'
    )
    
    # Handler de archivo con rotación
    file_handler = RotatingFileHandler(
        log_file, maxBytes=10*1024*1024, backupCount=5
    )
    file_handler.setFormatter(file_formatter)
    file_handler.setLevel(logging.DEBUG)
    logger.addHandler(file_handler)
    
    # Handler de consola
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(getattr(logging, log_level.upper()))
    logger.addHandler(console_handler)


# ============================================================================
# PIPELINE PRINCIPAL
# ============================================================================

def oracle_to_csv_pipeline(config_file: str = "Connect.ini", circuito: str = None) -> Dict[str, Any]:
    """
    Pipeline completo de extracción Oracle → CSV.
    
    Este es el flujo principal que coordina todos los módulos.
    
    Args:
        config_file: Ruta al archivo de configuración
        circuito: Código del circuito a procesar
        
    Returns:
        Diccionario con resultados:
        {
            'success': bool,
            'files': {'nodes': path, 'lines': path},
            'stats': {
                'nodes_count': int,
                'lines_count': int,
                'execution_time': float
            },
            'errors': List[str]
        }
        
    Flujo:
        1. Leer configuración
        2. Conectar a Oracle
        3. Ejecutar procedimiento AGRUPAR_CIRCUITOS.PROCESAR(circuito)
        4. Extraer datos de HIT_NODE y HIT_LINE
        5. Transformar y validar datos
        6. Generar archivos CSV
        7. Cerrar conexión
    """
    start_time = time.time()
    result = {
        'success': False,
        'files': {},
        'stats': {},
        'errors': []
    }
    
    try:
        logging.info("=" * 70)
        logging.info("INICIANDO EXPORTACIÓN DESDE ORACLE")
        logging.info("=" * 70)
        
        # 1. Configuración
        logging.info(f"Leyendo configuración desde {config_file}")
        config = read_config(config_file)
        validate_config(config)
        logging.info("[OK] Configuración validada")
        
        # Setup logging from config
        if 'LOGGING' in config:
            log_level = config['LOGGING'].get('log_level', 'INFO')
            log_file = config['LOGGING'].get('log_file', 'oracle_export.log')
            setup_logging(log_level, log_file)
        
        # 2. Conexión
        logging.info("Conectando a Oracle...")
        with oracle_connection(config) as conn:
            
            # Test connection
            if not test_connection(conn):
                raise OracleConnectionError("La conexión no está activa")
            
            # 3. Ejecutar procedimiento
            db_config = config['DATABASE']
            if db_config.get('package_name'):
                execute_package(
                    conn, 
                    db_config['package_name'], 
                    circuito,
                    db_config.get('schema')
                )
            
            # 4. Extraer datos
            logging.info("Extrayendo datos de Oracle...")
            df_nodes_raw, df_lines_raw = extract_data(conn, config)
            
        # Connection is now closed (context manager)
        
        # 5. Transformar y validar
        logging.info("Transformando y validando datos...")
        df_nodes = transform_nodes(df_nodes_raw)
        df_lines = transform_lines(df_lines_raw)
        
        is_valid, errors = validate_data_integrity(df_nodes, df_lines)
        if not is_valid:
            result['errors'].extend(errors)
            raise DataValidationError(f"Errores de validación: {errors}")
        
        # 6. Generar CSV
        logging.info("Generando archivos CSV...")
        files = generate_csv_files(df_nodes, df_lines, config)
        
        # 7. Verificar formato
        expected_node_cols = ['id_nodo', 'nombre', 'tipo', 'voltaje_kv', 'x', 'y']
        expected_line_cols = ['id_segmento', 'id_circuito', 'nodo_inicio', 'nodo_fin', 
                             'longitud_m', 'tipo_conductor', 'capacidad_amp']
        
        if not verify_csv_format(files['nodes'], expected_node_cols):
            raise CSVWriteError("El formato del CSV de nodos no es correcto")
        if not verify_csv_format(files['lines'], expected_line_cols):
            raise CSVWriteError("El formato del CSV de segmentos no es correcto")
        
        # Success
        result['success'] = True
        result['files'] = files
        result['stats'] = {
            'nodes_count': len(df_nodes),
            'lines_count': len(df_lines),
            'execution_time': time.time() - start_time
        }
        
        logging.info("=" * 70)
        logging.info("PROCESO COMPLETADO EXITOSAMENTE")
        logging.info(f"Nodos: {result['stats']['nodes_count']}")
        logging.info(f"Segmentos: {result['stats']['lines_count']}")
        logging.info(f"Tiempo: {result['stats']['execution_time']:.2f}s")
        logging.info("=" * 70)
        
    except Exception as e:
        raise OracleExportError(str(e))
    
    return result


# ============================================================================
# CLI - EJECUCIÓN STANDALONE
# ============================================================================

def main():
    """
    Función principal para ejecución standalone.
    
    Argumentos CLI:
        --config: Ruta al archivo Connect.ini (default: "./Connect.ini")
        --circuito: Código del circuito a procesar (requerido)
        --output-dir: Directorio para archivos CSV (default: "./")
        --verbose: Modo verboso de logging
        --dry-run: Simular ejecución sin escribir archivos
        --skip-package: No ejecutar package Oracle
    """
    parser = argparse.ArgumentParser(
        description='Exportación CSV desde Base de Datos Oracle',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  python oracle_export.py --circuito "12 0m4n"
  python oracle_export.py --config /ruta/a/config.ini --circuito "15 501"
  python oracle_export.py --config Connect.ini --circuito "12 0m4n" --verbose
  python oracle_export.py --output-dir ./data --circuito "12 0m4n" --skip-procedure

Para más información, consultar oracle_export_documentation.md
        """
    )
    
    parser.add_argument(
        '--config',
        type=str,
        default='Connect.ini',
        help='Ruta al archivo de configuración (default: Connect.ini)'
    )
    
    parser.add_argument(
        '--circuito',
        type=str,
        required=True,
        help='Código del circuito a procesar (requerido)'
    )
    
    parser.add_argument(
        '--output-dir',
        type=str,
        help='Directorio de salida para archivos CSV (sobrescribe config)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Modo verboso de logging'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Simular ejecución sin escribir archivos (no implementado)'
    )
    
    parser.add_argument(
        '--skip-procedure',
        action='store_true',
        help='No ejecutar procedimiento Oracle'
    )
    
    args = parser.parse_args()
    
    # Setup basic logging
    log_level = 'DEBUG' if args.verbose else 'INFO'
    setup_logging(log_level)
    
    try:
        # Check if cx_Oracle is available
        if not ORACLE_AVAILABLE:
            logging.error("=" * 70)
            logging.error("ERROR: oracledb no está instalado")
            logging.error("=" * 70)
            logging.error("")
            logging.error("Para usar este módulo, debe instalar oracledb:")
            logging.error("  pip install oracledb")
            logging.error("")
            logging.error("Para modo thick requiere Oracle Instant Client instalado:")
            logging.error("  https://www.oracle.com/database/technologies/instant-client.html")
            logging.error("")
            sys.exit(1)
        
        # Check if config file exists
        if not os.path.exists(args.config):
            logging.error(f"Archivo de configuración no encontrado: {args.config}")
            logging.error("")
            logging.error("Cree el archivo a partir de Connect.ini.example:")
            logging.error(f"  cp Connect.ini.example {args.config}")
            logging.error(f"  # Editar {args.config} con sus credenciales")
            logging.error("")
            sys.exit(1)
        
        # Read and modify config if needed
        temp_config_file = None

        if args.output_dir or args.skip_procedure:
            config = read_config(args.config)
            
            if args.output_dir:
                if 'OUTPUT' not in config:
                    config['OUTPUT'] = {}
                config['OUTPUT']['output_dir'] = args.output_dir
            
            if args.skip_procedure:
                if 'DATABASE' in config:
                    config['DATABASE']['package_name'] = ''
            
            # Write temporary config
            with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as f:
                temp_config_file = f.name
                config_parser = configparser.ConfigParser()
                for section, values in config.items():
                    config_parser[section] = {}
                    # Convert all values to strings for ConfigParser
                    for key, value in values.items():
                        config_parser[section][key] = str(value)
                config_parser.write(f)
            
            config_file = temp_config_file
        else:
            config_file = args.config
        
        # Run pipeline
        result = oracle_to_csv_pipeline(config_file, args.circuito)
        
        # Success
        sys.exit(0)
            
    except KeyboardInterrupt:
        logging.info("\nProceso interrumpido por el usuario")
        sys.exit(130)
    except Exception as e:
        logging.error(f"El proceso falló: {e}", exc_info=args.verbose)
        sys.exit(1)
    finally:
        # Cleanup temp config in finally block to ensure cleanup even on error
        if 'temp_config_file' in locals() and temp_config_file and os.path.exists(temp_config_file):
            try:
                os.unlink(temp_config_file)
            except Exception as e:
                logging.warning(f"No se pudo eliminar archivo temporal: {e}")


if __name__ == "__main__":
    main()
