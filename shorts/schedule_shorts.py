#!/usr/bin/env python3
"""Schedule the remaining Private Shorts via Studio edit page.

For each Short:
  1. Open https://studio.youtube.com/video/{yt_id}/edit
  2. Click visibility edit icon
  3. Expand second-container (Programmer section)
  4. Pick day in calendar
  5. Set time input
  6. Click OK then Enregistrer
"""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, "/host/home/follox/.openclaw/yt-viral/runs/voidline-20260527-002843")
import mcp_stealth as m

SESSION = "yt_upload"
STATE = Path(__file__).parent / "shorts_state.json"


def js(script):
    r = m.call("stealth_evaluate", {"session": SESSION, "script": script})
    return r.get("result", {}).get("content", [{}])[0].get("text", "")


def schedule_one(yt_id, target_date, target_time):
    """target_date: 'YYYY-MM-DD' ; target_time: 'HH:MM'"""
    year, month, day = [int(x) for x in target_date.split("-")]
    print(f"\n>>> {yt_id} → {target_date} {target_time}")

    # 1. Open edit page
    m.call("stealth_navigate", {
        "url": f"https://studio.youtube.com/video/{yt_id}/edit",
        "session": SESSION,
    })
    time.sleep(9)

    # 2. Click visibility edit icon
    print("  edit-pencil:", js("""
    (() => {
      const cont = document.querySelector('ytcp-video-metadata-visibility');
      const btn = cont?.querySelector('ytcp-icon-button');
      if (!btn) return {err:'no_pencil'};
      btn.click();
      return {ok:1};
    })()
    """)[:120])
    time.sleep(4)

    # 3. Expand the Programmer section (second-container)
    print("  expand:", js("""
    (() => {
      const btn = document.querySelector('#second-container-expand-button');
      if (!btn) return {err:'no_expand'};
      btn.click();
      return {ok:1};
    })()
    """)[:120])
    time.sleep(3)

    # 4. Pick the target day in the calendar
    months_fr = ["janvier","février","mars","avril","mai","juin","juillet","août","septembre","octobre","novembre","décembre"]
    target_month_label = f"{months_fr[month-1]} {year}".lower()

    print("  day-pick:", js(f"""
    (async () => {{
      const sleep = (ms) => new Promise(r => setTimeout(r, ms));
      /* Open the date dropdown */
      const dp = document.querySelector('ytcp-datetime-picker');
      if (!dp) return {{err:'no_dp'}};
      const trigger = dp.querySelector('ytcp-text-dropdown-trigger');
      if (!trigger) return {{err:'no_trigger'}};
      trigger.click();
      await sleep(800);

      const targetLabel = {json.dumps(target_month_label)};
      const targetDay = {day};

      /* Scroll calendar to the target month if needed */
      for (let attempt = 0; attempt < 12; attempt++) {{
        const headers = Array.from(document.querySelectorAll('div,span'))
          .filter(e => e.offsetParent !== null && /^(janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\\s+\\d{{4}}$/i.test(e.textContent.trim()));
        const matchH = headers.find(h => h.textContent.trim().toLowerCase() === targetLabel);
        if (matchH) break;
        const nextBtn = Array.from(document.querySelectorAll('button,ytcp-icon-button'))
          .filter(b => b.offsetParent !== null)
          .find(b => (b.getAttribute('aria-label')||'').toLowerCase().match(/suivant|next|mois suivant/));
        if (!nextBtn) break;
        nextBtn.click();
        await sleep(400);
      }}

      /* Find target day SPAN after target header in DOM order */
      const all = Array.from(document.querySelectorAll('span,div,td,button')).filter(e => e.offsetParent !== null);
      let foundHeader = false;
      for (const el of all) {{
        const txt = (el.textContent||'').trim();
        if (!foundHeader && txt.toLowerCase() === targetLabel) {{ foundHeader = true; continue; }}
        if (foundHeader && txt === String(targetDay) && /calendar-day/.test(el.className||'')) {{
          el.click();
          return {{ok:1, txt}};
        }}
      }}
      return {{err:'day_not_found'}};
    }})()
    """)[:200])
    time.sleep(3)

    # 5. Set time input
    print("  time-set:", js(f"""
    (() => {{
      const inp = document.querySelector('ytcp-datetime-picker input');
      if (!inp) return {{err:'no_time_input'}};
      inp.focus();
      inp.select();
      const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
      setter.call(inp, {json.dumps(target_time)});
      inp.dispatchEvent(new Event('input', {{bubbles:true}}));
      inp.dispatchEvent(new Event('change', {{bubbles:true}}));
      inp.dispatchEvent(new Event('blur', {{bubbles:true}}));
      return {{val: inp.value}};
    }})()
    """)[:120])
    time.sleep(2)

    # 6. Click OK in the dialog
    print("  OK:", js("""
    (() => {
      const ok = Array.from(document.querySelectorAll('ytcp-button,button'))
        .filter(b => b.offsetParent !== null && b.closest('ytcp-video-visibility-edit-popup'))
        .find(b => (b.textContent||'').trim() === 'OK');
      if (!ok) return {err:'no_ok'};
      if (ok.hasAttribute('disabled')) return {err:'disabled'};
      ok.click();
      return {ok:1};
    })()
    """)[:120])
    time.sleep(4)

    # 7. Click outer Enregistrer
    print("  save:", js("""
    (() => {
      const btns = Array.from(document.querySelectorAll('ytcp-button,button')).filter(b => b.offsetParent !== null);
      const save = btns.find(b => /^Enregistrer$/.test((b.textContent||'').trim()));
      if (!save) return {err:'no_save'};
      if (save.hasAttribute('disabled')||save.getAttribute('aria-disabled')==='true') return {err:'disabled'};
      save.click();
      return {ok:1};
    })()
    """)[:120])
    time.sleep(6)

    # Confirm
    final = js("""
    (() => {
      const cont = document.querySelector('ytcp-video-metadata-visibility');
      return { vis: cont?.textContent.trim().slice(0, 100) };
    })()
    """)
    print("  state:", final[:200])
    return "Programm" in final  # "Programmée" indicates success


def main():
    m.initialize()
    state = json.loads(STATE.read_text())
    target_id = sys.argv[1] if len(sys.argv) > 1 else None

    for s in state["shorts"]:
        if s["status"] != "PRIVATE":
            continue
        if target_id and s["short_id"] != target_id:
            continue
        # Parse target publish_at
        dt = s["publish_at"]  # e.g. "2026-06-02T12:00:00Z"
        date_part = dt.split("T")[0]
        time_part = dt.split("T")[1][:5]  # HH:MM
        try:
            ok = schedule_one(s["yt_id"], date_part, time_part)
            if ok:
                s["status"] = "SCHEDULED"
                s["scheduled_at"] = dt
        except Exception as e:
            print(f"  !! exception: {e}")
        time.sleep(4)

    STATE.write_text(json.dumps(state, indent=2))


if __name__ == "__main__":
    main()
