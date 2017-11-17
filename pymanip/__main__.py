"""

pymanip CLI interface

"""

from pathlib import Path
from argparse import ArgumentParser
from pymanip.util.session import manip_info, check_hdf, rebuild_from_dat
from pymanip.util.gpib import scanGpib
try:
    from pymanip.daq import DAQmx
    has_daq = True
except ModuleNotFoundError:
    has_daq = False

# Create top-level parser
parser = ArgumentParser(description=__doc__, prog='pymanip')
#parser.add_argument('command',
#                    help="pymanip command",
#                    metavar="command")
subparsers = parser.add_subparsers(title='command',
                                   help="pymanip command",
                                   dest='command')

# Create parser for the "info" command
parser_info = subparsers.add_parser("info", 
                help="shows the content of a saved pymanip session")
parser_info.add_argument('sessionName', 
                        help="name of the saved session to inspect",
                        metavar="session_name")
parser_info.add_argument('-q', '--quiet', 
                         action='store_true', 
                         help="do not list content.")
parser_info.add_argument('-l', '--line', 
                         help="print specified line of logged data.", 
                         type=int, 
                         metavar="line")
parser_info.add_argument('-p', '--plot', 
                         help="plot the specified variable.", 
                         metavar="varname")

# Create parser for "list_instruments"
parser_list_inst = subparsers.add_parser("list_instruments",
                                         help="List supported instruments")

# Create parser for "list_daq"
parser_daq = subparsers.add_parser("list_daq",
                                   help="List available acquisition cards")

# Create parser for "check_hdf"
parser_hdf = subparsers.add_parser("check_hdf",
                                   help="checks dat and hdf files are identical")
parser_hdf.add_argument('sessionName', 
                        help='Name of the pymanip acquisition to inspect',
                        metavar="session_name")
parser_hdf.add_argument('-p', '--plot', 
                        help='Plot the specified variable',
                        metavar="varname")

# Create parser for "rebuild_hdf"
parser_rebuild = subparsers.add_parser("rebuild_hdf",
                                       help="Rebuilds a pymanip HDF5 file from the ASCII dat file")
parser_rebuild.add_argument('input_file', help='Input ASCII file')
parser_rebuild.add_argument('output_name', help='Output MI session name')

# Create parser for "scan_gpib"
parser_gpib = subparsers.add_parser("scan_gpib",
                                    help="Scans for connected instruments on the specified GPIB board (linux-gpib only)"
                                    )
parser_gpib.add_argument('boardNumber', 
            help="GPIB board to scan for connected instruments", 
            metavar="board_number", type=int, default=0, nargs='?')

# Parse arguments
args = parser.parse_args()

if args.command == 'info':
    manip_info(args.sessionName, args.quiet, args.line, args.plot)
elif args.command == 'list_instruments':
    import pymanip
    pymanip.pymanip_import_verbose = True
    import pymanip.instruments
elif args.command == 'check_hdf':
    check_hdf(args.sessionName, args.plot)
elif args.command == 'list_daq':
    if not has_daq:
        print('DAQmx is not available')
    else:
        DAQmx.print_connected_devices()
elif args.command == 'rebuild_hdf':
    rebuild_from_dat(Path(args.input_file), args.output_name)
elif args.command == 'scan_gpib':
    scanGpib(int(args.boardNumber))
else:
    print("Unknown command `{:}'.")
