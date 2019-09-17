#!/usr/bin/env python3

from pprint import pprint
import os
import sys
import argparse
from importlib import import_module

from jsonschema import validate
import ministac
from ministac.globals import ITEM_SCHEMA
from ministac.db import session_scope

from msadmin.datasets.landsat import parse


if __name__ == '__main__':
    epilog = """
Populate the ministac database with metadata parsed from a list of scenes

--------------
Example usage
--------------
# First, dry run to make sure parsing is successful
add_items.py /path/to/scenes/LC08* --collection landsat_sr_8 --parser landsat --dryrun

# In case of validation errors (Invalid json), investigate what's invalid
landsat_espa.py /path/to/scenes/LC08* --collection landsat_sr_8 --parser landsat --dryrun --reason

# If everything is OK, ingest the metadata in the ministac database
landsat_espa.py /path/to/scenes/LC08* --collection landsat_sr_8 --parser landsat --dryrun
"""
    parser = argparse.ArgumentParser(epilog=epilog,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument('paths',
                        nargs='+',
                        help='List of directories containing landsat data processed by espa')
    parser.add_argument('-c', '--collection',
                        required=False,
                        type=str,
                        help='Name of the collection (must already exist in the ministac database)')
    parser.add_argument('-parser', '--parser',
                        required=True,
                        type=str,
                        help='One of the parsers available in msadmin.datasets')
    parser.add_argument('--dryrun',
                        action='store_true',
                        help='Parses and validates generated metadata without ingesting to db')
    parser.add_argument('--reason',
                        action='store_true',
                        help='In case dry run returns validation errors (invalid jsons), re-run it and print the reason of the invalidity')
    parsed_args = vars(parser.parse_args())
    try:
        module = import_module('msadmin.datasets.%s' % parsed_args['parser'])
        parse = module.parse
    except ImportError as e:
        raise ValueError('Invalid parser name')
    if parsed_args['dryrun']:
        for path in parsed_args['paths']:
            print(path)
            try:
                scene_meta = parse(path)
                try:
                    validate(scene_meta, ITEM_SCHEMA)
                    print('OK')
                except Exception as e:
                    print('Invalid json')
                    if parsed_args['reason']:
                        print(e)
            except Exception as e:
                print('Failed to parse scene metadata')
                if parsed_args['reason']:
                    print(e)
    else:
        if parsed_args['collection'] is None:
            print('You must provide the name of an existing collection')
            sys.exit()
        dict_list = []
        for path in parsed_args['paths']:
            try:
                dict_list.append(parse(path))
            except Exception as e:
                print('skipped %s\nreason: %s' % (path, e))
        with session_scope() as session:
            ministac.add_items(session, dict_list, parsed_args['collection'])

