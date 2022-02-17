"""
Transform GeoJSON from https://data.gov.sg/dataset/community-clubs?resource_id=da666988-6c48-4f02-9ddf-bd8b11609cfd

to csv with schema:
name(str),long(float),lat(float)
"""

import geojson
import csv
from xml.etree import ElementTree as ET

path_to_geojson = "../data/community-clubs.geojson"
path_to_csv = "../data/rc_name_coords.csv"

# Extract
with open(path_to_geojson) as f:
    gj = geojson.load(f)

res = []

# Transform
for community_club in gj["features"]:
    html_str = community_club["properties"]["Description"]
    table = ET.XML(html_str).find("table")
    rows = [tr.getchildren() for tr in table.getchildren() if len(tr.getchildren()) == 2]
    kv_pairs = {row[0].text: row[1].text for row in rows}
    name = kv_pairs["NAME"]
    lng, lat, _ = community_club["geometry"]["coordinates"]
    res.append([name, lng, lat])

# Load
with open(path_to_csv, 'a') as csvfile:
    writer = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
    print(f"{len(res)} entries to write to {path_to_csv}")
    for entry in res:
        writer.writerow(entry)
    print("Done!")
