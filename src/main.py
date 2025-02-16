from src.controllers.manager import Manager

from src.controllers.strategies.force import BruteForce


def iniciar():
    """Punto de entrada principal"""
<<<<<<< HEAD
                   # ABCD #
    estado_inicio = "1000"
    condiciones =   "1111"
    alcance =       "1111"
    mecanismo =     "1111"
=======
                    # ABCD #
    estado_inicial = "1000"
    condiciones =    "1110"
    alcance =        "1110"
    mecanismo =      "1110"
>>>>>>> 32c873b3fdb7bec96c89605e78c9201e79623712

    gestor_sistema = Manager(estado_inicial)

    ### Ejemplo de solución mediante módulo de fuerza bruta ###
    analizador_fb = BruteForce(gestor_sistema)
    sia_uno = analizador_fb.aplicar_estrategia(condiciones, alcance, mecanismo)
    print(sia_uno)
