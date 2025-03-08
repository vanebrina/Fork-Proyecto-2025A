from src.controllers.strategies.phi import Phi
from src.controllers.strategies.q_nodes import QNodes
from src.controllers.manager import Manager

from src.controllers.strategies.force import BruteForce


def iniciar():
    """Punto de entrada principal"""
                    # ABCDEF #
    estado_inicial = "100000"
    condiciones =    "111111"
    alcance =        "111111"
    mecanismo =      "111111"

    gestor_sistema = Manager(estado_inicial)

    ### Ejemplo de solución mediante módulo de fuerza bruta ###
    analizador_fb = QNodes(gestor_sistema)
    sia_uno = analizador_fb.aplicar_estrategia(
        condiciones,
        alcance,
        mecanismo,
    )
    print(sia_uno)
