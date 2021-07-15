"""Tools to post-process text results like text2number"""

import re

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
            return alpha2digit(text_input, self.language_code_short)
        elif text_input:
            # return unchanged
            return text_input
        else:
            # return empty
            return ""
