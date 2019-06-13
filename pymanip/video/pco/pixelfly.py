"""

PCO PixelFly Wrapper

"""

import ctypes
import ctypes.wintypes
from enum import IntEnum
from typing import Tuple, Iterable
import datetime

# Open DLL
pixelfly_dllpath = r"C:\Program Files\Digital Camera Toolbox\Camware4\SC2_Cam.dll"
try:
    pixelfly_dll = ctypes.windll.LoadLibrary(pixelfly_dllpath)
except OSError:
    print(pixelfly_dllpath, "not found")
    raise ImportError


# General constants
class PCO_ErrorLayer(IntEnum):
    PCO_ERROR_FIRMWARE = 0x00001000  # error inside the firmware
    PCO_ERROR_DRIVER = 0x00002000  # error inside the driver
    PCO_ERROR_SDKDLL = 0x00003000  # error inside the SDK-dll
    PCO_ERROR_APPLICATION = 0x00004000  # error inside the application


class PCO_ErrorWarningSource(IntEnum):
    SC2_ERROR_PCOCAM_POWER_CPLD = 0x00010000  # error at CPLD in pco.power unit
    SC2_ERROR_PCOCAM_HEAD_UP = 0x00020000  # error at uP of head board in pco.camera
    SC2_ERROR_PCOCAM_MAIN_UP = 0x00030000  # error at uP of main board in pco.camera
    SC2_ERROR_PCOCAM_FWIRE_UP = (
        0x00040000
    )  # error at uP of firewire board in pco.camera
    SC2_ERROR_PCOCAM_MAIN_FPGA = 0x00050000  # error at FPGA of main board in pco.camera
    SC2_ERROR_PCOCAM_HEAD_FPGA = 0x00060000  # error at FGPA of head board in pco.camera
    SC2_ERROR_PCOCAM_MAIN_BOARD = 0x00070000  # error at main board in pco.camera
    SC2_ERROR_PCOCAM_HEAD_CPLD = 0x00080000  # error at CPLD of head board in pco.camera
    SC2_ERROR_SENSOR = 0x00090000  # error at image sensor (CCD or CMOS)
    SC2_ERROR_SDKDLL = 0x000A0000  # error inside the SDKDLL
    SC2_ERROR_DRIVER = 0x000B0000  # error inside the driver
    SC2_ERROR_POWER = 0x000D0000  # error within power unit
    PCO_ERROR_CAMWARE = 0x00100000  # error in CamWare (also some kind of "device")
    PCO_ERROR_CONVERTDLL = 0x00110000  # error inside the convert dll


# The following bits values are those returned by
# PCO_GetCameraHealthStatus
# cf pco.sdk_manual page 36, 37, 38


class PCO_WarningBits(IntEnum):
    WARNING_POWER_SUPPLY_VOLTAGE = 0x00000001
    WARNING_POWER_SUPPLY_TEMPERATURE = 0x00000002
    WARNING_CAMERA_TEMPERATURE = 0x00000004
    WARNING_SENSOR_TEMPERATURE = 0x00000008
    WARNING_BATTERY_DISCHARGED = 0x00000010
    WARNING_OFFSET_REGUL_RANGE = 0x00000020


class PCO_ErrorBits(IntEnum):
    ERROR_POWER_SUPPLY_VOLTAGE = 0x00000001
    ERROR_POWER_SUPPLY_TEMPERATURE = 0x00000002
    ERROR_CAMERA_TEMPERATURE = 0x00000004
    ERROR_SENSOR_TEMPERATURE = 0x00000008
    ERROR_BATTERY_DISCHARGED = 0x00000010
    ERROR_CAMERA_INTERFACE_FAILURE = 0x00010000
    ERROR_CAMERA_RAM_FAILURE = 0x00020000
    ERROR_CAMERA_MAIN_BOARD_FAILURE = 0x00040000
    ERROR_CAMERA_HEAD_BOARD_FAILURE = 0x00080000


class PCO_StatusBits(IntEnum):
    STATUS_DEFAULT_STATE = 0x00000001
    STATUS_SETTINGS_VALID = 0x00000002
    STATUS_RECORDING_STATE = 0x00000004
    STATUS_SENSOR_READOUT_STATE = 0x00000008
    STATUS_FRAMERATE_STATE = 0x00000010
    STATUS_TRIGGERED_STOP = 0x00000020
    STATUS_CAMERA_LOCKED_TO_EXT = 0x00000040
    STATUS_BATTERY_CONNECTED = 0x00000080
    STATUS_POWER_SAVE = 0x00000100
    STATUS_POWER_SAVE_LEFT = 0x00000200
    STATUS_CAMERA_LOCKED_TO_IRIG = 0x00000400
    STATUS_RESERVED = 0x80000000


# Error handling


class PCO_Error(Exception):
    pass


class PCO_Warning(RuntimeWarning):
    pass


def PCO_manage_error(ret_code):
    if ret_code != 0:
        f = pixelfly_dll.PCO_GetErrorText
        f.argtypes = (ctypes.wintypes.DWORD, ctypes.c_char_p, ctypes.wintypes.DWORD)
        desc = ctypes.create_string_buffer(256)
        f(ret_code, desc, 256)
        description = desc.raw.decode("ascii")
        if "warning" in description:
            raise PCO_Warning(description)
        else:
            raise PCO_Error(description)


# C Structure definitions
class PCO_SC2_Hardware_DESC(ctypes.Structure):
    _fields_ = [
        ("szName", ctypes.c_char * 16),
        ("wBatchNo", ctypes.wintypes.WORD),
        ("wRevision", ctypes.wintypes.WORD),
        ("wVariant", ctypes.wintypes.WORD),
        ("ZZwDummy", ctypes.wintypes.WORD * 20),
    ]


PCO_MAXVERSIONHW = 10


class PCO_HW_Vers(ctypes.Structure):
    _fields_ = [
        ("BoardNum", ctypes.wintypes.WORD),
        ("Board", PCO_SC2_Hardware_DESC * PCO_MAXVERSIONHW),
    ]


class PCO_SC2_Firmware_DESC(ctypes.Structure):
    _fields_ = [
        ("szName", ctypes.c_char * 16),
        ("bMinorRev", ctypes.wintypes.BYTE),
        ("bMajorRev", ctypes.wintypes.BYTE),
        ("wVariant", ctypes.wintypes.WORD),
        ("ZZwDummy", ctypes.wintypes.WORD * 22),
    ]


PCO_MAXVERSIONFW = 10


class PCO_FW_Vers(ctypes.Structure):
    _fields_ = [
        ("DeviceNum", ctypes.wintypes.WORD),
        ("Device", PCO_SC2_Firmware_DESC * PCO_MAXVERSIONFW),
    ]


class PCO_CameraType(ctypes.Structure):
    _fields_ = [
        ("wSize", ctypes.wintypes.WORD),
        ("wCamType", ctypes.wintypes.WORD),
        ("wCamSubType", ctypes.wintypes.WORD),
        ("ZZwAlignDummy1", ctypes.wintypes.WORD),
        ("dwSerialNumber", ctypes.wintypes.DWORD),
        ("dwHWVersion", ctypes.wintypes.DWORD),
        ("dwFWVersion", ctypes.wintypes.DWORD),
        ("wInterfaceType", ctypes.wintypes.WORD),
        ("strHardwareVersion", PCO_HW_Vers),
        ("strFirmwareVersion", PCO_FW_Vers),
        ("ZZwDummy", ctypes.wintypes.WORD * 39),
    ]

    def __init__(self):
        super(PCO_CameraType, self).__init__()
        self.wSize = ctypes.sizeof(PCO_CameraType)

    def __str__(self):
        return """CamType: {type:}
CamSubType: {subtype:}
Serial number: {serial:}
HW Version: {hw:}
FW Version: {fw:}
Interface type: {inter:}""".format(
            type=self.wCamType,
            subtype=self.wCamSubType,
            serial=self.dwSerialNumber,
            hw=self.dwHWVersion,
            fw=self.dwFWVersion,
            inter=self.wInterfaceType,
        )


