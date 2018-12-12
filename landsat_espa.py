def parse_scene(path):
    """Function to parse a single scene

    Args:
        path (str): The path to the directory containing the data

    Return:
        dict: Item dict compliant with stac specifications
    """
    d = {"id": scene_id,
         "type": "Feature",
         "bbox": bbox,
         "geometry": geom,
         "properties": {
           "datetime": dt_str,
           "c:level": level, # e.g. L1T
           "c:description": "Landsat data processed to surface reflectance on the espa platform",
           "eo:gsd": 30.0,
           "eo:cloud_cover" : cc,
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
           }
         }
        }
    return d
