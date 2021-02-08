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
import csv
import json

# Build paths inside the project like this: BASE_DIR / 'subdir'.


class AnkiCardOTron(object):
    """
    Class responsable for receive words from the user,
    acessing an API to get data
    and creating anki decks
    """

    def __init__(self, **kwargs):
        """
        Arguments:
        deck_name(str)
        csv(a csv in memory)
        file_path(a file path, str)
        file(a file handler)
        word_list(list of str)
        django(True/false)
        empty(optional->True)

        know issues:

        TODO: IMPLEMENT: model, template, from_kindle

        """
        for key, value in kwargs.items():
            setattr(self, key, value)

        if not hasattr(self, "empty"):
            if (not hasattr(self, "file_path")) and (not hasattr(self, "word_list")):
                raise NameError("You must pass a word_list or file_path as an argument")
            if hasattr(self, "file_path") and hasattr(self, "word_list"):
                raise NameError("You must pass either word_list or file_path, not both")

        # define the input type
        self.csv = False if hasattr(self, "word_list") else True

        if not hasattr(self, "deck_name"):
            self.deck_name = "anki_deck" + str(randrange(1 << 30, 1 << 31))

        # make word_list private.
        if hasattr(self, "word_list"):
            self.__word_list = self.word_list
            delattr(self, "word_list")

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
        self.__create_model()
        if hasattr(self, "empty"):
            return

        self.__errorHandler = self.AnkiTronError()
        self.number_errors = self.__errorHandler.number_errors
        self.input_errors = self.__errorHandler.input_errors
        self.translate_errors = self.__errorHandler.translate_errors
        self.errors = self.__errorHandler.errors
        self.__open_file()

    def __open_file(self) -> NoReturn:
        ## TODO: implement cleanup

        # for django compatibilitY
        if hasattr(self, "django") and self.csv:
            input_list = self.file_path.read().decode("utf-8-sig").splitlines()
        else:
            if self.csv:
                try:
                    with open(self.file_path, newline="", encoding="utf-8-sig") as f:
                        input_list = [line.strip() for line in f]
                        # check for two words in each input

                except FileNotFoundError as input_not_found:
                    raise FileNotFoundError(
                        "The CSV file doesn't exist"
                    ) from input_not_found
            else:
                input_list = self.__word_list

        self.__word_list = self.__format_input(input_list)

    def serialize(self) -> str:
        """
        Returns a string representation of the data
        """
        return json.dumps(self.df_main_table, ensure_ascii=False)

    def deserialize(self, serialized: str) -> NoReturn:
        """
        Receives a string representation of the data
        and
        """
        new_data = json.loads(serialized)
        self.df_main_table.update(new_data)

    def __format_input(self, input_list: list) -> str:
        """
        Receive a list of words from the user and format it
        return a list containing only words in Hebrew
        Does not separate multiple words as it may represent
        an expression

        """
        # some punctuations are excluded due to beeing used in Hebrew
        word_list_tmp = []
        punctuation = r""" !"#$%&()*+,-./:;<=>?@[\]^_{|}~"""
        for input in input_list:
            tmp = input.split(",")
            for word in tmp:
                regex = re.compile("[%s]" % re.escape(punctuation))
                word_list_tmp.append(regex.sub("", word))
        word_list_tmp = [x for x in word_list_tmp if x]
        word_list = word_list_tmp.copy()
        for word in word_list:
            if self.is_hebrew(word):
                pass
            else:
                self.__errorHandler.create_error(
                    word, "The token was not identified as Hebrew", "Input"
                )
                word_list_tmp.remove(word)
        return word_list_tmp

    def get_unprocessed_words(self) -> list:

        # return all untranslated words
        return self.__word_list

    def get_processed_words(self) -> list:

        # return all translated words
        processed_words = []
        for keys in self.df_main_table.keys():
            processed_words.append(keys)
        return processed_words

    def print_processed_words(self) -> NoReturn:
        processed_words = []
        for keys in self.df_main_table.keys():
            processed_words.append(keys)
        print(processed_words)

    def print_unprocessed_words(self) -> NoReturn:
        print(self.__word_list)

    def add_words(self, input_words: list) -> NoReturn:
        """
        Use to add extra words to the deck, after you should perform
        translate -> add notes normally.
        It shouldnt be called before calling create_note on the initial words
        it deletes all words that are in the "staging" area
        """
        assert type(input_words) == list, "You must provide a list of words"
        self.__word_list = self.__format_input(input_words)

    def pop_word(self, word: str) -> NoReturn:
        """
        Find the word, attempting first on the translated set
        and pop it. Else, try on the staged set, then finally returns
        not found
        """

        assert type(input_words) == str, "You must provide a string"

        if word in self.df_main_table.keys():
            del self.df_main_table[word]
        elif word in self.__word_list:
            self.__word_list.pop(word)
        else:
            print("The word was not found")

    def is_hebrew(self, word):
        return any(
            char in set("‎ב‎ג‎ד‎ה‎ו‎ז‎ח‎ט‎י‎כ‎ך‎ל‎מ‎נ‎ס‎ע‎פ‎צ‎ק‎ר‎ש‎ת‎ם‎ן‎ף‎ץ")
            for char in word.lower()
        )

    def translate(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.IO_main(loop))
        loop.close()
        # empty word list after process is done.
        self.__word_list = []

    async def IO_main(self, loop: object) -> NoReturn:
        headers = {
            "accept": "*/*",
            "Host": "services.morfix.com",
            "Content-Type": "application/json",
        }
        async with aiohttp.ClientSession(loop=loop, headers=headers) as session:
            response = await asyncio.gather(
                *[self.API_call(session, word) for word in self.__word_list],
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
            self.__errorHandler.create_error(word, html["ResultType"], "Translation")

    async def API_call(self, session: object, word: str) -> NoReturn:
        params = {"Query": word, "ClientName": "Android_Hebrew"}
        url = "http://services.morfix.com/translationhebrew/TranslationService/GetTranslation/"
        async with session.post(url, json=params, ssl=ssl.SSLContext()) as response:
            if response.reason == "OK":
                await self.extract_response(await response.json(), word)
            else:
                self.__errorHandler.__create_error(word, response.reason, "translate")

    def generate_deck(self, path: str) -> str:
        """
        Generate the deck in the given path
        It crashes if the path it's not valid
        """
        
        deck_filename = self.deck_name.lower().replace(" ", "_")
        my_package = genanki.Package(self.my_deck)
        # my_package.media_files = self.audio_paths # TODO: Kindle implementation
        output_path = os.path.join(path)
        if not os.path.exists(output_path):
            os.makedirs(output_path)
        self.deck_path = os.path.join(output_path, deck_filename + ".apkg")
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
                    "qfmt": '<div style="color:blue;text-align:center;font-size:25px"><b>{{Token}}</div></b><br><b>Word:</b> {{Hebrew}}<br> <b>Word class:</b> {{Classification}}',
                    "afmt": '{{FrontSide}}<hr id="answer"><div style="color:black;text-align:center;font-size:25px"><b>Translation</div></b>{{Translation}}',
                },
            ],
        )

    def create_note(self, data: dict) -> NoReturn:
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

    def save_notes(self) -> str:
        for key, value in self.df_main_table.items():
            self.create_note(value)

    class AnkiTronError(object):
        """
        An Error wrapper for AnkiTron
        """

        def __init__(self):
            self.num_errors = 0
            self.translated = False
            self.error_list = []

        def create_error(self, word: str, error: object, typeE: str):
            if not (typeE == "Input" or typeE == "Translation"):
                raise TypeError('The error should be "Translation" or "Input"')
            self.error_list.append({"word": word, "error": error, "type": typeE})

        def input_errors(self):
            input_errors = 0
            for item in self.error_list:
                if item["type"] == "Input":
                    input_errors += 1
            return input_errors

        def translate_errors(self):
            if not self.translated:
                msg = "You must call `.translate()` before accessing `.number_errors`."
                raise AssertionError(msg)

            translate_errors = 0
            for item in self.error_list:
                if item["type"] == "translate":
                    translate_errors += 1
            return translate_errors

        def number_errors(self):
            return len(self.error_list)

        def errors(self):
            return self.error_list

        def __set_translated(self):
            self.translated = True
