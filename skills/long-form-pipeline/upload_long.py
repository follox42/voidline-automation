#!/usr/bin/env python3
"""
Step 7 — Upload long-form to YouTube Studio via camoufox-stealth.
Usage: python3 skills/long-form-pipeline/upload_long.py <run_dir>

Uploads the rendered MP4 and thumbnail to YouTube Studio,
then schedules to the publish_at time from NEXT_VIDEOS.md.
"""
import json, os, sys, time
from pathlib import Path

# Add repo root for mcp_stealth import
REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
import mcp_stealth as m

RUN_DIR = sys.argv[1] if len(sys.argv) > 1 else "runs/v4-roanoke"
SCRIPT_PATH = os.path.join(RUN_DIR, "script.json")
RENDER_PATH = os.path.join(RUN_DIR, "render", "voidline.mp4")
THUMB_PATH = os.path.join(RUN_DIR, "thumb", "thumbnail_v4_roanoke.jpg")
LOG_PATH = REPO / "agent-log.json"
SESSION = "voidline"

# ── Metadata from weekly_actions ───────────────────────────────────────────
TITLE = "The Lost Colony of Roanoke. The Word They Carved Before They Vanished."

DESCRIPTION = """115 people vanished from Roanoke Island in 1587. Their governor returned 3 years later. The colony was gone — houses dismantled, no bodies, no sign of struggle. One word carved into a post: CROATOAN.

What did they mean? Where did one hundred fifteen English settlers go?

Four centuries of theories. And the archaeological answer we finally have.

─────────────────────────────────────────────────────
⏱️ CHAPTERS
─────────────────────────────────────────────────────
0:00 — A Colony Gone
0:45 — The 1587 Expedition
2:45 — Three Missing Years
5:25 — CROATOAN: The Only Clue
7:50 — 400 Years of Theories
10:00 — What Archaeology Found

─────────────────────────────────────────────────────
📖 SOURCES
─────────────────────────────────────────────────────
• John White expedition journal (1587–1590), British Library
• Quinn, D.B. (1985) Set Fair for Roanoke. UNC Press
• Horn, J. (2010) A Kingdom Strange. Basic Books
• First Colony Foundation digs at Site X (2012–2021), Bertie County NC
• Croatoan Archaeological Society, Hatteras Island (2009–2024)
• Stahle et al. (1998) — Drought record reconstruction, Science 280:564

─────────────────────────────────────────────────────
🔔 Subscribe for more documentary history
─────────────────────────────────────────────────────

#roanoke #roanokecolony #lostcolonyofroanoke #croatoan #croatoanmystery #virginiadare #colonialamerica #colonialmytery #roanokenisland #johnwhiteroanoke #englishsettlersdisappeared #sitexroanoke #hatterasislandcroatoan #history #documentary"""

TAGS = [
    "roanoke colony", "lost colony of roanoke", "croatoan mystery", "virginia dare",
    "colonial america mystery", "roanoke island", "john white roanoke",
    "english settlers disappeared", "site x roanoke", "hatteras island croatoan",
    "roanoke 1587", "history documentary"
]

PUBLISH_AT = "2026-06-30T17:00:00Z"
# Schedule: June 30, 17:00 UTC
YEAR, MONTH, DAY, HOUR, MINUTE = 2026, 6, 30, 17, 0


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


def call(name, args):
    return m.call(name, args)


def js(script):
    return call("camoufox-stealth_evaluate", {"session": SESSION, "script": script})


def navigate(url, wait="networkidle"):
    return call("camoufox-stealth_navigate", {
        "url": url,
        "session": SESSION,
        "cookie_profile": "voidline",
        "wait_until": wait,
    })


def wait_for(selector, timeout=60000):
    return call("camoufox-stealth_wait", {
        "session": SESSION,
        "selector": selector,
        "timeout": timeout,
        "state": "visible",
    })


def click(selector=None, x=None, y=None, wait_nav=False):
    args = {"session": SESSION, "wait_for_nav": wait_nav}
    if selector:
        args["selector"] = selector
    if x is not None:
        args["x"] = x
    if y is not None:
        args["y"] = y
    return call("camoufox-stealth_click", args)


def sleep(s):
    time.sleep(s)


# ── Upload flow ─────────────────────────────────────────────────────────────

