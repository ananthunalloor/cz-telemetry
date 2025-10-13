import matplotlib.pyplot as plt
from kivy_garden.matplotlib.backend_kivyagg import FigureCanvasKivyAgg
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout


class MyApp(App):
    def build(self):
        box = BoxLayout()

        box.add_widget(FigureCanvasKivyAgg(plt.gcf()))
        return box


def main():
    fig = plt.figure()
    ax = fig.add_subplot(projection="3d")

    ax.set(xlim3d=(0, 1), xlabel="X")
    ax.set(ylim3d=(0, 1), ylabel="Y")
    ax.set(zlim3d=(0, 1), zlabel="Z")
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
