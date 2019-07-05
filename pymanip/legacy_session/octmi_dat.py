#! /usr/bin/env python
# -*- coding: utf-8 -*-

import os
import numpy as np


def load_octmi_dat(acquisitionName, basePath="."):
    # Vérification de l'existence du fichier
    datFilePath = os.path.join(os.path.normpath(basePath), acquisitionName + "_MI.dat")
    if not os.path.exists(datFilePath):
        print("Could not stat file", datFilePath)
        raise NameError("File does not exist")

    # Décompte du nombre d'éléments
    nval = 0
    variableList = ""
    with open(datFilePath, "r") as f:
        for line in f:
            if line[0] == "T":
                if line != variableList:
                    variableList = line
                    # print variableList
            else:
                nval = nval + 1

    variableList = variableList.split(" ")

    dictionnaire = dict()
    dictionnaire["nval"] = nval
    if nval > 1:
        for i in range(len(variableList)):
            dictionnaire[variableList[i].strip()] = np.zeros(nval)

    linenum = 0
    with open(datFilePath, "r") as f:
        for line in f:
            contentList = line.split(" ")
            if contentList[0] != "Time":
                if nval == 1:
                    for i in range(len(variableList)):
                        dictionnaire[variableList[i].strip()] = eval(
                            contentList[i].strip()
                        )
                else:
                    for i in range(len(variableList)):
                        if i < len(contentList):
                            dataStr = contentList[i].strip()
                            if dataStr.lower() == "nan":
                                dictionnaire[variableList[i].strip()][linenum] = np.nan
                            else:
                                dictionnaire[variableList[i].strip()][linenum] = eval(
                                    contentList[i].strip()
                                )
                        else:
                            dictionnaire[variableList[i].strip()][linenum] = np.nan
                    linenum = linenum + 1

    return dictionnaire
