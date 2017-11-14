"""

PCO PixelFly Wrapper

"""

import ctypes
from enum import IntEnum

pixelfly_dllpath = r"C:\Program Files\Digital Camera Toolbox\Camware4\SC2_Cam.dll"
pixelfly_dll = ctypes.windll.LoadLibrary(pixelfly_dllpath)

class PCO_ErrorLayer(IntEnum):
	PCO_ERROR_FIRMWARE    = 0x00001000 # error inside the firmware
	PCO_ERROR_DRIVER      = 0x00002000 # error inside the driver
	PCO_ERROR_SDKDLL      = 0x00003000 # error inside the SDK-dll
	PCO_ERROR_APPLICATION = 0x00004000 # error inside the application

class PCO_ErrorWarningSource(IntEnum):
	SC2_ERROR_PCOCAM_POWER_CPLD = 0x00010000  # error at CPLD in pco.power unit
	SC2_ERROR_PCOCAM_HEAD_UP = 0x00020000     # error at uP of head board in pco.camera
	SC2_ERROR_PCOCAM_MAIN_UP = 0x00030000     # error at uP of main board in pco.camera 
	SC2_ERROR_PCOCAM_FWIRE_UP = 0x00040000    # error at uP of firewire board in pco.camera 
	SC2_ERROR_PCOCAM_MAIN_FPGA = 0x00050000   # error at FPGA of main board in pco.camera 
	SC2_ERROR_PCOCAM_HEAD_FPGA = 0x00060000   # error at FGPA of head board in pco.camera 
	SC2_ERROR_PCOCAM_MAIN_BOARD = 0x00070000  # error at main board in pco.camera
	SC2_ERROR_PCOCAM_HEAD_CPLD = 0x00080000   # error at CPLD of head board in pco.camera
	SC2_ERROR_SENSOR = 0x00090000             # error at image sensor (CCD or CMOS)
	SC2_ERROR_SDKDLL = 0x000A0000             # error inside the SDKDLL
	SC2_ERROR_DRIVER = 0x000B0000             # error inside the driver
	SC2_ERROR_POWER = 0x000D0000              # error within power unit
	PCO_ERROR_CAMWARE = 0x00100000            # error in CamWare (also some kind of "device")
	PCO_ERROR_CONVERTDLL = 0x00110000         # error inside the convert dll
	
class PCO_Exception(Exception):
	def __init__(self, ret_code):
		super(PCO_Exception, self).__init__(self)
		self.ret_code = ret_code

	def GetErrorText(self):
		""" 
		Get a detailed description for an error.
		"""
		
		f = pixelfly_dll.PCO_GetErrorText
		f.argtypes = (ctypes.c_uint, ctypes.c_char_p, ctypes.c_uint)
		desc = ctypes.create_string_buffer(256)
		f(self.ret_code, desc, 256)
		return desc.raw.decode('ascii')

class PCO_SC2_Hardware_DESC(ctypes.Structure):
	_fields_ = [('szName', ctypes.c_char * 16),
				('wBatchNo', ctypes.c_ushort),
				('wRevision', ctypes.c_ushort),
				('wVariant', ctypes.c_ushort),
				('ZZwDummy', ctypes.c_ushort * 20)]

PCO_MAXVERSIONHW = 10				
class PCO_HW_Vers(ctypes.Structure):
	_fields_ = [('BoardNum', ctypes.c_ushort),
				('Board', PCO_SC2_Hardware_DESC * PCO_MAXVERSIONHW)]

class PCO_SC2_Firmware_DESC(ctypes.Structure):
	_fields_ = [('szName', ctypes.c_char * 16),
				('bMinorRev', ctypes.c_byte),
				('bMajorRev', ctypes.c_byte),
				('wVariant', ctypes.c_ushort),
				('ZZwDummy', ctypes.c_ushort * 22)]

PCO_MAXVERSIONFW = 10				
class PCO_FW_Vers(ctypes.Structure):
	_fields_ = [('DeviceNum', ctypes.c_ushort),
				('Device', PCO_SC2_Firmware_DESC * PCO_MAXVERSIONFW)]
				
