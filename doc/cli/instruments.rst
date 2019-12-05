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
