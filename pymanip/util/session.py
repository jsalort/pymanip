"""

This module defines utility function to interact with pymanip sessions

"""

import sys
import time
import os

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.dates import AutoDateFormatter, AutoDateLocator, epoch2num
from fluiddyn.util.terminal_colors import cprint

try:
    import pandas as pd

    has_panda = True
except ModuleNotFoundError:
    has_panda = False
from pymanip.collection import Manip
from pymanip import Session, SavedSession
from pymanip.asyncsession import SavedAsyncSession
from pymanip.mytime import dateformat


def manip_info(sessionName, quiet, line_to_print, var_to_plot):
    """
    This function prints information about a session, and optionally
    plot specified variables.

    It can be accessed from the CLI tool ManipInfo
    """

    if os.path.exists(sessionName + ".db"):
        SavedAsyncSession(sessionName).print_description()
        return

    if sessionName.endswith(".hdf5"):
        N = len(sessionName)
        sessionName = sessionName[0 : (N - 5)]

    MI = Manip(sessionName).MI
    if line_to_print is not None:
        if line_to_print >= len(MI.log("t")):
            print("Specified line is out of bound.")
            sys.exit(1)
        format_str = "{:>15} | {:>20}"
        print("Printing saved values on line", line_to_print)
        print(format_str.format("Variable", "Value"))
        varlist = ["Time"]
        varlist += MI.log_variable_list()
        print("-" * 38)
        for varname in varlist:
            valtab = MI.log(varname)
            if isinstance(valtab, (float, int)):
                # might occur if only one line
                print(format_str.format(varname, MI.log(varname)))
            else:
                print(format_str.format(varname, MI.log(varname)[line_to_print]))
    elif not quiet:
        MI.describe()
    if var_to_plot is not None:
        if var_to_plot in MI.log_variable_list():
            t = epoch2num(MI.log("t"))
            vardata = MI.log(var_to_plot)
            fig = plt.figure()
            xtick_locator = AutoDateLocator()
            xtick_formatter = AutoDateFormatter(xtick_locator)
            ax = plt.axes()
            ax.xaxis.set_major_locator(xtick_locator)
            ax.xaxis.set_major_formatter(xtick_formatter)
            ax.plot(t, vardata, "o-")
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=70)
            fig.subplots_adjust(bottom=0.2)
            plt.ylabel(var_to_plot)
            plt.title(sessionName)
            plt.show()
        else:
            print("Variable", var_to_plot, "does not exist!")
            sys.exit(1)


def check_hdf(acqName, variable_to_plot):
    """
    This functions checks that the .dat file and the .hdf5 file of
    a pymanip session holds the same data.
    """

    if not has_panda:
        print("Pandas must be installed.")
        sys.exit(-1)

    # Lecture HDF5
    MI = SavedSession(acqName)

    # Lecture DAT
    datfile = acqName + ".dat"
    print("Loading saved session from file", datfile)
    data = pd.read_csv(datfile, sep=" ")
    start_t = data["Time"].values[0]
    end_t = data["Time"].values[-1]
    start_string = time.strftime(dateformat, time.localtime(start_t))
    end_string = time.strftime(dateformat, time.localtime(end_t))
    cprint.blue("*** Start date: " + start_string)
    cprint.blue("***  End date: " + end_string)

    varlist = ["Time"]
    varlist += MI.log_variable_list()

    # First line
    print("Printing first line.")
    format_str = "{:>15} | {:>20} | {:>20}"
    print(format_str.format("", "HDF", "DAT"))
    print("-" * 80)
    for varname in varlist:
        data_hdf = MI.log(varname)[0]
        data_dat = data[varname].values[0]
        print(format_str.format(varname, data_hdf, data_dat))

    # Comparaison
    length_warning_done = False
    for varname in varlist:
        var_hdf = MI.log(varname)
        var_dat = data[varname].values
        if len(var_hdf) != len(var_dat):
            common_length = np.min([len(var_hdf), len(var_dat)])
            if not length_warning_done:
                print("Number of data points differs.")
                print("HDF:", len(var_hdf))
                print("DAT:", len(var_dat))
                length_warning_done = True
                print("Comparing the first", common_length, " values")
            var_hdf = var_hdf[0:common_length]
            var_dat = var_dat[0:common_length]
        reldiff = np.abs(var_hdf - var_dat) / (var_hdf + var_dat)
        bb = reldiff > 0.01
        if bb.any():
            print("Data differs for variable " + varname)
            index = np.min(bb.argmax())
            print("On line", index, ": HDF=", var_hdf[index], "DAT=", var_dat[index])
        else:
            print("Identical data for variable " + varname)

    # Plot
    if variable_to_plot is not None:
        plt.figure(1)
        t = MI.log("t")
        var = MI.log(variable_to_plot)
        plt.plot(t - t[0], var)
        plt.title("HDF")
        plt.xlabel("t")
        plt.ylabel(variable_to_plot)

        plt.figure(2)
        t = data["Time"].values
        var = data[variable_to_plot].values
        plt.plot(t - t[0], var)
        plt.title("DAT")
        plt.xlabel("t")
        plt.ylabel(variable_to_plot)

        plt.show()


def rebuild_from_dat(inputDatfile, outputSessionName):
    """
    Rebuilds a pymanip HDF5 file from the ASCII dat file.
    """

    if not has_panda:
        print("Pandas is not available.")
    else:
        with inputDatfile.open() as in_f:
            data = pd.read_csv(in_f, sep=" ")
            liste_var = list(data.keys())
            liste_var.remove("Time")
            MI = Session(outputSessionName, liste_var)
            for line in data.iterrows():
                MI.log_addline(timestamp=line[1].Time, dict_caller=dict(line[1]))
            MI.Stop()
