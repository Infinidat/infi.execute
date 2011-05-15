
import os
import itertools
from setuptools import setup, find_packages

from infi.execute import __version__ as VERSION

setup(name="infi.execute",
      classifiers = [
          "Development Status :: 4 - Beta",
          "Intended Audience :: Developers",
          "License :: OSI Approved :: BSD License",
          "Programming Language :: Python :: 2.6",
          ],
      description="wrapper library for executing system commands from Python",
      license="BSD",
      author="Rotem Yaari",
      author_email="",
      #url="your.url.here",
      version=VERSION,
      packages=find_packages(exclude=["tests"]),
      namespace_packages=["infi"],
      install_requires=["pyforge"],
      scripts=[],
      )