class PCO_General(ctypes.Structure):
    _fields_ = [
        ("wSize", ctypes.wintypes.WORD),
        ("ZZwAlignDummy1", ctypes.wintypes.WORD),
        ("strCamType", PCO_CameraType),
        ("dwCamHealthWarnings", ctypes.wintypes.DWORD),
        ("dwCamHealthErrors", ctypes.wintypes.DWORD),
        ("dwCamHealthStatus", ctypes.wintypes.DWORD),
        ("sCCDTemperature", ctypes.wintypes.SHORT),
        ("sCamTemperature", ctypes.wintypes.SHORT),
        ("sPowerSupplyTemperature", ctypes.wintypes.SHORT),
        ("ZZwDummy", ctypes.wintypes.WORD * 37),
    ]

    def __init__(self):
        super(PCO_General, self).__init__()
        self.wSize = ctypes.sizeof(PCO_General)
        self.strCamType.__init__()

    def __str__(self):
        return """CamType = [{camType:}]
Health Warnings = {warn:}
Health Errors = {err:}
Health Status = {stat:}
CCD Temperature = {ccd:}
Power Supply Temperature = {power:}""".format(
            camType=str(self.strCamType),
            warn=self.dwCamHealthWarnings,
            err=self.dwCamHealthErrors,
            stat=self.dwCamHealthStatus,
            ccd=self.sCCDTemperature,
            power=self.sPowerSupplyTemperature,
        )


PCO_RECORDINGDUMMY = 22


class PCO_Recording(ctypes.Structure):
    _fields_ = [
        ("wSize", ctypes.wintypes.WORD),
        ("wStorageMode", ctypes.wintypes.WORD),
        ("wRecSubmode", ctypes.wintypes.WORD),
        ("wRecState", ctypes.wintypes.WORD),
        ("wAcquMode", ctypes.wintypes.WORD),
        ("wAcquEnableStatus", ctypes.wintypes.WORD),
        ("ucDay", ctypes.wintypes.BYTE),
        ("ucMonth", ctypes.wintypes.BYTE),
        ("wYear", ctypes.wintypes.WORD),
        ("wHour", ctypes.wintypes.WORD),
        ("ucMin", ctypes.wintypes.BYTE),
        ("ucSec", ctypes.wintypes.BYTE),
        ("wTimeSampMode", ctypes.wintypes.WORD),
        ("wRecordStopEventMode", ctypes.wintypes.WORD),
        ("dwRecordStopDelayImages", ctypes.wintypes.DWORD),
        ("wMetaDataMode", ctypes.wintypes.WORD),
        ("wMetaDataSize", ctypes.wintypes.WORD),
        ("wMetaDataVersion", ctypes.wintypes.WORD),
        ("ZZwDummy1", ctypes.wintypes.WORD),
        ("dwAcquModeExNumberImages", ctypes.wintypes.DWORD),
        ("dwAcquModeExReserved", ctypes.wintypes.DWORD * 4),
        ("ZZwDummy", ctypes.wintypes.WORD * PCO_RECORDINGDUMMY),
    ]

    def __init__(self):
        super(PCO_Recording, self).__init__()
        self.wSize = ctypes.sizeof(PCO_Recording)


class PCO_Description(ctypes.Structure):
    _fields_ = [
        ("wSize", ctypes.wintypes.WORD),
        ("wSensorTypeDESC", ctypes.wintypes.WORD),
        ("wSensorSubTypeDESC", ctypes.wintypes.WORD),
        ("wMaxHorzResStdDESC", ctypes.wintypes.WORD),
        ("wMaxVertResStdDESC", ctypes.wintypes.WORD),
        ("wMaxHorzResExtDESC", ctypes.wintypes.WORD),
        ("wMaxVertResExtDESC", ctypes.wintypes.WORD),
        ("wDynResDESC", ctypes.wintypes.WORD),
        ("wMaxBinHorzDESC", ctypes.wintypes.WORD),
        ("wBinHorzSteppingDESC", ctypes.wintypes.WORD),
        ("wMaxBinVertDESC", ctypes.wintypes.WORD),
        ("wBinVertSteppingDESC", ctypes.wintypes.WORD),
        ("wRoiHorStepsDESC", ctypes.wintypes.WORD),
        ("wRoiVertStepsDESC", ctypes.wintypes.WORD),
        ("wNumADCsDESC", ctypes.wintypes.WORD),
        ("wMinSizeHorzDESC", ctypes.wintypes.WORD),
        ("dwPixelRateDESC", ctypes.wintypes.DWORD * 4),
        ("ZZdwDummypr", ctypes.wintypes.DWORD * 20),
        ("wConvFactDESC", ctypes.wintypes.WORD * 4),
        ("sCoolingSetPoints", ctypes.wintypes.SHORT * 10),
        ("ZZdwDummycv", ctypes.wintypes.WORD * 8),
        ("wSoftRoiHozStepsDESC", ctypes.wintypes.WORD),
        ("wSoftRoiVertStepsDESC", ctypes.wintypes.WORD),
        ("wIRDESC", ctypes.wintypes.WORD),
        ("wMinSizeVertDESC", ctypes.wintypes.WORD),
        ("dwMinDelayDESC", ctypes.wintypes.DWORD),
        ("dwMaxDelayDESC", ctypes.wintypes.DWORD),
        ("dwMinDelayStepDESC", ctypes.wintypes.DWORD),
        ("dwMinExposureDESC", ctypes.wintypes.DWORD),
        ("dwMaxExposureDESC", ctypes.wintypes.DWORD),
        ("dwMinExposureStepDESC", ctypes.wintypes.DWORD),
        ("dwMinDelayIRDESC", ctypes.wintypes.DWORD),
        ("dwMaxDelayIRDESC", ctypes.wintypes.DWORD),
        ("dwMinExposureIRDESC", ctypes.wintypes.DWORD),
        ("dwMaxExposureIRDESC", ctypes.wintypes.DWORD),
        ("wTimeTableDESC", ctypes.wintypes.WORD),
        ("wDoubleImageDESC", ctypes.wintypes.WORD),
        ("sMinCoolSetDESC", ctypes.wintypes.SHORT),
        ("sMaxCoolSetDESC", ctypes.wintypes.SHORT),
        ("sDefaultCoolSetDESC", ctypes.wintypes.SHORT),
        ("wPowerDownModeDESC", ctypes.wintypes.WORD),
        ("wOffsetRegulationDESC", ctypes.wintypes.WORD),
        ("wColorPatternDESC", ctypes.wintypes.WORD),
        ("wPatternTypeDESC", ctypes.wintypes.WORD),
        ("wDummy1", ctypes.wintypes.WORD),
        ("wDummy2", ctypes.wintypes.WORD),
        ("wNumCoolingSetpoints", ctypes.wintypes.WORD),
        ("dwGeneralCapsDESC1", ctypes.wintypes.DWORD),
        ("dwGeneralCapsDESC2", ctypes.wintypes.DWORD),
        ("dwExtSyncFrequency", ctypes.wintypes.DWORD * 4),
        ("dwGeneralCapsDESC3", ctypes.wintypes.DWORD),
        ("dwGeneralCapsDESC4", ctypes.wintypes.DWORD),
        ("ZZdwDummy", ctypes.wintypes.DWORD * 40),
    ]

    def __init__(self):
        super(PCO_Description, self).__init__()
        self.wSize = ctypes.sizeof(PCO_Description)

    @property
    def maximum_resolution_std(self):
        """
        Maximum (horz, vert) resolution in std mode
        """
        return (self.wMaxHorzResStdDESC, self.wMaxVertResStdDESC)

    @property
    def maximum_resolution_ext(self):
        """
        Maximum (horz, vert) resolution in ext mode
        """
        return (self.wMaxHorzResExtDESC, self.wMaxVertResExtDESC)

    @property
    def dynamic_resolution(self):
        """
        Dynamic resolution of ADC in bit
        """
        return self.wDynResDESC

    @property
    def possible_pixelrate(self):
        """
        Possible pixelrate in Hz
        """
        return tuple(self.dwPixelRateDESC)

    @property
    def possible_delay(self):
        """
        Min delay (ns), Max delay (ms), Step (ns)
        """
        return (self.dwMinDelayDESC, self.dwMaxDelayDESC, self.dwMinDelayStepDESC)

    @property
    def possible_exposure(self):
        """
        Min exposure (ns), Max exposure (ms), Step (ns)
        """
        return (
            self.dwMinExposureDESC,
            self.dwMaxExposureDESC,
            self.dwMinExposureStepDESC,
        )

    def nth_cap(self, n):
        return (self.dwGeneralCapsDESC1 >> n) & 0x0001 == 0x0001

    @property
    def general_capabilities(self):
        return {
            "Noisefilter available": self.nth_cap(0),
            "Hotpixelfilter available": self.nth_cap(1),
            "Hotpixel works only with noisefilter": self.nth_cap(2),
            "Timestamp ASCII only available (Timestamp mode 3 enabled)": self.nth_cap(
                3
            ),
            "Dataformat 2x12": self.nth_cap(4),
            "Record Stop Event available": self.nth_cap(5),
            "Hot Pixel correction": self.nth_cap(6),
            "Ext.Exp.Ctrl. not available": self.nth_cap(7),
            "Timestamp not available": self.nth_cap(8),
            "Acquire mode not available": self.nth_cap(9),
            "Dataformat 4x16": self.nth_cap(10),
            "Dataformat 5x16": self.nth_cap(11),
            "Camera has no internal recorder memory": self.nth_cap(12),
            "Camera can be set to fast timing mode (PIV)": self.nth_cap(13),
            "Camera can produce metadata": self.nth_cap(14),
            "Camera allows Set/GetFrameRate cmd": self.nth_cap(15),
            "Camera has Correlated Double Image Mode": self.nth_cap(16),
            "Camera has CCM": self.nth_cap(17),
            "Camera can be synched externally": self.nth_cap(18),
            "Global shutter setting not available": self.nth_cap(19),
            "Camera supports global reset rolling readout": self.nth_cap(20),
            "Camera supports extended acquire command": self.nth_cap(21),
            "Camera supports fan control command": self.nth_cap(22),
            "Camera vert.ROI must be symmetrical to horizontal axis": self.nth_cap(23),
            "Camera horz.ROI must be symmetrical to vertical axis": self.nth_cap(24),
            "Camera has cooling setpoints instead of cooling range": self.nth_cap(25),
            "HW_IO_SIGNAL_DESCRIPTOR available": self.nth_cap(30),
            "Enhanced descriptor available": self.nth_cap(31),
        }

    def __str__(self):
        desc = """Maximum resolution (STD): {:} x {:}
Maximum resolution (EXT): {:} x {:}
Dynamic resolution: {:} bits
Possible pixel rates: {:} Hz
Possible delay: min {:} ns, max {:} ms, step {:} ns
Possible exposure: min {:} ns, max {:} ms, step {:} ns""".format(
            self.maximum_resolution_std[0],
            self.maximum_resolution_std[1],
            self.maximum_resolution_ext[0],
            self.maximum_resolution_ext[1],
            self.dynamic_resolution,
            str(self.possible_pixelrate),
            self.possible_delay[0],
            self.possible_delay[1],
            self.possible_delay[2],
            self.possible_exposure[0],
            self.possible_exposure[1],
            self.possible_exposure[2],
        )
        caps_dict = self.general_capabilities
        caps = "\n".join([k + ":" + str(caps_dict[k]) for k in caps_dict])
        return desc + "\n" + caps


