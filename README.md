pymanip
=======

Python framework for experiments based on fluidlab.
It is  developed in close relation to fluidlab package. It aims at
providing simpler bindings for the less nerdy end-user.

It is distributed, as is, in the hope that it will be useful,
but without any warranty of usefulness, under the terms of
the CECILL-B license, a BSD compatible French license.

You can get the source code from [github](https://github.com/jsalort/pymanip).

Typical GPIB usage
------------------

```python
from pymanip import Session
from pymanip.instruments import Agilent34970a

MI = Session('Monitoring', ('R1', 'R2') )

try:
    multiplexer = Agilent34970a('GPIB0::9::INSTR')
   
    while True:
        (R1, R2) = multiplexer.ohm_4w.get( (101, 102) )
        
        MI.log_addline()
        MI.log_plot(1, ('R1') )
        MI.sleep(30)

except KeyboardInterrupt:
    pass
finally:
    MI.Stop()
```

Typical Acquisition card usage
------------------------------

```python
from pymanip import Session
from pymanip.daq import DAQmx

N = 10000
fs = 50e3

data, = DAQmx.read_analog('Dev1/ai0', 'Diff',
                          volt_min=-10.0, volt_max=10.0,
                          samples_per_chan=N, sample_rate=fs)
MI.save_dataset('data')
MI.save_parameters( ('N', 'fs') )
MI.Stop()
```


