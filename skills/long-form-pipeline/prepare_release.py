#!/usr/bin/env python3
"""Stage a rendered .mp4 (+ thumb) for upload — pushes to a GitHub Release asset
so the file is reachable from any host via a public URL.

This solves the cross-container filesystem problem:
  - Cloud Routine sandbox has the .mp4 (sandbox-local FS)
  - camoufox-stealth MCP server runs on mcphub.nocode18.com (different host)
  - GitHub Release = bridge, 2GB asset limit, free, no expiry

After this script runs, the Claude agent calls (in this order):
  1. camoufox-stealth_download(url=<asset_url>)  →  pulls .mp4 to MCP server FS
  2. camoufox-stealth_navigate("https://studio.youtube.com/")
  3. camoufox-stealth_upload(selector="input[type='file']", file_path=<mcp_local_path>)
  4. fill metadata / schedule
  5. (optional) cleanup release asset after publish confirmed

Usage:
    python3 prepare_release.py <runs/<topic>>

Outputs:
    runs/<topic>/upload_manifest.json — { asset_url, thumb_url, title, description, tags, schedule_at }
"""
import json
import os
import subprocess
import sys
from pathlib import Path


def gh_release_upload(repo: str, tag: str, asset_path: Path) -> str:
    """Upload an asset to a GitHub Release. Creates the release if missing.
    Returns the public download URL of the asset.
    """
    # Create release if it doesn't exist
    check = subprocess.run(
        ["gh", "release", "view", tag, "--repo", repo, "--json", "tagName"],
        capture_output=True, text=True
    )
    if check.returncode != 0:
        subprocess.check_call([
            "gh", "release", "create", tag,
            "--repo", repo,
            "--title", f"Voidline asset {tag}",
            "--notes", "Auto-generated asset for upload pipeline. Safe to delete after publish.",
            "--draft=false", "--prerelease=false",
        ])

    # Upload the asset (--clobber so re-runs are idempotent)
    subprocess.check_call([
        "gh", "release", "upload", tag, str(asset_path),
        "--repo", repo, "--clobber",
    ])

    # Get the asset URL
    out = subprocess.check_output([
        "gh", "release", "view", tag, "--repo", repo, "--json", "assets"
    ], text=True)
    assets = json.loads(out)["assets"]
    for a in assets:
        if a["name"] == asset_path.name:
            return a["url"]
    raise RuntimeError(f"Asset {asset_path.name} not found in release {tag} after upload")


def load_metadata(run_dir: Path) -> dict:
    """Load title/description/tags/schedule from the run's script.json + NEXT_VIDEOS.md."""
    script = json.loads((run_dir / "script.json").read_text())
    meta = {
        "title": script.get("title") or script.get("hook"),
        "description": script.get("description") or "",
        "tags": script.get("tags") or [],
        "schedule_at": script.get("publish_at"),
    }
    return meta


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: prepare_release.py <runs/<topic>>")

    run_dir = Path(sys.argv[1]).resolve()
    if not run_dir.exists():
        sys.exit(f"[release] {run_dir} not found")

    # Locate the rendered .mp4 — try common paths
    candidates = [
        run_dir / "render" / "final.mp4",
        run_dir / "render" / "voidline.mp4",
        *list((run_dir / "render").glob("*.mp4")) if (run_dir / "render").exists() else [],
    ]
    video = next((p for p in candidates if p.exists()), None)
    if not video:
        sys.exit(f"[release] no .mp4 found in {run_dir}/render/ — candidates checked: {candidates}")

    thumb_candidates = [
        run_dir / "thumb" / "thumbnail.jpg",
        *list((run_dir / "thumb").glob("*.jpg")) if (run_dir / "thumb").exists() else [],
    ]
    thumb = next((p for p in thumb_candidates if p.exists()), None)

    # GitHub repo + tag
    repo = os.environ.get("GITHUB_REPOSITORY") or "follox42/voidline-automation"
    tag = f"upload-{run_dir.name}"

    print(f"[release] uploading {video.name} ({video.stat().st_size // (1024*1024)} MB) to {repo} release '{tag}'...")
    video_url = gh_release_upload(repo, tag, video)
    print(f"[release] asset URL: {video_url}")

    thumb_url = None
    if thumb:
        print(f"[release] uploading thumb {thumb.name}...")
        thumb_url = gh_release_upload(repo, tag, thumb)
        print(f"[release] thumb URL: {thumb_url}")

    meta = load_metadata(run_dir)

    manifest = {
        "asset_url": video_url,
        "asset_filename": video.name,
        "thumb_url": thumb_url,
        "thumb_filename": thumb.name if thumb else None,
        "release_tag": tag,
        "repo": repo,
        **meta,
    }

    manifest_path = run_dir / "upload_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))
    print(f"[release] wrote {manifest_path}")
    print()
    print("=== NEXT STEPS for the agent ===")
    print(f"Read {manifest_path}, then call MCP tools in this order:")
    print(f"  1. camoufox-stealth_navigate(url='about:blank', cookie_profile='voidline')")
    print(f"  2. camoufox-stealth_download(url='{video_url}', path='/tmp/voidline_upload.mp4')")
    if thumb_url:
        print(f"  3. camoufox-stealth_download(url='{thumb_url}', path='/tmp/voidline_thumb.jpg')")
    print(f"  4. camoufox-stealth_navigate(url='https://studio.youtube.com/')")
    print(f"  5. Click upload, then camoufox-stealth_upload(selector=\"input[type='file']\", file_path='/tmp/voidline_upload.mp4')")
    print(f"  6. Fill title='{meta['title']}', description, tags, set thumb, schedule={meta.get('schedule_at')}")
    print(f"  7. After publish confirmed, optionally: gh release delete {tag} --repo {repo} --yes")


if __name__ == "__main__":
    main()
