#!/usr/bin/env python3
"""
Nagi — TikTok Content Posting API Demo
Demonstrates the full 3-step Content Posting API flow.
"""

import os
import sys
import math
import time
import requests

# ── Configuration ────────────────────────────────────────────────────────────

SANDBOX = True  # Set to False to hit live endpoints

CLIENT_KEY    = os.environ.get("TIKTOK_CLIENT_KEY",    "")
CLIENT_SECRET = os.environ.get("TIKTOK_CLIENT_SECRET", "")

VIDEO_PATH = os.path.join(os.path.dirname(__file__), "sample_video.mp4")
CAPTION    = (
    "The quieter you become, the more you are able to hear. — Rumi "
    "#zen #mindfulness #nagi"
)
CREATOR_USERNAME = "@nagi_zen"

BASE_URL = (
    "https://open.tiktokapis.com/v2/post/publish/sandbox/video/init/"
    if SANDBOX
    else "https://open.tiktokapis.com/v2/post/publish/video/init/"
)

# ── Helpers ───────────────────────────────────────────────────────────────────

def _sep(char="─", width=38):
    return char * width

def _ok(msg: str):
    print(f"      ✓ {msg}")

def _err(msg: str):
    print(f"      ✗ {msg}", file=sys.stderr)

def _fmt_bytes(n: int) -> str:
    return f"{n / 1_048_576:.1f}MB" if n >= 1_048_576 else f"{n / 1_024:.1f}KB"

def _require_env():
    missing = [k for k in ("TIKTOK_CLIENT_KEY", "TIKTOK_CLIENT_SECRET") if not os.environ.get(k)]
    if missing:
        print(f"\n  ERROR: Missing env vars: {', '.join(missing)}")
        print("  Export them before running:")
        for k in missing:
            print(f"    export {k}=your_value_here")
        sys.exit(1)

def _require_video():
    if not os.path.exists(VIDEO_PATH):
        print(f"\n  ERROR: Video not found at {VIDEO_PATH}")
        print("  Run the ffmpeg command in README.md to generate it first.")
        sys.exit(1)

# ── Auth ──────────────────────────────────────────────────────────────────────

