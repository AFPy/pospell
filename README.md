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
```


## Example

pospell "just" lists the wrong words, it's up to you to find where
they are in your file. Yes this can be enhanced by giving the line
number so we could use it as a linter in our editors.

```
$ pospell --language fr --glob *.po
# about.po
reStructuredText
Docutils
Fredrik
Lundh
language
librarie
```
