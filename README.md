# pospell

`pospell` is a spellcheckers for po files containing reStructuedText.


## Examples

By giving files to `pospell`:
```
$ pospell --language fr about.po
about.po:47:Jr.
about.po:55:reStructuredText
about.po:55:Docutils
about.po:63:Fredrik
about.po:63:Lundh
about.po:75:language
about.po:75:librarie
```

By using a bash expansion (note that we do not put quotes around
`*.po` to let bash do its expansion):

```
$ pospell --language fr *.po
…
```

By using a glob pattern (note that we *do* put quotes around `**/*.po`
to keep your shell from trying to expand it, we'll let Python do the
expansion:

```
$ pospell --language fr --glob '**/*.po'
…
```

## Usage

```
usage: pospell [-h] [-l LANGUAGE] [--glob GLOB] [--debug] [-p PERSONAL_DICT]
               [po_file [po_file ...]]

Check spelling in po files containing restructuredText.

positional arguments:
  po_file               Files to check, can optionally be mixed with --glob,
                        or not, use the one that fit your needs.

optional arguments:
  -h, --help            show this help message and exit
  -l LANGUAGE, --language LANGUAGE
                        Language to check, you'll have to install the
                        corresponding hunspell dictionary, on Debian see apt
                        list 'hunspell-*'.
  --glob GLOB           Provide a glob pattern, to be interpreted by pospell,
                        to find po files, like --glob '**/*.po'.
  --debug
  -p PERSONAL_DICT, --personal-dict PERSONAL_DICT
```

A personal dict (the `-p` option) is simply a text file with one word
per line.
