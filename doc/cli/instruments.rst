Instrument informations and live-preview
========================================

.. _list_instruments:

Instrument classnames
---------------------

The names of the available instrument classes available in the :mod:`pymanip.instruments` module can be conveniently obtained from the command line:

.. code-block:: bash

    $ python -m pymanip list_instruments

Scanning for instruments
------------------------

Two command line tools are provided to scan for instruments:

- the `list_daq` sub-command searches for acquisition cards using the NI-DAQmx library;

- the `scan_gpib` sub-command searches for connected GPIB devices using the linux-gpib free library (linux only). On Windows and Macs, this is not useful because one can simply use the GUI provided by National Instruments (NI MAX).

Live-preview
------------

Two simple GUI interfaces are provided:

- the `oscillo` sub-commands implements a simple matplotlib GUI for the :mod:`pymanip.aiodaq` module, and allows use any of these channels as oscilloscope and live signal analyser. It is simply invoked with this command

.. code-block:: bash
    
    $ python -m pymanip oscillo

then the user is prompted for the channels that can be viewed (on the connected DAQmx and Scope cards).

- the `video` sub-command implements live video preview with the :mod:`pymanip.video` classes. Two GUI toolkits are possible: pyqt or opencv. The desired camera and acquisition parameters must be passed as argument on the command line.