class PCO_Description2(ctypes.Structure):
    _fields_ = [
        ("wSize", ctypes.wintypes.WORD),
        ("ZZwAlignDummy1", ctypes.wintypes.WORD),
        ("dwMinPeriodicalTimeDESC2", ctypes.wintypes.DWORD),
        ("dwMaxPeriodicalTimeDESC2", ctypes.wintypes.DWORD),
        ("dwMinPeriodicalConditionDESC2", ctypes.wintypes.DWORD),
        ("dwMaxNumberOfExposuresDESC2", ctypes.wintypes.DWORD),
        ("lMinMonitorSignalOffsetDESC2", ctypes.wintypes.LONG),
        ("dwMaxMonitorSignalOffsetDESC2", ctypes.wintypes.DWORD),
        ("dwMinPeriodicalStepDESC2", ctypes.wintypes.DWORD),
        ("dwStartTimeDelayDESC2", ctypes.wintypes.DWORD),
        ("dwMinMonitorStepDESC2", ctypes.wintypes.DWORD),
        ("dwMinDelayModDESC2", ctypes.wintypes.DWORD),
        ("dwMaxDelayModDESC2", ctypes.wintypes.DWORD),
        ("dwMinDelayStepModDESC2", ctypes.wintypes.DWORD),
        ("dwMinExposureModDESC2", ctypes.wintypes.DWORD),
        ("dwMaxExposureModDESC2", ctypes.wintypes.DWORD),
        ("dwMinExposureStepModDESC2", ctypes.wintypes.DWORD),
        ("dwModulateCapsDESC2", ctypes.wintypes.DWORD),
        ("dwReserved", ctypes.wintypes.DWORD * 16),
        ("ZZdwDummy", ctypes.wintypes.DWORD * 41),
    ]

    def __init__(self):
        super(PCO_Description2, self).__init__()
        self.wSize = ctypes.sizeof(PCO_Description2)


NUM_MAX_SIGNALS = 20
NUM_SIGNALS = 4
NUM_SIGNAL_NAMES = 4


class PCO_Single_Signal_Desc(ctypes.Structure):
    _fields_ = [
        ("wSize", ctypes.wintypes.WORD),
        ("ZZwAlignDummy1", ctypes.wintypes.WORD),
        ("strSignalName", (ctypes.c_char * 25) * NUM_SIGNAL_NAMES),
        ("wSignalDefinitions", ctypes.wintypes.WORD),
        ("wSignalTypes", ctypes.wintypes.WORD),
        ("wSignalPolarity", ctypes.wintypes.WORD),
        ("wSignalFilter", ctypes.wintypes.WORD),
        ("dwDummy", ctypes.wintypes.DWORD * 22),
    ]

    def __init__(self):
        super(PCO_Single_Signal_Desc, self).__init__()
        self.wSize = ctypes.sizeof(PCO_Single_Signal_Desc)


class PCO_Signal_Description(ctypes.Structure):
    _fields_ = [
        ("wSize", ctypes.wintypes.WORD),
        ("wNumOfSignals", ctypes.wintypes.WORD),
        ("strSingleSignalDesc", PCO_Single_Signal_Desc * NUM_MAX_SIGNALS),
        ("dwDummy", ctypes.wintypes.DWORD * 524),
    ]

    def __init__(self):
        super(PCO_Signal_Description, self).__init__()
        self.wSize = ctypes.sizeof(PCO_Signal_Description)
        for i in range(NUM_MAX_SIGNALS):
            self.strSingleSignalDesc[i].__init__()


PCO_SENSORDUMMY = 7


class PCO_Sensor(ctypes.Structure):
    _fields_ = [
        ("wSize", ctypes.wintypes.WORD),
        ("ZZwAlignDummy1", ctypes.wintypes.WORD),
        ("strDescription", PCO_Description),
        ("strDescription2", PCO_Description2),
        ("ZZdwDummy2", ctypes.wintypes.DWORD * 256),
        ("wSensorFormat", ctypes.wintypes.WORD),
        ("wRoiX0", ctypes.wintypes.WORD),
        ("wRoiY0", ctypes.wintypes.WORD),
        ("wRoiX1", ctypes.wintypes.WORD),
        ("wRoiY1", ctypes.wintypes.WORD),
        ("wBinHorz", ctypes.wintypes.WORD),
        ("wBinVert", ctypes.wintypes.WORD),
        ("ZZwAlignDummy2", ctypes.wintypes.WORD),
        ("dwPixelRate", ctypes.wintypes.DWORD),
        ("wConvFact", ctypes.wintypes.WORD),
        ("wDoubleImage", ctypes.wintypes.WORD),
        ("wADCOperation", ctypes.wintypes.WORD),
        ("wIR", ctypes.wintypes.WORD),
        ("sCoolSet", ctypes.wintypes.SHORT),
        ("wOffsetRegulation", ctypes.wintypes.WORD),
        ("wNoiseFilterMode", ctypes.wintypes.WORD),
        ("wFastReadoutMode", ctypes.wintypes.WORD),
        ("wDSNUAdjustMode", ctypes.wintypes.WORD),
        ("wCDIMode", ctypes.wintypes.WORD),
        ("ZZwDummy", ctypes.wintypes.WORD * 36),
        ("strSignalDesc", PCO_Signal_Description),
        ("ZZdwDummy", ctypes.wintypes.DWORD * PCO_SENSORDUMMY),
    ]

    def __init__(self):
        super(PCO_Sensor, self).__init__()
        self.wSize = ctypes.sizeof(PCO_Sensor)
        self.strDescription.__init__()
        self.strDescription2.__init__()
        self.strSignalDesc.__init__()

    def __str__(self):
        return (
            str(self.strDescription)
            + """
SensorFormat: {:}
ROI: ({:}, {:}) x ({:}, {:})
PixelRate: {:} Hz""".format(
                self.wSensorFormat,
                self.wRoiX0,
                self.wRoiY0,
                self.wRoiX1,
                self.wRoiY1,
                self.dwPixelRate,
            )
        )


