"""Andor reader module (:mod:`pymanip.video.andor.reader`)
==========================================================

This module implements simple pure-python reader for Andor DAT and SIF
files.

.. autoclass:: AndorAcquisitionReader
   :members:
   :private-members:

.. autoclass:: SIFFile
   :members:
   :private-members:

"""

import os
import io
import configparser
import glob
from datetime import datetime

import numpy as np


class AndorAcquisitionReader:
    """This class is a simple pure-python reader for Andor DAT spool files in a directory.

    :param acquisition_folder: the folder in which to read the DAT spool files
    :type acquisition_folder: str

    """

    def __init__(self, acquisition_folder):
        """Constructor method
        """
        config = configparser.ConfigParser()
        with io.open(
            os.path.join(acquisition_folder, "acquisitionmetadata.ini"),
            "r",
            encoding="utf-8-sig",
        ) as f:
            config.read_file(f)
            self.metadata = {
                "AOIWidth": int(config["data"]["aoiwidth"]),
                "AOIHeight": int(config["data"]["aoiheight"]),
                "AOIStride": int(config["data"]["aoistride"]),
                "PixelEncoding": str(config["data"]["pixelencoding"]),
                "ImageSizeBytes": int(config["data"]["imagesizebytes"]),
                "ImagesPerFile": int(config["multiimage"]["imagesperfile"]),
            }

            self.dt = np.uint16 if self.metadata["PixelEncoding"] == "Mono16" else None
            if not self.dt:
                raise ValueError("Unsupported pixel encoding")

            self.file_list = glob.glob(os.path.join(acquisition_folder, "*spool.dat"))
            self.file_list.sort()

    def images(self):
        """This generator method yields the images found in the folder.
        """
        for i in range(len(self)):
            yield self[i]

    def __getitem__(self, key):
        """This method returns the nth image in the folder.

        :param key: image number
        :type key: int

        """
        bname = os.path.basename(self.file_list[key])
        n = bname.find("spool")
        timestamp = int(bname[:n]) / 1e6
        with open(self.file_list[key], "rb") as f:
            _ = f.read(40)
            data = np.fromfile(f, dtype=self.dt).reshape(
                (self.metadata["AOIHeight"], self.metadata["AOIWidth"])
            )
        return timestamp, data[::-1, :]

    def __len__(self):
        """Number of images in folder.
        """
        return len(self.file_list)


