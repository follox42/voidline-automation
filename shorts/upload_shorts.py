#!/usr/bin/env python3
"""Batch-upload Voidline Shorts with scheduled publish via camoufox stealth.

For each Short:
  1. Open Studio upload dialog
  2. Fetch MP4 from raw.githubusercontent.com + DataTransfer inject
  3. Fill title + description (contenteditable boxes)
  4. Not made for kids
  5. Suivant × 3 → Visibility step
  6. Click "Programmer" radio
  7. Pick date in calendar widget + set time
  8. Confirm "Programmer" button

Logs each result to agent-log.json.
"""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, "/host/home/follox/.openclaw/yt-viral/runs/voidline-20260527-002843")
import mcp_stealth as m

SESSION = "yt_upload"
RAW_BASE = "https://raw.githubusercontent.com/follox42/voidline-remotion-preview/main/public"

LOG_PATH = Path(
    "/host/home/follox/.openclaw/yt-viral/runs/voidline-20260527-002843/remotion/public/agent-log.json"
)


def log(action, detail):
    data = json.loads(LOG_PATH.read_text())
    data.setdefault("decisions", []).append({
        "t": time.strftime("%Y-%m-%d %H:%M"),
        "action": action,
        "detail": detail,
    })
    LOG_PATH.write_text(json.dumps(data, indent=2))


def call(name, args):
    return m.call(name, args)


def js(script):
    return call("stealth_evaluate", {"session": SESSION, "script": script})


def wait_text_match(needles, timeout=30):
    """Poll page text until any of `needles` substring appears."""
    end = time.time() + timeout
    while time.time() < end:
        r = js("(() => document.body.innerText.slice(0, 4000))()")
        try:
            txt = r["result"]["content"][0]["text"]
            # The JSON-wrapped result has the actual text inside "result": "..."
            import re
            m2 = re.search(r'"result"\s*:\s*"((?:[^"\\]|\\.)*)"', txt)
            if m2:
                page = m2.group(1).replace("\\n", "\n").replace('\\"', '"')
                if any(n in page for n in needles):
                    return True
        except Exception:
            pass
        time.sleep(1.5)
    return False


def navigate_upload():
    """Open the upload dialog from the channel videos page."""
    call("stealth_navigate", {
        "url": "https://studio.youtube.com/channel/UCzbzLj0WW72_mTa86MwzkQQ/videos/upload",
        "session": SESSION,
    })
    time.sleep(5)
    # Click Create
    js("""
    (() => {
      const all = Array.from(document.querySelectorAll('button,ytcp-button')).filter(b => b.offsetParent !== null);
      const cr = all.find(b => (b.getAttribute('aria-label')||'').toLowerCase().includes('créer'));
      if (cr) cr.click();
      return cr ? 1 : 0;
    })()
    """)
    time.sleep(2)
    # Click "Importer des vidéos"
    js("""
    (() => {
      const items = Array.from(document.querySelectorAll('tp-yt-paper-item,ytcp-text-menu-item')).filter(e => e.offsetParent !== null);
      const imp = items.find(i => i.textContent.includes('Importer'));
      if (imp) imp.click();
      return imp ? 1 : 0;
    })()
    """)
    time.sleep(4)


def inject_file(filename):
    """Fetch the MP4 from GitHub raw and inject as DataTransfer File."""
    url = f"{RAW_BASE}/{filename}"
    script = f"""
    (async () => {{
      const resp = await fetch({json.dumps(url)});
      if (!resp.ok) return {{err:'fetch', status:resp.status}};
      const blob = await resp.blob();
      const file = new File([blob], {json.dumps(filename)}, {{type:'video/mp4'}});
      const input = document.querySelector('input[type=file]');
      if (!input) return {{err:'no_input'}};
      const dt = new DataTransfer();
      dt.items.add(file);
      input.files = dt.files;
      input.dispatchEvent(new Event('change', {{bubbles:true}}));
      return {{ok:1, size_mb:(file.size/1024/1024).toFixed(1)}};
    }})()
    """
    return js(script)


def wait_for_editors(timeout=60):
    """Wait until the title/description contenteditable boxes appear."""
    end = time.time() + timeout
    while time.time() < end:
        r = js("(() => Array.from(document.querySelectorAll('[contenteditable=true]')).filter(e => e.offsetParent !== null).length)()")
        try:
            txt = r["result"]["content"][0]["text"]
            if '"result": 2' in txt or '"result":2' in txt:
                return True
        except Exception:
            pass
        time.sleep(2)
    return False


