from src.controllers.manager import Manager
from src.models.strategies.force import BruteForce


def iniciar():
    """Punto de entrada principal"""
    #                ABCD #
    estado_inicio = "100000000000000"
    condiciones =   "111111111111111"
    alcance =       "101010101010101"
    mecanismo =     "111111111111111"

    config_sistema = Manager(estado_inicial=estado_inicio)

    print(f'{config_sistema.pagina=}')

    ### Ejemplo de solución mediante módulo de fuerza bruta ###
    analizador_fb = BruteForce(config_sistema)
    sia_uno = analizador_fb.aplicar_estrategia(condiciones, alcance, mecanismo)
    print(sia_uno)
