"""Batched version of the original follow-and-anchor chain solver."""

from dataclasses import dataclass
import math
import numpy as np


@dataclass(frozen=True)
class Settings:
    chains: int = 16
    segments: int = 32
    length: int = 12

    def __post_init__(self):
        for value, maximum in ((self.chains, 50), (self.segments, 100), (self.length, 100)):
            if type(value) is not int or not 1 <= value <= maximum:
                raise ValueError('Use 1–50 chains, 1–100 segments, and length 1–100')


class ArmField:
    def __init__(self, size, settings=Settings()):
        self.settings = settings
        width, height = size
        if not all(math.isfinite(value) and value > 0 for value in size):
            raise ValueError('Field dimensions must be positive and finite')
        angle = np.arange(settings.chains) * (2 * math.pi / settings.chains)
        radial = np.column_stack((np.cos(angle), np.sin(angle)))
        center = np.array((width / 2, height / 2))
        self.bases = center + radial * (0.42 * min(size))
        self.points = (self.bases[:, None, :] - radial[:, None, :]
                       * np.arange(settings.segments + 1)[None, :, None] * settings.length)
        self.directions = np.diff(self.points, axis=1)
        self.delta = np.empty((settings.chains, 2))
        self.distance = np.empty(settings.chains)
        self.scale = np.zeros(settings.chains)

    def update(self, target, anchored=True):
        target = np.asarray(target, dtype=np.float64)
        if target.shape != (2,) or not np.isfinite(target).all():
            raise ValueError('Target must contain two finite coordinates')
        self.points[:, -1] = target
        for i in range(self.settings.segments - 1, -1, -1):
            np.subtract(self.points[:, i], self.points[:, i + 1], out=self.delta)
            np.hypot(self.delta[:, 0], self.delta[:, 1], out=self.distance)
            coincident = self.distance < 1e-12
            np.divide(self.settings.length, self.distance, out=self.scale, where=~coincident)
            self.delta *= self.scale[:, None]
            # Keep the previous direction when a joint and target coincide.
            self.delta[coincident] = -self.directions[coincident, i]
            np.add(self.points[:, i + 1], self.delta, out=self.points[:, i])
            self.directions[:, i] = -self.delta
        if anchored:
            self.points[:, 0] = self.bases
            np.cumsum(self.directions, axis=1, out=self.points[:, 1:])
            self.points[:, 1:] += self.bases[:, None, :]


@dataclass
class Ball:
    x: float = 30
    y: float = 30
    vx: float = 5 / 0.03
    vy: float = 5 / 0.03
    radius: int = 30

    def drag(self, point, size):
        self.x = max(self.radius, min(point[0], size[0] - self.radius))
        self.y = max(self.radius, min(point[1], size[1] - self.radius))

    def update(self, dt, size):
        if not math.isfinite(dt) or dt < 0:
            raise ValueError('dt must be finite and nonnegative')
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += (0.1 / 0.03 ** 2) * dt
        if self.x < self.radius:
            self.x, self.vx = self.radius, abs(self.vx)
        elif self.x > size[0] - self.radius:
            self.x, self.vx = size[0] - self.radius, -abs(self.vx)
        if self.y < self.radius:
            self.y, self.vy = self.radius, abs(self.vy)
        elif self.y > size[1] - self.radius:
            self.y = size[1] - self.radius
            self.vy = -abs(self.vy) * 0.95
            self.vx *= 0.95
