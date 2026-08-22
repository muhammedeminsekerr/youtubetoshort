"""Transkripti bir LLM'e göndererek en iyi shorts adaylarını bulur.

Varsayılan sağlayıcı Groq (ücretsiz, kredi kartı gerektirmez). İsterseniz
.env dosyasında LLM_PROVIDER=anthropic yaparak Claude API'ye geçebilirsiniz.
"""
import json
import re

from app.config import settings

SYSTEM_PROMPT = """Sen deneyimli bir sosyal medya video editörüsün. Sana uzun bir \
videonun zaman damgalı transkripti verilecek. Görevin, bu videodan bağımsız \
YouTube Shorts / TikTok / Instagram Reels klipleri olabilecek en güçlü anları \
seçmek.

İyi bir klip:
- Kendi başına anlaşılır olur (bağlam için öncesine ihtiyaç duymaz)
- Güçlü bir açılış cümlesi / kanca (hook) ile başlar
- Net bir fikir, şaka, itiraf, sürpriz veya öğretici an içerir
- Ortada kesilmiş bir cümleyle bitmez, mümkünse net biter

SADECE geçerli bir JSON nesnesi döndür, başka hiçbir açıklama, markdown veya \
kod bloğu işareti ekleme. Format tam olarak şöyle olmalı:
{"clips": [{"start": 12.5, "end": 45.0, "title": "Kısa başlık", "hook": "Kanca cümlesi"}, ...]}

Alanlar:
- "start": klibin başlangıç saniyesi (sayı)
- "end": klibin bitiş saniyesi (sayı)
- "title": klip için kısa, dikkat çekici bir başlık (Türkçe, en fazla 8 kelime)
- "hook": izleyiciyi ilk 2 saniyede durduracak bir alt başlık / kanca cümlesi
"""


def _build_user_prompt(
    segments: list[dict],
    clip_count: int,
    min_duration: int,
    max_duration: int,
    video_title: str,
) -> str:
    transcript_lines = [
        f"[{seg['start']:.1f}-{seg['end']:.1f}] {seg['text']}" for seg in segments
    ]
    transcript_text = "\n".join(transcript_lines)

    return f"""Video başlığı: {video_title}

Zaman damgalı transkript:
{transcript_text}

En fazla {clip_count} klip öner. Her klip {min_duration}-{max_duration} \
saniye arasında olmalı. Klipler birbiriyle örtüşmemeli. "start" ve "end" \
değerleri yukarıdaki transkriptteki gerçek zaman damgalarına dayanmalı."""


def _extract_json(raw_text: str) -> list:
    """Modelin döndürdüğü metinden klip listesini ayıklar.

    Hem {"clips": [...]} hem de (eski/uyumluluk için) düz [...] formatını
    kabul eder, kod bloğu işaretlerini temizler.
    """
    cleaned = raw_text.strip()
    cleaned = re.sub(r"^```(json)?", "", cleaned).strip()
    cleaned = re.sub(r"```$", "", cleaned).strip()

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}|\[.*\]", cleaned, re.DOTALL)
        if not match:
            raise
        data = json.loads(match.group(0))

    if isinstance(data, dict):
        return data.get("clips", [])
    if isinstance(data, list):
        return data
    return []


def _call_groq(user_prompt: str) -> str:
    from groq import Groq

    if not settings.GROQ_API_KEY:
        raise RuntimeError(
            "GROQ_API_KEY tanımlı değil. .env dosyanıza console.groq.com "
            "üzerinden aldığınız (ücretsiz) API anahtarınızı ekleyin."
        )

    client = Groq(api_key=settings.GROQ_API_KEY)
    response = client.chat.completions.create(
        model=settings.GROQ_MODEL,
        max_tokens=2000,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
    )
    return response.choices[0].message.content or ""


def _call_anthropic(user_prompt: str) -> str:
    import anthropic

    if not settings.ANTHROPIC_API_KEY:
        raise RuntimeError(
            "ANTHROPIC_API_KEY tanımlı değil. .env dosyanıza Anthropic API "
            "anahtarınızı ekleyin."
        )

    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    response = client.messages.create(
        model=settings.ANTHROPIC_MODEL,
        max_tokens=2000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )
    return "".join(
        block.text for block in response.content if getattr(block, "type", "") == "text"
    )


def find_highlights(
    segments: list[dict],
    clip_count: int,
    min_duration: int,
    max_duration: int,
    video_title: str,
    video_duration: float | None = None,
) -> list[dict]:
    """Seçili LLM sağlayıcısını kullanarak transkriptten en iyi klip adaylarını seçer."""
    user_prompt = _build_user_prompt(
        segments, clip_count, min_duration, max_duration, video_title
    )

    if settings.LLM_PROVIDER == "anthropic":
        raw_text = _call_anthropic(user_prompt)
    else:
        raw_text = _call_groq(user_prompt)

    clips = _extract_json(raw_text)

    validated = []
    for clip in clips:
        try:
            start = float(clip["start"])
            end = float(clip["end"])
        except (KeyError, TypeError, ValueError):
            continue

        if end <= start:
            continue
        if video_duration and end > video_duration:
            end = video_duration
        if end - start < 3:
            continue

        validated.append(
            {
                "start": start,
                "end": end,
                "title": str(clip.get("title", "Klip"))[:120],
                "hook": str(clip.get("hook", ""))[:200],
            }
        )

    validated.sort(key=lambda c: c["start"])
    return validated[:clip_count]
