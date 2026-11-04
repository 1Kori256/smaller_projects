import unittest
import numpy as np
from fluid_model import Fluid


class FluidTests(unittest.TestCase):
    def test_empty_fluid_stays_empty(self):
        fluid = Fluid(12)
        for _ in range(10):
            fluid.step()
        np.testing.assert_array_equal(fluid.density, 0)
        np.testing.assert_array_equal(fluid.vx, 0)
        np.testing.assert_array_equal(fluid.vy, 0)

    def test_scalar_boundaries_and_reflected_velocity(self):
        fluid = Fluid(12)
        for component in (0, 1, 2):
            field = np.arange(144, dtype=float).reshape(12, 12)
            fluid.boundary(component, field)
            np.testing.assert_array_equal(field[1:-1, 0], (-1 if component == 1 else 1) * field[1:-1, 1])
            np.testing.assert_array_equal(field[0, 1:-1], (-1 if component == 2 else 1) * field[1, 1:-1])
            self.assertEqual(field[0, 0], 0.5 * (field[0, 1] + field[1, 0]))

    def test_diffusion_preserves_constant_scalar_field(self):
        fluid = Fluid(12)
        field, source = np.ones((12, 12)), np.ones((12, 12))
        fluid.diffuse(0, field, source, 0.1)
        np.testing.assert_allclose(field, 1)

    def test_jacobi_matches_scalar_reference(self):
        fluid = Fluid(8, iterations=3)
        source = np.random.default_rng(1).random((8, 8))
        expected = np.zeros((8, 8))
        actual = expected.copy()
        for _ in range(3):
            old = expected.copy()
            for y in range(1, 7):
                for x in range(1, 7):
                    expected[y, x] = (source[y, x] + 0.5 * (
                        old[y, x + 1] + old[y, x - 1] + old[y + 1, x] + old[y - 1, x])) / 3
            fluid.boundary(0, expected)
        fluid.linear_solve(0, actual, source, 0.5, 3)
        np.testing.assert_allclose(actual, expected)

    def test_projection_reduces_divergence(self):
        fluid = Fluid(24, iterations=80)
        rng = np.random.default_rng(1)
        vx, vy = rng.normal(size=(24, 24)), rng.normal(size=(24, 24))
        fluid.boundary(1, vx)
        fluid.boundary(2, vy)
        def divergence():
            return np.linalg.norm(vx[1:-1, 2:] - vx[1:-1, :-2] + vy[2:, 1:-1] - vy[:-2, 1:-1])
        before = divergence()
        fluid.project(vx, vy)
        self.assertLess(divergence(), before)

    def test_zero_velocity_advection_preserves_interior(self):
        fluid = Fluid(12)
        source = np.random.default_rng(2).random((12, 12))
        output = np.zeros_like(source)
        fluid.advect(0, output, source, fluid.vx, fluid.vy)
        np.testing.assert_allclose(output[1:-1, 1:-1], source[1:-1, 1:-1])

    def test_extreme_velocity_stays_inside_sampling_grid(self):
        fluid = Fluid(12)
        source = np.arange(144, dtype=float).reshape(12, 12)
        for speed in (-1e6, 1e6):
            velocity = np.full((12, 12), speed)
            output = np.zeros_like(source)
            fluid.advect(0, output, source, velocity, velocity)
            self.assertTrue(np.isfinite(output).all())
            self.assertGreaterEqual(output.min(), source.min())
            self.assertLessEqual(output.max(), source.max())

    def test_density_is_nonnegative_during_injection(self):
        fluid = Fluid(16)
        for _ in range(50):
            fluid.source(3, 8, 2500, 3, -2)
            fluid.step()
        self.assertTrue(np.isfinite(fluid.density).all())
        self.assertTrue(np.isfinite(fluid.vx).all())
        self.assertGreaterEqual(fluid.density.min(), 0)
        self.assertGreater(fluid.density.max(), 0)

    def test_small_density_fades_completely(self):
        fluid = Fluid(12)
        fluid.density.fill(0.5)
        fluid.step()
        np.testing.assert_array_equal(fluid.density, 0)

    def test_sources_cannot_wrap_negative_or_outside_indices(self):
        fluid = Fluid(12)
        for x, y in ((-1, 2), (2, 12), (0, 0), (1.5, 2)):
            with self.assertRaises(ValueError):
                fluid.source(x, y, 1)
        for size in (0, 7, 257):
            with self.assertRaises(ValueError):
                Fluid(size)
