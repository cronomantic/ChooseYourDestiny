# -- coding: utf-8 -*-
#
# Choose Your Destiny.
#
# Copyright (C) 2024 Sergio Chico <cronomantic@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# Based on:
# DAAD Reborn Tokenizer
# Copyright (C) 2010, 2013, 2018-2020, 2022 José Manuel Ferrer Ortiz


import os
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from concurrent.futures.process import BrokenProcessPool

try:
    import progressbar

    pbarAvailable = True
except ImportError:
    pbarAvailable = False


NUM_TOKENS = 128

# Below this many characters of text the token search is quick and starting
# worker processes would cost more than it saves.
PARALLEL_MIN_CHARS = 1000


class _NoTranslation:
    @staticmethod
    def gettext(s):
        return s


def _generate_worker(job):
    """One run of the token search for a given maximum token length. Module
    level so worker processes can unpickle it."""
    strings, max_len_token, num_tokens, superset_limit = job
    compressor = CydcTextCompressor(_NoTranslation, superset_limit)
    compressor.num_tokens = num_tokens
    return max_len_token, compressor._generate_tokens(strings, max_len_token)


class _Sized:
    """Iterable with a known length, for the progress bar."""

    def __init__(self, iterable, length):
        self.iterable, self.length = iterable, length

    def __iter__(self):
        return iter(self.iterable)

    def __len__(self):
        return self.length


def optimal_parse(text, tokens):
    """Encode text as the fewest codes: each code is a literal character or
    the index of a token (128 + i) covering len(token) characters. The Z80
    decoder expands any such sequence, so this only picks the best one."""
    by_prefix = {}
    for i, token in enumerate(tokens):
        if token:
            by_prefix.setdefault(token[:2], []).append((token, i))
    n = len(text)
    cost = [0] * (n + 1)
    choice = [None] * (n + 1)
    for pos in range(n - 1, -1, -1):
        cost[pos] = cost[pos + 1] + 1
        for token, i in by_prefix.get(text[pos : pos + 2], ()):
            end = pos + len(token)
            if end <= n and cost[end] + 1 < cost[pos] and text.startswith(token, pos):
                cost[pos] = cost[end] + 1
                choice[pos] = i
    codes = []
    pos = 0
    while pos < n:
        i = choice[pos]
        if i is None:
            codes.append(ord(text[pos]))
            pos += 1
        else:
            codes.append(128 + i)
            pos += len(tokens[i])
    return codes


