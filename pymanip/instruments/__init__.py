"""Instruments module (:mod:`pymanip.instruments`)
==================================================

This module auto-imports all the instruments classes from :class:`fluidlab.instruments`:

.. currentmodule:: pymanip.instruments

.. autosummary::

{instruments:}

"""

from .fluidlab_instruments import *
from .fluidlab_instruments import __all__

instruments_str = "\n".join("   " + c for c in __all__)
__doc__ = __doc__.format(instruments=instruments_str)
