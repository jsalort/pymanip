import ctypes
from ctypes.util import find_library
import os
import platform
from enum import IntEnum
from pprint import pprint

libpath = find_library('nisyscfg')
if os.name=='posix':
    lib = ctypes.cdll.LoadLibrary(libpath)
elif os.name=='nt':
    lib = ctypes.windll.LoadLibrary(libpath)

NISysCfgEnumExpertHandle = ctypes.c_void_p
NISysCfgSessionHandle = ctypes.c_void_p
NISysCfgStatus = ctypes.c_uint64
NISysCfgBool = ctypes.c_int
NISysCfgBusType = ctypes.c_int
NISysCfgHasDriverType = ctypes.c_int
NISysCfgIsPresentType = ctypes.c_int
NISysCfgTimestampUTC = ctypes.c_uint32*4
NISysCfgFirmwareUpdateMode = ctypes.c_int
NISysCfgAccessType = ctypes.c_int
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

NISysCfgResourcePropertyType = {
    NISysCfgResourceProperty.IsDevice: (NISysCfgBool, 0, None, ctypes.byref, None),
    NISysCfgResourceProperty.IsChassis: (NISysCfgBool, 0, None, ctypes.byref, None),
    NISysCfgResourceProperty.ConnectsToBusType: (NISysCfgBusType, 0, None, ctypes.byref, None),
    NISysCfgResourceProperty.VendorId: (ctypes.c_uint, 0, None, ctypes.byref, None),
    NISysCfgResourceProperty.VendorName: (ctypes.c_char_p, NISYSCFG_SIMPLE_STRING_LENGTH, ctypes.create_string_buffer, lambda x: x, None), 
    NISysCfgResourceProperty.ProductId: (ctypes.c_uint, 0, None, ctypes.byref, None),
    NISysCfgResourceProperty.ProductName: (ctypes.c_char_p, NISYSCFG_SIMPLE_STRING_LENGTH, ctypes.create_string_buffer, lambda x: x, None),
    NISysCfgResourceProperty.SerialNumber: (ctypes.c_char_p, NISYSCFG_SIMPLE_STRING_LENGTH, ctypes.create_string_buffer, lambda x: x, None),
    NISysCfgResourceProperty.FirmwareRevision: (ctypes.c_char_p, NISYSCFG_SIMPLE_STRING_LENGTH, ctypes.create_string_buffer, lambda x: x, None),
    NISysCfgResourceProperty.IsNIProduct: (NISysCfgBool, 0, None, ctypes.byref, None),
    NISysCfgResourceProperty.IsSimulated: (NISysCfgBool, 0, None, ctypes.byref, None),
    NISysCfgResourceProperty.ConnectsToLinkName: (ctypes.c_char_p, NISYSCFG_SIMPLE_STRING_LENGTH, ctypes.create_string_buffer, lambda x: x, None),
    NISysCfgResourceProperty.HasDriver: (NISysCfgHasDriverType, 0, None, ctypes.byref, None),
    NISysCfgResourceProperty.IsPresent: (NISysCfgIsPresentType, 0, None, ctypes.byref, None),
    NISysCfgResourceProperty.SlotNumber: (ctypes.c_int, 0, None, ctypes.byref, None),
    NISysCfgResourceProperty.SupportsInternalCalibration: (NISysCfgBool, 0, None, ctypes.byref, None),
    NISysCfgResourceProperty.InternalCalibrationLastTime: (NISysCfgTimestampUTC, [0,0,0,0], None, ctypes.byref, None),
    NISysCfgResourceProperty.InternalCalibrationLastTemp: (ctypes.c_double, 0.0, None, ctypes.byref, None),
    NISysCfgResourceProperty.SupportsExternalCalibration: (NISysCfgBool, 0, None, ctypes.byref, None),
    NISysCfgResourceProperty.ExternalCalibrationLastTemp: (ctypes.c_double, 0.0, None, ctypes.byref, None),
    NISysCfgResourceProperty.CalibrationComments: (ctypes.c_char_p, NISYSCFG_SIMPLE_STRING_LENGTH, ctypes.create_string_buffer, lambda x: x, None),
    NISysCfgResourceProperty.CurrentTemp: (ctypes.c_double, 0.0, None, ctypes.byref, None),
    NISysCfgResourceProperty.PxiPciBusNumber: (ctypes.c_uint, 0, None, ctypes.byref, None),
    NISysCfgResourceProperty.PxiPciDeviceNumber: (ctypes.c_uint, 0, None, ctypes.byref, None),
    NISysCfgResourceProperty.PxiPciFunctionNumber: (ctypes.c_uint, 0, None, ctypes.byref, None),
    NISysCfgResourceProperty.PxiPciLinkWidth: (ctypes.c_int, 0, None, ctypes.byref, None),
    NISysCfgResourceProperty.PxiPciMaxLinkWidth: (ctypes.c_int, 0, None, ctypes.byref, None),
    NISysCfgResourceProperty.UsbInterface: (ctypes.c_uint, 0, None, ctypes.byref, None),
    NISysCfgResourceProperty.TcpHostName: (ctypes.c_char_p, NISYSCFG_SIMPLE_STRING_LENGTH, ctypes.create_string_buffer, lambda x: x, None),
    NISysCfgResourceProperty.TcpMacAddress: (ctypes.c_char_p, NISYSCFG_SIMPLE_STRING_LENGTH, ctypes.create_string_buffer, lambda x: x, None),
    NISysCfgResourceProperty.TcpIpAddress: (ctypes.c_char_p, NISYSCFG_SIMPLE_STRING_LENGTH, ctypes.create_string_buffer, lambda x: x, None),
    NISysCfgResourceProperty.TcpDeviceClass: (ctypes.c_char_p, NISYSCFG_SIMPLE_STRING_LENGTH, ctypes.create_string_buffer, lambda x: x, None),
    NISysCfgResourceProperty.GpibPrimaryAddress: (ctypes.c_int, 0, None, ctypes.byref, None),
    NISysCfgResourceProperty.GpibSecondaryAddress: (ctypes.c_int, 0, None, ctypes.byref, None),
    NISysCfgResourceProperty.ProvidesBusType: (NISysCfgBusType, 0, None, ctypes.byref, None),
    NISysCfgResourceProperty.ProvidesLinkName: (ctypes.c_char_p, NISYSCFG_SIMPLE_STRING_LENGTH, ctypes.create_string_buffer, lambda x: x, None),
    NISysCfgResourceProperty.NumberOfSlots: (ctypes.c_int, 0, None, ctypes.byref, None),
    NISysCfgResourceProperty.SupportsFirmwareUpdate: (NISysCfgBool, 0, None, ctypes.byref, None),
    NISysCfgResourceProperty.FirmwareFilePattern: (ctypes.c_char_p, NISYSCFG_SIMPLE_STRING_LENGTH, ctypes.create_string_buffer, lambda x: x, None),
    NISysCfgResourceProperty.RecommendedCalibrationInterval: (ctypes.c_int, 0, None, ctypes.byref, None),
    NISysCfgResourceProperty.SupportsCalibrationWrite: (NISysCfgBool, 0, None, ctypes.byref, None),
    NISysCfgResourceProperty.HardwareRevision: (ctypes.c_char_p, NISYSCFG_SIMPLE_STRING_LENGTH, ctypes.create_string_buffer, lambda x: x, None),
    NISysCfgResourceProperty.CpuModelName: (ctypes.c_char_p, NISYSCFG_SIMPLE_STRING_LENGTH, ctypes.create_string_buffer, lambda x: x, None),
    NISysCfgResourceProperty.CpuSteppingRevision: (ctypes.c_int, 0, None, ctypes.byref, None),
    #NISysCfgResourceProperty.FirmwareUpdateMode: NISysCfgFirmwareUpdateMode,
    #NISysCfgResourceProperty.ExternalCalibrationLastTime: NISysCfgTimestampUTC,
    #NISysCfgResourceProperty.RecommendedNextCalibrationTime: NISysCfgTimestampUTC,
    NISysCfgResourceProperty.CalibrationCurrentPassword: (ctypes.c_char_p, NISYSCFG_SIMPLE_STRING_LENGTH, ctypes.create_string_buffer, lambda x: x, None),
    NISysCfgResourceProperty.CalibrationNewPassword: (ctypes.c_char_p, NISYSCFG_SIMPLE_STRING_LENGTH, ctypes.create_string_buffer, lambda x: x, None),
    #NISysCfgResourceProperty.SysCfgAccess: NISysCfgAccessType,
    #NISysCfgResourceProperty.AdapterType: NISysCfgAdapterType,
    NISysCfgResourceProperty.MacAddress: (ctypes.c_char_p, NISYSCFG_SIMPLE_STRING_LENGTH, ctypes.create_string_buffer, lambda x: x, None),
    #NISysCfgResourceProperty.AdapterMode: NISysCfgAdapterMode,
    #NISysCfgResourceProperty.TcpIpRequestMode: NISysCfgIpAddressMode,
    NISysCfgResourceProperty.TcpIpv4Address: (ctypes.c_char_p, NISYSCFG_SIMPLE_STRING_LENGTH, ctypes.create_string_buffer, lambda x: x, None),
    NISysCfgResourceProperty.TcpIpv4Subnet: (ctypes.c_char_p, NISYSCFG_SIMPLE_STRING_LENGTH, ctypes.create_string_buffer, lambda x: x, None),
    NISysCfgResourceProperty.TcpIpv4Gateway: (ctypes.c_char_p, NISYSCFG_SIMPLE_STRING_LENGTH, ctypes.create_string_buffer, lambda x: x, None),
    NISysCfgResourceProperty.TcpIpv4DnsServer: (ctypes.c_char_p, NISYSCFG_SIMPLE_STRING_LENGTH, ctypes.create_string_buffer, lambda x: x, None),
    #NISysCfgResourceProperty.TcpPreferredLinkSpeed: NISysCfgLinkSpeed,
    #NISysCfgResourceProperty.TcpCurrentLinkSpeed: NISysCfgLinkSpeed,
    #NISysCfgResourceProperty.TcpPacketDetection: NISysCfgPacketDetection,
    NISysCfgResourceProperty.TcpPollingInterval: (ctypes.c_uint, 0, None, ctypes.byref, None),
    NISysCfgResourceProperty.IsPrimaryAdapter: (NISysCfgBool, 0, None, ctypes.byref, None),
    NISysCfgResourceProperty.EtherCatMasterId: (ctypes.c_uint, 0, None, ctypes.byref, None),
    NISysCfgResourceProperty.EtherCatMasterRedundancy: (NISysCfgBool, 0, None, ctypes.byref, None),
    NISysCfgResourceProperty.WlanBssid: (ctypes.c_char_p, NISYSCFG_SIMPLE_STRING_LENGTH, ctypes.create_string_buffer, lambda x: x, None),
    NISysCfgResourceProperty.WlanCurrentLinkQuality: (ctypes.c_uint, 0, None, ctypes.byref, None),
    NISysCfgResourceProperty.WlanCurrentSsid: (ctypes.c_char_p, NISYSCFG_SIMPLE_STRING_LENGTH, ctypes.create_string_buffer, lambda x: x, None),
    #NISysCfgResourceProperty.WlanCurrentConnectionType: NISysCfgConnectionType,
    #NISysCfgResourceProperty.WlanCurrentSecurityType: NISysCfgSecurityType,
    #NISysCfgResourceProperty.WlanCurrentEapType: NISysCfgEapType,
    NISysCfgResourceProperty.WlanCountryCode: (ctypes.c_int, 0, None, ctypes.byref, None),
    NISysCfgResourceProperty.WlanChannelNumber: (ctypes.c_uint, 0, None, ctypes.byref, None),
    NISysCfgResourceProperty.WlanClientCertificate: (ctypes.c_char_p, NISYSCFG_SIMPLE_STRING_LENGTH, ctypes.create_string_buffer, lambda x: x, None),
    NISysCfgResourceProperty.WlanSecurityIdentity: (ctypes.c_char_p, NISYSCFG_SIMPLE_STRING_LENGTH, ctypes.create_string_buffer, lambda x: x, None),
    NISysCfgResourceProperty.WlanSecurityKey: (ctypes.c_char_p, NISYSCFG_SIMPLE_STRING_LENGTH, ctypes.create_string_buffer, lambda x: x, None),
    #NISysCfgResourceProperty.SystemStartTime: NISysCfgTimestampUTC ,
    #NISysCfgResourceProperty.CurrentTime: NISysCfgTimestampUTC,
    NISysCfgResourceProperty.TimeZone: (ctypes.c_char_p, NISYSCFG_SIMPLE_STRING_LENGTH, ctypes.create_string_buffer, lambda x: x, None),
    NISysCfgResourceProperty.UserDirectedSafeModeSwitch: (NISysCfgBool, 0, None, ctypes.byref, None),
    NISysCfgResourceProperty.ConsoleOutSwitch: (NISysCfgBool, 0, None, ctypes.byref, None),
    NISysCfgResourceProperty.IpResetSwitch: (NISysCfgBool, 0, None, ctypes.byref, None),
    NISysCfgResourceProperty.NumberOfDiscoveredAccessPoints: (ctypes.c_uint, 0, None, ctypes.byref, None),
    NISysCfgResourceProperty.NumberOfExperts: (ctypes.c_int, 0, None, ctypes.byref, None),
    NISysCfgResourceProperty.NumberOfServices: (ctypes.c_int, 0, None, ctypes.byref, None),
    NISysCfgResourceProperty.NumberOfAvailableFirmwareVersions: (ctypes.c_int, 0, None, ctypes.byref, None),
    NISysCfgResourceProperty.NumberOfCpus: (ctypes.c_int, 0, None, ctypes.byref, None),
    NISysCfgResourceProperty.NumberOfFans: (ctypes.c_int, 0, None, ctypes.byref, None),
    NISysCfgResourceProperty.NumberOfTemperatureSensors: (ctypes.c_int, 0, None, ctypes.byref, None),
    NISysCfgResourceProperty.NumberOfVoltageSensors: (ctypes.c_int, 0, None, ctypes.byref, None),
    NISysCfgResourceProperty.NumberOfUserLedIndicators: (ctypes.c_int, 0, None, ctypes.byref, None),
    NISysCfgResourceProperty.NumberOfUserSwitches: (ctypes.c_int, 0, None, ctypes.byref, None),
}

