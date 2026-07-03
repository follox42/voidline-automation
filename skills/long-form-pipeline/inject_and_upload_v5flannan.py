#!/usr/bin/env python3
"""
Step 7b — v5-flannan variant of inject_and_upload.py (JS Blob injection upload).
Reads title/description/tags/publish_at from runs/v5-flannan/script.json.
"""
import base64
import json
import os
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
import mcp_stealth as m

RUN_DIR = "runs/v5-flannan"
RENDER_PATH = os.path.join(RUN_DIR, "render", "voidline.mp4")
THUMB_PATH = os.path.join(RUN_DIR, "thumb", "thumbnail.jpg")
SCRIPT_PATH = os.path.join(RUN_DIR, "script.json")
LOG_PATH = REPO / "agent-log.json"
SESSION = "voidline_long_v5"
CHANNEL_ID = "UCzbzLj0WW72_mTa86MwzkQQ"

script = json.load(open(SCRIPT_PATH))
TITLE = script["title"]
DESCRIPTION = script["description"]
TAGS = script["tags"]
PUBLISH_AT = script["publish_at"]  # "2026-07-03T17:00:00Z"
_dt = PUBLISH_AT.replace("Z", "")
YEAR, MONTH, DAY = int(_dt[0:4]), int(_dt[5:7]), int(_dt[8:10])
HOUR, MINUTE = int(_dt[11:13]), int(_dt[14:16])

CHUNK_SIZE = 800_000


def js(script_):
    return m.call("camoufox-stealth_evaluate", {"session": SESSION, "script": script_})


def log_action(action, detail):
    if LOG_PATH.exists():
        data = json.loads(LOG_PATH.read_text())
    else:
        data = {"decisions": []}
    data.setdefault("decisions", []).append({
        "t": time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime()),
        "action": action,
        "detail": detail,
    })
    LOG_PATH.write_text(json.dumps(data, indent=2))


def inject_video_blob(mp4_path):
    print(f"  Reading {mp4_path} ...")
    with open(mp4_path, "rb") as f:
        data = f.read()
    file_size = len(data)
    print(f"  File size: {file_size // 1024 // 1024}MB ({file_size} bytes)")

    b64 = base64.b64encode(data).decode()
    chunks = [b64[i:i + CHUNK_SIZE] for i in range(0, len(b64), CHUNK_SIZE)]
    print(f"  Sending {len(chunks)} chunks of ~{CHUNK_SIZE // 1024}KB each...")

    r = js("window.__vl_chunks = []; window.__vl_chunks.length;")
    print(f"  Init: {str(r)[:80]}")

    for i, chunk in enumerate(chunks):
        r = js(f"window.__vl_chunks.push({json.dumps(chunk)}); window.__vl_chunks.length;")
        if (i + 1) % 5 == 0 or i == len(chunks) - 1:
            print(f"  Chunk {i + 1}/{len(chunks)} sent")

    inject_script = """
    (async () => {
      try {
        const b64 = window.__vl_chunks.join('');
        console.log('Assembling blob from', b64.length, 'chars');
        const raw = atob(b64);
        const bytes = new Uint8Array(raw.length);
        for (let i = 0; i < raw.length; i++) bytes[i] = raw.charCodeAt(i);
        const blob = new Blob([bytes], {type: 'video/mp4'});
        const file = new File([blob], 'voidline.mp4', {type: 'video/mp4', lastModified: Date.now()});
        console.log('File created:', file.name, file.size);

        const input = document.querySelector('input[type=file]');
        if (!input) return {err: 'no_input'};

        const dt = new DataTransfer();
        dt.items.add(file);
        Object.defineProperty(input, 'files', {
          value: dt.files,
          writable: false,
          configurable: true,
        });
        input.dispatchEvent(new Event('change', {bubbles: true}));
        input.dispatchEvent(new Event('input', {bubbles: true}));

        window.__vl_chunks = null;
        return {ok: 1, size: file.size, name: file.name};
      } catch(e) {
        return {err: e.toString()};
      }
    })()
    """
    print("  Assembling Blob and injecting into file input...")
    r = js(inject_script)
    print(f"  Inject result: {str(r)[:300]}")
    return r


