import os
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

import math
import unittest
from unittest.mock import patch
import numpy as np
import pygame
from fibonacci_sphere import Game


class UITests(unittest.TestCase):
    def setUp(self):
        self.game = Game(size=(960, 600))
        pygame.event.clear()

    def tearDown(self):
        self.game.close()

    def post(self, event_type, **attributes):
        pygame.event.post(pygame.event.Event(event_type, **attributes))

    def test_first_drag_does_not_jump(self):
        self.post(pygame.MOUSEBUTTONDOWN, button=1, pos=(800, 500))
        self.post(pygame.MOUSEMOTION, pos=(805, 503))
        self.game.frame(0)
        np.testing.assert_allclose(self.game.angles, (0.03, 0.05, 0))
        self.post(pygame.MOUSEMOTION, pos=(600, 300))
        self.game.frame(0)
        np.testing.assert_allclose(self.game.angles, ((0.03 - 2.03) % math.tau, (0.05 - 2.05) % math.tau, 0))

    def test_release_and_focus_loss_stop_dragging(self):
        for release in (pygame.MOUSEBUTTONUP, pygame.WINDOWFOCUSLOST):
            self.post(pygame.MOUSEBUTTONDOWN, button=1, pos=(300, 200))
            attrs = {'button': 1, 'pos': (300, 200)} if release == pygame.MOUSEBUTTONUP else {}
            self.post(release, **attrs)
            self.game.frame(0)
            self.assertFalse(self.game.dragging)
            angles = self.game.angles.copy()
            self.post(pygame.MOUSEMOTION, pos=(0, 0))
            self.game.frame(0)
            self.assertEqual(self.game.angles, angles)

    def test_first_control_press_toggles_auto_and_repeats_are_ignored(self):
        self.post(pygame.KEYDOWN, key=pygame.K_LCTRL)
        self.game.frame(1 / 60)
        self.assertTrue(self.game.auto)
        self.assertAlmostEqual(self.game.angles[1], 0.01)
        self.post(pygame.KEYDOWN, key=pygame.K_LCTRL, repeat=True)
        self.game.frame(1 / 60)
        self.assertTrue(self.game.auto)
        self.post(pygame.KEYDOWN, key=pygame.K_SPACE)
        self.game.frame(0)
        self.assertFalse(self.game.auto)

    def test_auto_speed_is_independent_of_frame_rate(self):
        self.game.auto = True
        for _ in range(60):
            self.game.frame(1 / 60)
        expected = self.game.angles.copy()
        self.game.reset()
        self.game.auto = True
        for _ in range(30):
            self.game.frame(1 / 30)
        np.testing.assert_allclose(self.game.angles, expected)

    def test_modern_and_legacy_wheel_are_not_applied_twice(self):
        before = self.game.zoom
        self.post(pygame.MOUSEBUTTONDOWN, button=4, pos=(0, 0))
        self.post(pygame.MOUSEWHEEL, y=1, x=0)
        self.game.frame(0)
        self.assertEqual(self.game.zoom, before + 5)
        self.post(pygame.MOUSEWHEEL, y=1, x=0, precise_y=0.25)
        self.game.frame(0)
        self.assertEqual(self.game.zoom, before + 6.25)

    def test_zoom_never_reaches_zero_or_negative_scale(self):
        self.game.zoom_by(-100000)
        self.game.frame(0)
        self.assertEqual(self.game.zoom, 20)
        self.game.zoom_by(100000)
        self.game.frame(0)
        self.assertEqual(self.game.zoom, 2400)

    def test_lines_toggle_and_reset(self):
        self.post(pygame.KEYDOWN, key=pygame.K_l)
        self.game.frame(0)
        self.assertFalse(self.game.show_lines)
        self.game.zoom_by(20)
        self.post(pygame.KEYDOWN, key=pygame.K_r)
        self.game.frame(0)
        self.assertTrue(self.game.show_lines)
        self.assertEqual(self.game.angles, [0, 0, 0])
        self.assertEqual(self.game.zoom, 252)

    def test_static_scene_does_not_redraw(self):
        self.game.frame(0)
        with patch.object(self.game, 'render') as render:
            self.game.frame(0)
            render.assert_not_called()
        self.post(pygame.WINDOWEXPOSED)
        with patch.object(self.game, 'render') as render:
            self.game.frame(0)
            render.assert_called_once()

    def test_quit_does_not_render_again(self):
        self.post(pygame.QUIT)
        with patch.object(self.game, 'render') as render:
            self.assertFalse(self.game.frame(0))
            render.assert_not_called()
