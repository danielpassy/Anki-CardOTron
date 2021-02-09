# AnkiCardOTron
Automates the creation of Anki cards for studying Hebrew-English<br>
 Anki is a software to aid studying, largely used by language learners and Medicine students - it helps memorizing a lot of information<br>
https://pypi.org/project/AnkiOTron/
<br>
This library helps the creation of Anki Decks to study Hebrew, however it could be easily extended for other languagues<br>
It receives a list of words, either via a list or using a .csv file, calls an API asynchronously, create the deck and return it.<br>
<br>

Install it using Pip
```py
pip install AnkiOTron
```
Create an AnkiOTron instance passing the list of words that you wish to translate
```py
from AnkiOTron import AnkiOTron
list = ["שלום", "להיתרות"]
instance = AnkiOTron(word_list=list)
```
call translate method
```py
instance.translate()
```
generate the deck using the path
```py
instance.generate_deck()
```