class PCO_CameraType(ctypes.Structure):
	_fields_ = [('wSize', ctypes.c_ushort),
				('wCamType', ctypes.c_ushort),
				('wCamSubType', ctypes.c_ushort),
				('ZZwAlignDummy1', ctypes.c_ushort),
				('dwSerialNumber', ctypes.c_uint),
				('dwHWVersion', ctypes.c_uint),
				('dwFWVersion', ctypes.c_uint),
				('wInterfaceType', ctypes.c_ushort),
				('strHardwareVersion', PCO_HW_Vers),
				('strFirmwareVersion', PCO_FW_Vers),
				('ZZwDummy', ctypes.c_ushort * 39)]
	
	def __init__(self):
		super(PCO_CameraType, self).__init__()
		self.wSize = ctypes.sizeof(PCO_CameraType)
		
	def __str__(self):
		return """CamType: {type:}
CamSubType: {subtype:}
Serial number: {serial:}
HW Version: {hw:}
FW Version: {fw:}
Interface type: {inter:}""".format(type=self.wCamType,
			subtype=self.wCamSubType,
			serial=self.dwSerialNumber,
			hw=self.dwHWVersion,
			fw=self.dwFWVersion,
			inter=self.wInterfaceType)

class PCO_General(ctypes.Structure):
	_fields_ = [('wSize', ctypes.c_ushort),
				('ZZwAlignDummy1', ctypes.c_ushort),
				('strCamType', PCO_CameraType),
				('dwCamHealthWarnings', ctypes.c_uint),
				('dwCamHealthErrors', ctypes.c_uint),
				('dwCamHealthStatus', ctypes.c_uint),
				('sCCDTemperature', ctypes.c_short),
				('sCamTemperature', ctypes.c_short),
				('sPowerSupplyTemperature', ctypes.c_short),
				('ZZwDummy', ctypes.c_ushort * 37)]
	
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
Power Supply Temperature = {power:}""".format(camType=str(self.strCamType),
			warn=self.dwCamHealthWarnings,
			err=self.dwCamHealthErrors,
			stat=self.dwCamHealthStatus,
			ccd=self.sCCDTemperature,
			power=self.sPowerSupplyTemperature)
				
PCO_RECORDINGDUMMY = 22
class PCO_Recording(ctypes.Structure):
	_fields_ = [("wSize", ctypes.c_ushort),
			    ("wStorageMode", ctypes.c_ushort),
				("wRecSubmode", ctypes.c_ushort),
				("wRecState", ctypes.c_ushort),
				("wAcquMode", ctypes.c_ushort),
				("wAcquEnableStatus", ctypes.c_ushort),
				("ucDay", ctypes.c_byte),
				("ucMonth", ctypes.c_byte),
				("wYear", ctypes.c_ushort),
				("wHour", ctypes.c_ushort),
				("ucMin", ctypes.c_byte),
				("ucSec", ctypes.c_byte),
				("wTimeSampMode", ctypes.c_ushort),
				("wRecordStopEventMode", ctypes.c_ushort),
				("dwRecordStopDelayImages", ctypes.c_uint),
				("wMetaDataMode", ctypes.c_ushort),
				("wMetaDataSize", ctypes.c_ushort),
				("wMetaDataVersion", ctypes.c_ushort),
				("ZZwDummy1", ctypes.c_ushort),
				("dwAcquModeExNumberImages", ctypes.c_uint),
				("dwAcquModeExReserved", ctypes.c_uint * 4),
				("ZZwDummy", ctypes.c_short * PCO_RECORDINGDUMMY)]
	
	def __init__(self):
		super(PCO_Recording, self).__init__()
		self.wSize = ctypes.sizeof(PCO_Recording)

class PCO_Description(ctypes.Structure):
	_fields_ = [("wSize", ctypes.c_ushort),
			    ("wSensorTypeDESC", ctypes.c_ushort),
				("wSensorSubTypeDESC", ctypes.c_ushort),
				("wMaxHorzResStdDESC", ctypes.c_ushort),
				("wMaxVertResStdDESC", ctypes.c_ushort),
				("wMaxHorzResExtDESC", ctypes.c_ushort),
				("wMaxVertResExtDESC", ctypes.c_ushort),
				("wDynResDESC", ctypes.c_ushort),
				("wMaxBinHorzDESC", ctypes.c_ushort),
				("wBinHorzSteppingDESC", ctypes.c_ushort),
				("wMaxBinVertDESC", ctypes.c_ushort),
				("wBinVertSteppingDESC", ctypes.c_ushort),
				("wRoiHorStepsDESC", ctypes.c_ushort),
				("wRoiVertStepsDESC", ctypes.c_ushort),
				("wNumADCsDESC", ctypes.c_ushort),
				("wMinSizeHorzDESC", ctypes.c_ushort),
				("dwPixelRateDESC", ctypes.c_uint*4),
				("ZZdwDummypr", ctypes.c_uint*20),
				("wConvFactDESC", ctypes.c_ushort*4),
				("sCoolingSetPoints", ctypes.c_short*10),
				("ZZdwDummycv", ctypes.c_ushort*8),
				("wSoftRoiHozStepsDESC", ctypes.c_ushort),
				("wSoftRoiVertStepsDESC", ctypes.c_ushort),
				("wIRDESC", ctypes.c_ushort),
				("wMinSizeVertDESC", ctypes.c_ushort),
				("dwMinDelayDESC", ctypes.c_uint),
				("dwMaxDelayDESC", ctypes.c_uint),
				("dwMinDelayStepDESC", ctypes.c_uint),
				("dwMinExposureDESC", ctypes.c_uint),
				("dwMaxExposureDESC", ctypes.c_uint),
				("dwMinExposureStepDESC", ctypes.c_uint),
				("dwMinDelayIRDESC", ctypes.c_uint),
				("dwMaxDelayIRDESC", ctypes.c_uint),
				("dwMinExposureIRDESC", ctypes.c_uint),
				("dwMaxExposureIRDESC", ctypes.c_uint),
				("wTimeTableDESC", ctypes.c_ushort),
				("wDoubleImageDESC", ctypes.c_ushort),
				("sMinCoolSetDESC", ctypes.c_short),
				("sMaxCoolSetDESC", ctypes.c_short),
				("sDefaultCoolSetDESC", ctypes.c_short),
				("wPowerDownModeDESC", ctypes.c_ushort),
				("wOffsetRegulationDESC", ctypes.c_ushort),
				("wColorPatternDESC", ctypes.c_ushort),
				("wPatternTypeDESC", ctypes.c_ushort),
				("wDummy1", ctypes.c_ushort),
				("wDummy2", ctypes.c_ushort),
				("wNumCoolingSetpoints", ctypes.c_ushort),
				("dwGeneralCapsDESC1", ctypes.c_uint),
				("dwGeneralCapsDESC2", ctypes.c_uint),
				("dwExtSyncFrequency", ctypes.c_uint*4),
				("dwGeneralCapsDESC3", ctypes.c_uint),
				("dwGeneralCapsDESC4", ctypes.c_uint),
				("ZZdwDummy", ctypes.c_uint*40)]
	
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
		return self.dwPixelRateDESC
		
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
		return (self.dwMinExposureDESC, self.dwMaxExposureDESC, self.dwMinExposureStepDESC)
		
	def nth_cap(self, n):
		return (self.dwGeneralCapsDESC1 >> n) & 0x0001 == 0x0001
		
	@property
	def general_capabilities(self):
		return {'Noisefilter available': self.nth_cap(0),
			    'Hotpixelfilter available': self.nth_cap(1),
				'Hotpixel works only with noisefilter': self.nth_cap(2),
				'Timestamp ASCII only available (Timestamp mode 3 enabled)': self.nth_cap(3),
				'Dataformat 2x12': self.nth_cap(4),
				'Record Stop Event available': self.nth_cap(5),
				'Hot Pixel correction': self.nth_cap(6),
				'Ext.Exp.Ctrl. not available': self.nth_cap(7),
				'Timestamp not available': self.nth_cap(8),
				'Acquire mode not available': self.nth_cap(9),
				'Dataformat 4x16': self.nth_cap(10),
				'Dataformat 5x16': self.nth_cap(11),
				'Camera has no internal recorder memory': self.nth_cap(12),
				'Camera can be set to fast timing mode (PIV)': self.nth_cap(13),
				'Camera can produce metadata': self.nth_cap(14),
				'Camera allows Set/GetFrameRate cmd': self.nth_cap(15),
				'Camera has Correlated Double Image Mode': self.nth_cap(16),
				'Camera has CCM': self.nth_cap(17),
				'Camera can be synched externally': self.nth_cap(18),
				'Global shutter setting not available': self.nth_cap(19),
				'Camera supports global reset rolling readout': self.nth_cap(20),
				'Camera supports extended acquire command': self.nth_cap(21),
				'Camera supports fan control command': self.nth_cap(22),
				'Camera vert.ROI must be symmetrical to horizontal axis': self.nth_cap(23),
				'Camera horz.ROI must be symmetrical to vertical axis': self.nth_cap(24),
				'Camera has cooling setpoints instead of cooling range': self.nth_cap(25),
				'HW_IO_SIGNAL_DESCRIPTOR available': self.nth_cap(30),
				'Enhanced descriptor available': self.nth_cap(31)}
				
	def __str__(self):
		desc = """Maximum resolution (STD): {:} x {:}