def fill_title_desc(title, desc):
    script = f"""
    (async () => {{
      const sleep = (ms) => new Promise(r => setTimeout(r, ms));
      const editors = Array.from(document.querySelectorAll('[contenteditable=true]')).filter(e => e.offsetParent !== null);
      if (editors.length < 2) return {{err:'editors', n:editors.length}};
      const setText = async (el, value) => {{
        el.focus();
        await sleep(180);
        document.execCommand('selectAll', false, null);
        document.execCommand('delete', false, null);
        document.execCommand('insertText', false, value);
        el.dispatchEvent(new Event('input', {{bubbles:true}}));
        el.dispatchEvent(new Event('change', {{bubbles:true}}));
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
      const inputs = Array.from(document.querySelectorAll('tp-yt-paper-radio-button,paper-radio-button')).filter(e => e.offsetParent !== null);
      const notMFK = inputs.find(r => (r.getAttribute('name')||'') === 'VIDEO_MADE_FOR_KIDS_NOT_MFK');
      if (notMFK) { notMFK.click(); return {ok:1}; }
      return {err:'not_found'};
    })()
    """)


def click_next():
    return js("""
    (() => {
      const btn = Array.from(document.querySelectorAll('ytcp-button,button'))
        .filter(b => b.offsetParent !== null)
        .find(b => {
          const txt = (b.textContent || '').trim().toLowerCase();
          const al = (b.getAttribute('aria-label') || '').toLowerCase();
          return (txt === 'suivant' || al.includes('suivant')) && !al.includes('précédent');
        });
      if (!btn) return {err:'no_next'};
      if (btn.hasAttribute('disabled') || btn.getAttribute('aria-disabled')==='true') return {err:'disabled'};
      btn.click();
      return {ok:1};
    })()
    """)


