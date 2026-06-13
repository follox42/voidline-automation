# Voidline — Thumbnail AI Prompt Template

> **Goal**: generate a single cinematic image per video that maximises YouTube
> CTR for a historical-mystery long-form documentary channel. Style ref:
> **Fern / LEMMiNO / MrBallen** — hyperreal photographic, atmospheric,
> period-accurate.

The image is **only the base**. Text headline + date + red arrow are added
later in PIL via `shorts/make_fern_thumb.py`. The AI must therefore leave a
clean visual space at **TOP-LEFT** (~40% of frame width, ~25% of frame height)
for the overlay, and the focal subject should sit **center-right** or
**bottom-center** of the frame.

---

## 🟡 Master prompt (template)

```
Cinematic hyperreal photograph of {SCENE_SUBJECT}, {PERIOD_CONTEXT}, soft
diffused {LIGHT_DIRECTION} light through {ATMOSPHERIC_ELEMENT} (fog / dust /
smoke / falling snow), pale sepia + cold teal shadow color grade, heavy
atmospheric perspective, slight film grain, low contrast highlights, deep
crushed shadows, ultra-wide composition 16:9 1280x720, photorealistic 4k,
documentary still, dramatic vignette built into the lighting, single focal
subject in {SUBJECT_PLACEMENT}, clean negative space upper-left for text
overlay, no text on image, no logos, Fern documentary aesthetic, LEMMiNO
color palette, shot on Leica M with 35mm lens, slight Kodak Portra warmth.
```

### Variables to fill

| Variable | Description | Examples |
|---|---|---|
| `SCENE_SUBJECT` | The single iconic visual object of the mystery | "an abandoned brigantine ship adrift in calm North Atlantic at dusk" / "a torn canvas tent in fresh snow with frozen footprints leading away" / "a vast flattened forest radiating in butterfly-wing pattern from a single point" |
| `PERIOD_CONTEXT` | Year + setting cue | "December 1872 Atlantic Ocean" / "February 1959 Ural Mountains at dawn" / "June 1908 Siberian taiga" |
| `LIGHT_DIRECTION` | Where light comes from | "golden hour side-light from low west" / "blue hour back-light through ice fog" / "dawn god rays through dust" |
| `ATMOSPHERIC_ELEMENT` | The medium between camera and subject | "ocean mist" / "blizzard particulate" / "smoke + ash + low fog" |
| `SUBJECT_PLACEMENT` | Where the focal subject sits in frame | "center-right at depth" / "bottom-center foreground" / "mid-frame slightly right of center" |

---

## 🔥 The viral hook angle

Each Voidline doc maps to ONE iconic forensic question. The thumb image must
**make you think the answer is in the image**. Pick the *single most uncanny
detail* of the case and put it in the focal point. The PIL pass then adds a
red arrow pointing AT IT.

| Doc | Iconic detail (= where arrow points) | Headline (added in PIL) | Date |
|---|---|---|---|
| **v1 Mary Celeste 1872** | empty captain wheel / breakfast bowl still steaming on the galley table | `STILL WARM` | `1872` |
| **v2 Dyatlov 1959** | the tent slit cut from inside / barefoot prints in snow | `CUT FROM INSIDE` | `1959` |
| **v3 Tunguska 1908** | the flattened forest with NO impact crater at the center | `NO CRATER` | `1908` |
| **future: Roanoke 1590** | the carved word "CROATOAN" on a tree post / abandoned palisade gate ajar | `JUST GONE` | `1590` |
| **future: Flannan Isles 1900** | half-eaten meal on table in lighthouse + open door to storm | `MEAL HALF EATEN` | `1900` |
| **future: SS Ourang Medok 1947** | freighter on calm sea with one corpse visible through smoke | `SMILES FROZEN` | `1947` |

---

## 📐 Post-processing in PIL (`make_fern_thumb.py`)

Once the AI image is generated and saved to
`runs/<run-id>/assets/thumbnails/raw/ai_base.jpg`, the PIL pipeline adds:

1. **Headline** Impact `#E0B854` (warm gold, not pure #FFD700), 130–150pt,
   9px black stroke, positioned `x=40, y=22` (top-left)
2. **Date** Impact `#FFFFFF`, 80–95pt, 5px black stroke, directly below
   headline with `gap=4`
3. **Red arrow** polygon `#D9343F` with 6px black border, tip-pointing at the
   iconic detail, angle typically `-30°` to `-50°` from horizontal, shaft 50px
   wide, head 130x110px

Config example: see `shorts/make_fern_thumb.py` + recent `*_fern.json` configs.

---

## ✅ A/B test recipe per video

Generate **3 variants** by varying:
- **A — Mystery framing**: `{SCENE_SUBJECT}` is *only* the iconic detail (no
  humans). Wide composition.
- **B — Human framing**: `{SCENE_SUBJECT}` includes a single anonymous human
  silhouette (no face) at the iconic detail.
- **C — Scale framing**: `{SCENE_SUBJECT}` shows the iconic detail at extreme
  scale (drone-shot wide / macro detail).

Ship **A** as default. After 24h, swap to whichever has highest CTR per
Studio analytics (target: 6%+ for documentaries, anything <3% is failing).

---

## 🚫 What NOT to do (lessons from failed iterations)

1. **Don't crush brightness** to 0.55-0.65 — kills CTR. The v1 winner uses
   0.90-0.95 brightness, NOT a dark sepia.
2. **Don't put text in the center** — covers the focal subject. Text always
   top-left or top-center, max 30% of frame area.
3. **Don't use real grainy archive photos** as the base — they read "boring
   history class". Only AI-cinematic or modern-shot stills work for YT CTR.
4. **Don't add vignette in PIL** — the AI image already has cinematic
   light/shadow gradient built in. Adding more = looks like an Instagram
   filter from 2014.
5. **Don't use pure #FFD700** for the gold — too bright, looks like spam.
   Use `#E0B854` warm gold to match the brand.

---

## API options (in priority order)

1. **Imagen 3 / 4** via Gemini API — fastest, best photographic realism
2. **Midjourney v6** — most cinematic but no API, manual workflow
3. **FLUX.1 [pro]** via Replicate / fal.ai — solid alternative
4. **DALL·E 3** via OpenAI — last resort, weaker photoreal

Setup: any of these requires API key in `~/.config/voidline/api_keys.env`.
