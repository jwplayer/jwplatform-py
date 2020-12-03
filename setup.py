#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
from os import path
from codecs import open

from setuptools import setup, find_packages

here = path.abspath(path.dirname(__file__))


def read_file(*names, **kwargs):
    with open(
        path.join(here, *names),
        encoding=kwargs.get('encoding', 'utf8')
    ) as f:
        return f.read()


def get_version():
    version_file = read_file('jwplatform', '__init__.py')
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                              version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError('Unable to find version string.')


setup(
    name='jwplatform',
    version=get_version(),
    description='A Python client library for accessing JW Platform API',
    long_description=read_file('README.rst') + '\n\n' + read_file('CHANGES.rst'),
    url='https://github.com/jwplayer/jwplatform-py',
    author='Kamil Sindi',
    author_email='support@jwplayer.com',
    license='MIT',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3 :: Only',
    ],
    keywords=['JW Platform', 'api', 'client', 'JW Player'],
    packages=find_packages(exclude=['docs', 'tests', 'examples']),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'requests>=2.24.0'
    ],
    setup_requires=[
        'pytest-runner',
    ],
    tests_require=[
        'pytest',
        'pytest-cov',
        'responses>=0.12.0',
        'networktest'
    ],
)