Maximum resolution (EXT): {:} x {:}
Dynamic resolution: {:} bits
Possible pixel rates: {:} Hz
Possible delay: min {:} ns, max {:} ms, step {:} ns
Possible exposure: min {:} ns, max {:} ms, step {:} ns""".format( \
		self.maximum_resolution_std[0], self.maximum_resolution_std[1],
		self.maximum_resolution_ext[0], self.maximum_resolution_ext[1], 
		self.dynamic_resolution,
		str(self.possible_pixelrate),
		self.possible_delay[0], self.possible_delay[1], self.possible_delay[2],
		self.possible_exposure[0], self.possible_exposure[1], self.possible_exposure[2])
		caps_dict = self.general_capabilities
		caps = '\n'.join([k + ':' + str(caps_dict[k]) for k in caps_dict])
		return desc + "\n" + caps
		
class PCO_Description2(ctypes.Structure):
	_fields_ = [("wSize", ctypes.c_ushort),
				("ZZwAlignDummy1", ctypes.c_ushort),
				("dwMinPeriodicalTimeDESC2", ctypes.c_uint),
				("dwMaxPeriodicalTimeDESC2", ctypes.c_uint),
				("dwMinPeriodicalConditionDESC2", ctypes.c_uint),
				("dwMaxNumberOfExposuresDESC2", ctypes.c_uint),
				("lMinMonitorSignalOffsetDESC2", ctypes.c_long),
				("dwMaxMonitorSignalOffsetDESC2", ctypes.c_uint),
				("dwMinPeriodicalStepDESC2", ctypes.c_uint),
				("dwStartTimeDelayDESC2", ctypes.c_uint),
				("dwMinMonitorStepDESC2", ctypes.c_uint),
				("dwMinDelayModDESC2", ctypes.c_uint),
				("dwMaxDelayModDESC2", ctypes.c_uint),
				("dwMinDelayStepModDESC2", ctypes.c_uint),
				("dwMinExposureModDESC2", ctypes.c_uint),
				("dwMaxExposureModDESC2", ctypes.c_uint),
				("dwMinExposureStepModDESC2", ctypes.c_uint),
				("dwModulateCapsDESC2", ctypes.c_uint),
				("dwReserved", ctypes.c_uint*16),
				("ZZdwDummy", ctypes.c_uint*41)]
	
	def __init__(self):
		super(PCO_Description2, self).__init__()
		self.wSize = ctypes.sizeof(PCO_Description2)

NUM_MAX_SIGNALS = 20
NUM_SIGNALS = 4
NUM_SIGNAL_NAMES = 4

class PCO_Single_Signal_Desc(ctypes.Structure):
	_fields_ = [("wSize", ctypes.c_ushort),
				("ZZwAlignDummy1", ctypes.c_ushort),
				("strSignalName", (ctypes.c_char*25)*NUM_SIGNAL_NAMES),
				("wSignalDefinitions", ctypes.c_ushort),
				("wSignalTypes", ctypes.c_ushort),
				("wSignalPolarity", ctypes.c_ushort),
				("wSignalFilter", ctypes.c_ushort),
				("dwDummy", ctypes.c_uint*22)]
	
	def __init__(self):
		super(PCO_Single_Signal_Desc, self).__init__()
		self.wSize = ctypes.sizeof(PCO_Single_Signal_Desc)
		
class PCO_Signal_Description(ctypes.Structure):
	_fields_ = [("wSize", ctypes.c_ushort),
				("wNumOfSignals", ctypes.c_ushort),
				("strSingleSignalDesc", PCO_Single_Signal_Desc*NUM_MAX_SIGNALS),
				("dwDummy", ctypes.c_uint*524)]
				
	def __init__(self):
		super(PCO_Signal_Description, self).__init__()
		self.wSize = ctypes.sizeof(PCO_Signal_Description)
		for i in range(NUM_MAX_SIGNALS):
			self.strSingleSignalDesc[i].__init__()
			
PCO_SENSORDUMMY = 7
class PCO_Sensor(ctypes.Structure):
	_fields_ = [("wSize", ctypes.c_ushort),
				("ZZwAlignDummy1", ctypes.c_ushort),
				("strDescription", PCO_Description),
				("strDescription2", PCO_Description2),
				("ZZdwDummy2", ctypes.c_uint * 256),
				("wSensorFormat", ctypes.c_ushort),
				("wRoiX0", ctypes.c_ushort),
				("wRoiY0", ctypes.c_ushort),
				("wRoiX1", ctypes.c_ushort),
				("wRoiY1", ctypes.c_ushort),
				("wBinHorz", ctypes.c_ushort),
				("wBinVert", ctypes.c_ushort),
				("ZZwAlignDummy2", ctypes.c_ushort),
				("dwPixelRate", ctypes.c_uint),
				("wConvFact", ctypes.c_ushort),
				("wDoubleImage", ctypes.c_ushort),
				("wADCOperation", ctypes.c_ushort),
				("wIR", ctypes.c_ushort),
				("sCoolSet", ctypes.c_short),
				("wOffsetRegulation", ctypes.c_ushort),
				("wNoiseFilterMode", ctypes.c_ushort),
				("wFastReadoutMode", ctypes.c_ushort),
				("wDSNUAdjustMode", ctypes.c_ushort),
				("wCDIMode", ctypes.c_ushort),
				("ZZwDummy", ctypes.c_ushort * 36),
				("strSignalDesc", PCO_Signal_Description),
				("ZZdwDummy", ctypes.c_uint * PCO_SENSORDUMMY)]
				
	def __init__(self):
		super(PCO_Sensor, self).__init__()
		self.wSize = ctypes.sizeof(PCO_Sensor)
		self.strDescription.__init__()
		self.strDescription2.__init__()
		self.strSignalDesc.__init__()
		
	def __str__(self):
		return str(self.strDescription) + """
