pymanip
-------

Python framework for experiments based on fluidlab.
This package aims at replacing OctMI.
It is  developed in close relation to fluidlab package. It aims at
providing simpler bindings for the non geeky end-user.

To use:

    >>> from pymanip import Session
    >>> from pymanip.instruments import Agilent34970a
    >>> MI = Session('Monitoring', ('R1', 'R2') )
    >>> multiplexer = Agilent34970a('GPIB0::9::INSTR')
    >>> (R1, R2) = multiplexer.ohm_4w.get( (101, 102) )
    >>> MI.log_addline()
    >>> MI.log_plot(1, ('R1') )
    >>> MI.sleep(30)
    >>> MI.Stop()
