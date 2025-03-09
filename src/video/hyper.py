from manim import *
import numpy as np

class Hipercubo(ThreeDScene):
    def construct(self):
        # Configuración de la escena 3D
        self.set_camera_orientation(phi=75 * DEGREES, theta=30 * DEGREES)
        self.camera.frame_center = ORIGIN
        
        # Definir vértices del hipercubo 4D (representados en coordenadas 4D)
        vertices_4d = []
        for x in [-1, 1]:
            for y in [-1, 1]:
                for z in [-1, 1]:
                    for w in [-1, 1]:
                        vertices_4d.append([x, y, z, w])
        
        # Función para proyectar del 4D al 3D (proyección estereográfica simple)
        def project_4d_to_3d(point_4d, w_factor=0.5):
            x, y, z, w = point_4d
            factor = 1 / (w_factor - w)
            return np.array([x * factor, y * factor, z * factor])
        
        # Proyectar vértices a 3D
        vertices_3d = [project_4d_to_3d(v) for v in vertices_4d]
        
        # Crear puntos para los vértices
        dots = VGroup(*[Dot3D(point=p, color=BLUE, radius=0.05) for p in vertices_3d])
        
        # Definir las aristas del hipercubo conectando vértices que difieren en una coordenada
        edges = []
        for i, v1 in enumerate(vertices_4d):
            for j, v2 in enumerate(vertices_4d):
                if i < j:  # Para evitar duplicados
                    diff = sum(1 for a, b in zip(v1, v2) if a != b)
                    if diff == 1:  # Conectar solo vértices que difieren en una coordenada
                        edges.append((i, j))
        
        # Crear líneas para las aristas
        lines = VGroup(*[Line3D(
            vertices_3d[i], vertices_3d[j],
            color=WHITE, thickness=0.02
        ) for i, j in edges])
        
        # Crear el hipercubo (vértices + aristas)
        hypercube = VGroup(dots, lines)
        
        # Mostrar y animar
        self.play(Create(lines), run_time=2)
        self.play(Create(dots), run_time=1)
        
        # Rotar para mejor visualización
        self.begin_ambient_camera_rotation(rate=0.1)
        self.wait(5)