"""

Utility function for cameras and videos

"""

try:
    from pymanip.video.pco import PCO_Camera

    has_pco = True
except Exception:
    has_pco = False
try:
    from pymanip.video.avt import AVT_Camera

    has_avt = True
except Exception:
    has_avt = False
try:
    from pymanip.video.andor import Andor_Camera

    has_andor = True
except Exception:
    has_andor = False

try:
    from pymanip.video.ids import IDS_Camera

    has_ids = True
except Exception:
    has_ids = False

try:
    from pymanip.video.ximea import Ximea_Camera

    has_ximea = True
except Exception:
    has_ximea = False

try:
    from pymanip.video.photometrics import Photometrics_Camera

    has_photometrics = True
except Exception as e:
    has_photometrics = False
    photometrics_exc = e

from contextlib import ExitStack
import asyncio


def preview_pco(
    interface="all",
    board=0,
    backend="cv",
    slice=None,
    zoom=0.5,
    TriggerMode=None,
    exposure_ms=20,
    rotate=0,
    roi=None,
):
    if not has_pco:
        print("PCO bindings are not available.")
    else:
        with PCO_Camera(interface, board) as cam:
            if TriggerMode:
                cam.set_trigger_mode(TriggerMode)
            else:
                cam.set_trigger_mode("auto sequence")
            cam.set_delay_exposuretime(exposuretime=exposure_ms / 1000)
            if roi is None:
                res = cam.resolution
                roi = (1, 1, res[0], res[1])
            cam.set_roi(*roi)
            cam.preview(backend, slice, zoom, rotate)


def preview_avt(
    board=0,
    backend="cv",
    slice=None,
    zoom=0.5,
    TriggerMode=None,
    exposure_ms=10,
    rotate=0,
    roi=None,
):
    if not has_avt:
        print("Pymba is not available.")
    else:
        if backend == "cv":
            print("Press 's' to close window")
        if isinstance(board, list) and len(board) == 1:
            board = board[0]
        if isinstance(board, list):
            with ExitStack() as stack:
                cams = [stack.enter_context(AVT_Camera(b)) for b in board]
                if TriggerMode:
                    print("External trigger")
                    for c in cams:
                        c.set_trigger_mode(True)
                else:
                    print("Internal trigger")
                    for c in cams:
                        c.set_trigger_mode(False)
                if roi:
                    for c in cams:
                        c.set_roi(*roi)
                loop = asyncio.get_event_loop()
                loop.run_until_complete(
                    asyncio.gather(
                        *[
                            c.preview_async_cv(
                                slice, zoom, name="AVT " + str(c.num), rotate=rotate
                            )
                            for c in cams
                        ]
                    )
                )
                loop.close()
        else:
            with AVT_Camera(board) as cam:
                if TriggerMode:
                    print("External trigger")
                    cam.set_trigger_mode(True)
                else:
                    print("Internal trigger")
                    cam.set_trigger_mode(False)
                if roi:
                    cam.set_roi(*roi)
                cam.set_exposure_time(exposure_ms / 1000)
                cam.preview(backend, slice, zoom, rotate)


def preview_andor(
    num=0,
    backend="cv",
    slice=None,
    zoom=1.0,
    TriggerMode=None,
    exposure_ms=1,
    bitdepth=12,
    framerate=10.0,
    rotate=0,
):
    if not has_andor:
        print("Andor bindings are not available.")
    else:
        with Andor_Camera(num) as cam:
            cam.set_exposure_time(exposure_ms / 1000)
            cam.FrameRate.setValue(framerate)
            if bitdepth == 12:
                cam.PixelEncoding.setString("Mono12Packed")  # Mono12Packed Mono16
                # cam.BitDepth.setString('12 Bit')
                cam.SimplePreAmpGainControl.setString("11-bit (low noise)")
            elif bitdepth == 16:
                cam.PixelEncoding.setString("Mono16")
                # cam.BitDepth.setString('16 Bit')
                cam.SimplePreAmpGainControl.setString(
                    "16-bit (low noise & high well capacity)"
                )
            else:
                raise ValueError("Only 12-bits or 16-bits")
            cam.preview(backend, slice, zoom, rotate)


def preview_ids(
    num=0,
    backend="cv",
    slice=None,
    zoom=1.0,
    TriggerMode=None,
    exposure_ms=1,
    bitdepth=12,
    framerate=10.0,
    rotate=0,
):
    if not has_ids:
        print("IDS bindings (pyueyes) are not available")
    else:
        with IDS_Camera(num) as cam:
            cam.set_exposure_time(exposure_ms)
            cam.set_frame_rate(framerate)
            cam.preview(backend, slice, zoom, rotate)


def preview_ximea(
    num=None,
    backend="cv",
    slice=None,
    zoom=1.0,
    TriggerMode=None,
    exposure_ms=1.0,
    rotate=0,
    white_balance=False,
    roi=None,
):

    if not has_ximea:
        print("Ximea bindings are not available.")
    else:
        with Ximea_Camera(num) as cam:
            cam.set_trigger_mode(TriggerMode)
            cam.set_exposure_time(exposure_ms * 1e-3)
            if cam.cam.is_iscolor():
                cam.set_auto_white_balance(white_balance)
            if roi is not None:
                cam.set_roi(*roi)
            cam.preview(backend, slice, zoom, rotate)


def preview_photometrics(
    num=0,
    backend="cv",
    slice=None,
    zoom=1.0,
    TriggerMode=None,
    exposure_ms=1.0,
    bitdepth=12,
    rotate=0,
    roi=None,
):
    """Bitdepth is 8, 12 or 16. Then we choose readout_port "Speed" (1), "Sensitivity" (0) or "Dynamic Range" (2)"""
    if not has_photometrics:
        print("Photometrics bindings are not available.")
        raise photometrics_exc
    else:
        if bitdepth == 8:
            readout_port = 1
        elif bitdepth == 12:
            readout_port = 0
        elif bitdepth == 16:
            readout_port = 2
        with Photometrics_Camera(num, readout_port) as cam:
            cam.set_exposure_time(exposure_ms * 1e-3)
            try:
                cam.set_trigger_mode(TriggerMode)
            except RuntimeError:
                pass
            if roi is not None:
                cam.set_roi(*roi)
            cam.preview(backend, slice, zoom, rotate)