class SIFFile:
    """This class implements a pure-python reader for Andor SIF files.

    :param filename: the SIF filename
    :type filename: str

    """

    def __init__(self, filename):
        """Constructor method
        """
        self.filename = filename

    def open(self):
        """This method opens the file.
        """
        self.f = open(self.filename, "rb")

    def close(self):
        """This method closes the file.
        """
        self.f.close()

    def __enter__(self):
        """Context manager enter method
        """
        self.open()
        self.read_header()
        return self

    def __exit__(self, type_, value, cb):
        """Context manager exit method
        """
        self.close()

    def read_header(self):
        """This method reads the header in the SIF file.
        """
        self.filetype = self.f.readline().decode("ascii").strip()
        if self.filetype != "Andor Technology Multi-Channel File":
            raise ValueError("Wrong file type")

        tokens = self.f.readline().decode("ascii").strip().split()
        self.version = int(tokens[0])
        self.signal_present = int(tokens[1])
        if self.version != 65538:
            raise ValueError("Unknown version")

        # InstaImage
        TInstaImage = dict()
        tokens = iter(self.f.readline().split())
        TInstaImage["version"] = int(next(tokens))
        TInstaImage["type"] = int(next(tokens))
        TInstaImage["active"] = int(next(tokens))
        TInstaImage["structure_version"] = int(next(tokens))
        TInstaImage["timedate"] = datetime.fromtimestamp(int(next(tokens)))
        TInstaImage["temperature"] = float(next(tokens))
        TInstaImage["head"] = next(tokens)
        TInstaImage["store_type"] = next(tokens)
        TInstaImage["data_type"] = next(tokens)
        TInstaImage["mode"] = next(tokens)
        TInstaImage["trigger_source"] = next(tokens)
        TInstaImage["trigger_level"] = float(next(tokens))
        TInstaImage["exposure_time"] = float(next(tokens))
        TInstaImage["delay"] = float(next(tokens))
        TInstaImage["integration_cycle_time"] = float(next(tokens))
        TInstaImage["no_integrations"] = int(next(tokens))
        TInstaImage["sync"] = next(tokens)
        TInstaImage["kinetic_cycle_time"] = float(next(tokens))
        TInstaImage["pixel_readout_time"] = float(next(tokens))
        TInstaImage["no_points"] = int(next(tokens))
        TInstaImage["fast_track_height"] = int(next(tokens))
        TInstaImage["gain"] = float(next(tokens))
        TInstaImage["gate_delay"] = float(next(tokens))
        TInstaImage["gate_width"] = float(next(tokens))
        TInstaImage["gate_step"] = float(next(tokens))
        TInstaImage["track_height"] = int(next(tokens))
        TInstaImage["series_length"] = int(next(tokens))
        TInstaImage["read_pattern"] = next(tokens)
        TInstaImage["shutter_delay"] = next(tokens)
        TInstaImage["st_centre_row"] = int(next(tokens))
        TInstaImage["mt_offset"] = int(next(tokens))
        TInstaImage["operation_mode"] = int(next(tokens))
        TInstaImage["FlipX"] = int(next(tokens))
        TInstaImage["FlipY"] = int(next(tokens))
        TInstaImage["Clock"] = int(next(tokens))
        TInstaImage["AClock"] = int(next(tokens))
        TInstaImage["MCP"] = int(next(tokens))
        TInstaImage["Prop"] = int(next(tokens))
        TInstaImage["IOC"] = int(next(tokens))
        TInstaImage["Freq"] = float(next(tokens))
        TInstaImage["VertClockAmp"] = float(next(tokens))
        TInstaImage["data_v_shift_speed"] = float(next(tokens))
        TInstaImage["OutputAmp"] = float(next(tokens))
        TInstaImage["PreAmpGain"] = float(next(tokens))
        TInstaImage["Serial"] = next(tokens)
        TInstaImage["NumPulses"] = int(next(tokens))
        TInstaImage["mFrameTransferAcqMode"] = int(next(tokens))
        if TInstaImage["version"] != 65550:
            TInstaImage["unstabilizedTemperature"] = float(next(tokens))
            TInstaImage["mBaselineClamp"] = float(next(tokens))
        TInstaImage["mPreScan"] = next(tokens)
        if TInstaImage["version"] in (65555, 65558, 65567):
            TInstaImage["mEMRealGain"] = next(tokens)
            TInstaImage["mBaselineOffset"] = next(tokens)
            TInstaImage["mSWVersion"] = next(tokens)
        if TInstaImage["version"] in (65558, 65567):
            TInstaImage["miGateMode"] = next(tokens)
            TInstaImage["mSWDllVer"] = next(tokens)
            TInstaImage["mSWDllRev"] = next(tokens)
            TInstaImage["mSWDllRel"] = next(tokens)
            TInstaImage["mSWDllBld"] = next(tokens)
        if TInstaImage["version"] == 65567:
            next(tokens)
            next(tokens)
        TInstaImage["len"] = int(next(tokens))

        TInstaImage["head_model"] = self.f.readline().decode("ascii").strip()
        tokens = iter(self.f.readline().decode("ascii").strip().split())

        TInstaImage["detector_format_x"] = next(tokens)
        TInstaImage["detector_format_y"] = next(tokens)
        TInstaImage["len2"] = next(tokens)

        TInstaImage["filename"] = self.f.readline().decode("ascii").strip()

        self.TInstaImage = TInstaImage

        # UserText
        TUserText = dict()
        tokens = iter(self.f.readline().decode("ascii").strip().split())
        TUserText["version"] = int(next(tokens))
        if TUserText["version"] != 65538:
            raise ValueError("Unknown TUserText version")
        TUserText["len"] = self.f.readline()
        TUserText["usertext"] = self.f.readline()
        self.f.readline()
        self.f.readline()
        self.f.readline()
        self.f.readline()
        self.f.readline()
        self.TUserText = TUserText

        # Shutter
        TShutter = dict()
        tokens = iter(self.f.readline().decode("ascii").strip().split())
        TShutter["version"] = int(next(tokens))
        if TShutter["version"] != 65538:
            raise ValueError("Unknown Shutter version")
        TShutter["type"] = next(tokens)
        TShutter["mode"] = next(tokens)
        TShutter["custom_bg_mode"] = next(tokens)
        TShutter["custom_mode"] = next(tokens)
        TShutter["custom_time"] = next(tokens)
        TShutter["opening_time"] = next(tokens)
        self.TShutter = TShutter

        # ShamrockSave
        TShamrockSave = dict()
        tokens = iter(self.f.readline().decode("ascii").strip().split())
        TShamrockSave["version"] = int(next(tokens))
        if TShamrockSave["version"] not in (65536, 65538, 65540):
            raise ValueError("Unknown ShamrockSave version")
        try:
            TShamrockSave["isActive"] = next(tokens)
            TShamrockSave["waveDrivePresent"] = next(tokens)
            TShamrockSave["wavelength"] = next(tokens)
            TShamrockSave["gratingTurretPresent"] = next(tokens)
            TShamrockSave["grating"] = next(tokens)
            TShamrockSave["gratingLines"] = next(tokens)
            TShamrockSave["gratingBlaze"] = next(tokens)
            TShamrockSave["slitPresent"] = next(tokens)
            TShamrockSave["slitWidth"] = next(tokens)
            TShamrockSave["flipperMirrorPresent"] = next(tokens)
            TShamrockSave["flipperPort"] = next(tokens)
            TShamrockSave["filterPresent"] = next(tokens)
            TShamrockSave["filterIndex"] = next(tokens)
            TShamrockSave["len"] = next(tokens)
            TShamrockSave["filterLabel"] = next(tokens)
            TShamrockSave["accessoryAttached"] = next(tokens)
            TShamrockSave["port1State"] = next(tokens)
            TShamrockSave["port2State"] = next(tokens)
            TShamrockSave["port3State"] = next(tokens)
            TShamrockSave["inputPortState"] = next(tokens)
            TShamrockSave["outputSlitPresent"] = next(tokens)
            TShamrockSave["outputSlitWidth"] = next(tokens)
        except StopIteration:
            pass

        for i in range(6):
            self.f.readline()

        self.TShamrockSave = TShamrockSave

        # SpectrographSave
        TSpectrographSave = dict()
        raw = self.f.readline().decode("ascii").strip()
        tokens = iter(raw.split())
        TSpectrographSave["version"] = int(next(tokens))
        TSpectrographSave["isActive"] = next(tokens)
        TSpectrographSave["wavelength"] = next(tokens)
        TSpectrographSave["gratingLines"] = next(tokens)
        tokens = iter(self.f.readline().decode("ascii").strip().split())
        TSpectrographSave["unspecified"] = next(tokens)
        TSpectrographSave["spectrographName"] = next(tokens)
        TSpectrographSave["unspecified2"] = next(tokens)
        self.f.readline()
        self.TSpectrographSave = TSpectrographSave

        # CalibImage
        TCalibImage = dict()
        raw = self.f.readline().decode("ascii").strip()
        tokens = iter(raw.split())
        TCalibImage["version"] = int(next(tokens))
        if TCalibImage["version"] != 65539:
            raise ValueError("Unknown TCalibImage version")

        # TImage
        while True:
            raw = self.f.readline()
            if raw.startswith(b"Pixel number65541"):
                raw = raw[12:]
                break

        TImage = dict()
        tokens = iter(raw.split())
        TImage["version"] = int(next(tokens))
        if TImage["version"] not in (65538, 65541):
            raise ValueError("Unknown TImage version")
        TImage["image_format.left"] = int(next(tokens))
        TImage["image_format.top"] = int(next(tokens))
        TImage["image_format.right"] = int(next(tokens))
        TImage["image_format.bottom"] = int(next(tokens))
        TImage["no_images"] = int(next(tokens))
        TImage["no_subimages"] = int(next(tokens))
        TImage["total_length"] = int(next(tokens))
        TImage["image_length"] = int(next(tokens))
        self.TImage = TImage

        # TSubImage
        TSubImage = dict()
        for subimage_index in range(TImage["no_subimages"]):
            raw = self.f.readline().decode("ascii").strip()
            tokens = iter(raw.split())
            TSubImage["version"] = int(next(tokens))
            if TSubImage["version"] != 65538:
                raise ValueError("Unknown SubImage version")
            TSubImage["left"] = int(next(tokens))
            TSubImage["top"] = int(next(tokens))
            TSubImage["right"] = int(next(tokens))
            TSubImage["bottom"] = int(next(tokens))
            TSubImage["vertical_bin"] = int(next(tokens))
            TSubImage["horizontal_bin"] = int(next(tokens))
            TSubImage["subimage_offset"] = int(next(tokens))
        self.TSubImage = TSubImage

        # timestamp
        self.timestamp = np.zeros((TImage["no_images"],))
        for i in range(TImage["no_images"]):
            self.timestamp[i] = int(self.f.readline().decode("ascii").strip())

        self.f.readline()

        for i in range(TImage["no_images"]):
            self.f.readline()

        self.datastart = self.f.tell()

        TImage["dimX"] = TImage["image_format.right"] - TImage["image_format.left"] + 1
        TImage["dimY"] = TImage["image_format.top"] - TImage["image_format.bottom"] + 1
        TSubImage["dimX"] = TSubImage["right"] - TSubImage["left"] + 1
        TSubImage["dimY"] = TSubImage["top"] - TSubImage["bottom"] + 1
        self.Npixels = TSubImage["dimX"] * TSubImage["dimY"]

    def read_nth_frame(self, n):
        """This method reads and returns the nth frame in the file.

        :param n: frame number to read
        :type n: int
        :return: frame
        :rtype: numpy.ndarray

        """
        self.f.seek(self.datastart + self.Npixels * n * 4)
        return self.read_frame()

    def read_frame(self):
        """The methods reads the next frame in file.

        :return: frame
        :rtype: numpy.ndarray
        """
        return np.fromfile(self.f, dtype=np.float32, count=self.Npixels).reshape(
            (self.TSubImage["dimY"], self.TSubImage["dimX"])
        )[::-1, :]

    def images(self):
        """This generator yields all the frames in the file.
        """
        self.f.seek(self.datastart)
        for ts in self.timestamp:
            yield ts, self.read_frame()

    def __len__(self):
        """Number of frames in file.
        """
        return self.timestamp.size
