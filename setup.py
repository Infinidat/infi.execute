import os
import platform
import itertools
from setuptools import setup, find_packages

with open(os.path.join(os.path.dirname(__file__), "infi", "execute", "__version__.py")) as version_file:
    exec version_file.read()

_INSTALL_REQUIREMENTS = ["pyforge"]
if platform.python_version() < '2.7':
    _INSTALL_REQUIREMENTS.append('unittest2')

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
      version=__version__,
      packages=find_packages(exclude=["tests"]),
      namespace_packages=["infi"],
      install_requires=_INSTALL_REQUIREMENTS,
      scripts=[],
      )
