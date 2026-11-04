"""Rainbow inverse-kinematics chains, drawn with Pygame."""

import argparse
import colorsys
from functools import lru_cache
import pygame

from ik_model import ArmField, Ball, Settings

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
FIXED_STEP = 1 / 60


@lru_cache(maxsize=128)
def text(font, label):
    return font.render(str(label), True, WHITE)


class Slider:
    def __init__(self, label, x, top, bottom, maximum, value):
        self.label = label
        self.x, self.top, self.bottom = x, top, bottom
        self.maximum, self.value = maximum, value
        self.hitbox = pygame.Rect(x - 35, top - 20, 70, bottom - top + 40)

    @property
    def y(self):
        return round(self.top + (self.value - 1) / (self.maximum - 1) * (self.bottom - self.top))

    def set_from_y(self, y):
        fraction = max(0, min(1, (y - self.top) / (self.bottom - self.top)))
        self.value = round(1 + fraction * (self.maximum - 1))


class Game:
    def __init__(self, size=(1280, 720), settings=Settings(), fullscreen=False):
        self.closed = False
        pygame.display.init()
        pygame.font.init()
        try:
            size = pygame.display.get_desktop_sizes()[0] if fullscreen else size
            if size[0] < 800 or size[1] < 480:
                raise ValueError('Use a window of at least 800×480')
            self.screen = pygame.display.set_mode(size, pygame.FULLSCREEN if fullscreen else 0)
            pygame.display.set_caption('Inverse Kinematics')
            self.width, self.height = self.screen.get_size()
            self.panel_width = max(280, min(360, self.width // 4))
            self.field_size = (self.width - self.panel_width, self.height)
            self.field_rect = pygame.Rect((0, 0), self.field_size)
            self.toggle_rect = pygame.Rect(self.field_size[0], 0, self.panel_width, 100)
            self.font = pygame.font.Font(None, 24)
            self.title_font = pygame.font.Font(None, 32)
            self.settings = settings
            self.sliders = [Slider(label, self.field_size[0] + round(self.panel_width * fraction),
                                   150, self.height - 150, maximum, value)
                            for label, fraction, maximum, value in
                            (('Chains', 0.2, 50, settings.chains),
                             ('Segments', 0.5, 100, settings.segments),
                             ('Length', 0.8, 100, settings.length))]
            self.panel = pygame.Surface(self.screen.get_size()).convert()
            self.panel.fill(BLACK)
            pygame.draw.line(self.panel, WHITE, (self.field_size[0], 0), (self.field_size[0], self.height))
            pygame.draw.line(self.panel, WHITE, (self.field_size[0], 100), (self.width, 100))
            for slider in self.sliders:
                pygame.draw.line(self.panel, WHITE, (slider.x, slider.top), (slider.x, slider.bottom), 2)
                for y in (slider.top, slider.bottom):
                    pygame.draw.line(self.panel, WHITE, (slider.x - 20, y), (slider.x + 20, y), 2)
                label = text(self.font, slider.label)
                self.panel.blit(label, label.get_rect(center=(slider.x, 125)))
            hint = text(self.font, 'Drag ball · R reset · Esc exit')
            self.panel.blit(hint, hint.get_rect(center=(self.toggle_rect.centerx, self.height - 25)))
            self.anchored = True
            self.dragging_ball = False
            self.dragging_slider = None
            self.running = True
            self.accumulator = 0
            self.clock = pygame.time.Clock()
            self.reset()
        except Exception:
            self.close()
            raise

    def configure(self, settings):
        self.settings = settings
        self.field = ArmField(self.field_size, settings)
        # The original segment order runs from the red tip back to the root.
        self.colors = [tuple(round(channel * 255) for channel in
                             colorsys.hsv_to_rgb(i / settings.segments, 0.9, 0.9))
                       for i in reversed(range(settings.segments))]

    def reset(self):
        self.ball = Ball()
        self.configure(self.settings)
        self.dragging_ball = False
        self.dragging_slider = None

    def events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_F1):
                    self.running = False
                elif event.key == pygame.K_r:
                    self.reset()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.dragging_ball = False
                self.dragging_slider = None
                if self.toggle_rect.collidepoint(event.pos):
                    self.anchored = not self.anchored
                elif self.field_rect.collidepoint(event.pos):
                    self.dragging_ball = True
                    self.ball.drag(event.pos, self.field_size)
                else:
                    self.dragging_slider = next(
                        (slider for slider in self.sliders if slider.hitbox.collidepoint(event.pos)), None)
                    if self.dragging_slider is not None:
                        self.dragging_slider.set_from_y(event.pos[1])
            elif event.type == pygame.MOUSEMOTION:
                if self.dragging_ball:
                    self.ball.drag(event.pos, self.field_size)
                elif self.dragging_slider is not None:
                    self.dragging_slider.set_from_y(event.pos[1])
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if self.dragging_ball:
                    self.ball.drag(event.pos, self.field_size)
                elif self.dragging_slider is not None:
                    self.dragging_slider.set_from_y(event.pos[1])
                self.dragging_ball = False
                self.dragging_slider = None
            elif event.type in (pygame.WINDOWFOCUSLOST, pygame.WINDOWLEAVE):
                self.dragging_ball = False
                self.dragging_slider = None
        settings = Settings(*(slider.value for slider in self.sliders))
        if settings != self.settings:
            self.configure(settings)

    def update(self):
        if not self.dragging_ball:
            self.ball.update(FIXED_STEP, self.field_size)
        self.field.update((self.ball.x, self.ball.y), self.anchored)

    def render(self):
        self.screen.blit(self.panel, (0, 0))
        self.screen.set_clip(self.field_rect)
        for points in self.field.points.round().astype('int32').tolist():
            for color, start, end in zip(self.colors, points, points[1:]):
                pygame.draw.line(self.screen, color, start, end, 5)
        pygame.draw.circle(self.screen, WHITE, (round(self.ball.x), round(self.ball.y)), self.ball.radius)
        self.screen.set_clip(None)
        title = text(self.title_font, 'ANCHOR: ON' if self.anchored else 'ANCHOR: OFF')
        self.screen.blit(title, title.get_rect(center=self.toggle_rect.center))
        for slider in self.sliders:
            pygame.draw.circle(self.screen, WHITE, (slider.x, slider.y), 10)
            label = text(self.font, slider.value)
            self.screen.blit(label, label.get_rect(center=(slider.x, self.height - 90)))

    def frame(self, elapsed):
        self.events()
        if not self.running:
            return False
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
    parser.add_argument('--size', type=int, nargs=2, default=(1280, 720), metavar=('WIDTH', 'HEIGHT'))
    parser.add_argument('--fullscreen', action='store_true')
    parser.add_argument('--chains', type=int, default=16)
    parser.add_argument('--segments', type=int, default=32)
    parser.add_argument('--length', type=int, default=12)
    args = parser.parse_args()
    game = None
    try:
        game = Game(args.size, Settings(args.chains, args.segments, args.length), args.fullscreen)
        game.run()
    except (ValueError, pygame.error) as error:
        parser.exit(1, f'Cannot start: {error}\n')
    finally:
        if game is not None:
            game.close()


if __name__ == '__main__':
    main()
