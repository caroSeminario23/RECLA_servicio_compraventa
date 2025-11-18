import unittest
import requests
import concurrent.futures
import time
import random

class TestFiltrarProductoCarga(unittest.TestCase):
    """
    Pruebas de carga para el servicio de filtrar productos
    """
    
    BASE_URL = "http://127.0.0.1:5002/producto_routes"
    ENDPOINT_FILTRAR = f"{BASE_URL}/filtrar_productos"
    
    @staticmethod
    def generar_filtro_aleatorio(id_usuario_actual):
        """Genera datos aleatorios para un filtro único"""
        return {
            "tipo": random.sample([1, 2, 3], k=random.randint(1, 2)),  # 1 o 2 tipos
            "material": ",".join(str(random.randint(1, 5)) for _ in range(random.randint(1, 3))),  # Materiales separados por coma
            "id_usuario_actual": id_usuario_actual
        }
    
    @staticmethod
    def filtrar_producto_individual(url, datos_filtro, numero_intento):
        """Realiza una búsqueda de productos individual y retorna el resultado"""
        try:
            inicio = time.time()
            respuesta = requests.post(url, json=datos_filtro, timeout=10)
            tiempo_respuesta = time.time() - inicio
            
            return {
                "intento": numero_intento,
                "status_code": respuesta.status_code,
                "tiempo_respuesta": tiempo_respuesta,
                "respuesta": respuesta.json(),
                "exito": respuesta.status_code == 200,
                "error": None,
                "productos_encontrados": len(respuesta.json().get("data", [])) if respuesta.status_code == 200 else 0
            }
        except Exception as e:
            tiempo_respuesta = time.time() - inicio
            return {
                "intento": numero_intento,
                "status_code": None,
                "tiempo_respuesta": tiempo_respuesta,
                "respuesta": None,
                "exito": False,
                "error": str(e),
                "productos_encontrados": 0
            }
    
    def simular_filtros_simultaneos(self, cantidad_usuarios, id_usuario_actual=5):
        """
        Simula el filtrado de productos por múltiples usuarios de forma simultánea
        
        Args:
            cantidad_usuarios (int): Cantidad de usuarios buscando simultáneamente (1-20)
            id_usuario_actual (int): ID del usuario actual (para excluir sus productos)
        
        Returns:
            dict: Estadísticas del test de carga
        """
        
        if not (1 <= cantidad_usuarios <= 20):
            raise ValueError("La cantidad de usuarios debe estar entre 1 y 20")
        
        print(f"\n{'='*70}")
        print(f"INICIANDO TEST DE CARGA: {cantidad_usuarios} usuarios filtrando simultáneamente")
        print(f"Usuario actual (excluido de búsqueda): {id_usuario_actual}")
        print(f"{'='*70}\n")
        
        # Generar datos para los filtros
        filtros = [self.generar_filtro_aleatorio(id_usuario_actual) for _ in range(cantidad_usuarios)]
        
        # Ejecutar filtros en paralelo
        tiempo_inicio_total = time.time()
        resultados = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=cantidad_usuarios) as executor:
            futures = [
                executor.submit(
                    self.filtrar_producto_individual,
                    self.ENDPOINT_FILTRAR,
                    filtros[i],
                    i + 1
                )
                for i in range(cantidad_usuarios)
            ]
            
            for future in concurrent.futures.as_completed(futures):
                resultados.append(future.result())
        
        tiempo_total = time.time() - tiempo_inicio_total
        
        # Procesar estadísticas
        exitosos = sum(1 for r in resultados if r["exito"])
        fallidos = cantidad_usuarios - exitosos
        tiempo_promedio = sum(r["tiempo_respuesta"] for r in resultados) / cantidad_usuarios
        tiempo_maximo = max(r["tiempo_respuesta"] for r in resultados)
        tiempo_minimo = min(r["tiempo_respuesta"] for r in resultados)
        productos_promedio = sum(r["productos_encontrados"] for r in resultados) / cantidad_usuarios
        
        # Mostrar resultados
        self._mostrar_resultados(
            cantidad_usuarios, exitosos, fallidos, 
            tiempo_total, tiempo_promedio, tiempo_maximo, 
            tiempo_minimo, productos_promedio, resultados
        )
        
        return {
            "cantidad_usuarios": cantidad_usuarios,
            "exitosos": exitosos,
            "fallidos": fallidos,
            "tiempo_total": tiempo_total,
            "tiempo_promedio": tiempo_promedio,
            "tiempo_maximo": tiempo_maximo,
            "tiempo_minimo": tiempo_minimo,
            "productos_promedio": productos_promedio,
            "resultados_detallados": resultados
        }
    
    @staticmethod
    def _mostrar_resultados(cantidad, exitosos, fallidos, tiempo_total, 
                            tiempo_promedio, tiempo_maximo, tiempo_minimo, 
                            productos_promedio, resultados):
        """Muestra los resultados en formato legible"""
        print(f"RESUMEN DE RESULTADOS:")
        print(f"-" * 70)
        print(f"Total de búsquedas:       {cantidad}")
        print(f"Búsquedas exitosas:       {exitosos} ✓")
        print(f"Búsquedas fallidas:       {fallidos} ✗")
        print(f"Tasa de éxito:            {(exitosos/cantidad)*100:.1f}%")
        print(f"\nTIEMPOS DE RESPUESTA:")
        print(f"-" * 70)
        print(f"Tiempo total:             {tiempo_total:.3f}s")
        print(f"Tiempo promedio/búsqueda: {tiempo_promedio:.3f}s")
        print(f"Tiempo máximo:            {tiempo_maximo:.3f}s")
        print(f"Tiempo mínimo:            {tiempo_minimo:.3f}s")
        print(f"\nRESULTADOS:")
        print(f"-" * 70)
        print(f"Productos promedio/búsqueda: {productos_promedio:.1f}")
        print(f"\nDETALLES POR INTENTO:")
        print(f"-" * 70)
        
        for resultado in sorted(resultados, key=lambda x: x["intento"]):
            estado = "✓" if resultado["exito"] else "✗"
            print(f"Intento {resultado['intento']:2d}: {estado} | "
                  f"Status: {resultado['status_code'] or 'ERROR':>3} | "
                  f"Tiempo: {resultado['tiempo_respuesta']:.3f}s | "
                  f"Productos: {resultado['productos_encontrados']:3d}", end="")
            if resultado["error"]:
                print(f" | Error: {resultado['error']}")
            else:
                print()
        
        print(f"{'='*70}\n")
    
    def test_1_usuario(self):
        """Test con 1 usuario filtrando"""
        resultado = self.simular_filtros_simultaneos(1)
        self.assertGreaterEqual(resultado["exitosos"], 1)
    
    def test_5_usuarios(self):
        """Test con 5 usuarios filtrando"""
        resultado = self.simular_filtros_simultaneos(5)
        self.assertGreaterEqual(resultado["exitosos"], 4)
    
    def test_10_usuarios(self):
        """Test con 10 usuarios filtrando"""
        resultado = self.simular_filtros_simultaneos(10)
        self.assertGreaterEqual(resultado["exitosos"], 8)

    def test_15_usuarios(self):
        """Test con 15 usuarios filtrando"""
        resultado = self.simular_filtros_simultaneos(15)
        self.assertGreaterEqual(resultado["exitosos"], 12)
    
    def test_20_usuarios(self):
        """Test con 20 usuarios filtrando (máximo)"""
        resultado = self.simular_filtros_simultaneos(20)
        self.assertGreaterEqual(resultado["exitosos"], 15)


if __name__ == "__main__":
    # Ejecutar pruebas
    unittest.main(verbosity=2)
    
    # O ejecutar directamente sin unittest:
    # test = TestFiltrarProductoCarga()
    # test.simular_filtros_simultaneos(10)