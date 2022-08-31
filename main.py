from PyQt5 import uic
from PyQt5.QtWidgets import *
from PyQt5.QtCore import QThread, pyqtSignal, Qt
import pyqtgraph as pg
from serial import Serial
from time import time, sleep
import csv


class MainWindow(QMainWindow):
    time = [0]
    known_ids = []
    data_lines = {}
    colors = ['r', 'b', 'g']
    max_data_length = 30

    def __init__(self):
        super().__init__()
        self.com = None
        self.serial = None
        uic.loadUi("ui/main_window.ui", self)
        self.actionExporter.triggered.connect(self.export_action)
        self.graphWidget = pg.PlotWidget()
        self.graph_slider = QSlider()
        self.graph_slider.setValue(30)
        self.create_graph()

        self.is_paused = False

        self.resetButton.clicked.connect(self.reset)
        self.pauseButton.clicked.connect(self.handle_paused)
        self.graph_slider.valueChanged.connect(self.set_max_data_length)
        self.startButton.clicked.connect(self.start)

        self.start_time = time()
        self.show()

    def start(self):
        port_com = self.lineEditCom.text()
        baudrate = self.spinBoxBaudrate.value()
        try :
            self.serial = Serial(baudrate=baudrate, port=port_com)
        except Exception as e:
            print(e)
        self.com = ComThread(self.serial)
        self.com.res_signal.connect(self.handle_response)
        self.com.start()
        self.startButton.setText("Stop")
        self.startButton.clicked.connect(self.stop)

    def stop(self):
        self.com.stop()
        self.startButton.setText("Start")
        self.startButton.clicked.connect(self.start)
        self.serial.close()

    def export_action(self):
        with open('C:/Users/Guillaume/PycharmProjects/Debugger/export.csv', 'w',encoding='UTF8', newline='') as f:
            # create the csv writer
            writer = csv.writer(f)

            # write the header
            writer.writerow(self.known_ids)

            # write multiple rows
            for item in self.data_lines.values():
                print(item[0])
                writer.writerow(item[0])

    def reset(self):
        self.known_ids = []
        self.data_lines = {}
        self.graphWidget.clear()

    def create_graph(self):
        self.graphWidget.setBackground('w')
        self.graphWidget.showGrid(x=True, y=True)
        self.graphWidget.addLegend()
        self.graphWidget.setLabel('left', "<span style=\"color:red;font-size:20px\">Received Data (°C)</span>")
        self.graphWidget.setLabel('bottom', "<span style=\"color:red;font-size:20px\">Time (s)</span>")
        self.graph_slider.setOrientation(1)
        self.graph_slider.setMaximum(100)
        self.graph_slider.setMinimum(10)
        #self.graph_layout.addWidget(self.graph_slider)
        self.verticalLayout.addWidget(self.graphWidget)
        self.verticalLayout.addWidget(self.graph_slider)

    def handle_paused(self):
        self.is_paused = not self.is_paused
        print(self.is_paused)

    def handle_response(self, msg):
        t = time() - self.start_time

        try:
            id, arg = msg.split(" ")
        except:
            return

        self.textEdit.append(f"{id} {arg}")

        if id not in self.known_ids:
            self.known_ids.append(id)
            pen = pg.mkPen(color=self.get_color())
            self.data_lines[id] = ([], [], self.graphWidget.plot([], [], name=id, pen=pen))
            #self.graphWidget.addLegend()

        self.data_lines[id][0].append(float(arg))
        self.data_lines[id][1].append(t)
        self.time.append(t)

        if not self.is_paused:

            plot_data = self.get_data(id)
            self.data_lines[id][2].setData(plot_data[0], plot_data[1])

    def get_color(self):
        color = self.colors.pop()
        self.colors.insert(0, color)
        return color

    def get_data(self, index):
        data, time = self.data_lines[index][0],  self.data_lines[index][1]
        if len(data)>self.max_data_length:
            self.graphWidget.setXRange(time[-self.max_data_length], time[-1])

        return time, data

    def set_max_data_length(self, value):
        self.max_data_length = value
        if self.is_paused:
            for id in self.known_ids:
                plot_data = self.get_data(id)
                self.data_lines[id][2].setData(plot_data[0], plot_data[1])


class ComThread(QThread):

    res_signal = pyqtSignal(str)

    def __init__(self, ser):
        super().__init__()
        self.serial = ser
        self.is_running = True

    def run(self):
        while self.is_running:
            try:
                res = self.serial.read_until(b'\n', 128)
                print(res)
            except Exception as e:
                print(e)
                break
            self.res_signal.emit(res.decode('ascii'))
        self.serial.close()

    def stop(self):
        print("stopping")
        self.is_running = False


if __name__ == '__main__':
    app = QApplication([])
    w = MainWindow()
    app.exec_()
