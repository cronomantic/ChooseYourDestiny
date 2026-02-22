from pyZX0.optimize import INITIAL_OFFSET, optimize

MAX_OFFSET_ZX0 = 32640
MAX_OFFSET_ZX7 = 2176


class CompressStream:
    def __init__(self, optimal, input_size, skip, backwards_mode):
        output_size = (optimal.bits + 25) // 8
        self.output_data = bytearray(output_size)

        self.backwards_mode = backwards_mode
        self.input_index = skip
        self.output_index = 0

        self.diff = output_size - input_size + skip
        self.bit_mask = 0
        self.bit_index = 0
        self.backtrack = True

        self.delta = 0

    def read_bytes(self, n):
        self.input_index += n
        self.diff += n
        if self.delta < self.diff:
            self.delta = self.diff

    def write_byte(self, value):
        self.output_data[self.output_index] = value
        self.output_index += 1
        self.diff -= 1

    def write_bit(self, value):
        if self.backtrack:
            if value:
                self.output_data[self.output_index - 1] |= 1
            self.backtrack = False
        else:
            if not self.bit_mask:
                self.bit_mask = 128
                self.bit_index = self.output_index
                self.write_byte(0)
            if value:
                self.output_data[self.bit_index] |= self.bit_mask
            self.bit_mask >>= 1

    def write_interlaced_elias_gamma(self, value, invert_mode):
        i = 2
        while i <= value:
            i <<= 1
        i >>= 1
        while i > 1:
            i >>= 1
            self.write_bit(self.backwards_mode)
            self.write_bit(not (value & i) if invert_mode else (value & i))
        self.write_bit(not self.backwards_mode)

    def set_backtrack(self):
        self.backtrack = True


def reverse_chain(optimal):
    previous_block = None
    while optimal:
        next_block = optimal.chain
        optimal.chain = previous_block
        previous_block = optimal
        optimal = next_block
    return previous_block


def compress(optimal, input_data, skip, backwards_mode, invert_mode):
    # Reverse the chain
    prev = reverse_chain(optimal)

    stream = CompressStream(optimal, len(input_data), skip, backwards_mode)

    last_offset = INITIAL_OFFSET

    optimal = prev.chain  # Skip the fake block
    while optimal:
        length = optimal.index - prev.index

        if optimal.offset == 0:
            stream.write_bit(0)  # Literal indicator
            stream.write_interlaced_elias_gamma(length, False)  # Length
            for i in range(length):  # Copy literal values
                stream.write_byte(input_data[stream.input_index])
                stream.read_bytes(1)
        elif optimal.offset == last_offset:
            stream.write_bit(0)  # Copy from last offset
            stream.write_interlaced_elias_gamma(length, False)  # Length
            stream.read_bytes(length)  # Advance the input index without writing on the output
        else:
            optimal_offset = optimal.offset - 1

            stream.write_bit(1)  # Copy from a new offset
            stream.write_interlaced_elias_gamma(optimal_offset // 128 + 1, invert_mode)  # MSB
            if backwards_mode:
                stream.write_byte((optimal_offset % 128) << 1)  # LSB (backwards)
            else:
                stream.write_byte((127 - optimal_offset % 128) << 1)  # LSB

            # Copy length bytes from the offset
            stream.set_backtrack()  # To use the last bit of the previous byte
            stream.write_interlaced_elias_gamma(length - 1, False)
            stream.read_bytes(length)
            last_offset = optimal.offset

        prev = optimal
        optimal = optimal.chain

    stream.write_bit(1)
    stream.write_interlaced_elias_gamma(256, invert_mode)

    return stream.output_data, stream.delta


def compress_data(input_data, skip, backwards_mode, classic_mode, quick_mode):
    if backwards_mode:
        input_data = input_data[::-1]

    optimized_data = optimize(input_data, skip, MAX_OFFSET_ZX7 if quick_mode else MAX_OFFSET_ZX0)
    output_data, delta = compress(optimized_data, input_data, skip, backwards_mode,
                                  not classic_mode and not backwards_mode)
    if backwards_mode:
        output_data = output_data[::-1]

    return output_data, delta
