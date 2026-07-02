#!/usr/bin/env python3
"""Voidline Asset Manager — search, download, rename, index, score.

Multi-source library builder for documentary YouTube pipeline. Free / CC0 first,
paid APIs (ElevenLabs SFX, Suno, fal.ai) on top when configured.

Commands:
    search   <category>[/<style>] "<context>"          → top 5 ranked assets
    explore  <category>[/<style>] "<query>"            → API fetch new candidates (top 10)
    download <source> <original_id> <category> <style> → single fetch + index
    record   <asset_id> <run_id> <context> <rating>    → score after use
    rebalance                                          → fill thin cats + archive lowest
    stats                                              → library health
    index                                              → rebuild index.json from disk

Category tree matches assets_packs/ folders (music, sfx, video, stills, overlays,
fonts, luts, maps). Styles are the subfolders.

Env vars (optional, source falls silently if missing):
    FREESOUND_TOKEN, PIXABAY_KEY, PEXELS_KEY, FAL_KEY, SUNO_API_KEY, ELEVENLABS_KEY
"""
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
ASSETS_ROOT = REPO / "assets_packs"
INDEX_PATH = ASSETS_ROOT / "index.json"
PROVENANCE_PATH = ASSETS_ROOT / "PROVENANCE.md"
API_KEYS_PATH = REPO / "skills" / "long-form-pipeline" / "assets_library" / "api_keys.json"


# ───────────────────────── helpers ─────────────────────────

def load_index() -> dict:
    if not INDEX_PATH.exists():
        return {"version": 1, "assets": {}}
    return json.loads(INDEX_PATH.read_text())


def save_index(idx: dict):
    INDEX_PATH.write_text(json.dumps(idx, indent=2, ensure_ascii=False))


def load_api_key(source: str) -> str | None:
    if API_KEYS_PATH.exists():
        keys = json.loads(API_KEYS_PATH.read_text())
        val = keys.get(source)
        if val and val.startswith("$"):
            return os.environ.get(val[1:])
        return val
    env_map = {
        "freesound": "FREESOUND_TOKEN",
        "pixabay": "PIXABAY_KEY",
        "pexels": "PEXELS_KEY",
        "fal_ai": "FAL_KEY",
        "suno": "SUNO_API_KEY",
        "elevenlabs": "ELEVENLABS_KEY",
    }
    return os.environ.get(env_map.get(source, ""))


def slugify(text: str, max_words: int = 4) -> str:
    words = re.findall(r"[a-zA-Z0-9]+", text.lower())[:max_words]
    return "-".join(words) if words else "unknown"


def canonical_filename(source: str, category: str, style: str, slug: str, original_id: str, ext: str) -> str:
    ext = ext.lstrip(".").lower()
    return f"{source}_{category}_{style}_{slug}_{original_id}.{ext}"


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def append_provenance(entry: dict):
    line = (
        f"- {entry['downloaded_at']} {entry['source']} "
        f"id={entry['source_original_id']} — {entry['license']} — "
        f"{entry.get('duration_s') or entry.get('dimensions') or ''} — "
        f"{entry.get('query_that_found_it', '')}\n"
    )
    with open(PROVENANCE_PATH, "a") as f:
        f.write(line)


# ───────────────────────── sources ─────────────────────────

class Source:
    """Base class — each source implements search + download."""
    name = "base"
    default_license = "unknown"
    default_cat_map = {}   # source native category → local category/style

    def search_api(self, query: str, limit: int = 10) -> list[dict]:
        raise NotImplementedError

    def download_url(self, item: dict) -> str:
        raise NotImplementedError


