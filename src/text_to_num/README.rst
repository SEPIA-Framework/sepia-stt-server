text2num
========

|docs|


``text2num`` is a python package that provides functions and parser classes for:

- Parsing of numbers expressed as words in French, English, Spanish, Portuguese, German and Catalan and convert them to integer values.
- Detection of ordinal, cardinal and decimal numbers in a stream of French, English, Spanish and Portuguese words and get their decimal digit representations. NOTE: Spanish does not support ordinal numbers yet.
- Detection of ordinal, cardinal and decimal numbers in a German text (BETA). NOTE: No support for 'relaxed=False' yet (behaves like 'True' by default).

Compatibility
-------------

Tested on python 3.7. Requires Python >= 3.6.

License
-------

This sofware is distributed under the MIT license of which you should have received a copy (see LICENSE file in this repository).

Installation
------------

``text2num`` does not depend on any other third party package.

To install text2num in your (virtual) environment::

    pip install text2num

That's all folks!

Usage examples
--------------

Parse and convert
~~~~~~~~~~~~~~~~~


French examples:

.. code-block:: python

    >>> from text_to_num import text2num
    >>> text2num('quatre-vingt-quinze', "fr")
    95

    >>> text2num('nonante-cinq', "fr")
    95

    >>> text2num('mille neuf cent quatre-vingt dix-neuf', "fr")
    1999

    >>> text2num('dix-neuf cent quatre-vingt dix-neuf', "fr")
    1999

    >>> text2num("cinquante et un million cinq cent soixante dix-huit mille trois cent deux", "fr")
    51578302

    >>> text2num('mille mille deux cents', "fr")
    ValueError: invalid literal for text2num: 'mille mille deux cent'


English examples:

.. code-block:: python

    >>> from text_to_num import text2num

    >>> text2num("fifty-one million five hundred seventy-eight thousand three hundred two", "en")
    51578302

    >>> text2num("eighty-one", "en")
    81


Russian examples:

.. code-block:: python

    >>> from text_to_num import text2num

    >>> text2num("пятьдесят один миллион пятьсот семьдесят восемь тысяч триста два", "ru")
    51578302

    >>> text2num("миллиард миллион тысяча один", "ru")
    1001001001

    >>> text2num("один миллиард один миллион одна тысяча один", "ru")
    1001001001

    >>> text2num("восемьдесят один", "ru")
    81


Spanish examples:

.. code-block:: python

    >>> from text_to_num import text2num
    >>> text2num("ochenta y uno", "es")
    81

    >>> text2num("nueve mil novecientos noventa y nueve", "es")
    9999

    >>> text2num("cincuenta y tres millones doscientos cuarenta y tres mil setecientos veinticuatro", "es")
    53243724


Portuguese examples:

.. code-block:: python

    >>> from text_to_num import text2num
    >>> text2num("trinta e dois", "pt")
    32

    >>> text2num("mil novecentos e seis", "pt")
    1906

    >>> text2num("vinte e quatro milhões duzentos mil quarenta e sete", "pt")
    24200047


German examples:

.. code-block:: python

    >>> from text_to_num import text2num

    >>> text2num("einundfünfzigmillionenfünfhundertachtundsiebzigtausenddreihundertzwei", "de")
    51578302

    >>> text2num("ein und achtzig", "de")
    81


Catalan examples:

.. code-block:: python

    >>> from text_to_num import text2num
    >>> text2num('noranta-cinc', "ca")
    95

    >>> text2num('huitanta-u', "ca")
    81

    >>> text2num('mil nou-cents noranta-nou', "ca")
    1999

    >>> text2num("cinquanta-un milions cinc-cents setanta-vuit mil tres-cents dos", "ca")
    51578302

    >>> text2num('mil mil dos-cents', "ca")
    ValueError: invalid literal for text2num: 'mil mil dos-cents'


Find and transcribe
~~~~~~~~~~~~~~~~~~~

Any numbers, even ordinals.

French:

.. code-block:: python

    >>> from text_to_num import alpha2digit
    >>> sentence = (
    ...     "Huit cent quarante-deux pommes, vingt-cinq chiens, mille trois chevaux, "
    ...     "douze mille six cent quatre-vingt-dix-huit clous.\n"
    ...     "Quatre-vingt-quinze vaut nonante-cinq. On tolère l'absence de tirets avant les unités : "
    ...     "soixante seize vaut septante six.\n"
    ...     "Nombres en série : douze quinze zéro zéro quatre vingt cinquante-deux cent trois cinquante deux "
    ...     "trente et un.\n"
    ...     "Ordinaux: cinquième troisième vingt et unième centième mille deux cent trentième.\n"
    ...     "Décimaux: douze virgule quatre-vingt dix-neuf, cent vingt virgule zéro cinq ; "
    ...     "mais soixante zéro deux."
    ... )
    >>> print(alpha2digit(sentence, "fr", ordinal_threshold=0))
    842 pommes, 25 chiens, 1003 chevaux, 12698 clous.
    95 vaut 95. On tolère l'absence de tirets avant les unités : 76 vaut 76.
    Nombres en série : 12 15 004 20 52 103 52 31.
    Ordinaux: 5ème 3ème 21ème 100ème 1230ème.
    Décimaux: 12,99, 120,05 ; mais 60 02.

    >>> sentence = "Cinquième premier second troisième vingt et unième centième mille deux cent trentième."
    >>> print(alpha2digit(sentence, "fr", ordinal_threshold=3))
    5ème premier second troisième 21ème 100ème 1230ème.


English:

.. code-block:: python

    >>> from text_to_num import alpha2digit

    >>> text = "On May twenty-third, I bought twenty-five cows, twelve chickens and one hundred twenty five point forty kg of potatoes."
    >>> alpha2digit(text, "en")
    'On May 23rd, I bought 25 cows, 12 chickens and 125.40 kg of potatoes.'


