#!/usr/bin/env python3
"""
Step 3 — Asset Summoner (Wikimedia Commons)
Usage: python3 skills/long-form-pipeline/fetch_assets.py <run_dir>
"""
import os, sys, json, time, requests
from urllib.parse import quote

RUN_DIR = sys.argv[1] if len(sys.argv) > 1 else "runs/v4-roanoke"
ASSETS_DIR = os.path.join(RUN_DIR, "assets/images")
ATTR_FILE = os.path.join(RUN_DIR, "assets/ATTRIBUTION.md")
os.makedirs(ASSETS_DIR, exist_ok=True)

HEADERS = {"User-Agent": "VoidlineDocBot/1.0 (nolann42400@gmail.com)"}

# Wikimedia search queries per chapter (chapter_id → list of queries)
CHAPTER_QUERIES = {
    0: [],  # AI shot (placeholder generated later)
    1: [
        "Walter Raleigh portrait 1588",
        "Queen Elizabeth I patent charter New World",
        "John White watercolor Algonquian village Roanoke 1585",
        "Roanoke expedition 1585 route map",
        "Pomeiooc village John White watercolor",
    ],
    2: [
        "Spanish Armada 1588 battle painting",
        "De Bry Roanoke Island map 1590 engraving",
        "Algonquian dugout canoe period",
    ],
    3: [
        "CROATOAN carved post Roanoke colony discovery engraving",
        "Theodor de Bry Algonquian council fire engraving",
        "John White 1590 Roanoke return",
    ],
    4: [
        "Spanish galleon 16th century period art",
        "tree ring drought study paleoclimate data",
        "Native American colonial assimilation 17th century",
    ],
    5: [
        "Hatteras Island archaeological excavation",
        "Roanoke colony archaeology Site X Bertie County",
        "Croatan Buxton North Carolina dig",
    ],
}

attribution_lines = ["# Asset Attribution\n"]

def search_wikimedia(query, n=2):
    """Search Wikimedia Commons for images matching query."""
    url = "https://commons.wikimedia.org/w/api.php"
    params = {
        "action": "query",
        "list": "search",
        "srsearch": f"file:{query}",
        "srnamespace": 6,
        "srlimit": n * 2,
        "format": "json",
    }
    try:
        r = requests.get(url, params=params, headers=HEADERS, timeout=15)
        results = r.json().get("query", {}).get("search", [])
        return [res["title"] for res in results[:n]]
    except Exception as e:
        print(f"    Search error: {e}")
        return []

def get_image_info(file_title):
    """Get direct URL and license for a Wikimedia file."""
    url = "https://commons.wikimedia.org/w/api.php"
    params = {
        "action": "query",
        "titles": file_title,
        "prop": "imageinfo",
        "iiprop": "url|extmetadata|size",
        "iiurlwidth": 1280,
        "format": "json",
    }
    try:
        r = requests.get(url, params=params, headers=HEADERS, timeout=15)
        pages = r.json().get("query", {}).get("pages", {})
        for page in pages.values():
            info_list = page.get("imageinfo", [])
            if not info_list:
                continue
            info = info_list[0]
            meta = info.get("extmetadata", {})
            license_short = meta.get("LicenseShortName", {}).get("value", "Unknown")
            author = meta.get("Artist", {}).get("value", "Unknown")
            url_thumb = info.get("thumburl") or info.get("url")
            url_full = info.get("url", "")
            w = info.get("width", 0)
            h = info.get("height", 0)
            return {"url": url_thumb or url_full, "url_full": url_full, "license": license_short, "author": author, "w": w, "h": h}
    except Exception as e:
        print(f"    Info error: {e}")
    return None

def download_image(url, out_path):
    """Download image to path."""
    try:
        r = requests.get(url, headers=HEADERS, timeout=30, stream=True)
        if r.status_code == 200:
            with open(out_path, "wb") as f:
                for chunk in r.iter_content(8192):
                    f.write(chunk)
            return os.path.getsize(out_path)
        return 0
    except Exception as e:
        print(f"    Download error: {e}")
        return 0

