import time
import cv2
import os
from pymanip.video.andor import Andor_Camera

# Exemple avec one-shot
if False:
    with Andor_Camera() as cam:
        for n in range(5):
            img = cam.acquisition_oneshot()
            print(img.metadata['timestamp'])
            cv2.imwrite(f'img-{n:04d}.png', img)
            print('Saved', n+1)
            time.sleep(10.0)

try:
    os.mkdir('toto')
except Exception:
    pass
    
with Andor_Camera() as cam:
    cam.ExposureTime.setValue(10e-3)
    cam.FrameRate.setValue(20.0)
    cam.PixelEncoding.setString('Mono16')
    cam.SimplePreAmpGainControl.setString('16-bit (low noise & high well capacity)')
    count, ts = cam.acquire_to_files(10, 'toto/img_', zerofill=4,
                                     dryrun=False, file_format='png',
                                     compression_level=9,
                                     delay_save=True,
                                     progressbar=True)

import matplotlib.pyplot as plt

plt.plot(count, ts, 'o')
plt.show()