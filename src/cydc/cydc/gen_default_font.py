#
# Choose Your Destiny.
#
# Copyright (C) 2024 Sergio Chico <cronomantic@gmail.com>
#
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# 
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#  

import sys
import os

from cydc_font import CydcFont

font = CydcFont()
chars = font.font_chars
n_chars = int(len(chars)/8)

for c in range(256-n_chars):
    chars += [0 for x in range(8)]

try:
    with open("default_charset.chr", "wb") as f:
        f.write(bytes(chars))
except OSError as err:
    sys.exit(f"{err}")
sys.exit(0)
