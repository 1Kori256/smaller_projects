"""Measure Fibonacci-sphere rendering, without display updates or the frame cap."""

import argparse
import json
import os
from pathlib import Path
import statistics
import sys
import time

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
os.environ.setdefault('PYGAME_HIDE_SUPPORT_PROMPT', '1')
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pygame
from fibonacci_sphere import Game


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--points', type=int, default=100)
    parser.add_argument('--frames', type=int, default=600)
    parser.add_argument('--preview', type=Path)
    args = parser.parse_args()
    if args.frames < 1:
        parser.error('--frames must be positive')
    game = Game(args.points)
    try:
        samples = []
        for frame in range(args.frames + 30):
            game.angles = (0.35, frame * 0.01, 0.1)
            start = time.perf_counter()
            game.render()
            if frame >= 30:
                samples.append((time.perf_counter() - start) * 1000)
        if args.preview:
            game.angles = (0.35, 0.6, 0)
            game.render()
            args.preview.parent.mkdir(parents=True, exist_ok=True)
            pygame.image.save(game.screen, str(args.preview))
        print(json.dumps({'points': args.points, 'connections': len(game.edge_indices),
                          'frames': args.frames, 'render_median_ms': round(statistics.median(samples), 3)}, indent=2))
    finally:
        game.close()


if __name__ == '__main__':
    main()
