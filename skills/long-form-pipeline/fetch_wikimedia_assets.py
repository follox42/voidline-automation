#!/usr/bin/env python3
"""
Step 3 — Asset fetching from Wikimedia Commons
Usage: python3 skills/long-form-pipeline/fetch_wikimedia_assets.py <run_dir>

Searches Wikimedia Commons for each chapter's visual needs and downloads
the best-matching image (min 1280px wide, license-clear).
"""
import os, sys, json, time, requests
from pathlib import Path
from urllib.parse import quote

RUN_DIR = sys.argv[1] if len(sys.argv) > 1 else "runs/v4-roanoke"
ASSETS_DIR = os.path.join(RUN_DIR, "assets")
SCRIPT_PATH = os.path.join(RUN_DIR, "script.json")

WIKIMEDIA_API = "https://commons.wikimedia.org/w/api.php"
HEADERS = {"User-Agent": "VoidlineBot/1.0 (nolann42400@gmail.com; youtube.com/@voidlinedocs)"}

# Image search queries per chapter (ordered by preference)
CHAPTER_QUERIES = {
    0: ["Roanoke colony painting", "palisade fort colonial america", "english settlement 16th century"],
    1: ["Walter Raleigh portrait 16th century", "Queen Elizabeth I 1585", "John White Algonquian watercolor"],
    2: ["Spanish Armada 1588 painting", "Howard Effingham battle fleet", "Roanoke island map de Bry 1590"],
    3: ["CROATOAN Roanoke discovery engraving", "John White 1590 Roanoke", "de Bry Algonquian council fire"],
    4: ["Spanish galleon 16th century", "tree ring drought data chart", "Native American colonial era engraving"],
    5: ["Roanoke archaeological excavation", "colonial artifacts pottery 16th century", "Hatteras island Outer Banks"],
}

def search_wikimedia(query, min_width=800, max_results=5):
    """Search Wikimedia Commons and return image info list."""
    params = {
        "action": "query",
        "generator": "search",
        "gsrnamespace": "6",  # File namespace
        "gsrsearch": f"file:{query}",
        "gsrlimit": max_results * 2,
        "prop": "imageinfo",
        "iiprop": "url|size|extmetadata",
        "iiurlwidth": 1280,
        "format": "json",
    }
    try:
        r = requests.get(WIKIMEDIA_API, params=params, headers=HEADERS, timeout=15)
        if r.status_code != 200:
            return []
        data = r.json()
        pages = data.get("query", {}).get("pages", {})
        results = []
        for page in pages.values():
            ii = page.get("imageinfo", [{}])[0]
            w = ii.get("width", 0)
            h = ii.get("height", 0)
            if w < min_width:
                continue
            url = ii.get("thumburl") or ii.get("url", "")
            if not url or not url.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
                continue
            # Check license
            meta = ii.get("extmetadata", {})
            license_short = meta.get("LicenseShortName", {}).get("value", "")
            license_url = meta.get("LicenseUrl", {}).get("value", "")
            # Accept CC licenses and PD
            if any(x in license_short.upper() for x in ["CC", "PD", "PUBLIC", "CC0", "ATTRIBUTION"]):
                results.append({
                    "title": page.get("title", ""),
                    "url": url,
                    "width": w,
                    "height": h,
                    "license": license_short,
                    "license_url": license_url,
                    "description": meta.get("ImageDescription", {}).get("value", "")[:200],
                })
        return results
    except Exception as e:
        print(f"    Wikimedia API error: {e}")
        return []


def download_image(url, out_path):
    """Download image to out_path. Returns True on success."""
    try:
        r = requests.get(url, headers=HEADERS, timeout=30, stream=True)
        if r.status_code != 200:
            return False
        with open(out_path, "wb") as f:
            for chunk in r.iter_content(65536):
                f.write(chunk)
        return os.path.getsize(out_path) > 5000
    except Exception as e:
        print(f"    Download error: {e}")
        return False


