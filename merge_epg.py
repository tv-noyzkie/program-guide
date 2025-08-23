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
        data = json.load(f)

    channels = data.get("channels", [])
    extra_epg = data.get("extra_epg", [])

    tv = ET.Element("tv")

    # --- Add <channel> list (epg.pw) ---
    for ch in channels:
        ch_id = get_channel_id(ch)
        channel_el = ET.SubElement(tv, "channel", id=ch_id)
        ET.SubElement(channel_el, "display-name", lang="en").text = ch["name"]
        if ch.get("logo"):
            ET.SubElement(channel_el, "icon", src=ch["logo"])

    # --- Add <channel> list (extra_epg) ---
    for src in extra_epg:
        for ch in src["channels"]:
            channel_el = ET.SubElement(tv, "channel", id=ch["id"])
            ET.SubElement(channel_el, "display-name", lang="en").text = ch["name"]

    # --- Add <programme> list (epg.pw) ---
    for ch in channels:
        ch_id = get_channel_id(ch)
        try:
            res = requests.get(ch["url"], timeout=15)
            res.raise_for_status()
            xml_text = res.text

            # Extract only the <programme> contents
            inner = xml_text.split("<tv", 1)[1].split(">", 1)[1].rsplit("</tv>", 1)[0]
            prog_root = ET.fromstring("<tv>" + inner + "</tv>")

            for prog in prog_root.findall("programme"):
                prog.set("channel", ch_id)
                prog.set("display-name", ch["name"])  # add channel name for clarity
                tv.append(prog)

        except Exception as e:
            print(f"❌ Failed for {ch['name']}: {e}")

    # --- Add <programme> list (extra_epg) ---
    for src in extra_epg:
        try:
            res = requests.get(src["url"], timeout=15)
            res.raise_for_status()
            xml_text = res.text
            xml_root = ET.fromstring(xml_text)

            wanted_ids = {c["id"]: c["name"] for c in src["channels"]}

            for prog in xml_root.findall("programme"):
                ch_id = prog.get("channel")
                if ch_id in wanted_ids:
                    prog.set("channel", ch_id)
                    prog.set("display-name", wanted_ids[ch_id])  # include readable name
                    tv.append(prog)
        except Exception as e:
            print(f"❌ Failed loading extra EPG {src['url']}: {e}")

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
