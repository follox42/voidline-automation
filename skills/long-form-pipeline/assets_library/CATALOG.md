# Voidline Asset Library — CATALOG

Full inventory of free / CC0 / royalty-free sources for documentary YouTube pipeline. Every source has 3 access methods (nav / api / bulk download) where available. The agent uses `asset_manager.py` to search + download + rename + organize, and `asset_scorer.py` to tag what worked.

---

## 🎵 MUSIC — background beds, docu underscore, tension, ambient

### CC0 / free tier with API

| Source | Nav | API | Bulk | License | Style match | Notes |
|---|---|---|---|---|---|---|
| **Freesound.org (music tag)** | https://freesound.org/browse/tags/music/ | ✅ v2 REST OAuth2 | via API | CC0 filter available | ✅ ambient / drone | 60 req/min authed, filters BPM/duration/tags |
| **Pixabay Music** | https://pixabay.com/music/ | ✅ REST /music | via API | CC0-equivalent | ⚠️ commercial-friendly but generic | Free API key, unlimited |
| **YouTube Audio Library** | https://studio.youtube.com/channel/UC/music | ❌ | via yt-dlp on library page | Free with monetization | ⚠️ some ambient OK | scrape via cookie'd browser |
| **Free Music Archive** | https://freemusicarchive.org/ | ✅ v1 API | via API | CC-BY mostly | ⚠️ variable | requires attribution in description |
| **Jamendo** | https://www.jamendo.com/ | ✅ OAuth2 | via API | CC-BY / commercial paid | ⚠️ | Pro tier needed for commercial |

### CC-BY / free with attribution (manual pick)

| Source | Nav | Direct download | Style match |
|---|---|---|---|
| **Purple Planet** | https://www.purple-planet.com/ | wget per track | 🔥 **excellent dark ambient / cinematic docu** — highly recommended |
| **Chosic** | https://www.chosic.com/free-music/ | direct MP3 | ✅ cinematic + ambient sections |
| **Bensound** | https://www.bensound.com/ | direct MP3 | ⚠️ pop mostly, few docu |
| **Kevin MacLeod (incompetech)** | https://incompetech.com/ | direct MP3 (browse then wget) | ⚠️ dated 2026 |
| **Silverman Sound Studios** | https://www.silvermansound.com/ | free .zip packs | ⚠️ vlog mostly |

### AI-generated (paid, prompt-driven)

| Source | Nav | API | Cost | Notes |
|---|---|---|---|---|
| **Suno v4** | https://suno.com/ | ✅ REST | $10/mo Pro | prompt-driven custom beds/stings |
| **Stable Audio 2** | https://stableaudio.com/ | ✅ REST | $0.01/sec | ambient beds prompt |
| **Udio** | https://www.udio.com/ | ⚠️ waitlist | $10-30/mo | music generation |
| **MusicGen (Meta via Replicate)** | https://replicate.com/meta/musicgen | ✅ Replicate API | $0.002-0.01/gen | Apache-2.0 model, license clarity murky |

---

## 🔊 SFX — whoosh, sting, glitch, foley, transitions, atmospheres

### CC0 with API (top choice)

| Source | Nav | API | Bulk | License | Volume |
|---|---|---|---|---|---|
| **Freesound.org (CC0 filter)** | https://freesound.org/search/?q=&f=license%3A%22Creative+Commons+0%22 | ✅ v2 REST OAuth2 | via API | CC0 | 🔥 **100k+ CC0 SFX** |
| **Pixabay SFX** | https://pixabay.com/sound-effects/ | ✅ REST /sfx | via API | CC0-equivalent | ~15k sounds |

### Free with account (manual, but big catalogs)

| Source | Nav | Direct | License |
|---|---|---|---|
| **Zapsplat** | https://www.zapsplat.com/ | manual (login) | Free personal + $ commercial | 
| **99Sounds** | https://99sounds.org/ | free .zip packs | CC0 |
| **Mixkit SFX** | https://mixkit.co/free-sound-effects/ | direct MP3 | Free commercial | curated qual |

### AI-generated SFX

| Source | Nav | API | Cost | Notes |
|---|---|---|---|---|
| **ElevenLabs Sound Effects** | https://elevenlabs.io/sound-effects | ✅ text-to-SFX API | Creator tier (déjà payé) | 🔥 **on l'a déjà** — whooshes, stings, glitches par prompt |

### Archive scrape (specific reference)

| Source | Nav | Access |
|---|---|---|
| **BBC Sound Effects** | https://sound-effects.bbcrewind.co.uk/ | manual, personal use ONLY (not YT-safe) |
| **Internet Archive Audio** | https://archive.org/details/audio | wget direct | often public domain |

