# ME206 – Interactive Two-Body Gravitational Simulator (Assignment 4)

An interactive two-body orbital dynamics simulator solved in the **Barycentric (Center-of-Mass) Frame** using the symplectic **Velocity Verlet** integrator to conserve total mechanical energy and angular momentum.

This repository provides:
1. **Python Interactive GUI** (`python_gui/two_body_simulator.py`) — Primary interactive desktop application built with Tkinter & Matplotlib.
2. **MATLAB Interactive GUI** (`matlab/two_body_simulator.m`) — Original MATLAB implementation using `uifigure` and `timer`.

---

## Repository Structure

```text
ME206-Two-Body-Simulator/
├── python_gui/
│   ├── two_body_simulator.py   # Interactive Python GUI simulator
│   └── requirements.txt        # Python dependencies
├── matlab/
│   └── two_body_simulator.m    # Original MATLAB App/GUI simulator
└── README.md                   # Documentation & run instructions