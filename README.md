# Smaller projects

A few visual experiments in Python.

| Demo | UI | Description |
| --- | --- | --- |
| [Inverse kinematics](inverse_kinematics.py) | Pygame | Rainbow chains following a draggable, bouncing ball |
| [Fibonacci sphere](fibonacci_sphere.py) | Tkinter | Points distributed over a rotating sphere |
| [Turbulent flow](turbulent_flow.py) | Tkinter | Interactive fluid simulation |

## Inverse kinematics

![Inverse kinematics preview](docs/inverse_kinematics.png)

Requires Python 3.10+.

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python inverse_kinematics.py
```

On Windows, activate with `.venv\Scripts\activate`.

- Drag anywhere in the playfield to hold and move the ball; release to resume bouncing.
- Drag the three sliders to change chain count, segments per chain, and segment length.
- Click **ANCHOR** to pin roots to the circle or let the chains follow freely.
- **R** resets the ball and chains with the current settings. **Escape/F1** exits.

The default scene has 16 chains with 32 segments of length 12. Window and starting
values can be set from the command line:

```sh
python inverse_kinematics.py --size 1280 720 --chains 50 --segments 100 --length 10
python inverse_kinematics.py --fullscreen
```

## Performance

Inverse kinematics uses Pygame instead of Tkinter. The original follow-and-anchor
solver is batched across chains with NumPy, replacing repeated angle calculations
with vector normalization. Coincident joints keep their previous direction.
Anchors fit the playfield, sliders rebuild chains only when values change, and
static controls and text are cached. Simulation runs at 60 fixed steps per second.

For 50 chains × 100 segments, local solver time fell from about 5.2 ms to 0.89 ms.
The new update/draw path took about 2.8 ms, excluding display updates and the frame
cap. The original rainbow colors, black background, ball, and chain behavior remain.

```sh
python -m unittest discover -s tests -v
python tools/benchmark_ik.py --chains 50 --segments 100 --length 10
python tools/benchmark_ik.py --preview docs/inverse_kinematics.png
```

Tests and the benchmark run headlessly. Checks cover segment lengths, anchor and
target positions, coincident joints, ball bounds, dragging, sliders, and frame-rate
independence. The preview is rendered by the application.
