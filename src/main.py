from src.controllers.manager import Manager

from src.controllers.strategies.q_nodes import QNodes


def iniciar():
    """Punto de entrada principal"""
    #                ABCDE #
    estado_inicio = "1000"
    condiciones =   "1110"
    alcance =       "1110"
    mecanismo =     "1110"

    config_sistema = Manager(estado_inicial=estado_inicio)

    ## Ejemplo de solución mediante módulo de fuerza bruta ###
    analizador_fb = QNodes(config_sistema)
    sia_uno = analizador_fb.aplicar_estrategia(condiciones, alcance, mecanismo)
    print(sia_uno)