class FreesoundSource(Source):
    name = "freesound"
    default_license = "CC0"

    def search_api(self, query: str, limit: int = 10, cc0_only: bool = True) -> list[dict]:
        token = load_api_key("freesound")
        if not token:
            print("[freesound] no FREESOUND_TOKEN — skip", file=sys.stderr)
            return []
        params = {
            "query": query,
            "page_size": limit,
            "fields": "id,name,duration,previews,tags,license,download,filesize,samplerate,type",
        }
        if cc0_only:
            params["filter"] = 'license:"Creative Commons 0"'
        url = "https://freesound.org/apiv2/search/text/?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(url, headers={
            "Authorization": f"Token {token}",
            "User-Agent": "voidline-asset-manager/1.0",
        })
        # 429 backoff: distinguish rate limit from genuinely-empty result. Freesound = 60 req/min.
        for attempt in range(2):
            try:
                with urllib.request.urlopen(req, timeout=15) as r:
                    body = json.load(r)
                break
            except urllib.error.HTTPError as e:
                if e.code == 429 and attempt == 0:
                    print("[freesound] 429 rate limit — waiting 65s + retry", file=sys.stderr)
                    time.sleep(65)
                    continue
                print(f"[freesound] HTTPError {e.code}: {e.reason}", file=sys.stderr)
                return []
            except Exception as e:
                print(f"[freesound] error: {e}", file=sys.stderr)
                return []
        else:
            return []
        return [
            {
                "source": self.name,
                "original_id": str(i["id"]),
                "title": i["name"],
                "duration_s": i.get("duration"),
                "tags": i.get("tags", []),
                "license": i.get("license", "CC0"),
                "preview_url": i["previews"].get("preview-hq-mp3") or i["previews"].get("preview-lq-mp3"),
                "download_url_authed": i["download"],
                "url": f"https://freesound.org/s/{i['id']}/",
                "ext": (i.get("type") or "wav").lower(),
            }
            for i in body.get("results", [])
        ]

    def download(self, item: dict, out_path: Path):
        # use the free preview MP3 (no auth needed for MP3 preview)
        # download_url_authed requires OAuth2 for original WAV
        url = item.get("preview_url") or item["download_url_authed"]
        urllib.request.urlretrieve(url, out_path)


class PexelsVideoSource(Source):
    name = "pexels"
    default_license = "Pexels License"

    def search_api(self, query: str, limit: int = 10) -> list[dict]:
        key = load_api_key("pexels")
        if not key:
            print("[pexels] no PEXELS_KEY — skip", file=sys.stderr)
            return []
        url = f"https://api.pexels.com/videos/search?query={urllib.parse.quote(query)}&per_page={limit}"
        req = urllib.request.Request(url, headers={
            "Authorization": key,
            "User-Agent": "voidline-asset-manager/1.0 (github.com/follox42/voidline-automation)",
        })
        try:
            with urllib.request.urlopen(req, timeout=15) as r:
                body = json.load(r)
        except Exception as e:
            print(f"[pexels] error: {e}", file=sys.stderr)
            return []
        out = []
        for v in body.get("videos", []):
            hd = next((f for f in v["video_files"] if f.get("quality") == "hd"), v["video_files"][0])
            out.append({
                "source": self.name,
                "original_id": str(v["id"]),
                "title": v.get("url", "").rsplit("/", 2)[-2] or f"pexels-{v['id']}",
                "duration_s": v.get("duration"),
                "tags": [(v.get("user", {}).get("name") or "")],
                "license": "Pexels License",
                "preview_url": hd["link"],
                "download_url_authed": hd["link"],
                "url": v["url"],
                "ext": "mp4",
            })
        return out

    def download(self, item: dict, out_path: Path):
        # Pexels download URLs sometimes 403 without a User-Agent header
        req = urllib.request.Request(item["preview_url"], headers={
            "User-Agent": "voidline-asset-manager/1.0 (github.com/follox42/voidline-automation)",
        })
        with urllib.request.urlopen(req, timeout=60) as r, open(out_path, "wb") as f:
            while chunk := r.read(65536):
                f.write(chunk)


