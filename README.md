# 📺 EPG Aggregator

This project merges multiple XMLTV sources into a single `epg.xml` for IPTV apps like **TiviMate**.

## 🔧 How it works
- `channels.json` → Channel names + source URLs.
- `merge_epg.py` → Downloads, validates, merges, and generates `epg.xml`.
- GitHub Actions → Runs daily at 3 AM UTC and commits a fresh `epg.xml`.
- Netlify → Serves `epg.xml` as a static file.

## 🌐 TiviMate EPG URL
