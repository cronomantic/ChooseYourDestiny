#!/usr/bin/python3

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'cydc'))

from cydc import cli

if __name__ == '__main__':
    cli()
