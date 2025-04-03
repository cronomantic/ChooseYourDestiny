#
# MIT License
#
# Copyright (c) 2025 Sergio Chico
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#



from pyZX0.compress import compress_data


class ScreenCompress(object):

    MAX_OFFSET_ZX0 = 32640
    MAX_SIZE = 6912
    SECTOR1 = 2048
    ATTRIB1 = 768

    def __init__(self, scr_data):
        self.input_data = bytearray(scr_data[0:self.MAX_SIZE])
        self.screen_data = bytearray(self.MAX_SIZE - self.ATTRIB1)
        self.att_data = bytearray(self.ATTRIB1)

    def convert_to_CSC(self, num_lines=192, force_mirror=False):
        txt = ""
        num_lines_scr = num_lines
        num_lines_att = num_lines >> 3
        if (num_lines & 0x7) > 0:
            num_lines_att += 1

        if force_mirror:
            mirror_mode = True
        else:
            mirror_mode = self.__is_symmetric(
                num_lines_scr=num_lines_scr, num_lines_att=num_lines_att
            )
            if mirror_mode:
                txt += "Symmetric image detected! Enabling mirror mode.\n"

        self.__convert_scr(
            num_lines_scr=num_lines_scr,
            num_lines_att=num_lines_att,
            mirror_mode=mirror_mode,
        )

        scr_zx0, scr_delta = compress_data(self.screen_data, False, False, False, False)
        scr_zx0 = list(scr_zx0)
        txt += f"Pixel data compressed from {num_lines_scr*32} to {len(scr_zx0)} bytes! (delta {scr_delta})\n"

        att_zx0, att_delta = compress_data(self.att_data, False, False, False, False)
        att_zx0 = list(att_zx0)
        txt += f"Attributes compressed from {num_lines_att*32} to {len(att_zx0)} bytes! (delta {att_delta})\n"

        filesize = len(scr_zx0) + len(att_zx0) + 2
        num_lines_scr &= 0xFF
        num_lines_att &= 0xFF
        if mirror_mode:
            num_lines_att |= 0x80
        csc = [(filesize & 0xFF), ((filesize >> 8) & 0xFF)]
        csc.append(num_lines_scr)
        csc.append(num_lines_att)
        csc += scr_zx0
        csc += att_zx0

        return (csc, txt)

    def __convert_scr(self, num_lines_scr=192, num_lines_att=32, mirror_mode=False):
        sector = 0
        row = 0
        char_row = 0
        col = 0
        i = 0
        j = 0
        line_cnt = 0

        # transform bitmap area
        for sector in range(3):
            for row in range(8):
                for char_row in range(8):
                    for col in range(32):
                        if (col >= 16 and mirror_mode) or (line_cnt >= num_lines_scr):
                            self.screen_data[i] = 0
                            i += 1
                        else:
                            idx = (((((sector << 3) + char_row) << 3) + row) << 5) + col
                            self.screen_data[i] = self.input_data[idx]
                            i += 1

        # just copy attributes
        for row in range(24):
            for col in range(32):
                if (col >= 16 and mirror_mode) or (row >= num_lines_att):
                    self.att_data[j] = 0
                    j += 1
                    i += 1
                else:
                    self.att_data[j] = self.input_data[i]
                    j += 1
                    i += 1

    def __is_symmetric_bytes(self, bpn, bpr, ban, bar):
        for i in range(8):
            if bpn & 0x80:
                col_n = ban & 0xC7
            else:
                col_n = ban & 0xC0
                col_n |= (ban >> 3) & 0x07

            if bpr & 0x01:
                col_r = bar & 0xC7
            else:
                col_r = bar & 0xC0
                col_r |= (bar >> 3) & 0x07

            if (col_n & 0x07) == 0:
                col_n &= 0x87

            if (col_r & 0x07) == 0:
                col_r &= 0x87

            if col_n != col_r:
                return False

            bpn <<= 1
            bpr >>= 1
        return True

    def __is_symmetric(self, num_lines_scr=192, num_lines_att=32):
        line_cnt = 0
        att_cnt = 0

        # transform bitmap area
        for sector in range(3):
            for row in range(8):
                for char_row in range(8):
                    pxl_idx = (((sector << 3) + char_row) << 3) + row << 5
                    att_idx = (((sector << 3) + row) << 5) + (32 * 192)
                    if line_cnt < num_lines_scr and att_cnt < num_lines_att:
                        for col in range(16):
                            pn = self.input_data[pxl_idx + col]
                            pr = self.input_data[pxl_idx + (31 - col)]
                            an = self.input_data[att_idx + col]
                            ar = self.input_data[att_idx + (31 - col)]
                            if not self.__is_symmetric_bytes(pn, pr, an, ar):
                                return False
                    line_cnt += 1
                att_cnt += 1

        return True
