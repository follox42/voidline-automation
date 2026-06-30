#!/usr/bin/env python3
"""
Step 7 — Upload long-form to YouTube Studio + schedule
Usage: python3 skills/long-form-pipeline/upload_long.py <run_dir>

Requires:
  - MCPHUB_TOKEN env var (camoufox-stealth MCP)
  - Video accessible at CDN_BASE/<filename>
  - voidline cookie profile active in camoufox session

CDN_BASE default: https://raw.githubusercontent.com/follox42/voidline-remotion-preview/main/public
Override via env var: VOIDLINE_CDN_BASE=<url>
"""
import json, os, sys, time
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import mcp_stealth as m

SESSION = "voidline"
CHANNEL_ID = "UCzbzLj0WW72_mTa86MwzkQQ"
CDN_BASE = os.environ.get("VOIDLINE_CDN_BASE", "https://raw.githubusercontent.com/follox42/voidline-remotion-preview/main/public")
RUN_DIR = sys.argv[1] if len(sys.argv) > 1 else "runs/v4-roanoke"

TITLE = "What Did CROATOAN Mean? (1587) — The Lost Colony of Roanoke"
DESCRIPTION = """\
A hundred and fifteen English settlers disappeared from Roanoke Island in 1587. No bodies. No graves. No sign of struggle. One word carved into a tree post: CROATOAN.

For 400 years, historians and archaeologists searched for what happened. In 2009, two separate excavations finally found the answer — and it was encoded in that single carved word all along.

▬▬▬▬▬ TIMESTAMPS ▬▬▬▬▬

0:00 — A Colony Gone
0:45 — The 1587 Expedition
2:45 — Three Missing Years
5:25 — CROATOAN: The Only Clue
7:50 — 400 Years of Theories
10:00 — What Archaeology Found

▬▬▬▬▬ SOURCES ▬▬▬▬▬

• John White expedition journal (1587–1590), British Library MS
• Quinn, D.B. (1985) Set Fair for Roanoke, UNC Press
• Horn, J. (2010) A Kingdom Strange, Basic Books
• First Colony Foundation digs at Site X (2012–2021), Bertie County NC
• Croatoan Archaeological Society, Hatteras/Buxton (2009–2024) — Charles Heath, Mark Horton
• Stahle et al. (1998) Drought reconstructions for Roanoke 1587–1590, Science 280:564

▬▬▬▬▬ VOIDLINE ▬▬▬▬▬

We document the cases that history forgot. Sourced, verified, no fluff.
→ Subscribe for weekly mysteries: @voidlinedocs

#roanoke #lostcolony #croatoan #colonialamerica #historymystery #voidline #documentary #unsolved"""

TAGS = "roanoke colony,lost colony of roanoke,croatoan mystery,virginia dare,colonial america mystery,roanoke island,john white roanoke,english settlers disappeared,site x roanoke,hatteras island croatoan,1587,american history"

PUBLISH_DATE = {"year": 2026, "month": 7, "day": 1}
PUBLISH_TIME = {"hour": 17, "minute": 0}  # Paris UTC+2 → set 19:00 in Studio

VIDEO_FILENAME = "voidline_v4_roanoke.mp4"
THUMB_PATH = os.path.join(RUN_DIR, "flow_thumbs", "voidline_v4_roanoke_thumb_A.jpg")

LOG_PATH = Path("agent-log.json")


def log_action(action, detail):
    data = []
    if LOG_PATH.exists():
        try:
            data = json.loads(LOG_PATH.read_text())
        except Exception:
            data = []
    data.append({"at": time.strftime("%Y-%m-%dT%H:%M:%SZ"), "type": action, "detail": detail})
    LOG_PATH.write_text(json.dumps(data, indent=2))


def js(script, timeout=30):
    return m.call("stealth_evaluate", {"session": SESSION, "script": script}, timeout=timeout)


