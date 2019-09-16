import os

from pyproj import CRS
from shapely.geometry import shape

from msadmin.utils import read_txt, read_xml
from msadmin import LANDSAT_FOOTPRINTS


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



def parse_xml(root, field, attrib=None, ns='http://espa.cr.usgs.gov/v2'):
    """Helper function to easily parse landsat ET root as returned by read_xml
    """
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


def parse(path, bucket=None):
    """Function to parse a single scene

    Args:
        path (str): The path to the directory containing the data

    Return:
        dict: Item dict compliant with stac specifications
    """
    mtl = read_txt(path)
    root = read_xml(path)
    # We only need cloud cover from mtl file
    for line in mtl:
        if 'CLOUD_COVER_LAND' in line:
            cc = float(line.split('=')[1].strip())
            break
    # Retrieve all required info from xml metadata file
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

    # Footprint geometry
    pr_str = '%03d%03d' % (int(wrs_path), int(wrs_row))
    geom = LANDSAT_FOOTPRINTS[pr_str]
    bbox = shape(geom).bounds

    # build path 
    path_type = 'filesystem'
    if bucket is not None:
        path = 's3:/%s' % path
        path_type = 's3'

    # Build dictionary
    d = {"id": product_id,
         "type": "Feature",
         "bbox": list(bbox),
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
           "root": {
             "href": path,
             "type": path_type
           }
         }
        }
    return d
