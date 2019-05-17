import platform

__all__ = list()

if platform.system() == "Linux":
    try:
        from fluidlab.interfaces.gpib_inter import GPIBInterface

        __all__.append("GPIBInterface")
    except ImportError:
        print("Warning: Linux-GPIB Python bindings not found")
        pass
    try:
        from fluidlab.interfaces.usbtmc_inter import USBTMCInterface

        __all__.append("USBTMCInterface")
    except ImportError:
        print("Warning: Linux USBTMC bindings not found.")
        pass

try:
    from fluidlab.interfaces.visa_inter import VISAInterface

    __all__.append("VISAInterface")
except ImportError:
    print("Warning: PyVISA not found")
    pass

try:
    from fluidlab.interfaces.serial_inter import SerialInterface

    __all__.append("SerialInterface")
except ImportError:
    print("Warning: SerialInterface not found")
    pass
