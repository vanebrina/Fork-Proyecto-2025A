import time
import numpy as np
from src.funcs.base import ABECEDARY, lil_endian
from src.funcs.format import fmt_biparticion
from src.controllers.manager import Manager

import math

import pyphi
from pyphi import Network, Subsystem
from pyphi.labels import NodeLabels
from pyphi.models.cuts import Bipartition, Part

from src.middlewares.slogger import SafeLogger
from src.middlewares.observer import DebugObserver
from src.middlewares.profile import profiler_manager, profile

from src.models.base.sia import SIA
from src.models.core.solution import Solution
from src.models.enums.distance import MetricDistance
from src.models.base.application import aplicacion


from src.constants.base import (
    STR_ONE,
)
from src.constants.models import (
    DUMMY_ARR,
    DUMMY_PARTITION,
)


class Phi(SIA):
    """Class Phi is used as base for other strategies, bruteforce with pyphi."""

    def __init__(self, config: Manager) -> None:
        super().__init__(config)
        profiler_manager.start_session(
            f"NET{len(config.estado_inicial)}{config.pagina}"
        )
        self.logger = SafeLogger("phi_analysis")
        self.debug_observer = DebugObserver()

    # @profile(context={TYPE_TAG: "pyphi_analysis"})
    def aplicar_estrategia(self, condiciones: str, alcance: str, mecanismo: str):
        self.sia_tiempo_inicio = time.time()
        estado_inicial = tuple(int(s) for s in self.sia_loader.estado_inicial)
        longitud = len(estado_inicial)

        indices = tuple(range(longitud))
        etiquetas = tuple(ABECEDARY[:longitud])

        completo = NodeLabels(etiquetas, indices)
        mpt_estados_nodos_on = self.sia_cargar_tpm()
        red = Network(tpm=mpt_estados_nodos_on, node_labels=completo)

        candidato = tuple(
            completo[i] for i, bit in enumerate(condiciones) if bit == STR_ONE
        )
        subsistema = Subsystem(network=red, state=estado_inicial, nodes=candidato)
        alcance = tuple(
            ind
            for ind, (bit, cond) in enumerate(zip(alcance, condiciones))
            if (bit == STR_ONE) and (cond == STR_ONE)
        )
        mecanismo = tuple(
            ind
            for ind, (bit, cond) in enumerate(zip(mecanismo, condiciones))
            if (bit == STR_ONE) and (cond == STR_ONE)
        )

        mip = (
            subsistema.effect_mip(mecanismo, alcance)
            if aplicacion.distancia_metrica == MetricDistance.EMD_EFECTO.value
            else subsistema.cause_mip(mecanismo, alcance)
        )
        small_phi: float = mip.phi

        repertorio = repertorio_partido = DUMMY_ARR
        format = DUMMY_PARTITION

        if mip.repertoire is not None:
            repertorio = mip.repertoire.flatten()
            repertorio_partido = mip.partitioned_repertoire.flatten()

            states = int(math.log2(mip.repertoire.size))
            sub_estados: np.ndarray = lil_endian(states)

            repertorio.put(sub_estados, repertorio)
            repertorio_partido.put(sub_estados, repertorio_partido)

            mejor_biparticion: Bipartition = mip.partition
            prim: Part = mejor_biparticion.parts[True]
            dual: Part = mejor_biparticion.parts[False]

            prim_mech, prim_purv = prim.mechanism, prim.purview
            dual_mech, dual_purv = dual.mechanism, dual.purview
            format = fmt_biparticion(
                [dual_mech, dual_purv],
                [prim_mech, prim_purv],
            )

        return Solution(
            estrategia="Pyphi",
            perdida=small_phi,
            distribucion_subsistema=repertorio,
            distribucion_particion=repertorio_partido,
            tiempo_total=time.time() - self.sia_tiempo_inicio,
            particion=format,
        )
