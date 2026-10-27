"""Viewport debug overlays. No USD geometry is added to camera/depth products."""
from collections import deque
import numpy as np
from isaacsim.util.debug_draw import _debug_draw
from isaacsim.core.utils.viewports import set_camera_view
import omni.ui as ui
from pxr import UsdGeom
import omni.usd
from omni.kit.viewport.utility import get_active_viewport


def top_view():
    # Below the building roof; orthographic framing covers the entire pool.
    viewport = get_active_viewport()
    camera = UsdGeom.Camera.Define(omni.usd.get_context().get_stage(), "/OmniverseKit_Persp")
    viewport.camera_path = "/OmniverseKit_Persp"
    camera.CreateProjectionAttr("orthographic")
    camera.CreateHorizontalApertureAttr(95.0)
    camera.CreateVerticalApertureAttr(53.4375)
    set_camera_view(eye=np.array([.3, .6, 2.8]), target=np.array([.3, .6001, 1]), camera_prim_path="/OmniverseKit_Persp")


def perspective_view():
    viewport = get_active_viewport()
    camera = UsdGeom.Camera.Define(omni.usd.get_context().get_stage(), "/OmniverseKit_Persp")
    viewport.camera_path = "/OmniverseKit_Persp"
    camera.CreateProjectionAttr("perspective")
    camera.CreateHorizontalApertureAttr(20.955)
    camera.CreateVerticalApertureAttr(11.787)
    set_camera_view(eye=np.array([0, -6, 5]), target=np.array([0, .6, 1]), camera_prim_path="/OmniverseKit_Persp")


class ViewportPaths:
    def __init__(self, config, headless=False):
        self.config = config
        self.draw = _debug_draw.acquire_debug_draw_interface()
        self.current, self.controls = [], []
        self.previous = deque(maxlen=3)
        self.journal = deque(maxlen=1000)
        self.updates = 0
        self.info = {}
        self.planner_status = {}
        self.tracking_status = {}
        self.show = {"Current plan (cyan)": True, "Previous plans (orange)": True,
                     "Control polygon (yellow)": False, "Executed path (green)": True}
        self.status = None
        if not headless:
            self.window = ui.Window("ROV navigation", width=380, height=330)
            with self.window.frame:
                with ui.VStack(spacing=6):
                    ui.Label(config["title"].split("/")[0].strip())
                    ui.Label("Paths projected above water for visibility", word_wrap=True)
                    self.status = ui.Label("Waiting for planner...", word_wrap=True, height=95)
                    for label, value in self.show.items():
                        with ui.HStack():
                            # Bind each checkbox independently.
                            checkbox = ui.CheckBox(width=20)
                            checkbox.model.set_value(value)
                            checkbox.model.add_value_changed_fn(lambda model, key=label: self.show.__setitem__(key, model.as_bool))
                            ui.Label(label)
                    with ui.HStack(spacing=8):
                        ui.Button("Top view", clicked_fn=top_view)
                        ui.Button("Perspective", clicked_fn=perspective_view)

    def receive_path(self, msg):
        points = [(p.pose.position.x, p.pose.position.y, p.pose.position.z) for p in msg.poses]
        if len(points) < 2:
            return
        if self.current:
            self.previous.append(self.current)
        self.current = points
        self.updates += 1
        stamp = msg.header.stamp.sec + msg.header.stamp.nanosec / 1e9
        self.journal.append({"start_time": stamp, "points": points})

    def receive_controls(self, msg):
        self.controls = [(p.pose.position.x, p.pose.position.y, p.pose.position.z) for p in msg.poses]

    def update(self, history, position):
        self.draw.clear_lines()
        self.draw.clear_points()
        starts, ends, colors, widths = [], [], [], []
        def add(points, color, width, z):
            if len(points) < 2:
                return
            projected = [(float(p[0]), float(p[1]), z) for p in points]
            starts.extend(projected[:-1]); ends.extend(projected[1:])
            colors.extend([color]*(len(points)-1)); widths.extend([width]*(len(points)-1))
        surface = self.config["water_surface"]
        if self.show["Previous plans (orange)"]:
            for old in self.previous:
                add(old, (1.0, .45, .05, .4), 2, surface+.12)
        if self.show["Executed path (green)"]:
            add(history, (.1, 1.0, .2, 1), 4, surface+.14)
        if self.show["Control polygon (yellow)"]:
            add(self.controls, (1, .9, .15, .8), 2, surface+.18)
            if self.controls:
                self.draw.draw_points([(x, y, surface+.18) for x, y, _ in self.controls],
                    [(1, .9, .15, 1)]*len(self.controls), [7]*len(self.controls))
        if self.show["Current plan (cyan)"]:
            add(self.current, (.05, .9, 1.0, 1), 5, surface+.20)
        if starts:
            self.draw.draw_lines(starts, ends, colors, widths)
        if self.status:
            error = float(np.linalg.norm(np.array(position)-self.config["goal"]))
            self.status.text = (f"Plan updates: {self.updates} | Trajectory: {self.info.get('trajectory_id', '-')}\n"
                                f"Goal distance: {error:.2f} m | Hold depth: 1.0 m\n"
                                f"Planner: {self.planner_status.get('state', 'waiting')} | Tracker: {self.tracking_status.get('mode', 'waiting')}\n"
                                + ("Goal occupied: select a free target" if self.planner_status.get("state")=="BLOCKED_GOAL"
                                   else "Turning: trajectory progress held" if self.planner_status.get("heading_paused")
                                   else "Waiting for a valid local trajectory" if self.planner_status.get("state")=="GEN_NEW_TRAJ" else ""))
