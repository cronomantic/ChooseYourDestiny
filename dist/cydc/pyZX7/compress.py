from pyZX7.optimize import optimize


class BitWriter:
    def __init__(self):
        self.output = bytearray()
        self.bit_index = 0
        self.bit_mask = 0

    def write_byte(self, value: int):
        self.output.append(value & 0xFF)

    def write_bit(self, value: int):
        if self.bit_mask == 0:
            self.bit_mask = 0x80
            self.bit_index = len(self.output)
            self.write_byte(0)
        if value:
            self.output[self.bit_index] |= self.bit_mask
        self.bit_mask >>= 1

    def write_elias_gamma(self, value: int):
        i = 2
        while i <= value:
            self.write_bit(0)
            i <<= 1
        i >>= 1
        while i > 0:
            self.write_bit(1 if (value & i) else 0)
            i >>= 1


def compress(input_data: bytes | bytearray) -> bytearray:
    input_size = len(input_data)
    if input_size == 0:
        return bytearray()

    optimal = optimize(input_data)

    # Build the forward decision chain from index 0 to the end.
    next_index = [0] * input_size
    input_index = input_size - 1
    while input_index > 0:
        length = optimal[input_index].length if optimal[input_index].length > 0 else 1
        input_prev = input_index - length
        next_index[input_prev] = input_index
        input_index = input_prev

    writer = BitWriter()

    # First byte is always literal.
    writer.write_byte(input_data[0])

    input_index = 0
    while True:
        input_index = next_index[input_index]
        if input_index <= 0:
            break

        node = optimal[input_index]
        if node.length == 0:
            writer.write_bit(0)
            writer.write_byte(input_data[input_index])
            continue

        writer.write_bit(1)
        writer.write_elias_gamma(node.length - 1)

        offset1 = node.offset - 1
        if offset1 < 128:
            writer.write_byte(offset1)
        else:
            offset1 -= 128
            writer.write_byte((offset1 & 0x7F) | 0x80)
            mask = 1024
            while mask > 127:
                writer.write_bit(1 if (offset1 & mask) else 0)
                mask >>= 1

    # End marker (> MAX_LEN): sequence indicator + gamma(65536).
    writer.write_bit(1)
    for _ in range(16):
        writer.write_bit(0)
    writer.write_bit(1)

    return writer.output


def compress_data(input_data: bytes | bytearray):
    return compress(input_data)