class PixabayVideoSource(Source):
    name = "pixabay"
    default_license = "Pixabay License"

    def search_api(self, query: str, limit: int = 10, media_type: str = "video") -> list[dict]:
        key = load_api_key("pixabay")
        if not key:
            print("[pixabay] no PIXABAY_KEY — skip", file=sys.stderr)
            return []
        base = "https://pixabay.com/api/videos/" if media_type == "video" else "https://pixabay.com/api/"
        url = f"{base}?key={key}&q={urllib.parse.quote(query)}&per_page={min(limit, 20)}"
        try:
            with urllib.request.urlopen(url, timeout=15) as r:
                body = json.load(r)
        except Exception as e:
            print(f"[pixabay] error: {e}", file=sys.stderr)
            return []
        out = []
        for h in body.get("hits", []):
            video_url = h.get("videos", {}).get("medium", {}).get("url") if media_type == "video" else h.get("largeImageURL")
            out.append({
                "source": self.name,
                "original_id": str(h["id"]),
                "title": h.get("tags", "")[:60] or f"pixabay-{h['id']}",
                "duration_s": h.get("duration"),
                "tags": (h.get("tags") or "").split(", "),
                "license": "Pixabay License",
                "preview_url": video_url,
                "download_url_authed": video_url,
                "url": h.get("pageURL"),
                "ext": "mp4" if media_type == "video" else "jpg",
            })
        return out

    def download(self, item: dict, out_path: Path):
        # Pixabay CDN sometimes 403 without User-Agent + Referer
        req = urllib.request.Request(item["preview_url"], headers={
            "User-Agent": "Mozilla/5.0 (voidline-asset-manager/1.0)",
            "Referer": "https://pixabay.com/",
        })
        with urllib.request.urlopen(req, timeout=60) as r, open(out_path, "wb") as f:
            while chunk := r.read(65536):
                f.write(chunk)


