# Live Temperature Data Recorder

This project listens to meteorological station radio signals, decodes them and records the data in `history/`. Data from current day are updated every update interval and saved in `temp.out`.

## Prerequisites
1. This program makes use of the universal radio signal decoder `rtl-433` (https://github.com/merbanan/rtl_433). Currently supported are Realtek RTL2832 based DVB dongles.
2. Decoded data are processed via the Python script `temp_live.py`.
3. The Python script makes use of the non-standard library `pysolar` (https://pysolar.readthedocs.io/en/latest/) to calculate the position of the Sun.

## Runing the pipeline
1. Make sure you change permissions of `run.sh` to make it executable.
2. Run `run.sh`.

# Notes and modifications
1. `run.sh` essentially runs two infinite while-loops: the `rtl-433` receiver and decoder, and the `temp_live.py` script for plotting and saving. These processes detatch from the running terminal and so can only be killed via their `PID`, or with `killall python`.
2. If your weather station's signals adhere to a different protocol than `AlectoV1 Weather Sensor`, you need to swap the `-R` argument in `run.sh` with your device's working protocol, which you can find in `rtl-433`'s repository. In my case, I have added `-R -53` to prevent interfering signals from a soil moisture meter sending data in the same frequency.
3. For the signal updates, you need to change the hard-coded `time.sleep(151)` command in `temp_live.py` to your station's updating interval.
4. For the position of the Sun you need to change the hard-coded goegraphical coordinates in `temp_live.py` (37.9, 23.9) to your local ones.

# Credits
If you make use of this project (or part of it) please cite the link to this repository.
