# Caption Styles — autonomous experiment library

Each `*.json` here is a complete style spec for `generate_captions.py`. Styles are picked by Production routines based on `KNOWN_GOOD.md` + open `experiments/`.

## How the learning loop works

1. **Default** = `voidline_core.json` (the safest baseline, on-brand).
2. **Production routine picks a style:**
   - Reads `KNOWN_GOOD.md` → if a style is promoted there, use it.
   - Reads `experiments/*.json` open → if a caption experiment is open, may pick the variant being tested.
   - Else → fallback `voidline_core.json`.
3. **Tag** the chosen style in `runs/<run_id>/caption_style.json` (auto-written by `generate_captions.py`).
4. **Weekly Intel** (Sun 10:00 UTC) reads tags + analytics → updates experiments:
   - 3+ videos with same style + ≥10% CTR/retention beat baseline → promote to `KNOWN_GOOD.md`
   - 3+ videos + ≥10% under baseline → demote to `KNOWN_BAD.md`
5. **Monthly Niche Intel** scans LEMMiNO/Fern/MrBallen captions. If a pattern we don't have → propose new style JSON via `experiments_to_open`.

## Style parameters (full surface)

| Field | Type | Description |
|---|---|---|
| `font_name` | string | Any TTF/OTF in `/usr/share/fonts/` (Impact, Liberation Sans, etc.) |
| `font_size` | int | Pixel size at 1080p reference |
| `font_color` | hex `#RRGGBB` | Primary word color (already-shown words) |
| `highlight_color` | hex | Active word color (the word currently being spoken) |
| `outline_color` | hex | Stroke around glyphs |
| `outline_width` | int | Stroke px |
| `shadow_color` | hex | Drop shadow (can be brand red `#D9343F` for accent) |
| `shadow_offset` | int | Shadow distance in px |
| `bold` | bool | Bold style enforced |
| `alignment` | int (1-9) | ASS numpad position: 2=bottom-center, 5=middle-center, 8=top-center |
| `margin_v` | int | Vertical margin (ignored when alignment=5) |
| `max_chars_per_line` | int | Auto-wrap threshold |
| `max_words_per_line` | int | Max words shown together |
| `pop_scale_pct` | int (100-150) | Pop-in scale of active word (100=no pop) |
| `pop_duration_ms` | int | Pop animation duration |
| `fade_in_ms` | int | Fade-in (0 = instant) |
| `hold_after_last_word_ms` | int | How long the full line stays after last word |

## Existing styles

| Style | Category | Risk | When to use |
|---|---|---|---|
| `voidline_core.json` | voidline-native | low | DEFAULT — baseline for all experiments |
| `voidline_bold.json` | voidline-native | low | Long-form ch5 reveal + Short HOOK cards |
| `lemmino_subtle.json` | competitor-mimic | low | A/B vs core to test minimalism |
| `fern_punchy.json` | competitor-mimic | medium | HOOK Shorts where iconic term recall matters |
| `tiktok_yellow.json` | trendy | medium | A/B only — breaks Fern grade, test if niche shifts |

## Adding a new style

1. Create `caption_styles/<name>.json` with all fields above (clone voidline_core then tweak).
2. Add `_description` + `_metadata` (category + risk + use_when) for future routines to read.
3. Optionally open an experiment via `experiment_tracker.py open EXP-CAP-<id>` with:
   ```json
   {
     "hypothesis": "style <name> beats voidline_core on retention",
     "test_assets": [],
     "metric": "retention_at_60s_pct",
     "result_30d": null
   }
   ```
4. Production routine will pick `<name>` for next batch of videos.

## Capability vs CapCut

This pipeline covers ~95% of CapCut's caption animation surface (per-word reveal, highlight, pop, fade, shadow, blur, position anim, color cycles). The 5% missing = true 3D perspective + particle systems, not relevant for documentary content.

The KEY advantage of doing it this way: **every style choice is a measurable experiment**. CapCut gives you 200 templates but no learning loop. Here, after 8-12 weeks of run, we'll have empirical data on which style of caption converts BEST for OUR audience on OUR niche. Compounds.