class NISysCfgIndexedProperty(IntEnum):
    ExpertName = 16900096
    ExpertResourceName = 16896000
    ExpertUserAlias = 16904192

def NISysCfgInitializeSession(target='localhost', user=None, password=None, 
                              lang=NISysCfgLocale.Default, force_refresh=False, 
                              connect_timeout=1000):
    if isinstance(target, str):
        target = target.encode('ascii')
    if isinstance(user, str):
        user = user.encode('ascii')
    if isinstance(password, str):
        password = password.encode('ascii')
    f = lib.NISysCfgInitializeSession
    f.argtypes = (ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p,
                  ctypes.c_int, ctypes.c_int, ctypes.c_uint,
                  ctypes.POINTER(NISysCfgEnumExpertHandle),
                  ctypes.POINTER(NISysCfgSessionHandle))
    f.restype = NISysCfgStatus
    expertHdl = NISysCfgEnumExpertHandle(0)
    sesnHdl = NISysCfgSessionHandle(0)
    status = f(target, user, password, lang, force_refresh, connect_timeout,
               ctypes.byref(expertHdl), ctypes.byref(sesnHdl))
    return status, expertHdl, sesnHdl

def NISysCfgFindHardware(sesnHandle, 
                         filterMode=NISysCfgFilterMode.MatchValuesAll, 
                         filterHandle=None,
                         expert_names=None):
    f = lib.NISysCfgFindHardware
    f.argtypes = (NISysCfgSessionHandle, ctypes.c_int, ctypes.c_void_p,
                  ctypes.c_char_p, ctypes.POINTER(ctypes.c_void_p))
    f.restype = NISysCfgStatus
    resourceEnumHandle = ctypes.c_void_p(0)
    status = f(sesnHandle, filterMode, filterHandle, expert_names, ctypes.byref(resourceEnumHandle))
    return status, resourceEnumHandle
    
