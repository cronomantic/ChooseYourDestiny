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

# Nested tokens (a token may contain other tokens): table entries are
# [length][symbols], a symbol >= 128 being a reference, and the interpreter is
# assembled with NESTED_TOKENS (EXPAND_TOKEN in text_manager.asm).
NESTED_MAX_LEN = 12  # longest token the nested search considers
NESTED_MAX_DEPTH = 3  # EXPAND_TOKEN recursion, bounded for the Z80 stack
# Extra interpreter bytes of the nested decoder over the flat one. The nested
# format is chosen only when it saves more than this (see the test that
# assembles both). Its 32 bytes of TOKEN_BUFFER RAM are freed on top of that.
NESTED_DECODER_EXTRA_BYTES = 0


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


def _nested_worker(job):
    strings, max_len, max_depth, num_tokens = job
    return "nested", nested_token_search(strings, max_len, max_depth, num_tokens)


def expand_tokens(tokens):
    """Plain text of each token; in nested tokens chr(128 + i) is token i."""
    cache = {}

    def expand(i, seen=()):
        if i not in cache:
            if i in seen or not 0 <= i < len(tokens):
                raise ValueError("invalid token reference")
            cache[i] = "".join(
                expand(ord(c) - 128, seen + (i,)) if ord(c) >= 128 else c
                for c in tokens[i]
            )
        return cache[i]

    return [expand(i) for i in range(len(tokens))]


def token_depth(tokens):
    """Nesting depth of the deepest token (1 = no nested references)."""
    depth = {}

    def d(i):
        if i not in depth:
            depth[i] = 1 + max((d(ord(c) - 128) for c in tokens[i] if ord(c) >= 128), default=0)
        return depth[i]

    return max((d(i) for i in range(len(tokens))), default=0)


def is_nested(tokens):
    return any(ord(c) >= 128 for t in tokens for c in t)


def _substring_counts(seg, max_len, counts, sign):
    n = len(seg)
    for i in range(n - 1):
        for length in range(2, min(max_len, n - i) + 1):
            key = seg[i : i + length]
            counts[key] = counts.get(key, 0) + sign


def nested_token_search(texts, max_len=NESTED_MAX_LEN, max_depth=NESTED_MAX_DEPTH,
                        num_tokens=NUM_TOKENS, candidates=64):
    """Greedy nested token set: repeatedly take the substring (which may already
    contain token references) whose replacement saves the most bytes, counting
    its table entry (symbols + length byte), and replace it everywhere."""
    segs = list(texts)
    counts = {}
    for seg in segs:
        _substring_counts(seg, max_len, counts, 1)
    tokens, depth = [], []

    def depth_of(t):
        return max((depth[ord(c) - 128] for c in t if ord(c) >= 128), default=0)

    for i in range(num_tokens):
        ranked = sorted(
            ((n * (len(t) - 1) - len(t) - 1, t) for t, n in counts.items() if n > 1),
            reverse=True,
        )
        best, best_gain, tried = None, 0, 0
        for approx, t in ranked:  # approx over-counts overlaps; re-score exactly
            if approx <= best_gain or tried >= candidates:
                break
            if depth_of(t) >= max_depth:
                continue
            tried += 1
            n = sum(seg.count(t) for seg in segs if t in seg)
            gain = n * (len(t) - 1) - len(t) - 1
            if gain > best_gain:
                best, best_gain = t, gain
        if best is None:
            break
        tokens.append(best)
        depth.append(depth_of(best) + 1)
        symbol = chr(128 + i)
        for k, seg in enumerate(segs):
            if best in seg:
                _substring_counts(seg, max_len, counts, -1)
                segs[k] = seg.replace(best, symbol)
                _substring_counts(segs[k], max_len, counts, 1)
        counts = {t: n for t, n in counts.items() if n > 0}
    return tokens


