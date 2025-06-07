import numpy as np
from itertools import combinations
from src.models.base.sia import SIA

class GeometricSIA(SIA):
    def __init__(self, gestor):
        super().__init__(gestor)

    def aplicar_estrategia(self):
        tensores = self.descomponer_tensores_elementales()
        tabla_costos = self.calcular_tabla_costos(tensores)
        biparticiones = self.identificar_biparticiones(tabla_costos)
        mejor_biparticion = None
        mejor_discrepancia = float('inf')
        for biparticion in biparticiones:
            discrepancia = self.evaluar_discrepancia_tensorial(biparticion, tensores)
            if discrepancia < mejor_discrepancia:
                mejor_discrepancia = discrepancia
                mejor_biparticion = biparticion
        return mejor_biparticion

    def descomponer_tensores_elementales(self):
        # Supón que el gestor tiene un atributo 'matriz_adyacencia' (numpy array)
        # Si no, reemplaza esto por la forma correcta de obtener la matriz
        if hasattr(self.gestor, 'matriz_adyacencia'):
            return self.gestor.matriz_adyacencia
        # Si no existe, crea una matriz de ejemplo (¡ajusta esto a tu caso real!)
        n = len(self.gestor.estado_inicial)
        return np.zeros((n, n))

    def calcular_tabla_costos(self, matriz_adyacencia):
        n = matriz_adyacencia.shape[0]
        # Genera todas las biparticiones posibles (excepto vacía y total)
        particiones = []
        for r in range(1, n // 2 + 1):
            for grupoA in combinations(range(n), r):
                grupoB = tuple(set(range(n)) - set(grupoA))
                particiones.append((grupoA, grupoB))
        # Calcula el costo para cada bipartición
        tabla_costos = []
        for grupoA, grupoB in particiones:
            costo = matriz_adyacencia[np.ix_(grupoA, grupoB)].sum() + matriz_adyacencia[np.ix_(grupoB, grupoA)].sum()
            tabla_costos.append({'biparticion': (grupoA, grupoB), 'costo': costo})
        return tabla_costos

    def identificar_biparticiones(self, tabla_costos):
        # Selecciona las biparticiones con menor costo (puedes ajustar el criterio)
        if not tabla_costos:
            return []
        min_costo = min(item['costo'] for item in tabla_costos)
        return [item['biparticion'] for item in tabla_costos if item['costo'] == min_costo]

    def evaluar_discrepancia_tensorial(self, biparticion, matriz_adyacencia):
        grupoA, grupoB = biparticion
        # La discrepancia es la suma de las conexiones entre los dos grupos
        return matriz_adyacencia[np.ix_(grupoA, grupoB)].sum() + matriz_adyacencia[np.ix_(grupoB, grupoA)].sum()