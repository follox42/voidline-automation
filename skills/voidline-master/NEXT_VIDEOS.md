# Active week — 2026-W28.md

See: weekly_plans/2026-W28.md

---

# Voidline plan — 2026-W28

> Auto-locked on 2026-07-05 14:08 UTC. Locked by Idea Lock routine, 2026-07-05 14:xx UTC.
> Inputs consumed: monthly_intel/2026-07-actions.json (content_gaps, HIGHEST priority) →
> viewer_feedback/2026-W27.json (BLOCKED this week — treated as unknown, not "no requests",
> per its own blocker_note; fell back to backlog per that note) → weekly_actions/2026-W27.md
> (BLOCKED — no CTR/retention deltas, nothing auto-appliable) → KNOWN_GOOD/KNOWN_BAD →
> open experiments (test-tagged both long-forms to advance sample size). Niche-radar:
> SKIPPED (0/5 queries) — content_gaps + backlog already covered both long-form slots.

## Long-forms (2)

### LONG-1 — Tuesday 2026-07-07
- topic: The Zodiac Killer — the investigation, not the murders (press/police procedural angle)
- source: monthly_intel/2026-07-actions.json content_gaps[0], priority HIGH — explicit ask on LEMMiNO's Kennedy Assassination video, 3.5k-like comment
- iconic detail: Vallejo PD's prime suspect (Arthur Leigh Allen) was cleared and let go in 1971 over a single fingerprint comparison; the case then sat cold for 49 years until independent amateur codebreakers — not police — cracked the Z340 cipher in December 2020
- hook question (spoken, S-tier forensic-contradiction): "THEY HAD A SUSPECT. ONE FINGERPRINT LET HIM WALK."
- YT title (EXP-TITLE-001 CONTROL arm — iconic_question_year): "The Zodiac Killer Investigation (1969–2020): What Did The Police Miss?"
- target duration: 11-13 min
- sources to fetch: Wikimedia + 5 Veo 3.1 clips (case files / press clippings / evidence-board style AI shots — no murder-scene reenactment, keep to procedural/investigation visuals per content-gap framing)
- thumb prompt: Cinematic hyperreal photograph of a 1970s detective's evidence corkboard, a single yellowed fingerprint card pinned dead-center under a gooseneck lamp, red thread connecting it to a blacked-out photo silhouette, dim precinct office bokeh in the background, sepia color grade with cold teal shadow tones, heavy atmospheric perspective, slight film grain, ultra-wide 16:9 1280x720, photorealistic 4k documentary still, dramatic vignette built into the lighting, fingerprint card sits center-right at mid distance, clean negative space upper-left for text overlay, no text on image, no logos, Fern documentary aesthetic, LEMMiNO color palette, shot on Leica M 35mm, Kodak Portra warmth
- voice: david_documentary (ppLqTilh7rH7fbUVlXsf) — EXP-VOICE-001 CONTROL arm
- test-tags (apply real yt_id once published): EXP-HOOK-001 variant=contradiction_punch · EXP-TITLE-001 control=iconic_question_year · EXP-VOICE-001 control=david_documentary

### LONG-2 — Friday 2026-07-10

> **STATUS 2026-07-11 — PARTIAL, BLOCKED (`runs/LONG-2/PRODUCTION_STATE.md`).** Script + variants +
> curated assets done and committed. Voice BLOCKED: ElevenLabs quota exhausted (892 chars left vs
> 8,854 needed; resets 2026-07-30). Thumb/upload BLOCKED: voidline cookie dead day 13. Fri 07-10
> slot MISSED; `script.json.publish_at` provisionally Tue 2026-07-14 17:00 UTC but realistic
> earliest is post-quota-reset. Fri HOOK / Sat ANSWER Shorts un-producible (no render).

- topic: SS Ourang Medan (1947, Strait of Malacca) — the ghost ship that may never have existed
- source: backlog fallback (viewer_feedback/2026-W27.json BLOCKED this week — its own blocker_note says treat as unknown and fall back to backlog; this topic already ran as a validated discovery Short on 2026-07-05 with a strong hook, same short-then-long-form promotion pattern used for Flannan Isles in W27) — NOT a niche-radar pick, 0 queries used
- iconic detail: Final radio transmission "I die" after every officer and the captain were found dead in the chartroom with no wounds and faces frozen in terror; the ship then explodes and sinks before a tow line can be attached — and no shipping registry has ever listed a vessel by that name
- hook question (spoken, S-tier numbers+contradiction): "EVERY MAN ABOARD DIED SMILING. THE SHIP NEVER EXISTED."
- YT title (EXP-TITLE-001 VARIANT arm — numbers_iconic_contradiction): "28 Men Died Smiling in 1947. The Ship Was a Ghost."
- target duration: 11-13 min
- sources: Wikimedia + 5 Veo 3.1 clips
- thumb prompt: Cinematic hyperreal photograph of a derelict cargo freighter adrift at dusk in the Strait of Malacca, 1947, dead in the water with no visible crew on deck, thick tropical haze rolling low over flat glassy water, single porthole glowing faint amber against a darkening teal sky, sepia color grade with cold teal shadow tones, heavy atmospheric perspective, slight film grain, low contrast highlights, deep crushed shadows, ultra-wide 16:9 1280x720, photorealistic 4k documentary still, dramatic vignette built into the lighting, ship sits center-right at mid distance, clean negative space upper-left for text overlay, no text on image, no logos, Fern documentary aesthetic, LEMMiNO color palette, shot on Leica M 35mm, Kodak Portra warmth, mysterious atmospheric tension
- voice: daniel_authoritative (onwK4e9ZLuTAKqWW03F9) — EXP-VOICE-001 VARIANT arm (2nd data point)
- test-tags (apply real yt_id once published): EXP-HOOK-001 control=question_first_8s · EXP-TITLE-001 variant=numbers_iconic_contradiction · EXP-VOICE-001 variant=daniel_authoritative