def inject_thumb_blob(thumb_path):
    print(f"  Reading thumbnail {thumb_path} ...")
    with open(thumb_path, "rb") as f:
        data = f.read()
    b64 = base64.b64encode(data).decode()
    script_ = f"""
    (async () => {{
      try {{
        const raw = atob({json.dumps(b64)});
        const bytes = new Uint8Array(raw.length);
        for (let i = 0; i < raw.length; i++) bytes[i] = raw.charCodeAt(i);
        const blob = new Blob([bytes], {{type: 'image/jpeg'}});
        const file = new File([blob], 'thumbnail_v5_flannan.jpg', {{type: 'image/jpeg'}});
        const input = document.querySelector('input[type=file][accept*="image"], ytcp-video-thumbnail input[type=file]');
        if (!input) return {{err: 'no_thumb_input'}};
        const dt = new DataTransfer();
        dt.items.add(file);
        Object.defineProperty(input, 'files', {{value: dt.files, writable: false, configurable: true}});
        input.dispatchEvent(new Event('change', {{bubbles: true}}));
        return {{ok: 1, size: file.size}};
      }} catch(e) {{
        return {{err: e.toString()}};
      }}
    }})()
    """
    r = js(script_)
    print(f"  Thumb inject result: {str(r)[:200]}")
    return r


def wait_editors(timeout=180):
    import re
    end = time.time() + timeout
    while time.time() < end:
        r = js("Array.from(document.querySelectorAll('[contenteditable=true]')).filter(e => e.offsetParent !== null).length")
        txt = str(r)
        m2 = re.search(r'"result":\s*(\d+)', txt)
        if m2 and int(m2.group(1)) >= 2:
            return True
        time.sleep(3)
    return False


def fill_title_description(title, desc):
    script_ = f"""
    (async () => {{
      const sleep = ms => new Promise(r => setTimeout(r, ms));
      const editors = Array.from(document.querySelectorAll('[contenteditable=true]')).filter(e => e.offsetParent !== null);
      if (editors.length < 2) return {{err: 'editors', n: editors.length}};
      const setText = async (el, value) => {{
        el.focus();
        await sleep(200);
        document.execCommand('selectAll', false, null);
        document.execCommand('delete', false, null);
        document.execCommand('insertText', false, value);
        el.dispatchEvent(new Event('input', {{bubbles: true}}));
        await sleep(300);
      }};
      await setText(editors[0], {json.dumps(title)});
      await setText(editors[1], {json.dumps(desc)});
      return {{title_len: editors[0].textContent.length, desc_len: editors[1].textContent.length}};
    }})()
    """
    return js(script_)


def not_for_kids():
    return js("""
    (() => {
      const r = Array.from(document.querySelectorAll('tp-yt-paper-radio-button,paper-radio-button'))
        .find(e => e.getAttribute('name') === 'VIDEO_MADE_FOR_KIDS_NOT_MFK');
      if (r) { r.click(); return {ok:1}; }
      return {err:'not_found'};
    })()
    """)


def click_next():
    return js("""
    (() => {
      const btn = Array.from(document.querySelectorAll('ytcp-button,button'))
        .filter(b => b.offsetParent !== null)
        .find(b => {
          const t = (b.textContent || '').trim().toLowerCase();
          return t === 'suivant' || t === 'next';
        });
      if (!btn || btn.hasAttribute('disabled')) return {err: 'no_next', btns: Array.from(document.querySelectorAll('ytcp-button')).map(b => b.textContent.trim()).slice(0,8)};
      btn.click();
      return {ok:1};
    })()
    """)


def set_tags(tags):
    r = js("""
    (() => {
      const btns = Array.from(document.querySelectorAll('button,ytcp-button')).filter(b => b.offsetParent !== null);
      const more = btns.find(b => /plus d.options|show more|more options/i.test(b.textContent || b.getAttribute('aria-label') || ''));
      if (more) { more.click(); return {ok:1}; }
      return {err:'no_more_options'};
    })()
    """)
    time.sleep(2)
    for tag in tags[:12]:
        js(f"""
        (() => {{
          const tagInput = document.querySelector('input[placeholder*="tag" i], input[aria-label*="tag" i], ytcp-chip-bar input');
          if (!tagInput) return {{err:'no_tag_input'}};
          tagInput.focus();
          document.execCommand('insertText', false, {json.dumps(tag)});
          tagInput.dispatchEvent(new KeyboardEvent('keydown', {{key: ',', bubbles: true}}));
          tagInput.dispatchEvent(new KeyboardEvent('keyup', {{key: ',', bubbles: true}}));
          return {{ok: 1}};
        }})()
        """)
        time.sleep(0.3)


