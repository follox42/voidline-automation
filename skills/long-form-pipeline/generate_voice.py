#!/usr/bin/env python3
"""
Step 2 — Voice Generation (ElevenLabs eleven_v3)
Usage: python3 skills/long-form-pipeline/generate_voice.py <run_dir>
"""
import os, sys, json, time, requests

RUN_DIR = sys.argv[1] if len(sys.argv) > 1 else "runs/v4-roanoke"
SCRIPT_PATH = os.path.join(RUN_DIR, "script.json")
VOICE_DIR = os.path.join(RUN_DIR, "voice")
ELEVENLABS_KEY = os.environ.get("ELEVENLABS_KEY", "")
VOICE_ID = os.environ.get("VOICE_ID", "ppLqTilh7rH7fbUVlXsf")  # default: David Documentary
MODEL_ID = os.environ.get("MODEL_ID", "eleven_v3")
VOICE_SETTINGS = {
    "stability": 0.5,
    "similarity_boost": 0.75,
    "style": 0.35,
    "speed": 0.95,
    "use_speaker_boost": True
}

def strip_stage_directions(text):
    """Remove ElevenLabs stage directions like [serious] [softly] etc."""
    import re
    # Keep the brackets as ElevenLabs v3 understands them natively
    return text.strip()

def generate_chapter_voice(chapter_id, text, out_path):
    """Call ElevenLabs TTS API and save MP3."""
    if os.path.exists(out_path):
        print(f"  [SKIP] ch{chapter_id} already exists: {out_path}")
        return True

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
    headers = {
        "xi-api-key": ELEVENLABS_KEY,
        "Content-Type": "application/json",
        "Accept": "audio/mpeg"
    }
    payload = {
        "text": text,
        "model_id": MODEL_ID,
        "voice_settings": VOICE_SETTINGS
    }
    print(f"  Generating ch{chapter_id} ({len(text)} chars)...")
    resp = requests.post(url, headers=headers, json=payload, timeout=120)
    if resp.status_code != 200:
        print(f"  ERROR ch{chapter_id}: {resp.status_code} {resp.text[:200]}")
        return False

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "wb") as f:
        f.write(resp.content)
    size_kb = len(resp.content) // 1024
    print(f"  OK ch{chapter_id}: {size_kb}KB → {out_path}")
    return True

def get_character_count():
    """Check remaining ElevenLabs character quota."""
    url = "https://api.elevenlabs.io/v1/user"
    resp = requests.get(url, headers={"xi-api-key": ELEVENLABS_KEY}, timeout=10)
    if resp.status_code == 200:
        data = resp.json()
        sub = data.get("subscription", {})
        remaining = sub.get("character_limit", 0) - sub.get("character_count", 0)
        print(f"  ElevenLabs quota: {remaining} chars remaining")
        return remaining
    return None

def main():
    if not ELEVENLABS_KEY:
        print("ABORT: ELEVENLABS_KEY not set")
        sys.exit(1)

    with open(SCRIPT_PATH) as f:
        script = json.load(f)

    # Variant settings from script.json win over module defaults, so A/B
    # voice arms (pick_variant.py voices/*.json) keep identical settings
    # across data points.
    global VOICE_ID, MODEL_ID
    vs = script.get("_voice_settings") or {}
    if vs:
        MODEL_ID = os.environ.get("MODEL_ID") or vs.get("model_id", MODEL_ID)
        for k in ("stability", "similarity_boost", "style", "speed", "use_speaker_boost"):
            if k in vs:
                VOICE_SETTINGS[k] = vs[k]
            elif k == "speed":
                VOICE_SETTINGS.pop("speed", None)
    if script.get("_voice_id"):
        VOICE_ID = os.environ.get("VOICE_ID") or script["_voice_id"]

    print("=== Step 2: Voice Generation ===")
    print(f"Run dir: {RUN_DIR}")
    print(f"Voice: {VOICE_ID} ({MODEL_ID})")
    print(f"Settings: {VOICE_SETTINGS}")

    # Check quota
    remaining = get_character_count()

    chapters = script["chapters"]
    total_chars = sum(len(ch["voiceover"]) for ch in chapters)
    print(f"Total chars to generate: {total_chars}")

    if remaining is not None and remaining < total_chars:
        print(f"ABORT: Insufficient quota ({remaining} < {total_chars})")
        sys.exit(1)

    os.makedirs(VOICE_DIR, exist_ok=True)
    results = []

    for ch in chapters:
        chapter_id = ch["chapter_id"]
        voiceover = ch["voiceover"]
        out_path = os.path.join(VOICE_DIR, f"ch{chapter_id}.mp3")
        ok = generate_chapter_voice(chapter_id, voiceover, out_path)
        results.append({"chapter_id": chapter_id, "path": out_path, "ok": ok, "chars": len(voiceover)})
        if ok and chapter_id < len(chapters) - 1:
            time.sleep(2)  # brief pause between API calls

    # Summary
    success = sum(1 for r in results if r["ok"])
    total_cost_usd = (total_chars / 1000) * 0.11
    print(f"\n=== Voice Done: {success}/{len(chapters)} chapters ===")
    print(f"Est. cost: ${total_cost_usd:.2f} USD")

    # Write voice manifest
    manifest_path = os.path.join(VOICE_DIR, "manifest.json")
    with open(manifest_path, "w") as f:
        json.dump({"chapters": results, "total_chars": total_chars, "est_cost_usd": round(total_cost_usd, 4)}, f, indent=2)
    print(f"Manifest: {manifest_path}")

    if success < len(chapters):
        sys.exit(1)

if __name__ == "__main__":
    main()
