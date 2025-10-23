from typing import Optional, Sequence, Tuple, Any, List
import numpy as np
import math
import logging

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from mpl_toolkits.mplot3d import Axes3D

logger = logging.getLogger(__name__)


class GPSGraph:
    def __init__(self) -> None:
        self.fig: Optional[Figure] = None
        self.canvas: Optional[FigureCanvas] = None
        self.ax: Optional[Axes3D] = None

        self._trajectory_line: Optional[Any] = None
        self._current_point: Optional[Any] = None

        self.positions_enu: List[Tuple[float, float, float]] = []

        self.ref_lat: Optional[float] = None
        self.ref_lon: Optional[float] = None
        self.ref_alt: Optional[float] = None
        self.ref_set: bool = False

    def setup_gps_graph(self) -> FigureCanvas:
        fig = Figure()
        canvas = FigureCanvas(fig)
        self.fig = fig
        self.canvas = canvas
        # create 3D axes
        self.ax = fig.add_subplot(111, projection="3d")
        self.ax.set_xlabel("East (m)")
        self.ax.set_ylabel("North (m)")
        self.ax.set_zlabel("Up (m)")
        self.ax.set_title("Position Data")
        return canvas

    def geodetic_to_ecef(
        self,
        lat_deg: Sequence[float] | float,
        lon_deg: Sequence[float] | float,
        alt_m: Sequence[float] | float,
    ) -> np.ndarray:
        # WGS84 constants
        a = 6378137.0
        f = 1.0 / 298.257223563
        e2 = f * (2.0 - f)

        lat_arr = np.asarray(lat_deg, dtype=float)
        lon_arr = np.asarray(lon_deg, dtype=float)
        alt_arr = np.asarray(alt_m, dtype=float)

        # broadcast to same shape
        lat_arr, lon_arr, alt_arr = np.broadcast_arrays(lat_arr, lon_arr, alt_arr)

        lat = np.deg2rad(lat_arr)
        lon = np.deg2rad(lon_arr)

        sin_lat = np.sin(lat)
        cos_lat = np.cos(lat)
        sin_lon = np.sin(lon)
        cos_lon = np.cos(lon)

        N = a / np.sqrt(1.0 - e2 * sin_lat * sin_lat)

        x = (N + alt_arr) * cos_lat * cos_lon
        y = (N + alt_arr) * cos_lat * sin_lon
        z = (N * (1.0 - e2) + alt_arr) * sin_lat

        # stack into (n,3)
        ecef = np.vstack((x.ravel(), y.ravel(), z.ravel())).T
        return ecef

    def ecef_to_enu(
        self,
        ecef_pts: Sequence[float] | np.ndarray,
        lat0_deg: float | None,
        lon0_deg: float | None,
        alt0_m: float | None,
    ) -> np.ndarray:
        if not self.ref_set and (
            lat0_deg is None or lon0_deg is None or alt0_m is None
        ):
            raise ValueError(
                "Reference geodetic must be provided or set before conversion."
            )

        ecef_pts_arr = np.asarray(ecef_pts, dtype=float)
        ecef_pts_arr = np.atleast_2d(ecef_pts_arr)  # ensure shape (n,3)

        if ecef_pts_arr.shape[1] != 3:
            raise ValueError("ecef_pts must have shape (n,3) or (3,)")

        # Reference ECEF (1,3)
        # If any of the provided reference values are None, fall back to stored reference values.
        if lat0_deg is None:
            if self.ref_lat is None:
                raise ValueError("Latitude reference is missing.")
            lat0_val = float(self.ref_lat)
        else:
            lat0_val = float(lat0_deg)

        if lon0_deg is None:
            if self.ref_lon is None:
                raise ValueError("Longitude reference is missing.")
            lon0_val = float(self.ref_lon)
        else:
            lon0_val = float(lon0_deg)

        if alt0_m is None:
            if self.ref_alt is None:
                raise ValueError("Altitude reference is missing.")
            alt0_val = float(self.ref_alt)
        else:
            alt0_val = float(alt0_m)

        ref = self.geodetic_to_ecef(lat0_val, lon0_val, alt0_val)[0]

        # Precompute trig
        lat0 = math.radians(lat0_val)
        lon0 = math.radians(lon0_val)
        sin_lat0 = math.sin(lat0)
        cos_lat0 = math.cos(lat0)
        sin_lon0 = math.sin(lon0)
        cos_lon0 = math.cos(lon0)

        # ECEF vector relative to reference
        d = ecef_pts_arr - ref  # shape (n,3)

        # ENU conversion (vectorized)
        east = -sin_lon0 * d[:, 0] + cos_lon0 * d[:, 1]
        north = (
            -sin_lat0 * cos_lon0 * d[:, 0]
            - sin_lat0 * sin_lon0 * d[:, 1]
            + cos_lat0 * d[:, 2]
        )
        up = (
            cos_lat0 * cos_lon0 * d[:, 0]
            + cos_lat0 * sin_lon0 * d[:, 1]
            + sin_lat0 * d[:, 2]
        )

        enu = np.vstack((east, north, up)).T
        return enu

    def _initialize_reference(self, lat: float, lon: float, alt: float) -> bool:
        if lat is None or lon is None or alt is None:
            logger.debug("Attempted to initialize reference with None values.")
            return False

        try:
            self.ref_lat = float(lat)
            self.ref_lon = float(lon)
            self.ref_alt = float(alt)
        except Exception:
            logger.exception("Failed to convert reference geodetic to float")
            return False

        self.ref_set = True
        logger.info(
            "Reference geodetic set to lat=%s lon=%s alt=%s",
            self.ref_lat,
            self.ref_lon,
            self.ref_alt,
        )
        return True

    def set_reference(self, lat: float, lon: float, alt: float) -> bool:
        return self._initialize_reference(lat, lon, alt)

    def _update_plot_with_new_point(self, enu_point: Sequence[float]) -> None:
        enu_arr = np.asarray(enu_point, dtype=float).ravel()
        if enu_arr.size != 3:
            logger.error("enu_point must be of length 3")
            return

        # Append point to stored list
        self.positions_enu.append(
            (float(enu_arr[0]), float(enu_arr[1]), float(enu_arr[2]))
        )

        if self.ax is None:
            logger.warning(
                "Attempted to update plot but axes (self.ax) are not initialized."
            )
            return

        pts = np.array(self.positions_enu)
        x = pts[:, 0]
        y = pts[:, 1]
        z = pts[:, 2]

        if self._trajectory_line is None:
            lines = self.ax.plot(x, y, z, color="blue", linewidth=1.5)
            if lines:
                self._trajectory_line = lines[0]
            else:
                logger.warning("ax.plot returned no lines")
            self._current_point = self.ax.scatter(
                [x[-1]], [y[-1]], [z[-1]], color="red", s=30
            )
            try:
                self.ax.legend()
            except Exception:
                pass
        else:
            try:
                self._trajectory_line.set_data(x, y)

                self._trajectory_line.set_3d_properties(z)
            except Exception:
                logger.exception(
                    "Failed to update trajectory line data; attempting to recreate line."
                )
                try:
                    self._trajectory_line.remove()
                except Exception:
                    logger.debug("Failed to remove old trajectory line", exc_info=True)
                lines = self.ax.plot(
                    x, y, z, color="blue", linewidth=1.5, label="trajectory"
                )
                self._trajectory_line = lines[0] if lines else None

            if self._current_point is not None:
                try:
                    self._current_point._offsets3d = (
                        np.array([x[-1]]),
                        np.array([y[-1]]),
                        np.array([z[-1]]),
                    )
                except Exception:
                    logger.debug(
                        "Failed to update current point offsets; recreating scatter.",
                        exc_info=True,
                    )
                    try:
                        self._current_point.remove()
                    except Exception:
                        logger.debug(
                            "Failed to remove old current point", exc_info=True
                        )
                    self._current_point = self.ax.scatter(
                        [x[-1]], [y[-1]], [z[-1]], color="red", s=30
                    )
            else:
                self._current_point = self.ax.scatter(
                    [x[-1]], [y[-1]], [z[-1]], color="red", s=30
                )

        pad = 1.0  # meters
        try:
            xmin, xmax = float(np.min(x)), float(np.max(x))
            if not math.isfinite(xmin) or not math.isfinite(xmax):
                pass
            else:
                if abs(xmax - xmin) < 1e-6:
                    xmin -= 1.0
                    xmax += 1.0
                self.ax.set_xlim(xmin - pad, xmax + pad)

            ymin, ymax = float(np.min(y)), float(np.max(y))
            if math.isfinite(ymin) and math.isfinite(ymax):
                if abs(ymax - ymin) < 1e-6:
                    ymin -= 1.0
                    ymax += 1.0
                self.ax.set_ylim(ymin - pad, ymax + pad)

            zmin, zmax = float(np.min(z)), float(np.max(z))
            if math.isfinite(zmin) and math.isfinite(zmax):
                if abs(zmax - zmin) < 1e-6:
                    zmin -= 1.0
                    zmax += 1.0
                self.ax.set_zlim(zmin - pad, zmax + pad)
        except Exception:
            logger.exception("Failed to set axis limits.")

        if self.canvas is not None:
            try:
                self.canvas.draw_idle()
            except Exception:
                logger.exception("Failed to redraw canvas")

    def update_gps_graph(
        self, lat: float | None, lon: float | None, alt: float | None
    ) -> None:
        if lat is None or lon is None or alt is None:
            logger.debug("Received None geodetic values; ignoring update.")
            return

        if not self.ref_set:
            ok = self._initialize_reference(lat, lon, alt)
            if not ok:
                return

        try:
            latf = float(lat)
            lonf = float(lon)
            altf = float(alt)
        except Exception:
            logger.exception("Invalid geodetic values in telemetry")
            return

        ecef = self.geodetic_to_ecef(latf, lonf, altf)  # shape (1,3)
        enu = self.ecef_to_enu(
            ecef, self.ref_lat, self.ref_lon, self.ref_alt
        )  # shape (1,3)
        enu_point = enu[0]

        self._update_plot_with_new_point(enu_point)

    def clear(self) -> None:
        self.positions_enu.clear()
        if self.ax is not None:
            try:
                if self._trajectory_line is not None:
                    try:
                        self._trajectory_line.remove()
                    except Exception:
                        logger.debug("Failed to remove trajectory line", exc_info=True)
                    self._trajectory_line = None
                if self._current_point is not None:
                    try:
                        self._current_point.remove()
                    except Exception:
                        logger.debug("Failed to remove current point", exc_info=True)
                    self._current_point = None
                # optionally clear axes
                self.ax.cla()
                # restore labels
                self.ax.set_xlabel("East (m)")
                self.ax.set_ylabel("North (m)")
                self.ax.set_zlabel("Up (m)")
                self.ax.set_title("Telemetry Position Data")
            except Exception:
                logger.exception("Error while clearing plot")

    def get_positions(self) -> List[Tuple[float, float, float]]:
        return list(self.positions_enu)
