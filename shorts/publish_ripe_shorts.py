#!/usr/bin/env python3
"""Scan shorts_state.json and flip any PRIVATE Short whose publish_at is in
the past to PUBLIC via Studio. Idempotent — safe to run repeatedly.

Intended to be called by a daily cron / cloud schedule.

Auth: relies on the `voidline` cookie_profile stored in the camoufox MCP
container. If cookies expire, this will fail (prints to stderr).
"""
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, "/host/home/follox/.openclaw/yt-viral/runs/voidline-20260527-002843")
import mcp_stealth as m

STATE = Path(__file__).parent / "shorts_state.json"
SESSION = "publish_runner"


def js(script):
    return m.call("stealth_evaluate", {"session": SESSION, "script": script})


def publish_one(yt_id, title):
    """Open Studio edit page for the video, flip visibility → Public, save."""
    print(f"\n>>> publishing {yt_id} — {title[:60]}")
    m.call("stealth_navigate", {
        "url": f"https://studio.youtube.com/video/{yt_id}/edit",
        "session": SESSION,
        "cookie_profile": "voidline",
    })
    time.sleep(8)

    # The visibility setting on the edit page is a dropdown trigger. Click it
    # to open the visibility selector.
    r = js("""
    (() => {
      const triggers = Array.from(document.querySelectorAll('ytcp-text-dropdown-trigger,ytcp-visibility-text-dropdown'))
        .filter(e => e.offsetParent !== null);
      const vis = triggers.find(t => /priv|publi|non répert/i.test(t.textContent||''));
      if (!vis) return {err:'no_trigger', n:triggers.length};
      vis.click();
      return {ok:1};
    })()
    """)
    print("  trigger:", r.get("result", {}).get("content", [{}])[0].get("text", "")[:120])
    time.sleep(3)

    # The visibility dialog now has the PRIVATE/UNLISTED/PUBLIC radios.
    r = js("""
    (() => {
      const radios = Array.from(document.querySelectorAll('tp-yt-paper-radio-button')).filter(e => e.offsetParent !== null);
      const pub = radios.find(r => r.getAttribute('name') === 'PUBLIC');
      if (!pub) return {err:'no_public', names:radios.map(r => r.getAttribute('name'))};
      pub.click();
      return {ok:1};
    })()
    """)
    print("  PUBLIC:", r.get("result", {}).get("content", [{}])[0].get("text", "")[:150])
    time.sleep(2)

    # Confirm: click "Enregistrer" / "Save"
    r = js("""
    (() => {
      const btns = Array.from(document.querySelectorAll('ytcp-button,button')).filter(b => b.offsetParent !== null);
      const save = btns.find(b => /^enregistrer$|^save$|^publier$/i.test((b.textContent||'').trim()));
      if (!save) return {err:'no_save', labels: btns.map(b => b.textContent.trim().slice(0,20))};
      save.click();
      return {ok:1, txt: save.textContent.trim()};
    })()
    """)
    print("  save:", r.get("result", {}).get("content", [{}])[0].get("text", "")[:200])
    time.sleep(5)
    return True


def main():
    m.initialize()
    state = json.loads(STATE.read_text())
    now = datetime.now(timezone.utc)
    ripe = []
    for s in state["shorts"]:
        if s["status"] != "PRIVATE":
            continue
        ts = datetime.fromisoformat(s["publish_at"].replace("Z", "+00:00"))
        if ts <= now:
            ripe.append(s)

    if not ripe:
        print(f"[{now.isoformat()}] No ripe Shorts (next: {min((datetime.fromisoformat(s['publish_at'].replace('Z','+00:00')) for s in state['shorts'] if s['status']=='PRIVATE'), default='—')})")
        return

    print(f"[{now.isoformat()}] {len(ripe)} ripe Shorts to publish: {[s['short_id'] for s in ripe]}")
    for s in ripe:
        try:
            ok = publish_one(s["yt_id"], s["title"])
            if ok:
                s["status"] = "PUBLIC"
                s["published_at"] = now.isoformat()
        except Exception as e:
            print(f"  !! exception: {e}")
            s.setdefault("errors", []).append({"at": now.isoformat(), "err": str(e)})

    STATE.write_text(json.dumps(state, indent=2))
    print(f"\nState updated. {sum(1 for s in state['shorts'] if s['status']=='PUBLIC')}/{len(state['shorts'])} Public.")


if __name__ == "__main__":
    main()
