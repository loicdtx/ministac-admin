#!/usr/bin/env python3

from pprint import pprint
import os
import sys
import argparse
from glob import glob
import re
import xml.etree.ElementTree as ET

from rasterio.crs import CRS
from rasterio.features import bounds
from pyproj import Proj


LANDSAT_BANDS = {'TM': {'blue': 'sr_band1',
                        'green': 'sr_band2',
                        'red': 'sr_band3',
                        'nir': 'sr_band4',
                        'swir1': 'sr_band5',
                        'swir2': 'sr_band7',
                        'pixel_qa': 'pixel_qa',
                        'radsat_qa': 'radsat_qa'},
                 'OLI_TIRS': {'blue': 'sr_band2',
                              'green': 'sr_band3',
                              'red': 'sr_band4',
                              'nir': 'sr_band5',
                              'swir1': 'sr_band6',
                              'pixel_qa': 'pixel_qa',
                              'radsat_qa': 'radsat_qa',
                              'swir2': 'sr_band7'}}
LANDSAT_BANDS['ETM'] = LANDSAT_BANDS['TM']


def parse_mtl(f):
    with open(f) as fp:
        for line in fp:
            if 'CORNER_UL_LAT_PRODUCT' in line:
                ul_lat = float(line.split('=')[1].strip())
                continue
            if 'CORNER_UL_LON_PRODUCT' in line:
                ul_lon = float(line.split('=')[1].strip())
                continue
            if 'CORNER_UR_LAT_PRODUCT' in line:
                ur_lat = float(line.split('=')[1].strip())
                continue
            if 'CORNER_UR_LON_PRODUCT' in line:
                ur_lon = float(line.split('=')[1].strip())
                continue
            if 'CORNER_LL_LAT_PRODUCT' in line:
                ll_lat = float(line.split('=')[1].strip())
                continue
            if 'CORNER_LL_LON_PRODUCT' in line:
                ll_lon= float(line.split('=')[1].strip())
                continue
            if 'CORNER_LR_LAT_PRODUCT' in line:
                lr_lat = float(line.split('=')[1].strip())
                continue
            if 'CORNER_LR_LON_PRODUCT' in line:
                lr_lon = float(line.split('=')[1].strip())
                continue
            if 'CLOUD_COVER_LAND' in line:
                cc = float(line.split('=')[1].strip())
                continue
    coords = [[[ul_lon, ul_lat],
               [ll_lon, ll_lat],
               [lr_lon, lr_lat],
               [ur_lon, ur_lat],
               [ul_lon, ul_lat]]]
    geom = {'type': 'Polygon',
            'coordinates': coords}
    return (cc, geom)


def parse_xml(root, field, attrib=None, ns='http://espa.cr.usgs.gov/v2'):
    if attrib is None:
        out = root.find('ns:global_metadata/ns:%s' % field,
                        namespaces={'ns': ns}).text
    else:
        out = root.find('ns:global_metadata/ns:%s' % field,
                        namespaces={'ns': ns}).attrib[attrib]
    return out


def get_band_path(root, color, instrument, ns='http://espa.cr.usgs.gov/v2'):
    out = root.find('ns:bands/ns:band[@name="%s"]/ns:file_name' %
                    LANDSAT_BANDS[instrument][color],
                    namespaces={'ns': ns}).text
    return out


