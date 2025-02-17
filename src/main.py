from src.middlewares.slogger import SafeLogger
from src.controllers.strategies.phi import Phi
from src.controllers.strategies.q_nodes import QNodes
from src.controllers.manager import Manager

from src.controllers.strategies.force import BruteForce


def iniciar():
    """Punto de entrada principal"""
    # ABCD #
    estado_inicial = "1000"
    condiciones = "1110"
    alcance = "1110"
    mecanismo = "1110"

    gestor_sistema = Manager(estado_inicial)

    logger = SafeLogger("test")

    ### Ejemplo de solución mediante módulo oficial de Pyphi ###
    analizador_fb = Phi(gestor_sistema)
    sia_uno = analizador_fb.aplicar_estrategia(condiciones, alcance, mecanismo)
    logger.critic(sia_uno)

    ### Ejemplo de solución mediante módulo de fuerza bruta ###
    analizador_fb = BruteForce(gestor_sistema)
    sia_uno = analizador_fb.aplicar_estrategia(condiciones, alcance, mecanismo)
    logger.critic(sia_uno)

    analizador_fb = QNodes(gestor_sistema)
    sia_uno = analizador_fb.aplicar_estrategia(condiciones, alcance, mecanismo)
    logger.critic(sia_uno)