---

## 🎥 VIDEO — stock B-roll, ambience, period-look

### CC0 with API

| Source | Nav | API | Volume | Notes |
|---|---|---|---|---|
| **Pexels Video** | https://www.pexels.com/videos/ | ✅ REST | 🔥 excellent 4K library | free API key, unlimited |
| **Pixabay Video** | https://pixabay.com/videos/ | ✅ REST | good 4K | free API key |
| **Coverr** | https://coverr.co/ | ✅ REST | moyen | free commercial |

### CC0 no API but curated (worth manual)

| Source | Nav | License | Notes |
|---|---|---|---|
| **Mixkit Video** | https://mixkit.co/free-stock-video/ | Free commercial | curated qualité YT |
| **Videezy** | https://www.videezy.com/ | Free with attribution | variable |
| **Videvo** | https://www.videvo.net/ | Free (some paid) | mixed |

### AI-generated video (i2v, for period B-roll)

| Source | Nav | API | Cost | Verdict |
|---|---|---|---|---|
| **Google Veo 3.1 Fast** | https://labs.google/flow | ✅ via Gemini API | **$0.05/sec** | 🥇 best archival + physics |
| **Kling 3.0** | https://klingai.com/ | ✅ REST + fal.ai | $0.15-0.20/sec | 🥈 best i2v from stills |
| **MiniMax Hailuo 02 Pro** | https://hailuoai.com/ | ✅ REST | **$0.047/sec** | 💰 cheapest credible |
| **Runway Gen-4.5** | https://runwayml.com/ | ✅ REST | $0.12/sec | ⚠️ clean cinematic not archival |
| **fal.ai unified** | https://fal.ai/ | ✅ REST **[unifies Veo/Kling/Hailuo/Wan]** | pass-through | 🎯 **single integration point** |
| **Sora 2** | ❌ | ⛔ | dying Sept 24 2026 | **DO NOT USE** |
| **Wan 2.2 (open-source)** | https://github.com/Wan-Video | self-host | GPU only | 24GB VRAM, Apache-2.0 |

---

## 🖼️ STILLS — historical, archive, period photos

| Source | Nav | API | Bulk | License |
|---|---|---|---|---|
| **Wikimedia Commons** | https://commons.wikimedia.org/ | ✅ MediaWiki API | ✅ Category tarball via `wget` | Public domain + CC | ✅ (already integrated) |
| **Library of Congress** | https://www.loc.gov/photos/ | ✅ /photos/?fo=json | ✅ URL patterns | Public domain (US gov) | 🔥 huge archive |
| **NASA imagery** | https://images.nasa.gov/ | ✅ REST | ✅ | Public domain | space/earth |
| **Smithsonian Open Access** | https://www.si.edu/openaccess | ✅ Edan API | ✅ | CC0 | 4.4M objects |
| **Rijksmuseum** | https://www.rijksmuseum.nl/ | ✅ REST | ✅ | CC0 | European art/portraits |
| **Metropolitan Museum** | https://www.metmuseum.org/art/collection | ✅ REST v1 | ✅ | CC0 (400k+ works) | historical portraits |
| **British Library Flickr** | https://www.flickr.com/photos/britishlibrary/ | via Flickr API | via API | Public domain | ~1M scanned pages/images |
| **Old Book Illustrations** | https://www.oldbookillustrations.com/ | ❌ | scrape | Public domain | Victorian etchings |
| **Public Domain Review** | https://publicdomainreview.org/ | ❌ | scrape | Public domain | curated collections |
| **Google Arts & Culture** | https://artsandculture.google.com/ | ⚠️ limited API | ❌ | mostly CC | museum partnerships |

### AI image gen (period)

| Source | Nav | API | Cost | Notes |
|---|---|---|---|---|
| **Flow (Nano Banana 2)** | https://labs.google/flow | ⚠️ browser only | Free (Google acct) | ⚠️ UI cassée 06-13 → 07-01 |
| **DALL-E 3 (OpenAI)** | via API | ✅ REST | $0.04/image std | fallback |
| **Stable Diffusion 3.5 / FLUX** | HuggingFace / Replicate | ✅ REST | $0.003-0.03/image | period aesthetic strong |
| **Midjourney** | https://midjourney.com/ | ⚠️ Discord only | $10/mo | manual, best quality visuel |

---

## ✨ OVERLAYS — light leaks, grain, film scratches, VHS

