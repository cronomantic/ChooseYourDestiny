import sys

try:
    import progressbar

    pbarAvailable = True
except:
    pbarAvailable = False


NUM_TOKENS = 128


class CydcTextCompressor(object):
    def __init__(self, gettext, superset_limit, verbose=False):
        self._ = gettext.gettext
        self.special_chars = [c.decode("iso-8859-15") for c in self.special_characters]
        self.superset_limit = superset_limit
        self.verbose = verbose
        self.num_tokens = NUM_TOKENS

    special_characters = (
        b"\xAA",
        b"\xA1",
        b"\xBF",
        b"\xAB",
        b"\xBB",
        b"\xE1",
        b"\xE9",
        b"\xED",
        b"\xF3",
        b"\xFA",
        b"\xF1",
        b"\xD1",
        b"\xFC",
        b"\xDC",
    )

    def _replace_chars(self, old_string):
        new_string = ""
        for char in old_string:
            if ord(char) > 127:
                try:
                    char = self.special_chars.index(char) + 16
                except:
                    char = ord(char)
            elif char == "\n":
                char = ord("\r")
            else:
                char = ord(char)
            new_string += chr(char)
        return new_string

    """  
    Devuelve cuántas veces aparece cada combinación de chares en las strings dadas, y cuánto se ahorraría por abreviar cada una de ellas
    strings strings de las que contar las ocurrencias
    minAbrev Longitud mínima de las tokens
    maxLenToken Longitud máxima de las tokens
    """

    def _token_counter(self, strings, min_len, max_len):
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
                        savings[token] = 0  # No se ahorra ni desperdicia nada
                        tokens[token] = 1
        return (savings, tokens)

    """
        Calcula y devuelve las tokens ï¿½ptimas, y la longitud de las strings tras aplicarse
         maxLenToken Longitud mï¿½xima de las tokens
        textos strings sobre las que aplicar tokens
    """

    def _generate_tokens(self, strings, max_len_token):
        len_after = 0  # Longitud total de las strings tras aplicar tokens, incluyendo espacio de ï¿½stas
        min_len_token = 2  # Longitud mï¿½nima de las tokens
        # Tomamos las mejores tokens
        optimum_tokens = []  # tokens ï¿½ptimas calculadas
        for i in range(self.num_tokens):
            # Calculamos cuï¿½ntas veces aparece cada combinaciï¿½n
            (savings, occurrences) = self._token_counter(
                strings, min_len_token, max_len_token
            )
            if not savings:  # Ya no hay mï¿½s strings de longitud mï¿½nima
                break
            savings_ordered = sorted(savings, key=savings.get, reverse=True)
            token = savings_ordered[0]
            saving = savings[token]
            # print ((token, saving, occurrences[token]))
            # Buscamos superconjuntos entre el resto de combinaciones posibles
            # saving mï¿½ximo combinado por reemplazar token por un superconjunto, entre ambos
            max_savings_up = saving
            max_super_set = None
            pos_max_saving = None
            s_set = None
            if (
                i < self.superset_limit
            ):  # En las ï¿½ltimas, es poco probable que se aproveche esto
                # Buscamos superconjuntos entre el resto de combinaciones posibles
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
                            # print ('"%s" (%d) es superconjunto de "%s", savings %d, occurrences %d. savings combinados tomando ?ste %d' %
                            #     (s_set, d, token, savings[s_set], occurrences[s_set], savings_up))
            # Tenï¿½a algï¿½n superconjunto (TODO: puede que siempre ocurra, si len (token) < max_len_token)
            if pos_max_saving:
                # print ('La entrada "' + savings_ordered[pos_max_saving] + '" (' + str (pos_max_saving) + ') reemplaza "' + token + '" (0)')
                token = max_super_set
            if max_savings_up < 1:
                break  # Ya no se ahorra nada mï¿½s
            # Aï¿½adimos esta token a la lista de tokens ï¿½ptimas calculadas
            saving = savings[token]
            # print ((token, saving, occurrences[token]))
            optimum_tokens.append((token, saving, occurrences[token]))
            len_after += len(token)
            # Quitamos las occurrences de esta token en las strings
            c = 0
            new_strings = []
            while c < len(strings):
                parts = strings[c].split(token)
                if len(parts) > 1:  # La token aparecï¿½a en esa string
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

        lenBefore = 0  # Longitud total de los textos antes de abreviar
        texts = []  # strings sobre las que aplicar tokens
        for string in strings:
            string = self._replace_chars(string)
            texts.append(string)
            lenBefore += len(string) + 1

        for string in strings:
            for char in string:
                if ord(char) > 255:
                    sys.exit(
                        self._(
                            f"ERROR: Invalid character.{ord(char)} - {char} in {string}"
                        )
                    )

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
                    tokens = (
                        posibles  # Conjunto de tokens que produjo la m?xima reducc??n
                    )
                    minLength = len_token  # Reducciï¿½n mï¿½xima de longitud total de textos lograda
                    maxLen = maxLenToken  # Longitud mï¿½xima en la busqueda de tokens
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

            # Ponemos tokens de relleno
            for i in range(len(tokens), self.num_tokens):
                tokens.append(chr(127))
            # Hay que dejar eso como la primera token
            tokens = [chr(127)] + tokens

            tokensTmp = []
            for token in tokens:
                tokensTmp.append(self._replace_chars(token))
            tokens = tokensTmp

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
