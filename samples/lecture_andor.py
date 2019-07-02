import cv2
import numpy as np
import matplotlib.pyplot as plt

img = cv2.imread("img-0000.png", -1)
plt.figure(1)
plt.imshow(img.T, cmap="gray")
plt.colorbar()

img = cv2.imread("toto/img_-0001.png", -1)
plt.figure(2)
plt.imshow(img.T, cmap="gray")
plt.colorbar()

plt.show()