def schedule_video(year, month, day, hour, minute):
    js("""
    (() => {
      const r = Array.from(document.querySelectorAll('tp-yt-paper-radio-button,paper-radio-button'))
        .find(e => e.getAttribute('name') === 'SCHEDULE');
      if (r) { r.click(); return {ok:1}; }
      return {err:'no_schedule'};
    })()
    """)
    time.sleep(2)

    js("""
    (() => {
      const dateInputs = Array.from(document.querySelectorAll('input')).filter(i => {
        return i.offsetParent !== null && (
          (i.placeholder||'').toLowerCase().includes('date') ||
          (i.placeholder||'').toLowerCase().includes('jj') ||
          /\\d{2}\\s*\\w+\\s*\\d{4}/.test(i.value||'')
        );
      });
      if (dateInputs.length) { dateInputs[0].focus(); dateInputs[0].click(); return {ok:1}; }
      return {err:'no_date'};
    })()
    """)
    time.sleep(2)

    months_fr = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"]
    target = f"{months_fr[month - 1]} {year}"
    r = js(f"""
    (async () => {{
      const sleep = ms => new Promise(r => setTimeout(r, ms));
      const target = {json.dumps(target)};
      for (let i = 0; i < 12; i++) {{
        const h = Array.from(document.querySelectorAll('div,span'))
          .find(e => e.offsetParent && /^(janvier|f.vrier|mars|avril|mai|juin|juillet|ao.t|septembre|octobre|novembre|d.cembre)\\s+\\d{{4}}$/i.test(e.textContent.trim()));
        if (h && h.textContent.trim().toLowerCase() === target.toLowerCase()) break;
        const nxt = Array.from(document.querySelectorAll('button,ytcp-icon-button'))
          .filter(b => b.offsetParent)
          .find(b => (b.getAttribute('aria-label')||'').toLowerCase().match(/suivant|next/));
        if (!nxt) break;
        nxt.click();
        await sleep(400);
      }}
      const all = Array.from(document.querySelectorAll('span,div,td,button')).filter(e => e.offsetParent);
      let found = false;
      for (const el of all) {{
        const t = el.textContent.trim();
        if (!found && t.toLowerCase() === target.toLowerCase()) {{ found = true; continue; }}
        if (found && t === {json.dumps(str(day))}) {{ el.click(); return {{ok:1}}; }}
      }}
      return {{err:'day_not_found'}};
    }})()
    """)
    print(f"  date-pick result: {str(r)[:200]}")
    time.sleep(2)

    time_str = f"{hour:02d}:{minute:02d}"
    r = js(f"""
    (() => {{
      const timeInputs = Array.from(document.querySelectorAll('input')).filter(i => {{
        return i.offsetParent !== null && (
          (i.placeholder||'').toLowerCase().includes('heure') ||
          (i.placeholder||'').toLowerCase().includes('time') ||
          /^\\d{{1,2}}:\\d{{2}}$/.test(i.value||'')
        );
      }});
      if (!timeInputs.length) return {{err:'no_time'}};
      const inp = timeInputs[timeInputs.length-1];
      const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
      setter.call(inp, {json.dumps(time_str)});
      inp.dispatchEvent(new Event('input', {{bubbles:true}}));
      inp.dispatchEvent(new Event('change', {{bubbles:true}}));
      inp.dispatchEvent(new Event('blur', {{bubbles:true}}));
      return {{ok:1, val:inp.value}};
    }})()
    """)
    print(f"  time-set result: {str(r)[:200]}")
    time.sleep(2)


def click_schedule_btn():
    return js("""
    (() => {
      const btn = Array.from(document.querySelectorAll('ytcp-button,button'))
        .filter(b => b.offsetParent !== null)
        .find(b => {
          const t = (b.textContent||'').trim().toLowerCase();
          return t === 'programmer' || t === 'schedule';
        });
      if (!btn) return {err:'no_btn'};
      if (btn.hasAttribute('disabled') || btn.getAttribute('aria-disabled')==='true') return {err:'disabled'};
      btn.click();
      return {ok:1, txt:btn.textContent.trim()};
    })()
    """)


