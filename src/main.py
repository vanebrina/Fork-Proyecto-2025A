from src.controllers.manager import Manager

from src.controllers.strategies.force import BruteForce


def iniciar():
    """Punto de entrada principal"""
                    # ABCD #
    estado_inicial = "100"
    condiciones =    "111"
    alcance =        "111"
    mecanismo =      "111"

    gestor_sistema = Manager(estado_inicial)

    ### Ejemplo de solución mediante módulo de fuerza bruta ###
    analizador_fb = BruteForce(gestor_sistema)
    # sia_uno = analizador_fb.aplicar_estrategia(condiciones, alcance, mecanismo)
    sia_uno = analizador_fb.analizar_completamente_una_red()
    # print(sia_uno)
