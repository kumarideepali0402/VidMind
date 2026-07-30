import os

import yt_dlp
from pydub import AudioSegment

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


def _youtube_ydl_opts(output_path: str) -> dict:
    """yt-dlp options tuned for YouTube's current anti-bot / JS-challenge requirements."""
    return {
        "format": "bestaudio/best",
        "outtmpl": output_path,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "wav",
                "preferredquality": "192",
            }
        ],
        "quiet": True,
        "no_warnings": True,
        # YouTube now requires a JS runtime to solve download challenges (403 without it).
        "js_runtimes": {"node": {}},
        "remote_components": ["ejs:github"],
        "extractor_args": {
            "youtube": {
                "player_client": ["android", "web"],
            }
        },
        "retries": 10,
        "fragment_retries": 10,
    }


def download_youtube_audio(url: str) -> str:
    output_path = os.path.join(DOWNLOAD_DIR, "%(title)s.%(ext)s")
    ydl_opts = _youtube_ydl_opts(output_path)

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            base_path, _ = os.path.splitext(ydl.prepare_filename(info))
            wav_path = f"{base_path}.wav"
            if os.path.exists(wav_path):
                return wav_path
            # Fallback if postprocessor kept another extension.
            prepared = ydl.prepare_filename(info)
            if os.path.exists(prepared):
                return prepared
            raise FileNotFoundError(f"Download finished but audio file not found for: {url}")
    except yt_dlp.utils.DownloadError as exc:
        message = str(exc)
        if "403" in message or "Forbidden" in message:
            raise RuntimeError(
                "YouTube blocked the audio download (HTTP 403). "
                "Try again shortly, run `pip install -U yt-dlp`, ensure Node.js is installed, "
                "or upload the video file directly instead of pasting a URL."
            ) from exc
        raise




def convert_to_wav(input_path:str) -> str:
    """Convert any audio/video to WAV format using pydub"""
    output_path = os.path.splitext(input_path)[0] + "_converted.wav"
    audio = AudioSegment.from_file(input_path);
    audio = audio.set_channels(1).set_frame_rate(16000)  #16kHz
    audio.export(output_path, format="wav")
    return output_path




def chunk_audio(wav_path : str, chunk_minutes : int = 10) -> list:
    audio = AudioSegment.from_wav(wav_path)
    chunk_ms = chunk_minutes * 60 * 1000

    chunks = []

    for i, start in enumerate(range(0, len(audio), chunk_ms)):
        chunk = audio[start : start + chunk_ms]
        chunk_path = f"{wav_path}_chunk_{i}.wav"
        chunk.export(chunk_path, format = "wav")
        chunks.append(chunk_path)
    return chunks


def process_input(source : str) -> list:
    if source.startswith("http://") or source.startswith("https://"):
        print("It's a yt  url. Downloading audio..")
        wav_path = download_youtube_audio(source)
    else:
        print("It's a local file. Converting to WAV...")
        wav_path = convert_to_wav(source)
    
    print("Chunking audio...")
    chunks = chunk_audio(wav_path)
    print(f"Audio ready - {len(chunks)} chunk(s) created")
    return chunks