> Experiment note: EXP-HOOK-001 / EXP-TITLE-001 / EXP-VOICE-001 each had only 1 video
> tagged (mgdNSwtkrnw). Tagging both of this week's long-forms brings each to 3 videos
> tagged — the min_videos threshold — once published. Do NOT open PASSIVE-TIME-001's
> siblings from monthly_intel (16-18min duration test, arrow-removal CTR test): the
> experiment cap is already oversubscribed (4 pending / cap 3, confirmed via
> `python3 skills/weekly-intel/experiment_tracker.py`, none closeable yet — all created
> within the last 5 days, need 14+ day age). Re-run that tracker next week to see if any
> can close and free up a slot.

## Shorts (7 — 1/day at 12:00 UTC)

| Day | Date | Type | Source | Hook question | Iconic detail |
|---|---|---|---|---|---|
| Mon | 2026-07-06 | discovery | NEW | KEPT IN THE DARK 16 YEARS. THEN HE APPEARED. | Kaspar Hauser, Nuremberg 1828 — a teenager appears in the town square able to say almost nothing but his name, claims a lifetime in a darkened cell; stabbed to death 5 years later, identity never confirmed |
| Tue | 2026-07-07 | HOOK | LONG-1 | THEY HAD A SUSPECT. ONE FINGERPRINT LET HIM WALK. | Zodiac case — fingerprint clearance of Arthur Leigh Allen, 1971 |
| Wed | 2026-07-08 | ANSWER | LONG-1 | WE FOUND THE CODE. NOT THE POLICE. | Z340 cipher solved by amateur codebreakers, December 2020 — 51 years after the letters were sent |
| Thu | 2026-07-09 | discovery | NEW | HE JUMPED WITH THE CASH. NEVER LANDED. | D.B. Cooper, 1971, Pacific Northwest USA — hijacker parachutes from a 727 with $200k, never found, case still open |
| Fri | 2026-07-10 | HOOK | LONG-2 | EVERY MAN ABOARD DIED SMILING. THE SHIP NEVER EXISTED. | SS Ourang Medan distress call + mass deaths, 1947 |
| Sat | 2026-07-11 | ANSWER | LONG-2 | NO REGISTRY. NO WRECK. NO CREW LIST. EVER. | Ourang Medan's total absence from any shipping record — the leading theory it was a smuggling ship carrying undeclared cargo that gassed its own crew |
| Sun | 2026-07-12 | discovery | NEW | 3 KIDS WALKED TO THE BEACH. ONE CAME BACK. | The Beaumont Children, Adelaide Australia 1966 — 3 siblings vanish from a beach in broad daylight, Australia's most infamous cold case |

Decade/region check: Kaspar Hauser (1828, Germany/Europe) · D.B. Cooper (1971, USA/North America)
· Beaumont Children (1966, Australia/Oceania) — three different decades, three different regions, no clustering.

## Community-tab schedule

- Mon 18:00 UTC — behind-scenes single image (LONG-1 thumb tease)
- Tue 18:00 UTC — long-form drop card (Zodiac)
- Wed 18:00 UTC — theory poll on LONG-1 ("Did police already have him?")
- Thu 18:00 UTC — viewer theory roundup + iconic-detail crop — per monthly_intel content_gaps[1]
  (priority MEDIUM): surface amateur theories / cultural context viewers volunteer unprompted in
  comments, a format pattern observed on 4/4 sampled MrBallen videos that MrBallen itself never
  acts on. NOTE: community comment mining was BLOCKED this week (camoufox-stealth/mcphub down,
  see weekly_actions/2026-W27.md) so there is no live comment pool to pull from yet — community-
  manager routine should pull fresh comments off LONG-1 (published Tue) before Thursday, or defer
  this post format to W29 if none have accumulated by then.
- Fri 18:00 UTC — long-form drop card (Ourang Medan)
- Sat 18:00 UTC — tomorrow tease for SUN short
- Sun 18:00 UTC — reader pick of the week

## Validation gates

Before this plan locks (agent action):
- [x] All placeholder fields filled (topics, iconic details, hook questions, thumb prompts, shorts table)
- [x] Hook questions pass S-tier check (contradiction / forensic-detail / curiosity-gap patterns per
      youtube-virality-expert/sub-skills/hook.md; no pure narrative opens, no date-dumps, no
      "today we're going to talk about" per KNOWN_BAD.md)
- [x] Topics not duplicates of last 3 published long-forms (Tunguska v3, Roanoke v4, Flannan Isles v5)
- [x] 3 discovery Shorts each have a different decade/region (1828 Germany, 1971 USA, 1966 Australia)

When all checks pass, agent runs:
  python3 skills/idea-forge/idea_lock_runner.py --lock
