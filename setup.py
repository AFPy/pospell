#!/usr/bin/env python3

import setuptools

with open('README.md') as readme:
    long_description = readme.read()

setuptools.setup(
    name='pospell',
    version='0.0.3',
    description="Spellcheck .po files containing reStructuredText translations",
    long_description=long_description,
    long_description_content_type='text/markdown', # This is important!
    author="Julien Palard",
    author_email='julien@palard.fr',
    url='https://github.com/JulienPalard/pospell',
    py_modules=[
        'pospell',
    ],
    entry_points={
        'console_scripts': ['pospell=pospell:main']
    },
    install_requires=['polib'],
    license="MIT license",
    keywords='po spell gettext',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6'
    ]
)