def NISysCfgNextResource(sesnHandle, resourceEnumHandle):
    f = lib.NISysCfgNextResource
    f.argtypes = (NISysCfgSessionHandle, ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p))
    f.restype = NISysCfgStatus
    resourceHandle = ctypes.c_void_p(0)
    status = f(sesnHandle, resourceEnumHandle, ctypes.byref(resourceHandle))
    return status, resourceHandle

def NISysCfgCloseHandle(handle):
    f = lib.NISysCfgCloseHandle
    f.argtypes = (ctypes.c_void_p,)
    f.restype = NISysCfgStatus
    status = f(handle)
    return status
    
def NISysCfgGetResourceProperty(resourceHandle, propertyID):
    attr_ctype, attr_ini, create_func, ref_func, enum_class = NISysCfgResourcePropertyType[propertyID]
    if create_func is None:
        create_func = attr_ctype
    if ref_func == ctypes.byref:
        attr_func = ctypes.POINTER(attr_ctype)
    else:
        attr_func = attr_ctype
    f = lib.NISysCfgGetResourceProperty
    f.argtypes = (ctypes.c_void_p, ctypes.c_int, attr_func)
    f.restype = NISysCfgStatus
    val = create_func(attr_ini)
    status = f(resourceHandle, propertyID, ref_func(val))
    try:
        val = val.value
        val = val.decode('ascii')
    except AttributeError:
        pass
    
    return status, val
    
