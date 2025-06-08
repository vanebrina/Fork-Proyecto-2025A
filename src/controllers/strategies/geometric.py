import time
import numpy as np
import multiprocessing as mp
from datetime import datetime
from numba import njit
from tqdm import tqdm
from scipy.sparse import lil_matrix
import csv

from src.controllers.manager import Manager
from src.models.base.sia import SIA
from src.models.core.solution import Solution
from src.middlewares.profile import profiler_manager, profile
from src.middlewares.slogger import SafeLogger
from src.middlewares.observer import DebugObserver
from src.funcs.system import biparticiones
from src.funcs.format import fmt_biparticion
from src.constants.models import DUMMY_ARR
from src.funcs.base import emd_efecto  # Importar emd_efecto

@njit(cache=True)
def l1_distance(a: np.ndarray, b: np.ndarray) -> float:
    result = 0.0
    for i in range(a.size):
        result += abs(a[i] - b[i])
    return result

def calcular_tabla_costos_sparse(tensor: np.ndarray):
    n = tensor.shape[0]
    tabla = lil_matrix((n, n), dtype=np.float32)
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            d = bin(i ^ j).count("1")
            gamma = 2 ** (-d)
            tabla[i, j] = gamma * abs(tensor[i] - tensor[j])
    return tabla

_phi_cache = {}

def evaluar_biparticion(args):
    subsistema, dist_subsistema, futuros, presentes = args
    key = (tuple(sorted(futuros)), tuple(sorted(presentes)))
    if key in _phi_cache:
        return _phi_cache[key]

    bip = subsistema.bipartir(
        np.array(futuros, dtype=np.int8),
        np.array(presentes, dtype=np.int8)
    )

    dist_particion = bip.distribucion_marginal()
    phi = emd_efecto(dist_particion, dist_subsistema)
    _phi_cache[key] = (phi, dist_particion, key)
    print(f"Evaluando: futuros={futuros}, presentes={presentes}, phi={phi}")  # Log para depuración
    return _phi_cache[key]

@profile(context={"strategy": "geometric"})
class Geometric(SIA):
    def __init__(self, config: Manager) -> None:
        super().__init__(config)
        profiler_manager.start_session(f"NET{len(config.estado_inicial)}{config.pagina}")
        self.logger = SafeLogger("geometric")
        self.debug_observer = DebugObserver()

    def aplicar_estrategia(self, condiciones: str, alcance: str, mecanismo: str) -> Solution:
        self.sia_tiempo_inicio = time.time()

        print("[1] Preparando subsistema y distribuciones...")
        self.sia_preparar_subsistema(condiciones, alcance, mecanismo)
        subsistema = self.sia_subsistema
        dist_subsistema = subsistema.distribucion_marginal()
        print(f"Subsistema: indices_ncubos={subsistema.indices_ncubos}, dims_ncubos={subsistema.dims_ncubos}")

        print("[2] Calculando tabla de costos aproximada...")
        tensor = getattr(subsistema, 'tensor_principal', dist_subsistema)
        tabla_costos = calcular_tabla_costos_sparse(tensor)
        self.debug_observer.on_tensor_product({
            "n_cubes": 1,
            "active_dims": list(range(tensor.shape[0])),
            "cubes": [type('DummyCube', (), {"indices": list(range(tensor.shape[0])), "dims": list(range(tensor.shape[0])), "data": tabla_costos})()]
        })

        print("[3] Generando biparticiones candidatas geométricas...")
        futuros = subsistema.indices_ncubos
        presentes = subsistema.dims_ncubos
        n = len(futuros)

        candidatas_list = []
        for i, b in enumerate(biparticiones(futuros, presentes)):
            # Permitir tamaños flexibles
            if 0 <= len(b[0]) <= n and 0 <= len(b[1]) <= n:
                candidatas_list.append(b)
            if len(candidatas_list) >= 5000000:
                break

        print(f"    ▸ Total de biparticiones evaluadas: {len(candidatas_list)}")

        print("[4] Evaluando biparticiones por discrepancia tensorial...")
        tareas = [(subsistema, dist_subsistema, f, p) for f, p in candidatas_list]

        mejor_phi = np.inf
        mejor_dist = DUMMY_ARR
        mejor_bipart = None

        with mp.Pool(processes=mp.cpu_count()) as pool:
            for resultado in tqdm(pool.imap_unordered(evaluar_biparticion, tareas), total=len(tareas), desc="    ▸ Evaluando"):
                phi, dist_part, bipart = resultado
                if phi < mejor_phi:
                    mejor_phi = phi
                    mejor_dist = dist_part
                    mejor_bipart = bipart
                    print(f"    ▸ φ provisional: {mejor_phi}, bipartición: {bipart}")
                    if mejor_phi == 0.0:
                        print("    ▸ φ = 0 encontrado. Finalizando evaluación anticipadamente.")
                        pool.terminate()
                        break

        fsel, psel = mejor_bipart
        dual_p = set(subsistema.dims_ncubos.tolist()) - set(psel)
        dual_f = set(subsistema.indices_ncubos.tolist()) - set(fsel)
        bipart_str = fmt_biparticion((fsel, psel), (tuple(dual_f), tuple(dual_p)))
        tiempo_total = time.time() - self.sia_tiempo_inicio

        # Complejidad:
        # - Tabla de costos: O(n^2) donde n = 2^d
        # - Evaluación de m biparticiones: O(m)
        # - Total: O(n^2 + m)

        return Solution(
            estrategia="Geometric",
            perdida=mejor_phi,
            distribucion_subsistema=dist_subsistema,
            distribucion_particion=mejor_dist,
            particion=bipart_str,
            tiempo_total=tiempo_total,
            hablar=True
        )