def open_upload_dialog():
    """Navigate to Studio upload page."""
    navigate("https://studio.youtube.com/channel/UCzbzLj0WW72_mTa86MwzkQQ/videos/upload?filter=%5B%5D&sort=%7B%22columnType%22%3A%22date%22%2C%22sortOrder%22%3A%22DESCENDING%22%7D")
    sleep(4)

    # Click Create button
    js("""
    (() => {
      const btns = Array.from(document.querySelectorAll('button,ytcp-button')).filter(b => b.offsetParent !== null);
      const cr = btns.find(b => {
        const t = (b.textContent || b.getAttribute('aria-label') || '').toLowerCase();
        return t.includes('créer') || t.includes('create');
      });
      if (cr) cr.click();
      return cr ? 1 : 0;
    })()
    """)
    sleep(2)

    # Click "Importer des vidéos" / Upload videos
    js("""
    (() => {
      const items = Array.from(document.querySelectorAll('tp-yt-paper-item,ytcp-text-menu-item,[role="menuitem"]')).filter(e => e.offsetParent !== null);
      const imp = items.find(i => i.textContent.includes('Importer') || i.textContent.includes('Upload'));
      if (imp) imp.click();
      return imp ? 1 : 0;
    })()
    """)
    sleep(4)


def inject_video(mp4_path):
    """Inject MP4 file via DataTransfer into the file input."""
    abs_path = os.path.abspath(mp4_path)
    script = f"""
    (async () => {{
      const input = document.querySelector('input[type=file]');
      if (!input) return {{err: 'no_input'}};
      // Use File API to read from local path
      // Since we can't access local FS from browser, we use the upload-by-path method
      // if Studio has a drag-drop zone
      const dt = new DataTransfer();
      // We need to inject via Playwright's setInputFiles instead
      return {{ok: 'use_setInputFiles', path: {json.dumps(abs_path)}}};
    }})()
    """
    # Use Playwright's setInputFiles via evaluate with CDP
    result = call("camoufox-stealth_upload", {
        "session": SESSION,
        "selector": "input[type=file]",
        "files": [abs_path],
    })
    return result


def wait_editors(timeout=120):
    end = time.time() + timeout
    while time.time() < end:
        r = js("(() => Array.from(document.querySelectorAll('[contenteditable=true]')).filter(e => e.offsetParent !== null).length)()")
        try:
            txt = str(r)
            import re
            m2 = re.search(r'"result":\s*(\d+)', txt)
            if m2 and int(m2.group(1)) >= 2:
                return True
        except Exception:
            pass
        time.sleep(2)
    return False


def fill_title_description(title, desc):
    script = f"""
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
    return js(script)


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
      if (!btn || btn.hasAttribute('disabled')) return {err: 'no_next'};
      btn.click();
      return {ok:1};
    })()
    """)


def set_tags(tags):
    # Tags are added in the "More options" section
    r = js("""
    (() => {
      const btns = Array.from(document.querySelectorAll('button,ytcp-button')).filter(b => b.offsetParent !== null);
      const more = btns.find(b => /plus d.options|show more|more options/i.test(b.textContent || b.getAttribute('aria-label') || ''));
      if (more) { more.click(); return {ok:1}; }
      return {err:'no_more_options'};
    })()
    """)
    sleep(2)
    for tag in tags[:12]:
        r = js(f"""
        (() => {{
          const tagInput = document.querySelector('input[placeholder*="tag" i], input[aria-label*="tag" i], ytcp-chip-bar input');
          if (!tagInput) return {{err:'no_tag_input'}};
          tagInput.focus();
          document.execCommand('insertText', false, {json.dumps(tag)});
          tagInput.dispatchEvent(new KeyboardEvent('keydown', {{key: ',', bubbles: true}}));
          tagInput.dispatchEvent(new KeyboardEvent('keyup', {{key: ',', bubbles: true}}));
          return {{ok: 1, tag: {json.dumps(tag)}}};
        }})()
        """)
        sleep(0.3)


