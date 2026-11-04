"""Vectorized two-dimensional stable-fluid steps with bounded advection."""

import math
import numpy as np


class Fluid:
    def __init__(self, size=45, dt=0.1, diffusion=0, viscosity=1e-7, iterations=20):
        if type(size) is not int or not 8 <= size <= 256:
            raise ValueError('Grid size must be between 8 and 256')
        if type(iterations) is not int or iterations < 1:
            raise ValueError('Use at least one solver iteration')
        if not all(math.isfinite(value) for value in (dt, diffusion, viscosity)) or dt <= 0 or min(diffusion, viscosity) < 0:
            raise ValueError('Use a positive time step and nonnegative diffusion/viscosity')
        self.size, self.dt = size, dt
        self.diffusion, self.viscosity, self.iterations = diffusion, viscosity, iterations
        self.density, self.s, self.vx, self.vy, self.vx0, self.vy0, self.pressure, self.divergence, self.work = (
            np.zeros((size, size)) for _ in range(9))
        self.grid_x, self.grid_y = np.meshgrid(np.arange(1, size - 1), np.arange(1, size - 1))

    def source(self, x, y, density=0, vx=0, vy=0):
        if not (isinstance(x, (int, np.integer)) and isinstance(y, (int, np.integer))
                and 1 <= x < self.size - 1 and 1 <= y < self.size - 1):
            raise ValueError('Sources must be inside the grid boundary')
        if not all(math.isfinite(value) for value in (density, vx, vy)) or density < 0:
            raise ValueError('Use finite source values and nonnegative density')
        self.density[y, x] += density
        self.vx[y, x] += vx
        self.vy[y, x] += vy

    def boundary(self, component, field):
        field[0, 1:-1] = (-1 if component == 2 else 1) * field[1, 1:-1]
        field[-1, 1:-1] = (-1 if component == 2 else 1) * field[-2, 1:-1]
        field[1:-1, 0] = (-1 if component == 1 else 1) * field[1:-1, 1]
        field[1:-1, -1] = (-1 if component == 1 else 1) * field[1:-1, -2]
        field[0, 0] = 0.5 * (field[0, 1] + field[1, 0])
        field[0, -1] = 0.5 * (field[0, -2] + field[1, -1])
        field[-1, 0] = 0.5 * (field[-1, 1] + field[-2, 0])
        field[-1, -1] = 0.5 * (field[-1, -2] + field[-2, -1])

    def linear_solve(self, component, field, source, a, c):
        if a == 0:
            np.copyto(field, source)
            self.boundary(component, field)
            return
        # Jacobi passes update the whole grid together, avoiding Python cell loops.
        for _ in range(self.iterations):
            self.work[1:-1, 1:-1] = (source[1:-1, 1:-1] + a * (
                field[1:-1, 2:] + field[1:-1, :-2] + field[2:, 1:-1] + field[:-2, 1:-1])) / c
            self.boundary(component, self.work)
            np.copyto(field, self.work)

    def diffuse(self, component, field, source, amount):
        a = self.dt * amount * (self.size - 2) ** 2
        self.linear_solve(component, field, source, a, 1 + 4 * a)

    def project(self, vx, vy):
        p, div = self.pressure, self.divergence
        p.fill(0)
        div.fill(0)
        div[1:-1, 1:-1] = -0.5 * (
            vx[1:-1, 2:] - vx[1:-1, :-2] + vy[2:, 1:-1] - vy[:-2, 1:-1]) / self.size
        self.boundary(0, p)
        self.boundary(0, div)
        self.linear_solve(0, p, div, 1, 4)
        vx[1:-1, 1:-1] -= 0.5 * self.size * (p[1:-1, 2:] - p[1:-1, :-2])
        vy[1:-1, 1:-1] -= 0.5 * self.size * (p[2:, 1:-1] - p[:-2, 1:-1])
        self.boundary(1, vx)
        self.boundary(2, vy)

    def advect(self, component, field, source, vx, vy):
        factor = self.dt * (self.size - 2)
        # Bilinear samples need both floor(p) and floor(p)+1 inside the array.
        x = np.clip(self.grid_x - factor * vx[1:-1, 1:-1], 0.5, self.size - 1.5)
        y = np.clip(self.grid_y - factor * vy[1:-1, 1:-1], 0.5, self.size - 1.5)
        x0, y0 = x.astype(np.intp), y.astype(np.intp)
        sx, sy = x - x0, y - y0
        field[1:-1, 1:-1] = (
            (1 - sx) * ((1 - sy) * source[y0, x0] + sy * source[y0 + 1, x0])
            + sx * ((1 - sy) * source[y0, x0 + 1] + sy * source[y0 + 1, x0 + 1]))
        self.boundary(component, field)

    def step(self):
        self.diffuse(1, self.vx0, self.vx, self.viscosity)
        self.diffuse(2, self.vy0, self.vy, self.viscosity)
        self.project(self.vx0, self.vy0)
        self.advect(1, self.vx, self.vx0, self.vx0, self.vy0)
        self.advect(2, self.vy, self.vy0, self.vx0, self.vy0)
        self.project(self.vx, self.vy)
        self.diffuse(0, self.s, self.density, self.diffusion)
        self.advect(0, self.density, self.s, self.vx, self.vy)
        np.maximum(self.density - 1, 0, out=self.density)
