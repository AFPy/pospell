#!/usr/bin/env python3

import setuptools

setuptools.setup(
    name='pospell',
    version='0.0.1',
    description="Spellcheck .po files containing reStructuredText translations",
    author="Julien Palard",
    author_email='julien@palard.fr',
    url='https://github.com/JulienPalard/pospell',
    modules=[
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
