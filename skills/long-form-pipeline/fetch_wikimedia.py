#!/usr/bin/env python3
"""
Step 3 (partial) — Wikimedia Commons asset sourcing.
Usage: python3 skills/long-form-pipeline/fetch_wikimedia.py <run_dir>

Reads a CHAPTER_QUERIES list (curated search terms per chapter, since the
script.json visual_mix entries are prose descriptions, not search terms),
queries the Wikimedia Commons API for license-clear images, downloads the
best match(es) per query, and writes assets/ATTRIBUTION.md.
"""
import os
import sys
import json
import time
import requests

RUN_DIR = sys.argv[1] if len(sys.argv) > 1 else "runs/v4-roanoke"
ASSETS_DIR = os.path.join(RUN_DIR, "assets")
API = "https://commons.wikimedia.org/w/api.php"
HEADERS = {"User-Agent": "VoidlineDocsBot/1.0 (nolann42400@gmail.com) research/non-commercial documentary"}

# chapter_id -> list of (slug, search query, min_width)
CHAPTER_QUERIES = {
    0: [
        ("ch0_roanoke_island_map", "Roanoke Island map 16th century", 800),
    ],
    1: [
        ("ch1_walter_raleigh", "Walter Raleigh portrait", 800),
        ("ch1_elizabeth_i", "Elizabeth I portrait Armada", 800),
        ("ch1_john_white_village", "John White watercolor Algonquian village Pomeiooc", 800),
        ("ch1_john_white_canoe", "John White watercolor Indian canoe", 800),
    ],
    2: [
        ("ch2_spanish_armada", "Spanish Armada 1588 painting", 800),
        ("ch2_debry_roanoke_map", "Theodor de Bry Virginia map 1590", 800),
        ("ch2_algonquian_canoe", "John White Algonquian dugout canoe watercolor", 800),
    ],
    3: [
        ("ch3_croatoan_carving", "CROATOAN Roanoke carved tree engraving", 600),
        ("ch3_debry_council_fire", "Theodor de Bry council fire engraving Virginia", 800),
    ],
    4: [
        ("ch4_spanish_galleon", "Spanish galleon 16th century painting", 800),
        ("ch4_powhatan", "Powhatan engraving 17th century", 800),
    ],
    5: [
        ("ch5_site_x_dig", "Roanoke colony archaeology excavation", 700),
        ("ch5_hatteras_island_map", "Hatteras Island map North Carolina", 700),
    ],
}


def search_commons(query, limit=5):
    params = {
        "action": "query",
        "format": "json",
        "list": "search",
        "srsearch": f"{query} filetype:bitmap",
        "srnamespace": 6,  # File namespace
        "srlimit": limit,
    }
    r = requests.get(API, params=params, headers=HEADERS, timeout=20)
    r.raise_for_status()
    return [hit["title"] for hit in r.json().get("query", {}).get("search", [])]


def get_image_info(titles):
    if not titles:
        return {}
    params = {
        "action": "query",
        "format": "json",
        "titles": "|".join(titles),
        "prop": "imageinfo",
        "iiprop": "url|extmetadata|size",
        "iiurlwidth": 1600,
    }
    r = requests.get(API, params=params, headers=HEADERS, timeout=20)
    r.raise_for_status()
    pages = r.json().get("query", {}).get("pages", {})
    out = {}
    for p in pages.values():
        title = p.get("title")
        infos = p.get("imageinfo")
        if infos:
            out[title] = infos[0]
    return out


def pick_best(infos, min_width):
    candidates = [
        (t, i) for t, i in infos.items()
        if i.get("width", 0) >= min_width and i.get("width", 0) > 0
    ]
    if not candidates:
        candidates = list(infos.items())
    candidates.sort(key=lambda kv: kv[1].get("width", 0), reverse=True)
    return candidates[0] if candidates else None


def download(url, dest):
    r = requests.get(url, headers=HEADERS, timeout=60, stream=True)
    r.raise_for_status()
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(dest, "wb") as f:
        for chunk in r.iter_content(8192):
            f.write(chunk)
    return os.path.getsize(dest)


def main():
    os.makedirs(ASSETS_DIR, exist_ok=True)
    attribution_lines = ["# Wikimedia Commons Attribution — v4 Roanoke\n"]
    manifest = []

    for chapter_id, queries in CHAPTER_QUERIES.items():
        for slug, query, min_width in queries:
            print(f"[ch{chapter_id}] searching: {query}")
            try:
                titles = search_commons(query)
                if not titles:
                    print(f"  NO RESULTS for '{query}'")
                    continue
                infos = get_image_info(titles)
                best = pick_best(infos, min_width)
                if not best:
                    print(f"  NO USABLE IMAGE for '{query}'")
                    continue
                title, info = best
                url = info.get("thumburl") or info["url"]
                ext = url.split(".")[-1].split("?")[0].lower()
                if ext not in ("jpg", "jpeg", "png"):
                    ext = "jpg"
                dest = os.path.join(ASSETS_DIR, f"ch{chapter_id}_{slug}.{ext}")
                size = download(url, dest)
                meta = info.get("extmetadata", {})
                artist = meta.get("Artist", {}).get("value", "Unknown")
                license_short = meta.get("LicenseShortName", {}).get("value", "Public Domain")
                credit = meta.get("Credit", {}).get("value", "")
                attribution_lines.append(
                    f"- `{os.path.basename(dest)}` — {title} — {license_short} — "
                    f"artist: {artist[:120]} — source: https://commons.wikimedia.org/wiki/{title.replace(' ', '_')}\n"
                )
                manifest.append({
                    "chapter_id": chapter_id, "slug": slug, "path": dest,
                    "title": title, "width": info.get("width"), "height": info.get("height"),
                    "bytes": size,
                })
                print(f"  OK -> {dest} ({size//1024}KB, {info.get('width')}x{info.get('height')})")
            except Exception as e:
                print(f"  ERROR '{query}': {e}")
            time.sleep(0.5)

    with open(os.path.join(ASSETS_DIR, "ATTRIBUTION.md"), "w") as f:
        f.writelines(attribution_lines)
    with open(os.path.join(ASSETS_DIR, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"\n=== Done: {len(manifest)} assets ===")


if __name__ == "__main__":
    main()
