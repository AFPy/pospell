"""pospell is a spellcheckers for po files containing reStructuedText.
"""
from collections import defaultdict
import io
import logging
import subprocess
import sys
import tempfile
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

__version__ = "1.0.6"

DEFAULT_DROP_CAPITALIZED = {"fr": True, "fr_FR": True}


try:
    HUNSPELL_VERSION = subprocess.check_output(
        ["hunspell", "--version"], universal_newlines=True
    ).split("\n")[0]
except FileNotFoundError:
    print("hunspell not found, please install hunspell.", file=sys.stderr)
    exit(1)


class DummyNodeClass(docutils.nodes.Inline, docutils.nodes.TextElement):
    pass


def monkey_patch_role(role):
    def role_or_generic(role_name, language_module, lineno, reporter):
        base_role, message = role(role_name, language_module, lineno, reporter)
        if base_role is None:
            roles.register_generic_role(role_name, DummyNodeClass)
            base_role, message = role(role_name, language_module, lineno, reporter)
        return base_role, message

    return role_or_generic


roles.role = monkey_patch_role(roles.role)


class NodeToTextVisitor(docutils.nodes.NodeVisitor):
    def __init__(self, document):
        self.output = []
        self.depth = 0
        super().__init__(document)

    def dispatch_visit(self, node):
        self.depth += 1
        super().dispatch_visit(node)

    def dispatch_departure(self, node):
        self.depth -= 1
        super().dispatch_departure(node)

    def unknown_visit(self, node):
        """Mandatory implementation to visit unknwon nodes."""
        # print(" " * self.depth * 4, node.__class__.__name__, ":", node)

    def unknown_departure(self, node):
        """To help debugging tree."""
        # print(node, repr(node), node.__class__.__name__)

    def visit_emphasis(self, node):
        raise docutils.nodes.SkipChildren

    def visit_superscript(self, node):
        raise docutils.nodes.SkipChildren

    def visit_title_reference(self, node):
        raise docutils.nodes.SkipChildren

    def visit_strong(self, node):
        raise docutils.nodes.SkipChildren

    def visit_DummyNodeClass(self, node):
        raise docutils.nodes.SkipChildren

    def visit_reference(self, node):
        raise docutils.nodes.SkipChildren

    def visit_literal(self, node):
        raise docutils.nodes.SkipChildren

    def visit_Text(self, node):
        self.output.append(node.rawsource)

    def __str__(self):
        return " ".join(self.output)


def strip_rst(line):
    if line.endswith("::"):
        # Drop :: at the end, it would cause Literal block expected
        line = line[:-2]
    parser = docutils.parsers.rst.Parser()
    components = (docutils.parsers.rst.Parser,)
    settings = docutils.frontend.OptionParser(
        components=components
    ).get_default_values()
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
        # Strip accronyms
        r"\b[\w-]*\p{Uppercase}{2,}[0-9.\w-]*\b",
        r"---?",  # -- and --- separators to be ignored
        r" - ",  # Drop lone dashes (sometimes used in place of -- or ---)
        r"-\\ ",  # Ignore "MINUS BACKSLASH SPACE" typically used in
        # formulas, like '-\ *π*' but *π* gets removed too
        r"{[a-z_]*?}",  # Sphinx variable
        r"'?-?\b([0-9]+\.)*[0-9]+\.[0-9abcrx]+\b'?",  # Versions
        r"[0-9]+h",  # Hours
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


def po_to_text(po_path, drop_capitalized=False):
    """Converts a po file to a text file, by stripping the msgids and all
    po syntax, but by keeping the kept lines at their same position /
    line number.
    """
    buffer = []
    lines = 0
    entries = polib.pofile(po_path)
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
        help="Always drop capitalized words in sentences (defaults according to the language).",
    )
    parser.add_argument(
        "--no-drop-capitalized",
        action="store_true",
        help="Never drop capitalized words in sentences (defaults according to the language).",
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
        exit(1)
    if not args.po_file and not args.modified:
        parser.print_help()
        exit(1)
    return args


def spell_check(
    po_files,
    personal_dict=None,
    language="en_EN",
    drop_capitalized=False,
    debug_only=False,
):
    """Check for spelling mistakes in the files po_files (po format,
    containing restructuredtext), for the given language.
    personal_dict allow to pass a personal dict (-p) option, to hunspell.

    Debug only will show what's passed to Hunspell instead of passing it.
    """
    errors = []
    personal_dict_arg = ["-p", personal_dict] if personal_dict else []
    for po_file in po_files:
        if debug_only:
            print(po_to_text(str(po_file), drop_capitalized))
            continue
        text_for_hunspell = po_to_text(str(po_file), drop_capitalized)
        try:
            output = subprocess.run(
                ["hunspell", "-d", language, "-l"] + personal_dict_arg,
                universal_newlines=True,
                input=text_for_hunspell,
                stdout=subprocess.PIPE,
            )
        except subprocess.CalledProcessError:
            return -1
        if not output.stdout:
            continue  # No errors :)
        line_of_words = defaultdict(set)
        for misspelled_word in {word for word in output.stdout.split("\n") if word}:
            for line_number, line in enumerate(text_for_hunspell.split("\n"), start=1):
                if misspelled_word in line:
                    errors.append((po_file, line_number, misspelled_word))
    errors.sort()
    for error in errors:
        print(":".join(str(token) for token in error))
    return len(errors)


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
        error("  sudo apt install hunspell-{}".format(language))
    else:
        error(
            """I don't know your environment, but I bet the package name looks like:

    hunspell-{language}

If you find it, please tell me (by opening an issue or a PR on
https://github.com/JulienPalard/pospell/) so I can enhance this error message.
""".format(
                language=language
            )
        )
    exit(1)


def main():
    """Module entry point."""
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
            ["git", "status", "--porcelain"], encoding="utf-8"
        )
        git_status_lines = [
            line.split(maxsplit=2) for line in git_status.split("\n") if line
        ]
        args.po_file.extend(
            Path(filename)
            for status, filename in git_status_lines
            if filename.endswith(".po")
        )
    errors = spell_check(
        args.po_file, args.personal_dict, args.language, drop_capitalized, args.debug
    )
    if errors == -1:
        gracefull_handling_of_missing_dicts(args.language)
    exit(0 if errors == 0 else -1)


if __name__ == "__main__":
    main()
