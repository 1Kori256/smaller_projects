"""Measure inverse-kinematics update/draw work without the display or frame cap."""

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
from ik_model import Settings
from inverse_kinematics import Game


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--frames', type=int, default=300)
    parser.add_argument('--chains', type=int, default=16)
    parser.add_argument('--segments', type=int, default=32)
    parser.add_argument('--length', type=int, default=12)
    parser.add_argument('--preview', type=Path)
    args = parser.parse_args()
    if args.frames < 1:
        parser.error('--frames must be positive')
    settings = Settings(args.chains, args.segments, args.length)
    game = Game(settings=settings)
    try:
        update, draw = [], []
        for frame in range(args.frames + 30):
            start = time.perf_counter()
            game.update()
            middle = time.perf_counter()
            game.render()
            end = time.perf_counter()
            if frame >= 30:
                update.append((middle - start) * 1000)
                draw.append((end - middle) * 1000)
        if args.preview:
            args.preview.parent.mkdir(parents=True, exist_ok=True)
            pygame.image.save(game.screen, str(args.preview))
        print(json.dumps({'chains': args.chains, 'segments': args.segments,
                          'frames': args.frames, 'update_median_ms': round(statistics.median(update), 3),
                          'draw_median_ms': round(statistics.median(draw), 3)}, indent=2))
    finally:
        game.close()


if __name__ == '__main__':
    main()
