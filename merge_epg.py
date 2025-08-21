import requests
import json
import xml.etree.ElementTree as ET
from xml.dom import minidom
import sys

INPUT_JSON = "channels.json"
OUTPUT_XML = "epg.xml"

def merge_epg(input_json, output_file):
    print("📡 Downloading and merging EPG sources...")

    with open(input_json, "r", encoding="utf-8") as f:
        channels = json.load(f)

    merged_root = ET.Element("tv")

    seen_channels = set()
    seen_programmes = set()

    channel_elements = []
    programme_elements = []

    for ch in channels:
        name, url = ch["name"], ch["url"]

        try:
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            response.encoding = "utf-8"

            try:
                root = ET.fromstring(response.text)
            except ET.ParseError:
                print(f"⚠️ Skipping malformed XML from: {url}")
                continue

            for elem in root:
                if elem.tag == "channel":
                    channel_id = elem.attrib.get("id")
                    if channel_id not in seen_channels:
                        # overwrite display-name
                        display = elem.find("display-name")
                        if display is not None:
                            display.text = name
                        else:
                            ET.SubElement(elem, "display-name").text = name

                        channel_elements.append(elem)
                        seen_channels.add(channel_id)

                elif elem.tag == "programme":
                    prog_id = (elem.attrib.get("start"), elem.attrib.get("channel"))
                    if prog_id not in seen_programmes:
                        # tag programme with source channel name
                        elem.set("source", name)
                        programme_elements.append(elem)
                        seen_programmes.add(prog_id)

        except Exception as e:
            print(f"❌ Error fetching {url}: {e}")

    # Append channels first, then programmes
    for c in channel_elements:
        merged_root.append(c)

    for p in programme_elements:
        merged_root.append(p)

    # Pretty print XML
    xml_bytes = ET.tostring(merged_root, encoding="utf-8")
    pretty_xml = minidom.parseString(xml_bytes).toprettyxml(indent="  ", encoding="utf-8")

    # Validate final XML
    try:
        ET.fromstring(pretty_xml.decode("utf-8"))
    except ET.ParseError as e:
        print(f"❌ Final merged EPG is invalid: {e}")
        sys.exit(1)

    with open(output_file, "wb") as f:
        f.write(pretty_xml)

    print(f"✅ Merged EPG saved to: {output_file}")


if __name__ == "__main__":
    merge_epg(INPUT_JSON, OUTPUT_XML)
