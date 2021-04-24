Video acquisition
=================

The :mod:`pymanip.video` module provides tools to help with camera acquisition. We
use the third-party :mod:`pymba` module bindings to the AVT Vimba_ SDK for 
AVT cameras, the third-party :mod:`pyAndorNeo` module bindings to the
Andor_ SDK3 library for the Andor Camera, the third-party :mod:`pyueye` module
bindings to the IDS ueye library, the Python module provided by Ximea_ for the
Ximea cameras, and PyVCAM_ wrapper for Photometrics camera.

We wrote our own bindings to the Pixelfly_ library for the PCO camera.
Beware that the code works for us, but there is no garantee that it will work with
your camera models.

The idea was for us to be able to switch cameras, without having to change much of
the acquisition code. So we define an abstract :class:`pymanip.video.Camera` base 
class, and all concrete sub-classes follow the exact same user API. The methods allow
to start video acquisition, in a manner consistent with our needs, and also provides
a unified live preview API.
It also makes it relatively straightforward to do simultaneous acquisition on several
cameras, even if they are totally different models and brands and use different
underlying libraries.

The useful concrete classes are given in this table:

=============  =======================================================
Camera type    Concrete class
=============  =======================================================
AVT            :class:`pymanip.video.avt.AVT_Camera`
PCO            :class:`pymanip.video.pco.PCO_Camera`
Andor          :class:`pymanip.video.andor.Andor_Camera`
IDS            :class:`pymanip.video.ids.IDS_Camera`
Ximea          :class:`pymanip.video.ximea.Ximea_Camera`
Photometrics   :class:`pymanip.video.photometrics.Photometrics_Camera`
=============  =======================================================

They all are sub-classes of the :class:`pymanip.video.Camera` abstract base
class. Most of the user-level useful documentation lies in the base class.
Indeed, all the concrete implementation share the same API, so their internal 
methods are implementation details.

In addition, a high-level class, :class:`pymanip.video.session` is provided to
build simple video acquisition scripts, with possible concurrent cameras trigged
by a function generator.

.. toctree::
   :maxdepth: 2
   :caption: Contents

   basic
   asynchronous
   advanced
   session
   implementation
   andor
   avt
   pco
   ids
   ximea
   photometrics

.. _Andor: https://www.scivision.dev/andor-neo-windows-sdk3-install/

.. _Vimba: https://www.alliedvision.com/en/products/software.html

.. _Pixelfly: https://www.pco.de/software/

.. _Ximea: https://www.ximea.com/support/wiki/apis/Python_inst_win

.. _PyVCAM: https://github.com/Photometrics/PyVCAM