class PCO_Segment(ctypes.Structure):
    _fields_ = [
        ("wSize", ctypes.wintypes.WORD),
        ("wXRes", ctypes.wintypes.WORD),
        ("wYRes", ctypes.wintypes.WORD),
        ("wBinHorz", ctypes.wintypes.WORD),
        ("wBinVert", ctypes.wintypes.WORD),
        ("wRoiX0", ctypes.wintypes.WORD),
        ("wRoiY0", ctypes.wintypes.WORD),
        ("wRoiX1", ctypes.wintypes.WORD),
        ("wRoiY1", ctypes.wintypes.WORD),
        ("ZZwAlignDummy1", ctypes.wintypes.WORD),
        ("dwValidImageCnt", ctypes.wintypes.DWORD),
        ("dwMaxImageCnt", ctypes.wintypes.DWORD),
        ("wRoiSoftX0", ctypes.wintypes.WORD),
        ("wRoiSoftY0", ctypes.wintypes.WORD),
        ("wRoiSoftX1", ctypes.wintypes.WORD),
        ("wRoiSoftY1", ctypes.wintypes.WORD),
        ("wRoiSoftXRes", ctypes.wintypes.WORD),
        ("wRoiSoftYRes", ctypes.wintypes.WORD),
        ("wRoiSoftDouble", ctypes.wintypes.WORD),
        ("ZZwDummy", ctypes.wintypes.WORD * 33),
    ]

    def __init__(self):
        super(PCO_Segment, self).__init__()
        self.wSize = ctypes.sizeof(PCO_Segment)


class PCO_Image_ColorSet(ctypes.Structure):
    _fields_ = [
        ("wSize", ctypes.wintypes.WORD),
        ("sSaturation", ctypes.wintypes.SHORT),
        ("sVibrance", ctypes.wintypes.SHORT),
        ("wColorTemp", ctypes.wintypes.WORD),
        ("sTint", ctypes.wintypes.SHORT),
        ("wMulNormR", ctypes.wintypes.WORD),
        ("wMulNormG", ctypes.wintypes.WORD),
        ("wMulNormB", ctypes.wintypes.WORD),
        ("sContrast", ctypes.wintypes.SHORT),
        ("wGamma", ctypes.wintypes.WORD),
        ("wSharpFixed", ctypes.wintypes.WORD),
        ("wSharpAdaptive", ctypes.wintypes.WORD),
        ("wScaleMin", ctypes.wintypes.WORD),
        ("wScaleMax", ctypes.wintypes.WORD),
        ("wProcOptions", ctypes.wintypes.WORD),
        ("wLutSelection", ctypes.wintypes.WORD),
        ("ZZwDummy", ctypes.wintypes.WORD * 92),
    ]

    def __init__(self):
        super(PCO_Image_ColorSet, self).__init__()
        self.wSize = ctypes.sizeof(PCO_Image_ColorSet)
        self.wMulNormR = 0x8000
        self.wMulNormG = 0x8000
        self.wMulNormB = 0x8000


class PCO_Image(ctypes.Structure):
    _fields_ = [
        ("wSize", ctypes.wintypes.WORD),
        ("ZZwAlignDummy1", ctypes.wintypes.WORD),
        ("strSegment", PCO_Segment * 4),
        ("ZZstrDummySeg", PCO_Segment * 14),
        ("strColorSet", PCO_Image_ColorSet),
        ("wBitAlignment", ctypes.wintypes.WORD),
        ("wHotPixelCorrectionMode", ctypes.wintypes.WORD),
    ]

    def __init__(self):
        super(PCO_Image, self).__init__()
        self.wSize = ctypes.sizeof(PCO_Image)
        for i in range(4):
            self.strSegment[i].__init__()
        for i in range(14):
            self.ZZstrDummySeg[i].__init__()
        self.strColorSet.__init__()


def bcd_byte_to_str(input):
    if isinstance(input, Iterable) and len(input) > 1:
        raise ValueError("Exactly one byte is expected")
    input_a = (int(input) & 0xF0) >> 4
    input_b = int(input) & 0x0F
    return "{:d}{:d}".format(input_a, input_b)


def bcd_to_int(input, endianess="little"):
    """
    Decimal-encoded value

    Decimal digit | Bits
    --------------+------
        0         | 0000
        1         | 0001
        2         | 0010
        3         | 0011
        4         | 0100
        5         | 0101
        6         | 0110
        7         | 0111
        8         | 1000
        9         | 1001
    """
    if isinstance(input, Iterable):
        if endianess == "little":
            return int("".join([bcd_byte_to_str(b) for b in reversed(input)]))
        else:
            return int("".join([bcd_byte_to_str(b) for b in input]))
    else:
        return int(bcd_byte_to_str(input))


class PCO_METADATA(ctypes.Structure):
    _fields_ = [
        ("wSize", ctypes.wintypes.WORD),
        ("wVersion", ctypes.wintypes.WORD),
        ("bIMAGE_COUNTER_BCD", ctypes.wintypes.BYTE * 4),
        ("bIMAGE_TIME_US_BCD", ctypes.wintypes.BYTE * 3),
        ("bIMAGE_TIME_SEC_BCD", ctypes.wintypes.BYTE),
        ("bIMAGE_TIME_MIN_BCD", ctypes.wintypes.BYTE),
        ("bIMAGE_TIME_HOUR_BCD", ctypes.wintypes.BYTE),
        ("bIMAGE_TIME_DAY_BCD", ctypes.wintypes.BYTE),
        ("bIMAGE_TIME_MON_BCD", ctypes.wintypes.BYTE),
        ("bIMAGE_TIME_YEAR_BCD", ctypes.wintypes.BYTE),
        ("bIMAGE_TIME_STATUS", ctypes.wintypes.BYTE),
        ("wEXPOSURE_TIME_BASE", ctypes.wintypes.WORD),
        ("dwEXPOSURE_TIME", ctypes.wintypes.DWORD),
        ("dwFRAMERATE_MILLIHZ", ctypes.wintypes.DWORD),
        ("sSENSOR_TEMPERATURE", ctypes.wintypes.SHORT),
        ("wIMAGE_SIZE_X", ctypes.wintypes.WORD),
        ("wIMAGE_SIZE_Y", ctypes.wintypes.WORD),
        ("bBINNING_X", ctypes.wintypes.BYTE),
        ("bBINNING_Y", ctypes.wintypes.BYTE),
        ("dwSENSOR_READOUT_FREQUENCY", ctypes.wintypes.DWORD),
        ("wSENSOR_CONV_FACTOR", ctypes.wintypes.WORD),
        ("dwCAMERA_SERIAL_NO", ctypes.wintypes.DWORD),
        ("wCAMERA_TYPE", ctypes.wintypes.WORD),
        ("bBIT_RESOLUTION", ctypes.wintypes.BYTE),
        ("bSYNC_STATUS", ctypes.wintypes.BYTE),
        ("wDARK_OFFSET", ctypes.wintypes.WORD),
        ("bTRIGGER_MODE", ctypes.wintypes.BYTE),
        ("bDOUBLE_IMAGE_MODE", ctypes.wintypes.BYTE),
        ("bCAMERA_SYNC_MODE", ctypes.wintypes.BYTE),
        ("bIMAGE_TYPE", ctypes.wintypes.BYTE),
        ("wCOLOR_PATTERN", ctypes.wintypes.WORD),
    ]

    def __init__(self):
        super(PCO_METADATA, self).__init__()
        self.wSize = ctypes.sizeof(PCO_METADATA)

    @property
    def raw_value(self):
        return {key[1:]: getattr(self, key).value for key in self._fields_}

    @property
    def value(self):
        data = self.raw_value
        IMAGE_COUNTER_BCD = data.pop("IMAGE_COUNTER_BCD")
        IMAGE_TIME_US_BCD = data.pop("IMAGE_TIME_BCD")
        IMAGE_TIME_SEC_BCD = data.pop("IMAGE_TIME_SEC_BCD")
        IMAGE_TIME_MIN_BCD = data.pop("IMAGE_TIME_MIN_BCD")
        IMAGE_TIME_HOUR_BCD = data.pop("IMAGE_TIME_HOUR_BCD")
        IMAGE_TIME_DAY_BCD = data.pop("IMAGE_TIME_DAY_BCD")
        IMAGE_TIME_MON_BCD = data.pop("IMAGE_TIME_MON_BCD")
        IMAGE_TIME_YEAR_BCD = data.pop("IMAGE_TIME_YEAR_BCD")

        # IMAGE_COUNTER
        # 0x00000001 to 0x99999999 where first byte is a
        # least significant byte (Little Endian)
        data["IMAGE_COUNTER"] = bcd_to_int(IMAGE_COUNTER_BCD)

        # IMAGE_DATETIME
        data["IMAGE_DATETIME"] = datetime.datetime(
            bcd_to_int(IMAGE_TIME_YEAR_BCD) + 2000,
            bcd_to_int(IMAGE_TIME_MON_BCD),
            bcd_to_int(IMAGE_TIME_DAY_BCD),
            bcd_to_int(IMAGE_TIME_HOUR_BCD),
            bcd_to_int(IMAGE_TIME_MIN_BCD),
            bcd_to_int(IMAGE_TIME_SEC_BCD),
            bcd_to_int(IMAGE_TIME_US_BCD),
        )

        return data


