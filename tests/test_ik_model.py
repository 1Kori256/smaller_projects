import math
import unittest
import numpy as np
from ik_model import ArmField, Ball, Settings


class SolverTests(unittest.TestCase):
    def test_anchored_chains_keep_roots_and_segment_lengths(self):
        field = ArmField((960, 720), Settings(16, 32, 12))
        rng = np.random.default_rng(2)
        for target in rng.uniform((0, 0), (960, 720), (30, 2)):
            field.update(target)
            np.testing.assert_allclose(field.points[:, 0], field.bases)
            lengths = np.linalg.norm(np.diff(field.points, axis=1), axis=2)
            np.testing.assert_allclose(lengths, 12, atol=1e-10)

    def test_free_chains_end_at_target(self):
        field = ArmField((960, 720), Settings(8, 24, 10))
        for target in ((300, 300), (0, 0), (960, 720)):
            field.update(target, anchored=False)
            np.testing.assert_allclose(field.points[:, -1], np.tile(target, (8, 1)), atol=1e-10)
            np.testing.assert_allclose(np.linalg.norm(np.diff(field.points, axis=1), axis=2), 10)

    def test_coincident_target_has_no_division_by_zero(self):
        for anchored in (True, False):
            field = ArmField((600, 480), Settings(1, 1, 10))
            target = field.points[0, 0].copy()
            with np.errstate(all='raise'):
                for _ in range(20):
                    field.update(target, anchored)
            self.assertTrue(np.isfinite(field.points).all())
            np.testing.assert_allclose(np.linalg.norm(np.diff(field.points, axis=1), axis=2), 10)

    def test_maximum_settings_stay_finite(self):
        field = ArmField((960, 720), Settings(50, 100, 100))
        for _ in range(10):
            field.update((480, 360))
        self.assertEqual(field.points.shape, (50, 101, 2))
        self.assertTrue(np.isfinite(field.points).all())
        np.testing.assert_allclose(np.linalg.norm(np.diff(field.points, axis=1), axis=2), 100, atol=1e-9)

    def test_anchors_fit_smaller_windows(self):
        field = ArmField((520, 480), Settings(50, 10, 5))
        self.assertTrue((field.bases >= 0).all())
        self.assertTrue((field.bases <= (520, 480)).all())

    def test_straight_chain_matches_scalar_follow_and_anchor(self):
        field = ArmField((520, 480), Settings(4, 8, 10))
        points = field.points.copy()
        for target in ((50, 60), (200, 200), (500, 400)):
            for chain, root in zip(points, field.bases):
                vectors = np.empty((8, 2))
                child = np.array(target, dtype=float)
                for i in range(7, -1, -1):
                    angle = math.atan2(child[1] - chain[i, 1], child[0] - chain[i, 0])
                    vector = np.array((math.cos(angle), math.sin(angle))) * 10
                    chain[i] = child - vector
                    vectors[i] = vector
                    child = chain[i].copy()
                chain[0] = root
                for i in range(8):
                    chain[i + 1] = chain[i] + vectors[i]
            field.update(target)
            np.testing.assert_allclose(field.points, points, atol=1e-9)

    def test_invalid_settings_and_targets(self):
        for values in ((0, 1, 1), (51, 1, 1), (1, 101, 1), (1, 1, 0), (1, 1, 101), (1, 2.5, 10)):
            with self.assertRaises(ValueError):
                Settings(*values)
        field = ArmField((600, 480))
        for target in ((math.nan, 0), (math.inf, 1), (1,), (1, 2, 3)):
            with self.assertRaises(ValueError):
                field.update(target)


class BallTests(unittest.TestCase):
    def test_wall_hits_clamp_and_reflect(self):
        ball = Ball(x=590, y=470, vx=200, vy=200)
        ball.update(1 / 60, (600, 480))
        self.assertEqual((ball.x, ball.y), (570, 450))
        self.assertLess(ball.vx, 0)
        self.assertLess(ball.vy, 0)
        ball = Ball(x=0, y=0, vx=-200, vy=-200)
        ball.update(1 / 60, (600, 480))
        self.assertEqual((ball.x, ball.y), (30, 30))
        self.assertGreater(ball.vx, 0)
        self.assertGreater(ball.vy, 0)

    def test_dragging_clamps_to_playfield(self):
        ball = Ball()
        ball.drag((-1000, 1000), (600, 480))
        self.assertEqual((ball.x, ball.y), (30, 450))

    def test_ball_stays_in_bounds_over_long_run(self):
        ball = Ball()
        for _ in range(2000):
            ball.update(1 / 60, (600, 480))
            self.assertTrue(30 <= ball.x <= 570)
            self.assertTrue(30 <= ball.y <= 450)
