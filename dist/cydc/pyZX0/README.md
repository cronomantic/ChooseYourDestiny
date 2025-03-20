ZX0 compressor for Python
=========================

ZX0 compressor for Python is an implementation of the [ZX0](https://github.com/einar-saukas/ZX0) compression algorithm
in Python.

I needed a Python implementation of ZX0 for simplicity reasons on the build chain I use
for a project. Also as an exersice.

The code is heavily based on the original ZX0 C code.
It is also not optimized for speed at all, contrary to the original ZX0 C code.

Usage:

```
> python3 pyzx0.py -h
usage: pyzx0.py [-h] [-f] [-c] [-b] [-q] [-s SKIP] input_name [output_name]

pyZX0 v2.2: Python port of ZX0 compressor by Einar Saukas for the same version.

positional arguments:
  input_name   Input file
  output_name  Output file

options:
  -h, --help   show this help message and exit
  -f           Force overwrite of output file
  -c           Classic file format (v1.*)
  -b           Compress backwards
  -q           Quick non-optimal compression
  -s SKIP      Skip first N bytes of input file
```
