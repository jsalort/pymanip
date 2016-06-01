# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import os
import numpy as np
import matplotlib.pyplot as plt
from PyQt4 import QtGui, QtCore
import itertools

myplot_colors = {'blue'      : (0.0, 0.0, 1.0),
                 'green'     : (0.0, 1.0, 0.0),
                 'red'       : (1.0, 0.0, 0.0),
                 'cyan'      : (0.0, 1.0, 1.0),
                 'magenta'   : (1.0, 0.0, 1.0),
                 'yellow'    : (1.0, 1.0, 0.0),
                 'k'         : (0.0, 0.0, 0.0),
                 'igoine'    : (0.0, 0.5, 0.0),
                 'eau'       : (0.0, 0.6, 1.0),
                 'qarotte'   : (1.0, 0.6, 0.0),
                 'fushia'    : (1.0, 0.0, 0.6),
                 'lila'      : (0.6, 0.0, 1.0),
                 'terre'     : (0.6, 0.2, 0.0),
                 'nuit'      : (0.0, 0.2, 0.6),
                 'anthracite': (0.4, 0.4, 0.4),
                 'jackson'   : (0.7, 0.7, 0.7),
                 'Red'       : (0.5, 0.0, 0.0)
                 }

def myplot_color(name):
    for key in myplot_colors:
        if (key == name) or (key[0] == name):
            break
    else:
        key='black'
    return myplot_colors[key]

myplot_colorcycle_ = itertools.cycle(["b", "g", "r", "c", "m", "y", "k", "i", "e", "q", "f", "l", "t", "n", "a", "j", "R"])

def myplot_colorcycle():
    return myplot_color(next(myplot_colorcycle_))

def myplot_gridvisibility(ax):
    return True

def myplot_color2Tikz(color):
    return {
            'b': 'blue',
            'g': 'green',
            'r': 'red',
            'c': 'cyan',
            'm': 'magenta',
            'y': 'yellow',
            'k': 'black',
            'w': 'white',
            'i': 'green!50!black',
            'e': 'blue!50!cyan',
            'q': 'orange',
            'f': 'violet',
            'l': 'purple',
            't': 'brown',
            'n': 'blue!50!black',
            'a': 'darkgray',
            'j': 'gray',
            'R': 'red!50!black',
            'G': 'teal',
            'C': 'lime',
            'S': 'pink'}.get(color, 'black')

def myplot_marker2Tikz(marker):
    return {
            None: 'no marks',
            'None': 'no marks',
            0: 'mark=-',
            1: 'mark=-',
            2: 'mark=|',
            3: 'mark=|',
            4: 'mark=triangle',
            5: 'mark=triangle',
            6: 'mark=triangle',
            7: 'mark=triangle',
            '': 'no marks',
            ' ': 'no marks',
            '*': 'mark=star',
            '+': 'mark=+',
            ',': 'mark=*',
            '.': 'mark=*',
            '1': 'mark=triangle',
            '2': 'mark=triangle',
            '3': 'mark=triangle',
            '4': 'mark=triangle',
            '8': 'mark=pentagon',
            '<': 'mark=triangle',
            '>': 'mark=triangle',
            'D': 'mark=diamond',
            'H': 'mark=pentagon',
            '^': 'mark=triangle',
            '_': 'mark=-',
            'd': 'mark=diamond',
            'h': 'mark=pentagon',
            'o': 'mark=o',
            'p': 'mark=pentagon',
            's': 'mark=square',
            'v': 'mark=triangle',
            'x': 'mark=x',
            '|': 'mark=|'}.get(marker, 'o')

