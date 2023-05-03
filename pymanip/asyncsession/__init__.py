"""Asynchronous Session Module (:mod:`pymanip.asyncsession`)
============================================================

This module defines two classes for live acquisition, :class:`~pymanip.asyncsession.AsyncSession`
and :class:`~pymanip.asyncsession.RemoteObserver`. The former is used to
manage an experimental session, the latter to access its live data from a
remote computer. There is also one class for read-only access to previous session,
:class:`~pymanip.asyncsession.SavedAsyncSession`.

.. autoclass:: AsyncSession
   :members:
   :private-members:

.. autoclass:: SavedAsyncSession
   :members:
   :private-members:

.. autoclass:: RemoteObserver
   :members:
   :private-members:

.. _FluidLab: https://foss.heptapod.net/fluiddyn/fluidlab

"""

from .asyncsession import AsyncSession
from .remoteobserver import RemoteObserver
from .savedasyncsession import SavedAsyncSession

__all__ = ["AsyncSession"]


if __name__ == "__main__":
    with AsyncSession("Essai") as sesn:
        sesn.add_entry(a=1, b=2)
        sesn.save_parameter(c=3)
        sesn.plot("a")
