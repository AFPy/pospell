from pospell import clear, strip_rst


def test_clear():
    # We don't remove legitimally capitalized first words:
    assert clear("test", "Sport is great.") == "Sport is great."
    assert clear("test", "Sport is great.", drop_capitalized=True) == "Sport is great."

    # Sometimes we can't guess it's a firstname:
    assert clear("test", "Julien Palard teste.") == "Julien Palard teste."
    assert (
        clear("test", "Julien Palard teste.", drop_capitalized=True) == "Julien  teste."
    )

    # We remove capitalized words in the middle of a sentence
    # they are typically names
    assert clear("test", "Great is Unicode.") == "Great is Unicode."
    assert clear("test", "Great is Unicode.", drop_capitalized=True) == "Great is ."

    # We remove capitalized words even prefixed with l' in french.
    assert (
        clear("test", "Bah si, l'Unicode c'est bien.")
        == "Bah si, l'Unicode c'est bien."
    )
    assert (
        clear("test", "Bah si, l'Unicode c'est bien.", drop_capitalized=True)
        == "Bah si,  c'est bien."
    )

    # We remove single letters in quotes
    assert clear("test", "La lettre « é » est seule.") == "La lettre  est seule."

    # We remove soft hyphens
    assert clear("test", "some\xadthing") == "something"

    # We drop hours because hunspell whines on them
    assert clear("test", "Rendez-vous à 10h chez Murex") == "Rendez-vous à  chez Murex"

    # When we removed a dashed name, remove it all
    assert clear("test", "Marc-André Lemburg a fait") != "Marc- Lemburg a fait"

    # Even in the middle of a sentence
    assert (
        clear("test", "Hier, Marc-André Lemburg a fait")
        == "Hier, Marc-André Lemburg a fait"
    )

    # We remove variables
    assert clear("test", "Starting {days_since} days ago") == "Starting  days ago"

    # Drop PEP 440 versions
    assert (
        clear("test", "under python 1.6a1, 1.5.2, and earlier.")
        == "under python , , and earlier."
    )

    # Double space should change nothing
    assert clear("test", "Test. Aujourd'hui, j'ai faim.") == clear(
        "test", "Test.  Aujourd'hui, j'ai faim."
    )

    assert (
        clear("test", strip_rst(":pep:`305` - Interface des fichiers"))
        == "Interface des fichiers"
    )


def test_clear_accronyms():
    for drop_capitalized in True, False:
        # We always drop accronyms
        assert (
            clear("test", "HTTP is great.", drop_capitalized=drop_capitalized)
            == " is great."
        )

        # Even suffixed with a number
        assert (
            clear("test", "POSIX.1 is great.", drop_capitalized=drop_capitalized)
            == " is great."
        )

        # Correctly drop prefix of accronyms
        assert (
            clear("test", "non-HTTP is bad.", drop_capitalized=drop_capitalized)
            == " is bad."
        )

        # Also skip accronyms in the middle of a sentence
        assert (
            clear("test", "Yes HTTP is great.", drop_capitalized=drop_capitalized)
            == "Yes  is great."
        )

        assert (
            clear("", "Ho. PEPs good.", drop_capitalized=drop_capitalized)
            == "Ho.  good."
        )
