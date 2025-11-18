import unittest
import requests
import concurrent.futures
import time
import random
import string

class TestRegistroProductoCarga(unittest.TestCase):
    """
    Pruebas de carga para el servicio de registro de producto
    """
    
    BASE_URL = "http://127.0.0.1:5002/producto_routes"  # Ajusta según tu configuración
    ENDPOINT_REGISTRO = f"{BASE_URL}/registro_producto"
    
    @staticmethod
    def generar_producto_aleatorio(id_vendedor):
        """Genera datos aleatorios para un producto único"""
        random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        return {
            "nombre": f"Producto_{random_suffix}",
            "descripcion": f"Descripcion del producto {random_suffix}",
            "precio": round(random.uniform(10.00, 500.00), 2),
            "cantidad": random.randint(1, 100),
            "tipo": random.choice([1, 2]),
            "material": f"{random.randint(1, 5)},{random.randint(1, 5)}",
            "url_foto": f"https://ejemplo.com/foto_{random_suffix}.jpg",
            "id_vendedor": id_vendedor
        }
    
    @staticmethod
    def registrar_producto_individual(url, datos_producto, numero_intento):
        """Registra un producto individual y retorna el resultado"""
        try:
            inicio = time.time()
            respuesta = requests.post(url, json=datos_producto, timeout=10)
            tiempo_respuesta = time.time() - inicio
            
            return {
                "intento": numero_intento,
                "status_code": respuesta.status_code,
                "tiempo_respuesta": tiempo_respuesta,
                "respuesta": respuesta.json(),
                "exito": respuesta.status_code == 201,
                "error": None
            }
        except Exception as e:
            tiempo_respuesta = time.time() - inicio
            return {
                "intento": numero_intento,
                "status_code": None,
                "tiempo_respuesta": tiempo_respuesta,
                "respuesta": None,
                "exito": False,
                "error": str(e)
            }
    
    def simular_registros_simultaneos(self, cantidad_productos, id_vendedor=1):
        """
        Simula el registro de múltiples productos de forma simultánea
        
        Args:
            cantidad_productos (int): Cantidad de productos a registrar (1-20)
            id_vendedor (int): ID del vendedor que registra los productos
        
        Returns:
            dict: Estadísticas del test de carga
        """
        
        if not (1 <= cantidad_productos <= 20):
            raise ValueError("La cantidad de productos debe estar entre 1 y 20")
        
        print(f"\n{'='*70}")
        print(f"INICIANDO TEST DE CARGA: {cantidad_productos} productos simultáneos")
        print(f"Vendedor ID: {id_vendedor}")
        print(f"{'='*70}\n")
        
        # Generar datos para los productos
        productos = [self.generar_producto_aleatorio(id_vendedor) for _ in range(cantidad_productos)]
        
        # Ejecutar registros en paralelo
        tiempo_inicio_total = time.time()
        resultados = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=cantidad_productos) as executor:
            futures = [
                executor.submit(
                    self.registrar_producto_individual,
                    self.ENDPOINT_REGISTRO,
                    productos[i],
                    i + 1
                )
                for i in range(cantidad_productos)
            ]
            
            for future in concurrent.futures.as_completed(futures):
                resultados.append(future.result())
        
        tiempo_total = time.time() - tiempo_inicio_total
        
        # Procesar estadísticas
        exitosos = sum(1 for r in resultados if r["exito"])
        fallidos = cantidad_productos - exitosos
        tiempo_promedio = sum(r["tiempo_respuesta"] for r in resultados) / cantidad_productos
        tiempo_maximo = max(r["tiempo_respuesta"] for r in resultados)
        tiempo_minimo = min(r["tiempo_respuesta"] for r in resultados)
        
        # Mostrar resultados
        self._mostrar_resultados(
            cantidad_productos, exitosos, fallidos, 
            tiempo_total, tiempo_promedio, tiempo_maximo, 
            tiempo_minimo, resultados
        )
        
        return {
            "cantidad_productos": cantidad_productos,
            "exitosos": exitosos,
            "fallidos": fallidos,
            "tiempo_total": tiempo_total,
            "tiempo_promedio": tiempo_promedio,
            "tiempo_maximo": tiempo_maximo,
            "tiempo_minimo": tiempo_minimo,
            "resultados_detallados": resultados
        }
    
    @staticmethod
    def _mostrar_resultados(cantidad, exitosos, fallidos, tiempo_total, 
                            tiempo_promedio, tiempo_maximo, tiempo_minimo, resultados):
        """Muestra los resultados en formato legible"""
        print(f"RESUMEN DE RESULTADOS:")
        print(f"-" * 70)
        print(f"Total de intentos:        {cantidad}")
        print(f"Registros exitosos:       {exitosos} ✓")
        print(f"Registros fallidos:       {fallidos} ✗")
        print(f"Tasa de éxito:            {(exitosos/cantidad)*100:.1f}%")
        print(f"\nTIEMPOS DE RESPUESTA:")
        print(f"-" * 70)
        print(f"Tiempo total:             {tiempo_total:.3f}s")
        print(f"Tiempo promedio/producto: {tiempo_promedio:.3f}s")
        print(f"Tiempo máximo:            {tiempo_maximo:.3f}s")
        print(f"Tiempo mínimo:            {tiempo_minimo:.3f}s")
        print(f"\nDETALLES POR INTENTO:")
        print(f"-" * 70)
        
        for resultado in sorted(resultados, key=lambda x: x["intento"]):
            estado = "✓" if resultado["exito"] else "✗"
            print(f"Intento {resultado['intento']:2d}: {estado} | "
                  f"Status: {resultado['status_code'] or 'ERROR':>3} | "
                  f"Tiempo: {resultado['tiempo_respuesta']:.3f}s", end="")
            if resultado["error"]:
                print(f" | Error: {resultado['error']}")
            else:
                print()
        
        print(f"{'='*70}\n")
    
    def test_1_producto(self):
        """Test con 1 producto"""
        resultado = self.simular_registros_simultaneos(1)
        self.assertEqual(resultado["exitosos"], 1)
    
    def test_5_productos(self):
        """Test con 5 productos"""
        resultado = self.simular_registros_simultaneos(5)
        self.assertGreaterEqual(resultado["exitosos"], 4)
    
    def test_10_productos(self):
        """Test con 10 productos"""
        resultado = self.simular_registros_simultaneos(10)
        self.assertGreaterEqual(resultado["exitosos"], 8)

    def test_15_productos(self):
        """Test con 15 productos"""
        resultado = self.simular_registros_simultaneos(15)
        self.assertGreaterEqual(resultado["exitosos"], 12)
    
    def test_20_productos(self):
        """Test con 20 productos (máximo)"""
        resultado = self.simular_registros_simultaneos(20)
        self.assertGreaterEqual(resultado["exitosos"], 15)


if __name__ == "__main__":
    # Ejecutar pruebas
    unittest.main(verbosity=2)
    
    # O ejecutar directamente sin unittest:
    # test = TestRegistroProductoCarga()
    # test.simular_registros_simultaneos(10)