"""

Module for PCO camera

"""

import numpy as np

def PCO_read_binary_file(f):
    return np.fromfile(f, dtype='<i2').reshape( (1200, 1600) )