"""Tools to post-process text results like text2number"""

import re
from typing import Optional

from text_to_num.lang import LANG
from text_to_num import alpha2digit

class TextProcessor():
    """Common text processor interface"""
    def __init__(self, language_code: str = None):
        """Create new processor for specific language"""
        self.language_code = language_code
        if self.language_code:
            self.language_code_short = re.split("[-_]", self.language_code)[0].lower()
        else:
            self.language_code_short = None
        self.supports_language = False # overwrite in actual processor instance

    def process(self, text_input: str):
        """Process string and return new string"""

# Tools:

def search_via_regex(text_in: str, pattern: str) -> Optional[dict]:
    """Search pattern using regular expression (ignore case)
    and return dict with 'text_before', 'text_match', 'text_after' or None"""
    if not text_in:
        return None
    pattern = r'(?P<before>^|\W)(?P<match>' + pattern + r')(?P<after>\W|$)'
    search_res = re.search(pattern, text_in, flags=re.IGNORECASE)
    if not search_res:
        return None
    # first match
    res_span = search_res.span()
    text_before = text_in[:res_span[0]] + search_res.group("before")
    text_match = search_res.group("match")
    text_after = search_res.group("after") + text_in[res_span[1]:]
    # parts = re.split(r"\s+", text_match)
    return {
        'text_before': text_before,
        'text_match': text_match,
        'text_after': text_after,
    }


class TextToNumberProcessor(TextProcessor):
    """Convert numbers written as text ('two hundred', 'zweihundert')
    to real numbers"""
    def __init__(self, language_code: str = None):
        """Create text2num processor for specific language"""
        super().__init__(language_code)
        if self.language_code_short in LANG:
            self.supports_language = True

    def process(self, text_input: str):
        """Take input text and replace number strings with real numbers"""
        if text_input and self.supports_language:
            # convert numbers in text to digits
            return alpha2digit(text_input, self.language_code_short,
                relaxed=True, ordinal_threshold=0)
        elif text_input:
            # return unchanged
            return text_input
        else:
            # return empty
            return ""

class DateAndTimeOptimizer(TextProcessor):
    """Optimize presentation of dates (e.g. "22. 1. 2022" -> "22.01.2022")
    and times (e.g. "8 30 am" -> "8:30 a.m." or "12 Uhr 30" -> "12:30 Uhr")
    """
    def __init__(self, language_code: str = None):
        """Create processor and check language support"""
        super().__init__(language_code)
        # Currently supported languages: DE, EN
        if self.language_code_short in ["en", "de"]:
            self.supports_language = True
            if self.language_code_short == "de":
                self.time_optimizer = DateAndTimeOptimizer.optimize_time_de
                self.date_optimizer = DateAndTimeOptimizer.optimize_date_de
            elif self.language_code_short == "en":
                self.time_optimizer = DateAndTimeOptimizer.optimize_time_en
                self.date_optimizer = DateAndTimeOptimizer.optimize_date_en

    @staticmethod
    def optimize_time_de(text_in: str):
        """Optimize time presentation for German"""
        opt_text = re.sub(r"(\b)(ein Uhr)(\b)", r"1 Uhr", text_in, flags=re.IGNORECASE)
        search_res = search_via_regex(opt_text, r"\d{1,2} Uhr \d{1,2}")
        if not search_res:
            return opt_text
        # match
        parts = re.split(r"\s+", search_res['text_match'])
        hour = int(parts[0])
        minutes = int(parts[2])
        opt_text = search_res['text_before']
        if hour <= 24 and minutes < 60:
            # valid times - replace and continue search in rest
            opt_text += str(hour) + ":" + str(minutes).zfill(2) + " Uhr"
        else:
            # invalid times - keep org
            opt_text += search_res['text_match']
        # continue search in rest
        return opt_text + DateAndTimeOptimizer.optimize_time_de(search_res['text_after'])

    @staticmethod
    def optimize_time_en(text_in: str):
        """Optimize time presentation for English"""
        return text_in

    @staticmethod
    def optimize_date_de(text_in: str):
        """Optimize date presentation for German"""
        opt_text = text_in
        search_res = search_via_regex(opt_text, r"\d{1,2}\. \d{1,2}\.( \d{4}|)")
        if not search_res:
            return opt_text
        # match
        parts = re.split(r"\s+", search_res['text_match'])
        day = int(parts[0].replace(".", ""))
        month = int(parts[1].replace(".", ""))
        year = parts[2] if len(parts) == 3 else ""
        opt_text = search_res['text_before']
        if day <= 31 and month <= 12:
            # valid date numbers - replace
            opt_text += str(day).zfill(2) + "." + str(month).zfill(2) + "." + year
        else:
            # invalid day/month - keep
            opt_text += search_res['text_match']
        # continue search in rest
        return opt_text + DateAndTimeOptimizer.optimize_date_de(search_res['text_after'])

    @staticmethod
    def optimize_date_en(text_in: str):
        """Optimize date presentation for English"""
        return text_in

    def process(self, text_input: str):
        """Take input text and optimize date and time presentation"""
        if text_input and self.supports_language:
            # optimize
            opt_text = self.time_optimizer(text_input)
            opt_text = self.date_optimizer(opt_text)
            return opt_text
        elif text_input:
            # return unchanged
            return text_input
        else:
            # return empty
            return ""
