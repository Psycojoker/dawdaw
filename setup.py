#!/usr/bin/python
# -*- coding:Utf-8 -*-

# "THE BELGIAN BEER-WARE LICENSE" (Revision 42):
# <cortex@worlddomination.be> wrote this file. As long as you retain this notice
# you can do whatever you want with this stuff. If we meet some day, and you
# think this stuff is worth it, you can buy me a belgian beer in return -- Laurent Peuch

from setuptools import setup

setup(name='dawdaw',
      version='0.1.2',
      description='salt renderer for extremly lazy python dev',
      author='Laurent Peuch',
      long_description=open("README.md", "r").read(),
      author_email='cortex@worlddomination.be',
      url='https://github.com/Psycojoker/dawdaw',
      install_requires=[],
      packages=['dawdaw'],
      py_modules=[],
      license='beerware',
      scripts=[],
      keywords='salt renderer',
     )
