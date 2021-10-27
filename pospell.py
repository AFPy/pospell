"""pospell is a spellcheckers for po files containing reStructuedText."""
import io
from string import digits
from unicodedata import category
import logging
import subprocess
import sys
from typing import Dict
from contextlib import redirect_stderr
from itertools import chain
from pathlib import Path
from shutil import which

import docutils.frontend
import docutils.nodes
import docutils.parsers.rst
import polib
from docutils.parsers.rst import roles
from docutils.utils import new_document

import regex

__version__ = "1.0.13"

DEFAULT_DROP_CAPITALIZED = {"fr": True, "fr_FR": True}


class POSpellException(Exception):
    """All exceptions from this module inherit from this one."""


class Unreachable(POSpellException):
    """The code encontered a state that should be unreachable."""


try:
    HUNSPELL_VERSION = subprocess.check_output(
        ["hunspell", "--version"], universal_newlines=True
    ).split("\n", maxsplit=1)[0]
except FileNotFoundError:
    print("hunspell not found, please install hunspell.", file=sys.stderr)
    sys.exit(1)


class DummyNodeClass(docutils.nodes.Inline, docutils.nodes.TextElement):
    """Used to represent any unknown roles, so we can parse any rst blindly."""


def monkey_patch_role(role):
    """Patch docutils.parsers.rst.roles.role so it always match.

    Giving a DummyNodeClass for unknown roles.
    """

    def role_or_generic(role_name, language_module, lineno, reporter):
        base_role, message = role(role_name, language_module, lineno, reporter)
        if base_role is None:
            roles.register_generic_role(role_name, DummyNodeClass)
            base_role, message = role(role_name, language_module, lineno, reporter)
        return base_role, message

    return role_or_generic


roles.role = monkey_patch_role(roles.role)


class NodeToTextVisitor(docutils.nodes.NodeVisitor):
    """Recursively convert a docutils node to a Python string.

    Usage:

    >>> visitor = NodeToTextVisitor(document)
    >>> document.walk(visitor)
    >>> print(str(visitor))

    It ignores (see IGNORE_LIST) some nodes, which we don't want in
    hunspell (enphasis typically contain proper names that are unknown
    to dictionaires).
    """

    IGNORE_LIST = (
        "emphasis",
        "superscript",
        "title_reference",
        "strong",
        "DummyNodeClass",
        "reference",
        "literal",
        "Text",
    )

    def __init__(self, document):
        """Initialize visitor for the given node/document."""
        self.output = []
        super().__init__(document)

    def unknown_visit(self, node):
        """Mandatory implementation to visit unknwon nodes."""

    @staticmethod
    def ignore(node):
        """Just raise SkipChildren.

        Used for all visit_* in the IGNORE_LIST.

        See __getattr__.
        """
        raise docutils.nodes.SkipChildren

    def __getattr__(self, name):
        """Skip childrens from the IGNORE_LIST."""
        if name.startswith("visit_") and name[6:] in self.IGNORE_LIST:
            return self.ignore
        raise AttributeError(name)

    def visit_Text(self, node):
        """Keep this node text, this is typically what we want to spell check."""
        self.output.append(node.rawsource)

    def __str__(self):
        """Give the accumulated strings."""
        return " ".join(self.output)


def strip_rst(line):
    """Transform reStructuredText to plain text."""
    if line.endswith("::"):
        # Drop :: at the end, it would cause Literal block expected
        line = line[:-2]
    parser = docutils.parsers.rst.Parser()
    settings = docutils.frontend.Values(
        {
            "report_level": 2,
            "halt_level": 4,
            "exit_status_level": 5,
            "debug": None,
            "warning_stream": None,
            "error_encoding": "utf-8",
            "error_encoding_error_handler": "backslashreplace",
            "language_code": "en",
            "id_prefix": "",
            "auto_id_prefix": "id",
            "pep_references": None,
            "pep_base_url": "http://www.python.org/dev/peps/",
            "pep_file_url_template": "pep-%04d",
            "rfc_references": None,
            "rfc_base_url": "http://tools.ietf.org/html/",
            "tab_width": 8,
            "trim_footnote_reference_space": None,
            "syntax_highlight": "long",
            "line_length_limit": 10000,
        }
    )
    stderr_stringio = io.StringIO()
    with redirect_stderr(stderr_stringio):
        document = new_document("<rst-doc>", settings=settings)
        parser.parse(line, document)
    stderr = stderr_stringio.getvalue()
    if stderr:
        print(stderr.strip(), "while parsing:", line)
    visitor = NodeToTextVisitor(document)
    document.walk(visitor)
    return str(visitor)


