from types import SimpleNamespace
from pathlib import Path

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

    # We drop hours because hunspell whines on them
    assert "10h" not in clear("Rendez-vous à 10h chez Murex")

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

    # Drop PEP 440 versions
    assert "1.6a1" not in clear("under python 1.6a1, 1.5.2, and earlier.")
    assert "1.5.2" not in clear("under python 1.6a1, 1.5.2, and earlier.")

    # Double space should change nothing
    assert clear("Test. Aujourd'hui, j'ai faim.") == clear(
        "Test.  Aujourd'hui, j'ai faim."
    )

    assert ":pep:`305`" not in clear(strip_rst(":pep:`305` - Interface des fichiers"))


def test_clear_accronyms():
    for drop_capitalized in True, False:
        # We always drop accronyms
        assert "HTTP" not in clear("HTTP is great.", drop_capitalized)

        # Even suffixed with a number
        assert "POSIX.1" not in clear("POSIX.1 is great.", drop_capitalized)

        # Correctly drop prefix of accronyms
        assert "non-HTTP" not in clear("non-HTTP is bad.", drop_capitalized)

        # Also skip accronyms in the middle of a sentence
        assert "HTTP" not in clear("Yes HTTP is great.", drop_capitalized)

        assert "PEPs" not in clear("Ho. PEPs good.", drop_capitalized)


def test_with_an_error(tmp_path, capsys, monkeypatch):
    import subprocess

    tmp_path = Path(tmp_path)
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(stdout="Pyhton\n"),
    )
    (tmp_path / "test.po").write_text(
        """
msgid "Python FTW!"
msgstr "Gloire à Pyhton !"
"""
    )
    assert spell_check([tmp_path / "test.po"]) > 0
    captured = capsys.readouterr()
    assert "Pyhton" in captured.out
    assert not captured.err


def test_with_no_error(tmp_path, capsys, monkeypatch):
    import subprocess

    tmp_path = Path(tmp_path)
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(stdout=""),
    )
    (tmp_path / "test.po").write_text(
        """
msgid "Python FTW!"
msgstr "Gloire à Python !"
"""
    )
    assert spell_check([tmp_path / "test.po"]) == 0
    captured = capsys.readouterr()
    assert not captured.out
    assert not captured.err


def test_issue_19(tmp_path, capsys, monkeypatch):
    import subprocess

    tmp_path = Path(tmp_path)
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(stdout="pubb\nsubb\n"),
    )
    (tmp_path / "test.po").write_text(
        """
msgid "pubb/subb yo"
msgstr "pubb/subb"
"""
    )
    assert spell_check([tmp_path / "test.po"]) > 0
    captured = capsys.readouterr()
    assert "pubb" in captured.out
    assert not captured.err
