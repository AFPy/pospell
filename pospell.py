#!/usr/bin/env python3


import tempfile
import subprocess
import sys
from pathlib import Path
import polib
import re


def strip_rst(line):
    return re.sub(
        r""":[^:]*?:`[^`]*?` |
            ``.*?`` |
            {[a-z]*?} |  # Sphinx tag
            -[A-Za-z]\b |
            `[^`]*?`_ |
            \*[^*]*?\*
        """, '', line, flags=re.VERBOSE)


def po_to_text(po):
    buffer = []
    entries = polib.pofile(po)
    for entry in entries:
        buffer.append(strip_rst(entry.msgstr))
    return '\n'.join(buffer)


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description='Check spelling in po files containing restructuredText.')
    parser.add_argument('-l', '--language', type=str, default='fr')
    parser.add_argument('--glob', type=str, default='**/*.po')
    args = parser.parse_args()
    with tempfile.TemporaryDirectory() as tmpdirname:
        tmpdir = Path(tmpdirname)
        for po_file in Path('.').glob(args.glob):
            (tmpdir / po_file.name).write_text(po_to_text(str(po_file)))
            print('#', po_file.name)
            output = subprocess.check_output(
                ['hunspell', '-d', args.language, '-p', 'perso', '-l',
                 str(tmpdir / po_file.name)],
                universal_newlines=True)
            print(output)


if __name__ == '__main__':
    main()
