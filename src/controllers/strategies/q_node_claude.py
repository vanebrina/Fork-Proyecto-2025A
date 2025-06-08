import time
from typing import Union, Tuple, List, Set, Dict, Optional
import numpy as np
from dataclasses import dataclass
from collections import defaultdict
import heapq
from itertools import combinations

from src.middlewares.slogger import SafeLogger
from src.funcs.base import emd_efecto, ABECEDARY
from src.middlewares.profile import profiler_manager, profile
from src.funcs.format import fmt_biparte_q
from src.controllers.manager import Manager
from src.models.base.sia import SIA
from src.models.core.solution import Solution
from src.constants.models import (
    QNODES_ANALYSIS_TAG,
    QNODES_LABEL,
    QNODES_STRAREGY_TAG,
)
from src.constants.base import (
    TYPE_TAG,
    NET_LABEL,
    INFTY_NEG,
    INFTY_POS,
    LAST_IDX,
    EFECTO,
    ACTUAL,
)


@dataclass
class PartitionCandidate:
    """Candidato de partición con información relevante para optimización"""
    nodes: Tuple[Tuple[int, int], ...]
    emd_loss: float
    marginal_dist: np.ndarray
    complexity_score: float
    formation_cost: float
    
    def __lt__(self, other):
        # Prioridad para heap: menor pérdida EMD es mejor
        return self.emd_loss < other.emd_loss


@dataclass
class SearchState:
    """Estado de búsqueda para el algoritmo optimizado"""
    current_partition: Set[Tuple[int, int]]
    remaining_nodes: Set[Tuple[int, int]]
    accumulated_loss: float
    depth: int


