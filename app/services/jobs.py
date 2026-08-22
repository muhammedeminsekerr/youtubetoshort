"""İndirme -> transkript -> analiz -> kesim adımlarını sırayla çalıştırır
ve iş (job) durumunu bellekte tutar."""
import os
import threading
import uuid
from dataclasses import dataclass, field

from app.config import settings
from app.services import analyzer, clipper, downloader, transcriber


@dataclass
class ClipResult:
    id: str
    title: str
    hook: str
    start: float
    end: float
    file_path: str


@dataclass
class Job:
    id: str
    youtube_url: str
    clip_count: int
    min_duration: int
    max_duration: int
    status: str = "kuyrukta"
    message: str = "Sırada bekliyor..."
    video_title: str = ""
    clips: list = field(default_factory=list)
    error: str | None = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "status": self.status,
            "message": self.message,
            "video_title": self.video_title,
            "error": self.error,
            "clips": [
                {
                    "id": c.id,
                    "title": c.title,
                    "hook": c.hook,
                    "start": round(c.start, 1),
                    "end": round(c.end, 1),
                    "duration": round(c.end - c.start, 1),
                }
                for c in self.clips
            ],
        }


class JobManager:
    def __init__(self):
        self._jobs: dict[str, Job] = {}
        self._lock = threading.Lock()

    def create_job(self, req) -> str:
        job_id = uuid.uuid4().hex[:10]
        job = Job(
            id=job_id,
            youtube_url=req.youtube_url,
            clip_count=req.clip_count,
            min_duration=req.min_duration,
            max_duration=req.max_duration,
        )
        with self._lock:
            self._jobs[job_id] = job
        return job_id

    def get(self, job_id: str) -> Job | None:
        return self._jobs.get(job_id)

    def get_clip(self, job_id: str, clip_id: str) -> ClipResult | None:
        job = self.get(job_id)
        if not job:
            return None
        for c in job.clips:
            if c.id == clip_id:
                return c
        return None

    def run(self, job_id: str) -> None:
        job = self._jobs[job_id]
        try:
            job.status = "indiriliyor"
            job.message = "Video YouTube'dan indiriliyor..."
            video_dir = os.path.join(settings.DOWNLOADS_DIR, job_id)
            info = downloader.download_video(job.youtube_url, video_dir)
            job.video_title = info["title"]

            job.status = "transkript"
            job.message = "Konuşma metne dönüştürülüyor (bu biraz zaman alabilir)..."
            segments = transcriber.transcribe(info["path"])

            if not segments:
                raise RuntimeError(
                    "Videoda algılanabilir konuşma bulunamadı, klip önerisi yapılamıyor."
                )

            job.status = "analiz"
            job.message = "En ilgi çekici anlar Claude ile belirleniyor..."
            highlights = analyzer.find_highlights(
                segments,
                job.clip_count,
                job.min_duration,
                job.max_duration,
                job.video_title,
                video_duration=info.get("duration"),
            )

            if not highlights:
                raise RuntimeError("Uygun klip anı bulunamadı.")

            job.status = "kesiliyor"
            out_dir = os.path.join(settings.OUTPUTS_DIR, job_id)
            os.makedirs(out_dir, exist_ok=True)

            for i, h in enumerate(highlights):
                job.message = f"Klip {i + 1}/{len(highlights)} kesiliyor ve formatlanıyor..."
                clip_id = f"clip{i + 1}"
                out_path = os.path.join(out_dir, f"{clip_id}.mp4")

                sub_segments = None
                if settings.BURN_SUBTITLES:
                    sub_segments = [
                        s for s in segments if s["end"] > h["start"] and s["start"] < h["end"]
                    ]

                clipper.cut_clip(info["path"], h["start"], h["end"], out_path, sub_segments)

                job.clips.append(
                    ClipResult(
                        id=clip_id,
                        title=h.get("title", f"Klip {i + 1}"),
                        hook=h.get("hook", ""),
                        start=h["start"],
                        end=h["end"],
                        file_path=out_path,
                    )
                )

            job.status = "tamam"
            job.message = f"{len(job.clips)} klip hazır."

        except Exception as exc:  # noqa: BLE001 - kullanıcıya hatayı göstermek istiyoruz
            job.status = "hata"
            job.error = str(exc)
            job.message = "Bir hata oluştu."


job_manager = JobManager()
