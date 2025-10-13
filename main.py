from kivy.app import runTouchApp
from kivy.lang import Builder


def main():
    runTouchApp(
        Builder.load_string("""
Button:
    text: 'Hello world with uv!'
""")
    )


if __name__ == "__main__":
    import logging

    LOGGING_FORMAT = "%(asctime)s | %(levelname)s | %(module)s | %(message)s"
    logger = logging.getLogger(__name__)
    logging.basicConfig(
        level=logging.INFO,
        format=LOGGING_FORMAT,
    )

    logger.info("Starting application")
    main()
    logger.info("Application finished")
