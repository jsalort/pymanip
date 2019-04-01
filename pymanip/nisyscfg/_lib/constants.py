"""

NI System Configuration constants

"""

from enum import IntEnum

NISYSCFG_SIMPLE_STRING_LENGTH = 1024

class NISysCfgLocale(IntEnum): 
    Default = 0,
    ChineseSimplified = 2052
    English = 1033
    French = 1036
    German = 1031
    Japanese = 1041
    Korean = 1042

class NISysCfgFilterMode(IntEnum):
   MatchValuesAll = 1
   MatchValuesAny = 2
   MatchValuesNone = 3
   ModeAllPropertiesExist = 4

class NISysCfgResourceProperty(IntEnum):
   # Read-only properties
   IsDevice = 16781312  # NISysCfgBool
   IsChassis = 16941056  # NISysCfgBool
   ConnectsToBusType = 16785408  # NISysCfgBusType
   VendorId = 16789504  # ctypes.c_uint,
   VendorName = 16793600  # ctypes.c_char_p,
   ProductId = 16797696  # ctypes.c_uint,
   ProductName = 16801792  # ctypes.c_char_p,
   SerialNumber = 16805888  # ctypes.c_char_p,
   FirmwareRevision = 16969728  # ctypes.c_char_p,
   IsNIProduct = 16809984  # NISysCfgBool
   IsSimulated = 16814080  # NISysCfgBool
   ConnectsToLinkName = 16818176  # ctypes.c_char_p,
   HasDriver = 16920576  # NISysCfgHasDriverType
   IsPresent = 16924672  # NISysCfgIsPresentType
   SlotNumber = 16822272  # int
   SupportsInternalCalibration = 16842752  # NISysCfgBool
   InternalCalibrationLastTime = 16846848  # NISysCfgTimestampUTC
   InternalCalibrationLastTemp = 16850944  # double
   SupportsExternalCalibration = 16859136  # NISysCfgBool
   ExternalCalibrationLastTemp = 16867328  # double
   CalibrationComments = 16961536  # ctypes.c_char_p,
   CurrentTemp = 16965632  # double
   PxiPciBusNumber = 16875520  # ctypes.c_uint,
   PxiPciDeviceNumber = 16879616  # ctypes.c_uint,
   PxiPciFunctionNumber = 16883712  # ctypes.c_uint,
   PxiPciLinkWidth = 16973824  # int
   PxiPciMaxLinkWidth = 16977920  # int
   UsbInterface = 16887808  # ctypes.c_uint,
   TcpHostName = 16928768  # ctypes.c_char_p,
   TcpMacAddress = 16986112  # ctypes.c_char_p,
   TcpIpAddress = 16957440  # ctypes.c_char_p,
   TcpDeviceClass = 17022976  # ctypes.c_char_p,
   GpibPrimaryAddress = 16994304  # int
   GpibSecondaryAddress = 16998400  # int
   ProvidesBusType = 16932864  # NISysCfgBusType
   ProvidesLinkName = 16936960  # ctypes.c_char_p,
   NumberOfSlots = 16826368  # int
   SupportsFirmwareUpdate = 17080320  # NISysCfgBool
   FirmwareFilePattern = 17084416  # ctypes.c_char_p,
   RecommendedCalibrationInterval = 17207296  # int
   SupportsCalibrationWrite = 17215488  # NISysCfgBool
   HardwareRevision = 17256448  # ctypes.c_char_p,
   CpuModelName = 17313792  # ctypes.c_char_p,
   CpuSteppingRevision = 17317888  # int

   # Read/Write firmware properties
   FirmwareUpdateMode = 17354752  # NISysCfgFirmwareUpdateMode

   # Read/Write calibration properties
   ExternalCalibrationLastTime = 16863232  # NISysCfgTimestampUTC
   RecommendedNextCalibrationTime = 16871424  # NISysCfgTimestampUTC

   # Write-only calibration properties
   CalibrationCurrentPassword = 17223680  # ctypes.c_char_p,
   CalibrationNewPassword = 17227776  # ctypes.c_char_p,

   # Read/Write remote access properties
   SysCfgAccess = 219504640  # NISysCfgAccessType

   # Read-only network adapter properties
   AdapterType = 219332608  # NISysCfgAdapterType
   MacAddress = 219168768  # ctypes.c_char_p,

   # Read/Write network adapter properties
   AdapterMode = 219160576  # NISysCfgAdapterMode
   TcpIpRequestMode = 219172864  # NISysCfgIpAddressMode
   TcpIpv4Address = 219181056  # ctypes.c_char_p,
   TcpIpv4Subnet = 219189248  # ctypes.c_char_p,
   TcpIpv4Gateway = 219193344  # ctypes.c_char_p,
   TcpIpv4DnsServer = 219197440  # ctypes.c_char_p,
   TcpPreferredLinkSpeed = 219213824  # NISysCfgLinkSpeed
   TcpCurrentLinkSpeed = 219222016  # NISysCfgLinkSpeed
   TcpPacketDetection = 219258880  # NISysCfgPacketDetection
   TcpPollingInterval = 219262976  # ctypes.c_uint,
   IsPrimaryAdapter = 219308032  # NISysCfgBool
   EtherCatMasterId = 219250688  # ctypes.c_uint,
   EtherCatMasterRedundancy = 219500544  # NISysCfgBool

   # Read-only wireless network adapter properties
   WlanBssid = 219398144  # ctypes.c_char_p,
   WlanCurrentLinkQuality = 219394048  # ctypes.c_uint,

   # Read/Write wireless network adapter properties
   WlanCurrentSsid = 219377664  # ctypes.c_char_p,
   WlanCurrentConnectionType = 219381760  # NISysCfgConnectionType
   WlanCurrentSecurityType = 219385856  # NISysCfgSecurityType
   WlanCurrentEapType = 219389952  # NISysCfgEapType
   WlanCountryCode = 219406336  # int
   WlanChannelNumber = 219410432  # ctypes.c_uint,
   WlanClientCertificate = 219422720  # ctypes.c_char_p,

   # Write-only wireless network adapter properties
   WlanSecurityIdentity = 219414528  # ctypes.c_char_p,
   WlanSecurityKey = 219418624  # ctypes.c_char_p,

   # Read-only time properties
   SystemStartTime = 17108992  # NISysCfgTimestampUTC 

   # Read/Write time properties
   CurrentTime = 219279360  # NISysCfgTimestampUTC 
   TimeZone = 219471872  # ctypes.c_char_p,

   # Read/Write startup settings properties
   UserDirectedSafeModeSwitch = 219537408  # NISysCfgBool
   ConsoleOutSwitch = 219541504  # NISysCfgBool
   IpResetSwitch = 219545600  # NISysCfgBool

   # Read-only counts for indexed properties
   NumberOfDiscoveredAccessPoints = 219365376  # ctypes.c_uint,
   NumberOfExperts = 16891904  # int
   NumberOfServices = 17010688  # int
   NumberOfAvailableFirmwareVersions = 17088512  # int
   NumberOfCpus = 17137664  # int
   NumberOfFans = 17174528  # int
   NumberOfTemperatureSensors = 17186816  # int
   NumberOfVoltageSensors = 17149952  # int
   NumberOfUserLedIndicators = 17281024  # int
   NumberOfUserSwitches = 17293312  # int

class NISysCfgIndexedProperty(IntEnum):
    ExpertName = 16900096
    ExpertResourceName = 16896000
    ExpertUserAlias = 16904192