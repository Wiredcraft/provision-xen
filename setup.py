#!/usr/bin/env python
import os
import sys
import shutil
from glob import glob

from provision import __version__, __author__, __author_email__

try:
    from setuptools import setup
except ImportError:
    print 'Setuptools is required.'
    sys.exit(1)

setup(
    name='provision',
    version=__version__,
    description='Batt simply backup all the things; databases and files',
    url = 'https://github.com/wiredcraft/provision-xen',
    author=__author__,
    author_email=__author_email__,
    license='MIT',
    install_requires=['docopt'],
    package_dir={ 
        'provision': 'provision'
    },
    packages=[
       'provision'
    ],
    scripts=[
        'bin/provision'
    ]
)