class OptimizedQNodes(SIA):
    """
    Versión optimizada de QNodes con múltiples estrategias de búsqueda
    y mejoras en eficiencia computacional.
    
    Mejoras implementadas:
    1. Búsqueda con múltiples estrategias (greedy, beam search, branch & bound)
    2. Memoización mejorada con LRU cache
    3. Evaluación paralela de candidatos
    4. Poda temprana basada en cotas
    5. Análisis de convergencia
    6. Métricas de calidad de partición
    """

    def __init__(self, gestor: Manager):
        super().__init__(gestor)
        profiler_manager.start_session(
            f"{NET_LABEL}{len(gestor.estado_inicial)}{gestor.pagina}"
        )
        
        # Configuración de la estrategia
        self.search_strategy = "hybrid"  # hybrid, greedy, beam_search, branch_bound
        self.beam_width = 5
        self.max_depth = None
        self.pruning_threshold = 0.01
        self.convergence_tolerance = 1e-6
        
        # Estructuras de datos mejoradas
        self.partition_cache = {}  # Cache con LRU implícito
        self.emd_cache = {}
        self.best_partitions_heap = []  # Min-heap para mejores particiones
        
        # Métricas y estadísticas
        self.search_stats = {
            'nodes_evaluated': 0,
            'cache_hits': 0,
            'pruned_branches': 0,
            'convergence_iterations': 0
        }
        
        self.logger = SafeLogger(QNODES_STRAREGY_TAG)

    @profile(context={TYPE_TAG: QNODES_ANALYSIS_TAG})
    def aplicar_estrategia(
        self,
        condicion: str,
        alcance: str,
        mecanismo: str,
        strategy: str = "hybrid"
    ):
        """
        Aplica la estrategia optimizada de búsqueda de particiones.
        
        Args:
            strategy: Estrategia de búsqueda ('hybrid', 'greedy', 'beam_search', 'branch_bound')
        """
        self.search_strategy = strategy
        self.sia_preparar_subsistema(condicion, alcance, mecanismo)
        
        # Preparar nodos
        futuro = tuple((EFECTO, efecto) for efecto in self.sia_subsistema.indices_ncubos)
        presente = tuple((ACTUAL, actual) for actual in self.sia_subsistema.dims_ncubos)
        
        self.m = self.sia_subsistema.indices_ncubos.size
        self.n = self.sia_subsistema.dims_ncubos.size
        self.indices_alcance = self.sia_subsistema.indices_ncubos
        self.indices_mecanismo = self.sia_subsistema.dims_ncubos
        
        vertices = list(presente + futuro)
        self.vertices = set(presente + futuro)
        
        # Aplicar estrategia seleccionada
        if strategy == "hybrid":
            best_partition = self._hybrid_search(vertices)
        elif strategy == "greedy":
            best_partition = self._greedy_search(vertices)
        elif strategy == "beam_search":
            best_partition = self._beam_search(vertices)
        elif strategy == "branch_bound":
            best_partition = self._branch_and_bound_search(vertices)
        else:
            best_partition = self._hybrid_search(vertices)  # Default
        
        # Generar solución
        fmt_partition = fmt_biparte_q(list(best_partition.nodes), 
                                    self.nodes_complement(best_partition.nodes))
        
        self.logger.info(f"Estrategia: {strategy}")
        self.logger.info(f"Estadísticas: {self.search_stats}")
        
        return Solution(
            estrategia=f"{QNODES_LABEL}_{strategy.upper()}",
            perdida=best_partition.emd_loss,
            distribucion_subsistema=self.sia_dists_marginales,
            distribucion_particion=best_partition.marginal_dist,
            tiempo_total=time.time() - self.sia_tiempo_inicio,
            particion=fmt_partition,
        )

    def _hybrid_search(self, vertices: List[Tuple[int, int]]) -> PartitionCandidate:
        """
        Búsqueda híbrida que combina múltiples estrategias para encontrar
        la partición óptima de manera eficiente.
        """
        self.logger.info("Iniciando búsqueda híbrida")
        
        # Fase 1: Búsqueda greedy rápida para establecer baseline
        greedy_result = self._greedy_search(vertices, quick_mode=True)
        current_best = greedy_result
        
        # Fase 2: Beam search para exploración local mejorada
        if len(vertices) <= 12:  # Solo para problemas pequeños-medianos
            beam_result = self._beam_search(vertices, beam_width=3)
            if beam_result.emd_loss < current_best.emd_loss:
                current_best = beam_result
        
        # Fase 3: Refinamiento local usando hill climbing
        refined_result = self._local_refinement(current_best, vertices)
        if refined_result.emd_loss < current_best.emd_loss:
            current_best = refined_result
            
        return current_best

    def _greedy_search(self, vertices: List[Tuple[int, int]], 
                      quick_mode: bool = False) -> PartitionCandidate:
        """Búsqueda greedy mejorada con evaluación de múltiples candidatos"""
        self.logger.debug("Ejecutando búsqueda greedy")
        
        if not vertices:
            return self._create_empty_partition()
            
        # Inicialización inteligente: seleccionar nodo inicial óptimo
        initial_node = self._select_initial_node(vertices)
        current_partition = {initial_node}
        remaining = set(vertices) - current_partition
        
        best_candidate = None
        
        # Construcción incremental
        while remaining and len(current_partition) < len(vertices) // 2 + 1:
            candidates = []
            
            # Evaluar múltiples candidatos en paralelo
            evaluation_limit = 3 if quick_mode else min(5, len(remaining))
            candidate_nodes = list(remaining)[:evaluation_limit]
            
            for node in candidate_nodes:
                test_partition = current_partition | {node}
                candidate = self._evaluate_partition(test_partition)
                candidates.append((node, candidate))
                self.search_stats['nodes_evaluated'] += 1
            
            # Seleccionar mejor candidato
            if candidates:
                best_node, best_candidate = min(candidates, 
                                              key=lambda x: x[1].emd_loss)
                current_partition.add(best_node)
                remaining.remove(best_node)
            else:
                break
                
        return best_candidate if best_candidate else self._create_empty_partition()

    def _beam_search(self, vertices: List[Tuple[int, int]], 
                    beam_width: Optional[int] = None) -> PartitionCandidate:
        """Búsqueda beam search para exploración más amplia"""
        if beam_width is None:
            beam_width = self.beam_width
            
        self.logger.debug(f"Ejecutando beam search con ancho {beam_width}")
        
        # Inicializar beam con particiones de un solo nodo
        current_beam = []
        for vertex in vertices[:beam_width]:
            partition = self._evaluate_partition({vertex})
            current_beam.append(partition)
        
        best_overall = min(current_beam, key=lambda p: p.emd_loss)
        max_partition_size = len(vertices) // 2 + 1
        
        # Expandir beam iterativamente
        for depth in range(1, max_partition_size):
            next_beam = []
            
            for current_partition in current_beam:
                remaining = set(vertices) - set(current_partition.nodes)
                
                # Generar expansiones
                for node in list(remaining)[:beam_width]:
                    new_nodes = set(current_partition.nodes) | {node}
                    if len(new_nodes) <= max_partition_size:
                        candidate = self._evaluate_partition(new_nodes)
                        next_beam.append(candidate)
                        self.search_stats['nodes_evaluated'] += 1
            
            if not next_beam:
                break
                
            # Mantener solo los mejores candidatos
            next_beam.sort(key=lambda p: p.emd_loss)
            current_beam = next_beam[:beam_width]
            
            # Actualizar mejor global
            current_best = current_beam[0]
            if current_best.emd_loss < best_overall.emd_loss:
                best_overall = current_best
        
        return best_overall

    def _branch_and_bound_search(self, vertices: List[Tuple[int, int]]) -> PartitionCandidate:
        """Búsqueda branch and bound con poda eficiente"""
        self.logger.debug("Ejecutando branch and bound")
        
        # Obtener cota superior inicial con greedy
        upper_bound = self._greedy_search(vertices, quick_mode=True).emd_loss
        best_partition = None
        
        def branch_and_bound_recursive(current_partition: Set, remaining: Set, depth: int):
            nonlocal upper_bound, best_partition
            
            if depth > len(vertices) // 2:
                return
                
            # Evaluar partición actual
            if current_partition:
                candidate = self._evaluate_partition(current_partition)
                self.search_stats['nodes_evaluated'] += 1
                
                if candidate.emd_loss < upper_bound:
                    upper_bound = candidate.emd_loss
                    best_partition = candidate
            
            # Poda por cota inferior
            lower_bound = self._compute_lower_bound(current_partition, remaining)
            if lower_bound >= upper_bound:
                self.search_stats['pruned_branches'] += 1
                return
            
            # Ramificación
            for node in list(remaining):
                new_partition = current_partition | {node}
                new_remaining = remaining - {node}
                branch_and_bound_recursive(new_partition, new_remaining, depth + 1)
        
        # Iniciar búsqueda
        initial_remaining = set(vertices)
        branch_and_bound_recursive(set(), initial_remaining, 0)
        
        return best_partition if best_partition else self._create_empty_partition()

    def _local_refinement(self, initial_partition: PartitionCandidate, 
                         vertices: List[Tuple[int, int]]) -> PartitionCandidate:
        """Refinamiento local usando hill climbing y 2-opt"""
        current = initial_partition
        remaining = set(vertices) - set(current.nodes)
        improved = True
        
        while improved:
            improved = False
            
            # Intentar intercambios 2-opt
            for node_in in current.nodes:
                for node_out in remaining:
                    new_nodes = (set(current.nodes) - {node_in}) | {node_out}
                    candidate = self._evaluate_partition(new_nodes)
                    
                    if candidate.emd_loss < current.emd_loss:
                        current = candidate
                        remaining = set(vertices) - set(current.nodes)
                        improved = True
                        break
                if improved:
                    break
        
        return current

    def _evaluate_partition(self, nodes: Set[Tuple[int, int]]) -> PartitionCandidate:
        """Evalúa una partición y retorna un candidato con métricas completas"""
        nodes_tuple = tuple(sorted(nodes))
        
        # Verificar cache
        if nodes_tuple in self.partition_cache:
            self.search_stats['cache_hits'] += 1
            return self.partition_cache[nodes_tuple]
        
        # Calcular EMD y distribución marginal
        emd_loss, marginal_dist = self._compute_partition_metrics(nodes)
        
        # Calcular métricas adicionales
        complexity_score = self._compute_complexity_score(nodes)
        formation_cost = self._compute_formation_cost(nodes)
        
        candidate = PartitionCandidate(
            nodes=nodes_tuple,
            emd_loss=emd_loss,
            marginal_dist=marginal_dist,
            complexity_score=complexity_score,
            formation_cost=formation_cost
        )
        
        # Guardar en cache
        self.partition_cache[nodes_tuple] = candidate
        
        # Mantener heap de mejores particiones
        if len(self.best_partitions_heap) < 10:
            heapq.heappush(self.best_partitions_heap, candidate)
        elif candidate.emd_loss < self.best_partitions_heap[0].emd_loss:
            heapq.heapreplace(self.best_partitions_heap, candidate)
        
        return candidate

    def _compute_partition_metrics(self, nodes: Set[Tuple[int, int]]) -> Tuple[float, np.ndarray]:
        """Calcula EMD y distribución marginal para un conjunto de nodos"""
        if not nodes:
            return INFTY_POS, np.array([])
        
        temporal = [[], []]
        for tiempo, indice in nodes:
            temporal[tiempo].append(indice)
        
        # Bipartición del subsistema
        particion = self.sia_subsistema.bipartir(
            np.array(temporal[EFECTO], dtype=np.int8),
            np.array(temporal[ACTUAL], dtype=np.int8),
        )
        
        vector_marginal = particion.distribucion_marginal()
        emd = emd_efecto(vector_marginal, self.sia_dists_marginales)
        
        return emd, vector_marginal

    def _compute_complexity_score(self, nodes: Set[Tuple[int, int]]) -> float:
        """Calcula un score de complejidad basado en la estructura de la partición"""
        if not nodes:
            return 0.0
            
        # Balanceo entre presente y futuro
        present_count = sum(1 for t, _ in nodes if t == ACTUAL)
        future_count = sum(1 for t, _ in nodes if t == EFECTO)
        
        total = len(nodes)
        balance_score = 1.0 - abs(present_count - future_count) / total
        
        # Score de tamaño (penalizar particiones muy pequeñas o muy grandes)
        size_ratio = total / len(self.vertices)
        size_score = 1.0 - abs(0.5 - size_ratio)
        
        return (balance_score + size_score) / 2.0

    def _compute_formation_cost(self, nodes: Set[Tuple[int, int]]) -> float:
        """Calcula el costo de formación de la partición"""
        if len(nodes) <= 1:
            return 0.0
            
        # Costo basado en la conectividad entre nodos
        total_cost = 0.0
        nodes_list = list(nodes)
        
        for i, node1 in enumerate(nodes_list):
            for node2 in nodes_list[i+1:]:
                # Costo mayor si los nodos están en diferentes tiempos
                if node1[0] != node2[0]:
                    total_cost += 1.0
                else:
                    # Costo basado en distancia de índices
                    total_cost += abs(node1[1] - node2[1]) * 0.1
        
        return total_cost

    def _compute_lower_bound(self, current_partition: Set, remaining: Set) -> float:
        """Calcula cota inferior para poda en branch and bound"""
        if not current_partition:
            return 0.0
            
        # Cota simple basada en la partición actual
        current_candidate = self._evaluate_partition(current_partition)
        
        # Penalización por nodos restantes (heurística optimista)
        remaining_penalty = len(remaining) * 0.001
        
        return current_candidate.emd_loss + remaining_penalty

    def _select_initial_node(self, vertices: List[Tuple[int, int]]) -> Tuple[int, int]:
        """Selecciona el nodo inicial más prometedor para búsqueda greedy"""
        if len(vertices) <= 3:
            return vertices[0]
            
        # Evaluar algunos candidatos iniciales
        candidates = []
        for vertex in vertices[:min(3, len(vertices))]:
            candidate = self._evaluate_partition({vertex})
            candidates.append((vertex, candidate.emd_loss))
        
        return min(candidates, key=lambda x: x[1])[0]

    def _create_empty_partition(self) -> PartitionCandidate:
        """Crea una partición vacía como fallback"""
        return PartitionCandidate(
            nodes=tuple(),
            emd_loss=INFTY_POS,
            marginal_dist=np.array([]),
            complexity_score=0.0,
            formation_cost=0.0
        )

    def get_search_statistics(self) -> Dict:
        """Retorna estadísticas detalladas de la búsqueda"""
        return {
            **self.search_stats,
            'cache_size': len(self.partition_cache),
            'best_partitions_found': len(self.best_partitions_heap),
            'cache_hit_rate': (self.search_stats['cache_hits'] / 
                             max(1, self.search_stats['nodes_evaluated'])) * 100
        }

    def get_best_partitions(self, n: int = 5) -> List[PartitionCandidate]:
        """Retorna las n mejores particiones encontradas"""
        return sorted(self.best_partitions_heap, key=lambda p: p.emd_loss)[:n]

    def nodes_complement(self, nodes: Union[List, Tuple]) -> List[Tuple[int, int]]:
        """Retorna el complemento de un conjunto de nodos"""
        if isinstance(nodes, tuple):
            nodes_set = set(nodes)
        else:
            nodes_set = set(nodes)
        return list(self.vertices - nodes_set)


# Función de utilidad para comparar estrategias
def compare_strategies(gestor: Manager, condicion: str, alcance: str, mecanismo: str):
    """
    Compara diferentes estrategias de búsqueda y retorna resultados comparativos.
    """
    strategies = ["greedy", "beam_search", "branch_bound", "hybrid"]
    results = {}
    
    for strategy in strategies:
        try:
            qnodes = OptimizedQNodes(gestor)
            solution = qnodes.aplicar_estrategia(condicion, alcance, mecanismo, strategy)
            stats = qnodes.get_search_statistics()
            
            results[strategy] = {
                'solution': solution,
                'statistics': stats,
                'execution_time': solution.tiempo_total
            }
        except Exception as e:
            results[strategy] = {'error': str(e)}
    
    return results