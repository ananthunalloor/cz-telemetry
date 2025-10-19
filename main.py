#!/usr/bin/env python3
"""
Telemetry plotter with three separate subplots (one per telemetry field).

Usage:
    python telemetry_plot_three.py --fake
    python telemetry_plot_three.py --port COM6
    python telemetry_plot_three.py --fake --fields temperature pressure altitude
"""

import argparse
import logging
import struct
import time
import random
import sys

from PyQt6 import QtWidgets, QtCore
import serial  # pyserial
import numpy as np

from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib import cm

# Configure these for your device by default
PORT = "COM3"
BAUD = 115200
TIMEOUT = 1.0

START_MARKER = b"\x02"
END_MARKER = b"\x03"

TELEMETRY_PACKET_FORMAT = (
    "<H I f f f B"  # header, timestamp, temp, pressure, altitude, crc
)
PACKET_SIZE = struct.calcsize(TELEMETRY_PACKET_FORMAT)
logger = logging.getLogger("telemetry_reader")


class SerialWorker(QtCore.QObject):
    new_data = QtCore.pyqtSignal(dict)
    finished = QtCore.pyqtSignal()

    def __init__(
        self, port: str, baud: int = 115200, timeout: float = 1.0, fake: bool = False
    ):
        super().__init__()
        self.port = port
        self.baud = baud
        self.timeout = timeout
        self.fake = fake
        self._running = False
        self._ser = None

    def compute_checksum(self, packet_bytes: bytes) -> int:
        return sum(packet_bytes[:-1]) & 0xFF

    def read_exact(self, ser: serial.Serial, n: int) -> bytes:
        buf = bytearray()
        start = time.time()
        while len(buf) < n and self._running:
            chunk = ser.read(n - len(buf))
            if not chunk:
                if (time.time() - start) >= ser.timeout:
                    raise TimeoutError("Timeout while reading from serial")
                continue
            buf.extend(chunk)
        if len(buf) < n:
            raise TimeoutError("Timeout while reading exact bytes")
        return bytes(buf)

    @QtCore.pyqtSlot()
    def run(self):
        logger.info("SerialWorker started (fake=%s)", self.fake)
        self._running = True

        if self.fake:
            while self._running:
                telemetry = {
                    "header": 0xABCD,
                    "timestamp": int(time.time()),
                    "temperature": random.uniform(15.0, 25.0),
                    "pressure": random.uniform(99000.0, 102000.0),
                    "altitude": random.uniform(0.0, 100.0),
                    "crc": 0x00,
                }
                self.new_data.emit(telemetry)
                time.sleep(0.05)
            self.finished.emit()
            return

        try:
            self._ser = serial.Serial(self.port, self.baud, timeout=self.timeout)
            logger.info("Opened serial port %s @ %d", self.port, self.baud)
        except Exception as e:
            logger.exception("Failed to open serial port %s: %s", self.port, e)
            self._running = False
            self.finished.emit()
            return

        ser = self._ser
        try:
            while self._running:
                b = ser.read(1)
                if not b:
                    continue
                if b != START_MARKER:
                    continue

                try:
                    packet_bytes = self.read_exact(ser, PACKET_SIZE)
                except TimeoutError:
                    logger.warning("Timeout reading packet body, resyncing")
                    continue

                end = ser.read(1)
                if not end:
                    logger.warning("Timeout reading end marker, resyncing")
                    continue
                if end != END_MARKER:
                    logger.warning(
                        "Bad end marker (expected %s got %s), resyncing",
                        END_MARKER,
                        end,
                    )
                    continue

                received_crc = packet_bytes[-1]
                calc_crc = self.compute_checksum(packet_bytes)
                if received_crc != calc_crc:
                    logger.warning(
                        "CRC mismatch: received=%02X calc=%02X, discarding packet",
                        received_crc,
                        calc_crc,
                    )
                    continue

                try:
                    header, timestamp, temperature, pressure, altitude, crc = (
                        struct.unpack(TELEMETRY_PACKET_FORMAT, packet_bytes)
                    )
                    telemetry = {
                        "header": header,
                        "timestamp": timestamp,
                        "temperature": temperature,
                        "pressure": pressure,
                        "altitude": altitude,
                        "crc": crc,
                    }
                    self.new_data.emit(telemetry)
                except struct.error as e:
                    logger.error("Struct unpack error: %s", e)
                    continue

        except Exception as e:
            logger.exception("Serial reading error: %s", e)
        finally:
            try:
                if ser and ser.is_open:
                    ser.close()
                    logger.info("Closed serial port")
            except Exception:
                pass
            self.finished.emit()

    def stop(self):
        logger.info("Stopping SerialWorker")
        self._running = False
        try:
            if self._ser and self._ser.is_open:
                self._ser.close()
        except Exception:
            pass


class MplCanvas(FigureCanvas):
    def __init__(self, fig: Figure, parent=None):
        self.fig = fig
        super().__init__(self.fig)