def load_chapter_queries(script_path: str, run_dir: str) -> dict:
    """Read chapter queries from (in order of priority):
      1. runs/<topic>/wikimedia_queries.json  (if present, curated per-run override)
      2. script.json ch[i].wikimedia_queries  (if present in the script)
      3. CHAPTER_QUERIES hardcoded fallback   (Roanoke; used only when 1+2 absent)

    Returns {ch_id_int: [queries]}.
    """
    override = Path(run_dir) / "wikimedia_queries.json"
    if override.exists():
        raw = json.loads(override.read_text())
        return {int(k): v for k, v in raw.items()}

    if os.path.exists(script_path):
        try:
            script = json.loads(open(script_path).read())
            chapters = script.get("chapters") or []
            per_ch = {}
            for i, ch in enumerate(chapters):
                q = ch.get("wikimedia_queries") or ch.get("assets_queries")
                if q:
                    per_ch[i] = q
            if per_ch:
                return per_ch
        except Exception as e:
            print(f"[wikimedia] script.json parse failed: {e}", file=sys.stderr)

    print(f"[wikimedia] no per-run queries; falling back to hardcoded CHAPTER_QUERIES (Roanoke). "
          f"Add script.json.chapters[i].wikimedia_queries OR runs/.../wikimedia_queries.json "
          f"for other topics.", file=sys.stderr)
    return CHAPTER_QUERIES


def main():
    os.makedirs(ASSETS_DIR, exist_ok=True)
    attribution = []
    manifest = {}

    print("=== Step 3: Wikimedia Asset Fetch ===")

    queries_map = load_chapter_queries(SCRIPT_PATH, RUN_DIR)
    for ch_id, queries in queries_map.items():
        ch_dir = os.path.join(ASSETS_DIR, f"ch{ch_id}")
        os.makedirs(ch_dir, exist_ok=True)
        ch_assets = []
        img_idx = 0

        for query in queries:
            if img_idx >= 4:  # max 4 images per chapter
                break
            print(f"  ch{ch_id} searching: '{query}'")
            results = search_wikimedia(query)
            time.sleep(0.5)  # polite pacing

            for res in results[:2]:  # take top 2 per query
                if img_idx >= 4:
                    break
                out_path = os.path.join(ch_dir, f"img_{img_idx:02d}.jpg")
                if os.path.exists(out_path) and os.path.getsize(out_path) > 5000:
                    print(f"    [SKIP] img_{img_idx:02d} already downloaded")
                    ch_assets.append({"path": out_path, "source": res["url"], "license": res.get("license","")})
                    img_idx += 1
                    continue

                print(f"    Downloading {res['width']}×{res['height']} [{res.get('license','?')}]: {res['title'][:60]}")
                ok = download_image(res["url"], out_path)
                if ok:
                    sz = os.path.getsize(out_path)
                    print(f"    OK → {out_path} ({sz//1024}KB)")
                    ch_assets.append({"path": out_path, "source": res["url"], "license": res.get("license","")})
                    attribution.append({
                        "chapter_id": ch_id,
                        "file": out_path,
                        "title": res["title"],
                        "url": res["url"],
                        "license": res.get("license",""),
                        "license_url": res.get("license_url",""),
                        "description": res.get("description",""),
                    })
                    img_idx += 1
                else:
                    print(f"    FAILED → {res['url'][:80]}")
                time.sleep(0.3)

        manifest[f"ch{ch_id}"] = ch_assets
        print(f"  ch{ch_id}: {len(ch_assets)} images downloaded")

    # Write attribution
    attr_path = os.path.join(ASSETS_DIR, "ATTRIBUTION.md")
    lines = ["# Wikimedia Commons Attribution\n"]
    for a in attribution:
        lines.append(f"## ch{a['chapter_id']}: {a['title']}\n- License: {a['license']}\n- URL: {a['url']}\n- License info: {a['license_url']}\n")
    Path(attr_path).write_text("\n".join(lines))

    # Write manifest
    manifest_path = os.path.join(ASSETS_DIR, "manifest.json")
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    total = sum(len(v) for v in manifest.values())
    print(f"\n=== Assets Done: {total} images ===")
    print(f"Attribution: {attr_path}")
    print(f"Manifest: {manifest_path}")


if __name__ == "__main__":
    main()
