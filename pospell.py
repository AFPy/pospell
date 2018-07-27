#!/usr/bin/env python3


import re
import subprocess
import sys
import tempfile
from pathlib import Path

import polib


def strip_rst(line):
    """Strip out reStructuredText and Sphinx-doc tags from a line.
    """
    return re.sub(
        r"""(C-)?:[^:]*?:`[^`]*?` |
            ``.*?``               |
            \b[A-Z][a-zA-Z-]{2,}[a-zA-Z.-]*\b |  # Strip capitalized words and accronyms
            {[a-z]*?}             | # reStructuredText tag
            \|[a-z]+?\|           | # reStructuredText substitution
            %\([a-z_]+?\)s        | # Sphinx variable
            -[A-Za-z]\b           |
            `[^`]*?`_             |
            \*[^*]*?\*
        """, '', line, flags=re.VERBOSE)


def clear(line):
    """Clear various other syntaxes we may encounter in a line.
    """
    return re.sub(r"""<a href="[^"]*?">(.*)</a>""", r"\1", line)


def po_to_text(po):
    buffer = []
    lines = 0
    entries = polib.pofile(po)
    for entry in entries:
        if entry.msgid == entry.msgstr:
            continue
        while lines < entry.linenum:
            buffer.append('')
            lines += 1
        buffer.append(clear(strip_rst(entry.msgstr)))
        lines += 1
    return '\n'.join(buffer)


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description='Check spelling in po files containing restructuredText.')
    parser.add_argument('-l', '--language', type=str, default='fr')
    parser.add_argument('--glob', type=str, default='**/*.po')
    parser.add_argument('--debug', action='store_true')
    parser.add_argument('-p', '--personal-dict', type=str)
    args = parser.parse_args()
    personal_dict = ['-p', args.personal_dict] if args.personal_dict else []
    errors = 0
    with tempfile.TemporaryDirectory() as tmpdirname:
        tmpdir = Path(tmpdirname)
        for po_file in Path('.').glob(args.glob):
            if args.debug:
                print(po_to_text(str(po_file)))
                continue
            (tmpdir / po_file.name).write_text(po_to_text(str(po_file)))
            output = subprocess.check_output(
                ['hunspell', '-d', args.language] + personal_dict + ['-u3',
                 str(tmpdir / po_file.name)],
                universal_newlines=True)
            for line in output.split('\n'):
                match = re.match(r'(?P<path>.*):(?P<line>[0-9]+): Locate: (?P<error>.*) \| Try: .*$', line)
                if match:
                    errors += 1
                    print(match.group('path').replace(str(tmpdir), '').lstrip('/'),
                          match.group('line'),
                          match.group('error'),
                          sep=':')
    exit(0 if errors == 0 else -1)


if __name__ == '__main__':
    main()
