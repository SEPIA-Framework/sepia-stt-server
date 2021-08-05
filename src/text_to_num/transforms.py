# MIT License

# Copyright (c) 2018-2019 Groupe Allo-Media

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import re
from itertools import dropwhile
from typing import Any, Iterator, List, Sequence, Tuple, Union, Optional

from .lang import LANG, Language, German, Portuguese
from .parsers import (
    WordStreamValueParserInterface,
    WordStreamValueParser,  # we should rename this to 'WordStreamValueParserCommon'
    WordStreamValueParserGerman,
    WordToDigitParser,
)

from text_to_num.lang.portuguese import OrdinalsMerger

omg = OrdinalsMerger()
USE_PT_ORDINALS_MERGER = True


def look_ahead(sequence: Sequence[Any]) -> Iterator[Tuple[Any, Any]]:
    """Look-ahead iterator.

    Iterate over a sequence by returning couples (current element, next element).
    The last couple returned before StopIteration is raised, is (last element, None).

    Example:

    >>> for elt, nxt_elt in look_ahead(sequence):
    ... # do something

    """
    maxi = len(sequence) - 1
    for i, val in enumerate(sequence):
        ahead = sequence[i + 1] if i < maxi else None
        yield val, ahead


def text2num(text: str, lang: Union[str, Language], relaxed: bool = False) -> int:
    """Convert the ``text`` string containing an integer number written as letters
    into an integer value.

    Set ``relaxed`` to True if you want to accept "quatre vingt(s)" as "quatre-vingt"
    (fr) or "ein und zwanzig" as "einundzwanzig" (de) etc..

    Raises an ValueError if ``text`` does not describe a valid number.
    Return an int.
    """
    language: Language
    # mypy seems unable to understand this
    language = LANG[lang] if type(lang) is str else lang  # type: ignore
    num_parser: WordStreamValueParserInterface

    # German
    if type(language) is German:
        # The German number writing rules do not apply to the common order of number processing
        num_parser = WordStreamValueParserGerman(
            language, relaxed=relaxed
        )
        num_parser.parse(text)
        return num_parser.value
    # Default
    else:
        num_parser = WordStreamValueParser(language, relaxed=relaxed)
        tokens = list(dropwhile(lambda x: x in language.ZERO, text.split()))
        if not all(num_parser.push(word, ahead) for word, ahead in look_ahead(tokens)):
            raise ValueError("invalid literal for text2num: {}".format(repr(text)))

    return num_parser.value


def alpha2digit(
    text: str,
    lang: str,
    relaxed: bool = False,
    signed: bool = True,
    ordinal_threshold: int = 3,
) -> str:
    """Return the text of ``text`` with all the ``lang`` spelled numbers converted to digits.
    Takes care of punctuation.
    Set ``relaxed`` to True if you want to accept some disjoint numbers as compounds.
    Set ``signed`` to False if you don't want to produce signed numbers, that is, for example,
    if you prefer to get « minus 2 » instead of « -2 ».

    Ordinals up to `ordinal_threshold` are not converted.
    """
    if lang not in LANG:
        raise Exception("Language not supported")

    language = LANG[lang]
    segments = re.split(
        r"\s*[\.,;\(\)…\[\]:!\?]+\s*", text
    )
    punct = re.findall(r"\s*[\.,;\(\)…\[\]:!\?]+\s*", text)
    if len(punct) < len(segments):
        punct.append("")

    # Process segments
    if type(language) is German:
        # TODO: we should try to build a proper 'WordToDigitParser' for German
        # and refactor the code to be more similar to the default logic below
        text = _alpha2digit_agg(
            language,
            segments,
            punct,
            relaxed=relaxed,
            signed=signed,
            ordinal_threshold=ordinal_threshold
        )
    else:
        # Default
        out_segments: List[str] = []
        for segment, sep in zip(segments, punct):
            tokens = segment.split()
            num_builder = WordToDigitParser(
                language,
                relaxed=relaxed,
                signed=signed,
                ordinal_threshold=ordinal_threshold,
            )
            in_number = False
            out_tokens: List[str] = []
            for word, ahead in look_ahead(tokens):
                if num_builder.push(word.lower(), ahead and ahead.lower()):
                    in_number = True
                elif in_number:
                    out_tokens.append(num_builder.value)
                    num_builder = WordToDigitParser(
                        language,
                        relaxed=relaxed,
                        signed=signed,
                        ordinal_threshold=ordinal_threshold,
                    )
                    in_number = num_builder.push(word.lower(), ahead and ahead.lower())
                if not in_number:
                    out_tokens.append(word)
            # End of segment
            num_builder.close()
            if num_builder.value:
                out_tokens.append(num_builder.value)
            out_segments.append(" ".join(out_tokens))
            out_segments.append(sep)
        text = "".join(out_segments)

    # Post-processing
    if type(language) is Portuguese and USE_PT_ORDINALS_MERGER:
        text = omg.merge_compound_ordinals_pt(text)

    return text