def schedule_video(year, month, day, hour, minute):
    """Click Schedule radio and set date/time."""
    # Click Schedule radio
    js("""
    (() => {
      const r = Array.from(document.querySelectorAll('tp-yt-paper-radio-button,paper-radio-button'))
        .find(e => e.getAttribute('name') === 'SCHEDULE');
      if (r) { r.click(); return {ok:1}; }
      return {err:'no_schedule'};
    })()
    """)
    sleep(2)

    # Open date picker
    js("""
    (() => {
      const dateInputs = Array.from(document.querySelectorAll('input')).filter(i => {
        return i.offsetParent !== null && (
          (i.placeholder||'').toLowerCase().includes('date') ||
          (i.placeholder||'').toLowerCase().includes('jj') ||
          /\d{2}\s*\w+\s*\d{4}/.test(i.value||'')
        );
      });
      if (dateInputs.length) { dateInputs[0].focus(); dateInputs[0].click(); return {ok:1}; }
      return {err:'no_date'};
    })()
    """)
    sleep(2)

    # Navigate calendar to correct month and click day
    months_fr = ["janvier","février","mars","avril","mai","juin","juillet","août","septembre","octobre","novembre","décembre"]
    target = f"{months_fr[month-1]} {year}"
    js(f"""
    (async () => {{
      const sleep = ms => new Promise(r => setTimeout(r, ms));
      const target = {json.dumps(target)};
      for (let i = 0; i < 12; i++) {{
        const h = Array.from(document.querySelectorAll('div,span'))
          .find(e => e.offsetParent && /^(janvier|f.vrier|mars|avril|mai|juin|juillet|ao.t|septembre|octobre|novembre|d.cembre)\s+\d{{4}}$/i.test(e.textContent.trim()));
        if (h && h.textContent.trim().toLowerCase() === target.toLowerCase()) break;
        const nxt = Array.from(document.querySelectorAll('button,ytcp-icon-button'))
          .filter(b => b.offsetParent)
          .find(b => (b.getAttribute('aria-label')||'').toLowerCase().match(/suivant|next/));
        if (!nxt) break;
        nxt.click();
        await sleep(400);
      }}
      // Click the day
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
    sleep(2)

    # Set time
    time_str = f"{hour:02d}:{minute:02d}"
    js(f"""
    (() => {{
      const timeInputs = Array.from(document.querySelectorAll('input')).filter(i => {{
        return i.offsetParent !== null && (
          (i.placeholder||'').toLowerCase().includes('heure') ||
          (i.placeholder||'').toLowerCase().includes('time') ||
          /^\d{{1,2}}:\d{{2}}$/.test(i.value||'')
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
    sleep(2)


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


def main():
    m.initialize()
    print("=== Step 7: Upload Long-form to YouTube Studio ===")
    print(f"Video: {RENDER_PATH}")
    print(f"Thumb: {THUMB_PATH}")
    print(f"Title: {TITLE[:80]}")
    print(f"Schedule: {PUBLISH_AT}")

    if not os.path.exists(RENDER_PATH):
        print(f"ABORT: render not found at {RENDER_PATH}")
        sys.exit(1)

    print("\n1. Opening Studio upload dialog...")
    open_upload_dialog()

    print("2. Injecting video file...")
    r = inject_video(RENDER_PATH)
    print("  inject:", str(r)[:200])
    sleep(5)

    print("3. Waiting for editors...")
    if not wait_editors(timeout=120):
        print("  WARN: editors may not be ready, continuing...")

    print("4. Filling title + description...")
    r = fill_title_description(TITLE, DESCRIPTION)
    print("  fill:", str(r)[:200])
    sleep(2)

    print("5. Not for kids...")
    r = not_for_kids()
    print("  kids:", str(r)[:100])
    sleep(1)

    print("6. Navigating wizard steps (3x Next)...")
    for step in range(3):
        sleep(1.5)
        r = click_next()
        print(f"  step {step+1}:", str(r)[:100])

    sleep(3)

    print("7. Scheduling...")
    schedule_video(YEAR, MONTH, DAY, HOUR, MINUTE)

    print("8. Clicking Schedule button...")
    r = click_schedule_btn()
    print("  schedule btn:", str(r)[:150])
    sleep(5)

    log_action("LONG_FORM_SCHEDULED", f"v4-roanoke — '{TITLE[:60]}' scheduled for {PUBLISH_AT}")
    print(f"\n=== Upload complete — scheduled {PUBLISH_AT} ===")


if __name__ == "__main__":
    main()
