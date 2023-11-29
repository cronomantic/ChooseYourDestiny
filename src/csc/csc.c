#include "cargs.h"
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

#include "zx0.h"
#include "symmetry.h"

#define VERSION "0.1"

#define MAX_OFFSET_ZX0 32640
#define MAX_SIZE 6912
#define SECTOR1 2048
#define ATTRIB1 768

unsigned char input_data[MAX_SIZE + 1];
unsigned char screen_data[(MAX_SIZE - ATTRIB1)];
unsigned char att_data[ATTRIB1];

void convert(uint8_t num_lines_scr, uint8_t num_lines_att, uint8_t mirror_mode)
{
    int sector;
    int row;
    int char_row;
    int col;
    int i, j, idx;
    uint8_t line_cnt;

    i = 0;
    j = 0;
    line_cnt = 0;

    /* transform bitmap area */
    for (sector = 0; sector < 3; sector++)
    {
        for (row = 0; row < 8; row++)
        {
            for (char_row = 0; char_row < 8; char_row++)
            {
                for (col = 0; col < 32; col++)
                {
                    if ((col >= 16 && mirror_mode) || (line_cnt >= num_lines_scr))
                    {
                        screen_data[i++] = 0;
                    }
                    else
                    {
                        idx = (((((sector << 3) + char_row) << 3) + row) << 5) + col;
                        screen_data[i++] = input_data[idx];
                    }
                }
            }
        }
    }

    /* just copy attributes */
    for (row = 0; row < 24; row++)
    {
        for (col = 0; col < 32; col++)
        {
            if ((col >= 16 && mirror_mode) || (row >= num_lines_att))
            {
                att_data[j++] = 0;
                i++;
            }
            else
            {
                att_data[j++] = input_data[i++];
            }
        }
    }
}

bool is_little_endian()
{
    short int number = 0x1;
    char *numPtr = (char *)&number;
    return (numPtr[0] == 1);
}

uint16_t swap_uint16(uint16_t val)
{
    return (val << 8) | (val >> 8);
}

void strip_ext(char *fname)
{
    char *end = fname + strlen(fname);

    while (end > fname && *end != '.' && *end != '\\' && *end != '/')
    {
        --end;
    }
    if ((end > fname && *end == '.') &&
        (*(end - 1) != '\\' && *(end - 1) != '/'))
    {
        *end = '\0';
    }
}

/**
 * This is the main configuration of all options available.
 */
static struct cag_option options[] = {
    {.identifier = 'f',
     .access_letters = "f",
     .access_name = "force",
     .description = "Force overwrite of output file"},

    {.identifier = 'm',
     .access_letters = "m",
     .access_name = "mirror",
     .description = "The right side of the image is the reflection of the left one."},

    {.identifier = 'o',
     .access_letters = "o",
     .access_name = "output",
     .value_name = "FILE",
     .description = "Output path for the file"},

    {.identifier = 'l',
     .access_letters = "l",
     .access_name = "num-lines",
     .value_name = "NUMBER",
     .description = "Number of visible lines"},

    {.identifier = 'h',
     .access_letters = "h",
     .access_name = "help",
     .description = "Shows the command help"}};

struct options
{
    bool forced_mode;
    bool mirror_mode;
    int num_lines;
    const char *input;
    const char *output;
};

