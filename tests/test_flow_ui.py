import os
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

import unittest
from unittest.mock import patch
import numpy as np
import pygame
from turbulent_flow import Game


class UITests(unittest.TestCase):
    def setUp(self):
        self.game = Game(grid=16, size=320, seed=1)
        pygame.event.clear()

    def tearDown(self):
        self.game.close()

    def post(self, event_type, **attributes):
        pygame.event.post(pygame.event.Event(event_type, **attributes))

    def test_pause_freezes_simulation(self):
        self.game.frame(1 / 30)
        before = self.game.fluid.density.copy()
        self.post(pygame.KEYDOWN, key=pygame.K_SPACE)
        self.game.frame(0.2)
        np.testing.assert_array_equal(self.game.fluid.density, before)
        self.assertTrue(self.game.paused)

    def test_stopped_emitter_does_not_inject(self):
        self.post(pygame.KEYDOWN, key=pygame.K_s)
        self.game.frame(1 / 30)
        np.testing.assert_array_equal(self.game.fluid.density, 0)
        self.assertFalse(self.game.emitting)

    def test_arrow_source_movement_is_clamped(self):
        for _ in range(10):
            self.post(pygame.KEYDOWN, key=pygame.K_RIGHT, mod=pygame.KMOD_SHIFT)
        self.game.frame(0)
        self.assertEqual(self.game.source_x, 14)
        for _ in range(10):
            self.post(pygame.KEYDOWN, key=pygame.K_UP, mod=pygame.KMOD_SHIFT)
        self.game.frame(0)
        self.assertEqual(self.game.source_y, 2)

    def test_click_sets_persistent_emitter_direction(self):
        self.post(pygame.MOUSEBUTTONDOWN, button=1, pos=(200, 80))
        self.game.frame(0)
        jet = self.game.jet
        self.assertFalse(self.game.sweep)
        for _ in range(3):
            self.game.frame(1 / 30)
        self.assertEqual(self.game.jet, jet)

    def test_hue_slider_cannot_inject_into_grid(self):
        self.post(pygame.KEYDOWN, key=pygame.K_s)
        self.post(pygame.MOUSEBUTTONDOWN, button=1, pos=(50, 370))
        self.post(pygame.MOUSEMOTION, pos=(1000, 370))
        self.game.frame(1 / 30)
        self.assertEqual(self.game.hue, 1)
        np.testing.assert_array_equal(self.game.fluid.density, 0)
        self.post(pygame.WINDOWFOCUSLOST)
        self.game.frame(0)
        self.assertFalse(self.game.dragging_hue)

    def test_right_drag_paints_dye(self):
        self.game.emitting = False
        self.post(pygame.MOUSEBUTTONDOWN, button=3, pos=(160, 160))
        self.game.frame(1 / 30)
        self.assertGreater(self.game.fluid.density.max(), 0)
        self.post(pygame.WINDOWFOCUSLOST)
        self.game.frame(0)
        self.assertFalse(self.game.painting)

    def test_render_rate_does_not_change_simulation(self):
        for _ in range(60):
            self.game.frame(1 / 60)
        expected = self.game.fluid.density.copy()
        self.game.reset()
        for _ in range(30):
            self.game.frame(1 / 30)
        np.testing.assert_allclose(self.game.fluid.density, expected)

    def test_reset_and_blocky_toggle(self):
        self.game.frame(1 / 30)
        self.post(pygame.KEYDOWN, key=pygame.K_b)
        self.post(pygame.KEYDOWN, key=pygame.K_r)
        self.game.frame(0)
        self.assertFalse(self.game.smooth)
        np.testing.assert_array_equal(self.game.fluid.density, 0)

    def test_quit_does_not_render(self):
        self.post(pygame.QUIT)
        with patch.object(self.game, 'render') as render:
            self.assertFalse(self.game.frame(1 / 30))
            render.assert_not_called()