| Source | Nav | Direct | License |
|---|---|---|---|
| **Enchanted Media Free Light Leaks** | https://www.enchanted.media/downloads | ✅ .zip pack direct | Free commercial | 🔥 recommended pour transitions |
| **Cinema Grain (RGrain/CineGrain samples)** | search "free film grain 4k" | manual .mov | Free samples | Kodak Vision3 grain sim |
| **VHS overlay packs** | search "free VHS overlay 4k" | manual | variable | glitch/tape aesthetic |
| **RocketStock free packs** | https://www.rocketstock.com/free-after-effects-templates/ | .zip .mov overlays | Free with account | mostly AE but MOV overlays usable |
| **PremiumBeat blog free downloads** | https://www.premiumbeat.com/blog/category/free-downloads/ | .zip | Free | film + light leaks + transitions |

---

## 🔤 FONTS — documentary typefaces

| Source | Nav | Direct | License |
|---|---|---|---|
| **Google Fonts** | https://fonts.google.com/ | ✅ TTF direct | SIL OFL Open Font | ✅ Anton, Bebas Neue, Oswald, Playfair Display |
| **Font Squirrel** | https://www.fontsquirrel.com/ | ✅ TTF direct | curated free commercial |
| **DaFont (commercial-free filter)** | https://www.dafont.com/ | direct | variable — filter by "100% free" |
| **Fontshare** | https://www.fontshare.com/ | ✅ direct | 100% free commercial | modern typefaces |

**Voidline defaults :** Impact (system) + Anton (fallback) + Playfair Display (chapter cards).

---

## 🎨 LUTS — color grading presets

| Source | Nav | Direct | License |
|---|---|---|---|
| **FreshLUTs.com** | https://freshluts.com/ | .cube direct | free commercial |
| **Ground Control LUTs (free sample)** | https://groundcontrolcolor.com/ | .cube direct | free samples |
| **Rocketstock LUT packs** | https://www.rocketstock.com/free-luts-cinematic-color-presets/ | .cube pack | free with account |
| **Peter McKinnon signature LUTs** | https://petermckinnon.com/collections/luts | mostly paid, some free | ⚠️ vlog-oriented |
| **IWLTBAP LUTs** | https://iwltbap.com/free-luts/ | .cube direct | free commercial |
| **Lattice LUTs by David J Miller** | search "free cinematic LUT cube" | github/gumroad | variable |

**Voidline target LUT :** sepia warmth + cold teal shadows (Kodak Portra base + slight blue-crush). Reproduced in ffmpeg with `colorbalance` + `curves` + `haldclut` if needed.

---

## 🗺️ MAPS — historical cartography + geo data

| Source | Nav | API | License |
|---|---|---|---|
| **OpenStreetMap** | https://www.openstreetmap.org/ | ✅ Overpass API | ODbL free | modern maps |
| **Natural Earth** | https://www.naturalearthdata.com/ | ❌ | ✅ shapefile bulk download | Public domain | 🔥 country/coast/river vectors |
| **David Rumsey Historical Map Collection** | https://www.davidrumsey.com/ | ⚠️ limited | scrape | CC-BY-NC | 3D-scannable historical maps |
| **Library of Congress Maps** | https://www.loc.gov/maps/ | ✅ | ✅ | Public domain | US-focused historical |
| **Mapbox** | https://www.mapbox.com/ | ✅ | 50k free/mo | free tier | modern styled maps |

---

## 🌐 3D ASSETS

| Source | Nav | Direct | License |
|---|---|---|---|
| **Poly Haven** | https://polyhaven.com/ | ✅ REST + direct | CC0 | HDRIs, textures, models |
| **Blender Open Movies** | https://studio.blender.org/films/ | ✅ direct .blend | CC-BY | reference production files |
| **NASA 3D Resources** | https://nasa3d.arc.nasa.gov/ | ✅ direct .obj | Public domain | space/earth/spacecraft |
| **Smithsonian 3D** | https://3d.si.edu/ | ✅ direct .obj/.usdz | CC0 | artifacts, portraits |

---

## Access modes summary

The `asset_manager.py` supports 3 modes per source :

| Mode | When to use | Function |
|---|---|---|
| `api` | Source has documented API + auth | `search_api(source, query, filters)` + `download_api(id)` |
| `nav` | Source is browser-only, no API | `camoufox_scrape(source, query)` — uses stealth session |
| `bulk` | Source has downloadable archive | `bulk_pull(source, url)` — wgets + unzips + tags |

Everything downloaded → renamed → stored in `assets_packs/<category>/<subcategory>/` → indexed in `assets_packs/index.json` with :
- `source`, `original_id`, `license`, `query`, `downloaded_at`
- `duration` (audio/video), `bpm` (music), `dimensions` (image/video)
- `tags` (extracted from source metadata)
- `used_in` = list of run_ids that consumed this asset
- `score` = agent's per-use rating (learned over time)

See `assets_library/README.md` for organization schema + `asset_manager.py` API.
