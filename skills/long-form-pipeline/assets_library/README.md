# Voidline Asset Library — Manager + Organization

The routine agent uses the assets_packs/ library to compose motion + audio in each production. This doc teaches the agent WHERE things go, HOW to name them, and HOW to learn what works.

## Structure canonique

```
assets_packs/
├── index.json                          # master catalog (one entry per file)
├── PROVENANCE.md                       # source + license per pack (auto-appended)
├── music/
│   ├── ambient/                        # slow evolving pads (0-70 BPM)
│   ├── tension/                        # rising suspense (60-90 BPM)
│   ├── dark/                           # minor-key underscore
│   ├── synth/                          # electronic pulses (LEMMiNO style)
│   └── transitions/                    # 2-8s musical bridges
├── sfx/
│   ├── whoosh/                         # transition whooshes
│   ├── sting/                          # reveal impacts, cinematic hits
│   ├── glitch/                         # digital distortion cuts
│   ├── foley/                          # ambient environmental (wind, water, paper)
│   ├── riser/                          # tension build-ups (3-10s)
│   └── drone/                          # sustained ambient beds
├── video/
│   ├── ambience/                       # static-cam nature/atmosphere
│   ├── texture/                        # abstract patterns, macro shots
│   ├── period/                         # historically-appropriate scenes (AI-gen)
│   └── overlay/                        # semi-transparent clips (fog, dust, particles)
├── stills/
│   ├── historical/                     # period-accurate photos/prints
│   └── archive/                        # docs, maps, ephemera
├── overlays/
│   ├── light_leaks/                    # transitions/color pops (MOV alpha)
│   ├── grain/                          # film grain 4K noise
│   ├── film/                           # scratches, dust, gate weave
│   └── vhs/                            # analog distortion
├── fonts/                              # .ttf/.otf downloaded once
├── luts/                               # .cube color grading presets
└── maps/                               # .geojson / .shp / images
```

## Naming schema (STRICT)

Every downloaded asset is renamed to :

```
<source>_<category>_<style>_<slug>_<originalid>.<ext>
```

Examples :
- `freesound_sfx_whoosh_deep-cinematic_412896.wav`
- `purpleplanet_music_dark_underscore-tension_the-descent.mp3`
- `pexels_video_ambience_ocean-storm-wide_3892178.mp4`
- `wikimedia_stills_historical_roanoke-1590-white_ce02.jpg`

Rules :
1. `<source>` = short slug of provider (freesound, pixabay, purpleplanet, pexels, wikimedia, elevenlabs, veo, kling, suno, ...)
2. `<category>` = matches folder name (music, sfx, video, stills, overlays)
3. `<style>` = subcategory folder (ambient, whoosh, sting, ...)
4. `<slug>` = 2-4 kebab-case keywords describing content
5. `<originalid>` = source ID for de-dup + attribution back-reference
6. Extension lowercase

## index.json schema

Every asset has ONE row :

```json
{
  "id": "freesound_sfx_whoosh_deep-cinematic_412896",
  "path": "assets_packs/sfx/whoosh/freesound_sfx_whoosh_deep-cinematic_412896.wav",
  "source": "freesound",
  "source_url": "https://freesound.org/s/412896/",
  "source_original_id": "412896",
  "license": "CC0",
  "license_ok_for_commercial_yt": true,
  "downloaded_at": "2026-07-01T10:24:00Z",
  "query_that_found_it": "cinematic whoosh deep reverb transition",
  "duration_s": 2.4,
  "bpm": null,
  "dimensions": null,
  "tags": ["whoosh", "cinematic", "deep", "transition", "reverb", "impact"],
  "sha256": "e3b0c44...",
  "size_bytes": 245680,
  "used_in": ["v4-roanoke", "v5-flannan"],
  "scores": [
    {"run_id": "v4-roanoke", "context": "ch3-reveal-transition", "rating": 4, "note": "hit right at the CROATOAN word reveal, high recall"},
    {"run_id": "v5-flannan", "context": "ch2-tension-build", "rating": 2, "note": "too deep for daytime lighthouse ambience"}
  ]
}
```

## The learning loop

### At production (per run) :

1. Routine calls `asset_manager.py search --category sfx/whoosh --context "reveal transition after long build"` 
2. Returns top 5 candidates ranked by :
   - Tag match to context
   - Historical `scores` (higher = surface first)
   - Fresh unused asset gets a diversity boost (avoid overusing same 2 sounds)
