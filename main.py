#!/usr/bin/env python3
"""
Main Integration Script - Agrupar Circuitos
============================================

Este script integra los módulos oracle_export.py y agrupar_circuitos.py
para ejecutar el pipeline completo:

1. Exportar datos desde Oracle a CSV
2. Agrupar segmentos de circuitos en tramos de ~1km

Este script está diseñado para funcionar ÚNICAMENTE en modo standalone.
NO debe ser importado como librería.

Autor: Roman Sarmiento
Fecha: 2025-12-14
Versión: 1.0
"""

import sys
import os
import argparse
import logging
from typing import Dict, Any

# Importar los módulos como librerías
try:
    import oracle_export
    import agrupar_circuitos
except ImportError as e:
    print(f"❌ Error al importar módulos: {e}")
    print("Asegúrate de que oracle_export.py y agrupar_circuitos.py están en el mismo directorio")
    sys.exit(1)


def setup_logging(verbose: bool = False) -> None:
    """
    Configura el sistema de logging para el script principal.
    
    Args:
        verbose: Si True, muestra logs de nivel DEBUG
    """
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='[%(levelname)s] %(message)s'
    )


def validate_circuito(circuito: str) -> bool:
    """
    Valida que el código del circuito tenga un formato válido.
    
    Args:
        circuito: Código del circuito a validar
        
    Returns:
        True si el circuito es válido
    """
    if not circuito or len(circuito.strip()) == 0:
        return False
    return True


def main_pipeline(
    circuito: str,
    config_file: str = "Connect.ini",
    output_dir: str = "./data",
    skip_oracle: bool = False,
    verbose: bool = False
) -> Dict[str, Any]:
    """
    Pipeline completo: Oracle Export → Agrupación de Circuitos.
    
    Args:
        circuito: Código del circuito a procesar (requerido)
        config_file: Ruta al archivo de configuración de Oracle
        output_dir: Directorio de salida para archivos CSV y resultados
        skip_oracle: Si True, salta la exportación de Oracle (usa CSV existentes)
        verbose: Si True, muestra información detallada
        
    Returns:
        Dict con resultados del pipeline completo:
        {
            'success': bool,
            'oracle_export': dict,
            'agrupacion': dict,
            'error': str (optional)
        }
    """
    result = {
        'success': False,
        'oracle_export': {},
        'agrupacion': {},
        'error': None
    }
    
    print("=" * 70)
    print("PIPELINE DE AGRUPACIÓN DE CIRCUITOS ELÉCTRICOS")
    print("=" * 70)
    print(f"Circuito: {circuito}")
    print(f"Directorio de salida: {output_dir}")
    print("=" * 70)
    
    try:
        # Crear directorio de salida si no existe
        os.makedirs(output_dir, exist_ok=True)
        
        # PASO 1: Exportar desde Oracle (si no se omite)
        if not skip_oracle:
            print("\n" + "=" * 70)
            print("PASO 1: EXPORTACIÓN DESDE ORACLE")
            print("=" * 70)
            
            try:
                # Modificar temporalmente la configuración de salida
                config = oracle_export.read_config(config_file)
                config['OUTPUT']['output_dir'] = output_dir
                config['OUTPUT']['node_csv'] = 'nodos_circuito.csv'
                config['OUTPUT']['segment_csv'] = 'segmentos_circuito.csv'
                
                # Ejecutar exportación
                export_result = oracle_export.oracle_to_csv_pipeline(config_file, circuito)
                result['oracle_export'] = export_result
                
                if not export_result['success']:
                    raise Exception(f"Error en exportación Oracle: {export_result['errors']}")
                
                print(f"\n✅ Exportación Oracle completada exitosamente")
                print(f"   • Nodos: {export_result['stats']['nodes_count']}")
                print(f"   • Segmentos: {export_result['stats']['lines_count']}")
                
            except FileNotFoundError:
                print(f"\n⚠️  Archivo de configuración '{config_file}' no encontrado")
                print(f"    Continuando con archivos CSV existentes en {output_dir}")
                result['oracle_export'] = {'skipped': True, 'reason': 'config_not_found'}
            except Exception as e:
                error_msg = str(e)
                if 'oracledb no está instalado' in error_msg:
                    print(f"\n⚠️  Oracle DB no disponible: {error_msg}")
                    print(f"    Continuando con archivos CSV existentes en {output_dir}")
                    result['oracle_export'] = {'skipped': True, 'reason': 'oracle_not_available'}
                else:
                    raise
        else:
            print("\n⚠️  Exportación Oracle omitida (--skip-oracle)")
            print(f"   Usando archivos CSV existentes en {output_dir}")
            result['oracle_export'] = {'skipped': True, 'reason': 'user_requested'}
        
        # PASO 2: Agrupar circuitos
        print("\n" + "=" * 70)
        print("PASO 2: AGRUPACIÓN DE CIRCUITOS")
        print("=" * 70)
        
        # Ejecutar agrupación usando el módulo como librería
        agrupacion_result = agrupar_circuitos.main(
            input_dir=output_dir,
            output_dir=output_dir
        )
        result['agrupacion'] = agrupacion_result
        
        if not agrupacion_result['success']:
            raise Exception(f"Error en agrupación: {agrupacion_result.get('error', 'Unknown error')}")
        
        print(f"\n✅ Agrupación completada exitosamente")
        print(f"   • Grupos generados: {agrupacion_result['stats']['num_grupos']}")
        print(f"   • Segmentos procesados: {agrupacion_result['stats']['num_segmentos']}")
        print(f"   • Nodos procesados: {agrupacion_result['stats']['num_nodos']}")
        
        # PASO 3: Resumen final
        print("\n" + "=" * 70)
        print("✅ PIPELINE COMPLETADO EXITOSAMENTE")
        print("=" * 70)
        print(f"\nResumen:")
        print(f"  • Circuito procesado: {circuito}")
        print(f"  • Directorio de salida: {output_dir}")
        
        if not result['oracle_export'].get('skipped'):
            print(f"\n  Exportación Oracle:")
            if 'stats' in result['oracle_export']:
                print(f"    - Nodos exportados: {result['oracle_export']['stats']['nodes_count']}")
                print(f"    - Segmentos exportados: {result['oracle_export']['stats']['lines_count']}")
        
        print(f"\n  Agrupación de circuitos:")
        print(f"    - Grupos de ~1km creados: {agrupacion_result['stats']['num_grupos']}")
        print(f"    - Segmentos agrupados: {agrupacion_result['stats']['num_segmentos']}")
        
        print(f"\n  Archivos generados en '{output_dir}':")
        if 'files' in agrupacion_result:
            for file_type, file_path in agrupacion_result['files'].items():
                print(f"    - {file_type}: {os.path.basename(file_path)}")
        
        print("\n" + "=" * 70)
        
        result['success'] = True
        
    except Exception as e:
        result['error'] = str(e)
        print(f"\n❌ ERROR EN PIPELINE: {str(e)}")
        logging.error(f"Error en pipeline: {e}", exc_info=verbose)
    
    return result


