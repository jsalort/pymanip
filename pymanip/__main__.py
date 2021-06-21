"""

pymanip CLI interface

"""

from pathlib import Path
from argparse import ArgumentParser
from pymanip.util.session import manip_info, check_hdf, rebuild_from_dat
from pymanip.util.gpib import scanGpib
from pymanip.util.video import (
    preview_pco,
    preview_avt,
    preview_andor,
    preview_ids,
    preview_ximea,
    preview_photometrics,
)

try:
    from pymanip.util.oscillo import Oscillo
    from pymanip.util.channel_selector import ChannelSelector
except ModuleNotFoundError:
    has_oscillo = False
has_video = True

try:
    from pymanip.daq import DAQmx

    has_daq = True
except (ModuleNotFoundError, NotImplementedError):
    has_daq = False

# Create top-level parser
parser = ArgumentParser(description=__doc__, prog="pymanip")
# parser.add_argument('command',
#                    help="pymanip command",
#                    metavar="command")
subparsers = parser.add_subparsers(
    title="command", help="pymanip command", dest="command"
)

# Create parser for the "info" command
parser_info = subparsers.add_parser(
    "info", help="shows the content of a saved pymanip session"
)
parser_info.add_argument(
    "sessionName", help="name of the saved session to inspect", metavar="session_name"
)
parser_info.add_argument(
    "-q", "--quiet", action="store_true", help="do not list content."
)
parser_info.add_argument(
    "-l",
    "--line",
    help="print specified line of logged data.",
    type=int,
    metavar="line",
)
parser_info.add_argument(
    "-p", "--plot", help="plot the specified variable.", metavar="varname"
)

# Create parser for "list_instruments"
parser_list_inst = subparsers.add_parser(
    "list_instruments", help="List supported instruments"
)

# Create parser for "list_daq"
parser_daq = subparsers.add_parser("list_daq", help="List available acquisition cards")

# Create parser for "check_hdf"
parser_hdf = subparsers.add_parser(
    "check_hdf", help="checks dat and hdf files are identical"
)
parser_hdf.add_argument(
    "sessionName",
    help="Name of the pymanip acquisition to inspect",
    metavar="session_name",
)
parser_hdf.add_argument(
    "-p", "--plot", help="Plot the specified variable", metavar="varname"
)

# Create parser for "rebuild_hdf"
parser_rebuild = subparsers.add_parser(
    "rebuild_hdf", help="Rebuilds a pymanip HDF5 file from the ASCII dat file"
)
parser_rebuild.add_argument("input_file", help="Input ASCII file")
parser_rebuild.add_argument("output_name", help="Output MI session name")

# Create parser for "scan_gpib"
parser_gpib = subparsers.add_parser(
    "scan_gpib",
    help="Scans for connected instruments on the specified GPIB board (linux-gpib only)",
)
parser_gpib.add_argument(
    "boardNumber",
    help="GPIB board to scan for connected instruments",
    metavar="board_number",
    type=int,
    default=0,
    nargs="?",
)

# Create parser for "oscillo"
parser_oscillo = subparsers.add_parser(
    "oscillo",
    help="Use NI-DAQmx and NI-Scope cards as oscilloscope and signal analyser",
)
parser_oscillo.add_argument(
    "channel",
    help="DAQmx channel names",
    metavar="channel_name",
    nargs="*",
    default=None,
)
parser_oscillo.add_argument(
    "-s", "--sampling", help="Sampling frequency", metavar="sampling_freq", default=5e3
)
parser_oscillo.add_argument(
    "-r", "--range", help="Channel volt range", metavar="volt_range", default=10.0
)
parser_oscillo.add_argument(
    "-t", "--trigger", help="Trigger level", metavar="level", default=None
)
parser_oscillo.add_argument(
    "-T", "--trigsource", help="Trigger source index", metavar="0", default=0
)
parser_oscillo.add_argument(
    "-b",
    "--backend",
    help="Choose daqmx or scope backend",
    metavar="daqmx",
    default="daqmx",
)
parser_oscillo.add_argument(
    "-p", "--serialport", help="Arduino Serial port", metavar="port", default=None
)

