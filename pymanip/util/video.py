"""

Utility function for cameras and videos

"""

try:
    from pymanip.video.pco import PCO_Camera
    has_pco = True
except ModuleNotFoundError:
    has_pco = False

def preview_pco(board=0, backend='cv', slice=None, zoom=0.5, TriggerMode=None):
    if not has_pco:
        print('PCO bindings are not available.')
    else:
        with PCO_Camera(board) as cam:
            if TriggerMode:
                cam.set_trigger_mode(TriggerMode)
            else:
                cam.set_trigger_mode('auto sequence')
            cam.preview(backend, slice, zoom)