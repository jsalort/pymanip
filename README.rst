pymanip
-------

Python framework for experiments
This package aims at replacing OctMI.

To use:

    >>> from pymanip import Session
    >>> MI = Session('Monitoring', ('R1', 'R2') )
    >>> (R1, R2) = multiplexer.ohm_4w.get( (101, 102) )
    >>> MI.log_addline()
    >>> MI.log_plot(1, ('R1') )
    >>> MI.sleep(30)
    >>> MI.Stop()
