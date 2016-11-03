#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import sys
from os import path
from codecs import open

from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand

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


class Tox(TestCommand):
    user_options = [('tox-args=', 'a', 'Arguments to pass to tox')]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.tox_args = None

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        # Import here. Outside the .eggs/ will not load
        import tox
        import shlex
        args = self.tox_args
        if args:
            args = shlex.split(self.tox_args)
        errno = tox.cmdline(args=args)
        sys.exit(errno)

setup(
    name='jwplatform',
    version=get_version(),
    description='A Python client library for accessing JW Platform API',
    long_description=read_file('README.rst') + '\n\n' + read_file('CHANGES.rst'),
    url='https://github.com/jwplayer/jwplatform-py',
    author='Sergey Lashin, LongTail Ad Solutions, Inc.',
    author_email='support@jwplayer.com',
    license='MIT',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
    keywords=['JW Platform', 'api', 'client'],
    packages=find_packages(exclude=['docs', 'tests', 'examples']),
    install_requires=[
        'requests>=2.11.0'
    ],
    tests_require=[
        'tox',
        'pytest',
        'virtualenv',
        'responses>=0.5.1'
    ],
    cmdclass={'test': Tox}
)
