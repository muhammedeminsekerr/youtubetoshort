from fastapi import BackgroundTasks, FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.models import GenerateRequest
from app.services.jobs import job_manager

app = FastAPI(title="Shorts Üretici")

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(request, "index.html")


@app.post("/api/generate")
def generate(req: GenerateRequest, background_tasks: BackgroundTasks):
    if "youtube.com" not in req.youtube_url and "youtu.be" not in req.youtube_url:
        raise HTTPException(400, "Lütfen geçerli bir YouTube bağlantısı girin.")

    job_id = job_manager.create_job(req)
    background_tasks.add_task(job_manager.run, job_id)
    return {"job_id": job_id}


@app.get("/api/jobs/{job_id}")
def get_job(job_id: str):
    job = job_manager.get(job_id)
    if not job:
        raise HTTPException(404, "İş bulunamadı.")
    return job.to_dict()


@app.get("/api/jobs/{job_id}/clips/{clip_id}/file")
def download_clip(job_id: str, clip_id: str):
    clip = job_manager.get_clip(job_id, clip_id)
    if not clip:
        raise HTTPException(404, "Klip bulunamadı.")
    return FileResponse(
        clip.file_path,
        media_type="video/mp4",
        filename=f"{clip.title[:40].strip() or clip_id}.mp4",
    )
