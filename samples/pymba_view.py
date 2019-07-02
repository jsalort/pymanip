"""

This file comes from pydc1394 examples.
Written by jordens.
Tested on Linux.
git clone https://github.com/jordens/pydc1394

"""
import time
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui

from pymba import Vimba


class CameraPlot:
    def __init__(self):
        self.vimba = Vimba()
        self.vimba.startup()
        self.system = self.vimba.getSystem()
        self.cameraIds = self.vimba.getCameraIds()
        self.init_win()
        self.init_camera()

    def init_win(self):
        self.win = QtGui.QMainWindow()
        self.win.show()
        self.win.resize(600, 400)
        self.win.setWindowTitle("pymba + pyqtgraph")
        self.img = pg.ImageView()
        self.win.setCentralWidget(self.img)

    def init_camera(self):
        print("Vimba version:", self.vimba.getVersion())
        print("Found {:d} cameras.".format(len(self.cameraIds)))
        self.cam = self.vimba.getCamera(self.cameraIds[0])
        self.cam.openCamera()
        info = self.cam.getInfo()
        print("cameraName:", info.cameraName.decode("ascii"))
        print("interfaceIdString:", info.interfaceIdString.decode("ascii"))
        print("modelName:", info.modelName.decode("ascii"))

    def start_camera(self):
        self.cam.AcquisitionMode = "Continuous"
        self.cam.IIDCPhyspeed = "S800"
        self.cam.PixelFormat = "Mono16"
        self.cam.TriggerMode = "Off"
        self.cam.AcquisitionFrameRate = 20.0

        self.frame = self.cam.getFrame()
        self.frame.announceFrame()
        self.cam.startCapture()
        self.cam.runFeatureCommand("AcquisitionStart")

    def process_images(self):
        QtCore.QTimer.singleShot(50, self.process_images)
        self.frame.queueFrameCapture()
        self.frame.waitFrameCapture()
        im = self.frame.getImage().T
        self.img.setImage(
            im, autoRange=False, autoLevels=False, autoHistogramRange=False
        )

    def stop_camera(self):
        self.cam.runFeatureCommand("AcquisitionStop")
        self.cam.endCapture()
        self.cam.revokeAllFrames()

    def deinit_camera(self):
        self.vimba.shutdown()


if __name__ == "__main__":
    app = QtGui.QApplication([])
    cam = CameraPlot()
    try:
        cam.start_camera()
        time.sleep(0.5)
        cam.process_images()
        cam.img.autoRange()
        cam.img.autoLevels()
        QtGui.QApplication.instance().exec_()
    finally:
        cam.stop_camera()
        cam.deinit_camera()