class CydcTextCompressor(object):
    def __init__(self, gettext, superset_limit, verbose=False):
        self._ = gettext.gettext
        self.superset_limit = superset_limit
        self.verbose = verbose
        self.num_tokens = NUM_TOKENS

    def _token_counter(self, strings, min_len, max_len):
        """
        Returns how may times every character combination appears on the given strings, and
        how much savings you get with them.
        strings: strings to process
        minAbrev: Min lenght of found tokens
        maxLenToken: Max lenght of found tokens
        """
        savings = {}
        tokens = {}
        for string in strings:
            len_string = len(string)
            if len_string < min_len:
                continue
            for pos in range(0, (len_string - min_len) + 1):
                for len_token in range(min_len, min(max_len, len_string - pos) + 1):
                    token = string[pos : pos + len_token]
                    saving = len_token - 1
                    if token in tokens:
                        savings[token] += saving
                        tokens[token] += 1
                    else:
                        savings[token] = 0  # Nothing saved nor wasted
                        tokens[token] = 1
        return (savings, tokens)

    def _generate_tokens(self, strings, max_len_token):
        """
        Returns the optimal abbreviations, and the lengths of the strings after the substitution.
        strings: Strings to compress
        max_len_token: Max token lenght
        """

        len_after = 0  # Max string lenght after token substitution
        min_len_token = 2  # Minimal token lenght
        # Tomamos las mejores tokens
        optimum_tokens = []  # Optimal tokens
        for i in range(self.num_tokens):
            # Calculate how many appearances some combination has
            (savings, occurrences) = self._token_counter(
                strings, min_len_token, max_len_token
            )
            if not savings:  # Ya no hay mï¿½s strings de longitud mï¿½nima
                break
            savings_ordered = sorted(savings, key=savings.get, reverse=True)
            token = savings_ordered[0]
            saving = savings[token]
            # print ((token, saving, occurrences[token]))
            # Find supersets on the remainding possible combinations
            # Max saving by replacing a token with superset
            max_savings_up = saving
            max_super_set = None
            pos_max_saving = None
            s_set = None
            if (
                i < self.superset_limit
            ):  # Find supersets on the remainding possible combinations
                for d in range(1, len(savings_ordered)):
                    if token in savings_ordered[d]:
                        s_set = savings_ordered[d]
                        savings_up = savings[s_set] + (
                            (occurrences[token] - occurrences[s_set]) * (len(token) - 1)
                        )
                        if savings_up > max_savings_up:
                            max_savings_up = savings_up
                            max_super_set = s_set
                            pos_max_saving = d
            # There was some superset (TODO: puede que siempre ocurra, si len (token) < max_len_token)
            if pos_max_saving:
                # print ('La entrada "' + savings_ordered[pos_max_saving] + '" (' + str (pos_max_saving) + ') reemplaza "' + token + '" (0)')
                token = max_super_set
            if max_savings_up < 1:
                break  # No more savings
            # Adding the token to the optimal token list
            saving = savings[token]
            # print ((token, saving, occurrences[token]))
            optimum_tokens.append((token, saving, occurrences[token]))
            len_after += len(token)
            # Remove token appearances on the string
            c = 0
            new_strings = []
            while c < len(strings):
                parts = strings[c].split(token)
                if len(parts) > 1:  # The token is already on the string
                    strings[c] = parts[0]
                    for p in range(1, len(parts)):
                        new_strings.append(parts[p])
                c += 1
            strings += new_strings
        for string in strings:
            len_string = len(string) + 1
            len_after += len_string
        if len(optimum_tokens) < self.num_tokens:
            # Se reemplazarï¿½n por tokens de un byte
            len_after += self.num_tokens - len(optimum_tokens)
        new_tokens = []
        for token in optimum_tokens:
            new_tokens.append(token[0])
        return (new_tokens, len_after)

    def _sweep(self, texts, lengths):
        """Run the token search once per maximum token length (in worker
        processes when there is enough text) and return {length: (tokens,
        len_after)}. Ctrl+C keeps the runs that already finished."""
        jobs = [(list(texts), m, self.num_tokens, self.superset_limit) for m in lengths]
        results = {}

        def progress(iterable):
            if self.verbose or not pbarAvailable:
                return iterable
            return progressbar.ProgressBar()(_Sized(iterable, len(jobs)))

        workers = min(len(jobs), os.cpu_count() or 1)
        if workers > 1 and sum(len(t) for t in texts) >= PARALLEL_MIN_CHARS:
            try:
                with ProcessPoolExecutor(max_workers=workers) as pool:
                    futures = [pool.submit(_generate_worker, job) for job in jobs]
                    try:
                        for future in progress(as_completed(futures)):
                            m, result = future.result()
                            results[m] = result
                    except KeyboardInterrupt:
                        pool.shutdown(wait=False, cancel_futures=True)
                        if not results:
                            raise
                return results
            except (OSError, ImportError, NotImplementedError, BrokenProcessPool):
                results = {}  # no worker processes here: fall back to one
        try:
            for job in progress(jobs):
                m, result = _generate_worker(job)
                results[m] = result
        except KeyboardInterrupt:
            if not results:
                raise
        return results

    def _encode(self, texts, tokens, drop_unused):
        """Optimal parse of every text with tokens. With drop_unused, remove the
        tokens that don't pay for their table bytes and put the most used
        first: the Z80 finds token k by walking the k tokens before it."""
        while True:
            codes = [optimal_parse(t, tokens) for t in texts]
            if not drop_unused:
                return codes, tokens
            uses = [0] * len(tokens)
            for text_codes in codes:
                for c in text_codes:
                    if c >= 128:
                        uses[c - 128] += 1
            # A token stores len(token) bytes and saves len(token) - 1 per use.
            keep = [i for i, t in enumerate(tokens) if uses[i] * (len(t) - 1) > len(t)]
            if len(keep) == len(tokens):
                break
            tokens = [tokens[i] for i in keep]
        order = sorted(range(len(tokens)), key=lambda i: -uses[i])
        new_index = {old: new for new, old in enumerate(order)}
        codes = [
            [128 + new_index[c - 128] if c >= 128 else c for c in text_codes]
            for text_codes in codes
        ]
        return codes, [tokens[i] for i in order]

    def compress(self, strings, min_length, max_length, final_tokens=None):
        if self.verbose:
            print(self._("Replacing special characters..."))

        lenBefore = 0  # Total length before compressing
        texts = []  # strings to compress with tokens
        for string in strings:
            texts.append(string)
            lenBefore += len(string) + 1

        if self.verbose:
            print(self._("Length of texts without compression:"), lenBefore)

        generated = final_tokens is None
        if generated:
            if self.verbose:
                print(self._("Generating text tokens..."))

            results = self._sweep(texts, range(min_length, max_length + 1))
            minLength = 999999
            for maxLenToken in sorted(results):
                (posibles, len_token) = results[maxLenToken]
                if self.verbose:
                    print(
                        self._(
                            "With maximum abbreviation length %(max_len_token)d, length of texts after compression: %(len_after)d."
                        )
                        % ({"max_len_token": maxLenToken, "len_after": len_token})
                    )
                if len_token < minLength:
                    tokens = posibles  # Token set with maximum reduction
                    minLength = len_token  # Max. reduction archieved
                    maxLen = maxLenToken  # Max. lenght tokens
            if self.verbose:
                print()
                print(
                    self._(
                        "The best combination of abbreviations was found with maximum abbreviation length"
                    ),
                    maxLen,
                )
                print(len(tokens), self._("abbreviations in total, which are:"))
                print(tokens)
                print()

            # Padding tokens
            for i in range(len(tokens), self.num_tokens):
                tokens.append(chr(127))
            # Set this as the first token
            tokens = [chr(127)] + tokens

            if self.verbose:
                print(self._("Calculating savings..."))

            savingTokens = {}
            for posToken, token in enumerate(tokens):
                for posString, string in enumerate(texts):
                    parts = string.split(token)
                    if len(parts) > 1:
                        for k in range(0, len(parts) - 1):
                            if posToken in savingTokens.keys():
                                savingTokens[posToken] += len(token) - 1
                            else:
                                savingTokens[posToken] = -1

            final_tokens = []
            for posToken, token in enumerate(tokens):
                if posToken > 0:
                    if posToken not in savingTokens.keys():
                        savingTokens[posToken] = 0
                    if savingTokens[posToken] > 0:
                        final_tokens.append(token)
                    elif self.verbose:
                        if savingTokens[posToken] == 0:
                            print(
                                "Warning: token ["
                                + token
                                + "] won't be used cause it was not used by any text."
                            )
                        else:
                            print(
                                "Warning: token ["
                                + token
                                + "]  won't be used cause using it wont save any bytes, but waste "
                                + str(abs(savingTokens[posToken]))
                                + " bytes."
                            )

        if self.verbose:
            print(self._("Replacing tokens on texts..."))

        # Tokens given by the caller (an imported tokens file) are kept as they
        # are, in their order; a generated set is pruned and sorted by use.
        codes, final_tokens = self._encode(texts, final_tokens, drop_unused=generated)

        if self.verbose:
            print(self._("Encoding texts & tokens..."))

        tokenBytes = []
        for token in final_tokens:
            remnant = len(token) - 1
            for char in token:
                if remnant == 0:
                    byte = ord(char) + 128
                else:
                    byte = ord(char)
                tokenBytes.append(byte)
                remnant -= 1

        textBytes = []
        lenAfter = 0
        for text_codes in codes:
            s_bytes = [c ^ 255 for c in text_codes + [0x0A]]
            lenAfter += len(s_bytes)
            textBytes.append(s_bytes)
        if generated:
            print(lenBefore - lenAfter - len(tokenBytes), self._("bytes saved from text compression"))
            print()
        if self.verbose:
            print(self._("Length of texts with compression:"), lenAfter)
        return (textBytes, tokenBytes, final_tokens)
