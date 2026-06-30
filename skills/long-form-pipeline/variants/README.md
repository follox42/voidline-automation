# Variants — A/B testing framework

Every production variable that can affect retention/CTR has a `variants/<dimension>/<variant_id>.json` library here. The production routine picks one variant per dimension at run time, tags it in `runs/<id>/variants_used.json`, and Weekly Intel + experiment_tracker measure which variant wins.

## Dimensions covered

| Dimension | What it controls | Library location |
|---|---|---|
| **titles** | The YT video title — biggest single CTR driver | `variants/titles/*.json` |
| **voices** | ElevenLabs voice_id + model + settings | `variants/voices/*.json` |
| **thumb_prompts** | Flow/Wikimedia thumbnail prompt template | `variants/thumb_prompts/*.json` |
| **hooks** | Cold-open chapter structure (45-60s) | `variants/hooks/*.json` |
| **caption_styles** | ASS subtitle animation styling | `../caption_styles/*.json` (existed before) |

## How the picker works (`pick_variant.py`)

```
For each dimension D :
  1. Read experiments/*.json for open experiments tagged `dimension == D`.
     If found → use its `variant_under_test` value.
  2. Else read KNOWN_GOOD.md for `default_<D>` field.
     If found → use it.
  3. Else fallback to the dimension's "_default" variant
     (each dimension MUST have a variant with `default: true` in its JSON).
```

Usage from the routine pipeline :

```python
from pick_variant import pick
title_variant = pick("titles", run_id="v4-roanoke")    # returns path to chosen JSON
voice_variant = pick("voices", run_id="v4-roanoke")
thumb_variant = pick("thumb_prompts", run_id="v4-roanoke")
hook_variant  = pick("hooks", run_id="v4-roanoke")
```

The picker writes the choice to `runs/<id>/variants_used.json` automatically.

## Schema by dimension

### titles
```json
{
  "_id": "iconic_question_year",
  "_description": "Question hook + (year) + iconic detail. The Fern/LEMMiNO classic.",
  "_default": false,
  "_category": "voidline-native",
  "template": "{question}? ({year}) — {iconic_detail}",
  "example": "What Did CROATOAN Mean? (1587) — The Lost Colony of Roanoke",
  "max_chars": 70,
  "style_notes": "Question must be answerable in the video. Iconic detail must be the unforgettable phrase."
}
```

### voices
```json
{
  "_id": "david_documentary",
  "_description": "Brian-adjacent UK documentary baritone, calmer than v1",
  "_default": true,
  "_category": "elevenlabs-premium",
  "voice_id": "ppLqTilh7rH7fbUVlXsf",
  "name": "David Documentary",
  "model": "eleven_multilingual_v2",
  "stability": 0.5,
  "similarity_boost": 0.85,
  "style": 0.25,
  "tier_required": "creator"
}
```

### thumb_prompts
```json
{
  "_id": "cinematic_post_iconic_detail",
  "_description": "Single weathered iconic detail with gold-hour side light, Fern aesthetic",
  "_default": true,
  "prompt_template": "Cinematic hyperreal photograph of {iconic_detail}, {year_period}, soft diffused golden hour side-light, sepia + cold teal grade, deep crushed shadows, Fern documentary aesthetic, LEMMiNO color palette, shot on Leica M 35mm, Kodak Portra warmth, 16:9 1280x720 ultra-wide, clean negative space upper-left for text overlay, no text in image, no logos",
  "headline_pattern": "{date} | {iconic_word}",
  "headline_color": "#E0B854",
  "arrow_color": "#D9343F"
}
```

### hooks
```json
{
  "_id": "iconic_question_first_15s",
  "_description": "Question opens at 0:00 (≤8 words). Then 15-30s of contextual setup. ch5 reveals the answer.",
  "_default": true,
  "structure": [
    {"t": "0:00", "beat": "Iconic question, ≤8 words, voice-over only"},
    {"t": "0:03", "beat": "Cold open imagery (no narration), 5s"},
    {"t": "0:08", "beat": "Restate question with context"},
    {"t": "0:15", "beat": "Set stakes: numbers + date + place"},
    {"t": "0:45", "beat": "Transition to ch1 (setup chapter)"}
  ],
  "duration_target_s": 60,
  "voiceover_chars": 200
}
```

## Adding a new variant

1. Create the JSON in the right dimension folder.
2. Fill all required fields per schema above (clone an existing one).
3. Tag with `_category` and `_default: false` (only ONE variant per dimension is default).
4. Optionally open an experiment :

```python
python3 skills/voidline-manager/experiment_tracker.py open EXP-TITLE-005 \
  '{"hypothesis":"variant <id> beats baseline on impression_ctr",
    "dimension":"titles",
    "variant_under_test":"<id>",
    "control":"iconic_question_year",
    "metric":"impression_ctr_pct",
    "min_videos":3,
    "min_impressions":500}'
```

Next production routine picks `<id>` for its run.

## Promotion / demotion (autonomous via Weekly Intel)

After 3+ videos at variant + 500+ impressions :
- variant beats control by ≥10% on the metric → **PROMOTE** : added to KNOWN_GOOD.md as new default
- variant loses by ≥10% → **DEMOTE** : added to KNOWN_BAD.md, never auto-picked again
- inconclusive → keep experiment open

This is the **closed learning loop**. The system converges on the best variant per dimension over 8-12 weeks, autonomously.

## Niche-intel coupling

The monthly niche-intel scan checks LEMMiNO / Fern / MrBallen / RealLifeLore for patterns we haven't tried. If 2+ of them use a title structure we don't have → it proposes a new variant JSON via the `experiments_to_open` field, picker uses it next routine, weekly-intel measures the result.

So the variant LIBRARY grows automatically too — not just the choice between existing variants.
