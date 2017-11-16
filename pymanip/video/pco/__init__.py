"""

Module for PCO camera

"""

import numpy as np
from .camera import PCO_Camera

def PCO_read_binary_file(f):
    return np.fromfile(f, dtype='<i2').reshape( (1200, 1600) )