def create_placeholder(chapter_id, out_path, label):
    """Create a solid-color placeholder image using ffmpeg."""
    color = "0x0d0d0d"
    cmd = f'ffmpeg -y -f lavfi -i "color=c={color}:size=1280x720:r=1" -vframes 1 -vf "drawtext=text=\'{label}\':fontcolor=gold:fontsize=40:x=(w-text_w)/2:y=(h-text_h)/2" {out_path} 2>/dev/null'
    os.system(cmd)
    return os.path.exists(out_path)

def main():
    print("=== Step 3: Asset Summoner (Wikimedia Commons) ===")
    chapter_assets = {}
    asset_count = 0

    for ch_id, queries in CHAPTER_QUERIES.items():
        ch_assets = []
        print(f"\n[ch{ch_id}] {len(queries)} queries")

        if ch_id == 0:
            # AI placeholder for cold-open
            ph_path = os.path.join(ASSETS_DIR, "ch0_placeholder.jpg")
            if not os.path.exists(ph_path):
                create_placeholder(ch_id, ph_path, "ROANOKE 1587")
            ch_assets.append({"path": ph_path, "source": "placeholder", "license": "local"})
            print(f"  ch0: placeholder created")
            chapter_assets[ch_id] = ch_assets
            continue

        for qi, query in enumerate(queries):
            print(f"  [{qi+1}/{len(queries)}] Searching: {query}")
            titles = search_wikimedia(query, n=2)
            time.sleep(0.5)

            for title in titles:
                info = get_image_info(title)
                if not info:
                    continue
                # Skip non-image files
                if not any(info["url"].lower().endswith(ext) for ext in [".jpg", ".jpeg", ".png", ".gif", ".webp", ".tif", ".tiff"]):
                    continue
                # Skip tiny images
                if info.get("w", 0) < 400:
                    continue

                safe_name = f"ch{ch_id}_{asset_count:02d}_{title.replace('File:', '').replace(' ', '_')[:50]}"
                ext = os.path.splitext(info["url"])[1].split("?")[0] or ".jpg"
                out_path = os.path.join(ASSETS_DIR, f"{safe_name}{ext}")

                if os.path.exists(out_path):
                    print(f"    SKIP (exists): {out_path}")
                    ch_assets.append({"path": out_path, "source": title, "license": info["license"]})
                    asset_count += 1
                    break

                size = download_image(info["url"], out_path)
                if size > 5000:
                    print(f"    OK: {size//1024}KB → {os.path.basename(out_path)} ({info['license']})")
                    ch_assets.append({"path": out_path, "source": title, "license": info["license"]})
                    attribution_lines.append(f"- `{os.path.basename(out_path)}`: {title} | {info['license']} | {info.get('author','')}\n")
                    asset_count += 1
                    break
                else:
                    if os.path.exists(out_path):
                        os.remove(out_path)

            time.sleep(0.3)

        # Ensure at least 1 asset per chapter (use placeholder if none found)
        if not ch_assets:
            ph_path = os.path.join(ASSETS_DIR, f"ch{ch_id}_placeholder.jpg")
            create_placeholder(ch_id, ph_path, f"CH{ch_id} — ROANOKE 1587")
            ch_assets.append({"path": ph_path, "source": "placeholder", "license": "local"})
            print(f"  ch{ch_id}: fallback placeholder created")

        chapter_assets[ch_id] = ch_assets

    # Write asset manifest
    manifest = {"chapter_assets": chapter_assets, "total_downloaded": asset_count}
    with open(os.path.join(RUN_DIR, "assets", "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=2)

    # Write attribution file
    with open(ATTR_FILE, "w") as f:
        f.writelines(attribution_lines)

    print(f"\n=== Assets Done: {asset_count} images ===")
    return chapter_assets

if __name__ == "__main__":
    main()
