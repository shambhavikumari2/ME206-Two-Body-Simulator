import math
from collections import deque
import tkinter as tk
import matplotlib

matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class TwoBodySimulatorApp:
    """Interactive Two-Body Gravitational Simulator (Center-of-Mass Frame)
    Integrator: Velocity Verlet (symplectic, preserves orbital energy)
    """

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Interactive Two-Body Gravitational Simulator")
        self.root.geometry("1120x640")
        self.root.configure(bg="#1f1f24")

        # Simulation parameters (same as MATLAB implementation)
        self.G = 1.0
        self.m1 = 10.0
        self.r0 = 2.0
        self.dt = 0.001
        self.substeps = 15
        self.paused = False
        self.after_id = None

        # Orbital trail buffers (max 700 points)
        self.trail1_x = deque(maxlen=700)
        self.trail1_y = deque(maxlen=700)
        self.trail2_x = deque(maxlen=700)
        self.trail2_y = deque(maxlen=700)

        self._build_ui()
        self.reset_simulation()

        self.root.protocol("WM_DELETE_WINDOW", self.cleanup_and_close)
        self.step_simulation()

    def _build_ui(self):
        # Main container
        main_frame = tk.Frame(self.root, bg="#1f1f24")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        # Left Panel: Matplotlib Orbital Plot
        left_frame = tk.Frame(main_frame, bg="#1f1f24")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 12))

        self.fig = Figure(figsize=(6.8, 6.0), dpi=100, facecolor="#1f1f24")
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor("#0f1217")
        self.ax.tick_params(colors="#bfbfc7")
        for spine in self.ax.spines.values():
            spine.set_color("#bfbfc7")
        self.ax.grid(True, color="#40404d", alpha=0.5)
        self.ax.set_aspect("equal", adjustable="box")
        self.ax.set_xlim(-3.5, 3.5)
        self.ax.set_ylim(-3.5, 3.5)
        self.ax.set_xlabel("x (AU-scaled)", color="#d9d9d9")
        self.ax.set_ylabel("y (AU-scaled)", color="#d9d9d9")
        self.ax.set_title(
            "Two-Body Orbital Dynamics (Barycentric Frame)",
            color="white",
            fontsize=12,
            fontweight="bold",
        )

        # Barycenter marker at origin (0,0)
        self.ax.plot(
            0, 0, "+w", markersize=10, markeredgewidth=1.3, label="Barycenter (CoM)"
        )

        # Animated orbital trails
        (self.trail1_line,) = self.ax.plot(
            [], [], color="#ffa626", linewidth=1.5, label="Body 1 Trail"
        )
        (self.trail2_line,) = self.ax.plot(
            [], [], color="#40bfff", linewidth=1.5, label="Body 2 Trail"
        )

        # Body markers
        (self.body1_marker,) = self.ax.plot(
            [0],
            [0],
            "o",
            markersize=14,
            markerfacecolor="#ffa626",
            markeredgecolor="white",
            label="Body 1 (m1)",
        )
        (self.body2_marker,) = self.ax.plot(
            [0],
            [0],
            "o",
            markersize=9,
            markerfacecolor="#40bfff",
            markeredgecolor="white",
            label="Body 2 (m2)",
        )

        self.ax.legend(
            loc="upper right",
            facecolor="#24262e",
            edgecolor="#40404d",
            labelcolor="white",
            fontsize=8.5,
        )

        self.canvas = FigureCanvasTkAgg(self.fig, master=left_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Right Panel: Controls & Live Telemetry
        ctrl_panel = tk.LabelFrame(
            main_frame,
            text=" Controls & Conservation Telemetry ",
            bg="#292b33",
            fg="white",
            font=("Segoe UI", 11, "bold"),
            padx=14,
            pady=12,
            width=330,
        )
        ctrl_panel.pack(side=tk.RIGHT, fill=tk.Y)
        ctrl_panel.pack_propagate(False)

        # Mass Ratio Slider
        self.lbl_mass = tk.Label(
            ctrl_panel,
            text="Mass Ratio (m2 / m1): 0.25",
            bg="#292b33",
            fg="white",
            font=("Segoe UI", 10, "bold"),
            anchor="w",
        )
        self.lbl_mass.pack(fill=tk.X, pady=(4, 2))

        self.sld_mass = tk.Scale(
            ctrl_panel,
            from_=0.05,
            to=1.00,
            resolution=0.01,
            orient=tk.HORIZONTAL,
            bg="#292b33",
            fg="white",
            highlightthickness=0,
            troughcolor="#404452",
            activebackground="#40bfff",
        )
        self.sld_mass.set(0.25)
        self.sld_mass.pack(fill=tk.X, pady=(0, 12))

        # Initial Speed Multiplier Slider
        self.lbl_vel = tk.Label(
            ctrl_panel,
            text="Initial Speed (v / v_circ): 1.00",
            bg="#292b33",
            fg="white",
            font=("Segoe UI", 10, "bold"),
            anchor="w",
        )
        self.lbl_vel.pack(fill=tk.X, pady=(4, 2))

        self.sld_vel = tk.Scale(
            ctrl_panel,
            from_=0.40,
            to=1.50,
            resolution=0.01,
            orient=tk.HORIZONTAL,
            bg="#292b33",
            fg="white",
            highlightthickness=0,
            troughcolor="#404452",
            activebackground="#ffa626",
        )
        self.sld_vel.set(1.00)
        self.sld_vel.pack(fill=tk.X, pady=(0, 16))

        # Pause & Reset Buttons
        btn_frame = tk.Frame(ctrl_panel, bg="#292b33")
        btn_frame.pack(fill=tk.X, pady=(0, 18))

        self.btn_pause = tk.Button(
            btn_frame,
            text="Pause",
            command=self.toggle_pause,
            bg="#4073bf",
            fg="white",
            font=("Segoe UI", 10, "bold"),
            relief=tk.FLAT,
            pady=6,
            cursor="hand2",
        )
        self.btn_pause.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))

        self.btn_reset = tk.Button(
            btn_frame,
            text="Reset Orbit",
            command=self.reset_simulation,
            bg="#4d525c",
            fg="white",
            font=("Segoe UI", 10, "bold"),
            relief=tk.FLAT,
            pady=6,
            cursor="hand2",
        )
        self.btn_reset.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(6, 0))

        # Telemetry Section
        tk.Label(
            ctrl_panel,
            text="--- Live Conserved Quantities ---",
            bg="#292b33",
            fg="#b3d9ff",
            font=("Segoe UI", 10, "bold"),
        ).pack(fill=tk.X, pady=(4, 10))

        self.lbl_regime = tk.Label(
            ctrl_panel,
            text="Orbit Type: Circular (E < 0)",
            bg="#292b33",
            fg="#66ff80",
            font=("Segoe UI", 10, "bold"),
            anchor="w",
        )
        self.lbl_regime.pack(fill=tk.X, pady=4)

        self.lbl_ke = tk.Label(
            ctrl_panel,
            text="Kinetic Energy (K):   +0.0000",
            bg="#292b33",
            fg="white",
            font=("Consolas", 10),
            anchor="w",
        )
        self.lbl_ke.pack(fill=tk.X, pady=3)

        self.lbl_pe = tk.Label(
            ctrl_panel,
            text="Potential Energy (U): +0.0000",
            bg="#292b33",
            fg="white",
            font=("Consolas", 10),
            anchor="w",
        )
        self.lbl_pe.pack(fill=tk.X, pady=3)

        self.lbl_te = tk.Label(
            ctrl_panel,
            text="Total Energy (E):     +0.00000",
            bg="#292b33",
            fg="#ffd959",
            font=("Consolas", 10, "bold"),
            anchor="w",
        )
        self.lbl_te.pack(fill=tk.X, pady=3)

        self.lbl_ang_mom = tk.Label(
            ctrl_panel,
            text="Angular Momentum (L): +0.0000",
            bg="#292b33",
            fg="white",
            font=("Consolas", 10),
            anchor="w",
        )
        self.lbl_ang_mom.pack(fill=tk.X, pady=3)

        # Bind slider callbacks after all widgets are ready
        self.sld_mass.configure(command=self.on_slider_change)
        self.sld_vel.configure(command=self.on_slider_change)

    def compute_accel(self, x1, y1, x2, y2):
        dx = x2 - x1
        dy = y2 - y1
        r2 = dx * dx + dy * dy + 1e-6
        inv_r3 = r2 ** (-1.5)

        a1x = self.G * self.m2 * dx * inv_r3
        a1y = self.G * self.m2 * dy * inv_r3
        a2x = -self.G * self.m1 * dx * inv_r3
        a2y = -self.G * self.m1 * dy * inv_r3
        return a1x, a1y, a2x, a2y

    def on_slider_change(self, _=None):
        self.lbl_mass.config(text=f"Mass Ratio (m2 / m1): {self.sld_mass.get():.2f}")
        self.lbl_vel.config(text=f"Initial Speed (v / v_circ): {self.sld_vel.get():.2f}")
        self.reset_simulation()

    def toggle_pause(self):
        self.paused = not self.paused
        if self.paused:
            self.btn_pause.config(text="Resume", bg="#33a666")
        else:
            self.btn_pause.config(text="Pause", bg="#4073bf")

    def reset_simulation(self):
        ratio = self.sld_mass.get()
        v_mult = self.sld_vel.get()

        self.m2 = ratio * self.m1
        M = self.m1 + self.m2

        self.x1 = -(self.m2 / M) * self.r0
        self.y1 = 0.0
        self.x2 = (self.m1 / M) * self.r0
        self.y2 = 0.0

        v_circ = math.sqrt(self.G * M / self.r0)
        v_rel = v_mult * v_circ

        self.vx1 = 0.0
        self.vy1 = -(self.m2 / M) * v_rel
        self.vx2 = 0.0
        self.vy2 = (self.m1 / M) * v_rel

        self.body2_marker.set_markersize(6 + 8 * ratio)

        self.trail1_x.clear()
        self.trail1_y.clear()
        self.trail2_x.clear()
        self.trail2_y.clear()

        self.update_graphics_and_telemetry()

    def update_graphics_and_telemetry(self):
        self.body1_marker.set_data([self.x1], [self.y1])
        self.body2_marker.set_data([self.x2], [self.y2])

        self.trail1_x.append(self.x1)
        self.trail1_y.append(self.y1)
        self.trail2_x.append(self.x2)
        self.trail2_y.append(self.y2)

        self.trail1_line.set_data(self.trail1_x, self.trail1_y)
        self.trail2_line.set_data(self.trail2_x, self.trail2_y)

        v1_sq = self.vx1**2 + self.vy1**2
        v2_sq = self.vx2**2 + self.vy2**2
        K = 0.5 * self.m1 * v1_sq + 0.5 * self.m2 * v2_sq

        r = math.hypot(self.x2 - self.x1, self.y2 - self.y1)
        U = -self.G * self.m1 * self.m2 / r
        E = K + U

        L = self.m1 * (self.x1 * self.vy1 - self.y1 * self.vx1) + self.m2 * (
            self.x2 * self.vy2 - self.y2 * self.vx2
        )

        v_mult = self.sld_vel.get()
        if abs(v_mult - 1.0) < 0.02:
            regime, color = "Circular (E < 0)", "#66ff80"
        elif E < -1e-4:
            regime, color = "Bound Elliptical (E < 0)", "#66d9ff"
        elif abs(E) <= 1e-4:
            regime, color = "Parabolic Escape (E = 0)", "#ffcc4d"
        else:
            regime, color = "Hyperbolic Escape (E > 0)", "#ff7373"

        self.lbl_regime.config(text=f"Orbit Type: {regime}", fg=color)
        self.lbl_ke.config(text=f"Kinetic Energy (K):   {K:+.4f}")
        self.lbl_pe.config(text=f"Potential Energy (U): {U:+.4f}")
        self.lbl_te.config(text=f"Total Energy (E):     {E:+.5f}")
        self.lbl_ang_mom.config(text=f"Angular Momentum (L): {L:+.4f}")

        self.canvas.draw_idle()

    def step_simulation(self):
        if not self.paused:
            for _ in range(self.substeps):
                a1x, a1y, a2x, a2y = self.compute_accel(
                    self.x1, self.y1, self.x2, self.y2
                )

                vx1_half = self.vx1 + 0.5 * a1x * self.dt
                vy1_half = self.vy1 + 0.5 * a1y * self.dt
                vx2_half = self.vx2 + 0.5 * a2x * self.dt
                vy2_half = self.vy2 + 0.5 * a2y * self.dt

                self.x1 += vx1_half * self.dt
                self.y1 += vy1_half * self.dt
                self.x2 += vx2_half * self.dt
                self.y2 += vy2_half * self.dt

                a1x_new, a1y_new, a2x_new, a2y_new = self.compute_accel(
                    self.x1, self.y1, self.x2, self.y2
                )

                self.vx1 = vx1_half + 0.5 * a1x_new * self.dt
                self.vy1 = vy1_half + 0.5 * a1y_new * self.dt
                self.vx2 = vx2_half + 0.5 * a2x_new * self.dt
                self.vy2 = vy2_half + 0.5 * a2y_new * self.dt

            self.update_graphics_and_telemetry()

        self.after_id = self.root.after(20, self.step_simulation)

    def cleanup_and_close(self):
        if self.after_id is not None:
            self.root.after_cancel(self.after_id)
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = TwoBodySimulatorApp(root)
    root.mainloop()