"""Proteome eXchange to catalog

Converts a ProteomeXchange announcement XML to catalog metadata

This is a very basic way to get some (but not all) most important
values from a ProteomeXchange XML file into a catalog format. The XML
is highly structured and probably there are better ways of getting
contents.

"""

import json
from urllib.request import urlopen
import uuid
from xml.etree import ElementTree as ET

def contact_to_author(contact):
    """A dumb helper to convert Contact element to a catalog dict"""
    # first change from cvParam elements to a dictionary
    src_dict = {cvp.get("name"): cvp.get("value") for cvp in contact}
    # rewrite keys
    author = {
        "name": src_dict.get("contact name"),
        "email": src_dict.get("contact email")
    }
    return author

def mint_uuid(raw_id, dns):
    """Generate deterministic UUIDv5 based on raw id"""
    return uuid.uuid5(
        uuid.uuid5(uuid.NAMESPACE_DNS, dns),
        raw_id,
    )

# input & output (hardcoded for now)
url = "https://proteomecentral.proteomexchange.org/cgi/GetDataset?ID=PXD029435.0-1&outputMode=XML&test=no"
target_file = "px_metadata.jsonl"

response = urlopen(url)

if response.status != 200:
    print(f"Got response {response.status}: {response.msg}, exiting")

root = ET.fromstring(response.read())

# title and description
summary = root.find("DatasetSummary")
title = summary.get("title")  # key-value in DatasetSummary
description = summary.findtext("Description")  # a text element

# dataset id
# first identifier should be ProteomeXchange accession number (can verify name), PXD...
pxd_id = root.find("DatasetIdentifierList")[0].find("cvParam").get("value")

# people
contacts = root.find("ContactList").findall("Contact")

# some conversions are needed
ds_id = str(mint_uuid(pxd_id, "proteomexchange.org"))
ds_version = "latest"
authors = [contact_to_author(c) for c in contacts]

ds_meta = {
    "type": "dataset",
    "dataset_id": ds_id,
    "dataset_version": ds_version,
    "name": title,
    "description": description,
    "url": url,
    "authors": authors,
}

# We have two options to get list of files
# 1. Directly from XML (DatasetFileList)
#    which contains names and urls
# 2. By listing the ftp server indicated in FullDatasetLink
#    this can also give bytesize for cheap
#
# Here we do the first thing

df_list = root.find("DatasetFileList").findall("DatasetFile")
f_meta_list = []

for f in df_list:
    f_name = f.get("name")
    f_url = f[0].get("value")  # cvParam with value=ftp_url
    
    f_meta_list.append(
        dict(
            type="file",
            dataset_id=ds_id,
            dataset_version=ds_version,
            path=f_name,
            url=f_url,
        )
    )

with open(target_file, "w") as json_file:
    json.dump(ds_meta, json_file)
    json_file.write("\n")
    for meta_obj in f_meta_list:
        json.dump(meta_obj, json_file)
        json_file.write("\n")
