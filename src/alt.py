from src.middlewares.slogger import SafeLogger

from src.testing.data import (
    NUM_NODOS,
    PRUEBAS,
    RED_05,
    RED_10,
    RED_15,
)
from src.constants.models import (
    QNODES_STRAREGY_TAG,
)

from src.controllers.manager import Manager
from src.controllers.strategies.phi import Phi

# En tu función principal:
from src.testing.result import GestorResultados  # Ajusta la ruta según tu estructura


def iniciar():
    """Punto de entrada principal"""
    red_usada = RED_10
    reactor = GestorResultados()  # Creamos una instancia del gestor

    muestras: list[list[tuple[str, str]]] = red_usada[PRUEBAS]
    num_nodos: int = red_usada[NUM_NODOS]

    estado_inicio = f"1{'0' * (num_nodos - 1)}"
    condiciones = "1" * num_nodos

    config_sistema = Manager(estado_inicial=estado_inicio)
    logger = SafeLogger(QNODES_STRAREGY_TAG)

    for lote in muestras:
        for prueba in lote:
            # Verificamos si ya existe el resultado
            if reactor.obtener_resultado(*prueba):
                continue

            logger.error(f"\n{prueba=}")
            alcance, mecanismo = prueba
            analizador_q = Phi(config_sistema)

            solucion = analizador_q.aplicar_estrategia(
                condiciones,
                alcance,
                mecanismo,
            )

            # Guardamos el resultado
            reactor.guardar_resultado(
                alcance=alcance,
                mecanismo=mecanismo,
                perdida=solucion.perdida,
                tiempo=solucion.tiempo_ejecucion,
            )
            break
        break


# def iniciar():
#     """Punto de entrada principal"""
#     red_usada = RED_05

#     muestras: list[list[tuple[str, str]]] = red_usada[PRUEBAS]
#     num_nodos: int = red_usada[NUM_NODOS]

#     estado_inicio = f"1{'0' * (num_nodos - 1)}"
#     condiciones = "1" * num_nodos

#     config_sistema = Manager(estado_inicial=estado_inicio)
#     # Cargar resultados previos
#     soluciones = cargar_resultados_existentes()

#     logger = SafeLogger(QNODES_STRAREGY_TAG)
#     for lote in muestras:
#         for prueba in lote:
#             if prueba in soluciones.keys():
#                 # Si ya está guardado, saltamos
#                 continue
#             logger.error(f"\n{prueba=}")

#             alcance, mecanismo = prueba
#             analizador_q = Phi(config_sistema)

#             solucion = analizador_q.aplicar_estrategia(
#                 condiciones,
#                 alcance,
#                 mecanismo,
#             )

#             # Guardar en memoria
#             soluciones[prueba] = (
#                 solucion.perdida,
#                 solucion.tiempo_ejecucion,
#             )
#             # Guardar inmediatamente para minimizar pérdida en caso de crash
#             guardar_resultados(soluciones)
#             # break  # Eliminar cuando esté listo
#         break  # Eliminar cuando esté listo