int main(int argc, char *argv[])
{
    char identifier;
    const char *value;
    cag_option_context context;
    struct options config = {FALSE, FALSE, 0, NULL, NULL};
    int param_index;
    char *output_name = NULL;
    unsigned char *output_data_scr;
    unsigned char *output_data_att;
    size_t input_size;
    size_t bytes_read;
    int output_size_scr;
    int output_size_att;
    uint16_t scr_size;
    uint8_t num_lines_scr;
    uint8_t num_lines_att;
    FILE *ifp;
    FILE *ofp;
    int delta_scr;
    int delta_att;
    int i;

    /**
     * Now we just prepare the context and iterate over all options. Simple!
     */
    cag_option_prepare(&context, options, CAG_ARRAY_SIZE(options), argc, argv);
    while (cag_option_fetch(&context))
    {
        identifier = cag_option_get(&context);
        switch (identifier)
        {
        case 'f':
            config.forced_mode = true;
            break;
        case 'm':
            config.mirror_mode = true;
            break;
        case 'l':
            value = cag_option_get_value(&context);
            config.num_lines = atoi(value);
            break;
        case 'o':
            value = cag_option_get_value(&context);
            config.output = value;
            break;
        case 'h':
            printf("CSC v%s: CYD Screen Compressor by Cronomantic\n", VERSION);
            printf("          Based on ZX0 v2.2 by Einar Saukas\n\n");
            printf(" Usage: CSC [-f] [-m] [-l=num_lines] [-o=output] input\n");
            cag_option_print(options, CAG_ARRAY_SIZE(options), stdout);
            return EXIT_SUCCESS;
        }
    }

    i = 0;
    for (param_index = context.index; param_index < argc; ++param_index)
    {
        if (i == 0)
            config.input = argv[param_index];
        i++;
    }

    if (i == 0)
    {
        fprintf(stderr, "Error: Input file not specified \n");
        return EXIT_FAILURE;
    }

    if (i > 1)
    {
        fprintf(stderr, "Error: Too many parameters\n");
        return EXIT_FAILURE;
    }

    if (config.output == NULL)
    {
        output_name = (char *)malloc(strlen(config.input) + 5);
        strcpy(output_name, config.input);
        strip_ext(output_name);
        strcat(output_name, ".csc");
    }
    else
    {
        output_name = (char *)malloc(strlen(config.output) + 1);
        strcpy(output_name, config.output);
    }

    if (config.num_lines < 0 || config.num_lines > 192)
    {
        fprintf(stderr, "Error: Invalid number of lines\n");
        return EXIT_FAILURE;
    }
    else if (config.num_lines == 0)
    {
        config.num_lines = 192;
    }

    num_lines_scr = (uint8_t)(config.num_lines);
    num_lines_att = (uint8_t)(config.num_lines >> 3);

    if (config.num_lines & 0x7)
        num_lines_att++;

    /* check output file */
    if (!config.forced_mode && fopen(output_name, "rb") != NULL)
    {
        fprintf(stderr, "Error: Already existing output file %s\n", output_name);
        return EXIT_FAILURE;
    }

    /* open input file */
    ifp = fopen(config.input, "rb");
    if (!ifp)
    {
        fprintf(stderr, "Error: Cannot access input file %s\n", config.input);
        return EXIT_FAILURE;
    }

    /* read input file */
    input_size = 0;
    while ((bytes_read = fread(input_data + input_size, sizeof(char), ((MAX_SIZE + 1) - input_size), ifp)) > 0)
    {
        input_size += bytes_read;
    }

    /* close input file */
    fclose(ifp);

    if (input_size == MAX_SIZE)
    {
        printf("Converting screen data...\n");
        if (!config.mirror_mode)
        {
            config.mirror_mode = is_symmetric(num_lines_scr, num_lines_att, input_data);
            if (config.mirror_mode)
                printf("Symmetric image detected! Enabling mirror mode.\n");
        }
        convert(num_lines_scr, num_lines_att, config.mirror_mode);
    }
    else
    {
        fprintf(stderr, "Error: Invalid input file %s\n", config.input);
        return EXIT_FAILURE;
    }

    /* create output file */
    ofp = fopen(output_name, "wb");
    if (!ofp)
    {
        fprintf(stderr, "Error: Cannot create output file %s\n", output_name);
        return EXIT_FAILURE;
    }

    /* generate output file */
    output_data_scr = compress(optimize(&(screen_data[0]), (num_lines_scr * 32), 0, MAX_OFFSET_ZX0), &(screen_data[0]), (num_lines_scr * 32), 0, FALSE, TRUE, &output_size_scr, &delta_scr);
    printf("Pixel data compressed from %d to %d bytes! (delta %d)\n", (num_lines_scr * 32), output_size_scr, delta_scr);

    output_data_att = compress(optimize(&(att_data[0]), (num_lines_att * 32), 0, MAX_OFFSET_ZX0), &(att_data[0]), (num_lines_att * 32), 0, FALSE, TRUE, &output_size_att, &delta_att);
    printf("Attributes compressed from %d to %d bytes! (delta %d)\n", (num_lines_att * 32), output_size_att, delta_att);

    scr_size = (uint16_t)(output_size_scr + output_size_att + 2);

    if (!is_little_endian())
    {
        scr_size = swap_uint16(scr_size);
    }

    if (fwrite(&scr_size, sizeof(char), 2, ofp) != 2)
    {
        fprintf(stderr, "Error: Cannot write output file %s\n", output_name);
        fclose(ofp);
        free(output_name);
        return EXIT_FAILURE;
    }

    if (fwrite(&num_lines_scr, sizeof(char), 1, ofp) != 1)
    {
        fprintf(stderr, "Error: Cannot write output file %s\n", output_name);
        fclose(ofp);
        free(output_name);
        return EXIT_FAILURE;
    }

    if (config.mirror_mode)
    {
        // Using MSB of the att size to tell if it is mirrored
        num_lines_att |= 0x80;
    }

    if (fwrite(&num_lines_att, sizeof(char), 1, ofp) != 1)
    {
        fprintf(stderr, "Error: Cannot write output file %s\n", output_name);
        fclose(ofp);
        free(output_name);
        return EXIT_FAILURE;
    }

    /* write output file */
    if (fwrite(output_data_scr, sizeof(char), output_size_scr, ofp) != output_size_scr)
    {
        fprintf(stderr, "Error: Cannot write output file %s\n", output_name);
        fclose(ofp);
        free(output_name);
        return EXIT_FAILURE;
    }

    /* write output file */
    if (fwrite(output_data_att, sizeof(char), output_size_att, ofp) != output_size_att)
    {
        fprintf(stderr, "Error: Cannot write output file %s\n", output_name);
        fclose(ofp);
        free(output_name);
        return EXIT_FAILURE;
    }

    /* close output file */
    fclose(ofp);
    free(output_name);

    return EXIT_SUCCESS;
}
