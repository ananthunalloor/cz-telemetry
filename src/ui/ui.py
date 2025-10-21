from PyQt6.QtGui import QFont
from PyQt6.QtGui import QCloseEvent
import logging
from PyQt6 import QtCore
from typing import Optional

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

from PyQt6.QtGui import QColor, QPalette

from src.telemetry import Telemetry

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
        # menubar = self.menuBar()

        # # # File menu
        # file_menu = menubar.addMenu("&File")
        # exit_action = QAction("&Exit", self)
        # exit_action.setShortcut("Ctrl+Q")
        # exit_action.triggered.connect(self.close)
        # file_menu.addAction(exit_action)

        # # Edit menu
        # edit_menu = menubar.addMenu("&Edit")
        # copy_action = QAction("&Copy", self)
        # paste_action = QAction("&Paste", self)
        # edit_menu.addAction(copy_action)
        # edit_menu.addAction(paste_action)

        # # Help menu
        # help_menu = menubar.addMenu("&Help")
        # about_action = QAction("&About", self)
        # about_action.triggered.connect(self._show_about)
        # help_menu.addAction(about_action)
        pass

    def _create_toolbar(self):
        """Create the toolbar with buttons"""
        # toolbar = QToolBar("Main Toolbar")
        # self.addToolBar(toolbar)

        # # Add actions to toolbar
        # new_action = QAction("New", self)
        # new_action.setStatusTip("Create a new file")
        # new_action.triggered.connect(lambda: print("New clicked"))

        # open_action = QAction("Open", self)
        # open_action.setStatusTip("Open a file")
        # open_action.triggered.connect(lambda: print("Open clicked"))

        # save_action = QAction("Save", self)
        # save_action.setStatusTip("Save current file")
        # save_action.triggered.connect(lambda: print("Save clicked"))

        # toolbar.addAction(new_action)
        # toolbar.addAction(open_action)
        # toolbar.addAction(save_action)

        # # Add a separator
        # toolbar.addSeparator()

        # # Add a button with custom action
        # btn = QPushButton("Custom Action")
        # btn.clicked.connect(self._custom_button_clicked)
        # toolbar.addWidget(btn)
        pass

    def _create_status_bar(self):
        """Create the status bar"""
        # self.statusBar().showMessage("Application ready")
        pass

    def _create_central_widget(self):
        """Create the main content area"""
        widget = QWidget()

        self.temperature = QLabel("0.0 V")
        self.pressure = QLabel("0.0 V")
        self.altitude = QLabel("0.0 V")

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
        qlayout.addWidget(Color("red"))
        qlayout.setSpacing(0)
        qlayout.setContentsMargins(0, 0, 0, 0)
        q.setLayout(qlayout)

        a = QWidget()
        a.setFixedWidth(420)
        alayout = QVBoxLayout()
        alayout.setSpacing(0)
        alayout.setContentsMargins(0, 0, 0, 0)

        dgrid = QWidget()
        dgridlayout = QGridLayout()
        dgridlayout.setSpacing(0)
        dgridlayout.setContentsMargins(0, 0, 0, 0)

        dgridlayout.addWidget(self.temperature, 1, 0)
        dgridlayout.addWidget(self.pressure, 2, 0)
        dgridlayout.addWidget(self.altitude, 3, 0)

        dgridlayout.addWidget(Color("red"), 1, 1)
        dgridlayout.addWidget(Color("yellow"), 2, 1)
        dgridlayout.addWidget(Color("cyan"), 3, 1)

        dgridlayout.addWidget(Color("green"), 1, 2)
        dgridlayout.addWidget(Color("grey"), 2, 2)
        dgridlayout.addWidget(Color("orange"), 3, 2)

        dgrid.setLayout(dgridlayout)

        alayout.addWidget(dgrid)
        alayout.addWidget(Color("yellow"))
        alayout.addWidget(Color("orange"))
        a.setLayout(alayout)

        qlayout.addWidget(a)

        outerLayout.addWidget(w)
        outerLayout.addWidget(q)

        widget.setLayout(outerLayout)
        self.setCentralWidget(widget)

    @QtCore.pyqtSlot(dict)
    def on_new_telemetry(self, telemetry: dict):
        # logger.info("Received Temp: %s", telemetry["temperature"])
        self.received_data = telemetry
        self.temperature.setText(str(telemetry["temperature"]))
        self.pressure.setText(str(telemetry["pressure"]))
        self.altitude.setText(str(telemetry["altitude"]))
        # self.my_label_2.setText(str(telemetry["temperature"]))

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
