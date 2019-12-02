"""PCO module (:mod:`pymanip.video.pco`)
========================================

This module is a shortcut for the :class:`pymanip.video.pco.camera.PCO_Camera`
class. It also defines utility functions for PCO camera.

.. autofunction:: PCO_read_binary_file

.. autofunction:: print_available_pco_cameras

"""

import numpy as np
from .camera import PCO_Camera
from . import pixelfly as pf


def PCO_read_binary_file(f):
    """This functions reads PCO binary image file.
    """
    return np.fromfile(f, dtype="<i2").reshape((1200, 1600))


def print_available_pco_cameras():
    """This functions queries the Pixelfly library for available cameras,
    and prints the result.
    """
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