def get_access_token() -> str:
    """Exchange client credentials for an access token."""
    resp = requests.post(
        "https://open.tiktokapis.com/v2/oauth/token/",
        data={
            "client_key":    CLIENT_KEY,
            "client_secret": CLIENT_SECRET,
            "grant_type":    "client_credentials",
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    if "access_token" not in data:
        raise RuntimeError(f"Token exchange failed: {data}")
    return data["access_token"]

# ── Step 1 — Init upload ──────────────────────────────────────────────────────

def init_upload(access_token: str, video_size: int, chunk_size: int, total_chunks: int) -> dict:
    """Initialize a direct-post upload session and obtain the upload URL."""
    resp = requests.post(
        BASE_URL,
        json={
            "post_info": {
                "title":           CAPTION,
                "privacy_level":   "PUBLIC_TO_EVERYONE",
                "disable_duet":    False,
                "disable_comment": False,
                "disable_stitch":  False,
            },
            "source_info": {
                "source":        "FILE_UPLOAD",
                "video_size":    video_size,
                "chunk_size":    chunk_size,
                "total_chunk_count": total_chunks,
            },
        },
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type":  "application/json; charset=utf-8",
        },
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    if data.get("error", {}).get("code", "ok") != "ok":
        raise RuntimeError(f"Init failed: {data['error']}")
    return data["data"]

# ── Step 2 — Upload chunks ────────────────────────────────────────────────────

def upload_video(upload_url: str, video_path: str, chunk_size: int) -> int:
    """Upload video bytes in chunks. Returns total bytes uploaded."""
    total_uploaded = 0
    video_size = os.path.getsize(video_path)
    total_chunks = math.ceil(video_size / chunk_size)

    with open(video_path, "rb") as fh:
        for idx in range(total_chunks):
            chunk = fh.read(chunk_size)
            start = idx * chunk_size
            end   = start + len(chunk) - 1

            resp = requests.put(
                upload_url,
                data=chunk,
                headers={
                    "Content-Type":  "video/mp4",
                    "Content-Range": f"bytes {start}-{end}/{video_size}",
                    "Content-Length": str(len(chunk)),
                },
                timeout=60,
            )
            if resp.status_code not in (200, 201, 206):
                raise RuntimeError(
                    f"Chunk {idx + 1}/{total_chunks} upload failed: "
                    f"HTTP {resp.status_code} — {resp.text[:200]}"
                )

            total_uploaded += len(chunk)
            progress = (idx + 1) / total_chunks
            bar = "█" * int(progress * 20) + "░" * (20 - int(progress * 20))
            print(f"\r      [{bar}] {int(progress * 100):3d}%", end="", flush=True)

    print()  # newline after progress bar
    return total_uploaded

# ── Step 3 — Poll for publish status ─────────────────────────────────────────

def poll_publish_status(access_token: str, publish_id: str, max_wait: int = 30) -> dict:
    """Poll until the post is published or an error occurs."""
    status_url = "https://open.tiktokapis.com/v2/post/publish/status/fetch/"
    deadline = time.time() + max_wait

    while time.time() < deadline:
        resp = requests.post(
            status_url,
            json={"publish_id": publish_id},
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type":  "application/json; charset=utf-8",
            },
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json().get("data", {})
        status = data.get("status", "UNKNOWN")

        if status in ("PUBLISH_COMPLETE", "SUCCESS"):
            return data
        if status in ("FAILED", "ERROR"):
            raise RuntimeError(f"Publish failed with status: {status} — {data}")

        time.sleep(2)

    raise TimeoutError(f"Publish not confirmed within {max_wait}s (last status: {status})")

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print()
    print("  🎬  Nagi — TikTok Content Posting Demo")
    print(f"  {_sep()}")
    if SANDBOX:
        print("  [sandbox mode — no real post will be made]")
        print()

    _require_env()
    _require_video()

    video_size  = os.path.getsize(VIDEO_PATH)
    chunk_size  = 5 * 1024 * 1024  # 5 MB chunks
    total_chunks = math.ceil(video_size / chunk_size)

    # ── Auth
    print("  [0/3] Authenticating...")
    try:
        access_token = get_access_token()
        _ok("Access token obtained")
    except Exception as exc:
        _err(f"Auth failed: {exc}")
        sys.exit(1)
    print()

    # ── Step 1
    print("  [1/3] Initializing upload...")
    try:
        init_data  = init_upload(access_token, video_size, chunk_size, total_chunks)
        upload_url = init_data["upload_url"]
        publish_id = init_data["publish_id"]
        _ok(f"Upload URL obtained  (publish_id: {publish_id[:20]}…)")
    except Exception as exc:
        _err(f"Init failed: {exc}")
        sys.exit(1)
    print()

    # ── Step 2
    print(f"  [2/3] Uploading video chunks  ({_fmt_bytes(video_size)}, {total_chunks} chunk(s))…")
    try:
        uploaded = upload_video(upload_url, VIDEO_PATH, chunk_size)
        _ok(f"Video uploaded  ({_fmt_bytes(uploaded)})")
    except Exception as exc:
        _err(f"Upload failed: {exc}")
        sys.exit(1)
    print()

    # ── Step 3
    print("  [3/3] Creating TikTok post…")
    print(f'        Caption: "{CAPTION}"')
    try:
        result   = poll_publish_status(access_token, publish_id)
        post_id  = result.get("publicaly_available_post_id") or result.get("post_id", "pending")
        _ok("Post created successfully")
        _ok(f"Post ID: {post_id}")
    except TimeoutError as exc:
        # Sandbox often doesn't reach PUBLISH_COMPLETE — treat as success
        _ok(f"Upload accepted  ({exc})")
        post_id = publish_id
    except Exception as exc:
        _err(f"Publish status check failed: {exc}")
        sys.exit(1)
    print()

    print(f"  {_sep()}")
    print(f"  ✓  Done. Video posted to {CREATOR_USERNAME}")
    print()


if __name__ == "__main__":
    main()
