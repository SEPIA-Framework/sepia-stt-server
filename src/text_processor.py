"""Tools to post-process text results like text2number"""

import re

class TextProcessor():
    """Common text processor interface"""
    def __init__(self, language_code: str = None):
        """Create new processor for specific language"""
        self.language_code = language_code
        if self.language_code:
            self.language_code_short = re.split("[-_]", self.language_code)[0].lower()
        else:
            self.language_code_short = None

    def process(self, text_input: str):
        """Process string and return new string"""

class TextToNumberProcessor(TextProcessor):
    """Convert numbers written as text ('two hundred', 'zweihundert')
    to real numbers"""
    def __init__(self, language_code: str = None):
        """Create text2num processor for specific language"""
        super().__init__(language_code)

    def process(self, text_input: str):
        """Take input text and replace number strings with real numbers"""
        if text_input and self.language_code_short:
            # TODO: implement
            return text_input
        else:
            return ""
