"""

Module for PCO camera

"""

import numpy as np
from .camera import PCO_Camera
from . import pixelfly as pf


def PCO_read_binary_file(f):
    return np.fromfile(f, dtype="<i2").reshape((1200, 1600))


def print_available_pco_cameras():
    cams = list()
    while True:
        try:
            h = pf.PCO_OpenCamera()
        except pf.PCO_Error:
            break
        if h == 0:
            break
        print(pf.PCO_GetInfoString(h))
        cams.append(h)
    for h in cams:
        pf.PCO_CloseCamera(h)
