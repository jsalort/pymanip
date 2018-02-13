"""

Andor Camera DAT image file reader


"""

import os
import io
import configparser
import glob

import numpy as np

class AndorAcquisitionReader:

    def __init__(self, acquisition_folder):
        config = configparser.ConfigParser()
        with io.open(os.path.join(acquisition_folder, 'acquisitionmetadata.ini'), 'r', 
                     encoding='utf-8-sig') as f:
            config.read_file(f)
            self.metadata = {'AOIWidth': int(config['data']['aoiwidth']),
                             'AOIHeight': int(config['data']['aoiheight']),
                             'AOIStride': int(config['data']['aoistride']),
                             'PixelEncoding': str(config['data']['pixelencoding']),
                             'ImageSizeBytes': int(config['data']['imagesizebytes']),
                             'ImagesPerFile': int(config['multiimage']['imagesperfile'])}

            self.dt = np.uint16 if self.metadata['PixelEncoding'] == 'Mono16' else None
            if not self.dt:
                raise ValueError('Unsupported pixel encoding')

            self.file_list = glob.glob(os.path.join(acquisition_folder, '*spool.dat'))
            self.file_list.sort()

    def images(self):
        for i in range(len(self)):
            yield self[i]
            

    def __getitem__(self, key):
        bname = os.path.basename(self.file_list[key])
        n = bname.find('spool')
        timestamp = int(bname[:n])/1e6
        with open(self.file_list[key], 'rb') as f:
            header = f.read(40)
            data = np.fromfile(f,dtype=self.dt).reshape((self.metadata['AOIHeight'],self.metadata['AOIWidth']))
        return timestamp, data[::-1,:]

    def __len__(self):
        return len(self.file_list)



