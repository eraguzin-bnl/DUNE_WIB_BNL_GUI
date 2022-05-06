ECHO "LAr and ADC test begin"
::#user input
python .\QC_top.py 1 

:::#init pwr chk
python .\QC_top.py 2 

::#init pwr meas
python .\QC_top.py 3

::#init pwr cycles 
python .\QC_top.py 4

::#init femb chk
python .\QC_top.py 5

::#init femb rms
python .\QC_top.py 6

::#init femb asicdac cali
python .\QC_top.py 7

::#init femb mon
python .\QC_top.py 8

::#init pwr off
python .\QC_top.py 9
python .\rigol_dp832_ps.py
PAUSE
