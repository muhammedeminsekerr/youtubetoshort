const form = document.getElementById("generate-form");
const submitBtn = document.getElementById("submit-btn");
const errorBox = document.getElementById("error-box");
const statusPanel = document.getElementById("status-panel");
const statusMessage = document.getElementById("status-message");
const resultsEl = document.getElementById("results");
const stageEls = Array.from(document.querySelectorAll(".stage"));

const STAGE_ORDER = ["indiriliyor", "transkript", "analiz", "kesiliyor"];

let pollTimer = null;

function showError(message) {
  errorBox.textContent = message;
  errorBox.classList.remove("hidden");
}

function clearError() {
  errorBox.classList.add("hidden");
  errorBox.textContent = "";
}

function setStage(status) {
  const currentIndex = STAGE_ORDER.indexOf(status);
  stageEls.forEach((el) => {
    const stage = el.dataset.stage;
    const idx = STAGE_ORDER.indexOf(stage);
    el.classList.remove("active", "done");
    if (status === "tamam") {
      el.classList.add("done");
    } else if (idx === currentIndex) {
      el.classList.add("active");
    } else if (idx < currentIndex) {
      el.classList.add("done");
    }
  });
}

function formatTime(seconds) {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
}

function renderResults(job) {
  resultsEl.innerHTML = "";
  job.clips.forEach((clip) => {
    const card = document.createElement("div");
    card.className = "result-card";

    const video = document.createElement("video");
    video.src = `/api/jobs/${job.id}/clips/${clip.id}/file`;
    video.controls = true;
    video.preload = "metadata";

    const meta = document.createElement("div");
    meta.className = "meta";
    meta.innerHTML = `
      <h3>${escapeHtml(clip.title)}</h3>
      <p>${escapeHtml(clip.hook || "")}</p>
      <div class="row">
        <span class="duration">${formatTime(clip.start)} – ${formatTime(clip.end)} · ${clip.duration}sn</span>
        <a class="download" href="/api/jobs/${job.id}/clips/${clip.id}/file" download>İndir</a>
      </div>
    `;

    card.appendChild(video);
    card.appendChild(meta);
    resultsEl.appendChild(card);
  });
  resultsEl.classList.remove("hidden");
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

async function pollJob(jobId) {
  try {
    const res = await fetch(`/api/jobs/${jobId}`);
    if (!res.ok) throw new Error("İş durumu alınamadı.");
    const job = await res.json();

    setStage(job.status);

    const titlePart = job.video_title
      ? ` — <span class="video-title">${escapeHtml(job.video_title)}</span>`
      : "";
    statusMessage.innerHTML = `${escapeHtml(job.message || "")}${titlePart}`;

    if (job.status === "hata") {
      showError(job.error || "Bilinmeyen bir hata oluştu.");
      submitBtn.disabled = false;
      return;
    }

    if (job.status === "tamam") {
      renderResults(job);
      submitBtn.disabled = false;
      return;
    }

    pollTimer = setTimeout(() => pollJob(jobId), 2000);
  } catch (err) {
    showError(err.message);
    submitBtn.disabled = false;
  }
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  clearError();
  resultsEl.classList.add("hidden");
  resultsEl.innerHTML = "";
  if (pollTimer) clearTimeout(pollTimer);

  const payload = {
    youtube_url: document.getElementById("youtube_url").value.trim(),
    clip_count: Number(document.getElementById("clip_count").value),
    min_duration: Number(document.getElementById("min_duration").value),
    max_duration: Number(document.getElementById("max_duration").value),
  };

  submitBtn.disabled = true;
  statusPanel.classList.remove("hidden");
  setStage("indiriliyor");
  statusMessage.textContent = "İş başlatılıyor...";

  try {
    const res = await fetch("/api/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      throw new Error(data.detail || "İstek başlatılamadı.");
    }

    const { job_id } = await res.json();
    pollJob(job_id);
  } catch (err) {
    showError(err.message);
    submitBtn.disabled = false;
  }
});
