import argparse
from pathlib import Path
import json
import uuid

parser = argparse.ArgumentParser()
parser.add_argument("ds_file_path", help="Dataset tabby file. Files tabby file will be deduced", type=Path)
parser.add_argument("target_file", help="Output file name", type=Path)
args = parser.parse_args()


files_file_path = args.ds_file_path.with_stem(args.ds_file_path.stem + "_files")

# get dataset id & version from dataset file
dataset_id = dataset_version = None
with open(args.ds_file_path) as tabby_file:
    for line in tabby_file:
        if line.startswith("#"):
            continue
        fields = line.rstrip().split("\t")
        if fields[0] == "identifier" and dataset_id is None:
            dataset_id = fields[1]
        elif fields[0] == "version" and dataset_version is None:
            dataset_version = fields[1]
        if dataset_id is not None and dataset_version is not None:
            break

if dataset_version is None:
    # use "latest" if not specified
    dataset_version = "latest"

dataset_id = str(
    uuid.uuid5(
        uuid.uuid5(uuid.NAMESPACE_DNS, 'datalad.org'),
        dataset_id,
    )
)

# get file metadata from the files file
file_meta = []
with open(files_file_path) as tabby_file:
    header = None
    for line in tabby_file:
        if line.startswith("#") or line.startswith("\ufeff"):
            # comment, ignore
            # note: a wild zero-width non-breaking space may appear
            continue
        if line.rstrip() == "":
            continue
        if header is None:
            header = line.rstrip().split("\t")
            continue

        values = line.rstrip().split("\t")
        
        if len(values) > 4:
            # reject columns not covered by header
            values = values[:4]

        #d = {k: values[i] if len(values) > i else None for i, k in enumerate(header)}
        d = {k: values[i] for i, k in enumerate(header) if len(values) > i}
        file_meta.append(d)

# translate into catalog schema and write to file
with open(args.target_file, "w") as json_file:
    for d in file_meta:
        # add dataset id & version
        catalog_meta_item = {
            "type": "file",
            "dataset_id": dataset_id,
            "dataset_version": dataset_version,
            "path": d.get("filename"),  # d["filename"] + catch value error
            "contentbytesize": d.get("contentbytesize"),
            "url": d.get("url"),
        }
        # convert type
        if catalog_meta_item.get("contentbytesize") is not None:
            catalog_meta_item["contentbytesize"] = int(catalog_meta_item["contentbytesize"])
        # remove None
        catalog_meta_item = {k: v for k, v in catalog_meta_item.items() if v is not None}

        json.dump(catalog_meta_item, json_file)
        json_file.write("\n")