def parse_scene(path):
    """Function to parse a single scene

    Args:
        path (str): The path to the directory containing the data

    Return:
        dict: Item dict compliant with stac specifications
    """
    # Check that the directory contains both MTL.txt and .xml file
    # use mtl.txt to get cloud cover as well as four corners coordinates
    xml_pattern = re.compile(r'[A-Z0-9]{4}_[A-Z0-9]{4}_\d{6}_\d{8}_\d{8}_01_(T1|T2|RT)\.xml$')
    mtl_pattern = re.compile(r'[A-Z0-9]{4}_[A-Z0-9]{4}_\d{6}_\d{8}_\d{8}_01_(T1|T2|RT)_MTL\.txt$')
    # Check that path is a dir and contains appropriate files
    if not os.path.isdir(path):
        raise ValueError('Argument path= is not a directory')
    file_list = glob(os.path.join(path, '*'))
    # Filter list of xml files with regex (there could be more than one in case
    # some bands have been opend in qgis for example)
    xml_file_list = [x for x in file_list if xml_pattern.search(x)]
    mtl_file_list = [x for x in file_list if mtl_pattern.search(x)]
    print(mtl_file_list)
    if (len(mtl_file_list) != 1) or (len(xml_file_list) != 1):
        raise ValueError('Could not identify a unique xml or mtl metadata file')
    mtl_file = mtl_file_list[0]
    xml_file = xml_file_list[0]
    # Start parsing
    # First mtl
    cc, geom = parse_mtl(mtl_file)
    bbox = bounds(geom)
    # second xml
    root = ET.parse(xml_file).getroot()
    product_id = parse_xml(root, 'product_id')
    # Date and time
    date_str = parse_xml(root, 'acquisition_date')
    time_str = parse_xml(root, 'scene_center_time')
    dt_str = '%sT%sZ' % (date_str, time_str[:8])
    # sensor
    sensor = parse_xml(root, 'instrument')
    # Spacecraft
    spacecraft = parse_xml(root, 'satellite')
    # crs
    utm_zone = int(root.find('ns:global_metadata/ns:projection_information/ns:utm_proj_params/ns:zone_code',
                             namespaces={'ns': 'http://espa.cr.usgs.gov/v2'}).text)
    crs = CRS({'proj': 'utm',
               'zone': utm_zone})
    # WRS2 PR
    wrs_path = parse_xml(root, 'wrs', 'path')
    wrs_row = parse_xml(root, 'wrs', 'row')

    # Build dictionary
    d = {"id": product_id,
         "type": "Feature",
         "bbox": bbox,
         "geometry": geom,
         "properties": {
           "datetime": dt_str,
           "c:description": "Landsat data processed to surface reflectance on the espa platform",
           "eo:processing_level": 'L1', # e.g. L1T
           "eo:spacecraft": spacecraft,
           "eo:sensor": sensor,
           "eo:gsd": 30.0,
           "eo:cloud_cover": cc,
           "eo:crs": crs.to_string(),
           "landsat:wrs_path": wrs_path,
           "landsat:wrs_row": wrs_row,
         },
         "assets" :{
           "metadata": {
             "href": xml_file,
             "type": "xml"
           },
           "blue": {
             "href": os.path.join(path, get_band_path(root, 'blue', sensor)),
             "type": "image/vnd.stac.geotiff",
           },
           "green": {
             "href": os.path.join(path, get_band_path(root, 'green', sensor)),
             "type": "image/vnd.stac.geotiff",
           },
           "red": {
             "href": os.path.join(path, get_band_path(root, 'red', sensor)),
             "type": "image/vnd.stac.geotiff",
           },
           "nir": {
             "href": os.path.join(path, get_band_path(root, 'nir', sensor)),
             "type": "image/vnd.stac.geotiff",
           },
           "swir1": {
             "href": os.path.join(path, get_band_path(root, 'swir1', sensor)),
             "type": "image/vnd.stac.geotiff",
           },
           "swir2": {
             "href": os.path.join(path, get_band_path(root, 'swir2', sensor)),
             "type": "image/vnd.stac.geotiff",
           },
           "pixel_qa": {
             "href": os.path.join(path, get_band_path(root, 'pixel_qa', sensor)),
             "type": "image/vnd.stac.geotiff",
           },
           "radsat_qa": {
             "href": os.path.join(path, get_band_path(root, 'radsat_qa', sensor)),
             "type": "image/vnd.stac.geotiff",
           }
         }
        }
    return d

if __name__ == '__main__':
    epilog = """
Populate the ministac database with metadata parsed from a list of Landsat espa
scenes. Essential metadata are parsed from the xml and MTL file present in each directory.

--------------
Example usage
--------------
./landsat_espa.py LC08*
"""
    parser = argparse.ArgumentParser(epilog=epilog,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument('paths',
                        nargs='+',
                        help = 'List of directories containing landsat data processed by espa')
    parsed_args = parser.parse_args()
    dict_list = []
    for path in vars(parsed_args)['paths']:
        try:
            dict_list.append(parse_scene(path))
        except Exception as e:
            print('skipped %s\nreason: %s' % (path, e))
    pprint(dict_list)
