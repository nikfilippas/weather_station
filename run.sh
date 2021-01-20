#!/bin/bash
rtl_433 -f 433.713M -R -53 -F json:temp.out &
/home/nick/anaconda3/bin/python temp_live.py &
