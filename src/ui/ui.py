from PyQt6.QtGui import QFont
from PyQt6.QtGui import QCloseEvent
import logging
from PyQt6 import QtCore
from typing import Optional
import numpy as np
import math

from PyQt6.QtWidgets import QHBoxLayout
from PyQt6.QtWidgets import QCheckBox
from PyQt6.QtWidgets import QLineEdit
from PyQt6.QtWidgets import QFormLayout
from PyQt6.QtWidgets import QGridLayout
import sys
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QMenuBar,
    QMenu,
    QToolBar,
    QPushButton,
    QLabel,
    QVBoxLayout,
    QWidget,
    QStatusBar,
    QMessageBox,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtGui import QAction

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401

from PyQt6.QtGui import QColor, QPalette

from src.ui.value_grid import ValueGrid
from src.telemetry import Telemetry
from src.ui.gps_graph import GPSGraph
from src.ui.log_viewer import LogViewer

logger = logging.getLogger(__name__)


class Color(QWidget):
    def __init__(self, color):
        super().__init__()
        self.setAutoFillBackground(True)

        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor(color))
        self.setPalette(palette)


class MainWindow(QMainWindow):
    # Custom signal for communication between widgets
    data_updated = pyqtSignal(str)

    def __init__(self, telemetry: Telemetry):
        super().__init__()
        logger.info("Initializing MainWindow")
        self.setWindowTitle("CZ Telemetry")
        # self.setGeometry(100, 100, 600, 200)
        self.setGeometry(100, 100, 1600, 900)
        self.status_bar = self.statusBar()
        self.telemetry = telemetry
        self.received_data: Optional[dict] = None

        self.graph_widget = GPSGraph()
        self.log_viewer_widget = LogViewer(max_lines=100)
        self.data_grid_widget = ValueGrid()

        # Initialize UI components
        self._create_menu_bar()
        self._create_toolbar()
        self._create_status_bar()
        self._create_central_widget()

        # Connect signals
        self.data_updated.connect(self._on_data_updated)
        self.telemetry.telemetry.connect(self.on_new_telemetry)

        # Set initial status
        if self.status_bar is not None:
            self.status_bar.showMessage("Ready")

        self._refresh_timer = QtCore.QTimer(self)
        self._refresh_timer.start(100)

    def _create_menu_bar(self):
        """Create the main menu bar with actions"""
        pass

    def _create_toolbar(self):
        """Create the toolbar with buttons"""
        pass

    def _create_status_bar(self):
        """Create the status bar"""
        pass

    def _create_central_widget(self):
        """Create the main content area"""

        canvas = self.graph_widget.setup_gps_graph()
        dgrid = self.data_grid_widget.setup_gps_graph()
        log_viewer = self.log_viewer_widget.setup_log_viewer()

        self.data_grid_widget.set_units(
            {
                "A0": "V",
                "A1": "A",
                "A2": "%",
                "B0": "°C",
                "B1": "mbar",
                "B2": "m",
                "C0": "V",
                "C1": "V",
                "C2": "V",
            }
        )

        # self.data_grid_widget.set_unit_for_key("A0", "V")
        # self.data_grid_widget.set_unit_for_key("A1", "V")
        # self.data_grid_widget.set_unit_for_key("A2", "V")
        # self.data_grid_widget.set_unit_for_key("B0", "V")
        # self.data_grid_widget.set_unit_for_key("B1", "V")
        # self.data_grid_widget.set_unit_for_key("B2", "V")
        # self.data_grid_widget.set_unit_for_key("C0", "V")
        # self.data_grid_widget.set_unit_for_key("C1", "V")
        # self.data_grid_widget.set_unit_for_key("C2", "V")

        widget = QWidget()
        outerLayout = QVBoxLayout()
        outerLayout.setSpacing(0)
        outerLayout.setContentsMargins(5, 0, 5, 0)

        w = QWidget()
        w.setFixedHeight(72)
        wlayout = QVBoxLayout()
        wlayout.setSpacing(0)
        wlayout.setContentsMargins(0, 0, 0, 0)
        wlayout.addWidget(Color("cyan"))
        w.setLayout(wlayout)

        q = QWidget()
        qlayout = QHBoxLayout()
        asas = QWidget()
        asas.setFixedWidth(420)

        qlayout.addWidget(canvas)
        qlayout.addWidget(asas)

        qlayout.setSpacing(0)
        qlayout.setContentsMargins(0, 0, 0, 0)
        q.setLayout(qlayout)

        a = QWidget()
        a.setFixedWidth(420)
        alayout = QVBoxLayout()
        alayout.setSpacing(0)
        alayout.setContentsMargins(0, 0, 0, 0)

        alayout.addWidget(dgrid)
        # alayout.addWidget(Color("yellow"))
        alayout.addWidget(log_viewer)
        # alayout.addWidget(Color("orange"))
        a.setLayout(alayout)

        qlayout.addWidget(a)

        outerLayout.addWidget(w)
        outerLayout.addWidget(q)

        widget.setLayout(outerLayout)
        self.setCentralWidget(widget)

    @QtCore.pyqtSlot(dict)
    def on_new_telemetry(self, telemetry: dict):
        # Update labels
        try:
            self.data_grid_widget.update_telemetry(
                "A0", str(telemetry.get("temperature", ""))
            )
            self.data_grid_widget.update_telemetry(
                "A1", str(telemetry.get("pressure", ""))
            )
            self.data_grid_widget.update_telemetry(
                "A2", str(telemetry.get("altitude", ""))
            )
            self.data_grid_widget.update_telemetry(
                "B0", str(telemetry.get("temperature", ""))
            )
            self.data_grid_widget.update_telemetry(
                "B1", str(telemetry.get("pressure", ""))
            )
            self.data_grid_widget.update_telemetry(
                "B2", str(telemetry.get("altitude", ""))
            )
            self.data_grid_widget.update_telemetry(
                "C0", str(telemetry.get("temperature", ""))
            )
            self.data_grid_widget.update_telemetry(
                "C1", str(telemetry.get("pressure", ""))
            )
            self.data_grid_widget.update_telemetry(
                "C2", str(telemetry.get("altitude", ""))
            )
            # self.received_data = telemetry
            # self.temperature.setText(str(telemetry.get("temperature", "")))
            # self.pressure.setText(str(telemetry.get("pressure", "")))
            # self.altitude.setText(
            #     str(telemetry.get("altitude", telemetry.get("alt", "")))
            # )
        except Exception:
            logger.exception("Failed to update telemetry labels")

        self.graph_widget.update_gps_graph(
            telemetry.get("latitude", telemetry.get("lat", None)),
            telemetry.get("longitude", telemetry.get("lon", None)),
            telemetry.get(
                "altitude", telemetry.get("alt", telemetry.get("elevation", None))
            ),
        )

        self.log_viewer_widget.add_log(telemetry.get("log", "No log message"))

    def _button_clicked(self):
        # """Handle main button click"""
        # self.data_updated.emit("Button clicked!")
        pass

    def _custom_button_clicked(self):
        # """Handle custom toolbar button click"""
        # self.statusBar().showMessage("Custom button clicked")
        pass

    def _on_data_updated(self, message):
        # """Handle custom signal"""
        # self.statusBar().showMessage(message)
        pass

    def _show_about(self):
        # """Show about dialog"""
        # QMessageBox.about(self, "About", "Qt6 Python App Template\n\nA basic PyQt6 application template.")
        pass

    # pyrefly: ignore[bad-param-name-override]
    def closeEvent(self, event: QCloseEvent):
        """Handle window closing"""
        logging.info("Stopping CZ Telemetry application")
        event.accept()
        # reply = QMessageBox.question(
        #     self,
        #     "Confirm Exit",
        #     "Are you sure you want to exit?",
        #     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        # )

        # if reply == QMessageBox.StandardButton.Yes:
        # event.accept()
        # else:
        #     event.ignore()
