#!/usr/bin/env python3

import os
import sys
from glob import glob
import re
import xml.etree.ElementTree as ET

from rasterio.crs import CRS
from pyproj import Proj


def mlt_to_cc(f):
    pass


def mtl_to_geom(f):
    pass


def xml_to_meta(f):
    pass


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
    # Start parsing xml
    root = ET.parse(mtl_file).getroot()
    ns = 'http://espa.cr.usgs.gov/v2'
    # Build datetime from date and time
    date_str = root.find('ns:global_metadata/ns:acquisition_date',
                         namespaces={'ns': ns}).text
    time_str = root.find('ns:global_metadata/ns:scene_center_time',
                         namespaces={'ns': ns}).text
    dt_str = '%sT%s' % (date_str, time_str[:8])
    # satellite sensor metadata
    sensor = root.find('ns:global_metadata/ns:instrument',
                           namespaces={'ns': ns}).text
    spacecraft = root.find('ns:global_metadata/ns:satellite',
                          namespaces={'ns': ns}).text
    # Scene corners in projected coordinates
    utm_zone = int(root.find('ns:global_metadata/ns:projection_information/ns:utm_proj_params/ns:zone_code',
                             namespaces={'ns': ns}).text)
    crs = CRS({'proj': 'utm',
               'zone': utm_zone})
    d = {"id": scene_id,
         "type": "Feature",
         "bbox": bbox,
         "geometry": geom,
         "properties": {
           "datetime": dt_str,
           "c:description": "Landsat data processed to surface reflectance on the espa platform",
           "eo:processing_level": level, # e.g. L1T
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
             "href": metadata_path,
             "type": "mtl"
           },
           "blue": {
             "href": blue_path,
             "type": "image/vnd.stac.geotiff",
           },
           "green": {
             "href": green_path,
             "type": "image/vnd.stac.geotiff",
           },
           "red": {
             "href": red_path,
             "type": "image/vnd.stac.geotiff",
           },
           "nir": {
             "href": nir_path,
             "type": "image/vnd.stac.geotiff",
           },
           "swir1": {
             "href": swir1_path,
             "type": "image/vnd.stac.geotiff",
           },
           "swir2": {
             "href": swir2_path,
             "type": "image/vnd.stac.geotiff",
           },
           "pixel_qa": {
             "href": pixel_qa_path,
             "type": "image/vnd.stac.geotiff",
           },
           "radsat_qa": {
             "href": radsat_qa_path,
             "type": "image/vnd.stac.geotiff",
           }
         }
        }
    return d