3. Routine picks one (or a few for A/B testing between segments)
4. After render, routine calls `asset_manager.py record --id <asset_id> --run-id <run_id> --context "ch3-reveal-transition" --rating 4 --note "..."` — score BEFORE upload, based on how well it fits the timeline
5. After 14d, weekly-intel can also score based on retention curve at that timestamp (did viewers stay at the reveal?)

### Discovery (when library is thin) :

`asset_manager.py explore --category <cat> --query "<what you need>"` :
- Searches Freesound / Pixabay / Pexels APIs in parallel
- Downloads top 10 results
- Auto-tags via source metadata
- Adds to index with `scores: []` empty
- Routine can immediately search + use them

### Rebalancing (bi-weekly) :

`asset_manager.py rebalance` :
- Finds tags with `< 3 assets` and generates auto-queries to fill
- Finds tags with `> 30 assets` and archives lowest-scored to `assets_packs/_archive/`
- Renames outliers if new naming schema is decided

### Provenance auto-tracking :

Every download appends to `assets_packs/PROVENANCE.md` :

```
- 2026-07-01 freesound.org sound #412896 by user_xyz — CC0 — WAV 2.4s cinematic whoosh
- 2026-07-01 pexels.com video #3892178 by Photog Name — Pexels Free Use — MP4 30s ocean storm
```

For CC-BY sources → an auto-generated attribution line goes into video descriptions.

## Access modes

Three ways the agent can pull assets, chosen automatically by source :

### Mode `api`

Sources with documented REST API :
- freesound.org (v2 OAuth2)
- pixabay.com (API key)
- pexels.com (API key)
- elevenlabs.io (SFX endpoint)
- suno.com (v4 tier)
- fal.ai (unified video AI)

Config in `assets_library/api_keys.json` (gitignored) :
```json
{
  "freesound": "your_oauth_token",
  "pixabay": "your_api_key",
  "pexels": "your_api_key",
  "fal_ai": "your_fal_key",
  "suno": "your_key",
  "elevenlabs": "$ELEVENLABS_KEY"
}
```

### Mode `nav`

Sources browser-only (no API) → camoufox stealth :
- Purple Planet, Chosic, Kevin MacLeod (music)
- Zapsplat, Mixkit (SFX)
- Videezy, Videvo (video)
- Enchanted Media (overlays)
- Freshluts, IWLTBAP (LUTs)

The manager uses `camoufox-stealth_navigate` + `camoufox-stealth_download` to grab direct URLs.

### Mode `bulk`

Sources that publish downloadable archives :
- 99Sounds packs (.zip)
- Enchanted Media light leaks (.zip)
- Blender Open Movies (.blend + assets)
- Natural Earth shapefiles

Pulled once via `wget`, extracted to appropriate folder, indexed.

## Discovery playbook by need

| Need | First move | Fallback |
|---|---|---|
| Dark ambient bed for chapter | Purple Planet nav → local search | Freesound API `ambient dark cinematic 60bpm` |
| Whoosh transition | Freesound API `CC0 whoosh transition` | ElevenLabs SFX prompt `deep cinematic whoosh 2s` |
| Reveal sting | ElevenLabs SFX prompt `cinematic impact sting` | Freesound `impact sting cinematic bass` |
| B-roll ambience (storm, water, forest) | Pexels API `<subject>` | Pixabay API |
| Period B-roll (1850s dock, 1580s colony) | Wikimedia + Ken Burns | fal.ai i2v Veo `<Wikimedia still> + prompt` |
| Location map | Natural Earth shapefile → Manim animate | Mapbox styled export |
| Historical portrait | Library of Congress → Rijksmuseum → Met | Wikimedia |
| Light leak transition | Enchanted Media pack | search "free light leak 4K" |
| Film grain overlay | Cinema Grain samples | ffmpeg `noise` filter fallback |

## Learning-by-testing playbook

Every production run :
1. Chooses 6-12 assets from library (music beds + SFX + overlays + optional AI video)
2. Records `scores` per asset for the context it was used in
3. Over time, `search` prioritizes high-scored assets for similar contexts
4. New assets get a "novelty bonus" so library grows in diversity
5. Under-tagged categories trigger auto-search via `explore` mode
6. The library becomes VOIDLINE-SPECIFIC over 8-12 weeks — the agent knows what fits our brand

## What the agent must do at every step

1. **Never dupe** — check SHA256 before adding to index
2. **Always tag** — extract tags from source metadata + augment with context keywords
3. **Always attribute** for CC-BY licenses — append to PROVENANCE.md + description template
4. **Always score** after use — even a quick 1-5 rating with 1-line note
5. **Rebalance monthly** — call `rebalance` command to fill thin categories + archive junk
6. **Only download once** — hits index cache before downloading again for a similar query
