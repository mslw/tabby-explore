"""List dataset files from a PRIDE ftp server
"""

import csv
from pprint import pprint
import sys
from urllib.parse import urljoin, urlparse
from collections import namedtuple
from pathlib import PurePosixPath

import fsspec

Tabbyline = namedtuple("Tabbyline", ["filename", "url", "contentbytesize"])

def list_remote(url):
    """Use fsspec to list files under a given url

    Returns a tabbyline with filename, url, and contentbytesize

    Note: we report the filename including its immediate parent name
    because we are going to run through several directories. Not
    intended in a general case.

    """
    parsed_url = urlparse(url)
    fs = fsspec.filesystem(parsed_url.scheme, host=parsed_url.netloc)
    ds_files = fs.ls(parsed_url.path)  # assumes flat, in general should be glob(path/**, detail=True)

    base_path = PurePosixPath(parsed_url.path)

    tabbylines = [
        Tabbyline(
            filename = PurePosixPath(f.get("name")).relative_to(base_path.parent),  # parent keeps one level
            url = urljoin(url, f.get("name")),  # with name starting at "/pride" urljoin gets the job done
            contentbytesize = f.get("size"),            
        )
        for f in ds_files
    ]

    return tabbylines

urls = [
    "ftp://ftp.pride.ebi.ac.uk/pride/data/archive/2022/11/PXD029435",
    "ftp://ftp.pride.ebi.ac.uk/pride/data/archive/2022/11/PXD031552",
    "ftp://ftp.pride.ebi.ac.uk/pride/data/archive/2022/11/PXD031535",
    "ftp://ftp.pride.ebi.ac.uk/pride/data/archive/2022/11/PXD031487",
    "ftp://ftp.pride.ebi.ac.uk/pride/data/archive/2022/11/PXD031555",
    "ftp://ftp.pride.ebi.ac.uk/pride/data/archive/2022/11/PXD031106",
    ]


with open("tabbytab_files.tsv", "w") as tsvfile:
    writer = csv.writer(tsvfile, delimiter="\t")
    writer.writerow(["filename", "url", "contentbytesize"])
    
    for url in urls:
        for tabbyline in list_remote(url):
            writer.writerow(list(tabbyline))

