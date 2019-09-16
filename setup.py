#!/usr/bin/env python
# -*- coding: utf-8 -*-

import codecs
from setuptools import setup, find_packages
import os

# Parse the version from the main __init__.py
with open('msadmin/__init__.py') as f:
    for line in f:
        if line.find("__version__") >= 0:
            version = line.split("=")[1].strip()
            version = version.strip('"')
            version = version.strip("'")
            continue


extra_reqs = {'docs': ['sphinx',
                       'sphinx-rtd-theme'],
              's3': ['boto3']}

with codecs.open('README.rst', encoding='utf-8') as f:
    readme = f.read()

setup(name='ministac-admin',
      version=version,
      description=u"Utils and script to ingest satellite image collections into ministac catalog",
      long_description=readme,
      keywords='stac, satellite, spatial, catalog',
      author=u"Loic Dutrieux",
      author_email='loic.dutrieux@gmail.com',
      url='https://github.com/loicdtx/ministac-admin',
      license='GPLv3',
      classifiers=[
          'Programming Language :: Python :: 3.5',
          'Programming Language :: Python :: 3.6',
          'Programming Language :: Python :: 3.7',
      ],
      packages=find_packages(),
      include_package_data=True,
      install_requires=[
          'ministac',
          'pyyaml',
          'jsonschema',
          'pyproj',
          'shapely',
      ],
      scripts=['msadmin/scripts/add_collection.py',
               'msadmin/scripts/add_items.py'],
      extras_require=extra_reqs)

