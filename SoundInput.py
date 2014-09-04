#! /usr/bin/env python
# -*- coding: utf-8 -*-

from pyaudio import PyAudio

def scanDevices():
	p = PyAudio()
	for i in range(p.get_device_count()):
		print p.get_device_info_by_index(i)