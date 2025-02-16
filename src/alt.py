import time

from src.middlewares.slogger import SafeLogger
from testing.funcs import cargar_resultados_existentes, guardar_resultados

from src.testing.data import (
    NUM_NODOS,
    PRUEBAS,
    RED_15,
)
from src.constants.models import (
    QNODES_STRAREGY_TAG,
)

from src.controllers.manager import Manager
from src.controllers.strategies.phi import Phi


def iniciar():
    """Punto de entrada principal"""
    red_usada = RED_15
    muestras: list[list[tuple[str, str]]] = red_usada[PRUEBAS]
    num_nodos: int = red_usada[NUM_NODOS]

    estado_inicio = f"1{'0' * (num_nodos - 1)}"
    condiciones = "1" * num_nodos

    config_sistema = Manager(estado_inicial=estado_inicio)
    soluciones = cargar_resultados_existentes()  # Cargar resultados previos

    logger = SafeLogger(QNODES_STRAREGY_TAG)
    for lote in muestras:
        for prueba in lote:
            if prueba in soluciones:
                continue  # Si ya está guardado, lo saltamos

            alcance, mecanismo = prueba
            analizador_q = Phi(config_sistema)

            inicio_tiempo = time.time()
            solucion = analizador_q.aplicar_estrategia(condiciones, alcance, mecanismo)
            tiempo_ejecucion = time.time() - inicio_tiempo

            soluciones[prueba] = (
                solucion.perdida,
                tiempo_ejecucion,
            )  # Guardar en memoria

            # Guardar inmediatamente para minimizar pérdida en caso de crash
            guardar_resultados(soluciones)
        # break  # Eliminarlo cuando estés listo para ejecutar todo

    logger.debug(f"{soluciones=}")
