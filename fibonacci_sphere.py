"""Rotate a rainbow Fibonacci sphere with Pygame."""

import argparse
import math
import pygame

from sphere_model import Sphere


class Game:
    def __init__(self, samples=100, size=(1280, 720), fullscreen=False):
        self.closed = False
        pygame.display.init()
        try:
            if fullscreen:
                size = pygame.display.get_desktop_sizes()[0]
            if min(size) < 240:
                raise ValueError('Use a window of at least 240×240')
            self.screen = pygame.display.set_mode(size, pygame.FULLSCREEN if fullscreen else 0)
            pygame.display.set_caption('Fibonacci Sphere')
            self.sphere = Sphere(samples)
            self.edge_indices = self.sphere.edges.tolist()
            self.clock = pygame.time.Clock()
            self.running = True
            self.reset()
        except Exception:
            self.close()
            raise

    def reset(self):
        self.angles = [0.0, 0.0, 0.0]
        self.zoom = min(300, min(self.screen.get_size()) * 0.42)
        self.auto = False
        self.show_lines = True
        self.dragging = False
        self.last_mouse = None
        self.dirty = True

    def zoom_by(self, steps):
        maximum = min(self.screen.get_size()) * 4
        self.zoom = max(20, min(maximum, self.zoom + 5 * steps))
        self.dirty = True

    def drag_to(self, position):
        if self.last_mouse is not None:
            dx, dy = position[0] - self.last_mouse[0], position[1] - self.last_mouse[1]
            self.angles[0] = (self.angles[0] + dy / 100) % math.tau
            self.angles[1] = (self.angles[1] + dx / 100) % math.tau
            self.dirty = True
        self.last_mouse = position

    def events(self):
        events = pygame.event.get()
        modern_wheel = any(event.type == pygame.MOUSEWHEEL for event in events)
        for event in events:
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN and not getattr(event, 'repeat', False):
                if event.key in (pygame.K_ESCAPE, pygame.K_F1):
                    self.running = False
                elif event.key in (pygame.K_LCTRL, pygame.K_RCTRL, pygame.K_SPACE):
                    self.auto = not self.auto
                elif event.key == pygame.K_l:
                    self.show_lines = not self.show_lines
                    self.dirty = True
                elif event.key == pygame.K_r:
                    self.reset()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    self.dragging = True
                    self.last_mouse = event.pos
                elif event.button in (4, 5) and not modern_wheel:
                    self.zoom_by(1 if event.button == 4 else -1)
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if self.dragging:
                    self.drag_to(event.pos)
                self.dragging = False
                self.last_mouse = None
            elif event.type == pygame.MOUSEMOTION and self.dragging:
                self.drag_to(event.pos)
            elif event.type == pygame.MOUSEWHEEL:
                self.zoom_by(getattr(event, 'precise_y', event.y))
            elif event.type in (pygame.WINDOWFOCUSLOST, pygame.WINDOWLEAVE):
                self.dragging = False
                self.last_mouse = None
            elif event.type in (pygame.WINDOWEXPOSED, pygame.WINDOWSHOWN):
                self.dirty = True

    def render(self):
        self.screen.fill((0, 0, 0))
        width, height = self.screen.get_size()
        projected = self.sphere.project(self.angles, self.zoom, (width / 2, height / 2)).tolist()
        if self.show_lines:
            for (i, j), color in zip(self.edge_indices, self.sphere.edge_colors):
                pygame.draw.aaline(self.screen, color, projected[i], projected[j])
        radius = max(1, min(8, round(self.zoom / 150)))
        for position, color in zip(projected, self.sphere.point_colors):
            pygame.draw.circle(self.screen, color, position, radius)

    def frame(self, elapsed):
        self.events()
        if not self.running:
            return False
        if self.auto:
            self.angles[1] = (self.angles[1] + min(max(elapsed, 0), 0.25) * 0.6) % math.tau
            self.dirty = True
        if self.dirty:
            self.render()
            pygame.display.flip()
            self.dirty = False
        return True

    def run(self):
        while self.frame(self.clock.tick(60) / 1000):
            pass

    def close(self):
        if not self.closed:
            self.closed = True
            pygame.quit()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--points', type=int, default=100)
    parser.add_argument('--size', type=int, nargs=2, default=(1280, 720), metavar=('WIDTH', 'HEIGHT'))
    parser.add_argument('--fullscreen', action='store_true')
    args = parser.parse_args()
    game = None
    try:
        game = Game(args.points, args.size, args.fullscreen)
        game.run()
    except (ValueError, pygame.error) as error:
        parser.exit(1, f'Cannot start: {error}\n')
    finally:
        if game is not None:
            game.close()


if __name__ == '__main__':
    main()
