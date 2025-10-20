from src.telemetry import Telemetry
from src.ui import MainWindow
import sys
from PyQt6.QtCore import QThread
from PyQt6.QtWidgets import QApplication


def main():
    logger.info("Starting CZ Telemetry application")

    app = QApplication([])
    telemetry = Telemetry(port="COM15")

    thread = QThread()
    telemetry.moveToThread(thread)
    thread.started.connect(telemetry.run)
    telemetry.finished.connect(thread.quit)
    telemetry.finished.connect(telemetry.deleteLater)
    thread.finished.connect(thread.deleteLater)

    window = MainWindow(telemetry=telemetry)
    window.show()
    thread.start()

    def on_about_to_quit():
        telemetry.stop()
        thread.quit()
        thread.wait()

    app.aboutToQuit.connect(on_about_to_quit)
    sys.exit(app.exec())


if __name__ == "__main__":
    import logging

    logger = logging.getLogger()
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s | %(levelname)-6s | %(module)-9s:%(lineno)-3d | %(message)s"
            )
        )
        logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    main()
