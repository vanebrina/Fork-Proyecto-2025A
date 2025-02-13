from logging import Manager
from typing import Callable

import numpy as np
import itertools as it

from src.funcs.format import fmt_biparticion
from src.models.core.solution import Solution
from src.middlewares.slogger import SafeLogger
from src.funcs.base import emd_efecto, seleccionar_metrica
from src.models.base.sia import SIA
from src.middlewares.profile import profile, profiler_manager
from src.models.base.application import aplicacion


class Branch(SIA):
    """Class Branch is used to ."""

    def __init__(self, config: Manager):
        super().__init__(config)
        profiler_manager.start_session(
            f"NET{len(config.estado_inicial)}{config.pagina}"
        )
        self.distancia_metrica: Callable = seleccionar_metrica(
            aplicacion.distancia_metrica
        )
        self.logger = SafeLogger("bruteforce_analysis")

    def aplicar_estrategia(
        self,
        condiciones: str,
        alcance: str,
        mecanismo: str,
    ):
        self.sia_preparar_subsistema(condiciones, alcance, mecanismo)
        # print(f"{self.sia_subsistema}")

        # Vamos a tomar cada una de las variables en tiempos presentes y futuros, evaluamos la bipartición generada al sacar dicha variable y al final del todo retornamos la bipartición que nos genere la menor pérdida.

        indices = self.sia_subsistema.indices_ncubos
        dimensiones = self.sia_subsistema.dims_ncubos
        empty = np.array((), dtype=np.int8)

        memoria_alcance = dict()
        memoria_mecanismo = dict()

        for ind in indices:
            subsistema_alcance = self.sia_subsistema
            particion_alcance = (
                np.array((ind,), dtype=np.int8),
                empty,
            )
            particion_act = subsistema_alcance.bipartir(*particion_alcance)
            dist_marginal = particion_act.distribucion_marginal()
            emd_alcance = emd_efecto(
                dist_marginal,
                self.sia_dists_marginales,
            )
            # memoria_alcance.append((emd_alcance, particion_alcance))
            memoria_alcance[emd_alcance] = particion_alcance

        for dim in dimensiones:
            subsistema_mecanismo = self.sia_subsistema
            particion_mecanismo = (
                empty,
                np.array((dim,), dtype=np.int8),
            )
            particion_sig = subsistema_mecanismo.bipartir(*particion_mecanismo)
            dist_marginal = particion_sig.distribucion_marginal()
            emd_alcance = emd_efecto(
                dist_marginal,
                self.sia_dists_marginales,
            )
            # memoria_mecanismo.append((emd_alcance, particion_alcance))
            memoria_mecanismo[emd_alcance] = particion_alcance

        minimo_local = min(memoria_alcance.keys() | memoria_mecanismo.keys())
        mip = (
            memoria_alcance[minimo_local]
            if minimo_local in memoria_alcance.keys()
            else memoria_mecanismo[minimo_local]
        )
        print(f"{minimo_local, mip=}")

    def aplicar(
        self,
        condiciones: str,
        alcance: str,
        mecanismo: str,
    ):
        listado_emd = {}

        self.sia_preparar_subsistema(condiciones, alcance, mecanismo)
        futuros = self.sia_subsistema.indices_ncubos
        presentes = self.sia_subsistema.dims_ncubos
        total = futuros.size + presentes.size

        for futuro in futuros:
            copia_subsistema = self.sia_subsistema
            # print(f"{futuro=}")
            particion = copia_subsistema.bipartir(
                np.array([futuro]),
                np.array([]),
            )
            dist_margin_particion = particion.distribucion_marginal()
            emd_particion_tpp = emd_efecto(
                dist_margin_particion,
                self.sia_dists_marginales,
            )
            listado_emd[emd_particion_tpp] = (1, futuro)

        for presente in presentes:
            particion = copia_subsistema.bipartir(
                np.array([]),
                np.array([presente]),
            )
            dist_margin_particion_t = particion.distribucion_marginal()
            emd_particion_t = emd_efecto(
                dist_margin_particion_t,
                self.sia_dists_marginales,
            )
            listado_emd[emd_particion_t] = (0, presente)

            print(f"{total=}")
            total -= 1

        minimo_local = min(listado_emd.keys())
        mip_local = listado_emd[minimo_local]

        print(f"{minimo_local, mip_local=}")

        prim_part = [[], []]
        dual_part = [[], []]
        for fut in futuros:
            if (1, fut) == mip_local:
                prim_part[1].append(fut)
            else:
                dual_part[1].append(fut)

        for pres in presentes:
            if (0, pres) == mip_local:
                prim_part[0].append(pres)
            else:
                dual_part[0].append(pres)

        mip_fmt = fmt_biparticion(prim_part, dual_part)

        print(f"{mip_fmt}")

        return Solution(
            perdida=minimo_local,
        )


"""

  - A B C
- - 5 2 7
a 5 
b 7
c 8

"""
