import sys
import os
import json

try:
    with open("new_charset.json", "r") as f:
        charset_string = f.read()
except OSError as err:
    sys.exit(f"{err}")

charset = json.loads(charset_string)

charset_p = []
charset_w = []
for char in charset:
    charset_p += char['Character']
    charset_w.append(char['Width'])

str_c = ""
for i, char in enumerate(charset_p):
    if (i % 8) == 0:
        if i != 0:
            str_c += "\n"
        str_c += "        "
    str_c += f"0x{char:02X},"
    
print(str_c)

str_w = ""
for i, w in enumerate(charset_w):
    if (i % 16) == 0:
        if i != 0:
            str_w += "\n"
        str_w += "        "
    str_w += f"{w},"

print(str_w)