def myplot2tikz(fig, outputFolder):
    # Normalisation du path et création du dossier
    os.path.normpath(outputFolder)
    if not os.path.exists(outputFolder):
        os.mkdir(outputFolder)

    # Création du fichier TeX
    tex_filename = outputFolder + '/' + os.path.basename(outputFolder) + '.tex'
    tex_fid = open(tex_filename, 'w')
    try:
        # Préambule du fichier TeX
        tex_fid.write("\\documentclass{article}\n")
        tex_fid.write("\\usepackage{fontspec, unicode-math}\n")
        tex_fid.write("\\usepackage{pgfplots}\n")
        tex_fid.write("\\pgfplotsset{compat=newest}\n")
        tex_fid.write("\\usepackage{siunitx}\n")
        tex_fid.write("\\usepackage[active,pdftex,tightpage]{preview}\n")
        tex_fid.write("\\usepackage{amsmath}\n")
        tex_fid.write("\\usetikzlibrary{plotmarks}\n")
        tex_fid.write("\n")

        tex_fid.write("% Uncomment this line if the bounding box is too tight:\n")
        tex_fid.write("% \\setlength{\\PreviewBorder}{2bp}\n")
        tex_fid.write("\n")

        tex_fid.write("\\begin{document}\n")
        tex_fid.write("\\begin{preview}\n")
        tex_fid.write("\\begin{tikzpicture}\n")

        axes = fig.get_axes()
        for axe in axes:
            # Type d'axe
            if axe.get_xaxis().get_scale() == 'linear' and axe.get_yaxis().get_scale() == 'linear':
                axisType = "axis"
            elif axe.get_xaxis().get_scale() == 'linear' and axe.get_yaxis().get_scale() != 'linear':
                axisType = "semilogyaxis"
            elif axe.get_xaxis().get_scale() != 'linear' and axe.get_yaxis().get_scale() == 'linear':
                axisType = "semilogxaxis"
            else:
                axisType = "loglogaxis"

            # Propriétés de l'axe
            tex_fid.write("\\begin{" + axisType + "}[%\n")
            if myplot_gridvisibility(axe):
                tex_fid.write("grid=both,\n")
            else:
                tex_fid.write("%grid=both,\n")
            if len(axe.get_title()) == 0:
                tex_fid.write("%title={},\n")
            else:
                tex_fid.write("title={" + axe.get_title() + "},\n")


            tex_fid.write("%width=16cm,\n")
            tex_fid.write("%height=7cm,\n")
            tex_fid.write("xmin=" + str(axe.get_xlim()[0]) + ",\n")
            tex_fid.write("xmax=" + str(axe.get_xlim()[1]) + ",\n")
            tex_fid.write("ymin=" + str(axe.get_ylim()[0]) + ",\n")
            tex_fid.write("ymax=" + str(axe.get_ylim()[1]) + ",\n")
            tex_fid.write( ("xlabel={" + axe.get_xlabel() + "},\n").encode("utf-8"))
            tex_fid.write( ("ylabel={" + axe.get_ylabel() + "},\n").encode("utf-8"))
            tex_fid.write("%every axis x label/.style={%\n")
            tex_fid.write("%  at={(0.8,0.07)}\n")
            tex_fid.write("%},\n")
            tex_fid.write("%every axis y label/.style={%\n")
            tex_fid.write("%  at={(0.95,0.05)},\n")
            tex_fid.write("%  rotate=90\n")
            tex_fid.write("%},\n")
            tex_fid.write("%font=\\small,\n")
            tex_fid.write("%xtick={},\n")
            tex_fid.write("%xticklabels={},\n")
            tex_fid.write("%ytick={},\n")
            tex_fid.write("%yticklabels={},\n")
            tex_fid.write("%every axis legend/.append style={%\n")
            tex_fid.write("% at={(1.02,1)},\n")
            tex_fid.write("% anchor=north west},\n")
            tex_fid.write("% axis background/.style={fill=white},\n")
            tex_fid.write("%legend cell align=left,\n")
            tex_fid.write("%legend columns=,\n");
            tex_fid.write("%legend pos=outer north east\n");
            tex_fid.write("]\n");

            # Plots
            lines = axe.get_lines()
            i=1
            for line in lines:
                # Export des données dans un fichier table
                tableFilename = outputFolder + "/figure-" + str(i) + ".table"
                i=i+1
                table_fid = open(tableFilename, "w")
                np.savetxt(table_fid, line.get_xydata())
                table_fid.close()

                # Ligne \addplot
                tex_fid.write("\\addplot[")
                tex_fid.write("color=" + myplot_color2Tikz(line.get_color()) + ",")
                tex_fid.write(myplot_marker2Tikz(line.get_marker()))
                tex_fid.write("] file {" + os.path.basename(tableFilename) + "};\n")
                if len(line.get_label()) > 0 and line.get_label()[0] != '_':
                    tex_fid.write("\\addlegendentry{" + line.get_label() + "};\n")
                else:
                    tex_fid.write("%\\addlegendentry{};\n")
            tex_fid.write("\\end{" + axisType + "}\n")

        tex_fid.write("\\end{tikzpicture}\n")
        tex_fid.write("\\end{preview}\n")
        tex_fid.write("\\end{document}\n")
    finally:
        tex_fid.close()

    old_cwd = os.getcwd()
    try:
        os.chdir(outputFolder)
        os.spawnlp(os.P_WAIT, 'lualatex', 'lualatex', os.path.basename(outputFolder))
    finally:
        os.chdir(old_cwd)
        os.system('open -a TeXShop ' + tex_filename)


