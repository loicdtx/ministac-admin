import xml.etree.ElementTree as ET
import tarfile
import os
from glob import glob

from msadmin.utils import s3


def read_xml(path, bucket=None):
    """Read a xml file, either from filesystem path, archive or s3 bucket

    The target, whether it is an archive, a filesystem directory or an s3 directory
    must contain no more than a single xml file

    Args:
        path (str): Path to Landsat directory or Landsat archive
        bucket (str): Optional bucket name containing the landsat scene

    Return:
        ElementTree: The ElementTree object of the file
    """
    if bucket is not None:
        # Retrieve key of xml file
        xml_key = s3.list_files(bucket=bucket, path=path,
                                pattern=r'.*\.xml$')[0]
        # s3.read_file()
        xml_str = s3.read_file(bucket=bucket, path=xml_key)
        # Build ET root
        root = ET.fromstring(xml_str)
    else:
        if path.endswith('.tar.gz'):
            with tarfile.open(path) as tar:
                # LIst all files contained in the archive
                file_list = tar.getnames()
                # Filter to keep only xml
                # TODO: Check that there's only one xml file in the archive raise Error otherwise
                xml_file = [x for x in file_list if x.endswith('.xml')][0]
                # Read the file 
                xml_fileobj = tar.extractfile(xml_file)
                root = ET.parse(xml_fileobj).getroot()
        elif os.path.isdir(path):
            # Let's hope there always only one xml file
            xml_file = glob(os.path.join(path, '*.xml'))[0]
            root = ET.parse(xml_file).getroot()
        else:
            raise ValueError("Don't know what to do with path; must point to directory or tar gz archive")
    return root


def read_txt(path, suffix='MTL', bucket=None):
    """Same as read_xml but for txt file
    TODO: Define return data structure of this function

    Args:
        path (str): Path to Landsat directory or Landsat archive
        suffix (str): Chain of character preceeding extension
        bucket (str): Optional bucket name containing the landsat scene

    Returns:
        list: A list of string (See readlines())
    """
    if bucket is not None:
        # Retrieve key of xml file
        mtl_key = s3.list_files(bucket=bucket, path=path,
                                pattern=r'.*%s\.txt$' % suffix)[0]
        # s3.read_file()
        mtl_str = s3.read_file(bucket=bucket, path=mtl_key)
        out = mtl_str.splitlines()
    else:
        if path.endswith('.tar.gz'):
            with tarfile.open(path) as tar:
                # LIst all files contained in the archive
                file_list = tar.getnames()
                # Filter to keep only xml
                # TODO: Check that there's only one txt file in the archive raise Error otherwise
                mtl_file = [x for x in file_list if x.endswith('%s.txt' % suffix)][0]
                # Read the file 
                mtl_fileobj = tar.extractfile(mtl_file)
                out = mtl_fileobj.readlines()
                out = [x.decode('UTF-8') for x in out]
        elif os.path.isdir(path):
            # Let's hope there always only one xml file
            mtl_file = glob(os.path.join(path, '*_%s.txt' % suffix))[0]
            with open(mtl_file) as con:
                out = con.readlines()
        else:
            raise ValueError("Don't know what to do with path; must point to directory or tar gz archive")
    out = [x.strip() for x in out]
    return out