SensorFormat: {:}
ROI: ({:}, {:}) x ({:}, {:})
PixelRate: {:} Hz""".format(self.wSensorFormat, self.wRoiX0, self.wRoiY0,
					self.wRoiX1, self.wRoiY1, self.dwPixelRate)
				
def PCO_OpenCamera(board=0):
	"""
	Open a camera device and attach it to a handle, which will be returned by the parameter ph. This
	function scans for the next available camera. If you want to access a distinct camera please use
	PCO_OpenCameraEx.
	Due to historical reasons the wCamNum parameter is a don’t care.
	"""
	
	f = pixelfly_dll.PCO_OpenCamera
	f.argtypes = (ctypes.POINTER(ctypes.c_int), ctypes.c_ushort)
	f.restype = ctypes.c_int
	h = ctypes.c_int(0)
	ret_code = f(ctypes.byref(h), board)
	if ret_code != 0:
		raise PCO_Exception(ret_code)
	return h

def PCO_CloseCamera(handle):
	"""
	Close a camera device
	"""
	
	f = pixelfly_dll.PCO_CloseCamera
	f.argtypes = (ctypes.c_int,)
	f.restype = ctypes.c_int
	ret_code = f(handle)
	if ret_code != 0:
		raise PCO_Exception(ret_code)

def PCO_GetInfoString(handle):
	"""
	This call can be used to read some information about the camera, e.g. firmware versions
	"""
	
	f = pixelfly_dll.PCO_GetInfoString
	f.argtypes = (ctypes.c_int, ctypes.c_uint, ctypes.c_char_p, ctypes.c_ushort)
	f.restype = ctypes.c_int
	p = ctypes.create_string_buffer(256)
	ret_code = f(handle, 0, p, 256)
	if ret_code != 0:
		raise PCO_Exception(ret_code)
	return p.raw.decode('ascii')

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
	f.argtypes = (ctypes.c_int, ctypes.POINTER(PCO_General))
	f.restype = ctypes.c_int
	strGeneral = PCO_General()
	ret_code = f(handle, ctypes.byref(strGeneral))
	if ret_code != 0:
		raise PCO_Exception(ret_code)
	return strGeneral

def PCO_GetSensorStruct(handle):
	"""
	Get the complete set of the sensor functions settings
	"""
	
	f = pixelfly_dll.PCO_GetSensorStruct
	f.argtypes = (ctypes.c_int, ctypes.POINTER(PCO_Sensor))
	f.restype = ctypes.c_int
	strSensor = PCO_Sensor()
	ret_code = f(handle, ctypes.byref(strSensor))
	if ret_code != 0:
		raise PCO_Exception(ret_code)
	return strSensor

def PCO_GetCameraDescription():
	pass
	
def PCO_GetTimingStruct():
	pass
	
def PCO_GetRecordingStruct(handle):
	"""
	Get the complete set of the recording function
	settings. Please fill in all wSize parameters,
	even in embedded structures.
	"""
	
	strRecording = PCO_Recording()
	f = pixelfly_dll.PCO_GetRecordingStruct
	f.argtypes = (ctypes.c_int, ctypes.POINTER(PCO_Recording))
	f.restype = ctypes.c_int
	ret_code = f(handle, ctypes.byref(strRecording))
	if ret_code != 0:
		raise PCO_Exception(ret_code)
	return strRecording
	
def PCO_GetSizes():
	pass

def PCO_AllocateBuffer():
	pass

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
	f.argtypes = (ctypes.c_int,)
	f.restype = ctypes.c_int
	ret_code = f(handle)
	if ret_code != 0:
		raise PCO_Exception(ret_code)
		
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
	
	f = pixelfly_dll.PCO_SetRecordingState
	f.argtypes = (ctypes.c_int, ctypes.c_ushort)
	f.restype = ctypes.c_int
	wRecState = ctypes.c_ushort(1 if state else 0)
	ret_code = f(handle, wRecState)
	if ret_code != 0:
		raise PCO_Exception(ret_code)
	
def PCO_AddBufferEx():
	pass
	
def PCO_CancelImages():
	pass

def PCO_GetNumberOfImagesInSegment():
	pass
	
def PCO_GetImageEx():
	pass
	
def PCO_FreeBuffer():
	pass
	
if __name__ == '__main__':
	try:
		h = PCO_OpenCamera()
		info = PCO_GetInfoString(h)
		print(info)
		general = PCO_GetGeneral(h)
		print(general)
		sensor = PCO_GetSensorStruct(h)
		print(sensor)
	except PCO_Exception as pe:
		print('Error: "', pe.GetErrorText(), '"')
	finally:
		PCO_CloseCamera(h)
		print('Camera closed')
	