"""Fibonacci points, cached local connections, and batched orthographic projection."""

import colorsys
import math
import numpy as np


def fibonacci_sphere(samples):
    if type(samples) is not int or not 1 <= samples <= 10000:
        raise ValueError('Use between 1 and 10,000 points')
    index = np.arange(samples, dtype=np.float64)
    y = index * (2 / samples) - 1 + 1 / samples
    radius = np.sqrt(np.maximum(0, 1 - y * y))
    angle = index * (math.pi * (3 - math.sqrt(5)))
    return np.column_stack((np.cos(angle) * radius, y, np.sin(angle) * radius))


def connections(points, radius):
    if not math.isfinite(radius) or radius <= 0:
        raise ValueError('Connection radius must be positive and finite')
    coordinates = points.tolist()
    cells, edges = {}, []
    squared_radius = radius * radius
    for i, (x, y, z) in enumerate(coordinates):
        key = (math.floor(x / radius), math.floor(y / radius), math.floor(z / radius))
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    for j in cells.get((key[0] + dx, key[1] + dy, key[2] + dz), ()):
                        a, b, c = coordinates[j]
                        if (x - a) ** 2 + (y - b) ** 2 + (z - c) ** 2 < squared_radius:
                            edges.append((j, i))
        cells.setdefault(key, []).append(i)
    # Match the order in which the original duplicate connections were last drawn.
    edges.sort(key=lambda edge: (edge[1], edge[0]))
    return np.asarray(edges, dtype=np.intp).reshape(-1, 2)


def rainbow(hue):
    return tuple(min(255, round(channel * 256))
                 for channel in colorsys.hsv_to_rgb(hue, 0.9, 0.9))


class Sphere:
    def __init__(self, samples=100):
        self.points = fibonacci_sphere(samples)
        self.points.setflags(write=False)
        # Preserve the original radius at 100 points; keep dense meshes local.
        self.connection_radius = min(1.0, 5 / math.sqrt(samples))
        self.edges = connections(self.points, self.connection_radius)
        self.point_colors = [rainbow(i / samples) for i in range(samples)]
        self.edge_colors = [rainbow(int(i) * int(j) / (samples * samples)) for i, j in self.edges]
        self.rotated = np.empty_like(self.points)
        self.projected = np.empty((samples, 2))

    def project(self, angles, scale, center):
        if len(angles) != 3 or not all(math.isfinite(value) for value in angles):
            raise ValueError('Use three finite rotation angles')
        if not math.isfinite(scale) or scale <= 0:
            raise ValueError('Scale must be positive and finite')
        if len(center) != 2 or not all(math.isfinite(value) for value in center):
            raise ValueError('Use a finite two-dimensional center')
        x, y, z = angles
        cx, sx, cy, sy, cz, sz = math.cos(x), math.sin(x), math.cos(y), math.sin(y), math.cos(z), math.sin(z)
        rx = np.array(((1, 0, 0), (0, cx, -sx), (0, sx, cx)))
        ry = np.array(((cy, 0, sy), (0, 1, 0), (-sy, 0, cy)))
        rz = np.array(((cz, -sz, 0), (sz, cz, 0), (0, 0, 1)))
        rotation = rz @ ry @ rx
        np.matmul(self.points, rotation.T, out=self.rotated)
        np.multiply(self.rotated[:, :2], scale, out=self.projected)
        self.projected += center
        return self.projected
