import unittest
from os import path
from util import DAnki


class TestInputCSV(unittest.TestCase):
    """
    docstring
    """

    def test_no_file(self):
        # no file handler
        with self.assertRaises(NameError):
            DAnki(deck_name="hello")

    def test_twoFileHandler(self):
        # both options

        with self.assertRaises(NameError):
            DAnki(file_path="c", word_list=[1, 2, 3])

    def test_one_word_not_right(self):
        Deck = DAnki(
            file_path=path.abspath(
                r"C:\Users\Daniel\Documents\Apps\Danki_with_Django\backend\DankiProcessor\csv_examples\oneWordLatin.csv"
            )
        )
        Deck.translate()
        error_list = Deck.error_list
        self.assertEqual(len(error_list), 1)

    def test_one_word_not_hebrew(self):
        Deck = DAnki(
            file_path=path.abspath(
                r"C:\Users\Daniel\Documents\Apps\Danki_with_Django\backend\DankiProcessor\csv_examples\oneWordLatin.csv"
            )
        )
        Deck.translate()
        error_list = Deck.error_list
        self.assertEqual(len(error_list), 1)

    def test_only_hebrew_words(self):
        Deck = DAnki(
            file_path=path.abspath(
                r"C:\Users\Daniel\Documents\Apps\Danki_with_Django\backend\DankiProcessor\csv_examples\only_hebrew_words.csv"
            )
        )
        Deck.translate()
        error_list = Deck.error_list
        self.assertEqual(len(error_list), 0)


class TestInputList(unittest.TestCase):
    """
    Verify the List feature Creation
    """

    def test_modify_input_words(self):
        """
        docstring
        """
        word_list = ["שלטוםs", "שדג", "ככה", "שלום", "asdasd"]
        Deck = DAnki(word_list=word_list)
        Deck.translate()
        Deck.save_notes()

        Deck.add_words(["שחרתי"])
        Deck.translate()
        Deck.save_notes()
        Deck.generate_deck()

        self.assertTrue(len(Deck.error_list) == 1)


if __name__ == "__main__":
    unittest.main()
