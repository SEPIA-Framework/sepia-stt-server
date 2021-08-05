"""Unit tests for text_processor"""

import unittest
from text_to_num import alpha2digit
from text_processor import DateAndTimeOptimizer

optimizer = {
    "de": DateAndTimeOptimizer("de"),
    "en": DateAndTimeOptimizer("en")
}

def apply_optimize_pipeline(text_org: str, lang: str) -> None:
    """Use text2num and 'DateAndTimeOptimizer' and return"""
    text_digi = alpha2digit(text_org, lang, ordinal_threshold=0)
    text_opt = optimizer[lang].process(text_digi)
    return text_opt

def optimize_and_plot(text_org: str, lang: str) -> None:
    """Use text2num and 'DateAndTimeOptimizer' and plot afterwards"""
    text_digi = alpha2digit(text_org, lang, ordinal_threshold=0)
    text_opt = optimizer[lang].process(text_digi)
    print(text_org, "\n", text_digi, "\n", text_opt, "\n")


class TestTextProcessor(unittest.TestCase):
    """Test class for text_processor"""

    DE = "de"
    EN = "en"

    def test_dates_de(self):
        """Date parsing and optimization tests for German"""

        self.assertEqual(apply_optimize_pipeline(
            "zwei und zwanzigster zweiter zweitausend zwei und zwanzig", self.DE),
            "22.02.2022"
        )
        self.assertEqual(apply_optimize_pipeline(
            "Am ersten ersten zweitausend einundzwanzig.", self.DE),
            "Am 01.01.2021."
        )
        self.assertEqual(apply_optimize_pipeline(
            "erster erster", self.DE),
            "01.01."
        )
        self.assertEqual(apply_optimize_pipeline(
            "Am ersten ersten.", self.DE),
            "Am 01.01.."
        )
        self.assertEqual(apply_optimize_pipeline(
            "Am sechsten vierten?", self.DE),
            "Am 06.04.?"
        )
        self.assertEqual(apply_optimize_pipeline(
            "Am ersten ersten zweitausend einundzwanzig und " +
            "am dritten zwölften zweitausenddreißig.", self.DE),
            "Am 01.01.2021 und am 03.12.2030."
        )
        self.assertEqual(apply_optimize_pipeline(
            "1. 1., 2. 2., 3. 3..", self.DE),
            "01.01., 02.02., 03.03.."
        )

    def test_times_de(self):
        """Time parsing and optimization tests for German"""

        self.assertEqual(apply_optimize_pipeline(
            "ein Uhr", self.DE),
            "1 Uhr"
        )
        self.assertEqual(apply_optimize_pipeline(
            "ein Uhr. Zwei Uhr. Dreizehn Uhr.", self.DE),
            "1 Uhr. 2 Uhr. 13 Uhr."
        )
        self.assertEqual(apply_optimize_pipeline(
            "zwölf Uhr dreißig", self.DE),
            "12:30 Uhr"
        )
        self.assertEqual(apply_optimize_pipeline(
            "sechsundzwanzig Uhr drei", self.DE),
            "26 Uhr 3"
        )
        self.assertEqual(apply_optimize_pipeline(
            "Um zwölf Uhr dreißig.", self.DE),
            "Um 12:30 Uhr."
        )
        self.assertEqual(apply_optimize_pipeline(
            "Um zwölf Uhr dreißig und siebzehn uhr fünfzehn.", self.DE),
            "Um 12:30 Uhr und 17:15 Uhr."
        )
        self.assertEqual(apply_optimize_pipeline(
            "zwölf Uhr dreißig am Samstag und dreizehn Uhr vier und " +
            "zwanzig am Sonntag und zwei Uhr fünfzehn am Montag.", self.DE),
            "12:30 Uhr am Samstag und 13:24 Uhr am Sonntag und 2:15 Uhr am Montag."
        )
        self.assertEqual(apply_optimize_pipeline(
            "Es ist dreiundzwanzig Uhr neunundfünfzig!", self.DE),
            "Es ist 23:59 Uhr!"
        )
        self.assertEqual(apply_optimize_pipeline(
            "Ist es null Uhr eins?", self.DE),
            "Ist es 0:01 Uhr?"
        )
        # self.assertRaises(ValueError, apply_optimize_pipeline, "test text", self.DE)

    def test_times_en(self):
        """Time parsing and optimization tests for German"""

        self.assertEqual(apply_optimize_pipeline(
            "one o'clock", self.EN),
            "1 o'clock"
        )
        self.assertEqual(apply_optimize_pipeline(
            "six thirty pm", self.EN),
            "6:30 pm"
        )
        self.assertEqual(apply_optimize_pipeline(
            "it's ten thirty a.m..", self.EN),
            "it's 10:30 a.m.."
        )
        self.assertEqual(apply_optimize_pipeline(
            "its one thirty PM!", self.EN),
            "its 1:30 PM!"
        )
        self.assertEqual(apply_optimize_pipeline(
            "eight PM, six thirty AM, ten o clock, twelve o'clock, five o`clock",
            self.EN),
            "8 PM, 6:30 AM, 10 o clock, 12 o'clock, 5 o`clock"
        )

        # TODO: expected to fail atm:
        self.assertEqual(apply_optimize_pipeline(
            "we meet at quarter past nine", self.EN),
            "we meet at quarter past 9"
        )


if __name__ == '__main__':

    # print("\n----------- Some custom tests -----------\n")

    # print("DE:\n")
    # optimize_and_plot("zwölf Uhr dreißig am Samstag.", "de")

    # print("EN:\n")
    # optimize_and_plot("twenty second of February two thousand twenty two", "en")

    # Unit tests
    unittest.main()