def navigate_studio_upload():
    m.call("stealth_navigate", {
        "url": f"https://studio.youtube.com/channel/{CHANNEL_ID}/videos/upload",
        "session": SESSION,
        "wait_until": "domcontentloaded",
    })
    time.sleep(5)
    # Click Créer button
    js("""
    (() => {
      const all = Array.from(document.querySelectorAll('button,ytcp-button')).filter(b => b.offsetParent !== null);
      const cr = all.find(b => (b.getAttribute('aria-label')||'').toLowerCase().includes('créer') || b.textContent.includes('Créer'));
      if (cr) { cr.click(); return {ok:1}; }
      return {err:'no_create_btn'};
    })()
    """)
    time.sleep(2)
    # Click Importer
    js("""
    (() => {
      const items = Array.from(document.querySelectorAll('tp-yt-paper-item,ytcp-text-menu-item,[role=menuitem]')).filter(e => e.offsetParent !== null);
      const imp = items.find(i => i.textContent.includes('Importer') || i.textContent.includes('Upload'));
      if (imp) { imp.click(); return {ok:1}; }
      return {err:'no_import'};
    })()
    """)
    time.sleep(4)


def inject_video(filename):
    """Fetch video from CDN and inject via DataTransfer into the file input."""
    url = f"{CDN_BASE}/{filename}"
    script = f"""
    (async () => {{
      const resp = await fetch({json.dumps(url)});
      if (!resp.ok) return {{err:'fetch_fail', status:resp.status, url:{json.dumps(url)}}};
      const blob = await resp.blob();
      const file = new File([blob], {json.dumps(filename)}, {{type:'video/mp4'}});
      const input = document.querySelector('input[type=file]');
      if (!input) return {{err:'no_file_input'}};
      const dt = new DataTransfer();
      dt.items.add(file);
      input.files = dt.files;
      input.dispatchEvent(new Event('change', {{bubbles:true}}));
      return {{ok:1, size_mb:(file.size/1024/1024).toFixed(1)}};
    }})()
    """
    return js(script, timeout=120)


def wait_for_title_editor(timeout=90):
    end = time.time() + timeout
    while time.time() < end:
        r = js("(() => Array.from(document.querySelectorAll('[contenteditable=true]')).filter(e => e.offsetParent !== null).length)()")
        try:
            txt = r.get("result", {}).get("content", [{}])[0].get("text", "")
            if '"result": 1' in txt or '"result":1' in txt or '"result": 2' in txt or '"result":2' in txt:
                return True
        except Exception:
            pass
        time.sleep(2)
    return False


def fill_metadata(title, desc, tags):
    script = f"""
    (async () => {{
      const sleep = (ms) => new Promise(r => setTimeout(r, ms));
      const editors = Array.from(document.querySelectorAll('[contenteditable=true]')).filter(e => e.offsetParent !== null);
      if (editors.length < 2) return {{err:'editors_missing', n:editors.length}};
      const setText = async (el, value) => {{
        el.focus(); await sleep(200);
        document.execCommand('selectAll', false, null);
        document.execCommand('delete', false, null);
        document.execCommand('insertText', false, value);
        el.dispatchEvent(new Event('input', {{bubbles:true}}));
        await sleep(300);
      }};
      await setText(editors[0], {json.dumps(title)});
      await setText(editors[1], {json.dumps(desc)});
      return {{title_len:editors[0].textContent.length, desc_len:editors[1].textContent.length}};
    }})()
    """
    r = js(script, timeout=30)
    time.sleep(1.5)

    # Tags field (if present)
    r2 = js(f"""
    (() => {{
      const tagInput = document.querySelector('input[placeholder*="tag"],input[aria-label*="tag"],input[aria-label*="Tag"]');
      if (!tagInput) return {{err:'no_tags'}};
      tagInput.focus();
      document.execCommand('insertText', false, {json.dumps(tags)});
      tagInput.dispatchEvent(new Event('input', {{bubbles:true}}));
      return {{ok:1}};
    }})()
    """)
    return r


def not_for_kids():
    return js("""
    (() => {
      const radios = Array.from(document.querySelectorAll('tp-yt-paper-radio-button,paper-radio-button')).filter(e => e.offsetParent !== null);
      const notMFK = radios.find(r => (r.getAttribute('name')||'') === 'VIDEO_MADE_FOR_KIDS_NOT_MFK');
      if (notMFK) { notMFK.click(); return {ok:1}; }
      return {err:'not_found'};
    })()
    """)


