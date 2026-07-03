import os
from typing import List, Optional


class Block:
    # __slots__ avoids a per-instance __dict__: the optimizer creates millions of
    # Block objects, so this cuts allocation cost and speeds up attribute access.
    __slots__ = ("chain", "bits", "index", "offset")

    def __init__(self, bits=None, index=None, offset=None, chain=None):
        self.chain = chain
        self.bits = bits
        self.index = index
        self.offset = offset


INITIAL_OFFSET = 1
MAX_SCALE = 50

# Compatibility switch. The default optimizer (``_optimize_fast``) is a
# byte-identical, faster reimplementation of the original reference optimizer
# (``_optimize_legacy``). Set the environment variable ``PYZX0_LEGACY=1`` (or flip
# this flag) to fall back to the original method should anything ever misbehave.
USE_LEGACY_OPTIMIZE = os.environ.get("PYZX0_LEGACY", "0") == "1"


def offset_ceiling(index, offset_limit):
    return offset_limit if index > offset_limit else (INITIAL_OFFSET if index < INITIAL_OFFSET else index)


def elias_gamma_needed_bits(value):
    bits = 1
    while value > 1:
        value >>= 1
        bits += 2
    return bits


def optimize(input_data, skip, offset_limit):
    """Find the optimal ZX0 parse.

    Dispatches to the fast optimizer by default, or to the legacy reference
    optimizer when ``USE_LEGACY_OPTIMIZE`` is set. Both return byte-identical
    results (guarded by tests); the legacy path is a safety fallback only.
    """
    if USE_LEGACY_OPTIMIZE:
        return _optimize_legacy(input_data, skip, offset_limit)
    return _optimize_fast(input_data, skip, offset_limit)


def _optimize_fast(input_data, skip, offset_limit):
    # Same algorithm as _optimize_legacy, with output-preserving speedups:
    #   - Elias-gamma bit counts served from a precomputed table (no per-iter call).
    #   - offset_ceiling inlined into the hot loop.
    #   - the current byte hoisted out of the inner offset loop.
    input_size = len(input_data)
    window_size = offset_ceiling(input_size - 1, offset_limit) + 1

    last_literal: List[Optional[Block]] = [None] * window_size
    last_match: List[Optional[Block]] = [None] * window_size
    match_length = [0] * window_size

    optimal = [None] * input_size
    best_length = [0] * input_size

    if input_size > 2:
        best_length[2] = 2

    last_match[INITIAL_OFFSET] = Block(-1, skip - 1, INITIAL_OFFSET, None)

    # Precompute Elias-gamma bit counts. Every value fed to elias_gamma_needed_bits
    # in the loop is in the range 1..input_size, so this table replaces the call.
    elias_bits = [0] * (input_size + 1)
    for v in range(1, input_size + 1):
        bits = 1
        w = v
        while w > 1:
            w >>= 1
            bits += 2
        elias_bits[v] = bits

    for index in range(skip, input_size):
        best_length_size = 2
        # inlined offset_ceiling(index, offset_limit)
        if index > offset_limit:
            max_offset = offset_limit
        elif index < INITIAL_OFFSET:
            max_offset = INITIAL_OFFSET
        else:
            max_offset = index
        cur = input_data[index]

        for offset in range(1, max_offset + 1):
            if index != skip and index >= offset and cur == input_data[index - offset]:
                current_literal = last_literal[offset]
                if current_literal is not None:
                    length = index - current_literal.index
                    bits = current_literal.bits + 1 + elias_bits[length]

                    last_match[offset] = Block(bits, index, offset, current_literal)

                    oi = optimal[index]
                    if not oi or oi.bits > bits:
                        optimal[index] = last_match[offset]

                match_length[offset] += 1
                ml = match_length[offset]

                if ml > 1:
                    if best_length_size < ml:
                        bits = (optimal[index - best_length[best_length_size]].bits +
                                elias_bits[best_length[best_length_size] - 1])

                        while True:
                            best_length_size += 1
                            bits2 = (optimal[index - best_length_size].bits +
                                     elias_bits[best_length_size - 1])
                            if bits2 <= bits:
                                best_length[best_length_size] = best_length_size
                                bits = bits2
                            else:
                                best_length[best_length_size] = best_length[best_length_size - 1]

                            if best_length_size >= ml:
                                break

                    length = best_length[ml]
                    bits = (optimal[index - length].bits + 8 +
                            elias_bits[(offset - 1) // 128 + 1] +
                            elias_bits[length - 1])
                    lm = last_match[offset]
                    if not lm or lm.index != index or lm.bits > bits:
                        last_match[offset] = Block(bits, index, offset, optimal[index - length])
                        oi = optimal[index]
                        if not oi or oi.bits > bits:
                            optimal[index] = last_match[offset]
            else:
                match_length[offset] = 0
                lm = last_match[offset]
                if lm:
                    length = index - lm.index
                    bits = lm.bits + 1 + elias_bits[length] + length * 8
                    last_literal[offset] = Block(bits, index, 0, lm)
                    oi = optimal[index]
                    if not oi or oi.bits > bits:
                        optimal[index] = last_literal[offset]

    return optimal[input_size - 1]


def _optimize_legacy(input_data, skip, offset_limit):
    # Original reference optimizer, kept verbatim as a compatibility fallback.
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
