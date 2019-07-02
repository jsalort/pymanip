import time
import cv2
import os
import h5py

from pymanip.video.andor import Andor_Camera


# Exemple avec one-shot
# if True:
# with Andor_Camera() as cam:
# for n in range(5):
# img = cam.acquisition_oneshot()
# print(img.metadata['timestamp'])
# cv2.imwrite(f'img-{n:04d}.png', img)
# print('Saved', n+1)
# time.sleep(10.0)
exposure_time_chosen = 4.0
frame_rate_chosen = 0.1
nb_images_chosen = 2
name_folder_chosen = "plusplusplustard"
bitdepth_chosen = "Mono16"
SimplePreAmpGainControl_chosen = "16-bit (low noise & high well capacity)"
try:
    os.mkdir(name_folder_chosen)
except Exception:
    pass

with Andor_Camera() as cam:
    cam.ExposureTime.setValue(exposure_time_chosen)  # 10e-3)
    cam.FrameRate.setValue(frame_rate_chosen)
    cam.PixelEncoding.setString(bitdepth_chosen)
    cam.SimplePreAmpGainControl.setString(SimplePreAmpGainControl_chosen)
    count, ts = cam.acquire_to_files(
        nb_images_chosen,
        name_folder_chosen + "/img",
        zerofill=4,
        dryrun=False,
        file_format="png",
        compression_level=9,
        delay_save=True,
        progressbar=True,
    )

# ecrire enregistrer les temps en hdf5 et parametres image
with h5py.File(name_folder_chosen + "timestamps_and_parameters.hdf5", "w") as f:
    f.create_dataset("ts", data=ts)
    f.attrs["exposure_time"] = exposure_time_chosen
    f.attrs["frame_rate"] = frame_rate_chosen
    f.attrs["bitdepth"] = bitdepth_chosen
    f.attrs["SimplePreAmpGainControl"] = SimplePreAmpGainControl_chosen


import matplotlib.pyplot as plt

plt.plot(count, ts, "o")
plt.show()


img = cv2.imread(name_folder_chosen + "/img" + "-0001.png", -1)
plt.figure(1)
plt.imshow(img.T, cmap="gray")
plt.colorbar()
plt.clim([0, 10000])

img = cv2.imread(name_folder_chosen + "/img" + "-0002.png", -1)
plt.figure(2)
plt.imshow(img.T, cmap="gray")
plt.colorbar()

plt.show()


with h5py.File(name_folder_chosen + "timestamps_and_parameters.hdf5", "r") as f:
    timestamps = f["ts"].value
    exposure_time = f.attrs["exposure_time"]
    print(timestamps)
    fhz = f.attrs["frame_rate"]
    print(fhz)