def click_next():
    r = js("""
    (() => {
      const btn = Array.from(document.querySelectorAll('ytcp-button,button'))
        .filter(b => b.offsetParent !== null)
        .find(b => {
          const al = (b.getAttribute('aria-label')||'').toLowerCase();
          const txt = (b.textContent||'').trim().toLowerCase();
          return (txt === 'suivant' || al.includes('suivant') || txt === 'next' || al.includes('next'))
            && !al.includes('précédent');
        });
      if (!btn) return {err:'no_next'};
      if (btn.getAttribute('disabled') || btn.getAttribute('aria-disabled') === 'true') return {err:'disabled'};
      btn.click();
      return {ok:1};
    })()
    """)
    time.sleep(3)
    return r


def schedule_video(year, month, day, hour_utc, minute_utc):
    """Schedule publish — Studio uses Paris UTC+2, so add 2h for UTC target."""
    # Paris is UTC+2 in summer; to publish at 17:00 UTC, set 19:00 in Studio
    studio_hour = (hour_utc + 2) % 24

    # 1. Click "Programmer" radio
    js("""
    (() => {
      const radios = Array.from(document.querySelectorAll('tp-yt-paper-radio-button,paper-radio-button')).filter(e => e.offsetParent !== null);
      const sched = radios.find(r => (r.getAttribute('name')||'') === 'SCHEDULE');
      if (sched) { sched.click(); return {ok:1}; }
      return {err:'no_schedule', names: radios.map(r=>r.getAttribute('name'))};
    })()
    """)
    time.sleep(2)

    # 2. Click date input to open calendar
    js("""
    (() => {
      const dateEl = document.querySelector('ytcp-date-picker') || document.querySelector('[aria-label*="date"]');
      if (dateEl) { dateEl.click(); return {ok:1}; }
      const inputs = Array.from(document.querySelectorAll('input')).filter(i => i.offsetParent !== null && (i.type==='text' || i.type==='date'));
      if (inputs.length) { inputs[0].click(); return {ok:2}; }
      return {err:'no_date_input'};
    })()
    """)
    time.sleep(2)

    months_fr = ["janvier","février","mars","avril","mai","juin","juillet","août","septembre","octobre","novembre","décembre"]
    target_month_label = f"{months_fr[month-1]} {year}"

    pick_script = f"""
    (async () => {{
      const sleep = (ms) => new Promise(r => setTimeout(r, ms));
      const targetLabel = {json.dumps(target_month_label)};
      for (let i = 0; i < 12; i++) {{
        const headers = Array.from(document.querySelectorAll('*'))
          .filter(e => e.offsetParent !== null && /^(janvier|f[ée]vrier|mars|avril|mai|juin|juillet|ao[ûu]t|septembre|octobre|novembre|d[ée]cembre)\\s+\\d{{4}}$/i.test((e.textContent||'').trim()));
        if (headers.some(h => h.textContent.trim().toLowerCase() === targetLabel.toLowerCase())) break;
        const nextBtn = Array.from(document.querySelectorAll('button,ytcp-icon-button'))
          .filter(b => b.offsetParent !== null)
          .find(b => /suivant|next|mois suivant/i.test(b.getAttribute('aria-label')||''));
        if (!nextBtn) return {{err:'no_next_month'}};
        nextBtn.click();
        await sleep(400);
      }}
      const all = Array.from(document.querySelectorAll('span,div,td,button')).filter(e => e.offsetParent !== null);
      let found = false;
      for (const el of all) {{
        const txt = (el.textContent||'').trim();
        if (!found && txt.toLowerCase() === targetLabel.toLowerCase()) {{ found = true; continue; }}
        if (found && txt === {json.dumps(str(day))}) {{
          el.click();
          return {{ok:1, day:txt}};
        }}
      }}
      return {{err:'day_not_found', searched:{json.dumps(str(day))}}};
    }})()
    """
    r = js(pick_script, timeout=30)
    print(f"  calendar: {r}")
    time.sleep(2)

    # 4. Set time (Paris local = UTC+2)
    time_str = f"{studio_hour:02d}:{minute_utc:02d}"
    js(f"""
    (() => {{
      const timeInputs = Array.from(document.querySelectorAll('input')).filter(i => {{
        return i.offsetParent !== null && (
          (i.placeholder||'').toLowerCase().includes('heure') ||
          /^\\d{{1,2}}:\\d{{2}}$/.test(i.value||'')
        );
      }});
      if (!timeInputs.length) return {{err:'no_time'}};
      const inp = timeInputs[timeInputs.length-1];
      const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value').set;
      setter.call(inp, {json.dumps(time_str)});
      inp.dispatchEvent(new Event('input', {{bubbles:true}}));
      inp.dispatchEvent(new Event('change', {{bubbles:true}}));
      inp.dispatchEvent(new Event('blur', {{bubbles:true}}));
      return {{ok:1, val:inp.value}};
    }})()
    """)
    time.sleep(1.5)
    return r


