
import os
import itertools
from setuptools import setup

from infi.execute import __version__ as VERSION

def _find_all_subpackages(*packages):
    for root_package in packages:
        root_dir = os.path.dirname(__file__)
        package_root = os.path.abspath(os.path.join(root_dir, root_package))
        yield root_package
        for directory, dirnames, filenames in os.walk(package_root):
            if "__init__.py" not in filenames:
                del dirnames[:]
                continue
            relative_package = os.path.relpath(directory, package_root).replace(os.path.sep, ".")
            if relative_package == '.':
                continue
            yield root_package + "." + relative_package


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
      packages=list(_find_all_subpackages("infi")),
      install_requires=["pyforge"],
      scripts=[],
      )
