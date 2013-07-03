#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

from opps import wiki


install_requires = ["opps"]

classifiers = ["Development Status :: 4 - Beta",
               "Intended Audience :: Developers",
               "Operating System :: OS Independent",
               "Framework :: Django",
               'Programming Language :: Python',
               "Programming Language :: Python :: 2.7",
               "Operating System :: OS Independent",
               "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
               'Topic :: Software Development :: Libraries :: Python Modules']

try:
    long_description = open('README.md').read()
except:
    long_description = wiki.__description__

setup(name='opps-wiki',
      namespace_packages=['opps'],
      version=wiki.__version__,
      description=wiki.__description__,
      long_description=long_description,
      classifiers=classifiers,
      keywords='wiki app-wiki app opps cms',
      author=wiki.__author__,
      author_email=wiki.__email__,
      packages=find_packages(exclude=('doc', 'docs',)),
      install_requires=install_requires,
      include_package_data=True,)
