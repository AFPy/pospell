from pospell import clear


def test_clear():
    # We don't remove legitimally capitalized first words:
    assert clear("test", "Sport is great.") == "Sport is great."

    # But we do if clearly accronyms
    assert clear("test", "HTTP is great.") == " is great."

    # Also skip accronyms in the middle of a sentence
    assert clear("test", "Because HTTP is great.") == "Because  is great."

    # We remove single letters in quotes
    assert clear("test", "La lettre « é » est seule.") == "La lettre  est seule."

    # We drop hours because hunspell whines on them
    assert clear("test", "Rendez-vous à 10h chez Murex") == "Rendez-vous à  chez Murex"

    # Drop PEP 440 versions
    assert (
        clear("test", "under python 1.6a1, 1.5.2, and earlier.")
        == "under python , , and earlier."
    )

    # Double space should change nothing
    assert clear("test", "Test. Aujourd'hui, j'ai faim.") == clear(
        "test", "Test.  Aujourd'hui, j'ai faim."
    )
