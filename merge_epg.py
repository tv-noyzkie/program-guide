import json, re, requests
import xml.etree.ElementTree as ET

def get_channel_id(ch):
    """Extract channel_id from URL, fallback to sanitized channel name."""
    url = ch.get("url", "")
    match = re.search(r"channel_id=(\d+)", url)
    if match:
        return match.group(1)

    # fallback: sanitize name → lowercase, only keep letters/numbers/underscore
    name = ch["name"].lower()
    safe_id = re.sub(r"[^a-z0-9]+", "_", name).strip("_")
    return safe_id

def merge_epg(channels_file, output_file):
    with open(channels_file, "r", encoding="utf-8") as f:
        channels = json.load(f)

    tv = ET.Element("tv")

    # --- Add <channel> list ---
    for ch in channels:
        ch_id = get_channel_id(ch)
        channel_el = ET.SubElement(tv, "channel", id=ch_id)

        ET.SubElement(channel_el, "display-name", lang="en").text = ch["name"]

        if ch.get("logo"):
            ET.SubElement(channel_el, "icon", src=ch["logo"])

    # --- Add <programme> list ---
    for ch in channels:
        try:
            res = requests.get(ch["url"], timeout=15)
            res.raise_for_status()
            xml_text = res.text

            # Extract only the <programme> contents
            inner = xml_text.split("<tv", 1)[1].split(">", 1)[1].rsplit("</tv>", 1)[0]
            prog_root = ET.fromstring("<tv>" + inner + "</tv>")

            for prog in prog_root.findall("programme"):
                tv.append(prog)

        except Exception as e:
            print(f"❌ Failed for {ch['name']}: {e}")

    # --- Pretty-print XML ---
    rough_string = ET.tostring(tv, encoding="utf-8")
    import xml.dom.minidom
    pretty_xml = xml.dom.minidom.parseString(rough_string).toprettyxml(indent="  ")
    pretty_xml = "\n".join([line for line in pretty_xml.splitlines() if line.strip()])

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(pretty_xml)

    print(f"✅ Merged EPG written to {output_file}")

if __name__ == "__main__":
    merge_epg("channels.json", "epg.xml")
