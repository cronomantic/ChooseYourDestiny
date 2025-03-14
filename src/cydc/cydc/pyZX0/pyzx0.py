import argparse
import os

from compress import compress_data


class ApplicationError(Exception):
    pass


def read_input_file(input_name, skip):
    try:
        with open(input_name, "rb") as ifp:
            # determine input size
            ifp.seek(0, os.SEEK_END)
            input_size = ifp.tell()
            ifp.seek(0, os.SEEK_SET)

            if input_size == 0:
                raise ApplicationError("Empty input file")

            if skip >= input_size:
                raise ApplicationError("Skip value exceeds input file size")

            input_data = bytearray(input_size)
            read_count = ifp.readinto(input_data)

            if read_count != input_size:
                raise ApplicationError("Cannot read input file")

    except FileNotFoundError:
        print(f"Error: Cannot access input file {input_name}")
        exit(1)
    except ApplicationError as e:
        print(f"Error: {e}")
        exit(1)
    return input_data


def write_output_file(output_name, output_data):
    with open(output_name, "wb") as ofp:
        ofp.write(output_data)
        ofp.close()


def write_summary(backwards_mode, delta, input_data, output_data, skip):
    text_backwards = " backwards" if backwards_mode else ""
    initial_size = len(input_data) - skip
    output_size = len(output_data)
    print(
        f"File compressed{text_backwards} from {initial_size} to {output_size} bytes! (delta {delta})")


def main():
    parser = argparse.ArgumentParser(
        description='pyZX0 v2.2: Python port of ZX0 compressor by Einar Saukas for the same version.')
    parser.add_argument('-f', action='store_true', help='Force overwrite of output file', dest='forced_mode')
    parser.add_argument('-c', action='store_true', help='Classic file format (v1.*)', dest='classic_mode')
    parser.add_argument('-b', action='store_true', help='Compress backwards', dest='backwards_mode')
    parser.add_argument('-q', action='store_true', help='Quick non-optimal compression', dest='quick_mode')
    parser.add_argument('-s', type=int, help='Skip first N bytes of input file', dest='skip')
    parser.add_argument('input_name', type=str, help='Input file')
    parser.add_argument('output_name', type=str, nargs='?', help='Output file')

    args = parser.parse_args()

    forced_mode = args.forced_mode
    classic_mode = args.classic_mode
    backwards_mode = args.backwards_mode
    quick_mode = args.quick_mode
    skip = args.skip if args.skip else 0
    output_name = args.output_name if args.output_name else args.input_name + ".zx0"

    input_data = read_input_file(args.input_name, skip)

    if not forced_mode and os.path.exists(output_name):
        raise ApplicationError(f"Already existing output file {output_name}")

    output_data, delta = compress_data(input_data, skip, backwards_mode, classic_mode, quick_mode)

    write_output_file(output_name, output_data)
    write_summary(backwards_mode, delta, input_data, output_data, skip)

    return 0


if __name__ == "__main__":
    main()