# Create parser for "video"
parser_video = subparsers.add_parser(
    "video", help="Display video preview for specified camera"
)
parser_video.add_argument(
    "camera_type", help="Camera type: PCO, AVT, DC1394, IDS", metavar="camera_type"
)
parser_video.add_argument(
    "-l", "--list", help="List available cameras", action="store_true"
)
parser_video.add_argument(
    "-i",
    "--interface",
    help="Specify interface",
    metavar="interface",
    default="",
    type=str,
)
parser_video.add_argument(
    "-b",
    "--board",
    help="Camera board address",
    metavar="board",
    default=0,
    type=int,
    nargs="+",
)
parser_video.add_argument(
    "-t",
    "--toolkit",
    help="Graphical toolkit to use: cv or qt",
    metavar="toolkit",
    default="qt",
    type=str,
    nargs=1,
)
parser_video.add_argument(
    "-s",
    "--slice",
    help="Slice image x0, x1, y0, y1 in pixels",
    metavar="slice",
    default=[],
    type=int,
    nargs=4,
)
parser_video.add_argument(
    "-z", "--zoom", help="Zoom factor", metavar="zoom", default=0.5, type=float, nargs=1
)
parser_video.add_argument(
    "-T",
    "--Trigger",
    help="Trigger mode",
    metavar="trigger",
    default=-1,
    type=int,
    nargs=1,
)

parser_video.add_argument(
    "-w",
    "--whitebalance",
    help="Enable auto white balance (for color cameras)",
    action="store_true",
)

parser_video.add_argument(
    "-e",
    "--exposure",
    help="Exposure time (ms)",
    metavar="exposure_ms",
    default=20,
    type=float,
    nargs=1,
)
parser_video.add_argument(
    "-d",
    "--bitdepth",
    help="Bit depth",
    metavar="bitdepth",
    default=12,
    type=int,
    nargs=1,
)
parser_video.add_argument(
    "-f",
    "--framerate",
    help="Acquisition framerate in Herz",
    metavar="framerate",
    default=10.0,
    type=float,
    nargs=1,
)
parser_video.add_argument(
    "-r",
    "--rotate",
    help="Rotate image",
    metavar="angle",
    default=0.0,
    type=float,
    nargs=1,
)

parser_video.add_argument(
    "-R",
    "--ROI",
    help="Set Region of Interest xmin, ymin, xmax, ymax",
    metavar="roi",
    default=None,
    type=int,
    nargs=4,
)

