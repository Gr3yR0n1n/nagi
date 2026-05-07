# Nagi — TikTok Content Posting API Demo

A screen-recording-ready demo of the TikTok Content Posting API v2.

---

## What this demo shows

| Step | API call | What happens |
|------|----------|--------------|
| 0 | `POST /v2/oauth/token/` | Exchange client credentials for an access token |
| 1 | `POST /v2/post/publish/video/init/` | Initialize a direct-post upload session |
| 2 | `PUT <upload_url>` | Stream the video in 5 MB chunks |
| 3 | `POST /v2/post/publish/status/fetch/` | Poll until the post is live |

`SANDBOX = True` (default) routes to the sandbox endpoint so no real post is made.

---

## Screen-recording checklist

### Before you record

1. Open browser to **https://gr3yr0n1n.github.io/nagi** — have it visible alongside the terminal.

2. Open a terminal and navigate to the demo folder:
   ```bash
   cd /Users/davis/davis/ai/sultanate/iago/projects/nagi/demo
   ```

3. Export your TikTok Developer credentials (from https://developers.tiktok.com):
   ```bash
   export TIKTOK_CLIENT_KEY=your_client_key_here
   export TIKTOK_CLIENT_SECRET=your_client_secret_here
   ```

4. Confirm the sample video is present:
   ```bash
   ls -lh sample_video.mp4
   ```

### Run the demo

```bash
python3 post_to_tiktok.py
```

Expected output:

```
  🎬  Nagi — TikTok Content Posting Demo
  ──────────────────────────────────────
  [sandbox mode — no real post will be made]

  [0/3] Authenticating...
        ✓ Access token obtained

  [1/3] Initializing upload...
        ✓ Upload URL obtained  (publish_id: 7xxxxxxxxxxxxxxxxx…)

  [2/3] Uploading video chunks  (8.4MB, 2 chunk(s))…
        [████████████████████] 100%
        ✓ Video uploaded  (8.4MB)

  [3/3] Creating TikTok post…
        Caption: "The quieter you become, the more you are able to hear. — Rumi #zen #mindfulness #nagi"
        ✓ Post created successfully
        ✓ Post ID: 7xxxxxxxxxxxxxxxxx

  ──────────────────────────────────────
  ✓  Done. Video posted to @nagi_zen
```

---

## Regenerate the sample video

If `sample_video.mp4` is missing, recreate it with:

```bash
/opt/homebrew/bin/ffmpeg -f lavfi \
  -i color=c=0x1C1C1E:size=1080x1920:duration=15:rate=30 \
  -vf "drawtext=fontfile=/System/Library/Fonts/Supplemental/Georgia.ttf:\
text='The quieter you become,\nthe more you are able to hear.':fontcolor=0xC9A84C:fontsize=52:\
x=(w-text_w)/2:y=(h-text_h)/2-60:line_spacing=20:\
alpha='if(lt(t,0.5),t*2,if(gt(t,14),(15-t),1))',\
drawtext=fontfile=/System/Library/Fonts/Supplemental/Georgia.ttf:\
text='— Rumi':fontcolor=white:fontsize=36:\
x=(w-text_w)/2:y=(h/2)+80:\
alpha='if(lt(t,0.5),t*2,if(gt(t,14),(15-t),1))',\
drawtext=fontfile=/System/Library/Fonts/Supplemental/Georgia.ttf:\
text='NAGI 凪':fontcolor=0xC9A84C:fontsize=28:\
x=(w-text_w)/2:y=h-80:alpha=0.6,\
fade=t=in:st=0:d=1,fade=t=out:st=14:d=1" \
  -c:v libx264 -pix_fmt yuv420p -movflags +faststart \
  sample_video.mp4
```

---

## Files

```
demo/
├── post_to_tiktok.py   # Demo script
├── sample_video.mp4    # 15-second portrait TikTok video
└── README.md           # This file
```

---

## TikTok API reference

- Content Posting API: https://developers.tiktok.com/doc/content-posting-api-get-started
- Sandbox testing: https://developers.tiktok.com/doc/content-posting-api-sandbox
- OAuth 2.0 / Client Credentials: https://developers.tiktok.com/doc/login-kit-manage-user-access-tokens
