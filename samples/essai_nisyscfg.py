from pprint import pprint

from pymanip.nisyscfg.session import NISysCfgSession
from pymanip.nisyscfg.resource import NISysCfgHardwareEnumerator

from pymanip.nisyscfg._lib.session import NISysCfgInitializeSession, NISysCfgFindHardware, NISysCfgNextResource, NISysCfgCloseHandle
from pymanip.nisyscfg._lib.properties import NISysCfgGetResourceProperty, NISysCfgGetResourceIndexedProperty
from pymanip.nisyscfg._lib.constants import NISysCfgResourceProperty
    
def find_resources():
    for res in NISysCfgHardwareEnumerator():
        try:
            resourceHandle = res.resourceHandle
            print(resourceHandle)
            for attr in ('VendorName',
                         'ProductName',
                         'SerialNumber',
                         'ConnectsToLinkName',
                         'PxiPciBusNumber',
                         'PxiPciDeviceNumber',
                         'PxiPciFunctionNumber',
                         'GpibPrimaryAddress',
                         'GpibSecondaryAddress',
                         'ProvidesBusType',
                         'ProvidesLinkName'):
                try:
                    val = getattr(res, attr)
                    print(attr, val)
                except AttributeError as e:
                    print(e)
            data = NISysCfgGetResourceIndexedProperty(resourceHandle)
            pprint(data)
        finally:
            res.close()
            
if __name__ == '__main__':
    find_resources()