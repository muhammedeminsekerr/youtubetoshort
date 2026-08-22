"""ffmpeg kullanarak klipleri keser, 9:16 dikey formata çevirir ve
isteğe bağlı olarak altyazı gömer."""
import os
import subprocess


def _format_srt_timestamp(seconds: float) -> str:
    if seconds < 0:
        seconds = 0
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int(round((seconds - int(seconds)) * 1000))
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def _build_srt(segments: list[dict], clip_start: float, clip_end: float, srt_path: str) -> bool:
    """Klip aralığına denk gelen transkript segmentlerinden bir .srt dosyası üretir."""
    lines = []
    index = 1
    for seg in segments:
        seg_start = max(seg["start"], clip_start) - clip_start
        seg_end = min(seg["end"], clip_end) - clip_start
        if seg_end <= seg_start:
            continue
        lines.append(str(index))
        lines.append(f"{_format_srt_timestamp(seg_start)} --> {_format_srt_timestamp(seg_end)}")
        lines.append(seg["text"])
        lines.append("")
        index += 1

    if not lines:
        return False

    with open(srt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return True


def _escape_for_ffmpeg_filter(path: str) -> str:
    # ffmpeg filtre argümanlarında ':' ve '\' özel karakterlerdir (özellikle Windows yollarında)
    return path.replace("\\", "/").replace(":", "\\:")


def cut_clip(
    source_path: str,
    start: float,
    end: float,
    out_path: str,
    subtitle_segments: list[dict] | None = None,
) -> None:
    """Kaynak videodan [start, end] aralığını keser, 1080x1920 dikey
    (bulanık arka plan + ortalanmış ön plan) formatına dönüştürür."""
    duration = max(0.1, end - start)

    vf_parts = [
        "split=2[bg][fg]",
        "[bg]scale=1080:1920:force_original_aspect_ratio=increase,"
        "crop=1080:1920,boxblur=20:1[bg2]",
        "[fg]scale=1080:-2:force_original_aspect_ratio=decrease[fg2]",
        "[bg2][fg2]overlay=(W-w)/2:(H-h)/2[base]",
    ]

    srt_path = out_path + ".srt"
    has_subs = False
    if subtitle_segments:
        has_subs = _build_srt(subtitle_segments, start, end, srt_path)

    if has_subs:
        style = (
            "FontName=Arial,FontSize=15,PrimaryColour=&H0022B0FF,"
            "OutlineColour=&H00000000,BorderStyle=3,Outline=2,"
            "Alignment=2,MarginV=90"
        )
        sub_filter = (
            f"subtitles={_escape_for_ffmpeg_filter(srt_path)}:force_style='{style}'"
        )
        vf_parts.append(f"[base]{sub_filter}[outv]")
        map_label = "[outv]"
    else:
        map_label = "[base]"

    filter_complex = ";".join(vf_parts)

    cmd = [
        "ffmpeg", "-y",
        "-ss", str(start),
        "-i", source_path,
        "-t", str(duration),
        "-filter_complex", filter_complex,
        "-map", map_label,
        "-map", "0:a?",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
        "-c:a", "aac", "-b:a", "160k",
        out_path,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if has_subs and os.path.exists(srt_path):
        os.remove(srt_path)

    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg klip kesme hatası:\n{result.stderr[-2000:]}")