def clear(line, drop_capitalized=False, po_path=""):
    """Clear various other syntaxes we may encounter in a line."""
    # Normalize spaces
    line = regex.sub(r"\s+", " ", line).replace("\xad", "")

    to_drop = {
        r'<a href="[^"]*?">',
        r"{[a-z_]*?}",  # Sphinx variable
        r"%\([a-z_]+?\)[diouxXeEfFgGcrsa%]",  # Sphinx variable
        r"« . »",  # Single letter examples (typically in Unicode documentation)
    }
    if drop_capitalized:
        to_drop.add(
            # Strip capitalized words in sentences
            r"(?<!\. |^|-)\b(\p{Letter}['’])?\b\p{Uppercase}\p{Letter}[\w.-]*\b"
        )
    if logging.getLogger().isEnabledFor(logging.DEBUG):
        for pattern in to_drop:
            for dropped in regex.findall(pattern, line):
                logging.debug(
                    "%s: dropping %r via %r due to from %r",
                    po_path,
                    dropped,
                    pattern,
                    line,
                )
    return regex.sub("|".join(to_drop), r" ", line)


def quote_for_hunspell(text):
    """Quote a paragraph so hunspell don't misinterpret it.

    Quoting the manpage:
    It is recommended that programmatic interfaces prefix
    every data line with an uparrow to protect themselves
    against future changes in hunspell.
    """
    out = []
    for line in text.split("\n"):
        out.append("^" + line if line else "")
    return "\n".join(out)


def po_to_text(po_path, drop_capitalized=False):
    """Convert a po file to a text file.

    This strips the msgids and all po syntax while keeping lines at
    their same position / line number.
    """
    buffer = []
    lines = 0
    try:
        entries = polib.pofile(Path(po_path).read_text(encoding="UTF-8"))
    except Exception as err:
        raise POSpellException(str(err)) from err
    for entry in entries:
        if entry.msgid == entry.msgstr:
            continue
        while lines < entry.linenum:
            buffer.append("")
            lines += 1
        buffer.append(clear(strip_rst(entry.msgstr), drop_capitalized, po_path=po_path))
        lines += 1
    return "\n".join(buffer)


