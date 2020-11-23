from pathlib import Path

import pytest

from pospell import clear, strip_rst, spell_check


def test_clear():
    # We don't remove legitimally capitalized first words:
    assert clear("Sport is great.") == "Sport is great."
    assert clear("Sport is great.", True) == "Sport is great."

    # Sometimes we can't guess it's a firstname:
    assert clear("Julien Palard teste.") == "Julien Palard teste."
    assert "Palard" not in clear("Julien Palard teste.", True)

    # We remove capitalized words in the middle of a sentence
    # they are typically names
    assert clear("Great is Unicode.") == "Great is Unicode."
    assert "Unicode" not in clear("Great is Unicode.", True)

    # We remove capitalized words even prefixed with l' in french.
    assert clear("Bah si, l'Unicode c'est bien.") == "Bah si, l'Unicode c'est bien."
    assert "Unicode" not in clear("Bah si, l'Unicode c'est bien.", True)

    # We remove single letters in quotes
    assert "é" not in clear("La lettre « é » est seule.")

    # We remove soft hyphens
    assert clear("some\xadthing") == "something"

    # When we removed a dashed name, remove it all
    assert clear("Marc-André Lemburg a fait").strip() == "Marc-André Lemburg a fait"
    assert "Marc-André" in clear("Marc-André Lemburg a fait", True)
    assert "Lemburg" not in clear("Marc-André Lemburg a fait", True)

    # Even in the middle of a sentence
    assert clear("Hier, Marc-André Lemburg a fait") == "Hier, Marc-André Lemburg a fait"
    assert "Marc-André" not in clear("Hier, Marc-André Lemburg a fait", True)
    assert "André" not in clear("Hier, Marc-André Lemburg a fait", True)
    assert "Marc" not in clear("Hier, Marc-André Lemburg a fait", True)
    assert "Lemburg" not in clear("Hier, Marc-André Lemburg a fait", True)

    # We remove variables
    assert "days_since" not in clear("Starting {days_since} days ago")

    # Double space should change nothing
    assert clear("Test. Aujourd'hui, j'ai faim.") == clear(
        "Test.  Aujourd'hui, j'ai faim."
    )

    assert ":pep:`305`" not in clear(strip_rst(":pep:`305` - Interface des fichiers"))


FIXTURE_DIR = Path(__file__).resolve().parent


@pytest.mark.parametrize("po_file", (FIXTURE_DIR / "expected_to_fail").glob("*.po"))
def test_expected_to_fail(po_file, capsys):
    assert spell_check([po_file]) > 0
    assert not capsys.readouterr().err


@pytest.mark.parametrize("po_file", (FIXTURE_DIR / "expected_to_success").glob("*.po"))
def test_expected_to_success(po_file, capsys):
    assert spell_check([po_file]) == 0
    assert not capsys.readouterr().err