if __name__ == "__main__":
    args = parser.parse_args()

    if args.command == "info":
        manip_info(args.sessionName, args.quiet, args.line, args.plot)
    elif args.command == "list_instruments":
        import pymanip

        pymanip.pymanip_import_verbose = True
        import pymanip.instruments
    elif args.command == "check_hdf":
        check_hdf(args.sessionName, args.plot)
    elif args.command == "list_daq":
        if not has_daq:
            print("DAQmx is not available")
        else:
            DAQmx.print_connected_devices()
    elif args.command == "rebuild_hdf":
        rebuild_from_dat(Path(args.input_file), args.output_name)
    elif args.command == "scan_gpib":
        scanGpib(int(args.boardNumber))
    elif args.command == "oscillo":
        if args.trigger is not None:
            trigger = float(args.trigger)
        else:
            trigger = None
        if args.backend is not None:
            backend = args.backend
        if args.channel:
            channel = args.channel
        else:
            if backend == "arduino":
                channel = [int(input("Arduino Analog input pin? "))]
            else:
                chansel = ChannelSelector()
                backend, channel = chansel.gui_select()
        if args.serialport:
            serialport = args.serialport
        elif backend == "arduino":
            serialport = input("Serial port (COM3, /dev/ttyS3, ...)? ")
        if args.sampling:
            sampling = float(args.sampling)
        else:
            sampling = 5e3
        if args.range:
            range_ = float(args.range)
        else:
            range_ = 5.0 if backend == "arduino" else 10.0
        if backend == "arduino":
            backend_args = [serialport]
        else:
            backend_args = None
        oscillo = Oscillo(
            channel,
            sampling,
            5.0 if backend == "arduino" else range_,
            trigger,
            int(args.trigsource),
            backend=backend,
            backend_args=backend_args,
            N=128 if backend == "arduino" else 1024,
        )
        oscillo.run()
    elif args.command == "video":
        if not has_video:
            print("Video libraries not found")
        if isinstance(args.toolkit, list):
            tk = args.toolkit[0]
        else:
            tk = args.toolkit
        if len(args.slice) < 4:
            slice = None
        else:
            slice = args.slice
        if isinstance(args.zoom, list):
            zoom = args.zoom[0]
        else:
            zoom = args.zoom
        if isinstance(args.Trigger, list):
            Trigger = args.Trigger[0]
        else:
            Trigger = args.Trigger
        if Trigger == -1:
            Trigger = None
        if isinstance(args.exposure, list):
            exposure_ms = args.exposure[0]
        else:
            exposure_ms = args.exposure
        if isinstance(args.board, list):
            board = int(args.board[0])
        else:
            board = int(args.board)
        if isinstance(args.bitdepth, list):
            bitdepth = int(args.bitdepth[0])
        else:
            bitdepth = int(args.bitdepth)
        if isinstance(args.framerate, list):
            framerate = float(args.framerate[0])
        else:
            framerate = float(args.framerate)
        if isinstance(args.rotate, list):
            rotate = float(args.rotate[0])
        else:
            rotate = float(args.rotate)
        if args.ROI is not None and len(args.ROI) != 4:
            raise ValueError("ROI must be 4 integers xmin, ymin, xmax, ymax")
        if args.camera_type.upper() == "PCO":
            if args.list:
                from pymanip.video.pco import print_available_pco_cameras

                print_available_pco_cameras()
            else:
                interface = str(args.interface)
                if not interface:
                    interface = "all"
                preview_pco(
                    interface,
                    board,
                    tk,
                    slice,
                    zoom,
                    Trigger,
                    exposure_ms,
                    rotate=rotate,
                    roi=args.ROI,
                )
        elif args.camera_type.upper() == "AVT":
            if args.list:
                print("Listing cameras not implemented for AVT")
            else:
                preview_avt(
                    board,
                    tk,
                    slice,
                    zoom,
                    Trigger,
                    exposure_ms,
                    rotate=rotate,
                    roi=args.ROI,
                )
        elif args.camera_type.upper() == "ANDOR":
            if args.list:
                print("Listing cameras not implemented for Andor")
            else:
                preview_andor(
                    board,
                    tk,
                    slice,
                    zoom,
                    Trigger,
                    exposure_ms,
                    bitdepth,
                    framerate,
                    rotate=rotate,
                )
        elif args.camera_type.upper() == "IDS":
            if args.list:
                print("Listing cameras not implemented for IDS")
            else:
                preview_ids(
                    board,
                    tk,
                    slice,
                    zoom,
                    Trigger,
                    exposure_ms,
                    bitdepth,
                    framerate,
                    rotate=rotate,
                )
        elif args.camera_type.upper() == "XIMEA":
            if args.list:
                print("Listing Ximea camera not implemented.")
            else:
                print("white_balance =", args.whitebalance)
                if board == 0:
                    board = None
                else:
                    raise NotImplementedError("open via SN")
                preview_ximea(
                    board,
                    tk,
                    slice,
                    zoom,
                    Trigger,
                    exposure_ms,
                    rotate=rotate,
                    white_balance=args.whitebalance,
                    roi=args.ROI,
                )
        elif args.camera_type.upper() in ("PHOTOMETRICS", "TELEDYNE", "KINETIX"):
            if args.list:
                from pyvcam.camera import Camera as PVCamera

                print(PVCamera.get_available_camera_names())
            else:
                preview_photometrics(
                    board,
                    tk,
                    slice,
                    zoom,
                    Trigger,
                    exposure_ms,
                    bitdepth,
                    rotate=rotate,
                    roi=args.ROI,
                )
        else:
            print("Unknown camera type: ", args.camera_type)
    else:
        print("Unknown command `{:}'.")
