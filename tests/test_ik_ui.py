import os
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

import unittest
from unittest.mock import patch
import numpy as np
import pygame
from ik_model import Settings
from inverse_kinematics import Game


class UITests(unittest.TestCase):
    def setUp(self):
        self.game = Game((960, 600), Settings(8, 16, 10))
        pygame.event.clear()

    def tearDown(self):
        self.game.close()

    def post(self, event_type, **attributes):
        pygame.event.post(pygame.event.Event(event_type, **attributes))

    def test_ball_can_be_held_and_dragged(self):
        self.post(pygame.MOUSEBUTTONDOWN, button=1, pos=(200, 200))
        self.game.frame(1 / 60)
        for _ in range(3):
            self.game.frame(1 / 60)
        self.assertEqual((self.game.ball.x, self.game.ball.y), (200, 200))
        self.post(pygame.MOUSEMOTION, pos=(300, 250))
        self.game.frame(1 / 60)
        self.assertEqual((self.game.ball.x, self.game.ball.y), (300, 250))
        self.post(pygame.MOUSEBUTTONUP, button=1, pos=(300, 250))
        self.game.frame(1 / 60)
        self.assertFalse(self.game.dragging_ball)
        self.assertGreater(self.game.ball.x, 300)

    def test_slider_bounds_and_rebuild(self):
        slider = self.game.sliders[0]
        self.post(pygame.MOUSEBUTTONDOWN, button=1, pos=(slider.x, slider.top))
        self.post(pygame.MOUSEMOTION, pos=(slider.x, slider.bottom + 1000))
        self.game.frame(1 / 60)
        self.assertEqual(self.game.settings.chains, 50)
        self.assertEqual(self.game.field.points.shape[0], 50)
        self.post(pygame.MOUSEMOTION, pos=(slider.x, slider.top - 1000))
        self.game.frame(1 / 60)
        self.assertEqual(self.game.settings.chains, 1)
        self.post(pygame.MOUSEBUTTONUP, button=1, pos=(slider.x, slider.top))
        self.game.frame(0)
        self.assertIsNone(self.game.dragging_slider)

    def test_slider_drag_does_not_change_other_sliders(self):
        slider = self.game.sliders[1]
        self.post(pygame.MOUSEBUTTONDOWN, button=1, pos=(slider.x, slider.top))
        self.post(pygame.MOUSEMOTION, pos=(self.game.sliders[2].x, slider.bottom))
        self.game.frame(1 / 60)
        self.assertEqual(self.game.settings, Settings(8, 100, 10))

    def test_anchor_toggle_switches_solver_mode(self):
        self.post(pygame.MOUSEBUTTONDOWN, button=1, pos=self.game.toggle_rect.center)
        self.game.frame(1 / 60)
        self.assertFalse(self.game.anchored)
        expected = np.tile((self.game.ball.x, self.game.ball.y), (8, 1))
        np.testing.assert_allclose(self.game.field.points[:, -1], expected)
        self.post(pygame.MOUSEBUTTONDOWN, button=1, pos=self.game.toggle_rect.center)
        self.game.frame(1 / 60)
        self.assertTrue(self.game.anchored)
        np.testing.assert_allclose(self.game.field.points[:, 0], self.game.field.bases)

    def test_focus_loss_releases_drag(self):
        self.post(pygame.MOUSEBUTTONDOWN, button=1, pos=(200, 200))
        self.post(pygame.WINDOWFOCUSLOST)
        self.game.frame(1 / 60)
        self.assertFalse(self.game.dragging_ball)
        self.assertIsNone(self.game.dragging_slider)

    def test_reset_keeps_settings(self):
        self.game.ball.drag((300, 300), self.game.field_size)
        self.post(pygame.KEYDOWN, key=pygame.K_r)
        self.game.frame(0)
        self.assertEqual((self.game.ball.x, self.game.ball.y), (30, 30))
        self.assertEqual(self.game.settings, Settings(8, 16, 10))

    def test_render_rate_does_not_change_simulation(self):
        for _ in range(60):
            self.game.frame(1 / 60)
        expected_points = self.game.field.points.copy()
        expected_ball = (self.game.ball.x, self.game.ball.y)
        self.game.reset()
        self.game.accumulator = 0
        for _ in range(30):
            self.game.frame(1 / 30)
        np.testing.assert_allclose(self.game.field.points, expected_points)
        self.assertEqual((self.game.ball.x, self.game.ball.y), expected_ball)

    def test_scene_cannot_overdraw_control_panel(self):
        self.game.field.points[:] = (self.game.width - 10, 200)
        self.game.render()
        self.assertEqual(tuple(self.game.screen.get_at((self.game.width - 10, 200)))[:3], (0, 0, 0))

    def test_quit_does_not_render_again(self):
        self.post(pygame.QUIT)
        with patch.object(self.game, 'render') as render:
            self.assertFalse(self.game.frame(1 / 60))
            render.assert_not_called()

    def test_render_uses_cached_panel_and_text(self):
        self.game.render()
        with patch('pygame.Surface', side_effect=AssertionError('allocation during draw')):
            self.game.render()
