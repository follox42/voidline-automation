# v4 Roanoke — Shorts batch plan

Per new cadence (no burst): **2 Shorts per long-form** (HOOK + ANSWER).

## Schedule

| Short | Type | Publish date | UTC time | Iconic detail | Hook question |
|---|---|---|---|---|---|
| v4_hook | HOOK | 2026-06-22 (long-form ship day) | 12:00 | Empty palisade + dismantled houses | "115 PEOPLE. ONE WORD. CROATOAN." |
| v4_answer | ANSWER | 2026-06-24 (J+2) | 12:00 | Site X + Hatteras digs map | "WE FOUND THEM." |

## Shorts source segments (from long-form script.json)

### v4 HOOK Short (60s)
**Source segment**: long-form ch0 (cold-open hook) 0-45.5s + light intro to ch1 = 0-58s
**Cutter v2 config**:
```json
{
  "source": "render/voidline_v4_roanoke.mp4",
  "start_s": 0,
  "duration_s": 60,
  "out": "shorts/short_v4_hook.mp4",
  "header_text": "ROANOKE · 1587",
  "hook_duration_s": 1.5,
  "outro_duration_s": 4.0,
  "hook_question": "115 PEOPLE.\\NONE WORD.\\NCROATOAN.",
  "outro_question": "WHERE DID\\NTHEY GO?",
  "outro_cta": "COMMENT ↓",
  "mask_until_s": 45,
  "captions": [
    {"start": 0.0, "end": 2.0, "text": "AUGUST 1587"},
    {"start": 2.0, "end": 4.0, "text": "ROANOKE ISLAND"},
    {"start": 4.0, "end": 6.0, "text": "115 ENGLISH\nSETTLERS"},
    {"start": 6.0, "end": 8.5, "text": "MEN. WOMEN.\nCHILDREN."},
    {"start": 8.5, "end": 11.0, "text": "GOVERNOR\nLEAVES FOR\nSUPPLIES"},
    {"start": 11.0, "end": 14.0, "text": "RETURNS\n3 YEARS LATER"},
    {"start": 14.0, "end": 17.5, "text": "COLONY GONE"},
    {"start": 17.5, "end": 20.5, "text": "HOUSES\nDISMANTLED"},
    {"start": 20.5, "end": 23.5, "text": "NO BODIES"},
    {"start": 23.5, "end": 27.0, "text": "NO GRAVES"},
    {"start": 27.0, "end": 30.0, "text": "NO SIGN OF\nSTRUGGLE"},
    {"start": 30.0, "end": 34.0, "text": "ONE WORD"},
    {"start": 34.0, "end": 38.0, "text": "CARVED\nINTO A TREE"},
    {"start": 38.0, "end": 42.0, "text": "C R O A T O A N"},
    {"start": 42.0, "end": 47.0, "text": "WHAT DID IT\nMEAN?"},
    {"start": 47.0, "end": 52.0, "text": "WHO READ THE\nSIGN?"}
  ]
}
```

### v4 ANSWER Short (60s)
**Source segment**: long-form ch5 (the 2020 answer) 600-660s = 60s window
**Cutter v2 config**:
```json
{
  "source": "render/voidline_v4_roanoke.mp4",
  "start_s": 600,
  "duration_s": 60,
  "out": "shorts/short_v4_answer.mp4",
  "header_text": "ROANOKE · 1587",
  "hook_duration_s": 1.5,
  "outro_duration_s": 4.0,
  "hook_question": "WE FOUND\\NTHE LOST\\NCOLONY.",
  "outro_question": "ARE THEIR\\NDESCENDANTS\\NSTILL ALIVE?",
  "outro_cta": "COMMENT ↓",
  "mask_until_s": 0,
  "captions": [
    {"start": 0.0, "end": 2.5, "text": "2009"},
    {"start": 2.5, "end": 5.0, "text": "TWO\nARCHAEOLOGICAL\nDIGS"},
    {"start": 5.0, "end": 8.0, "text": "HATTERAS\nISLAND"},
    {"start": 8.0, "end": 11.0, "text": "(THE\nCROATOAN)"},
    {"start": 11.0, "end": 14.5, "text": "FOUND:"},
    {"start": 14.5, "end": 17.5, "text": "COPPER\nRAPIER HILTS"},
    {"start": 17.5, "end": 20.5, "text": "SLATE WRITING\nTABLETS"},
    {"start": 20.5, "end": 24.0, "text": "ENGLISH\nGUNLOCKS\n1590-1620"},
    {"start": 24.0, "end": 27.0, "text": "SITE X"},
    {"start": 27.0, "end": 30.0, "text": "50 MILES\nINLAND"},
    {"start": 30.0, "end": 33.0, "text": "TILEWORK BY\nANANIAS DARE"},
    {"start": 33.0, "end": 37.0, "text": "THEY SPLIT"},
    {"start": 37.0, "end": 41.0, "text": "INTO 2 GROUPS"},
    {"start": 41.0, "end": 45.0, "text": "JOINED\nTHE LOCALS"},
    {"start": 45.0, "end": 49.0, "text": "VIRGINIA DARE"},
    {"start": 49.0, "end": 52.5, "text": "GREW UP\nSPEAKING\nALGONQUIAN"},
    {"start": 52.5, "end": 55.0, "text": "DESCENDANTS"},
    {"start": 55.0, "end": 56.0, "text": "ALIVE TODAY?"}
  ]
}
```

## Thumb concept (AI Nano Banana 2)

**Prompt** (per VOIDLINE_THUMB_AI_PROMPT.md template):
```
Cinematic hyperreal photograph of a single weathered wooden palisade post with five
deeply carved letters "CROATOAN" visible at center-right, the rest of the post showing
faded grain and lichen patches, August 1590 North Carolina coast at dawn, soft diffused
golden hour side-light through coastal fog, swamp grass and a partial palisade fence in
the deep background, pale sepia color grade with cold teal shadow tones, heavy atmospheric
perspective, slight film grain, low contrast highlights, deep crushed shadows, ultra-wide
16:9 1280x720, photorealistic 4k documentary still, dramatic vignette built into the
lighting, the carved post sits center-right at mid distance, clean negative space
upper-left for text overlay, no text on image, no logos, Fern documentary aesthetic,
LEMMiNO color palette, shot on Leica M 35mm, Kodak Portra warmth, mysterious atmospheric
tension, evocative of a colony's silent goodbye note
```

**Fern PIL overlay**:
- Headline gold `#E0B854` Impact: **"JUST GONE"** (top-left, 145pt, 9px stroke)
- Date white Impact: **"1587"** (below headline, 95pt, 5px stroke)
- Red arrow `#D9343F` pointing at the carved letters (mid-frame right)

## Production workflow

1. ✅ Script (this run) — done
2. ⏳ Voice generation (ElevenLabs David Documentary, ~9500 chars)
3. ⏳ Asset summoning (22 Wikimedia + 3 Nano Banana 2 + 5 Veo 3.1 clips)
4. ⏳ Timeline.json build
5. ⏳ ffmpeg render → `render/voidline_v4_roanoke.mp4`
6. ⏳ Thumb gen (Nano Banana 2) + Fern overlay
7. ⏳ 2 Shorts render via cutter v2
8. ⏳ Upload + schedule (long-form 22 juin 17:00, Shorts 22/24 juin 12:00)

ETA cumulative: ~4-6 hours of focused work.