class PCO_Openstruct(ctypes.Structure):
    _fields_ = [
        ("wSize", ctypes.wintypes.WORD),
        ("wInterfaceType", ctypes.wintypes.WORD),
        ("wCameraNumber", ctypes.wintypes.WORD),
        ("wCameraNumAtInterface", ctypes.wintypes.WORD),
        ("wOpenFlags", ctypes.wintypes.WORD * 10),
        ("dwOpenFlags", ctypes.wintypes.DWORD * 5),
        ("wOpenPtr", ctypes.c_void_p * 6),
        ("zzwDummy", ctypes.wintypes.WORD * 8),
    ]

    def __init__(self, interface_type=0xFFFF, camera_number=0):
        self.wSize = ctypes.sizeof(PCO_Openstruct)
        inters = {
            "FireWire": 1,
            "Camera Link Matrox": 2,
            "Camera Link Silicon Software mE III": 3,
            "Camera Link National Instruments": 4,
            "GigE": 5,
            "USB 2.0": 6,
            "Camera Link Silicon Software mE IV": 7,
            "USB 3.0": 8,
            "Reserved for WLAN": 9,
            "Camera Link serial port only": 10,
            "Camera Link HS": 11,
            "all": 0xFFFF,
        }
        if interface_type in inters:
            interface_type = inters[interface_type]
        else:
            interface_type = int(interface_type)
        self.wInterfaceType = interface_type
        self.wCameraNumber = camera_number
        self.wCameraNumAtInterface = 0
        for i in range(10):
            self.wOpenFlags[i] = 0
        for i in range(5):
            self.dwOpenFlags[i] = 0
        for i in range(6):
            self.wOpenPtr[i] = 0


# Pixelfly API functions
def PCO_OpenCamera():
    """
    Open a camera device and attach it to a handle, which will be returned by the parameter ph. This
    function scans for the next available camera. If you want to access a distinct camera please use
    PCO_OpenCameraEx.
    Due to historical reasons the wCamNum parameter is a don’t care.
    """

    f = pixelfly_dll.PCO_OpenCamera
    f.argtypes = (ctypes.POINTER(ctypes.wintypes.HANDLE), ctypes.wintypes.WORD)
    f.restype = ctypes.c_int
    h = ctypes.wintypes.HANDLE(0)
    ret_code = f(ctypes.byref(h), 0)  # the argument is ignored.
    PCO_manage_error(ret_code)  # PCO_OpenCamera must be called multiple times
    return h


def PCO_OpenCameraEx(interface_type, camera_number):
    """
    Open a distinct camera, e.g. a camera which is connected to a specific interface port.
    Possible interfaces:
      'FireWire': 1,
      'Camera Link Matrox': 2,
      'Camera Link Silicon Software mE III': 3,
      'Camera Link National Instruments': 4,
      'GigE': 5,
      'USB 2.0': 6,
      'Camera Link Silicon Software mE IV': 7,
      'USB 3.0': 8,
      'Reserved for WLAN': 9,
      'Camera Link serial port only': 10,
      'Camera Link HS': 11,
      'all': 0xFFFF
    """

    f = pixelfly_dll.PCO_OpenCameraEx
    f.argtypes = (
        ctypes.POINTER(ctypes.wintypes.HANDLE),
        ctypes.POINTER(PCO_Openstruct),
    )
    f.restype = ctypes.c_int
    h = ctypes.wintypes.HANDLE(0)
    strOpenStruct = PCO_Openstruct(interface_type, camera_number)
    ret_code = f(ctypes.byref(h), ctypes.byref(strOpenStruct))
    PCO_manage_error(ret_code)
    return h


def PCO_CloseCamera(handle):
    """
    Close a camera device
    """

    f = pixelfly_dll.PCO_CloseCamera
    f.argtypes = (ctypes.wintypes.HANDLE,)
    f.restype = ctypes.c_int
    ret_code = f(handle)
    PCO_manage_error(ret_code)


def PCO_GetInfoString(handle):
    """
    This call can be used to read some information about the camera, e.g. firmware versions
    """

    f = pixelfly_dll.PCO_GetInfoString
    f.argtypes = (
        ctypes.wintypes.HANDLE,
        ctypes.wintypes.DWORD,
        ctypes.c_char_p,
        ctypes.wintypes.WORD,
    )
    f.restype = ctypes.c_int
    p = ctypes.create_string_buffer(256)
    ret_code = f(handle, 0, p, 256)
    PCO_manage_error(ret_code)
    return p.raw.decode("ascii")


def PCO_GetROI(handle: int) -> Tuple[int, int, int, int]:
    """
    This function returns the current ROI
    (region of interest) setting in pixels.
    (X0,Y0) is the upper left corner and
    (X1,Y1) the lower right one.
    """
    f = pixelfly_dll.PCO_GetROI
    f.argtypes = (
        ctypes.wintypes.HANDLE,
        ctypes.POINTER(ctypes.wintypes.WORD),
        ctypes.POINTER(ctypes.wintypes.WORD),
        ctypes.POINTER(ctypes.wintypes.WORD),
        ctypes.POINTER(ctypes.wintypes.WORD),
    )
    f.restype = ctypes.c_int
    RoiX0 = ctypes.wintypes.WORD()
    RoiY0 = ctypes.wintypes.WORD()
    RoiX1 = ctypes.wintypes.WORD()
    RoiY1 = ctypes.wintypes.WORD()
    ret_code = f(
        handle,
        ctypes.byref(RoiX0),
        ctypes.byref(RoiY0),
        ctypes.byref(RoiX1),
        ctypes.byref(RoiY1),
    )
    PCO_manage_error(ret_code)
    return RoiX0.value, RoiY0.value, RoiX1.value, RoiY1.value


def PCO_SetROI(
    handle: int,
    RoiX0: ctypes.wintypes.WORD,
    RoiY0: ctypes.wintypes.WORD,
    RoiX1: ctypes.wintypes.WORD,
    RoiY1: ctypes.wintypes.WORD,
):
    """
    This function does set a ROI
    (region of interest) area on the sensor of the camera.
    """
    f = pixelfly_dll.PCO_SetROI
    f.argtypes = (
        ctypes.wintypes.HANDLE,
        ctypes.wintypes.WORD,
        ctypes.wintypes.WORD,
        ctypes.wintypes.WORD,
        ctypes.wintypes.WORD,
    )
    f.restype = ctypes.c_int
    ret_code = f(handle, RoiX0, RoiY0, RoiX1, RoiY1)
    PCO_manage_error(ret_code)


def PCO_GetFrameRate(handle):
    """
    This function returns the current frame rate and exposure
    time settings of the camera.Returned values are only
    valid if last timing command was PCO_SetFrameRate.
    """
    f = pixelfly_dll.PCO_GetFrameRate
    f.argtypes = (
        ctypes.wintypes.HANDLE,
        ctypes.POINTER(ctypes.wintypes.WORD),
        ctypes.POINTER(ctypes.wintypes.DWORD),
        ctypes.POINTER(ctypes.wintypes.DWORD),
    )
    f.restype = ctypes.c_int
    FrameRateStatus = ctypes.wintypes.WORD()
    FrameRate = ctypes.wintypes.DWORD()
    FrameRateExposure = ctypes.wintypes.DWORD()
    ret_code = f(
        handle,
        ctypes.byref(FrameRateStatus),
        ctypes.byref(FrameRate),
        ctypes.byref(FrameRateExposure),
    )
    PCO_manage_error(ret_code)
    return FrameRateStatus.value, FrameRate.value, FrameRateExposure.value


def PCO_SetFrameRate(
    handle: int,
    FrameRateMode: ctypes.wintypes.WORD,
    FrameRate: ctypes.wintypes.DWORD,
    FrameRateExposure: ctypes.wintypes.DWORD,
):
    """
    Sets Frame rate (mHz) and exposure time (ns)
    Frame rate status gives the limiting factors
    if the condition are not met.
    """
    f = pixelfly_dll.PCO_SetFrameRate
    f.argtypes = (
        ctypes.wintypes.HANDLE,
        ctypes.POINTER(ctypes.wintypes.WORD),
        ctypes.wintypes.WORD,
        ctypes.POINTER(ctypes.wintypes.DWORD),
        ctypes.POINTER(ctypes.wintypes.DWORD),
    )
    f.restype = ctypes.c_int
    FrameRateStatus = ctypes.wintypes.WORD()
    dwFrameRate = ctypes.wintypes.DWORD(FrameRate)
    dwFrameRateExposure = ctypes.wintypes.DWORD(FrameRateExposure)
    ret_code = f(
        handle,
        ctypes.byref(FrameRateStatus),
        FrameRateMode,
        ctypes.byref(dwFrameRate),
        ctypes.byref(dwFrameRateExposure),
    )
    PCO_manage_error(ret_code)
    return FrameRateStatus.value, FrameRate.value, FrameRateExposure.value