def parse_args():
    """Parse command line arguments."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Check spelling in po files containing restructuredText."
    )
    parser.add_argument(
        "-l",
        "--language",
        type=str,
        default="fr",
        help="Language to check, you'll have to install the corresponding "
        "hunspell dictionary, on Debian see apt list 'hunspell-*'.",
    )
    parser.add_argument(
        "--glob",
        type=str,
        help="Provide a glob pattern, to be interpreted by pospell, to find po files, "
        "like --glob '**/*.po'.",
    )
    parser.add_argument(
        "--drop-capitalized",
        action="store_true",
        help="Always drop capitalized words in sentences"
        " (defaults according to the language).",
    )
    parser.add_argument(
        "--no-drop-capitalized",
        action="store_true",
        help="Never drop capitalized words in sentences"
        " (defaults according to the language).",
    )
    parser.add_argument(
        "po_file",
        nargs="*",
        type=Path,
        help="Files to check, can optionally be mixed with --glob, or not, "
        "use the one that fit your needs.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="More output, use -vv, -vvv, and so on.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s " + __version__ + " using hunspell: " + HUNSPELL_VERSION,
    )
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("-p", "--personal-dict", type=str)
    parser.add_argument(
        "--modified", "-m", action="store_true", help="Use git to find modified files."
    )
    args = parser.parse_args()
    if args.drop_capitalized and args.no_drop_capitalized:
        print("Error: don't provide both --drop-capitalized AND --no-drop-capitalized.")
        parser.print_help()
        sys.exit(1)
    if not args.po_file and not args.modified:
        parser.print_help()
        sys.exit(1)
    return args


def look_like_a_word(word):
    """Return True if the given str looks like a word.

    Used to filter out non-words like `---` or `-0700` so they don't
    get reported. They typically are not errors.
    """
    if not word:
        return False
    if any(digit in word for digit in digits):
        return False
    if len([c for c in word if category(c) == "Lu"]) > 1:
        return False  # Probably an accronym, or a name like CPython, macOS, SQLite, ...
    if "-" in word:
        return False
    return True


def spell_check(
    po_files,
    personal_dict=None,
    language="en_US",
    drop_capitalized=False,
    debug_only=False,
):
    """Check for spelling mistakes in the given po_files.

    (po format, containing restructuredtext), for the given language.
    personal_dict allow to pass a personal dict (-p) option, to hunspell.

    Debug only will show what's passed to Hunspell instead of passing it.
    """
    personal_dict_arg = ["-p", personal_dict] if personal_dict else []
    texts_for_hunspell = {}
    for po_file in po_files:
        if debug_only:
            print(po_to_text(str(po_file), drop_capitalized))
            continue
        texts_for_hunspell[po_file] = po_to_text(str(po_file), drop_capitalized)
    if debug_only:
        return 0
    try:
        output = subprocess.run(
            ["hunspell", "-d", language, "-a"] + personal_dict_arg,
            universal_newlines=True,
            input=quote_for_hunspell("\n".join(texts_for_hunspell.values())),
            stdout=subprocess.PIPE,
            check=True,
        )
    except subprocess.CalledProcessError:
        return -1
    return parse_hunspell_output(texts_for_hunspell, output)


def parse_hunspell_output(hunspell_input: Dict[str, str], hunspell_output) -> int:
    """Parse `hunspell -a` output.

    Print one line per error on stderr, of the following format:

        FILE:LINE:ERROR

    Returns the number of errors.

    hunspell_input contains a dict of files: all_lines_for_this_file.
    """
    errors = 0
    checked_files = iter(hunspell_input.items())
    checked_file_name, checked_text = next(checked_files)
    checked_lines = iter(checked_text.split("\n"))
    next(checked_lines)
    current_line_number = 1
    for line in hunspell_output.stdout.split("\n")[1:]:
        if not line:
            try:
                next(checked_lines)
                current_line_number += 1
            except StopIteration:
                try:
                    checked_file_name, checked_text = next(checked_files)
                    checked_lines = iter(checked_text.split("\n"))
                    next(checked_lines)
                    current_line_number = 1
                except StopIteration:
                    return errors
            continue
        if line == "*":  # OK
            continue
        if line[0] == "&":
            _, original, *_ = line.split()
            if look_like_a_word(original):
                print(checked_file_name, current_line_number, original, sep=":")
                errors += 1
    raise Unreachable("Got this one? I'm sorry, read XKCD 2200, then open an issue.")


def gracefull_handling_of_missing_dicts(language):
    """Check if hunspell dictionary for given language is installed."""
    hunspell_dash_d = subprocess.check_output(
        ["hunspell", "-D"], universal_newlines=True, stderr=subprocess.STDOUT
    )
    languages = {Path(line).name for line in hunspell_dash_d}

    def error(*args, file=sys.stderr, **kwargs):
        print(*args, file=file, **kwargs)

    if language in languages:
        return
    error(
        "The hunspell dictionary for your language is missing, please install it.",
        end="\n\n",
    )
    if which("apt"):
        error("Maybe try something like:")
        error(f"  sudo apt install hunspell-{language}")
    else:
        error(
            f"""I don't know your environment, but I bet the package name looks like:

    hunspell-{language}

If you find it, please tell me (by opening an issue or a PR on
https://github.com/JulienPalard/pospell/) so I can enhance this error message.
"""
        )
    sys.exit(1)


def main():
    """Entry point (for command-line)."""
    args = parse_args()
    logging.basicConfig(level=50 - 10 * args.verbose)
    default_drop_capitalized = DEFAULT_DROP_CAPITALIZED.get(args.language, False)
    if args.drop_capitalized:
        drop_capitalized = True
    elif args.no_drop_capitalized:
        drop_capitalized = False
    else:
        drop_capitalized = default_drop_capitalized
    args.po_file = list(
        chain(Path(".").glob(args.glob) if args.glob else [], args.po_file)
    )
    if args.modified:
        git_status = subprocess.check_output(
            ["git", "status", "--porcelain", "--no-renames"], encoding="utf-8"
        )
        git_status_lines = [
            line.split(maxsplit=2) for line in git_status.split("\n") if line
        ]
        args.po_file.extend(
            Path(filename)
            for status, filename in git_status_lines
            if filename.endswith(".po") and status != "D"
        )
    try:
        errors = spell_check(
            args.po_file,
            args.personal_dict,
            args.language,
            drop_capitalized,
            args.debug,
        )
    except POSpellException as err:
        print(err, file=sys.stderr)
        sys.exit(-1)
    if errors == -1:
        gracefull_handling_of_missing_dicts(args.language)
    sys.exit(0 if errors == 0 else -1)


if __name__ == "__main__":
    main()
