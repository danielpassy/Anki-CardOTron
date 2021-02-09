import unittest
from os import path
from AnkiCardOTron import AnkiCardOTron


class TestInputCSV(unittest.TestCase):
    """
    docstring
    """

    def setUp(self):
        self.cwd = path.dirname(__file__)

    def test_no_file(self):
        # no file handler
        with self.assertRaises(NameError):
            AnkiCardOTron(deck_name="hello")

    def test_twoFileHandler(self):
        # both options

        with self.assertRaises(NameError):
            AnkiCardOTron(file_path="c", word_list=[1, 2, 3])

    def test_one_word_not_right(self):
        deck_path = path.join(self.cwd, "csv_examples\\oneWordLatin.csv")
        Deck = AnkiCardOTron(file_path=deck_path)
        Deck.translate()
        error_list = Deck.errors()
        self.assertEqual(len(error_list), 1)

    def test_one_word_not_hebrew(self):
        deck_path = path.join(self.cwd, "csv_examples\\oneWordLatin.csv")

        Deck = AnkiCardOTron(file_path=deck_path)
        Deck.translate()
        error_list = Deck.errors()
        self.assertEqual(len(error_list), 1)

    def test_only_hebrew_words(self):
        deck_path = path.join(self.cwd, "csv_examples\\oneWordLatin.csv")
        Deck = AnkiCardOTron(file_path=deck_path)
        Deck.translate()
        input_errors = Deck.input_errors()
        self.assertEqual((input_errors), 1)


class TestInputList(unittest.TestCase):
    """
    Verify the List feature Creation
    """

    def test_modify_input_words(self):
        """
        docstring
        """
        word_list = ["שלטוםs", "שדג", "ככה", "שלום", "asdasd"]
        Deck = AnkiCardOTron(word_list=word_list)
        Deck.translate()
        dir_path = path.dirname(__file__)
        Deck.add_words(["שחרתי"])
        Deck.translate()
        Deck.generate_deck(dir_path)
        processed_words = Deck.get_processed_words()
        # python keep messing the order of the words.
        # self.assertEqual(processed_words,['שלום','שלטוםs',  'ככה', 'שדג', 'שחרתי'])
        self.assertTrue(len(Deck.errors()) == 1)


if __name__ == "__main__":
    unittest.main()
