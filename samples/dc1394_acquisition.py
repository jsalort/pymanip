from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np

import pydc1394.camera2 as dc
import png

from pymanip import Session
from pymanip.instruments import HP33120a
from pymanip.interfaces import GPIBInterface

# Paramètres de l'acquisition
destination_dir = Path("/home/manip/Documents/Acquisitions")
acquisition_name = "essai_2"
images_dir = destination_dir / acquisition_name

if not destination_dir.exists():
    destination_dir.mkdir()
if not destination_dir.is_dir():
    raise NotADirectoryError
if not images_dir.exists():
    images_dir.mkdir()
if not images_dir.is_dir():
    raise NotADirectoryError

MI = Session(images_dir, ("timestamp",))

# Réglage fréquence trigger
gbf = HP33120a(GPIBInterface(0, 10))
gbf.freq.set(2.0)

# Ouverture de la caméra
cam = dc.Camera(iso_speed=800, mode="FORMAT7_0")
print(cam.vendor.decode("ascii"), cam.model.decode("ascii"))
cam.mode.color_coding = "Y16"
cam.trigger.active = True  # External trigger
print("bandwidth_usage =", cam.bandwidth_usage)
print("iso speed =", cam.iso_speed, flush=True)

# cam.mode = cam.modes[0]

# Acquisition
cam.start_capture()
cam.start_video()
images = []

for i in range(10):
    frame = cam.dequeue()  # This object references the actual frame in the
    # DMA buffer. It must be quickly enqueued
    data = frame.copy()
    timestamp = frame.timestamp / 1e6
    img = png.from_array(data, mode="L")
    # with open(images_dir / 'img-{:03d}.png'.format(i), 'wb') as f:
    #    img.save(f)
    images.append(img)
    MI.log_addline()
    frame.enqueue()

cam.stop_video()
cam.stop_capture()

# Enregistrement des images a posteriori
print("Saving pictures...", flush=True)
for i, img in enumerate(images):
    with open(images_dir / "img-{:03d}.png".format(i), "wb") as f:
        img.save(f)

# Graphe des timestamps
t = MI["timestamp"]
MI.Stop()
real_fs = 1 / np.mean(t[1:] - t[:-1])
print("Real fs =", real_fs, "Hz")

plt.figure()
plt.plot(t - t[0], "bo")
plt.show()
MI.Stop()
