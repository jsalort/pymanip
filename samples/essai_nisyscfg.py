from pprint import pprint

from pymanip.nisyscfg import print_resources, daqmx_devices, scope_devices

if __name__ == "__main__":
    print("All resources:")
    print_resources()

    print("DAQmx devices:", daqmx_devices())
    print("Scope devices:", scope_devices())
