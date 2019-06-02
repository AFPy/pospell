from pospell import clear


def test_clear():
    # We don't remove legitimally capitalized first words:
    assert clear("test", "Sport is great.") == "Sport is great."

    # Sometimes we can't guess it's a firstname:
    assert clear("test", "Julien Palard teste.") == "Julien  teste."

    # But we do if clearly accronyms
    assert clear("test", "HTTP is great.") == " is great."

    # Also skip accronyms in the middle of a sentence
    assert clear("test", "Because HTTP is great.") == "Because  is great."

    # We remove capitalized words in the middle of a sentence
    # they are typically names
    assert clear("test", "Great is Unicode.") == "Great is ."

    # We remove capitalized words even prefixed with l' in french.
    assert clear("test", "Bah si, l'Unicode c'est bien.") == "Bah si,  c'est bien."

    # We remove single letters in quotes
    assert clear("test", "La lettre « é » est seule.") == "La lettre  est seule."

    # We drop hours because hunspell whines on them
    assert clear("test", "Rendez-vous à 10h chez Murex") == "Rendez-vous à  chez "

    # When we removed a dashed name, remove it all
    assert clear("test", "Marc-André Lemburg a fait") != "Marc-  a fait"

    # Even in the middle of a sentence
    assert clear("test", "Hier, Marc-André Lemburg a fait") == "Hier,   a fait"