def _renumber(tokens, order):
    """tokens reordered as order (list of old indices), references remapped."""
    new_index = {old: new for new, old in enumerate(order)}
    return [
        "".join(chr(128 + new_index[ord(c) - 128]) if ord(c) >= 128 else c for c in tokens[i])
        for i in order
    ], new_index


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
    def __init__(self, gettext, superset_limit, verbose=False, token_format="auto"):
        self._ = gettext.gettext
        self.superset_limit = superset_limit
        self.verbose = verbose
        self.num_tokens = NUM_TOKENS
        # "auto" builds both token formats and keeps the smaller; "flat" or
        # "nested" forces one. After compress(), self.nested says which it used.
        self.token_format = token_format
        self.nested = False

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

    def _sweep(self, texts, lengths, nested=False):
        """Run the token search once per maximum token length, plus the nested
        search when asked (in worker processes when there is enough text).
        Returns {length: (tokens, len_after)}, with the nested token set under
        "nested". Ctrl+C keeps the runs that already finished."""
        jobs = [
            (_generate_worker, (list(texts), m, self.num_tokens, self.superset_limit))
            for m in lengths
        ]
        if nested:
            # First: it is the longest single job.
            jobs.insert(0, (_nested_worker, (list(texts), NESTED_MAX_LEN,
                                             NESTED_MAX_DEPTH, self.num_tokens)))
        results = {}

        def progress(iterable):
            if self.verbose or not pbarAvailable:
                return iterable
            return progressbar.ProgressBar()(_Sized(iterable, len(jobs)))

        workers = min(len(jobs), os.cpu_count() or 1)
        if workers > 1 and sum(len(t) for t in texts) >= PARALLEL_MIN_CHARS:
            try:
                with ProcessPoolExecutor(max_workers=workers) as pool:
                    futures = [pool.submit(worker, job) for worker, job in jobs]
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
            for worker, job in progress(jobs):
                m, result = worker(job)
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

    def _encode_nested(self, texts, tokens, drop_unused):
        """_encode for nested tokens: optimal parse over their expansions. With
        drop_unused, remove tokens no text or token uses that don't pay for
        their entry, then sort by how often the Z80 looks each one up (its own
        uses plus those through the tokens that contain it)."""
        while True:
            expanded = expand_tokens(tokens)
            codes = [optimal_parse(t, expanded) for t in texts]
            if not drop_unused:
                return codes, tokens
            uses = [0] * len(tokens)
            for text_codes in codes:
                for c in text_codes:
                    if c >= 128:
                        uses[c - 128] += 1
            refs = [0] * len(tokens)
            for t in tokens:
                for c in t:
                    if ord(c) >= 128:
                        refs[ord(c) - 128] += 1
            keep = [
                i for i, t in enumerate(tokens)
                if refs[i] or uses[i] * (len(expanded[i]) - 1) > len(t) + 1
            ]
            if len(keep) == len(tokens):
                break
            tokens, _ = _renumber(tokens, keep)
        # Generated tokens only reference tokens created before them.
        lookups = list(uses)
        for i in reversed(range(len(tokens))):
            for c in tokens[i]:
                if ord(c) >= 128:
                    lookups[ord(c) - 128] += lookups[i]
        order = sorted(range(len(tokens)), key=lambda i: -lookups[i])
        tokens, new_index = _renumber(tokens, order)
        codes = [
            [128 + new_index[c - 128] if c >= 128 else c for c in text_codes]
            for text_codes in codes
        ]
        return codes, tokens

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
        want_flat = self.token_format in ("auto", "flat")
        want_nested = self.token_format in ("auto", "nested")
        if generated:
            if self.verbose:
                print(self._("Generating text tokens..."))

            results = self._sweep(
                texts, range(min_length, max_length + 1) if want_flat else (),
                nested=want_nested,
            )
            nested_tokens = results.pop("nested", None)
            final_tokens = []
            if want_flat:
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
        if generated:
            candidates = []
            if want_flat:
                codes, toks = self._encode(texts, final_tokens, drop_unused=True)
                candidates.append((self._size(codes, toks, False), False, codes, toks))
            if want_nested and (nested_tokens is not None or not candidates):
                codes, toks = self._encode_nested(texts, nested_tokens or [], drop_unused=True)
                candidates.append((self._size(codes, toks, True), True, codes, toks))
            # Ties go to flat (listed first): no decoder change for nothing.
            _, self.nested, codes, final_tokens = min(candidates, key=lambda c: c[0])
            if self.verbose and len(candidates) == 2:
                print(
                    self._(
                        "Size with flat abbreviations: {flat} bytes; with nested "
                        "ones: {nested} bytes (decoder included)."
                    ).format(flat=candidates[0][0], nested=candidates[1][0])
                )
            if self.nested and len(candidates) == 2:
                print(
                    self._("Using nested abbreviations, {saved} bytes smaller.").format(
                        saved=candidates[0][0] - candidates[1][0]
                    )
                )
        else:
            self.nested = is_nested(final_tokens)
            # An empty entry would misalign the flat table, and the nested length
            # byte holds 1..255 symbols (0 would make the Z80 djnz loop 256 times).
            if any(not t or (self.nested and len(t) > 255) for t in final_tokens):
                raise ValueError("invalid token")
            if self.nested:
                expand_tokens(final_tokens)  # ValueError on a bad reference or a cycle
                if token_depth(final_tokens) > NESTED_MAX_DEPTH:
                    raise ValueError("nested tokens too deep")
                codes, final_tokens = self._encode_nested(texts, final_tokens, drop_unused=False)
            else:
                codes, final_tokens = self._encode(texts, final_tokens, drop_unused=False)

        if self.verbose:
            print(self._("Encoding texts & tokens..."))

        tokenBytes = self._table_bytes(final_tokens, self.nested)

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

    @staticmethod
    def _table_bytes(tokens, nested):
        """Flat: the token's characters, the last one with bit 7 set.
        Nested: [number of symbols][symbols], references being 128 + index."""
        table = []
        for token in tokens:
            if nested:
                table.append(len(token))
                table += [ord(c) for c in token]
            else:
                table += [ord(c) for c in token[:-1]] + [ord(token[-1]) + 128]
        return table

    @classmethod
    def _size(cls, codes, tokens, nested):
        """Bytes the texts, the table and (nested) the larger decoder take."""
        size = sum(len(c) + 1 for c in codes) + len(cls._table_bytes(tokens, nested))
        return size + (NESTED_DECODER_EXTRA_BYTES if nested else 0)
