"""

Python wrapper for the NI System Configuration library

"""

from pprint import pprint
from ._lib.constants import *
from .resource import NISysCfgHardwareEnumerator, NISysCfgResourceAttributeError

preferred_experts = ["daqmx", "scope", "ni-visa", "ni-488.2"]


def find_resources():
    for res in NISysCfgHardwareEnumerator():
        try:
            attrs = [
                "VendorName",
                "ProductName",
                "SerialNumber",
                "ConnectsToLinkName",
                "PxiPciBusNumber",
                "PxiPciDeviceNumber",
                "PxiPciFunctionNumber",
                "GpibPrimaryAddress",
                "GpibSecondaryAddress",
                "ProvidesBusType",
                "ProvidesLinkName",
            ]
            infos = dict()
            for attr in attrs:
                try:
                    val = getattr(res, attr)
                    infos[attr] = val
                except NISysCfgResourceAttributeError as e:
                    if e.status != NISysCfgStatus.PropDoesNotExist:  # noqa: F405
                        raise
            expert_infos = res.indexed_properties()
            found = False
            for preferred in preferred_experts:
                for e in expert_infos:
                    if e["ExpertName"] == preferred:
                        infos[preferred] = e
                        found = True
                        break
                if found:
                    break

        finally:
            res.close()
        yield infos


def print_resources():
    for infos in find_resources():
        try:
            titre = infos["VendorName"] + " " + infos["ProductName"]
        except KeyError:
            continue
        print(titre)
        print("-" * len(titre))
        pprint(infos)


def daqmx_devices():
    return [
        info["daqmx"]["ExpertUserAlias"] for info in find_resources() if "daqmx" in info
    ]


def scope_devices():
    return [
        info["scope"]["ExpertUserAlias"] for info in find_resources() if "scope" in info
    ]