Russian:

.. code-block:: python

    >>> from text_to_num import alpha2digit

    >>> # дробная часть не обрабатывает уточнения вроде "пять десятых", "двенадцать сотых", "сколько-то стотысячных" и т.п., поэтому их лучше опускать
    >>> text = "Двадцать пять коров, двенадцать сотен цыплят и сто двадцать пять точка сорок кг картофеля."
    >>> alpha2digit(text, "ru")
    '25 коров, 1200 цыплят и 125.40 кг картофеля.'

    >>> text = "каждый пятый на первый второй расчитайсь!"
    >>> alpha2digit(text, 'ru', ordinal_threshold=0)
    'каждый 5ый на 1ый 2ой расчитайсь!'


Spanish (ordinals not supported yet):

.. code-block:: python

    >>> from text_to_num import alpha2digit

    >>> text = "Compramos veinticinco vacas, doce gallinas y ciento veinticinco coma cuarenta kg de patatas."
    >>> alpha2digit(text, "es")
    'Compramos 25 vacas, 12 gallinas y 125.40 kg de patatas.'

    >>> text = "Tenemos mas veinte grados dentro y menos quince fuera."
    >>> alpha2digit(text, "es")
    'Tenemos +20 grados dentro y -15 fuera.'


Portuguese:

.. code-block:: python

    >>> from text_to_num import alpha2digit

    >>> text = "Comprámos vinte e cinco vacas, doze galinhas e cento vinte e cinco vírgula quarenta kg de batatas."
    >>> alpha2digit(text, "pt")
    'Comprámos 25 vacas, 12 galinhas e 125,40 kg de batatas.'

    >>> text = "Temos mais vinte graus dentro e menos quinze fora."
    >>> alpha2digit(text, "pt")
    'Temos +20 graus dentro e -15 fora.'

    >>> text = "Ordinais: quinto, terceiro, vigésimo, vigésimo primeiro, centésimo quarto"
    >>> alpha2digit(text, "pt")
    'Ordinais: 5º, terceiro, 20ª, 21º, 104º'


German (BETA, Note: 'relaxed' parameter is not supported yet and 'True' by default):

.. code-block:: python

    >>> from text_to_num import alpha2digit

    >>> text = "Ich habe fünfundzwanzig Kühe, zwölf Hühner und einhundertfünfundzwanzig kg Kartoffeln gekauft."
    >>> alpha2digit(text, "de")
    'Ich habe 25 Kühe, 12 Hühner und 125 kg Kartoffeln gekauft.'

    >>> text = "Die Temperatur beträgt minus fünfzehn Grad."
    >>> alpha2digit(text, "de")
    'Die Temperatur beträgt -15 Grad.'

    >>> text = "Die Telefonnummer lautet plus dreiunddreißig neun sechzig null sechs zwölf einundzwanzig."
    >>> alpha2digit(text, "de")
    'Die Telefonnummer lautet +33 9 60 0 6 12 21.'

    >>> text = "Der zweiundzwanzigste Januar zweitausendzweiundzwanzig."
    >>> alpha2digit(text, "de")
    '22. Januar 2022'

    >>> text = "Es ist ein Buch mit dreitausend Seiten aber nicht das erste."
    >>> alpha2digit(text, "de", ordinal_threshold=0)
    'Es ist ein Buch mit 3000 Seiten aber nicht das 1..'

    >>> text = "Pi ist drei Komma eins vier und so weiter, aber nicht drei Komma vierzehn :-p"
    >>> alpha2digit(text, "de", ordinal_threshold=0)
    'Pi ist 3,14 und so weiter, aber nicht 3 Komma 14 :-p'


Catalan:

.. code-block:: python

    >>> from text_to_num import alpha2digit
    >>> text = ("Huit-centes quaranta-dos pomes, vint-i-cinc gossos, mil tres cavalls, dotze mil sis-cents noranta-huit claus.\n Vuitanta-u és igual a huitanta-u.\n Nombres en sèrie: dotze quinze zero zero quatre vint cinquanta-dos cent tres cinquanta-dos trenta-u.\n Ordinals: cinquè tercera vint-i-uena centè mil dos-cents trentena.\n Decimals: dotze coma noranta-nou, cent vint coma zero cinc; però seixanta zero dos.")
    >>> print(alpha2digit(text, "ca", ordinal_threshold=0))
    842 pomes, 25 gossos, 1003 cavalls, 12698 claus.
    81 és igual a 81.
    Nombres en sèrie: 12 15 004 20 52 103 52 31.
    Ordinals: 5è 3a 21a 100è 1230a.
    Decimals: 12,99, 120,05; però 60 02.

    >>> text = "Cinqué primera segona tercer vint-i-ué centena mil dos-cents trenté."
    >>> print(alpha2digit(text, "ca", ordinal_threshold=3))
    5é primera segona tercer 21é 100a 1230é.

    >>> text = "Compràrem vint-i-cinc vaques, dotze gallines i cent vint-i-cinc coma quaranta kg de creïlles."
    >>> alpha2digit(text, "ca")
    'Compràrem 25 vaques, 12 gallines i 125,40 kg de creïlles.'

    >>> text = "Fa més vint graus dins i menys quinze fora."
    >>> alpha2digit(text, "ca")
    'Fa +20 graus dins i -15 fora.'


Read the complete documentation on `ReadTheDocs <http://text2num.readthedocs.io/>`_.

Contribute
----------

Join us on https://github.com/allo-media/text2num


.. |docs| image:: https://readthedocs.org/projects/text2num/badge/?version=latest
    :target: https://text2num.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status
