import json, re, requests
from xml.dom.minidom import Document, parseString

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

    doc = Document()
    tv = doc.createElement("tv")
    doc.appendChild(tv)

    # --- Add <channel> list ---
    for ch in channels:
        ch_id = get_channel_id(ch)
        channel_el = doc.createElement("channel")
        channel_el.setAttribute("id", ch_id)

        # display-name
        name_el = doc.createElement("display-name")
        name_el.setAttribute("lang", "en")
        name_el.appendChild(doc.createTextNode(ch["name"]))
        channel_el.appendChild(name_el)

        # icon
        if ch.get("logo"):
            icon_el = doc.createElement("icon")
            icon_el.setAttribute("src", ch["logo"])
            channel_el.appendChild(icon_el)

        tv.appendChild(channel_el)

    # --- Add <programme> list ---
    for ch in channels:
        try:
            res = requests.get(ch["url"], timeout=15)
            res.raise_for_status()
            xml_text = res.text

            inner = xml_text.split("<tv", 1)[1].split(">", 1)[1].rsplit("</tv>", 1)[0]
            programmes = inner.strip()

            prog_doc = parseString("<tv>"+programmes+"</tv>")
            for prog in prog_doc.getElementsByTagName("programme"):
                tv.appendChild(prog.cloneNode(deep=True))

        except Exception as e:
            print(f"❌ Failed for {ch['name']}: {e}")

    # Save pretty-printed XML
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(doc.toprettyxml(indent="  ", encoding="utf-8").decode("utf-8"))

    print(f"✅ Merged EPG written to {output_file}")

if __name__ == "__main__":
    merge_epg("channels.json", "epg.xml")
