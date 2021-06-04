#!/usr/bin/env python

from Cython.Build import cythonize
from setuptools import setup
from setuptools.extension import Extension

extensions = Extension('clara.pylpsolve', ['clara/pylpsolve.pyx'],
                       libraries=['lpsolve55'], library_dirs=['/usr/lib/lp_solve'])

setup(name='clara',
      version='1.0',
      packages=['clara'],
      ext_modules = cythonize(extensions),
      install_requires=['pycparser', 'zss'],
      scripts=['bin/clara']
     )