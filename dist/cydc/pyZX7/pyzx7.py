import argparse
import os

from compress import compress_data


def main():
    parser = argparse.ArgumentParser(
        description="pyZX7: Python ZX7 compressor by Einar Saukas"
    )
    parser.add_argument("input_name", type=str, help="Input file")
    parser.add_argument("output_name", type=str, nargs="?", help="Output file")
    args = parser.parse_args()

    output_name = args.output_name if args.output_name else args.input_name + ".zx7"

    with open(args.input_name, "rb") as ifp:
        input_data = ifp.read()

    output_data = compress_data(input_data)

    if os.path.exists(output_name):
        os.remove(output_name)
    with open(output_name, "wb") as ofp:
        ofp.write(output_data)

    print(f"File converted from {len(input_data)} to {len(output_data)} bytes")


if __name__ == "__main__":
    main()
