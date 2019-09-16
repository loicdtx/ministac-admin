import pkg_resources
import pickle

__version__ = "0.0.1"

landsat_fc_path = pkg_resources.resource_filename('msadmin', 'data/wrs2_grid.pkl')
with open(landsat_fc_path, 'rb') as con:
    LANDSAT_FOOTPRINTS = pickle.load(con)