def PCO_GetCameraName(handle):
    """
    This function retrieves the name of the camera.
    """

    f = pixelfly_dll.PCO_GetCameraName
    f.argtypes = (ctypes.wintypes.HANDLE, ctypes.c_char_p, ctypes.wintypes.WORD)
    f.restype = ctypes.c_int
    cameraName = ctypes.create_string_buffer(41)
    ret_code = f(handle, cameraName, 41)
    PCO_manage_error(ret_code)
    return cameraName.raw.decode("ascii")


def PCO_GetGeneral(handle):
    """
    Request all info contained in the following
    descriptions, especially:
        - camera type, hardware/firmware version,
          serial number, etc.
        - Request the current camera and power supply
          temperatures
    """

    f = pixelfly_dll.PCO_GetGeneral
    f.argtypes = (ctypes.wintypes.HANDLE, ctypes.POINTER(PCO_General))
    f.restype = ctypes.c_int
    strGeneral = PCO_General()
    ret_code = f(handle, ctypes.byref(strGeneral))
    PCO_manage_error(ret_code)
    return strGeneral


def PCO_GetSensorStruct(handle):
    """
    Get the complete set of the sensor functions settings
    """

    f = pixelfly_dll.PCO_GetSensorStruct
    f.argtypes = (ctypes.wintypes.HANDLE, ctypes.POINTER(PCO_Sensor))
    f.restype = ctypes.c_int
    strSensor = PCO_Sensor()
    ret_code = f(handle, ctypes.byref(strSensor))
    PCO_manage_error(ret_code)
    return strSensor


def PCO_GetCameraDescription(handle):
    """
    Sensor and camera specific description is queried. In the returned
    PCO_Description structure margins for all sensor related settings
    and bitfields for available options of the camera are given.
    """

    f = pixelfly_dll.PCO_GetCameraDescription
    f.argtypes = (ctypes.wintypes.HANDLE, ctypes.POINTER(PCO_Description))
    f.restype = ctypes.c_int
    desc = PCO_Description()
    ret_code = f(handle, ctypes.byref(desc))
    PCO_manage_error(ret_code)
    return desc


def PCO_GetCameraHealthStatus(handle):
    """
    This function retrives information about the current camera status.
    """

    # Call PCO_GetCameraHealthStatus function
    f = pixelfly_dll.PCO_GetCameraHealthStatus
    f.argtypes = (
        ctypes.wintypes.HANDLE,
        ctypes.POINTER(ctypes.wintypes.DWORD),
        ctypes.POINTER(ctypes.wintypes.DWORD),
        ctypes.POINTER(ctypes.wintypes.DWORD),
    )
    f.restype = ctypes.c_int
    dwWarn = ctypes.wintypes.DWORD()
    dwErr = ctypes.wintypes.DWORD()
    dwStatus = ctypes.wintypes.DWORD()
    ret_code = f(
        handle, ctypes.byref(dwWarn), ctypes.byref(dwErr), ctypes.byref(dwStatus)
    )
    PCO_manage_error(ret_code)

    return dwWarn.value, dwErr.value, dwStatus.value


def PCO_GetRecordingStruct(handle):
    """
    Get the complete set of the recording function
    settings. Please fill in all wSize parameters,
    even in embedded structures.
    """

    strRecording = PCO_Recording()
    f = pixelfly_dll.PCO_GetRecordingStruct
    f.argtypes = (ctypes.wintypes.HANDLE, ctypes.POINTER(PCO_Recording))
    f.restype = ctypes.c_int
    ret_code = f(handle, ctypes.byref(strRecording))
    PCO_manage_error(ret_code)
    return strRecording


def PCO_GetSizes(handle: int) -> Tuple[int, int, int, int]:
    """
    This function returns the current armed image size of the camera.
    """

    f = pixelfly_dll.PCO_GetSizes
    f.argtypes = (
        ctypes.wintypes.HANDLE,
        ctypes.POINTER(ctypes.wintypes.WORD),
        ctypes.POINTER(ctypes.wintypes.WORD),
        ctypes.POINTER(ctypes.wintypes.WORD),
        ctypes.POINTER(ctypes.wintypes.WORD),
    )
    f.restype = ctypes.c_int
    XResAct = ctypes.wintypes.WORD()
    YResAct = ctypes.wintypes.WORD()
    XResMax = ctypes.wintypes.WORD()
    YResMax = ctypes.wintypes.WORD()
    ret_code = f(
        handle,
        ctypes.byref(XResAct),
        ctypes.byref(YResAct),
        ctypes.byref(XResMax),
        ctypes.byref(YResMax),
    )
    PCO_manage_error(ret_code)
    return XResAct.value, YResAct.value, XResMax.value, YResMax.value


def PCO_AllocateBuffer(
    handle: int,
    bufNr: int,
    size: int,
    bufPtr: ctypes.POINTER(ctypes.wintypes.WORD),
    hEvent: ctypes.wintypes.HANDLE = 0,
) -> Tuple[int, ctypes.POINTER(ctypes.wintypes.WORD), int]:
    """
    This function sets up a buffer context to receive the transferred
    images. A buffer index is returned, which must be used for the
    image transfer functions. There is a maximum of 16 buffers per camera.

    Attention: This function cannot be used, if the connection to the
    camera is established through the serial connection of a Camera
    Link grabber. In this case, the SDK of the grabber must be used
    to do any buffer management.
    (est-ce le cas avec le grabber Solios ?)
    """

    f = pixelfly_dll.PCO_AllocateBuffer
    f.argtypes = (
        ctypes.wintypes.HANDLE,  # handle
        ctypes.POINTER(ctypes.wintypes.SHORT),  # sBufNr
        ctypes.wintypes.DWORD,  # dwSize
        ctypes.POINTER(ctypes.POINTER(ctypes.wintypes.WORD)),
        ctypes.POINTER(ctypes.wintypes.HANDLE),
    )
    f.restype = ctypes.c_int
    sBufNr = ctypes.wintypes.SHORT(bufNr)
    hEvent = ctypes.wintypes.HANDLE(hEvent)
    ret_code = f(
        handle, ctypes.byref(sBufNr), size, ctypes.byref(bufPtr), ctypes.byref(hEvent)
    )
    PCO_manage_error(ret_code)
    return sBufNr.value, hEvent.value


def PCO_FreeBuffer(handle, bufNr):
    """
    This function frees a previously allocated buffer context with
    a given index. If internal memory was allocated for this buffer
    context, it will be freed. If an internal event handle was
    created, it will be closed.
    """

    f = pixelfly_dll.PCO_FreeBuffer
    f.argtypes = (ctypes.wintypes.HANDLE, ctypes.wintypes.SHORT)
    f.restype = ctypes.c_int
    ret_code = f(handle, bufNr)
    PCO_manage_error(ret_code)


def PCO_GetBufferStatus(handle, sBufNr):
    """
    Queries the status of the buffer context with the given index:
        - StatusDll describes the state of the buffer context:
            0x80000000: Buffer is allocated
            0x40000000: Buffer event created inside the SDK DLL
            0x20000000: Buffer is allocated externally
            0x00008000: Buffer event is set
        - StatusDrv describes the state of the last image transfer
          into this buffer:
            PCO_NOERROR: Image transfer succeeded
            others: See error codes
    """

    f = pixelfly_dll.PCO_GetBufferStatus
    f.argtypes = (
        ctypes.wintypes.HANDLE,
        ctypes.wintypes.SHORT,
        ctypes.POINTER(ctypes.wintypes.DWORD),
        ctypes.POINTER(ctypes.wintypes.DWORD),
    )
    f.restype = ctypes.c_int
    statusDLL = ctypes.wintypes.DWORD()
    statusDrv = ctypes.wintypes.DWORD()
    ret_code = f(handle, sBufNr, ctypes.byref(statusDLL), ctypes.byref(statusDrv))
    PCO_manage_error(ret_code)
    return statusDLL.value, statusDrv.value


