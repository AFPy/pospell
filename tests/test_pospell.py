from pospell import clear, strip_rst, spell_check
from test.support import change_cwd
import pytest

POText = """
  msgid ""
  msgstr ""
  "Project-Id-Version: Python 3\n"
  "POT-Creation-Date: 2017-04-02 22:11+0200\n"
  "PO-Revision-Date: 2018-07-23 17:55+0200\n"
  "Language: fr\n"
  "MIME-Version: 1.0\n"
  "Content-Type: text/plain; charset=UTF-8\n"
  "Content-Transfer-Encoding: 8bit\n"

  #: ../Doc/about.rst:3
  msgid "About these documents"
  msgstr "À propos de ces documents"

  #: ../Doc/about.rst:6
  msgid ""
  "These documents are generated from `reStructuredText`_ sources by `Sphinx`_, "
  "a document processor specifically written for the Python documentation."
  msgstr ""
  "Ces documents sont générés à partir de sources en `reStructuredText`_ par "
  "`Sphinx`_, un analyseur de documents spécialement conçu pour la "
  "documentation Python."
  """

@pytest.fixture
def about_po(tmp_path):
    (tmp_path / "about.po").write_text(POText)
    with change_cwd(tmp_path):
        yield tmp_path

@pytest.fixture
def badfile_po(tmp_path):
    (tmp_path / "badfile.po").write_text("Not a po file")
    with change_cwd(tmp_path):
        yield tmp_path

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


def test_polib_correct_po_file(about_po):
    assert 0 == spell_check(["about.po"], None, "fr")


def test_polib_bad_file_po(badfile_po):
    assert -1 == spell_check(["badfile.po"], None, "fr")


def test_polib_non_existent_file():
    assert -1 == spell_check(['non_existent_file.po'], None, "fr")
