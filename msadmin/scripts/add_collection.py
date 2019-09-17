#!/usr/bin/env python3

import os
import sys
import argparse

import yaml

import ministac
from ministac.db import session_scope


if __name__ == '__main__':
    epilog = """
Read a collection description from a yaml file and add it to the ministac database

--------------
Example usage
--------------
./add_collection.py collections/landsat_sr_8.yaml
"""
    parser = argparse.ArgumentParser(epilog=epilog,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument('meta_file',
                        help='Path to yaml file containing collection metadata')
    parsed_args = vars(parser.parse_args())

    with open(parsed_args['meta_file']) as src:
        collection = yaml.load(src)

    with session_scope() as session:
        ministac.add_collection(session, collection)
