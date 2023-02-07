Installation
============

Dependencies
------------

:mod:`pymanip` requires FluidLab_ which it builds upon, as well as several third-party modules
to communicate with instruments, either indirectly through FluidLab_, or directly. Not all
dependencies are declared in the `requirements.txt` file, because none of them are hard
dependencies. It is possible to use :mod:`pymanip` or FluidLab_ with only a subset of these
dependencies.
Here is a dependence table, depending on what you want to do with the package. If a feature
is available through FluidLab_, the table indicates the FluidLab_ submodule that we are
using.

=============================  =========================== ==========================================================================
pymanip module                 fluidlab module             third-pary modules
=============================  =========================== ==========================================================================
:mod:`pymanip.instruments`     :mod:`fluidlab.instruments` gpib_ (linux-gpib python bindings), pymodbus_, pyserial_, pyvisa_
:mod:`pymanip.daq.DAQmx`       :mod:`fluidlab.daq.daqmx`   PyDAQmx_
:mod:`pymanip.daq.Scope`                                   niScope_
:mod:`pymanip.aiodaq.daqmx`                                nidaqmx_
:mod:`pymanip.aiodaq.scope`                                niScope_
:mod:`pymanip.aioinstruments`  :mod:`fluidlab.instruments` Similar to :mod:`pymanip.instruments`
:mod:`pymanip.video`                                       AndorNeo_, pymba_, opencv_, pyqtgraph_ (optional)
:mod:`pymanip.asyncsession`                                aiohttp_, aiohttp_jinja2_, PyQt5_ (optional)
:mod:`pymanip.session`                                     h5py_
=============================  =========================== ==========================================================================

We also have our own bindings for some external libs, such as :mod:`pymanip.video.pixelfly` for PCO Library, :mod:`pymanip.nisyscfg`
for National Instruments NISysCfg library.

Download and install
--------------------

We recommand to install FluidLab_ and :mod:`pymanip` from the repositories, i.e. FluidLab_ from Heptapod and
:mod:`pymanip` from GitHub, and to use the `-e` option of `pip install` to easily pull updates from the
repositories:

.. code-block:: bash

    $ hg clone https://foss.heptapod.net/fluiddyn/fluidlab
    $ cd fluidlab
    $ python -m pip install -e .
    $ cd ..
    $ git clone https://github.com/jsalort/pymanip.git
    $ cd pymanip
    $ python -m pip install -e .

However, it is also possible to install from PyPI:

.. code-block:: bash

    $ python -m pip install fluidlab pymanip

Full installation with conda
----------------------------

Of course, it is possible to install the module, and its dependencies any way you like. For the record, I write here
the procedure that we have been using in our lab for all our experimental room computers, using Anaconda. I am not
advocating that it is better than another method. It installs 
many packages that are not dependencies of pymanip or fluidlab, but that we use regularly. We install as many packages
as possible from conda, so that pip installs as little dependencies as possible. We also use black, flake8 and pre-commit
hooks for the git repository.

Our base environment is setup like this:

.. code-block:: bash

    $ conda create -n py37 python=3.7
    $ conda activate py37
    $ conda install conda
    $ conda install jupyterlab jupyter_console widgetsnbextension qtconsole spyder numpy matplotlib scipy
    $ conda install h5py scikit-image opencv
    $ conda install git
    $ conda install cython numba aiohttp flake8 filelock flask markdown
    $ python -m pip install --upgrade pip
    $ python -m pip install PyHamcrest
    $ python -m pip install clint pint aiohttp_jinja2
    $ python -m pip install pyserial pydaqmx pyvisa pyvisa-py
    $ python -m pip install pyqtgraph
    $ python -m pip install llc black pre-commit
    $ python -m pip install importlib_resources

Then fluiddyn, fluidimage, fluidlab and pymanip are installed from the repository, as indicated in the previous
section. For the computer with video acquisition, the third-party library must first be installed, and then the
corresponding third-party python package, as indicated in the table.


.. _FluidLab: https://fluidlab.readthedocs.io/en/latest/

.. _gpib: https://linux-gpib.sourceforge.io

.. _pymodbus: https://pypi.org/project/pymodbus3/

.. _pyserial: https://pypi.org/project/pyserial/

.. _pyvisa: https://pypi.org/project/PyVISA/

.. _PyDAQmx: https://pypi.org/project/PyDAQmx/

.. _niScope: https://pypi.org/project/niscope/

.. _nidaqmx: https://github.com/ni/nidaqmx-python/

.. _AndorNeo: https://github.com/scivision/pyAndorNeo/tree/master/AndorNeo

.. _pymba: https://pypi.org/project/pymba/

.. _opencv: https://opencv-python-tutroals.readthedocs.io/en/latest/py_tutorials/py_setup/py_intro/py_intro.html

.. _pyqtgraph: https://pypi.org/project/pyqtgraph/

.. _aiohttp: https://pypi.org/project/aiohttp/

.. _aiohttp_jinja2: https://pypi.org/project/aiohttp-jinja2/

.. _PyQt5: https://pypi.org/project/PyQt5/

.. _h5py: https://pypi.org/project/h5py/
