
#include "symmetry.h"
#include <stdio.h>

#define BYTE_TO_BINARY_PATTERN "%c%c%c%c%c%c%c%c"
#define BYTE_TO_BINARY(byte)       \
    ((byte)&0x80 ? '1' : '0'),     \
        ((byte)&0x40 ? '1' : '0'), \
        ((byte)&0x20 ? '1' : '0'), \
        ((byte)&0x10 ? '1' : '0'), \
        ((byte)&0x08 ? '1' : '0'), \
        ((byte)&0x04 ? '1' : '0'), \
        ((byte)&0x02 ? '1' : '0'), \
        ((byte)&0x01 ? '1' : '0')

bool is_symmetric_bytes(uint8_t bpn, uint8_t bpr, uint8_t ban, uint8_t bar)
{
    int i;
    uint8_t col_n, col_r;

    for (i = 0; i < 8; i++)
    {
        if (bpn & 0x80)
        {
            col_n = ban & 0xc7;
        }
        else
        {
            col_n = ban & 0xc0;
            col_n |= ((ban >> 3) & 0x07);
        }
        if (bpr & 0x01)
        {
            col_r = bar & 0xc7;
        }
        else
        {
            col_r = bar & 0xc0;
            col_r |= ((bar >> 3) & 0x07);
        }

        // If the color is 0, ignore BRIGHT bit
        if ((col_n & 0x07) == 0)
            col_n &= 0x87;

        if ((col_r & 0x07) == 0)
            col_r &= 0x87;

        // printf("--  bpn=%x, bpr=%x col_n=%x col_r=%d\n", bpn, bpr, col_n, col_r);

        if (col_n != col_r)
            return false;

        bpn = bpn << 1;
        bpr = bpr >> 1;
    }
    return true;
}

bool is_symmetric(uint8_t num_lines_scr, uint8_t num_lines_att, uint8_t *screen)
{
    int sector;
    int row;
    int char_row;
    int col;
    int pxl_idx, att_idx;
    uint8_t pn, pr, an, ar;
    int line_cnt, att_cnt;

    line_cnt = 0;
    att_cnt = 0;

    /* transform bitmap area */
    for (sector = 0; sector < 3; sector++)
    {
        for (row = 0; row < 8; row++)
        {
            for (char_row = 0; char_row < 8; char_row++)
            {
                pxl_idx = (((((sector << 3) + char_row) << 3) + row) << 5);
                att_idx = (((sector << 3) + row) << 5) + (32 * 192);
                if (line_cnt < num_lines_scr && att_cnt < num_lines_att)
                {
                    for (col = 0; col < 16; col++)
                    {
                        pn = screen[pxl_idx + col];
                        pr = screen[pxl_idx + (31 - col)];
                        an = screen[att_idx + col];
                        ar = screen[att_idx + (31 - col)];
                        // printf("- pxl_idx=%x att_idx=%x pn=%x, pr=%x an=%x ar=%d\n", pxl_idx, att_idx, pn, pr, an, ar);
                        if (!is_symmetric_bytes(pn, pr, an, ar))
                            return false;
                    }
                }
                line_cnt++;
            }
            att_cnt++;
        }
    }

    return true;
}
