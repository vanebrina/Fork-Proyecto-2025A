# Algoritmo QNodes: Descripción Macroalgoritmica

En esta sección está la explicación generalizada o macroalgoritmo Q/QNodes. Así mismo en la implementación del código se cuenta una extensa documentación sobre su funcionamiento.

## Inicialización y Preparación

1. **Inicializar QNodes**: Se crea una instancia de la clase QNodes heredando de SIA (System Irreducibility Analysis).

2. **Aplicar Estrategia**: El punto de entrada del algoritmo recibe los parámetros:
   - `condicion`: Condiciones del sistema
   - `alcance`: Elementos del subsistema a analizar (purview)
   - `mecanismo`: Elementos del mecanismo en la red

3. **Preparar Subsistema**: Se configura el subsistema con los parámetros recibidos.

4. **Definir Conjuntos y Configurar Índices**:
   - Se crean conjuntos `futuro` (elementos en tiempo de efecto)
   - Se crean conjuntos `presente` (elementos en tiempo actual)
   - Se configuran índices y dimensiones para los nodos manejados en correlación a estos futuros y presentes respectivamente.

## Algoritmo Q Principal

5. **Llamada al Algoritmo Principal**: Se invoca `algorithm` con los vértices combinados *(en formato tupla, donde la primera posición intica el tiempo $0$ para $t_0$ o $1$ $t_1$ y en la segunda posición el índice o dimensión del subsistema)*.

6. **Inicialización de Conjuntos Base**:
   - `omegas_origen`: Contiene el primer elemento de los vértices
   - `deltas_origen`: Contiene todos los elementos restantes
   - `vertices_fase`: Inicializado con los vértices originales

7. **Bucle Principal de Fases (i)**:
   Para cada fase `i` en el rango `(len(vertices_fase) - 2)` *(básicamente iterar todos los elementos exeptuando el primero pues es el nodo ya tomado en omega al inicio y el final puesto ya se conocerá cuál será el peor elemento a tomar al momento que queden 2 y se seleccione el mejor)*:
   Es en esta fase donde podemos apreciar que en cada iteración el conjunto de particiones candidatas tiende a aumentar.

   8. **Inicialización de Ciclo**:
      - `omegas_ciclo`: Comienza con el primer elemento de `vertices_fase`
      - `deltas_ciclo`: Contiene todos los elementos restantes de `vertices_fase`
      - `emd_particion_candidata`: Inicializada como infinito positivo

   9. **Bucle de Ciclos (j)**:
      Para cada ciclo `j` en el rango `(len(deltas_ciclo) - 1)` se realiza lo que es la selección del mejor elemento (delta) para añadir a omega, de forma que se incrementa hasta la penúltima iteración, donde nuevamente ya conocemos cuál será el peor cuando queden dos elementos y se evalúen sus EMDs:

      10. **Bucle de Iteraciones (k)**:
          Para cada iteración `k` en el rango `len(deltas_ciclo)` es donde se calcula cada EMD sobre los deltas remanentes del ciclo:

          11. **Evaluación Submodular**:
              - Llamar a `funcion_submodular(deltas_ciclo[k], omegas_ciclo)`
              - Esta función calcula:
                * `emd_delta`: EMD de la bipartición del delta individual
                * `emd_union`: EMD de la combinación de biparticionar (delta ∪ omega)
                * `dist_marginal_delta`: Distribución marginal del delta
              - Calcular `emd_iteracion = emd_union - emd_delta`

          12. **Actualización del Mejor Delta**:
              Al terminar el cálculo de la subrutina, si `emd_iteracion < emd_local`:
              - Actualizar `emd_local = emd_iteracion`
              - Guardar `indice_mip = k`

      11. **Movimiento del Delta Óptimo**:
          - Añadir `deltas_ciclo[indice_mip]` a `omegas_ciclo`
          - Eliminar `deltas_ciclo[indice_mip]` de `deltas_ciclo`

   10. **Almacenar Partición Candidata**:
       - Guardar en `memoria_particiones` la EMD y distribución de la partición actual

   11. **Crear Nuevo Par Candidato**:
       - Agrupar último elemento de `omegas_ciclo` y último elemento de `deltas_ciclo` como una lista (formación del par candidato)
       - Actualizar `vertices_fase` con estos nuevos grupos, que es modificar el conjunto V inicial, de forma que ahora se tiene la agrupación del par/grupo candidato,

8. **Selección de Partición Óptima**:
   - Retornar la partición con la menor EMD de todas las almacenadas en `memoria_particiones`

## Función Submodular

La función submodular evalúa la combinación de conjuntos delta y omega:

1. **Evaluar Delta Individual**:
   - Preparar una copia temporal del subsistema
   - Activar los nodos delta en sus tiempos correspondientes
   - Bipartir el subsistema usando solo delta
   - Calcular EMD del delta individual
   
2. **Evaluar Combinación Delta ∪ Omega**:
   - Añadir nodos omega a la copia temporal
   - Bipartir el subsistema completo
   - Calcular EMD de la unión delta ∪ omega
   
3. **Retornar Resultados**:
   - Devolver `(emd_union, emd_delta, vector_delta_marginal)`

## Finalización

1. **Formatear Partición Óptima**: Prepara el resultado para devolver.
2. **Crear Objeto Solution**: Encapsula toda la información de la solución.
3. **Retornar Resultado**: Devuelve el objeto Solution con la partición óptima encontrada.