def NISysCfgGetResourceIndexedProperty(resourceHandle):
    f = lib.NISysCfgGetResourceIndexedProperty
    f.argtypes = (ctypes.c_void_p, ctypes.c_int, ctypes.c_uint, ctypes.c_char_p)
    f.restype = NISysCfgStatus
    
    # implémenté seulement pour IndexedPropertyExpertName
    status, num_experts = NISysCfgGetResourceProperty(resourceHandle, NISysCfgResourceProperty.NumberOfExperts)
    data = list()
    for index in range(num_experts):
        indexed_data = dict()
        for attr in (NISysCfgIndexedProperty.ExpertName,
                     NISysCfgIndexedProperty.ExpertResourceName,
                     NISysCfgIndexedProperty.ExpertUserAlias):
            val = ctypes.create_string_buffer(NISYSCFG_SIMPLE_STRING_LENGTH)
            status = f(resourceHandle, attr, index, val)
            indexed_data[attr] = val.value.decode('ascii')
        data.append(indexed_data)
    return data
            
        
    
def find_resources():
    status, expertHandle, sessionHandle = NISysCfgInitializeSession()
    if status == 0:
        try:
            status, resourceEnumHandle = NISysCfgFindHardware(sessionHandle)
            if status == 0:
                try:
                    while status == 0:
                        status, resourceHandle = NISysCfgNextResource(sessionHandle, resourceEnumHandle)
                        if status == 0 and resourceHandle:
                            try:
                                print(resourceHandle)
                                for attr in (NISysCfgResourceProperty.VendorName,
                                             NISysCfgResourceProperty.ProductName,
                                             NISysCfgResourceProperty.SerialNumber,
                                             NISysCfgResourceProperty.ConnectsToLinkName,
                                             NISysCfgResourceProperty.PxiPciBusNumber,
                                             NISysCfgResourceProperty.PxiPciDeviceNumber,
                                             NISysCfgResourceProperty.PxiPciFunctionNumber,
                                             NISysCfgResourceProperty.GpibPrimaryAddress,
                                             NISysCfgResourceProperty.GpibSecondaryAddress,
                                             NISysCfgResourceProperty.ProvidesBusType,
                                             NISysCfgResourceProperty.ProvidesLinkName):
                                
                                    status, val = NISysCfgGetResourceProperty(resourceHandle, attr)
                                    print(attr, val)
                                data = NISysCfgGetResourceIndexedProperty(resourceHandle)
                                pprint(data)
                            finally:
                                status = NISysCfgCloseHandle(resourceHandle)
                                if status != 0:
                                    print(status)
                        else:
                            break
                finally:
                    status = NISysCfgCloseHandle(resourceEnumHandle)
                    if status != 0:
                        print(status)
            else:
                print(status)
        finally:
            if expertHandle:
                status = NISysCfgCloseHandle(expertHandle)
                if status != 0:
                    print(status)
            if sessionHandle:
                status = NISysCfgCloseHandle(sessionHandle)
                if status != 0:
                    print(status)
    else:
        print(status)
    
if __name__ == '__main__':
    find_resources()