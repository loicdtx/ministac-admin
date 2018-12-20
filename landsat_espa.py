#!/usr/bin/env python3

import os
import sys
from glob import glob
import re
import xml.etree.ElementTree as ET

from rasterio.crs import CRS
from rasterio.features import bounds
from pyproj import Proj


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


def parse_xml(f):
    # Start parsing xml
    root = ET.parse(f).getroot()
    ns = 'http://espa.cr.usgs.gov/v2'
    product_id = root.find('ns:global_metadata/ns:product_id',
                         namespaces={'ns': ns}).text
    # Build datetime from date and time
    date_str = root.find('ns:global_metadata/ns:acquisition_date',
                         namespaces={'ns': ns}).text
    time_str = root.find('ns:global_metadata/ns:scene_center_time',
                         namespaces={'ns': ns}).text
    dt_str = '%sT%sZ' % (date_str, time_str[:8])
    # satellite sensor metadata
    sensor = root.find('ns:global_metadata/ns:instrument',
                           namespaces={'ns': ns}).text
    spacecraft = root.find('ns:global_metadata/ns:satellite',
                          namespaces={'ns': ns}).text
    # Scene corners in projected coordinates
    utm_zone = int(root.find('ns:global_metadata/ns:projection_information/ns:utm_proj_params/ns:zone_code',
                             namespaces={'ns': ns}).text)
    wrs_path = root.find('ns:global_metadata/ns:wrs',
                         namespaces={'ns': ns}).attrib['path']
    wrs_row = root.find('ns:global_metadata/ns:wrs',
                         namespaces={'ns': ns}).attrib['row']
    crs = CRS({'proj': 'utm',
               'zone': utm_zone})
    return(product_id, dt_str, sensor, spacecraft, crs, wrs_path, wrs_row)


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
    cc, geom = parse_mtl(mtl_file)
    bbox = bounds(geom)
    product_id, dt_str, sensor, spacecraft, crs, wrs_path, wrs_row = parse_xml(xml_file)
    bands_path = os.path.join(path, product_id)
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
             "href": '',
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
