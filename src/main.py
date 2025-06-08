# main.py


from src.controllers.manager import Manager
from src.controllers.strategies.geometric import Geometric
from src.controllers.strategies.phi import Phi
from src.models.base.application import aplicacion
from src.controllers.strategies.q_nodes import QNodes
from src.controllers.strategies.q_nodes_modificate import QNodesMod


def iniciar_n6():
    """
    Ejemplo con n = 6 bits (N = 64 estados), para ver en consola todos los prints
    de progreso sin demorar más de ~1 segundo.
    """
    # 6 bits → "bitstrings" de longitud 6
    estado_inicio = "100000"  
    condiciones   = "111111"  # Condiciones iniciales (todos los bits activos)
    alcance       = "101010"
    mecanismo     = "010101"


    config = Manager(estado_inicial=estado_inicio)
    geom   = QNodes(config)
    print("\n▶︎Ejecutando Geometric en modo 'verbose' con n = 6 (64 estados)...\n")
    solucion = geom.aplicar_estrategia(condiciones, alcance, mecanismo)
    print("\n▶︎Solución obtenida:")
    print(solucion)

    geom2   = Geometric(config)
    print("\n▶︎Ejecutando Geometric en modo 'verbose' con n = 6 (64 estados)...\n")
    solucion2 = geom2.aplicar_estrategia(condiciones, alcance, mecanismo)
    print("\n▶︎Solución obtenida:")
    print(solucion2)


def generar_red_20A():
    # Configurar valores necesarios en la aplicación (si no están definidos)
    aplicacion.pagina_sample_network = "A"
    aplicacion.semilla_numpy = 42  # Puedes cambiarla si necesitas resultados distintos


    estado_inicial = "0" * 20  # Estado inicial de 20 bits


    # Crear instancia del manejador
    manager = Manager(estado_inicial=estado_inicial)


    # Forzar generación sin interacción y sin preguntar por reemplazo
    filename = manager.generar_red(dimensiones=20, datos_discretos=True)


    print(f"✅ Red generada: {filename}")


if __name__ == "__main__":
    # generar_red_20A()
    iniciar_n6()
