from src.ui import MainWindow
import sys
from PyQt6.QtWidgets import QApplication


def main():
    logger.info("Starting CZ Telemetry application")
    app = QApplication([])
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    import logging

    logger = logging.getLogger()
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s | %(levelname)-5s | %(module)-4s:%(lineno)-3d | %(message)s"
            )
        )
        logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    main()
