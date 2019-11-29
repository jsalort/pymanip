Instrument drivers
==================

The instrument drivers in :mod:`pymanip` are directly those of :mod:`fluidlab.instruments`.
An instance object represents an actual physical instrument, and the features that can be
read or set are represented as instance attributes. These attributes have consistant names
for all our instrument drivers, summarized in the table below

====================  ==============
Physical measurement  Attribute name
====================  ==============
DC Voltage            vdc
AC Voltage            vrms
DC Current            idc
AC Current            irms
2-wire impedence      ohm
4-wire impedence      ohm_4w
Signal phase shift    angle
Frequency             freq
On Off switch         onoff
Pressure              pressure
Temperature           temperature
Setpoint              setpoint
====================  ==============

Some device may have specific feature name in special cases, but we try to keep using similar
names for similar features.
Each feature then can be accessed by :meth:`get` and :meth:`set` methods, as appropriate. The
:meth:`get` will query the instrument for the value. The :meth:`set` method will set the value.
It is a design choice to use getters and setters, instead of python properties, to make the
actual communication command more explicit.

For example to read a voltage on a multimeter:

.. code-block:: python
   
   Vdc = multimeter.vdc.get()
    
And to set the voltage setpoint to 1 volt on a power supply:

.. code-block:: python

    powersupply.vdc.set(1.0)

Unless otherwise specified, :meth:`vdc.get()` will always read an actual voltage, and not 
the voltage setpoint. This is a design choice because we think the users should know what setpoint
they have set in the general case. In case it is necessary to actually query the instrument for
its setpoint, an additionnal :attr:`setpoint` attribute may be defined.

The implementation details of the instrument drivers, and how they are mixed with the interface
and feature classes is described in the :mod:`fluidlab.instruments` module documentation.

:mod:`pymanip.instruments` defines shortcut classes, as well as an asynchronous extension to
the :mod:`fluidlab.instruments` classes.


.. toctree::
   :maxdepth: 1
   :caption: Contents

   shortcut
   instrument_list
   aioinstruments
   aioinstruments_implementation
