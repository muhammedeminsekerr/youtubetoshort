"""faster-whisper ile videodaki konuşmayı zaman damgalı metne çevirir."""
from faster_whisper import WhisperModel

from app.config import settings

_model: WhisperModel | None = None


def _get_model() -> WhisperModel:
    global _model
    if _model is None:
        _model = WhisperModel(
            settings.WHISPER_MODEL,
            device=settings.WHISPER_DEVICE,
            compute_type=settings.WHISPER_COMPUTE_TYPE,
        )
    return _model


def transcribe(media_path: str) -> list[dict]:
    """Verilen video/ses dosyasını segmentlere ayrılmış transkripte çevirir.

    Returns:
        list[dict]: [{"start": float, "end": float, "text": str}, ...]
    """
    model = _get_model()
    segments, _info = model.transcribe(media_path, vad_filter=True)

    result = []
    for seg in segments:
        text = seg.text.strip()
        if not text:
            continue
        result.append({"start": seg.start, "end": seg.end, "text": text})
    return result
