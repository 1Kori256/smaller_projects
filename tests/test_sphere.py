import math
import unittest
import numpy as np
from sphere_model import Sphere, connections, fibonacci_sphere


class GeometryTests(unittest.TestCase):
    def test_original_fibonacci_distribution(self):
        expected = []
        for i in range(100):
            y = i * (2 / 100) - 1 + 1 / 100
            radius = math.sqrt(1 - y * y)
            angle = i * math.pi * (3 - math.sqrt(5))
            expected.append((math.cos(angle) * radius, y, math.sin(angle) * radius))
        np.testing.assert_allclose(fibonacci_sphere(100), expected, atol=1e-13)

    def test_points_are_on_unit_sphere(self):
        for count in (1, 2, 100, 1000):
            points = fibonacci_sphere(count)
            self.assertEqual(points.shape, (count, 3))
            np.testing.assert_allclose(np.linalg.norm(points, axis=1), 1, atol=1e-13)

    def test_connections_match_exhaustive_original_rule(self):
        sphere = Sphere(100)
        expected = {(i, j) for i in range(100) for j in range(i + 1, 100)
                    if np.linalg.norm(sphere.points[i] - sphere.points[j]) < 0.5}
        actual = [tuple(pair) for pair in sphere.edges.tolist()]
        self.assertEqual(set(actual), expected)
        self.assertEqual(len(actual), len(set(actual)))
        self.assertTrue(all(i < j for i, j in actual))

    def test_grid_finds_all_neighbors_for_other_radii(self):
        points = fibonacci_sphere(150)
        for radius in (0.2, 0.6):
            expected = {(i, j) for i in range(150) for j in range(i + 1, 150)
                        if np.linalg.norm(points[i] - points[j]) < radius}
            self.assertEqual(set(map(tuple, connections(points, radius))), expected)

    def test_dense_mesh_stays_local(self):
        sphere = Sphere(1000)
        self.assertLess(len(sphere.edges), 8 * len(sphere.points))
        self.assertGreater(len(sphere.edges), 1000)

    def test_batched_rotation_matches_scalar_xyz_projection(self):
        sphere = Sphere(100)
        original = sphere.points.copy()
        for x, y, z in ((0, 0, 0), (0.3, -0.5, 0.7), (-2.5, 1.5, -1), (math.pi, math.pi / 2, 0)):
            expected = []
            for a, b, c in sphere.points:
                b, c = b * math.cos(x) - c * math.sin(x), b * math.sin(x) + c * math.cos(x)
                a, c = a * math.cos(y) + c * math.sin(y), -a * math.sin(y) + c * math.cos(y)
                a, b = a * math.cos(z) - b * math.sin(z), a * math.sin(z) + b * math.cos(z)
                expected.append((a * 300 + 640, b * 300 + 360))
            np.testing.assert_allclose(sphere.project((x, y, z), 300, (640, 360)), expected, atol=1e-10)
            np.testing.assert_allclose(np.linalg.norm(sphere.rotated, axis=1), 1, atol=1e-13)
        np.testing.assert_array_equal(sphere.points, original)

    def test_single_point_has_no_edges(self):
        sphere = Sphere(1)
        self.assertEqual(sphere.edges.shape, (0, 2))
        self.assertTrue(np.isfinite(sphere.project((0, 0, 0), 100, (200, 200))).all())

    def test_invalid_values(self):
        for count in (0, -1, 10001, 2.5, True):
            with self.assertRaises(ValueError):
                fibonacci_sphere(count)
        sphere = Sphere()
        for angles, zoom, center in (((0, 0), 100, (0, 0)), ((math.nan, 0, 0), 100, (0, 0)),
                                     ((0, 0, 0), 0, (0, 0)), ((0, 0, 0), math.inf, (0, 0)),
                                     ((0, 0, 0), 100, (math.inf, 0))):
            with self.assertRaises(ValueError):
                sphere.project(angles, zoom, center)
