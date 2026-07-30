# VidMind

Transcribe, summarize, and chat with any meeting or video. Paste a YouTube URL or upload a local file — the assistant handles the rest.

## Features

- **Transcription** — English via OpenAI Whisper (local), Hinglish via Sarvam AI (cloud, translates to English)
- **Auto-generated title** — short professional title from the transcript
- **Meeting summary** — bullet-point summary using a map-reduce LLM chain
- **Action items** — tasks with owner and deadline extracted from the transcript
- **Key decisions** — decisions surfaced from the discussion
- **Open questions** — unresolved topics flagged for follow-up
- **RAG chat** — ask anything about the video; answers are grounded in the transcript via ChromaDB + Mistral

## Tech Stack

| Layer | Technology |
|---|---|
| Audio download | yt-dlp |
| Audio processing | pydub, FFmpeg |
| Transcription | OpenAI Whisper (local), Sarvam AI saaras:v2.5 |
| LLM | Mistral Small via LangChain LCEL |
| Embeddings | `all-MiniLM-L6-v2` (HuggingFace BGE) |
| Vector store | ChromaDB |
| Web UI | HTML, CSS, JavaScript + FastAPI |

## Prerequisites

- Python 3.9+
- **FFmpeg** installed and on `PATH` — required by pydub for audio conversion

  ```bash
  # macOS
  brew install ffmpeg

  # Ubuntu / Debian
  sudo apt install ffmpeg

  # Windows — download from https://ffmpeg.org/download.html and add to PATH
  ```

## Installation

```bash
git clone <repo-url>
cd VidMind

python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

## Configuration

Create a `.env` file in the project root:

```env
MISTRAL_API_KEY=your_mistral_api_key
WHISPER_MODEL=small          # base | small | medium | large
SARVAM_API_KEY=your_sarvam_api_key
SARVAM_STT_MODEL=saaras:v2.5
```

- **Mistral API key** — [console.mistral.ai](https://console.mistral.ai)
- **Sarvam API key** — required only for Hinglish transcription — [sarvam.ai](https://sarvam.ai)
- **WHISPER_MODEL** — larger models are more accurate but slower; `small` is a good default

## Usage

### Web UI

```bash
python -m uvicorn api:app --reload
```

Or on Windows, double-click `run_server.bat`.

Opens at `http://127.0.0.1:8000`. Paste a YouTube URL or upload a local audio/video file, choose a language, and click **Analyze**.

> **Note:** If `uvicorn` alone fails with `uv trampoline failed to canonicalize script path`, use `python -m uvicorn` instead (caused by the `uv` tool intercepting the command).

### CLI

```bash
python main.py
```

Prompts for a URL or file path and language, prints results, then enters an interactive chat loop. Type `exit` to quit.

## Project Structure

```
├── main.py                 # Pipeline orchestration + CLI entry point
├── api.py                  # FastAPI backend for the web UI
├── run_server.bat          # Windows shortcut to start the server
├── static/
│   ├── index.html          # Frontend page
│   ├── css/style.css
│   └── js/app.js
├── requirements.txt
├── .env                    # API keys (not committed)
├── core/
│   ├── transcriber.py      # Whisper (English) and Sarvam (Hinglish) transcription
│   ├── summarizer.py       # Map-reduce summarization and title generation
│   ├── extractor.py        # Action items, key decisions, open questions
│   ├── rag_engine.py       # RAG chain construction and Q&A
│   └── vector_store.py     # ChromaDB vector store with HuggingFace embeddings
├── utils/
│   └── audio_processor.py  # Download, convert to WAV, chunk audio
└── downloads/              # Temporary audio files (git-ignored)
```

## How It Works

```
YouTube URL / local file
        │
        ▼
  audio_processor.py
  ├─ Download via yt-dlp (URL) or convert to 16kHz mono WAV (local file)
  └─ Split into 10-minute chunks
        │
        ▼
  transcriber.py
  ├─ English  → Whisper (local inference)
  └─ Hinglish → Sarvam AI (25s pieces, translates to English)
        │
        ▼
  ┌─────────────────────────────────────────┐
  │  summarizer.py   → title + summary       │
  │  extractor.py    → actions / decisions   │
  │  vector_store.py → ChromaDB index        │
  └─────────────────────────────────────────┘
        │
        ▼
  rag_engine.py — answer questions via similarity retrieval + Mistral
```

## Language Support

| Language | Engine | Notes |
|---|---|---|
| English | OpenAI Whisper (local) | No API key needed |
| Hinglish | Sarvam AI saaras:v2.5 | Translates to English; requires `SARVAM_API_KEY` |
