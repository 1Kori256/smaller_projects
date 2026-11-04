"""Pygame dye flow with a movable emitter and a hue slider."""

import argparse
import colorsys
import math
import random
import numpy as np
import pygame

from fluid_model import Fluid

FIXED_STEP = 1 / 30


class Game:
    def __init__(self, grid=45, size=640, seed=None):
        self.closed = False
        pygame.display.init()
        try:
            if not 320 <= size <= 1600:
                raise ValueError('Use a playfield size between 320 and 1600')
            self.size, self.grid, self.seed = size, grid, seed
            self.hue = 0.55
            self.smooth = True
            self.reset()
            self.screen = pygame.display.set_mode((size, size + 100))
            self.field_surface = self.screen.subsurface((0, 0, size, size))
            self.grid_surface = pygame.Surface((grid, grid)).convert()
            self.panel = pygame.Surface((size, 100)).convert()
            self.panel.fill((0, 0, 0))
            pygame.draw.line(self.panel, (255, 255, 255), (0, 0), (size, 0))
            for x in range(50, size - 49):
                color = tuple(round(channel * 255) for channel in colorsys.hsv_to_rgb((x - 50) / (size - 100), 0.9, 0.9))
                pygame.draw.line(self.panel, color, (x, 49), (x, 51))
            for x in (50, size - 50):
                pygame.draw.line(self.panel, (230, 23, 23), (x, 30), (x, 70))
            self.clock = pygame.time.Clock()
            self.running = True
        except Exception:
            self.close()
            raise

    def reset(self):
        self.fluid = Fluid(self.grid)
        self.rng = random.Random(self.seed)
        self.source_x, self.source_y = 3, self.grid // 2
        self.angle = 0
        self.jet = (self.grid / 8, 0)
        self.emitting = self.sweep = True
        self.paused = False
        self.painting = self.dragging_hue = False
        self.brush = None
        self.brush_velocity = (0, 0)
        self.accumulator = 0
        self.caption = None

    def cell(self, point):
        return tuple(max(1, min(self.grid - 2, int(coordinate * self.grid / self.size))) for coordinate in point)

    def set_hue(self, x):
        self.hue = max(0, min(1, (x - 50) / (self.size - 100)))

    def events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_F1):
                    self.running = False
                elif event.key in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP, pygame.K_DOWN):
                    amount = 10 if getattr(event, 'mod', 0) & pygame.KMOD_SHIFT else 1
                    self.source_x += amount * ((event.key == pygame.K_RIGHT) - (event.key == pygame.K_LEFT))
                    self.source_y += amount * ((event.key == pygame.K_DOWN) - (event.key == pygame.K_UP))
                    self.source_x = max(2, min(self.grid - 2, self.source_x))
                    self.source_y = max(2, min(self.grid - 2, self.source_y))
                elif not getattr(event, 'repeat', False):
                    if event.key == pygame.K_s:
                        self.emitting = not self.emitting
                    elif event.key == pygame.K_SPACE:
                        self.paused = not self.paused
                    elif event.key == pygame.K_a:
                        self.sweep = not self.sweep
                    elif event.key == pygame.K_b:
                        self.smooth = not self.smooth
                    elif event.key == pygame.K_r:
                        self.reset()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    self.dragging_hue = event.pos[1] >= self.size
                    if self.dragging_hue:
                        self.set_hue(event.pos[0])
                    else:
                        x, y = self.cell(event.pos)
                        self.jet = ((x - self.source_x) / 4, (y - self.source_y) / 4)
                        self.sweep = False
                elif event.button == 3 and event.pos[1] < self.size:
                    self.painting = True
                    self.brush = event.pos
            elif event.type == pygame.MOUSEMOTION:
                if self.dragging_hue:
                    self.set_hue(event.pos[0])
                if self.painting:
                    dx, dy = event.pos[0] - self.brush[0], event.pos[1] - self.brush[1]
                    self.brush_velocity = (max(-20, min(20, dx / 10)), max(-20, min(20, dy / 10)))
                    self.brush = event.pos
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    self.dragging_hue = False
                elif event.button == 3:
                    self.painting = False
                    self.brush_velocity = (0, 0)
            elif event.type in (pygame.WINDOWFOCUSLOST, pygame.WINDOWLEAVE):
                self.painting = self.dragging_hue = False
                self.brush_velocity = (0, 0)

    def update(self):
        if self.emitting:
            if self.sweep:
                self.angle = max(-90, min(90, self.angle + self.rng.uniform(-5, 5)))
                self.jet = (math.cos(math.radians(self.angle)) * self.grid / 8,
                            math.sin(math.radians(self.angle)) * self.grid / 8)
            self.fluid.source(self.source_x, self.source_y, 2500, *self.jet)
        if self.painting and self.brush is not None and 0 <= self.brush[1] < self.size:
            self.fluid.source(*self.cell(self.brush), 500, *self.brush_velocity)
            self.brush_velocity = (0, 0)
        self.fluid.step()

    def render(self):
        base = np.array(colorsys.hsv_to_rgb(self.hue, 0.9, 1))
        brightness = 0.9 * np.sqrt(np.clip(self.fluid.density, 0, 900) / 900)
        rgb = np.rint(brightness[:, :, None] * base * 256).astype('uint8')
        pygame.surfarray.blit_array(self.grid_surface, rgb.swapaxes(0, 1))
        scale = pygame.transform.smoothscale if self.smooth else pygame.transform.scale
        scale(self.grid_surface, (self.size, self.size), self.field_surface)
        self.screen.blit(self.panel, (0, self.size))
        color = tuple(round(channel * 255) for channel in colorsys.hsv_to_rgb(self.hue, 0.9, 0.9))
        knob = (round(50 + self.hue * (self.size - 100)), self.size + 50)
        pygame.draw.circle(self.screen, color, knob, 10)
        pygame.draw.circle(self.screen, (255, 255, 255), knob, 10, 1)
        source = (round((self.source_x + 0.5) * self.size / self.grid),
                  round((self.source_y + 0.5) * self.size / self.grid))
        pygame.draw.circle(self.screen, (255, 255, 255), source, 4, 1)
        caption = 'Turbulent Flow' + (' — paused' if self.paused else '') + (' — emitter off' if not self.emitting else '')
        if caption != self.caption:
            pygame.display.set_caption(caption)
            self.caption = caption

    def frame(self, elapsed):
        self.events()
        if not self.running:
            return False
        if not self.paused:
            self.accumulator += min(max(elapsed, 0), 0.25)
            while self.accumulator + 1e-12 >= FIXED_STEP:
                self.update()
                self.accumulator -= FIXED_STEP
        self.render()
        pygame.display.flip()
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
    parser.add_argument('--grid', type=int, default=45)
    parser.add_argument('--size', type=int, default=640)
    parser.add_argument('--seed', type=int)
    args = parser.parse_args()
    game = None
    try:
        game = Game(args.grid, args.size, args.seed)
        game.run()
    except (ValueError, pygame.error) as error:
        parser.exit(1, f'Cannot start: {error}\n')
    finally:
        if game is not None:
            game.close()


if __name__ == '__main__':
    main()
