import yt_dlp
from pydub import AudioSegment
import os

DOWNLOAD_DIR = 'downloads'
os.makedirs(DOWNLOAD_DIR, exist_ok = True)

def download_youtub_audio(url: str) -> str:
    output_path = os.path.join(DOWNLOAD_DIR,"%(title)s.%(ext)s");
    ydl_opts = {
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
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info).replace(".webm", ".wav").replace(".m4a", ".wav")
    return filename

data= download_youtub_audio("https://www.youtube.com/watch?v=mtiOK2QG9Q0")



def convert_to_wav(input_path:str) -> str:
    """Convert any audio/video to WAV format using pydub"""
    output_path = os.path.splitext(input_path)[0] + "_converted.wav"
    audio = AudioSegment.from_file(input_path);
    audio = audio.set_channels(1).set_frame_rate(16000)  #16kHz
    audio.export(output_path, format="wav")
    return output_path

data_final = convert_to_wav(data)


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

print(chunk_audio(data_final))


