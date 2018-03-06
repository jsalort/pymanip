"""

Utility function for cameras and videos

"""

try:
    from pymanip.video.pco import PCO_Camera
    has_pco = True
except ModuleNotFoundError:
    has_pco = False
try:
    from pymanip.video.avt import AVT_Camera
    has_avt = True
except ModuleNotFoundError:
    has_avt = False
from contextlib import ExitStack
import asyncio

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

def preview_avt(board=0, backend='cv', slice=None, zoom=0.5, TriggerMode=None):
    if not has_avt:
        print('Pymba is not available.')
    else:
        print("Press 's' to close window")
        if isinstance(board, list):
            with ExitStack() as stack:
                cams = [stack.enter_context(AVT_Camera(b)) for b in board]
                loop = asyncio.get_event_loop()
                loop.run_until_complete(asyncio.gather(*[c.preview_async_cv(slice, zoom, 
                                                                            name="AVT " + str(c.num))
                                                         for c in cams]))
                loop.close()
        else:
            with AVT_Camera(board) as cam:
                cam.preview(backend, slice, zoom)