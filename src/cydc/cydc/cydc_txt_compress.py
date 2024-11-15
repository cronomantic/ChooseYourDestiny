#
# Copyright (C) 2023 Sergio Chico
#
# Based on DAAD Reborn Tokenizer
# Copyright (C) 2010, 2013, 2018-2020, 2022 José Manuel Ferrer Ortiz
#
# This file is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, released under the GPL v2 license
#
# This file is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# See <https://www.gnu.org/licenses/>.
#


import sys

try:
    import progressbar

    pbarAvailable = True
except ImportError:
    pbarAvailable = False


NUM_TOKENS = 128


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
        if self.verbose:
            print(
                self._(
                    "With maximum abbreviation length %(max_len_token)d, length of texts after compression: %(len_after)d."
                )
                % ({"max_len_token": max_len_token, "len_after": len_after})
            )
            # print (optimum_tokens)
        new_tokens = []
        for token in optimum_tokens:
            new_tokens.append(token[0])
        return (new_tokens, len_after)

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

        if final_tokens is None:
            if self.verbose:
                print(self._("Generating text tokens..."))

            minLength = 999999
            if self.verbose or not pbarAvailable:
                l_range = range(min_length, max_length + 1)
            else:
                progress = progressbar.ProgressBar()
                l_range = progress(range(min_length, max_length + 1))
            for maxLenToken in l_range:
                try:
                    (posibles, len_token) = self._generate_tokens(
                        list(texts), maxLenToken
                    )
                except KeyboardInterrupt:
                    break
                if len_token < minLength:
                    tokens = posibles  # Token set with maximum reduction
                    minLength = len_token  # Max. reduction archieved
                    maxLen = maxLenToken  # Max. lenght tokens
            print(lenBefore - minLength, self._("bytes saved from text compression"))
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

            ahorroTotal = 0
            final_tokens = []
            for posToken, token in enumerate(tokens):
                if posToken > 0:
                    if posToken not in savingTokens.keys():
                        savingTokens[posToken] = 0
                    if savingTokens[posToken] > 0:
                        final_tokens.append(token)
                        ahorroTotal += savingTokens[posToken]
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
        else:
            pass  # check if the tokens are good

        if self.verbose:
            print(self._("Replacing tokens on texts..."))

        for posToken, token in enumerate(final_tokens):
            for posString, string in enumerate(texts):
                parts = string.split(token)
                string = chr(posToken + 128).join(parts)
                texts[posString] = string

        if self.verbose:
            print(self._("Encoding texts & tokens..."))

        tokenBytes = []
        for token in final_tokens:
            remnant = len(token) - 1
            for char in token:
                if remnant == 0:
                    # byte = hex(ord(char) + 128)[2:].zfill(2)
                    byte = ord(char) + 128
                else:
                    # byte = hex(ord(char))[2:].zfill(2)
                    byte = ord(char)
                tokenBytes.append(byte)
                remnant -= 1

        # currentOffset = 0
        # arrayBytes = []
        # offsets = []
        textBytes = []
        lenAfter = 0
        for string in texts:
            string = string + chr(0x0A)
            # str_bytes = []
            s_bytes = []
            for char in string:
                s_bytes.append(ord(char) ^ 255)
                # str_bytes.append(hex(ord(char) ^ 255)[2:].zfill(2))
                lenAfter += 1
            textBytes.append(s_bytes)
            # offsets.append(currentOffset)
            # currentOffset += len(str_bytes)
            # arrayBytes += str_bytes
        if self.verbose:
            print(self._("Length of texts with compression:"), lenAfter)
        return (textBytes, tokenBytes, final_tokens)