def click_schedule_button():
    return js("""
    (() => {
      const btn = Array.from(document.querySelectorAll('ytcp-button,button'))
        .filter(b => b.offsetParent !== null)
        .find(b => /programmer|schedule/i.test((b.textContent||'').trim()));
      if (!btn) return {err:'no_btn'};
      if (btn.getAttribute('disabled') || btn.getAttribute('aria-disabled')==='true') return {err:'disabled'};
      btn.click();
      return {ok:1, txt:btn.textContent.trim()};
    })()
    """)


def main():
    print("=== Step 7: Upload Long-form to YouTube Studio ===")
    m.initialize()

    print(f"  Navigating Studio upload ({SESSION})...")
    navigate_studio_upload()

    print(f"  Injecting video from CDN: {CDN_BASE}/{VIDEO_FILENAME}")
    r = inject_video(VIDEO_FILENAME)
    print(f"  inject result: {json.dumps(r)[:400]}")

    # Check for CDN failure
    r_str = json.dumps(r)
    if "fetch_fail" in r_str or "no_file_input" in r_str:
        print("\n  BLOCKER: Video not accessible at CDN URL.")
        print(f"  Expected: {CDN_BASE}/{VIDEO_FILENAME}")
        print("  Fix: Push the render to the CDN repo or set VOIDLINE_CDN_BASE env var.")
        log_action("UPLOAD_BLOCKED_CDN", f"Video not found at {CDN_BASE}/{VIDEO_FILENAME}. Run again after pushing video to CDN.")
        sys.exit(2)

    print("  Waiting for title/desc editors...")
    if not wait_for_title_editor():
        print("  ERROR: Upload dialog editors not visible")
        log_action("UPLOAD_FAILED", "Editors did not appear after inject")
        sys.exit(1)

    print("  Filling title + description + tags...")
    r = fill_metadata(TITLE, DESCRIPTION, TAGS)
    print(f"  metadata: {json.dumps(r)[:200]}")

    time.sleep(1.5)
    print("  Setting not-for-kids...")
    not_for_kids()

    # Walk wizard: 3× Suivant
    for step in range(3):
        time.sleep(2)
        r = click_next()
        print(f"  next {step+1}: {json.dumps(r)[:100]}")
    time.sleep(4)

    print(f"  Scheduling: {PUBLISH_DATE['year']}-{PUBLISH_DATE['month']:02d}-{PUBLISH_DATE['day']:02d} {PUBLISH_TIME['hour']:02d}:{PUBLISH_TIME['minute']:02d} UTC")
    schedule_video(
        PUBLISH_DATE["year"], PUBLISH_DATE["month"], PUBLISH_DATE["day"],
        PUBLISH_TIME["hour"], PUBLISH_TIME["minute"]
    )

    time.sleep(2)
    print("  Clicking schedule button...")
    r = click_schedule_button()
    print(f"  schedule btn: {json.dumps(r)[:200]}")
    time.sleep(6)

    print("\n=== Upload submitted. Verify in Studio. ===")
    log_action("LONG_FORM_UPLOAD_SUBMITTED", {
        "title": TITLE,
        "publish_at": f"{PUBLISH_DATE['year']}-{PUBLISH_DATE['month']:02d}-{PUBLISH_DATE['day']:02d}T{PUBLISH_TIME['hour']:02d}:{PUBLISH_TIME['minute']:02d}:00Z",
        "video_file": VIDEO_FILENAME,
        "cdn_url": f"{CDN_BASE}/{VIDEO_FILENAME}",
        "thumb_path": THUMB_PATH,
    })


if __name__ == "__main__":
    main()
