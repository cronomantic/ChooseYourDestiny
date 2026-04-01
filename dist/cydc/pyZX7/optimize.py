from dataclasses import dataclass

MAX_OFFSET = 2176
MAX_LEN = 65536


@dataclass
class Optimal:
    bits: int
    offset: int = 0
    length: int = 0


def _elias_gamma_bits(value: int) -> int:
    bits = 1
    while value > 1:
        bits += 2
        value >>= 1
    return bits


def _count_bits(offset: int, length: int) -> int:
    return 1 + (12 if offset > 128 else 8) + _elias_gamma_bits(length - 1)


def optimize(input_data: bytes | bytearray) -> list[Optimal]:
    input_size = len(input_data)
    if input_size == 0:
        return []

    min_match = [0] * (MAX_OFFSET + 1)
    max_match = [0] * (MAX_OFFSET + 1)

    # Hash chains indexed by the last two bytes.
    match_heads = [-1] * (256 * 256)
    match_next = [-1] * input_size

    optimal = [Optimal(bits=0) for _ in range(input_size)]
    optimal[0].bits = 8  # First byte is always literal.

    for i in range(1, input_size):
        optimal[i].bits = optimal[i - 1].bits + 9
        match_index = (input_data[i - 1] << 8) | input_data[i]

        best_len = 1
        prev = -1
        node = match_heads[match_index]

        while node != -1 and best_len < MAX_LEN:
            offset = i - node
            if offset > MAX_OFFSET:
                if prev == -1:
                    match_heads[match_index] = -1
                else:
                    match_next[prev] = -1
                break

            length = 2
            while length <= MAX_LEN:
                if length > best_len:
                    best_len = length
                    bits = optimal[i - length].bits + _count_bits(offset, length)
                    if bits < optimal[i].bits:
                        optimal[i].bits = bits
                        optimal[i].offset = offset
                        optimal[i].length = length
                elif i + 1 == max_match[offset] + length and max_match[offset] != 0:
                    length = i - min_match[offset]
                    if length > best_len:
                        length = best_len

                if i < offset + length or input_data[i - length] != input_data[i - length - offset]:
                    break
                length += 1

            min_match[offset] = i + 1 - length
            max_match[offset] = i

            prev = node
            node = match_next[node]

        match_next[i] = match_heads[match_index]
        match_heads[match_index] = i

    return optimal
