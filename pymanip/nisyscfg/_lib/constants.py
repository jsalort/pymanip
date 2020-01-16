"""

NI System Configuration constants

"""

from enum import IntEnum

__all__ = [
    "NISYSCFG_SIMPLE_STRING_LENGTH",
    "NISysCfgLocale",
    "NISysCfgFilterMode",
    "NISysCfgResourceProperty",
    "NISysCfgIndexedProperty",
    "NISysCfgStatus",
]

NISYSCFG_SIMPLE_STRING_LENGTH = 1024


class NISysCfgLocale(IntEnum):
    Default = (0,)
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


class NISysCfgStatus(IntEnum):
    # Common success codes
    OK = 0  # The operation succeeded.
    EndOfEnum = (
        1  # Reached end of the enumeration. Used by the NISysCfgNext* functions.
    )
    SelfTestBasicOnly = (
        0x00040370
    )  # The expert performed a basic self-test because it does not implement the specified mode.
    FoundCachedOfflineSystem = (
        0x00040400
    )  # Initialization succeeded but the target is offline. Only cached system properties are available.
    RestartLocalhostInitiated = (
        0x00040401
    )  # For the local system, the option to wait until the restart is complete is ignored. The function has successfully initiated a restart with the operating system.

    # Common error codes
    NotImplemented = (
        0x80004001  # This operation is not implemented for this target or resource.
    )
    NullPointer = 0x80004003  # A required pointer parameter was NULL.
    Fail = 0x80004005  # Miscellaneous operation failure.
    Unexpected = (
        0x8000FFFF
    )  # A critical unexpected error occurred. Please report this to National Instruments.
    OutOfMemory = 0x8007000E  # Out of memory.
    InvalidArg = 0x80070057  # Some parameter is invalid.
    OperationTimedOut = 0x80040420  # The operation timed out.
    FileNotFound = 0x8004049E  # The specified file was not found.
    InvalidMACFormat = (
        0x800404CA
    )  # Unsupported MAC address format. Supply the MAC address as a colon separated string of characters instead of Hex display.

    # 'Hardware' and 'Resource' functions
    PropMismatch = (
        0x80040370  # The property already exists with a different type or value.
    )
    PropDoesNotExist = 0x80040371  # The property does not exist for this resource.
    UriIllegalSyntax = (
        0x80040372
    )  # The name of the target or expert contains illegal characters or has an invalid format. Each label of the hostname must be between 1 and 63 characters long, and the entire hostname, including delimiting dots, must be 255 characters or less.
    UriTargetDoesNotExist = (
        0x80040373
    )  # Could not contact the NI System Configuration API at the specified target address. Ensure that the system is online.
    UriExpertDoesNotExist = 0x80040374  # A specified expert is not installed.
    ItemDoesNotExist = 0x80040375  # The specified resource name does not exist.
    InvalidMode = 0x80040376  # The specified mode is invalid.
    SysConfigAPINotInstalled = (
        0x80040378
    )  # The NI System Configuration API is not installed on the specified target.
    NameSyntaxIllegal = 0x8004037A  # The suggested name contains illegal characters.
    NameCollision = 0x8004037B  # Another resource already has the suggested name.
    NoPropValidated = 0x8004037C  # None of the changed properties could be validated.
    UriUnauthorized = (
        0x8004037D
    )  # The current user does not have permission for the requested operation.
    RenameResourceDependencies = (
        0x8004037E
    )  # The resource being renamed has dependencies, and the 'updateDependencies' flag was false.
    ValueInvalid = (
        0x8004037F  # A property contained a value that is not valid or is out of range.
    )
    ValuesInconsistent = (
        0x80040380
    )  # Multiple properties contained values that are inconsistent with each other.
    Canceled = 0x80040381  # The operation was canceled.
    ResponseSyntax = (
        0x80040382
    )  # Could not parse the response from the NI System Configuration API at the specified target address.
    ResourceIsNotPresent = (
        0x80040383
    )  # The resource name is valid but the operation requires the resource to be present.
    ResourceIsSimulated = (
        0x80040384
    )  # The resource name is valid but the operation is not supported on simulated resources.
    NotInFirmwareUpdateState = (
        0x80040385
    )  # The resource requires being in the firmware update state to perform this operation.
    FirmwareImageDeviceMismatch = (
        0x80040386  # The uploaded firmware image does not work with this resource.
    )
    FirmwareImageCorrupt = (
        0x80040387  # The uploaded firmware image is corrupt or incomplete.
    )
    InvalidFirmwareVersion = (
        0x80040388  # The specified firmware version does not exist.
    )
    OlderFirmwareVersion = (
        0x80040389
    )  # The specified firmware version is older than what is currently installed.
    InvalidLoginCredentials = 0x8004038A  # The username or password is incorrect.
    FirmwareUpdateAttemptFailed = (
        0x8004038B
    )  # The specified firmware was not successfully installed. See the output parameters for more information.
    EncryptionFailed = 0x8004038C  # The data could not be encrypted.
    SomePropsNotValidated = (
        0x8004038D
    )  # The changes were not saved. Some of the modified properties were not validated because they do not apply to this item.
    InvalidCalibrationCredentials = 0x8004038E  # The calibration password is incorrect.
    CannotDeletePresentResource = (
        0x8004038F  # Could not delete the specified resource because it is present.
    )
    UriTargetTransmitError = (
        0x80040390
    )  # Failed transmitting data to or from the web server at the specified target address.
    DecryptionFailed = (
        0x80040391
    )  # The NI System Configuration API at the specified target address could not decrypt the data.
    FirmwareExpertVersionMismatch = (
        0x80040392
    )  # The specified firmware requires a newer version of the expert than what is currently installed.
    AmbiguousImportAction = (
        0x80040393
    )  # There was uncertainty regarding what action to take during an import.
    RequiredItemFailedImport = 0x80040394  # A required item could not be imported.

    # 'Report' functions
    PermissionDenied = (
        0x800403B0  # Unable to write to file or folder. Permission denied.
    )
    SystemNotFound = (
        0x800403B1
    )  # Unable to connect to the specified system. Ensure that the system is online.
    TransformFailed = 0x800403B2  # Error running transform to generate report.
    NotInstalled = 0x800403B3  # Unable to find MAX on the system. Please reinstall.
    LaunchFailure = 0x800403B4  # Unexpected error launching nimax.exe.
    InternalTimeout = (
        0x800403B5  # Launched nimax.exe but it did not complete in a reasonable time.
    )
    MissingTransform = (
        0x800403B6  # Unable to find an XSL transform to generate the report.
    )
    IncorrectExtension = 0x800403B7  # Incorrect report file extension provided.
    FileReadOnly = 0x800403B8  # Report file is read-only. Unable to generate report.
    ReportOverwrite = (
        0x800403B9
    )  # Report file exists and the NIMAX_FailIfOverwritingReport flag was set.
    DirectoryError = 0x800403BA  # Error creating directory for report files.

    # 'Export' and 'Import' functions
    CannotOpenFile = 0x80040400  # Error opening a file.
    InsufficientPermissions = (
        0x80040401  # The object cannot be accessed because of insufficient permissions.
    )
    NCECopierFailed = 0x80040402  # Error with the object copier.
    FileOperationFailed = 0x80040403  # Error performing a file operation.
    NameCollisionError = (
        0x80040404  # Names from one expert have collided with another expert.
    )
    UnexpectedError = 0x80040405  # Unexpected error has occurred.
    NCENoStreamError = (
        0x80040406
    )  # The expert requested its stream for import but one does not exist because it did not export a stream.
    NCECompressionError = 0x80040407  # Error compressing or decompressing file.
    NCEStreamReadError = 0x80040408  # Error reading from a stream.
    NCEStreamWriteError = 0x80040409  # Error writing to a stream.
    NCEStreamSeekError = 0x8004040A  # Error seeking to a position in a stream.
    NCERepoNotReady = 0x8004040B  # Repository not ready to be exported.
    NCERepoInvalid = (
        0x8004040C
    )  # The file or stream from which to import the repository is not a valid repository.
    NCERepoIncompat = (
        0x8004040D
    )  # The repository was exported with a newer version of MAX than what is on the importing machine.
    NCENoImportStorage = 0x8004040E  # The import storage could not be opened.
    NCENoExportStorage = 0x8004040F  # The export storage could not be created.
    NCENoObjCopier = 0x80040410  # The object copier could not be created.
    CopyInProgress = 0x80040411  # A PortCfg operation is already in progress.
    FileNotRecognized = 0x80040412  # The custom file does not belong to a given expert.
    SystemNotSupported = (
        0x80040413  # A specified system is not supported by this expert.
    )
    SystemNotReachable = (
        0x80040414
    )  # A specified system is presumably supported, but network errors prevent connection.
    ProductSoftwareNotInstalled = (
        0x80040415  # The product is not installed on the specified system.
    )
    ProductSoftwareTooOld = (
        0x80040416  # The product is installed on the remote system, but is too old.
    )
    ProductSoftwareTooNew = (
        0x80040417  # The product is installed on the remote system, but is too new.
    )
    DataTooOld = (
        0x80040418
    )  # The import data is too old. The product is not backward-compatible with this data.
    DataTooNew = (
        0x80040419
    )  # The import data is too new. The product is not forward-compatible with this data.
    NoItemsToCopy = (
        0x8004041A  # The operation failed because no source items were specified.
    )
    OrphanItems = 0x8004041B  # The operation failed because some items were orphans.
    DirtyItems = (
        0x8004041C
    )  # The operation failed because some items were in-edit and not saved.
    FileOverwrite = (
        0x8004041D  # The operation failed because it would overwrite a file.
    )
    ItemOverwrite = 0x8004041E  # The operation failed because it would overwrite items.
    MissingDependency = (
        0x8004041F  # The operation failed because of missing dependency items.
    )
    OperationCanceled = 0x80040421  # The operation was canceled by the client.
    WarningConflicts = 0x80040422  # The operation failed because of warning conflicts.
    ErrorConflicts = 0x80040423  # The operation failed because of general conflicts.
    ItemsRequireUserInput = (
        0x80040424
    )  # The operation failed because of unresolved conflicts requiring user input.
    ProductExpertNotReady = (
        0x80040425
    )  # An expert is not ready to accept the specified source or destination, but may become ready in the future.
    OrphanFiles = 0x80040426  # The operation failed because some files were orphans.
    IsConst = (
        0x80040427
    )  # Caller called a non-const method on an object that is logically const.
    UnsupportedProductMode = (
        0x80040428
    )  # An expert does not support the attempted copy mode (e.g. merge to file, etc.).

    # 'System' functions
    RestartLocalhostAmbiguous = (
        0x8004046C
    )  # To reboot your system, either specify 'localhost' on the front panel for Session in, or call Initialize Session first.
    ImageInvalidCorrupt = (
        0x8004046D  # The image is corrupt or the file type is invalid.
    )
    SafeOrInstallModeRequired = (
        0x8004046E
    )  # Can only perform this action in safe or install mode, and the 'auto restart' flag was false.
    EncryptPhraseMismatch = (
        0x8004046F
    )  # The encryption passphrase when applying an image was not the same as when the image was created.
    InvalidIP = 0x80040470  # IP Address is invalid.
    InvalidGateway = 0x80040471  # Gateway is invalid.
    InvalidDNS = 0x80040472  # DNS is invalid.
    InvalidSubnet = 0x80040473  # Subnet is invalid.
    CmdNotSupported = 0x80040474  # Command is not supported by given protocol.
    ConfigFailed = (
        0x80040475  # Remote system replied with the failure to config command.
    )
    Locked = 0x80040476  # Remote system is locked. Requires a password to configure.
    BadPassword = 0x80040477  # The password supplied for the operation is invalid.
    NotConfigurable = (
        0x80040478
    )  # The remote device is not configurable for some reason other than password.
    UnlockFailed = 0x80040479  # Failed to unlock the system.
    LockFailed = 0x8004047A  # Failed to lock the system.
    InstallFailed = 0x8004047B  # General installation failure.
    InstallationCorrupt = (
        0x8004047C
    )  # Installation component files were not found in the repository, or were corrupt.
    EmptyFile = 0x8004047D  # The installation file is empty.
    UnconfiguredIP = (
        0x8004047E
    )  # The system must have a valid IP before certain operations such as installation. Cannot be 0.0.0.0.
    InstallationGenericFailure = 0x80040480  # General install error.
    DownloadAlreadyStarted = (
        0x80040482
    )  # Installation to the specified target has already started. Multiple simultaneous installations are not allowed.
    Aborted = 0x80040483  # Remote action aborted.
    DiskFull = (
        0x8004048E
    )  # Hard Drive on the remote system is either full or has encountered an I/O error.
    HDFormatFailed = 0x8004048F  # Hard Drive Format failed.
    HDFormatNotSafeMode = (
        0x80040490  # System must be in safe mode before attempting Hard Drive Format.
    )
    HDFormatRebootFailed = (
        0x80040491
    )  # System failed to reboot after Hard Drive format. System is in unknown state.
    ConnectionRefused = 0x80040492  # The server refused the network connection.
    GetRemoteFilesFailed = (
        0x80040495  # Failed to get one or more files while creating system image.
    )
    PutRemoteFilesFailed = (
        0x80040496  # Failed to put one or more files while applying system image.
    )
    InvalidImage = 0x80040497  # The specified path does not point to a valid image.
    ImageDeviceCodeMismatch = (
        0x80040498
    )  # The image is for a different device class and is incompatible with the target.
    SystemMismatch = (
        0x80040499  # The image was not originally created from the specified target.
    )
    HDFormatWrongFS = (
        0x8004049A
    )  # The requested file system is not supported on the specified target.
    CustomInstallNotSupported = (
        0x8004049B
    )  # The specified target does not support custom software installations.
    FTPFailed = 0x8004049C  # A file transfer error (FTP or WebDAV) occurred.
    Timeout = 0x8004049D  # Operation timed out.
    DirNotFound = 0x8004049F  # The specified directory was not found.
    PathNotFound = 0x800404A0  # The specified file or directory path was not found.
    NoSoftwareAvailable = 0x800404A1  # No software is available for install.
    OverwriteError = (
        0x800404A2  # The file or directory exists and the overwrite flag was false.
    )
    HDFormatCannotKeepCfg = (
        0x800404A3
    )  # The target was not formatted because the option to keep configuration after a format is supported only for targets on the local subnet. To format the target, repeat the operation without requesting to keep the configuration.
    FileOrPathTooLong = (
        0x800404A4  # Filename or pathname is longer than what the server supports.
    )
    DDPInternalTimeout = (
        0x800404A5
    )  # Failed when communicating with the system. This issue is usually caused by a high latency in the network. Refer to KnowledgeBase article 42GH3O00 on ni.com for possible solutions.
    IOPermissionDenied = (
        0x800404A6  # The operation failed because of insufficient permissions.
    )
    PathAlreadyExists = (
        0x800404A7  # The operation failed because the path already exists.
    )
    ExecutionFailure = (
        0x800404A8
    )  # The execution of an external command, script, or application failed.
    DownloadError = (
        0x800404A9  # Failed to download the file from the 'RT Images' repository.
    )
    NetSendFailed = 0x800404AB  # Failed to send command.
    ContactHostDisconnected = (
        0x800404AC  # Could not contact remote target. Ensure that the system is online.
    )
    NetSvcDown = 0x800404AD  # Could not access network.
    NotConfirmed = (
        0x800404AE
    )  # Command was not confirmed. The result of the operation is uncertain.
    HostNotResolved = 0x800404AF  # Hostname could not be resolved by DNS.
    RebootTimeout = 0x800404B0  # Timeout while waiting for reboot. System is offline.
    NoConfirmationFP1600 = (
        0x800404B1
    )  # Sending new configuration operation returned a failure, but might not necessarily have failed.
    DuplicateStartup = 0x800404B4  # Cannot install more than one startup component.
    RemoteInvalidArgument = 0x800404B5  # Invalid argument passed.
    NotUninstallable = (
        0x800404B6  # Cannot uninstall a component. There are dependencies.
    )
    DuplicatesNotAllowed = (
        0x800404B7  # Cannot install multiple packages of the same component.
    )
    NotInstallable = 0x800404B8  # Cannot install a component. There are dependencies.
    WrongDevice = 0x800404B9  # Component will not work on this target.
    WrongOS = 0x800404BA  # Component will not work on this operating system.
    OSVersionTooOld = 0x800404BB  # A BIOS update is required before installing.
    IOError = 0x800404BC  # Cannot open file or folder.
    CorruptConfig = (
        0x800404BD  # Duplicate or missing components on target installation.
    )
    BufferOverflow = 0x800404BE  # Buffer overflow. Size is too small.
    UnsupportedCDFVersion = (
        0x800404BF
    )  # Unsupported version of CDF format. Needs a newer version of MAX or NI System Configuration.
    InvalidStack = 0x800404C0  # Invalid software set.
    IncompleteStack = (
        0x800404C1
    )  # Incompletely specified list of packages. Some hidden dependencies were added.
    StackItemMissing = (
        0x800404C2
    )  # One or more Software Set items could not be found in the repository.
    TopLevelHiddenComponentError = (
        0x800404C3  # There is a top-level hidden component installed.
    )
    InvalidAddon = (
        0x800404C4
    )  # A component was passed in that is not an installable add-on. It may be an unknown ID, a defined item that is not an add-on, a missing add-on, or a non-installable add-on.
    NoRTImagesFolder = (
        0x800404C5  # Could not find or access 'RT Images' repository location.
    )
    NoRTImagesRegistry = 0x800404C6  # Could not read the 'RT Images' registry key.
    NoRTS2CDF = 0x800404C7  # Could not find the rts2cdf conversion utility.
    UnsupportedOS = 0x800404C8  # The operating system is not supported.
    ExactVersionRequired = (
        0x800404C9
    )  # Unspecified version while trying to install exact version of a component.
    InvalidStartup = 0x800404CB  # A component was passed in that is not a startup.
