import os
from pathlib import Path
import asyncio
import re
import ssl
from random import randrange
from typing import NoReturn
import unicodedata
import sys
import aiohttp
import genanki

# Build paths inside the project like this: BASE_DIR / 'subdir'.


class AnkiCardOTron(object):
    """
    Create d
    """

    def __init__(self, **kwargs):
        """
        Arguments:
        deck_name, csv, from_kindle, file_path,
        TODO: IMPLEMENT: model, template

        """
        for key, value in kwargs.items():
            setattr(self, key, value)

        if (not hasattr(self, "file_path")) and (not hasattr(self, "word_list")):
            raise NameError("You must pass a word_list or file_path as an argument ")
        if hasattr(self, "file_path") and hasattr(self, "word_list"):
            raise NameError("You must pass either word_list or file_path, not both")

        # define the input type
        self.csv = False if hasattr(self, "word_list") else True

        if not hasattr(self, "deck_name"):
            self.deck_name = "anki_deck" + str(randrange(1 << 30, 1 << 31))

        ## TODO: implemenent a way to modify the model

        self.my_deck = genanki.Deck(randrange(1 << 30, 1 << 31), self.deck_name)

        self.list_of_fields = {
            "Hebrew",
            "Translation",
            "Token",
            "Classification",
            "Multiple_Meaning",
        }
        self.df_main_table = {}
        self.error_list = []
        self.__open_file()
        self.__create_model()

    def __open_file(self) -> NoReturn:
        ## TODO: implement cleanup

        if self.csv:
            try:
                with open(self.file_path, newline="", encoding="utf-8-sig") as f:
                    input_list = [line.strip() for line in f]
                    # check for two words in each input

            except FileNotFoundError:
                raise FileNotFoundError("The CSV file doesn't exist")
        else:
            input_list = self.word_list

        self.word_list = self.__format_input(input_list)

    def __format_input(self, input_list: list) -> str:
        """
        Receive a list of words from the user and format it
        return a list containing only words in Hebrew
        Does not separate multiple words as it may represent
        an expression

        """
        # some punctuations are excluded due to beeing used in Hebrew
        word_list_tmp = []
        punctuation = r"""!"#$%&()*+,-./:;<=>?@[\]^_{|}~"""
        for input in input_list:
            tmp = input.split(",")
            for word in tmp:
                regex = re.compile("[%s]" % re.escape(punctuation))
                word_list_tmp.append(regex.sub("", word))
        word_list_tmp = [x for x in word_list_tmp if x]
        for word in word_list_tmp:
            if self.is_hebrew(word):
                pass
            else:
                self.__create_error(word, "The token was not identified as Hebrew")
                word_list_tmp.remove(word)
        return word_list_tmp

    def add_words(self, input_words: list) -> NoReturn:
        """
        Use to add extra words to the deck, after you should perform
        translate -> add notes normally.
        It shouldnt be called before calling create_notes on the initial words
        it deletes all words that are in the "staging" area
        """
        assert type(input_words) == list, "You must provide a list of words"
        self.word_list = self.__format_input(input_words)

    def is_hebrew(self, word):
        return any(
            char in set("‎ב‎ג‎ד‎ה‎ו‎ז‎ח‎ט‎י‎כ‎ך‎ל‎מ‎נ‎ס‎ע‎פ‎צ‎ק‎ר‎ש‎ת‎ם‎ן‎ף‎ץ")
            for char in word.lower()
        )

    def translate(self):

        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.IO_main(loop))

    async def IO_main(self, loop: object) -> NoReturn:
        headers = {
            "accept": "*/*",
            "Host": "services.morfix.com",
            "Content-Type": "application/json",
        }
        async with aiohttp.ClientSession(loop=loop, headers=headers) as session:
            response = await asyncio.gather(
                *[self.API_call(session, word) for word in self.word_list],
                return_exceptions=False,
            )

    async def extract_response(self, html: str, word: str) -> str:
        if html["ResultType"] == "Match":
            meaning = html["Words"][0]
            table = {
                "Hebrew": word,
                "Translation": meaning["OutputLanguageMeaningsString"],
                "Token": meaning["InputLanguageMeanings"][0][0]["DisplayText"],
                "Classification": meaning["PartOfSpeech"],
            }
            if len(html["Words"]) == 1:
                table["Multiple_Meaning"] = True
            else:
                table["Multiple_Meaning"] = False
            self.df_main_table[word] = table
        else:
            self.__create_error(word, html["ResultType"])

    def __create_error(self, word: str, error):
        self.error_list.append({"word": word, "error": error})

    async def API_call(self, session: object, word: str) -> NoReturn:
        params = {"Query": word, "ClientName": "Android_Hebrew"}
        url = "http://services.morfix.com/translationhebrew/TranslationService/GetTranslation/"
        async with session.post(url, json=params, ssl=ssl.SSLContext()) as response:
            if response.reason == "OK":
                await self.extract_response(await response.json(), word)
            else:
                self.__create_error(word, response.reason)

    def auto_create_notes(self) -> str:
        for key, value in self.df_main_table.items():
            self.create_notes(value)

    def generate_deck(self) -> str:

        deck_filename = self.deck_name.lower().replace(" ", "_")
        my_package = genanki.Package(self.my_deck)
        # my_package.media_files = self.audio_paths # TODO: Kindle implementation
        self.deck_path = os.path.join(settings.MEDIA_ROOT, deck_filename + ".apkg")
        my_package.write_to_file(self.deck_path)
        return self.deck_path
        # returns the  path to the deck

    def __create_model(self):

        model_fields = []
        for field in [
            field for field in self.list_of_fields if field != "Multiple_Meaning"
        ]:
            model_fields.append({"name": field})
        self.my_model = genanki.Model(
            randrange(1 << 30, 1 << 31),
            "DAnkiModel",
            fields=model_fields,
            templates=[
                {
                    "name": "{Card}",
                    "qfmt": '<div style="color:blue;text-align:center;font-size:20px"><b>{{Token}}</div></b><br><b>Word:</b> {{Hebrew}}<br> <b>Word class:</b> {{Classification}}',
                    "afmt": '{{FrontSide}}<hr id="answer"><div style="color:black;text-align:center;font-size:12px"><b>Translation</div></b>{{Translation}}',
                },
            ],
        )

    def create_notes(self, data: dict) -> NoReturn:
        ## must receive a dictionary with each field and it's value
        # create a Note
        note_fields = []

        # append fields besides Multiple Meaning, that is used for return use
        for field in [i for i in self.list_of_fields if i != "Multiple_Meaning"]:
            note_fields.append(unicodedata.normalize("NFKC", data[field]))
        my_note = genanki.Note(
            model=self.my_model,
            fields=note_fields,
        )
        self.my_deck.add_note(my_note)

    def save_notes(self):
        """
        Streamline all the methods required for the rceation of a
        """
        self.auto_create_notes()