class ElevenLabsSfxSource(Source):
    """Text-to-SFX generation. Uses ELEVENLABS_KEY (already in env for voice)."""
    name = "elevenlabs"
    default_license = "ElevenLabs commercial (paid tier)"

    def generate(self, prompt: str, duration_s: float = 3.0, out_path: Path = None) -> dict | None:
        key = load_api_key("elevenlabs")
        if not key:
            print("[elevenlabs] no key — skip", file=sys.stderr)
            return None
        url = "https://api.elevenlabs.io/v1/sound-generation"
        payload = json.dumps({
            "text": prompt,
            "duration_seconds": duration_s,
            "prompt_influence": 0.4,
        }).encode()
        req = urllib.request.Request(
            url,
            data=payload,
            headers={
                "xi-api-key": key,
                "Content-Type": "application/json",
                "Accept": "audio/mpeg",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                data = r.read()
        except Exception as e:
            print(f"[elevenlabs] error: {e}", file=sys.stderr)
            return None
        if out_path:
            out_path.write_bytes(data)
        oid = hashlib.md5(f"{prompt}{time.time()}".encode()).hexdigest()[:12]
        return {
            "source": self.name,
            "original_id": oid,
            "title": prompt[:60],
            "duration_s": duration_s,
            "tags": [t.strip() for t in re.split(r"[,\s]+", prompt.lower()) if t.strip()][:10],
            "license": self.default_license,
            "preview_url": None,
            "url": None,
            "ext": "mp3",
        }


# ───────────────────────── FlowSource — browser-native AI stills ─────────────────────────

FLOW_URL = "https://labs.google/fx/fr/tools/flow"
FLOW_COOKIE_PROFILE = "voidline"
FLOW_IMAGES_PER_SUBMIT = 2  # Nano Banana 2 always returns 2 on the free/Pro plan
FLOW_MIN_SUBMIT_GAP_S = 90  # anti-abuse pacing BETWEEN submits (per KNOWN_GOOD 2026-06-04)
FLOW_RENDER_TIMEOUT_S = 90  # completion gate WITHIN one submit
FLOW_MONTHLY_QUOTA_GENS = 30  # submits/month conservative ceiling on Pro free-Veo allowance
FLOW_LEASE_TTL_S = 900
FLOW_QUOTA_LEDGER = ASSETS_ROOT / ".flow_quota.json"
FLOW_LEASE_PATH = ASSETS_ROOT / ".flow.lease"


def _flow_month_key() -> str:
    return time.strftime("%Y-%m", time.gmtime())


def _flow_load_ledger() -> dict:
    if not FLOW_QUOTA_LEDGER.exists():
        return {}
    try:
        return json.loads(FLOW_QUOTA_LEDGER.read_text())
    except Exception:
        return {}


def _flow_month_usage() -> int:
    return _flow_load_ledger().get(_flow_month_key(), 0)


def _flow_record_usage(submits: int):
    ledger = _flow_load_ledger()
    ledger[_flow_month_key()] = ledger.get(_flow_month_key(), 0) + submits
    FLOW_QUOTA_LEDGER.write_text(json.dumps(ledger, indent=2))


def _flow_try_lease() -> bool:
    """Best-effort lease. Not a distributed lock: two containers racing during
    commit/push latency can still collide. Prevents in-host concurrent Flow gen
    from tripping over the same voidline session."""
    now = time.time()
    if FLOW_LEASE_PATH.exists():
        try:
            data = json.loads(FLOW_LEASE_PATH.read_text())
            if now - data.get("t", 0) < FLOW_LEASE_TTL_S:
                return False  # someone else's lease still fresh
        except Exception:
            pass
    FLOW_LEASE_PATH.write_text(json.dumps({"t": now, "pid": os.getpid()}))
    return True


def _flow_release_lease():
    try:
        FLOW_LEASE_PATH.unlink()
    except FileNotFoundError:
        pass


class FlowSource(Source):
    """Browser-native Nano Banana 2 image gen via camoufox stealth on voidline cookies.

    Classifier-safe by construction:
      - text entry: document.execCommand('insertText', ...) via stealth_evaluate
      - submit: camoufox-stealth_click(selector=...) dedicated tool
      - NEVER stealth_type on auth'd form (LEARNINGS BLOCKER_2026-06-30-B)
      - NEVER .click() inside evaluate on form submit buttons

    Result is a FlowResult dict (JSON-serializable):
      {"status":"ok"|"blocked", "reason": "quota"|"anti_abuse"|"ui_drift"|"locked"|None,
       "paths":[...], "gens_used": int}
    """
    name = "flow"
    default_license = "Google Flow — Nolann's personal PRO account"

    def gen_image(self, prompt: str, aspect: str = "16:9", batch: int = 2, style: str = "cinematic",
                   run_budget: int = 1) -> dict:
        try:
            import mcp_stealth as m
        except ImportError:
            return {"status": "blocked", "reason": "no_mcp_stealth", "paths": [], "gens_used": 0}

        # Quota gate
        submits_needed = min(-(-batch // FLOW_IMAGES_PER_SUBMIT), run_budget)
        month_used = _flow_month_usage()
        if month_used + submits_needed > FLOW_MONTHLY_QUOTA_GENS:
            return {"status": "blocked", "reason": "quota",
                    "paths": [], "gens_used": 0,
                    "note": f"{month_used}/{FLOW_MONTHLY_QUOTA_GENS} used this month"}

        # Best-effort lease
        if not _flow_try_lease():
            return {"status": "blocked", "reason": "locked", "paths": [], "gens_used": 0}

        try:
            m.initialize()
            m.call("stealth_navigate", {
                "url": FLOW_URL, "cookie_profile": FLOW_COOKIE_PROFILE,
                "session": "voidline_flow",
            })
            time.sleep(3)

            tmp_paths = []
            for i in range(submits_needed):
                # 1. Read-only diagnostic BEFORE anything else (classifier-safe scan)
                probe_js = r"""
                (() => {
                  const btn = [...document.querySelectorAll('button')].find(b => (b.innerText||'').includes('Créer'));
                  const banner = document.body.innerText.match(/inhabituelle|quota|limite|anti.?abus/i);
                  return JSON.stringify({
                    disabled: btn?.disabled,
                    ariaDisabled: btn?.getAttribute('aria-disabled'),
                    bannerText: banner ? banner[0] : null,
                  });
                })()
                """
                diag = m.call("stealth_evaluate", {"session": "voidline_flow", "script": probe_js})
                # (parsing tolerant — MCP returns various wrappers)
                diag_str = json.dumps(diag)
                if "inhabituelle" in diag_str or "anti-abus" in diag_str:
                    return {"status": "blocked", "reason": "anti_abuse",
                            "paths": [str(p) for p in tmp_paths],
                            "gens_used": i}

                # 2. Focus prompt input (safe dedicated tool)
                m.call("stealth_click", {"session": "voidline_flow",
                                          "selector": 'input[aria-label="Texte modifiable"], [contenteditable=true]'})

                # 3. Clear + type via execCommand (classifier-safe)
                escaped = json.dumps(prompt)
                type_js = f"""
                (() => {{
                  const inp = document.querySelector('input[aria-label="Texte modifiable"], [contenteditable=true]');
                  inp && inp.focus();
                  document.execCommand('selectAll', false, null);
                  document.execCommand('delete', false, null);
                  document.execCommand('insertText', false, {escaped});
                  return inp?.value ? inp.value.length : 'ok';
                }})()
                """
                m.call("stealth_evaluate", {"session": "voidline_flow", "script": type_js})
                time.sleep(1)

                # 4. Post-type diagnostic: confirm submit is enabled
                confirm = m.call("stealth_evaluate", {"session": "voidline_flow", "script": probe_js})
                if '"true"' in json.dumps(confirm):  # ariaDisabled=true after typing = ui_drift
                    return {"status": "blocked", "reason": "ui_drift",
                            "paths": [str(p) for p in tmp_paths],
                            "gens_used": i}

                # 5. Submit — dedicated tool, real mouse gesture
                m.call("stealth_click", {"session": "voidline_flow",
                                          "selector": 'button:has-text("Créer")'})

                # 6. Poll render completion (distinct timer from anti-abuse pacing)
                render_deadline = time.time() + FLOW_RENDER_TIMEOUT_S
                render_ok = False
                while time.time() < render_deadline:
                    time.sleep(4)
                    n_imgs_js = "document.querySelectorAll('img[src*=\"flow-content\"], img[src*=\"aisandbox\"]').length"
                    n_res = m.call("stealth_evaluate", {"session": "voidline_flow", "script": n_imgs_js})
                    if str(n_res).count("2") >= 1 or "3" in str(n_res) or "4" in str(n_res):
                        render_ok = True
                        break
                if not render_ok:
                    return {"status": "blocked", "reason": "ui_drift",
                            "paths": [str(p) for p in tmp_paths],
                            "gens_used": i}

                # 7. Extract images as base64 → decode → write to /tmp
                for slot in range(FLOW_IMAGES_PER_SUBMIT):
                    grab_js = f"""
                    (() => {{
                      const imgs = document.querySelectorAll('img[src*="flow-content"], img[src*="aisandbox"]');
                      const img = imgs[{slot}];
                      if (!img) return null;
                      const c = document.createElement('canvas');
                      c.width = img.naturalWidth; c.height = img.naturalHeight;
                      c.getContext('2d').drawImage(img, 0, 0);
                      return c.toDataURL('image/jpeg', 0.92);
                    }})()
                    """
                    b64 = m.call("stealth_evaluate", {"session": "voidline_flow", "script": grab_js})
                    if not b64:
                        continue
                    b64_str = json.dumps(b64)
                    m2 = re.search(r"base64,([A-Za-z0-9+/=]+)", b64_str)
                    if not m2:
                        continue
                    import base64
                    data = base64.b64decode(m2.group(1))
                    slug = slugify(prompt, max_words=4)
                    ts = str(int(time.time()))
                    oid = f"{ts}-{i}-{slot}"
                    dest = dest_folder("stills", "historical")
                    fname = canonical_filename("flow", "stills", "historical", slug, oid, "jpg")
                    fpath = dest / fname
                    fpath.write_bytes(data)
                    tmp_paths.append(fpath)

                if i < submits_needed - 1:
                    time.sleep(FLOW_MIN_SUBMIT_GAP_S)

            # 8. Index everything we captured
            idx = load_index()
            entries = []
            for p in tmp_paths:
                digest = sha256_of(p)
                entry = {
                    "id": p.stem,
                    "path": str(p.relative_to(REPO)),
                    "source": "flow",
                    "source_url": FLOW_URL,
                    "source_original_id": p.stem.rsplit("_", 1)[-1],
                    "license": self.default_license,
                    "license_ok_for_commercial_yt": True,
                    "downloaded_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "query_that_found_it": prompt,
                    "duration_s": None,
                    "dimensions": None,
                    "tags": [t.strip() for t in re.split(r"[,\s]+", prompt.lower()) if t.strip()][:10],
                    "sha256": digest,
                    "size_bytes": p.stat().st_size,
                    "used_in": [],
                    "scores": [],
                }
                add_to_index(idx, entry)
                append_provenance(entry)
                entries.append(entry)
            save_index(idx)

            _flow_record_usage(submits_needed)
            return {"status": "ok", "reason": None,
                    "paths": [str(p) for p in tmp_paths],
                    "gens_used": submits_needed,
                    "month_used_after": _flow_month_usage()}
        finally:
            _flow_release_lease()


SOURCES = {
    "freesound": FreesoundSource(),
    "flow": FlowSource(),
    "pexels": PexelsVideoSource(),
    "pixabay": PixabayVideoSource(),
    "elevenlabs": ElevenLabsSfxSource(),
}


# ───────────────────────── operations ─────────────────────────

def add_to_index(idx: dict, entry: dict) -> str:
    """Add asset to index, dedup by sha256 or by (source, original_id)."""
    key = entry["id"]
    for existing_key, existing in idx["assets"].items():
        if existing.get("sha256") == entry.get("sha256") and entry.get("sha256"):
            return existing_key  # already have it
        if (existing["source"] == entry["source"]
                and existing["source_original_id"] == entry["source_original_id"]):
            return existing_key
    idx["assets"][key] = entry
    return key


def dest_folder(category: str, style: str) -> Path:
    p = ASSETS_ROOT / category / style
    p.mkdir(parents=True, exist_ok=True)
    return p


def do_explore(category_style: str, query: str, limit: int = 10):
    if "/" in category_style:
        category, style = category_style.split("/", 1)
    else:
        category, style = category_style, "misc"

    idx = load_index()
    added = 0

    # Category → source routing
    if category == "sfx":
        candidates = SOURCES["freesound"].search_api(query, limit=limit, cc0_only=True)
    elif category == "video":
        candidates = SOURCES["pexels"].search_api(query, limit=limit) + \
                     SOURCES["pixabay"].search_api(query, limit=max(0, limit - 5), media_type="video")
    elif category == "overlays":
        # Grain / dust / light-leaks — same providers as video, we treat them as short B-roll
        candidates = SOURCES["pexels"].search_api(query, limit=limit) + \
                     SOURCES["pixabay"].search_api(query, limit=max(0, limit - 5), media_type="video")
    elif category == "stills":
        candidates = SOURCES["pixabay"].search_api(query, limit=limit, media_type="image")
    elif category == "music":
        # freesound has music tagged too
        candidates = SOURCES["freesound"].search_api(f"{query} music", limit=limit, cc0_only=True)
    else:
        print(f"[explore] no source configured for category {category}", file=sys.stderr)
        return

    print(f"[explore] {len(candidates)} candidates for '{query}' in {category}/{style}")
    dest = dest_folder(category, style)

    for c in candidates:
        slug = slugify(c["title"], max_words=4)
        fname = canonical_filename(c["source"], category, style, slug, c["original_id"], c["ext"])
        fpath = dest / fname
        if fpath.exists():
            print(f"  ✓ skip existing {fname}")
            continue
        try:
            src_obj = SOURCES[c["source"]]
            src_obj.download(c, fpath)
        except Exception as e:
            print(f"  ✗ failed {fname}: {e}")
            continue
        digest = sha256_of(fpath)
        entry = {
            "id": fname.rsplit(".", 1)[0],
            "path": str(fpath.relative_to(REPO)),
            "source": c["source"],
            "source_url": c.get("url"),
            "source_original_id": c["original_id"],
            "license": c["license"],
            "license_ok_for_commercial_yt": True,
            "downloaded_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "query_that_found_it": query,
            "duration_s": c.get("duration_s"),
            "bpm": None,
            "dimensions": None,
            "tags": c.get("tags", []),
            "sha256": digest,
            "size_bytes": fpath.stat().st_size,
            "used_in": [],
            "scores": [],
        }
        add_to_index(idx, entry)
        append_provenance(entry)
        added += 1
        print(f"  ✓ {fname} ({fpath.stat().st_size // 1024}KB)")

    save_index(idx)
    print(f"[explore] added {added} new assets to index")


def do_search(category_style: str, context: str, limit: int = 5):
    if "/" in category_style:
        category, style = category_style.split("/", 1)
    else:
        category, style = category_style, None

    idx = load_index()
    ctx_words = set(re.findall(r"[a-z]+", context.lower()))

    candidates = []
    for aid, a in idx["assets"].items():
        if not a["path"].startswith(f"assets_packs/{category}/"):
            continue
        if style and not a["path"].startswith(f"assets_packs/{category}/{style}/"):
            continue
        tags = set(t.lower() for t in a.get("tags", []))
        query_words = set(re.findall(r"[a-z]+", (a.get("query_that_found_it") or "").lower()))
        overlap = len(ctx_words & (tags | query_words))
        avg_score = 0
        if a.get("scores"):
            avg_score = sum(s.get("rating", 3) for s in a["scores"]) / len(a["scores"])
        novelty = 0.5 if not a.get("used_in") else 0
        rank = overlap * 2 + avg_score + novelty
        candidates.append((rank, a))

    candidates.sort(key=lambda x: -x[0])
    top = candidates[:limit]
    print(f"[search] top {len(top)} candidates for context: {context!r}")
    for rank, a in top:
        print(f"  {rank:5.1f}  {a['id']:60s}  {a['path']}")
        if a.get("scores"):
            recent = a["scores"][-1]
            print(f"          last used: {recent.get('context')} — rating {recent.get('rating')}")
    return top


def do_record(asset_id: str, run_id: str, context: str, rating: int, note: str = ""):
    idx = load_index()
    a = idx["assets"].get(asset_id)
    if not a:
        sys.exit(f"[record] asset not found: {asset_id}")
    if run_id not in a["used_in"]:
        a["used_in"].append(run_id)
    a["scores"].append({
        "run_id": run_id,
        "context": context,
        "rating": int(rating),
        "note": note,
        "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    })
    save_index(idx)
    print(f"[record] {asset_id} — {rating}/5 in {context}")


def do_stats():
    idx = load_index()
    print(f"total assets: {len(idx['assets'])}")
    by_cat = {}
    for a in idx["assets"].values():
        p = a["path"].split("/")
        cat_style = f"{p[1]}/{p[2]}" if len(p) >= 3 else "misc"
        by_cat.setdefault(cat_style, 0)
        by_cat[cat_style] += 1
    for cs, n in sorted(by_cat.items()):
        thin = " ⚠ THIN" if n < 3 else ""
        print(f"  {cs:40s} {n:3d}{thin}")


def do_index_rebuild():
    """Rebuild index.json by walking assets_packs/. Preserves scores if same id."""
    old_idx = load_index()
    old_scores = {aid: a.get("scores", []) for aid, a in old_idx["assets"].items()}
    old_used = {aid: a.get("used_in", []) for aid, a in old_idx["assets"].items()}
    idx = {"version": 1, "assets": {}}
    for p in ASSETS_ROOT.rglob("*"):
        if not p.is_file() or p.name.startswith(("index.json", "PROVENANCE", "README", ".")):
            continue
        rel = p.relative_to(REPO).as_posix()
        parts = p.stem.split("_")
        if len(parts) < 5:
            continue
        aid = p.stem
        idx["assets"][aid] = {
            "id": aid,
            "path": rel,
            "source": parts[0],
            "source_original_id": parts[-1],
            "license": "unknown (reindex)",
            "sha256": sha256_of(p),
            "size_bytes": p.stat().st_size,
            "tags": [],
            "used_in": old_used.get(aid, []),
            "scores": old_scores.get(aid, []),
        }
    save_index(idx)
    print(f"[index] rebuilt — {len(idx['assets'])} assets")


# ───────────────────────── CLI ─────────────────────────

def main():
    if len(sys.argv) < 2:
        print(__doc__); return
    cmd = sys.argv[1]

    if cmd == "explore":
        do_explore(sys.argv[2], " ".join(sys.argv[3:]))
    elif cmd == "search":
        do_search(sys.argv[2], " ".join(sys.argv[3:]))
    elif cmd == "record":
        asset_id, run_id, context, rating = sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5]
        note = " ".join(sys.argv[6:]) if len(sys.argv) > 6 else ""
        do_record(asset_id, run_id, context, rating, note)
    elif cmd == "stats":
        do_stats()
    elif cmd == "index":
        do_index_rebuild()
    elif cmd == "flow-gen":
        # FlowSource — Nano Banana 2 image gen via camoufox stealth on voidline cookies.
        # Usage: flow-gen "<prompt>" [aspect=16:9] [batch=2] [style=cinematic]
        prompt = sys.argv[2] if len(sys.argv) > 2 else ""
        aspect = sys.argv[3] if len(sys.argv) > 3 else "16:9"
        batch = int(sys.argv[4]) if len(sys.argv) > 4 else 2
        style = sys.argv[5] if len(sys.argv) > 5 else "cinematic"
        if not prompt:
            sys.exit("usage: flow-gen \"<prompt>\" [aspect] [batch] [style]")
        result = SOURCES["flow"].gen_image(prompt, aspect=aspect, batch=batch, style=style)
        print(json.dumps(result, indent=2))
        sys.exit(0 if result["status"] == "ok" else 1)
    elif cmd == "generate-sfx":
        # elevenlabs on-demand SFX generation
        prompt = " ".join(sys.argv[2:-1]) if len(sys.argv) > 3 else " ".join(sys.argv[2:])
        style = sys.argv[-1] if len(sys.argv) > 3 else "sting"
        dest = dest_folder("sfx", style)
        oid_meta = SOURCES["elevenlabs"].generate(prompt, duration_s=3.0, out_path=dest / f"tmp_gen.mp3")
        if oid_meta:
            slug = slugify(prompt, max_words=4)
            fname = canonical_filename("elevenlabs", "sfx", style, slug, oid_meta["original_id"], "mp3")
            (dest / "tmp_gen.mp3").rename(dest / fname)
            idx = load_index()
            entry = {
                "id": fname.rsplit(".", 1)[0],
                "path": str((dest / fname).relative_to(REPO)),
                "source": "elevenlabs",
                "source_original_id": oid_meta["original_id"],
                "license": oid_meta["license"],
                "license_ok_for_commercial_yt": True,
                "downloaded_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "query_that_found_it": prompt,
                "duration_s": 3.0,
                "tags": oid_meta["tags"],
                "sha256": sha256_of(dest / fname),
                "size_bytes": (dest / fname).stat().st_size,
                "used_in": [],
                "scores": [],
            }
            add_to_index(idx, entry)
            append_provenance(entry)
            save_index(idx)
            print(f"[gen-sfx] {fname} written to {dest}")
    else:
        print(f"unknown command: {cmd}"); print(__doc__)


if __name__ == "__main__":
    main()