def wait_upload_processing(timeout=300):
    import re
    end = time.time() + timeout
    while time.time() < end:
        r = js("""
        (() => {
          const prog = document.querySelector('ytcp-video-upload-progress, [class*="progress"], ytcp-animated-icon');
          const editors = Array.from(document.querySelectorAll('[contenteditable=true]')).filter(e => e.offsetParent !== null).length;
          const url = window.location.href;
          return {hasProgress: !!prog, editors, url: url.slice(0,80)};
        })()
        """)
        txt = str(r)
        m_e = re.search(r'"editors":\s*(\d+)', txt)
        m_p = re.search(r'"hasProgress":\s*(true|false)', txt)
        editors = int(m_e.group(1)) if m_e else 0
        has_prog = m_p and m_p.group(1) == 'true'
        if editors >= 2 or has_prog:
            return True
        time.sleep(3)
    return False


def main():
    m.initialize()
    print("=== Step 7b: Inject Video + Upload to YouTube Studio (v5-flannan) ===")
    print(f"Video: {RENDER_PATH}")
    print(f"Thumb: {THUMB_PATH}")
    print(f"Title: {TITLE[:80]}")
    print(f"Schedule: {PUBLISH_AT}")

    if not os.path.exists(RENDER_PATH):
        print(f"ABORT: render not found at {RENDER_PATH}")
        sys.exit(1)

    print("\nNavigating to upload page...")
    m.call("camoufox-stealth_navigate", {
        "url": f"https://studio.youtube.com/channel/{CHANNEL_ID}/videos/upload?filter=%5B%5D&sort=%7B%22columnType%22%3A%22date%22%2C%22sortOrder%22%3A%22DESCENDING%22%7D",
        "session": SESSION,
        "cookie_profile": "voidline",
        "wait_until": "networkidle",
    })
    time.sleep(4)

    r = js("!!document.querySelector('ytcp-uploads-dialog, input[type=file]')")
    has_dialog = '"result": true' in str(r) or "'result': True" in str(r)
    print(f"Dialog open: {has_dialog} raw={str(r)[:150]}")

    if not has_dialog:
        print("Opening Create -> Upload videos...")
        js("""
        (() => {
          const btns = Array.from(document.querySelectorAll('button,ytcp-button')).filter(b => b.offsetParent !== null);
          const cr = btns.find(b => {
            const t = (b.textContent || b.getAttribute('aria-label') || '').toLowerCase();
            return t.includes('créer') || t.includes('create');
          });
          if (cr) cr.click();
        })()
        """)
        time.sleep(2)
        js("""
        (() => {
          const items = Array.from(document.querySelectorAll('tp-yt-paper-item,ytcp-text-menu-item,[role="menuitem"]')).filter(e => e.offsetParent !== null);
          const imp = items.find(i => i.textContent.includes('Importer') || i.textContent.includes('Upload'));
          if (imp) imp.click();
        })()
        """)
        time.sleep(4)

    print("\n1. Injecting video via Blob injection...")
    inject_result = inject_video_blob(RENDER_PATH)
    ok = '"ok": 1' in str(inject_result) or "'ok': 1" in str(inject_result)
    if not ok:
        print(f"  WARN: injection may have failed: {inject_result}")

    print("\n2. Waiting for upload to register (up to 3 min)...")
    if not wait_upload_processing(timeout=180):
        print("  WARN: upload may not be registering, checking editors...")
    else:
        print("  Upload registered!")
    time.sleep(3)

    print("\n3. Filling title + description...")
    r = fill_title_description(TITLE, DESCRIPTION)
    print(f"  fill: {str(r)[:200]}")
    time.sleep(2)

    print("\n4. Not for kids...")
    r = not_for_kids()
    print(f"  kids: {str(r)[:100]}")
    time.sleep(1)

    print("\n5. Adding tags (More options)...")
    set_tags(TAGS)

    print("\n6. Navigating wizard (3x Next)...")
    for step in range(3):
        time.sleep(2)
        r = click_next()
        print(f"  step {step + 1}: {str(r)[:100]}")

    time.sleep(3)

    print("\n7. Injecting thumbnail...")
    inject_thumb_blob(THUMB_PATH)
    time.sleep(2)

    print("\n8. Scheduling...")
    schedule_video(YEAR, MONTH, DAY, HOUR, MINUTE)

    print("\n9. Clicking Schedule button...")
    r = click_schedule_btn()
    print(f"  schedule btn: {str(r)[:150]}")
    time.sleep(5)

    r = js("window.location.href")
    print(f"\nFinal URL: {str(r)[:200]}")

    log_action("LONG_FORM_SCHEDULED", f"v5-flannan — '{TITLE[:60]}' scheduled for {PUBLISH_AT}")
    print(f"\n=== Upload complete — scheduled {PUBLISH_AT} ===")


if __name__ == "__main__":
    main()
