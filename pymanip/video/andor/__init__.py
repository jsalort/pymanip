"""

Support for Andor cameras
- camera submodule implements the pymanip.video.Camera object using pyAndorNeo module
- reader submodule implements reading of DAT and SIF files in pure python

"""

from .camera import Andor_Camera
