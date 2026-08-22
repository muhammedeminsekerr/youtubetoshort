"""YouTube videolarını yt-dlp ile indirir."""
import os
import yt_dlp


def download_video(url: str, output_dir: str) -> dict:
    """Verilen YouTube URL'sini indirir ve video bilgilerini döndürür.

    Returns:
        dict: path (mp4 dosya yolu), title, duration (saniye), id
    """
    os.makedirs(output_dir, exist_ok=True)

    ydl_opts = {
       "format": "bestvideo[height<=1080]+bestaudio/best[height<=1080]/best",
        "outtmpl": os.path.join(output_dir, "%(id)s.%(ext)s"),
        "merge_output_format": "mp4",
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filepath = ydl.prepare_filename(info)
        if not filepath.endswith(".mp4"):
            base, _ = os.path.splitext(filepath)
            candidate = base + ".mp4"
            if os.path.exists(candidate):
                filepath = candidate

        return {
            "path": filepath,
            "title": info.get("title") or "video",
            "duration": info.get("duration") or 0,
            "id": info.get("id"),
        }