def _alpha2digit_agg(
    language: Language,
    segments: List[str],
    punct: List[Any],
    relaxed: bool,
    signed: bool,
    ordinal_threshold: int = 3
) -> str:
    """Variant for "agglutinative" languages and languages with different style
    of processing numbers, for example:

    Default parser: "twenty one" (en) = 20, 1, "vingt et un" (fr) = 20, 1
    German parser: "einundzwanzig" or "ein und zwanzig" (de) = 1, 20

    Only German for now.
    """
    out_segments: List[str] = []

    def revert_if_alone(sentence_effective_len: int, current_sentence: List[str]) -> bool:
        """Test if word is 'alone' and should not be shown as number."""
        # TODO: move this to Language?
        if sentence_effective_len == 1 and current_sentence[0].lower() in language.NEVER_IF_ALONE:
            return True
        else:
            return False

    for segment, sep in zip(segments, punct):
        tokens = segment.split()
        # TODO: Should we use 'split_number_word' once on each token here if relaxed=True?
        sentence: List[str] = []
        out_tokens: List[str] = []
        out_tokens_is_num: List[bool] = []
        out_tokens_ordinal_org: List[Optional[str]] = []
        combined_num_result = None
        current_token_ordinal_org = None
        reset_to_last_if_failed = False
        token_index = 0

        while token_index < len(tokens):
            t = tokens[token_index]
            token_to_add = None
            token_to_add_is_num = False
            tmp_token_ordinal_org = None
            cardinal_for_ordinal = language.ord2card(t)
            if cardinal_for_ordinal:
                tmp_token_ordinal_org = t
                t = cardinal_for_ordinal
            sentence.append(t)
            try:
                # TODO: this is very inefficient because we analyze the same text
                # again and again until it fails including 'split_number_word' and all the
                # heavy lifting ... but it works and is hard to optimize ¯\_(ツ)_/¯
                num_result = text2num(" ".join(sentence), language, relaxed=relaxed)
                # TODO: here we need to use 'relaxed' to check how to continue
                combined_num_result = num_result
                current_token_ordinal_org = tmp_token_ordinal_org
                token_index += 1
                reset_to_last_if_failed = False
                # ordinals end groups
                if current_token_ordinal_org and num_result > ordinal_threshold:
                    token_to_add = str(combined_num_result)
                    token_to_add_is_num = True
                # ... but ordinals threshold reverts number back
                elif current_token_ordinal_org:
                    current_token_ordinal_org = None
                    sentence[len(sentence)-1] = str(tmp_token_ordinal_org)
                    token_to_add = " ".join(sentence)
                    token_to_add_is_num = False
            except ValueError:
                # This will happen if look-ahead was required (e.g. because of AND) but failed:
                if reset_to_last_if_failed:
                    reset_to_last_if_failed = False
                    # repeat last try but ...
                    token_index -= 1
                    # ... finish old group first and clean up
                    token_to_add = str(combined_num_result)
                    token_to_add_is_num = True
                # Happens if a) ends with no num b) ends with AND c) ends with invalid next num:
                elif combined_num_result is not None:
                    if t == language.AND and (token_index + 1) < len(tokens):
                        # number might continue after AND
                        # test the next and then decide to keep it or reset group
                        reset_to_last_if_failed = True
                        token_index += 1
                    else:
                        # last token has to be tested again in case there is sth like "eins eins"
                        # finish LAST group but keep token_index
                        token_to_add = str(combined_num_result)
                        token_to_add_is_num = True
                else:
                    # previous text was not a valid number
                    # prep. for next group
                    token_index += 1
                    token_to_add = t
                    token_to_add_is_num = False
            # new grouped tokens? then add and prep. next
            if token_to_add:
                if token_to_add_is_num and revert_if_alone(len(sentence)-1, sentence):
                    token_to_add = str(sentence[0])
                    token_to_add_is_num = False
                    current_token_ordinal_org = None
                out_tokens.append(token_to_add)
                out_tokens_is_num.append(token_to_add_is_num)
                out_tokens_ordinal_org.append(current_token_ordinal_org)
                sentence.clear()
                combined_num_result = None
                current_token_ordinal_org = None

        # any remaining tokens to add?
        if combined_num_result is not None:
            if revert_if_alone(len(sentence), sentence):
                out_tokens.append(str(sentence[0]))
                out_tokens_is_num.append(False)
            else:
                out_tokens.append(str(combined_num_result))
                out_tokens_is_num.append(True)
            out_tokens_ordinal_org.append(None)  # we can't reach this if it was ordinal

        # join all and keep track on signs
        out_segment = ""
        num_of_tokens = len(out_tokens)
        next_is_decimal_num = False
        for index, ot in enumerate(out_tokens):
            if next_is_decimal_num:
                # continue decimals?
                if (
                    index < num_of_tokens - 1
                    and out_tokens_is_num[index + 1]
                    and int(out_tokens[index + 1]) < 10
                ):
                    out_segment += ot
                else:
                    next_is_decimal_num = False
                    out_segment += ot + " "
            elif (ot in language.SIGN) and signed:
                # sign check
                if index < num_of_tokens - 1:
                    if out_tokens_is_num[index + 1] is True:
                        out_segment += language.SIGN[ot]
            elif out_tokens_ordinal_org[index] is not None:
                # cardinal transform
                out_segment += language.num_ord(ot, str(out_tokens_ordinal_org[index])) + " "
            elif (
                (ot.lower() in language.DECIMAL_SEP)
                and index > 0 and index < num_of_tokens - 1
                and out_tokens_is_num[index - 1] and out_tokens_is_num[index + 1]
                and int(out_tokens[index + 1]) < 10
            ):
                # decimal
                out_segment = out_segment.strip() + language.DECIMAL_SYM
                next_is_decimal_num = True
            else:
                out_segment += ot + " "

        # print("all:", out_tokens, out_tokens_is_num, out_tokens_ordinal_org) # DEBUG
        out_segments.append(out_segment.strip())
        out_segments.append(sep)
    return "".join(out_segments)