def main():
    """
    Función principal para ejecución standalone.
    
    Este script NO debe ser importado como librería.
    Usar oracle_export.py y agrupar_circuitos.py directamente como librerías.
    """
    # Detectar si el script está siendo importado
    if __name__ != "__main__":
        raise RuntimeError(
            "main.py está diseñado para ejecutarse ÚNICAMENTE en modo standalone.\n"
            "No debe ser importado como librería.\n"
            "Para uso programático, importar oracle_export.py y agrupar_circuitos.py directamente."
        )
    
    # Configurar argumentos CLI
    parser = argparse.ArgumentParser(
        description='Pipeline completo de exportación Oracle y agrupación de circuitos eléctricos',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  # Ejecutar pipeline completo desde Oracle
  python main.py --circuito "12 0m4n"
  
  # Usar archivos CSV existentes (omitir Oracle)
  python main.py --circuito "12 0m4n" --skip-oracle
  
  # Especificar directorio de salida personalizado
  python main.py --circuito "MT-001" --output-dir ./resultados
  
  # Usar archivo de configuración personalizado
  python main.py --circuito "12 0m4n" --config /ruta/config.ini
  
  # Modo verboso para debugging
  python main.py --circuito "12 0m4n" --verbose

Nota: Este script integra oracle_export.py y agrupar_circuitos.py.
      Ambos módulos también pueden ejecutarse independientemente.
        """
    )
    
    parser.add_argument(
        '--circuito',
        type=str,
        required=True,
        help='Código del circuito a procesar (REQUERIDO)'
    )
    
    parser.add_argument(
        '--config',
        type=str,
        default='Connect.ini',
        help='Ruta al archivo de configuración Oracle (default: Connect.ini)'
    )
    
    parser.add_argument(
        '--output-dir',
        type=str,
        default='./data',
        help='Directorio de salida para archivos CSV y resultados (default: ./data)'
    )
    
    parser.add_argument(
        '--skip-oracle',
        action='store_true',
        help='Omitir exportación desde Oracle (usar CSV existentes)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Modo verboso (mostrar información detallada)'
    )
    
    args = parser.parse_args()
    
    # Configurar logging
    setup_logging(args.verbose)
    
    # Validar circuito
    if not validate_circuito(args.circuito):
        print("❌ ERROR: El parámetro --circuito es requerido y no puede estar vacío")
        parser.print_help()
        sys.exit(1)
    
    # Ejecutar pipeline
    try:
        result = main_pipeline(
            circuito=args.circuito,
            config_file=args.config,
            output_dir=args.output_dir,
            skip_oracle=args.skip_oracle,
            verbose=args.verbose
        )
        
        # Exit con código apropiado
        if result['success']:
            sys.exit(0)
        else:
            sys.exit(1)
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Proceso interrumpido por el usuario")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ ERROR FATAL: {str(e)}")
        logging.error(f"Error fatal: {e}", exc_info=args.verbose)
        sys.exit(1)


if __name__ == "__main__":
    main()