def PCO_ArmCamera(handle):
    """
    Arms, i.e. prepares the camera for a consecutive
    set recording status = [run] command. All
    configurations and settings made up to this moment
    are accepted and the internal settings of the
    camera is prepared. Thus the camera is able to
    start immediately when the set recording status
    = [run] command is performed.
    """

    f = pixelfly_dll.PCO_ArmCamera
    f.argtypes = (ctypes.wintypes.HANDLE,)
    f.restype = ctypes.c_int
    ret_code = f(handle)
    PCO_manage_error(ret_code)


def PCO_GetRecordingState(handle):
    """
    Returns the current Recording state of the camera:
        - 0x0000: camera is stopped, recording state [stop]
        - 0x0001: camera is running, recording state [run]
    """

    f = pixelfly_dll.PCO_GetRecordingState
    f.argtypes = (ctypes.wintypes.HANDLE, ctypes.POINTER(ctypes.wintypes.WORD))
    f.restype = ctypes.c_int
    state = ctypes.wintypes.WORD()
    ret_code = f(handle, ctypes.byref(state))
    PCO_manage_error(ret_code)
    return state.value


def PCO_SetRecordingState(handle, state):
    """
    Sets the current recording status and waits till
    the status is valid. If the state can't be set the
    function will return an error.

    Notes:
     - it is necessary to arm camera before every
     set recording status command in order to ensure
     that all settings are accepted correctly.
     - During the recording session, it is possible
     to change the timing by calling
     PCO_SetDelayExposureTime.
    """

    if state not in (0x0000, 0x0001):
        raise ValueError("Wrong state value")
    f = pixelfly_dll.PCO_SetRecordingState
    f.argtypes = (ctypes.wintypes.HANDLE, ctypes.wintypes.WORD)
    f.restype = ctypes.c_int
    wRecState = ctypes.wintypes.WORD(1 if state else 0)
    ret_code = f(handle, wRecState)
    PCO_manage_error(ret_code)


def PCO_GetBitAlignment(handle):
    """
    This function returns the current bit alignment of the
    transferred image data. The data can be either
    MSB (Big Endian) or LSB (Little Endian) aligned.
    Returns:
        - 0x0000 [MSB]
        - 0x0001 [LSB]
    """

    f = pixelfly_dll.PCO_GetBitAlignment
    f.argtypes = (ctypes.wintypes.HANDLE, ctypes.POINTER(ctypes.wintypes.WORD))
    f.restype = ctypes.c_int
    bitAlignment = ctypes.wintypes.WORD()
    ret_code = f(handle, ctypes.byref(bitAlignment))
    PCO_manage_error(ret_code)
    return bitAlignment.value


def PCO_SetBitAlignment(handle, littleEndian):
    """
    This functions sets the bit alignment of the transferred
    image data.
    littleEndian can be 0 or 1.
    """

    f = pixelfly_dll.PCO_SetBitAlignment
    f.argtypes = (ctypes.wintypes.HANDLE, ctypes.wintypes.WORD)
    f.restype = ctypes.c_int
    ret_code = f(handle, littleEndian)
    PCO_manage_error(ret_code)


def PCO_GetImageStruct(handle):
    """
    Information about previously recorded images is queried from
    the camera and the variables of the PCO_Image structure are
    filled with this information.
    """

    f = pixelfly_dll.PCO_GetImageStruct
    f.argtypes = (ctypes.wintypes.HANDLE, ctypes.POINTER(PCO_Image))
    f.restype = ctypes.c_int
    strImage = PCO_Image()
    ret_code = f(handle, ctypes.byref(strImage))
    PCO_manage_error(ret_code)
    return strImage


def PCO_GetMetaData(handle, bufNr):
    """
    Cameras: pco.dimax and pco.edge

    Query additionnal image information, which the camera has attached to
    the transferred image, if Meta Data mode is enabled.
    """

    f = pixelfly_dll.PCO_GetMetaData
    f.argtypes = (
        ctypes.wintypes.HANDLE,
        ctypes.wintypes.SHORT,
        ctypes.POINTER(PCO_METADATA),
        ctypes.wintypes.DWORD,
        ctypes.wintypes.DWORD,
    )
    f.restype = ctypes.c_int
    MetaData = PCO_METADATA()
    ret_code = f(handle, bufNr, ctypes.byref(MetaData), 0, 0)
    PCO_manage_error(ret_code)
    return MetaData.value


def PCO_SetMetaDataMode(handle, MetaDataMode):
    """
    Cameras: pco.dimax and pco.edge

    Sets the mode for Meta Data and returns information about size and version
    of the Meta Data block.
    When Meta Data mode is set to [on], a Meta Data block with additional information
    is added at the end of each image. The internal buffers allocated with PCO_AllocateBuffer
    are adapted automatically.
    """

    f = pixelfly_dll.PCO_SetMetaDataMode
    f.argtypes = (
        ctypes.wintypes.HANDLE,
        ctypes.wintypes.WORD,
        ctypes.POINTER(ctypes.wintypes.WORD),
        ctypes.POINTER(ctypes.wintypes.WORD),
    )
    f.restype = ctypes.c_int
    MetaDataSize = ctypes.wintypes.WORD()
    MetaDataVersion = ctypes.wintypes.WORD()
    ret_code = f(
        handle, MetaDataMode, ctypes.byref(MetaDataSize), ctypes.byref(MetaDataVersion)
    )
    PCO_manage_error(ret_code)
    return MetaDataSize.value, MetaDataVersion.value


def PCO_GetMetaDataMode(handle):
    """
    Returns the current Meta Data mode of the camera and information about size
    and version of the Meta Data block.
    """

    f = pixelfly_dll.PCO_GetMetaDataMode
    f.argtypes = (
        ctypes.wintypes.HANDLE,
        ctypes.POINTER(ctypes.wintypes.WORD),
        ctypes.POINTER(ctypes.wintypes.WORD),
        ctypes.POINTER(ctypes.wintypes.WORD),
    )
    f.restype = ctypes.c_int
    MetaDataMode = ctypes.wintypes.WORD()
    MetaDataSize = ctypes.wintypes.WORD()
    MetaDataVersion = ctypes.wintypes.WORD()
    ret_code = f(
        handle,
        ctypes.byref(MetaDataMode),
        ctypes.byref(MetaDataSize),
        ctypes.byref(MetaDataVersion),
    )
    PCO_manage_error(ret_code)
    return MetaDataMode.value, MetaDataSize.value, MetaDataVersion.value


def PCO_SetTimestampMode(handle, mode):
    """
    Sets the timestamp mode of the camera:
        0x0000: [off]
        0x0001: [binary]
            BCD coded timestamp in the first 14 pixels
        0x0002: [binary+ASCII]
            BCD coded timestamp in the first 14 pixels + ASCII text
        0x0003: [ASCII]
            ASCII text only (see camera descriptor for availability)
    """

    if mode not in (0x0000, 0x0001, 0x0002, 0x0003):
        raise ValueError("Bad mode value")
    f = pixelfly_dll.PCO_SetTimestampMode
    f.argtypes = (ctypes.wintypes.HANDLE, ctypes.wintypes.WORD)
    f.restype = ctypes.c_int
    ret_code = f(handle, mode)
    PCO_manage_error(ret_code)


def PCO_AddBufferEx(
    handle, dw1stImage, dwLastImage, sBufNr, wXRes, wYRes, wBitPerPixel
):
    """
    This function sets up a request for a single transfer from the camera and
    returns immediately.
    """

    f = pixelfly_dll.PCO_AddBufferEx
    f.argtypes = (
        ctypes.wintypes.HANDLE,
        ctypes.wintypes.DWORD,
        ctypes.wintypes.DWORD,
        ctypes.wintypes.SHORT,
        ctypes.wintypes.WORD,
        ctypes.wintypes.WORD,
        ctypes.wintypes.WORD,
    )
    f.restype = ctypes.c_int
    ret_code = f(handle, dw1stImage, dwLastImage, sBufNr, wXRes, wYRes, wBitPerPixel)
    PCO_manage_error(ret_code)


def PCO_CancelImages(handle):
    """
    This function does remove all remaining buffers from the internal
    queue, reset the internal queue and also reset the transfer state
    machine in the camera. It is mandatory to call PCO_CancelImages
    after all image transfers are done. This function can be called
    before or after setting PCO_SetRecordingState to [stop].
    """

    f = pixelfly_dll.PCO_CancelImages
    f.argtypes = (ctypes.wintypes.HANDLE,)
    f.restype = ctypes.c_int
    ret_code = f(handle)
    PCO_manage_error(ret_code)


IMAGEPARAMETERS_READ_WHILE_RECORDING = 0x00000001
IMAGEPARAMETERS_READ_FROM_SEGMENTS = 0x00000002


