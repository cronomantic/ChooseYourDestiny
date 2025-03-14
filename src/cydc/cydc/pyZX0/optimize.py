from typing import List, Optional


class Block:
    def __init__(self, bits=None, index=None, offset=None, chain=None):
        self.chain = chain
        self.bits = bits
        self.index = index
        self.offset = offset


INITIAL_OFFSET = 1
MAX_SCALE = 50


def offset_ceiling(index, offset_limit):
    return offset_limit if index > offset_limit else (INITIAL_OFFSET if index < INITIAL_OFFSET else index)


def elias_gamma_needed_bits(value):
    bits = 1
    while value > 1:
        value >>= 1
        bits += 2
    return bits


def optimize(input_data, skip, offset_limit):
    # The algorithm has a floating window of size window_size describing the previous chain of matches
    input_size = len(input_data)
    window_size = offset_ceiling(input_size - 1, offset_limit) + 1

    last_literal: List[Optional[Block]] = [None] * window_size
    last_match: List[Optional[Block]] = [None] * window_size
    match_length = [0] * window_size

    # The algorithm is looking for the best match for each index of the input data
    optimal = [None] * input_size
    best_length = [0] * input_size

    if input_size > 2:
        best_length[2] = 2

    # Kickstart the algorithm by assigning a fake block
    last_match[INITIAL_OFFSET] = Block(-1, skip - 1, INITIAL_OFFSET, None)

    # The algorithm is checking for the best match for each index of the input data (skipping the skip part)
    for index in range(skip, input_size):
        best_length_size = 2  # It's useless to check for a match of length 1
        max_offset = offset_ceiling(index, offset_limit)

        for offset in range(1, max_offset + 1):
            # Checking for a match in the previous part of the input data, backwards
            if index != skip and index >= offset and input_data[index] == input_data[index - offset]:
                current_literal = last_literal[offset]
                if current_literal is not None:
                    length = index - current_literal.index
                    bits = current_literal.bits + 1 + elias_gamma_needed_bits(length)

                    # Chain the current match to the previous literal
                    last_match[offset] = Block(bits, index, offset, current_literal)

                    # Update the best match
                    if not optimal[index] or optimal[index].bits > bits:
                        optimal[index] = last_match[offset]

                match_length[offset] += 1

                if match_length[offset] > 1:
                    if best_length_size < match_length[offset]:
                        bits = (optimal[index - best_length[best_length_size]].bits +
                                elias_gamma_needed_bits(best_length[best_length_size] - 1))

                        while True:
                            best_length_size += 1
                            bits2 = (optimal[index - best_length_size].bits +
                                     elias_gamma_needed_bits(best_length_size - 1))
                            if bits2 <= bits:
                                best_length[best_length_size] = best_length_size
                                bits = bits2
                            else:
                                best_length[best_length_size] = best_length[best_length_size - 1]

                            if best_length_size >= match_length[offset]:
                                break

                    length = best_length[match_length[offset]]
                    bits = (optimal[index - length].bits + 8 +
                            elias_gamma_needed_bits((offset - 1) // 128 + 1) +
                            elias_gamma_needed_bits(length - 1))
                    if not last_match[offset] or last_match[offset].index != index or last_match[offset].bits > bits:
                        last_match[offset] = Block(bits, index, offset, optimal[index - length])
                        if not optimal[index] or optimal[index].bits > bits:
                            optimal[index] = last_match[offset]
            else:
                match_length[offset] = 0  # Resetting the match length
                if last_match[offset]:
                    length = index - last_match[offset].index
                    bits = last_match[offset].bits + 1 + elias_gamma_needed_bits(length) + length * 8
                    last_literal[offset] = Block(bits, index, 0, last_match[offset])
                    if not optimal[index] or optimal[index].bits > bits:
                        optimal[index] = last_literal[offset]

    return optimal[input_size - 1]
