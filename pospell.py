"""pospell is a spellcheckers for po files containing reStructuedText.
"""
import io
import re
import subprocess
import sys
import tempfile
from contextlib import redirect_stderr, redirect_stdout
from itertools import chain
from pathlib import Path
from types import SimpleNamespace

import docutils.frontend
import docutils.nodes
import docutils.parsers.rst
import polib
from docutils.parsers.rst import roles
from docutils.utils import new_document

__version__ = "0.2.2"
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
        super().__init__(document)

    def unknown_visit(self, node):
        pass
        # self.output.append(node.__class__.__name__ + ": " + node.rawsource)

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
        document = docutils.utils.new_document("<rst-doc>", settings=settings)
        parser.parse(line, document)
    stderr = stderr_stringio.getvalue()
    if stderr:
        print(stderr.strip(), "while parsing:", line)
    visitor = NodeToTextVisitor(document)
    document.walk(visitor)
    return str(visitor)


def clear(line):
    """Clear various other syntaxes we may encounter in a line.
    """
    return re.sub(
        r"""
    <a\ href="[^"]*?">             |  # Strip HTML links
    \b[A-Z][a-zA-Z-]+[a-zA-Z.-]*\b |  # Strip capitalized words and accronyms
    ---?                           |  # -- and --- separators to be ignored
    -\\\                           |  # Ignore "MINUS BACKSLASH SPACE" typically used in
                                      # formulas, like '-\ *π*' but *π* gets removed too
    {[a-z]*?}                         |  # Sphinx variable
    %\([a-z_]+?\)s                       # Sphinx variable
    """,
        r"",
        line,
        flags=re.VERBOSE,
    )


def po_to_text(po_path):
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
        buffer.append(clear(strip_rst(entry.msgstr)))
        lines += 1
    return "\n".join(buffer)


def parse_args():
    """Parse command line arguments.
    """
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
        "po_file",
        nargs="*",
        type=Path,
        help="Files to check, can optionally be mixed with --glob, or not, "
        "use the one that fit your needs.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s " + __version__ + " using hunspell: " + HUNSPELL_VERSION,
    )
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("-p", "--personal-dict", type=str)
    return parser.parse_args()


def main():
    """Module entry point.
    """
    args = parse_args()
    personal_dict = ["-p", args.personal_dict] if args.personal_dict else []
    errors = 0
    with tempfile.TemporaryDirectory() as tmpdirname:
        tmpdir = Path(tmpdirname)
        for po_file in chain(
            Path(".").glob(args.glob) if args.glob else [], args.po_file
        ):
            if args.debug:
                print(po_to_text(str(po_file)))
                continue
            (tmpdir / po_file.name).write_text(po_to_text(str(po_file)))
            output = subprocess.check_output(
                ["hunspell", "-d", args.language]
                + personal_dict
                + ["-u3", str(tmpdir / po_file.name)],
                universal_newlines=True,
            )
            for line in output.split("\n"):
                match = re.match(
                    r"(?P<path>.*):(?P<line>[0-9]+): Locate: (?P<error>.*) \| Try: .*$",
                    line,
                )
                if match:
                    errors += 1
                    print(
                        match.group("path").replace(str(tmpdir), "").lstrip("/"),
                        match.group("line"),
                        match.group("error"),
                        sep=":",
                    )
    exit(0 if errors == 0 else -1)


if __name__ == "__main__":
    main()