def PCO_SetImageParameters(handle, XRes, YRes, flags):
    """
    This function sets the image parameters for internal allocated resources.
    This function must be called before an image transfer is started.
    If next image will be transfered from a recording camera, flag
    IMAGEPARAMETERS_READ_WHILE_RECORDING must be set. If next action is to
    readout images from the camera internal memory, flag
    IMAGEPARAMETERS_READ_FROM_SEGMENTS must be set.
    """

    if flags not in (
        IMAGEPARAMETERS_READ_WHILE_RECORDING,
        IMAGEPARAMETERS_READ_FROM_SEGMENTS,
    ):
        raise ValueError("Wrong flag value")

    f = pixelfly_dll.PCO_SetImageParameters
    f.argtypes = (
        ctypes.wintypes.HANDLE,
        ctypes.wintypes.WORD,
        ctypes.wintypes.WORD,
        ctypes.wintypes.DWORD,
        ctypes.c_void_p,
        ctypes.c_int,
    )
    f.restype = ctypes.c_int
    ret_code = f(handle, XRes, YRes, flags, ctypes.c_void_p(), 0)
    PCO_manage_error(ret_code)


def PCO_GetImageEx(
    handle, segment, firstImage, lastImage, bufNr, xRes, yRes, bitsPerPixel
):
    """
    This function can be used to get a single image from the camera.
    The function does not return until the image is transferred to the
    buffer or an error occured. The timeout value for the transfer
    can be set with function PCO_SetTimeouts, the default value is
    6 seconds. On return the image stored in the memory area of the
    buffer, which is addressed through parameter sBufNr.
    """

    f = pixelfly_dll.PCO_GetImageEx
    f.argtypes = (
        ctypes.wintypes.HANDLE,  # handle
        ctypes.wintypes.WORD,  # wSegment
        ctypes.wintypes.DWORD,  # dw1stImage
        ctypes.wintypes.DWORD,  # dwLastImage
        ctypes.wintypes.SHORT,  # sBufNr
        ctypes.wintypes.WORD,  # wXRes
        ctypes.wintypes.WORD,  # wYRes
        ctypes.wintypes.WORD,  # wBitPerPixel
    )
    f.restype = ctypes.c_int
    ret_code = f(
        handle, segment, firstImage, lastImage, bufNr, xRes, yRes, bitsPerPixel
    )
    PCO_manage_error(ret_code)


PCO_Timebases = {0x0000: 1e-9, 0x0001: 1e-6, 0x0002: 1e-3}


def PCO_SetDelayExposureTime(
    handle, dwDelay, dwExposure, wTimeBaseDelay, wTimeBaseExposure
):
    """
    This function sets the delay and exposure time and the
    associated time base values.
    Restrictions for the parameter values are defined in the
    PCO_Description structure:
        dwMinDelayDESC
        dwMaxDelayDESC
        dwMinDelayStepDESC
        dwMinExposDESC
        dwMaxExposDESC
        dwMinExposStepDESC

    Possible values for wTimeBaseDelay and wTimeBaseExposure:
        0x0000: ns
        0x0001: µs
        0x0002: ms
    """

    f = pixelfly_dll.PCO_SetDelayExposureTime
    f.argtypes = (
        ctypes.wintypes.HANDLE,
        ctypes.wintypes.DWORD,
        ctypes.wintypes.DWORD,
        ctypes.wintypes.WORD,
        ctypes.wintypes.WORD,
    )
    f.restype = ctypes.c_int
    ret_code = f(handle, dwDelay, dwExposure, wTimeBaseDelay, wTimeBaseExposure)
    PCO_manage_error(ret_code)


def PCO_GetDelayExposureTime(handle):
    """
    Returns the current setting of delay and exposure time
    """

    f = pixelfly_dll.PCO_GetDelayExposureTime
    f.argtypes = (
        ctypes.wintypes.HANDLE,
        ctypes.POINTER(ctypes.wintypes.DWORD),
        ctypes.POINTER(ctypes.wintypes.DWORD),
        ctypes.POINTER(ctypes.wintypes.WORD),
        ctypes.POINTER(ctypes.wintypes.WORD),
    )
    f.restype = ctypes.c_int
    delay = ctypes.wintypes.DWORD()
    exposure = ctypes.wintypes.DWORD()
    timebase_delay = ctypes.wintypes.WORD()
    timebase_exposure = ctypes.wintypes.WORD()
    ret_code = f(
        handle,
        ctypes.byref(delay),
        ctypes.byref(exposure),
        ctypes.byref(timebase_delay),
        ctypes.byref(timebase_exposure),
    )
    PCO_manage_error(ret_code)
    return delay.value, exposure.value, timebase_delay.value, timebase_exposure.value


def PCO_GetTriggerMode(handle):
    """
    Returns the current trigger mode setting of the
    camera
    """

    f = pixelfly_dll.PCO_GetTriggerMode
    f.argtypes = (ctypes.wintypes.HANDLE, ctypes.POINTER(ctypes.wintypes.WORD))
    f.restype = ctypes.c_int
    triggerMode = ctypes.wintypes.WORD()
    ret_code = f(handle, ctypes.byref(triggerMode))
    PCO_manage_error(ret_code)
    return triggerMode.value


PCO_TriggerModeDescription = {
    0x0000: "auto sequence",
    0x0001: "software trigger",
    0x0002: "external exposure start & software trigger",
    0x0003: "external exposure control",
    0x0004: "external synchronized",
    0x0005: "fast external exposure control",
    0x0006: "external CDS control",
    0x0007: "slow external exposure control",
    0x0102: "external synchronized HDSDI",
}


def PCO_SetTriggerMode(handle, mode):
    """
    Sets the trigger mode of the camera.
    """

    f = pixelfly_dll.PCO_SetTriggerMode
    f.argtypes = (ctypes.wintypes.HANDLE, ctypes.wintypes.WORD)
    f.restype = ctypes.c_int
    ret_code = f(handle, mode)
    PCO_manage_error(ret_code)


def PCO_SetADCOperation(handle, operation):
    """
    Sets the ADC (analog-digital-converter) operating mode.
    If sensor data is read out using single ADC operation,
    linearity of image data is enhanced. Using dual ADC,
    operation readout is faster and allows higher frame rates.
    If dual ADC operating mode is set, horizontal ROI must be
    adapted to symmetrical values.

    Possible values:
        0x0001: [single ADC]
        0x0002: [dual ADC]
    """

    f = pixelfly_dll.PCO_SetADCOperation
    f.argtypes = (ctypes.wintypes.HANDLE, ctypes.wintypes.WORD)
    f.restype = ctypes.c_int
    ret_code = f(handle, operation)
    PCO_manage_error(ret_code)


def PCO_GetADCOperation(handle):
    """
    Returns the ADC operation mode (single / dual)
    """

    f = pixelfly_dll.PCO_GetADCOperation
    f.argtypes = (ctypes.wintypes.HANDLE, ctypes.POINTER(ctypes.wintypes.WORD))
    f.restype = ctypes.c_int
    operation = ctypes.wintypes.WORD()
    ret_code = f(handle, ctypes.byref(operation))
    PCO_manage_error(ret_code)
    return operation.value


def PCO_SetPixelRate(handle, rate):
    """
    This functions sets the pixel rate for the sensor readout.
    """

    f = pixelfly_dll.PCO_SetPixelRate
    f.argtypes = (ctypes.wintypes.HANDLE, ctypes.wintypes.DWORD)
    f.restype = ctypes.c_int
    ret_code = f(handle, rate)
    PCO_manage_error(ret_code)


def PCO_GetPixelRate(handle):
    """
    Returns the current pixel rate of the camera in Hz.
    The pixel rate determines the sensor readout speed.
    """

    f = pixelfly_dll.PCO_GetPixelRate
    f.argtypes = (ctypes.wintypes.HANDLE, ctypes.POINTER(ctypes.wintypes.DWORD))
    f.restype = ctypes.c_int
    rate = ctypes.wintypes.DWORD()
    ret_code = f(handle, ctypes.byref(rate))
    PCO_manage_error(ret_code)
    return rate.value


if __name__ == "__main__":
    try:
        h = PCO_OpenCamera()
        print("h =", h)
        info = PCO_GetInfoString(h)
        print("info =", info)
        general = PCO_GetGeneral(h)
        print("general =", general)
        sensor = PCO_GetSensorStruct(h)
        print("sensor =", sensor)
    except PCO_Error as pe:
        print('Error: "', pe.args[0], '"')
    finally:
        PCO_CloseCamera(h)
        print("Camera closed")
