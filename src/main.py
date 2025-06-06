from src.controllers.manager import Manager

from src.controllers.strategies.q_nodes_modificate import QNodesMod
from src.controllers.strategies.q_nodes import QNodes
# from src.controllers.strategies.QNodes_full_sparse import QNodesFullSparse


def iniciar():
    """Punto de entrada principal"""
                    # ABCDEFGHIJKLMNOPQRST #
    estado_inicio =  "11111111111111111111"
    condiciones =    "11111111111111111111"
    alcance =        "10111111111111111111"
    mecanismo =      "10111111111111111111"

    gestor_sistema = Manager(estado_inicial=estado_inicio)
    # gestor_sistema.generar_red(dimensiones=25)
    # print("Red generada con exito")

    analizador_fn = QNodes(gestor_sistema)
    analizador_fm = QNodesMod(gestor_sistema)
    # analizador_fs = QNodesFullSparse(gestor_sistema)
    sia_uno = analizador_fn.aplicar_estrategia(condiciones, alcance, mecanismo)
    sia_dos = analizador_fm.aplicar_estrategia(condiciones, alcance, mecanismo)
    # sia_tres = analizador_fs.aplicar_estrategia(condiciones, alcance, mecanismo)

    print("SIA con QNodes")
    print(sia_uno)
    print("SIA con QNodesMod")
    print(sia_dos)
    # print("SIA con QNodesSpace")
    # print(sia_tres)