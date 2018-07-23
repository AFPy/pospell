# pospell

`pospell` is a spellcheckers for po files containing reStructuedText.


## Usage

```
$ pospell --help
usage: pospell [-h] [-l LANGUAGE] [--glob GLOB]

Check spelling in po files containing restructuredText.

optional arguments:
  -h, --help            show this help message and exit
  -l LANGUAGE, --language LANGUAGE
  --glob GLOB
  -p PERSONAL_DICT, --personal-dict PERSONAL_DICT
```

A personal dict (the `-p` option) is simply a text file with one word
per line.


## Example

pospell "just" lists the wrong words, it's up to you to find where
they are in your file. Yes this can be enhanced by giving the line
number so we could use it as a linter in our editors.

```
$ pospell --language fr --glob *.po
about.po:47:Jr.
about.po:55:reStructuredText
about.po:55:Docutils
about.po:63:Fredrik
about.po:63:Lundh
about.po:75:language
about.po:75:librarie
```