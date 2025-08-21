import requests
import json
import xml.etree.ElementTree as ET
from xml.dom import minidom

with open("channels.json", "r", encoding="utf-8") as f:
    channels = json.load(f)

def merge_epg(channels, output_file):
    print("Downloading and merging EPG sources...")

    tv = ET.Element("tv")

    # Add channel list first
    for ch in channels:
        ch_elem = ET.SubElement(tv, "channel", id=ch["id"])
        disp = ET.SubElement(ch_elem, "display-name", lang=ch.get("lang", "en"))
        disp.text = ch["name"]

        logo_url = ch.get("logo", "")
        ET.SubElement(ch_elem, "icon", src=logo_url)

    # Then add programme data
    for ch in channels:
        try:
            response = requests.get(ch["url"])
            response.raise_for_status()
            content = response.text

            if "<tv" in content and "</tv>" in content:
                inner = content.split("<tv", 1)[1].split(">", 1)[1].rsplit("</tv>", 1)[0]
                parsed = ET.fromstring(f"<tv>{inner}</tv>")
                for prog in parsed.findall("programme"):
                    tv.append(prog)
            else:
                print(f"⚠️ Skipping malformed XML from: {ch['url']}")
        except Exception as e:
            print(f"❌ Error fetching {ch['url']}: {e}")

    # Pretty print clean XML
    xml_str = ET.tostring(tv, encoding="utf-8")
    parsed_str = minidom.parseString(xml_str)
    pretty_xml = parsed_str.toprettyxml(indent="  ", encoding="utf-8")

    with open(output_file, "wb") as f:
        f.write(pretty_xml)

    print(f"✅ Merged EPG saved to: {output_file}")

merge_epg(channels, "epg.xml")