class myplotcontrolWidget(QtGui.QWidget):
    def __init__(self, fig):
        print 'constructor'
        self.fig = fig
        super(myplotcontrolWidget, self).__init__()
        self.initUI()

    def __del__(self):
        print 'destructor'

    def initUI(self):
        # Setting window properties
        self.setGeometry(300, 300, 330, 550)
        self.setWindowTitle('Properties of figure')

        # Create table
        self.table = QtGui.QTableWidget()

        # Create layout
        vbox = QtGui.QVBoxLayout()
        vbox.addWidget(self.table)
        self.setLayout(vbox)

    def show():
        # Populate table
        print 'Populating table'
        axes = self.fig.get_axes()
        for axe in axes:
            lines = axe.get_lines()
            for line in lines:
                label = line.get_label()
                print label

        # Show
        super(myplotcontrolWidget, self).show()

    def toggle():
        print 'toggle'
        if self.isVisible():
            self.hide()
        else:
            self.show()


def mycustomizeplot(fig):
    # Check if QCoreApplication exists
    app_created = False
    app = QtCore.QCoreApplication.instance()
    if app is None:
        app = QtGui.QCoreApplication.instance()
        app_created = True
    app.references = set()

    # Create the myplotcontrol widget
    w = myplotcontrolWidget(fig)
    app.references.add(w)

    # Add the show/hide action to the figure toolbar
    tb = fig.canvas.toolbar
    mpcAction = QtGui.QAction(QtGui.QIcon(os.path.dirname(__file__) + '/myplotcontrol.png'), 'myplotcontrol', w)
    mpcAction.setStatusTip('Show/Hide myplotcontrol panel')
    mpcAction.triggered.connect(w.toggle)
    tb.addAction(mpcAction)

    # If app was just created, execute
    if app_created:
        app.exec_()


def myplot(*args, **kwargs):
    plt.ion()
    plt.plot(*args, **kwargs)
    fig = plt.gcf()
    mycustomizeplot(fig)
    if kwargs.has_key('label'):
        leg = plt.legend()
        leg.draggable()

def mysemilogx(*args, **kwargs):
    plt.ion()
    plt.semilogx(*args, **kwargs)
    fig = plt.gcf()
    mycustomizeplot(fig)
    if kwargs.has_key('label'):
        leg = plt.legend()
        leg.draggable()

def mysemilogy(*args, **kwargs):
    plt.ion()
    plt.semilogy(*args, **kwargs)
    fig = plt.gcf()
    mycustomizeplot(fig)
    if kwargs.has_key('label'):
        leg = plt.legend()
        leg.draggable()

def myloglog(*args, **kwargs):
    plt.ion()
    plt.loglog(*args, **kwargs)
    fig = plt.gcf()
    mycustomizeplot(fig)
    if kwargs.has_key('label'):
        leg = plt.legend()
        leg.draggable()
