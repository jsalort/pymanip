"""

This is the definition of a higher level PCO_Camera object
based on the low-level pco.pixelfly module.

"""

import sys
import numpy as np
import pymanip.pco.pixelfly as pf
import matplotlib.pyplot as plt

class PCO_Camera:

	# Open/Close camera
	def __init__(self, board=0):
		"""
		pco.sdk_manual page 10:
		First step is to PCO_OpenCamera
		As next step camera description and status should be queried
		by calling PCO_GetCameraDescription and PCO_GetCameraHealthStatus
		"""
		
		self.handle = pf.PCO_OpenCamera(board)
		self.camera_description = pf.PCO_GetCameraDescription(self.handle)
		warn, err, status = self.health_status()
		if warn or err:
			print('Warning bits :', warn)
			print('Error bits :', err)
		else:
			print('Connected to camera on board', board)
			#print(str(self.camera_description))
			print('Status bits :', status)
		pf.PCO_SetBitAlignment(self.handle, sys.byteorder == 'little')
	
	def close(self):
		pf.PCO_CloseCamera(self.handle)
		self.handle = None
		print('Connection to camera closed.')
	
	def __enter__(self):
		return self
		
	def __exit__(self, type_, value, cb):
		self.close()
	
	# Query states
	def health_status(self):
		warn, err, status = pf.PCO_GetCameraHealthStatus(self.handle)
		return warn, err, status
	
	# Image acquisition
	def grab_image(self):
		"""
		Simple one shot image grabbing
		"""
		# Arm camera
		pf.PCO_ArmCamera(self.handle)
		XResAct, YResAct, XResMax, YResMax = pf.PCO_GetSizes(self.handle)
		
		# Allocate buffer
		bufSizeInBytes = XResAct*YResAct*pf.ctypes.sizeof(pf.ctypes.wintypes.WORD)
		bufPtr = pf.ctypes.POINTER(pf.ctypes.wintypes.WORD)()
		bufNr, event = pf.PCO_AllocateBuffer(self.handle, -1, bufSizeInBytes, bufPtr)
		
		# Get Image
		try:
			pf.PCO_SetImageParameters(self.handle, XResAct, YResAct,
									  pf.IMAGEPARAMETERS_READ_WHILE_RECORDING)
			pf.PCO_SetRecordingState(self.handle, True)
			pf.PCO_GetImageEx(self.handle, 1, 0, 0, bufNr, XResAct, YResAct, 16)
			array = np.ctypeslib.as_array(bufPtr, shape=(YResAct, XResAct)).copy()
		finally:
			pf.PCO_SetRecordingState(self.handle, False)
			pf.PCO_CancelImages(self.handle)
			pf.PCO_FreeBuffer(self.handle, bufNr)
		return array

if __name__ == '__main__':
	import matplotlib.pyplot as plt
	with PCO_Camera() as cam:
		array = cam.grab_image()
	plt.imshow(array, origin='lower')
	plt.colorbar()
	plt.show()