class ThreePanelTelemetryWidget(QtWidgets.QWidget):
    """
    Display each telemetry field in its own subplot stacked vertically.
    Each subplot uses its own y-axis scaling so fields with different ranges don't squash each other.
    """

    def __init__(
        self, worker: SerialWorker, fields=None, buffer_len: int = 300, parent=None
    ):
        super().__init__(parent)
        self.worker = worker
        self.fields = fields or ["temperature", "pressure", "altitude"]
        if len(self.fields) != 3:
            raise ValueError("ThreePanelTelemetryWidget expects exactly 3 fields")
        self.buffer_len = buffer_len

        # Create a Figure with 3 subplots stacked vertically, shared x-axis
        fig = Figure(figsize=(8, 6), dpi=100)
        axes = [fig.add_subplot(3, 1, i + 1) for i in range(3)]
        fig.tight_layout(pad=3.0)
        self.canvas = MplCanvas(fig, parent=self)

        # Buffers: one per field
        self.xdata = np.arange(-self.buffer_len + 1, 1)
        self.ydata = np.zeros((3, self.buffer_len), dtype=float)

        # Colors
        cmap = cm.get_cmap("tab10")
        self.colors = [cmap(i % cmap.N) for i in range(3)]

        # Create lines and configure axes individually
        self.axes = axes
        self.lines = []
        for idx, (ax, field) in enumerate(zip(self.axes, self.fields)):
            (line,) = ax.plot(
                self.xdata, self.ydata[idx], color=self.colors[idx], label=field
            )
            self.lines.append(line)
            ax.set_ylabel(field)
            ax.grid(True)
            ax.legend(loc="upper right")

        # Only bottom subplot shows x label
        self.axes[-1].set_xlabel("Samples")

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.canvas)
        self.setLayout(layout)

        # connect signal
        self.worker.new_data.connect(self.on_new_telemetry)

        # Keep the plot responsive - redraw periodically (or rely on draw_idle inside update)
        self._refresh_timer = QtCore.QTimer(self)
        self._refresh_timer.timeout.connect(self.canvas.draw)
        self._refresh_timer.start(100)  # 10 Hz

    @QtCore.pyqtSlot(dict)
    def on_new_telemetry(self, telemetry: dict):
        updated_any = False
        for idx, field in enumerate(self.fields):
            if field not in telemetry:
                continue
            try:
                value = float(telemetry[field])
            except Exception:
                continue

            self.ydata[idx] = np.roll(self.ydata[idx], -1)
            self.ydata[idx, -1] = value
            self.lines[idx].set_ydata(self.ydata[idx])

            # autoscale this subplot individually
            ymin = np.min(self.ydata[idx])
            ymax = np.max(self.ydata[idx])
            # add small padding
            pad = (ymax - ymin) * 0.1 if ymax != ymin else 1.0
            self.axes[idx].set_ylim(ymin - pad, ymax + pad)
            updated_any = True

        if updated_any:
            self.canvas.draw_idle()


def main(argv):
    parser = argparse.ArgumentParser(
        description="Telemetry plotter (3 separate graphs)"
    )
    parser.add_argument("--port", "-p", default=PORT, help="Serial port")
    parser.add_argument("--baud", "-b", type=int, default=BAUD, help="Baud rate")
    parser.add_argument(
        "--fake",
        action="store_true",
        help="Emit fake telemetry instead of opening serial port",
    )
    parser.add_argument(
        "--fields",
        nargs=3,
        default=["temperature", "pressure", "altitude"],
        help="Three telemetry fields to plot (provide exactly 3)",
    )
    args = parser.parse_args(argv)

    # Setup logging
    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter("%(asctime)s| %(module)-5s | %(levelname)-5s | %(message)s")
    )
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    app = QtWidgets.QApplication([])

    # Setup worker + thread
    worker = SerialWorker(
        port=args.port, baud=args.baud, timeout=TIMEOUT, fake=args.fake
    )
    thread = QtCore.QThread()
    worker.moveToThread(thread)
    thread.started.connect(worker.run)
    worker.finished.connect(thread.quit)
    worker.finished.connect(worker.deleteLater)
    thread.finished.connect(thread.deleteLater)

    # Create GUI with three separate plots
    main_window = QtWidgets.QMainWindow()
    plot_widget = ThreePanelTelemetryWidget(
        worker=worker, fields=args.fields, buffer_len=300
    )
    main_window.setCentralWidget(plot_widget)
    main_window.setWindowTitle("CZ Telemetry - 3 Panels")
    main_window.resize(900, 700)
    main_window.show()

    # Start worker thread
    thread.start()

    # Ensure clean shutdown
    def on_about_to_quit():
        worker.stop()

    app.aboutToQuit.connect(on_about_to_quit)

    sys.exit(app.exec())


if __name__ == "__main__":
    main(sys.argv[1:])
