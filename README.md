# Kliphane 🎬

🇬🇧 English | [🇹🇷 Türkçe](README.tr.md)

Paste a YouTube link. **Kliphane** downloads the video, transcribes it,
uses AI to find the most compelling moments, and turns them into
captioned, vertical (9:16) shorts — ready to post.

- **Download:** [yt-dlp](https://github.com/yt-dlp/yt-dlp)
- **Transcription:** [faster-whisper](https://github.com/SYSTRAN/faster-whisper) (local, free)
- **Highlight selection:** [Groq](https://console.groq.com) (free, default) or [Claude API](https://console.anthropic.com) (paid, optional)
- **Cutting & vertical format:** ffmpeg (blurred background + centered footage + burned-in captions)
- **UI:** FastAPI + Jinja2 + vanilla JS (no frontend framework, single page)

Everything runs on your own machine; videos are kept only in your local
`downloads/` and `outputs/` folders — nothing is uploaded anywhere
automatically.

## Requirements

- Python 3.10+
- [ffmpeg](https://ffmpeg.org/download.html) installed and available on your `PATH`
  - macOS: `brew install ffmpeg`
  - Ubuntu/Debian: `sudo apt install ffmpeg`
  - Windows: download from [ffmpeg.org](https://ffmpeg.org/download.html) and add it to PATH
- A [Groq API key](https://console.groq.com/keys) — **completely free**, no credit card required

## Setup

```bash
git clone <repo-url>
cd youtube-shorts-generator

python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env
# open .env and set GROQ_API_KEY to your own (free) key
```

## Running

```bash
python run.py
```

Open [http://localhost:8000](http://localhost:8000) in your browser.

On first run, `faster-whisper` automatically downloads the Whisper model
you selected (default `small`, ~500 MB) — this only happens once.

## How it works

1. **Download** — yt-dlp fetches the video at the best available quality (≤1080p).
2. **Listen & analyze** — faster-whisper transcribes the speech into
   timestamped text; that transcript is sent to an LLM (default: Groq,
   free), which returns up to N self-contained, strong-hook clip
   suggestions (start/end timestamps, title, hook line) as JSON.
3. **Cut & format** — each suggestion is cut with ffmpeg, converted to a
   1080×1920 vertical format (blurred background + centered original
   footage), and has burned-in captions generated from that segment's
   transcript.

## Configuration (`.env`)

| Variable | Description | Default |
|---|---|---|
| `LLM_PROVIDER` | `groq` (free) or `anthropic` (paid) | `groq` |
| `GROQ_API_KEY` | Your Groq API key (required if LLM_PROVIDER=groq) | — |
| `GROQ_MODEL` | Model name on Groq | `openai/gpt-oss-120b` |
| `ANTHROPIC_API_KEY` | Your Claude API key (required if LLM_PROVIDER=anthropic) | — |
| `ANTHROPIC_MODEL` | Claude model used for highlight selection | `claude-sonnet-5` |
| `WHISPER_MODEL` | `tiny`/`base`/`small`/`medium`/`large-v3` | `small` |
| `WHISPER_DEVICE` | `cpu` or `cuda` | `cpu` |
| `WHISPER_COMPUTE_TYPE` | `int8`, `float16`, etc. | `int8` |
| `BURN_SUBTITLES` | Whether to burn captions into clips | `true` |

## Why Groq (free)?

Groq runs open-source models (like Llama and GPT-OSS) on its own custom
hardware and offers a genuinely free API with no credit card required
(there are per-minute/per-day request limits, but they're far more than
enough for this project — we only make one request per video). Get a key
in seconds at [console.groq.com](https://console.groq.com) with just an
email address.

Groq's model lineup changes over time as models get deprecated — if you
hit a "model not found" error, check
[console.groq.com/docs/models](https://console.groq.com/docs/models) for
the current list and update `GROQ_MODEL` in `.env` accordingly.

If you want higher quality, switch to `LLM_PROVIDER=anthropic` in `.env`
and add a Claude API key at any time — no code changes required.

## Project structure

app/
├── main.py # FastAPI routes
├── config.py # Environment settings
├── models.py # Request models
├── services/
│ ├── downloader.py # Video download via yt-dlp
│ ├── transcriber.py # Transcription via faster-whisper
│ ├── analyzer.py # Highlight selection via LLM (Groq/Claude)
│ ├── clipper.py # Cutting, vertical reframe, captions via ffmpeg
│ └── jobs.py # Job state tracking & pipeline orchestration
├── templates/index.html # Single-page UI
└── static/ # CSS / JS


## Roadmap ideas

- [ ] Face/object tracking for "smart crop" (currently center-crop + blurred background)
- [ ] Automatic title, description, and hashtag suggestions
- [ ] Direct publishing to YouTube/TikTok/Instagram
- [ ] Persist job queue in SQLite instead of memory (survive server restarts)
- [ ] Queue multiple videos at once

## Important note — copyright

This tool is intended only for **your own content** or videos you have
**permission to repost**. Downloading and republishing third-party videos
without permission may violate YouTube's Terms of Service and copyright
law. Responsibility lies with the user.

## License

MIT