def schedule_publish(year, month, day, hour, minute):
    """Click 'Programmer', pick date+time, confirm."""
    # 1. Click "Programmer" radio
    js("""
    (() => {
      const radios = Array.from(document.querySelectorAll('tp-yt-paper-radio-button,paper-radio-button')).filter(e => e.offsetParent !== null);
      const sched = radios.find(r => (r.getAttribute('name')||'') === 'SCHEDULE');
      if (sched) { sched.click(); return {ok:1}; }
      return {err:'no_schedule_radio', names: radios.map(r => r.getAttribute('name'))};
    })()
    """)
    time.sleep(2)
    # 2. Open date picker → click date input field
    js("""
    (() => {
      const dateInputs = Array.from(document.querySelectorAll('input')).filter(i => {
        const ph = (i.placeholder||'').toLowerCase();
        return i.offsetParent !== null && (ph.includes('date') || ph.includes('jj') || /\\d{2}\\s*\\w+\\s*\\d{4}/.test(i.value||''));
      });
      if (dateInputs.length) { dateInputs[0].focus(); dateInputs[0].click(); return {ok:1, val:dateInputs[0].value}; }
      const all = Array.from(document.querySelectorAll('ytcp-date-picker, ytcp-icon-button')).filter(e => e.offsetParent !== null);
      if (all.length) { all[0].click(); return {ok:2}; }
      return {err:'no_date'};
    })()
    """)
    time.sleep(2)

    # 3. Walk calendar to target month, click day
    months_fr = ["janvier","février","mars","avril","mai","juin","juillet","août","septembre","octobre","novembre","décembre"]
    target_month_label = f"{months_fr[month-1]} {year}"
    pick_script = f"""
    (async () => {{
      const sleep = (ms) => new Promise(r => setTimeout(r, ms));
      const targetLabel = {json.dumps(target_month_label)};
      // Find header that says e.g. "JUIN 2026" — climb calendar to reach it
      for (let attempt = 0; attempt < 12; attempt++) {{
        const headers = Array.from(document.querySelectorAll('div,span'))
          .filter(e => e.offsetParent !== null && /^(janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\\s+\\d{{4}}$/i.test(e.textContent.trim()));
        if (headers.some(h => h.textContent.trim().toLowerCase() === targetLabel.toLowerCase())) break;
        // Click "next month" button
        const nextBtn = Array.from(document.querySelectorAll('button,ytcp-icon-button'))
          .filter(b => b.offsetParent !== null)
          .find(b => (b.getAttribute('aria-label')||'').toLowerCase().match(/suivant|next|mois suivant/));
        if (!nextBtn) return {{err:'no_next_month'}};
        nextBtn.click();
        await sleep(300);
      }}
      // Find the day cell — needs to be the right "{day}" AFTER the target header
      const all = Array.from(document.querySelectorAll('span,div,td,button')).filter(e => e.offsetParent !== null);
      let foundHeader = false;
      for (const el of all) {{
        const txt = el.textContent.trim();
        if (!foundHeader && txt.toLowerCase() === targetLabel.toLowerCase()) {{ foundHeader = true; continue; }}
        if (foundHeader && txt === {json.dumps(str(day))}) {{
          el.click();
          return {{ok:1, clicked:txt}};
        }}
      }}
      return {{err:'day_not_found'}};
    }})()
    """
    r = js(pick_script)
    time.sleep(2)

    # 4. Set time field
    time_str = f"{hour:02d}:{minute:02d}"
    js(f"""
    (() => {{
      const timeInputs = Array.from(document.querySelectorAll('input')).filter(i => {{
        const ph = (i.placeholder||'').toLowerCase();
        return i.offsetParent !== null && (ph.includes('heure') || ph.includes('time') || /^\\d{{1,2}}:\\d{{2}}$/.test(i.value||''));
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
    time.sleep(2)
    return r


def click_publish_or_schedule():
    return js("""
    (() => {
      const btn = Array.from(document.querySelectorAll('ytcp-button,button'))
        .filter(b => b.offsetParent !== null)
        .find(b => {
          const txt = (b.textContent || '').trim().toLowerCase();
          return txt === 'programmer' || txt === 'publier' || txt === 'schedule' || txt === 'publish';
        });
      if (!btn) return {err:'no_btn', visible: Array.from(document.querySelectorAll('ytcp-button,button')).filter(b => b.offsetParent).map(b => b.textContent.trim().slice(0,20))};
      if (btn.hasAttribute('disabled') || btn.getAttribute('aria-disabled')==='true') return {err:'disabled'};
      btn.click();
      return {ok:1, txt:btn.textContent.trim()};
    })()
    """)


def upload_one(spec):
    """Upload as PRIVATE — YT does not support Shorts scheduling on
    non-monetized channels (trust-tier limitation). The Short will be
    published manually (or via ScheduleWakeup) at spec['schedule_date'].
    """
    filename = spec["filename"]
    print(f"\n{'='*60}\n>>> {spec['short_id']} ({filename}) — save PRIVATE, target publish {spec['schedule_date']} {spec['schedule_time']}\n{'='*60}")
    navigate_upload()
    r = inject_file(filename)
    print("inject:", json.dumps(r, indent=2)[:300])
    if not wait_for_editors():
        print("!! editors did not appear")
        return False
    r = fill_title_desc(spec["title"], spec["desc"])
    print("title/desc:", json.dumps(r, indent=2)[:300])
    time.sleep(1)
    r = not_for_kids()
    print("not-for-kids:", json.dumps(r, indent=2)[:200])
    time.sleep(1.5)
    # Walk wizard 3 steps to Visibility
    for step in range(3):
        time.sleep(1.5)
        r = click_next()
        print(f"next step {step+1}:", json.dumps(r, indent=2)[:150])
    time.sleep(4)
    # Select PRIVATE (we'll publish manually later via wakeup)
    r = js("""
    (() => {
      const r = Array.from(document.querySelectorAll('tp-yt-paper-radio-button')).find(e => e.getAttribute('name') === 'PRIVATE');
      if (r) { r.click(); return {ok:1}; }
      return {err:'no_private'};
    })()
    """)
    print("private:", json.dumps(r, indent=2)[:200])
    time.sleep(2)
    # Click Enregistrer
    r = js("""
    (() => {
      const btns = Array.from(document.querySelectorAll('ytcp-button,button')).filter(b => b.offsetParent !== null);
      const save = btns.find(b => /enregistrer|save|done|termin/i.test(b.textContent||''));
      if (!save) return {err:'no_save', labels:btns.map(b => b.textContent.trim().slice(0,25))};
      save.click();
      return {ok:1, txt:save.textContent.trim()};
    })()
    """)
    print("save:", json.dumps(r, indent=2)[:200])
    time.sleep(7)
    log(f"SHORT_{spec['short_id'].upper()}_UPLOADED_PRIVATE",
        f"{filename} — target publish {spec['schedule_date']} {spec['schedule_time']} — {spec['title'][:60]}")
    return True


SPECS = [
    {
        "short_id": "v1_twist",
        "filename": "short_v1_twist.mp4",
        "title": "Captain Morehouse Boards an Empty Ship — Mary Celeste #shorts",
        "desc": "December 5, 1872. The Mary Celeste was found drifting in the Atlantic. Sails set, breakfast still warm, lifeboat gone. Ten people had vanished.\n\n→ Full doc: https://youtu.be/sB8VXu2OHtY\n\n#shorts #history #mystery #marycelest #ghostship #voidline",
        "schedule_date": "2026-06-02", "schedule_time": "12:00",
    },
    {
        "short_id": "v2_hook",
        "filename": "short_v2_hook.mp4",
        "title": "9 Soviet Hikers Cut Their Tent and Ran Barefoot — Dyatlov 1959 #shorts",
        "desc": "February 1959. Nine experienced Soviet hikers cut their tent open from the inside and ran barefoot into a -30°C blizzard. Three weeks later, all found dead with injuries no avalanche should cause.\n\n→ Full doc: https://youtu.be/pM-u_8ONjI0\n\n#shorts #history #mystery #dyatlovpass #unsolved #voidline",
        "schedule_date": "2026-06-03", "schedule_time": "12:00",
    },
    {
        "short_id": "v1_answer",
        "filename": "short_v1_answer.mp4",
        "title": "The 9 Missing Barrels Theory — Mary Celeste Solved? #shorts",
        "desc": "1,701 barrels of alcohol in the hold. 9 found empty. The forensic theory that finally explains why a perfectly seaworthy ship was abandoned in seconds.\n\n→ Full doc: https://youtu.be/sB8VXu2OHtY\n\n#shorts #history #mystery #marycelest #solved #voidline",
        "schedule_date": "2026-06-04", "schedule_time": "12:00",
    },
    {
        "short_id": "v2_twist",
        "filename": "short_v2_twist.mp4",
        "title": "Every Dyatlov Pass Theory Failed for 62 Years #shorts",
        "desc": "Avalanche? Too steep. Attack? No tracks. Soviet military? Files classified. For 62 years no theory survived the evidence — until 2 Swiss engineers ran the physics in 2020.\n\n→ Full doc: https://youtu.be/pM-u_8ONjI0\n\n#shorts #dyatlovpass #unsolved #history #voidline",
        "schedule_date": "2026-06-05", "schedule_time": "12:00",
    },
    {
        "short_id": "v2_answer",
        "filename": "short_v2_answer.mp4",
        "title": "The 2021 Paper That Solved Dyatlov Pass #shorts",
        "desc": "Gaume & Puzrin 2021. A 5-meter slab avalanche too small to be detected — but heavy enough to crush 4 chests through a tent. 62 years for the answer.\n\n→ Full doc: https://youtu.be/pM-u_8ONjI0\n\n#shorts #dyatlovpass #science #history #voidline",
        "schedule_date": "2026-06-06", "schedule_time": "12:00",
    },
    {
        "short_id": "v3_hook",
        "filename": "short_v3_hook.mp4",
        "title": "The 1908 Siberian Sky Explosion — Tunguska #shorts",
        "desc": "June 30, 1908. 7:14 AM. The sky over Siberia exploded with 1,000× the force of Hiroshima. 80 million trees flattened. No crater. No fragments. 112 years of questions.\n\n→ Full doc coming June 5\n\n#shorts #tunguska #history #mystery #voidline",
        "schedule_date": "2026-06-08", "schedule_time": "12:00",
    },
    {
        "short_id": "v3_twist",
        "filename": "short_v3_twist.mp4",
        "title": "Antimatter? Black Hole? The Tunguska Mystery #shorts",
        "desc": "For decades the theories piled up — antimatter, black holes, alien craft. None matched the physics. Until Russian scientists ran the numbers in 2020.\n\n→ Full doc coming June 5\n\n#shorts #tunguska #science #unsolved #voidline",
        "schedule_date": "2026-06-10", "schedule_time": "12:00",
    },
    {
        "short_id": "v3_answer",
        "filename": "short_v3_answer.mp4",
        "title": "The 2020 Theory That Explains Tunguska #shorts",
        "desc": "Khrennikov et al, 2020. A 200-meter iron asteroid grazed Earth's atmosphere at 11 km/s. Airburst at 5-10 km. Then bounced back into space — still in orbit, somewhere.\n\n→ Full doc coming June 5\n\n#shorts #tunguska #asteroid #science #voidline",
        "schedule_date": "2026-06-12", "schedule_time": "12:00",
    },
]


def main():
    m.initialize()
    target_id = sys.argv[1] if len(sys.argv) > 1 else None
    for spec in SPECS:
        if target_id and spec["short_id"] != target_id:
            continue
        try:
            upload_one(spec)
        except Exception as e:
            print(f"!! exception on {spec['short_id']}: {e}")
            log(f"SHORT_{spec['short_id'].upper()}_FAILED", str(e)[:200])
        time.sleep(5)


if __name__ == "__main__":
    main()
