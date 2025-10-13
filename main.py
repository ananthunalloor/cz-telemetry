import matplotlib.pyplot as plt
from kivy_garden.matplotlib.backend_kivyagg import FigureCanvasKivyAgg
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout

plt.plot([1, 23, 2, 4])
plt.ylabel("some numbers")


class MyApp(App):
    def build(self):
        box = BoxLayout()
        box.add_widget(FigureCanvasKivyAgg(plt.gcf()))
        return box


def main():
    MyApp().run()


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
