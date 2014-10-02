#!/bin/bash

pip install numpy
pip install scipy
pip install Cython
pip install numexpr
pip install tables
export CFLAGS=-I/usr/include/gdal
pip install GDAL==1.8.1
export CFLAGS=
pip install -r ga.renci.org.txt
